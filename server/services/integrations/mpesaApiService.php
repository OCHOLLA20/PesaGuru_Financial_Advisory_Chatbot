<?php

class MPesaApiService {
    /**
     * @var string The base URL for M-Pesa API (sandbox or production)
     */
    private $baseUrl;
    
    /**
     * @var string The consumer key from the Daraja API
     */
    private $consumerKey;
    
    /**
     * @var string The consumer secret from the Daraja API
     */
    private $consumerSecret;
    
    /**
     * @var string The business short code (Paybill/Till number)
     */
    private $businessShortCode;
    
    /**
     * @var string The passkey provided by Safaricom
     */
    private $passkey;
    
    /**
     * @var string The callback URL for STK push responses
     */
    private $callbackUrl;
    
    /**
     * @var string The transaction type (CustomerPayBillOnline for paybill, CustomerBuyGoodsOnline for till)
     */
    private $transactionType;
    
    /**
     * @var string The access token for API authentication
     */
    private $accessToken;
    
    /**
     * @var int Access token expiry time
     */
    private $tokenExpiry;
    
    /**
     * Constructor
     * Initializes the M-Pesa API service with configuration
     * 
     * @param bool $isSandbox Whether to use sandbox environment (default: false)
     */
    public function __construct($isSandbox = false) {
        // Load configuration
        $config = $this->loadConfig();
        
        // Set environment-specific settings
        if ($isSandbox) {
            $this->baseUrl = 'https://sandbox.safaricom.co.ke';
            $this->consumerKey = $config['sandbox_consumer_key'];
            $this->consumerSecret = $config['sandbox_consumer_secret'];
        } else {
            $this->baseUrl = 'https://api.safaricom.co.ke';
            $this->consumerKey = $config['consumer_key'];
            $this->consumerSecret = $config['consumer_secret'];
        }
        
        // Set common settings
        $this->businessShortCode = $config['business_short_code'];
        $this->passkey = $config['passkey'];
        $this->callbackUrl = $config['callback_url'];
        $this->transactionType = $config['transaction_type'];
        
        // Initialize token variables
        $this->accessToken = null;
        $this->tokenExpiry = 0;
    }
    
    /**
     * Load M-Pesa API configuration
     * 
     * @return array Configuration array
     */
    private function loadConfig() {
        // Try to load configuration from the server's config directory
        $configFile = __DIR__ . '/../../../config/api_keys.php';
        
        if (file_exists($configFile)) {
            return include($configFile);
        }
        
        // If config file doesn't exist, use environment variables with defaults
        return [
            'consumer_key' => getenv('MPESA_CONSUMER_KEY') ?: '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
            'consumer_secret' => getenv('MPESA_CONSUMER_SECRET') ?: 'your_consumer_secret',
            'sandbox_consumer_key' => getenv('MPESA_SANDBOX_CONSUMER_KEY') ?: '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
            'sandbox_consumer_secret' => getenv('MPESA_SANDBOX_CONSUMER_SECRET') ?: 'your_sandbox_consumer_secret',
            'business_short_code' => getenv('MPESA_BUSINESS_SHORT_CODE') ?: '174379',
            'passkey' => getenv('MPESA_PASSKEY') ?: 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919',
            'callback_url' => getenv('MPESA_CALLBACK_URL') ?: 'https://pesaguru.com/api/mpesa/callback',
            'transaction_type' => getenv('MPESA_TRANSACTION_TYPE') ?: 'CustomerPayBillOnline',
        ];
    }
    
    /**
     * Get OAuth access token from M-Pesa API
     * 
     * @return string|null Access token or null on failure
     */
    public function getAccessToken() {
        // Return existing token if it's still valid
        if ($this->accessToken && time() < $this->tokenExpiry) {
            return $this->accessToken;
        }
        
        try {
            // Prepare authorization header
            $credentials = base64_encode($this->consumerKey . ':' . $this->consumerSecret);
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/oauth/v1/generate?grant_type=client_credentials');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Basic ' . $credentials
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Check if request was successful
            if ($httpCode == 200) {
                $result = json_decode($response);
                
                if (isset($result->access_token)) {
                    // Store token and set expiry (usually 1 hour, but we'll use 50 minutes to be safe)
                    $this->accessToken = $result->access_token;
                    $this->tokenExpiry = time() + 3000; // 50 minutes
                    return $this->accessToken;
                }
            }
            
            // Log error if token retrieval failed
            $this->logError('Failed to get access token', [
                'http_code' => $httpCode,
                'response' => $response
            ]);
            
            return null;
        } catch (Exception $e) {
            $this->logError('Exception in getAccessToken', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return null;
        }
    }
    
    /**
     * Initiate Lipa Na M-Pesa Online (STK Push) transaction
     * 
     * @param string $phoneNumber Customer's phone number (starting with 254...)
     * @param float $amount Amount to charge
     * @param string $accountReference Reference for the transaction
     * @param string $description Transaction description
     * @return array Response from the API
     */
    public function initiateSTKPush($phoneNumber, $amount, $accountReference, $description) {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare timestamp
            $timestamp = date('YmdHis');
            $password = base64_encode($this->businessShortCode . $this->passkey . $timestamp);
            
            // Prepare request data
            $data = [
                'BusinessShortCode' => $this->businessShortCode,
                'Password' => $password,
                'Timestamp' => $timestamp,
                'TransactionType' => $this->transactionType,
                'Amount' => round($amount),
                'PartyA' => $phoneNumber,
                'PartyB' => $this->businessShortCode,
                'PhoneNumber' => $phoneNumber,
                'CallBackURL' => $this->callbackUrl,
                'AccountReference' => $accountReference,
                'TransactionDesc' => $description
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/stkpush/v1/processrequest');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('STK Push failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in initiateSTKPush', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Check the status of an STK Push transaction
     * 
     * @param string $checkoutRequestId The checkout request ID from initiateSTKPush
     * @return array Response from the API
     */
    public function checkSTKStatus($checkoutRequestId) {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare timestamp
            $timestamp = date('YmdHis');
            $password = base64_encode($this->businessShortCode . $this->passkey . $timestamp);
            
            // Prepare request data
            $data = [
                'BusinessShortCode' => $this->businessShortCode,
                'Password' => $password,
                'Timestamp' => $timestamp,
                'CheckoutRequestID' => $checkoutRequestId
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/stkpushquery/v1/query');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('STK Status check failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in checkSTKStatus', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Check account balance
     * 
     * @param string $partyA The organization receiving the transaction (Paybill or Till number)
     * @param int $identifierType Type of organization (4 for Paybill, 2 for Till)
     * @param string $remarks Additional remarks for the transaction
     * @return array Response from the API
     */
    public function checkAccountBalance($partyA, $identifierType = 4, $remarks = 'PesaGuru balance query') {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare request data
            $data = [
                'Initiator' => $this->getConfig('initiator_name'),
                'SecurityCredential' => $this->getConfig('security_credential'),
                'CommandID' => 'AccountBalance',
                'PartyA' => $partyA,
                'IdentifierType' => $identifierType,
                'Remarks' => $remarks,
                'QueueTimeOutURL' => $this->getConfig('timeout_url'),
                'ResultURL' => $this->getConfig('result_url')
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/accountbalance/v1/query');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('Account balance check failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in checkAccountBalance', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Check transaction status
     * 
     * @param string $transactionId The transaction ID to check
     * @param string $partyA The organization receiving the transaction (Paybill or Till number)
     * @param int $identifierType Type of organization (4 for Paybill, 2 for Till)
     * @param string $remarks Additional remarks for the transaction
     * @param string $occasion The occasion for the transaction
     * @return array Response from the API
     */
    public function checkTransactionStatus($transactionId, $partyA, $identifierType = 4, $remarks = 'Transaction status', $occasion = 'Transaction status') {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare request data
            $data = [
                'Initiator' => $this->getConfig('initiator_name'),
                'SecurityCredential' => $this->getConfig('security_credential'),
                'CommandID' => 'TransactionStatusQuery',
                'TransactionID' => $transactionId,
                'PartyA' => $partyA,
                'IdentifierType' => $identifierType,
                'ResultURL' => $this->getConfig('result_url'),
                'QueueTimeOutURL' => $this->getConfig('timeout_url'),
                'Remarks' => $remarks,
                'Occasion' => $occasion
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/transactionstatus/v1/query');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('Transaction status check failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in checkTransactionStatus', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Business to Customer (B2C) payment
     * 
     * @param string $phoneNumber Customer's phone number (starting with 254...)
     * @param float $amount Amount to send
     * @param string $commandId Type of transaction (SalaryPayment, BusinessPayment, PromotionPayment)
     * @param string $remarks Additional remarks for the transaction
     * @param string $occasion The occasion for the transaction
     * @return array Response from the API
     */
    public function b2cPayment($phoneNumber, $amount, $commandId = 'BusinessPayment', $remarks = 'Payment', $occasion = 'Payment') {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare request data
            $data = [
                'InitiatorName' => $this->getConfig('initiator_name'),
                'SecurityCredential' => $this->getConfig('security_credential'),
                'CommandID' => $commandId,
                'Amount' => round($amount),
                'PartyA' => $this->businessShortCode,
                'PartyB' => $phoneNumber,
                'Remarks' => $remarks,
                'QueueTimeOutURL' => $this->getConfig('timeout_url'),
                'ResultURL' => $this->getConfig('result_url'),
                'Occasion' => $occasion
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/b2c/v1/paymentrequest');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('B2C payment failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in b2cPayment', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Register C2B URLs (for receiving payments)
     * 
     * @param string $validationUrl URL that receives validation requests
     * @param string $confirmationUrl URL that receives confirmation requests
     * @param int $responseType Response type (0 for Completed or 1 for Cancelled)
     * @return array Response from the API
     */
    public function registerC2BUrls($validationUrl, $confirmationUrl, $responseType = 0) {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare request data
            $data = [
                'ShortCode' => $this->businessShortCode,
                'ResponseType' => $responseType,
                'ConfirmationURL' => $confirmationUrl,
                'ValidationURL' => $validationUrl
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/c2b/v1/registerurl');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('C2B URL registration failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in registerC2BUrls', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Simulate a C2B transaction (sandbox only)
     * 
     * @param string $phoneNumber Customer's phone number (starting with 254...)
     * @param float $amount Amount to charge
     * @param string $billRefNumber Reference for the transaction
     * @param string $commandId Type of transaction (CustomerPayBillOnline, CustomerBuyGoodsOnline)
     * @return array Response from the API
     */
    public function simulateC2B($phoneNumber, $amount, $billRefNumber, $commandId = 'CustomerPayBillOnline') {
        try {
            // Get access token
            $accessToken = $this->getAccessToken();
            if (!$accessToken) {
                return ['status' => 'error', 'message' => 'Could not get access token'];
            }
            
            // Prepare request data
            $data = [
                'ShortCode' => $this->businessShortCode,
                'CommandID' => $commandId,
                'Amount' => round($amount),
                'Msisdn' => $phoneNumber,
                'BillRefNumber' => $billRefNumber
            ];
            
            // Set up cURL request
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/mpesa/c2b/v1/simulate');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            
            // Execute the request
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Process the response
            $result = json_decode($response, true);
            
            if ($httpCode >= 200 && $httpCode < 300) {
                return [
                    'status' => 'success',
                    'data' => $result
                ];
            } else {
                $this->logError('C2B simulation failed', [
                    'http_code' => $httpCode,
                    'response' => $response
                ]);
                
                return [
                    'status' => 'error',
                    'message' => isset($result['errorMessage']) ? $result['errorMessage'] : 'Unknown error',
                    'data' => $result
                ];
            }
        } catch (Exception $e) {
            $this->logError('Exception in simulateC2B', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return [
                'status' => 'error',
                'message' => 'An exception occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get a configuration value or use default
     * 
     * @param string $key The configuration key
     * @param mixed $default Default value if key not found
     * @return mixed The configuration value
     */
    private function getConfig($key, $default = null) {
        // Try to load from environment variable
        $envValue = getenv('MPESA_' . strtoupper($key));
        if ($envValue) {
            return $envValue;
        }
        
        // Return default
        return $default;
    }
    
    /**
     * Log error messages
     * 
     * @param string $message Error message
     * @param array $context Additional context data
     * @return void
     */
    private function logError($message, $context = []) {
        $logDir = __DIR__ . '/../../../logs';
        
        // Create logs directory if it doesn't exist
        if (!is_dir($logDir)) {
            mkdir($logDir, 0777, true);
        }
        
        $logFile = $logDir . '/mpesa_' . date('Y-m-d') . '.log';
        $timestamp = date('Y-m-d H:i:s');
        
        // Format the log message
        $logMessage = "[$timestamp] ERROR: $message\n";
        $logMessage .= "Context: " . json_encode($context, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n\n";
        
        // Write to log file
        file_put_contents($logFile, $logMessage, FILE_APPEND);
        
        // Also log to PHP error log for critical errors
        error_log("MPesaApiService: $message");
    }
}