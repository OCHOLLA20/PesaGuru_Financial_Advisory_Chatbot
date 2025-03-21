<?php

namespace PesaGuru\Services\Payments;

use Exception;

class MpesaService {
    /**
     * @var string The base URL for M-Pesa API endpoints (sandbox or production)
     */
    private $baseUrl;
    
    /**
     * @var string The consumer key for API authentication
     */
    private $consumerKey;
    
    /**
     * @var string The consumer secret for API authentication
     */
    private $consumerSecret;
    
    /**
     * @var string The business shortcode (Paybill or Till number)
     */
    private $shortCode;
    
    /**
     * @var string The passkey for STK Push transactions
     */
    private $passKey;
    
    /**
     * @var string The callback URL for STK Push responses
     */
    private $callbackUrl;
    
    /**
     * @var string The access token for API requests
     */
    private $accessToken;
    
    /**
     * Class constructor
     * 
     * @param bool $isSandbox Whether to use the sandbox environment
     */
    public function __construct($isSandbox = true) {
        // Load configuration based on environment
        $this->loadConfig($isSandbox);
        
        // Get access token on initialization
        $this->authenticate();
    }
    
    /**
     * Load configuration values
     * 
     * @param bool $isSandbox Whether to use sandbox environment
     */
    private function loadConfig($isSandbox) {
        // In a real application, these would come from a config file or environment variables
        if ($isSandbox) {
            $this->baseUrl = 'https://sandbox.safaricom.co.ke';
            $this->consumerKey = 'YOUR_SANDBOX_CONSUMER_KEY';
            $this->consumerSecret = 'YOUR_SANDBOX_CONSUMER_SECRET';
            $this->shortCode = 'YOUR_SANDBOX_SHORTCODE'; // Typically 174379 for sandbox
            $this->passKey = 'YOUR_SANDBOX_PASSKEY';
            $this->callbackUrl = 'https://example.com/api/mpesa/callback';
        } else {
            $this->baseUrl = 'https://api.safaricom.co.ke';
            $this->consumerKey = 'YOUR_PRODUCTION_CONSUMER_KEY';
            $this->consumerSecret = 'YOUR_PRODUCTION_CONSUMER_SECRET';
            $this->shortCode = 'YOUR_PRODUCTION_SHORTCODE'; // Your actual Paybill or Till number
            $this->passKey = 'YOUR_PRODUCTION_PASSKEY';
            $this->callbackUrl = 'https://pesaguru.com/api/mpesa/callback';
        }
    }
    
    /**
     * Authenticate with M-Pesa API to get access token
     * 
     * @return string The access token
     * @throws Exception If authentication fails
     */
    public function authenticate() {
        $url = $this->baseUrl . '/oauth/v1/generate?grant_type=client_credentials';
        
        $curl = curl_init();
        curl_setopt($curl, CURLOPT_URL, $url);
        $credentials = base64_encode($this->consumerKey . ':' . $this->consumerSecret);
        curl_setopt($curl, CURLOPT_HTTPHEADER, array('Authorization: Basic ' . $credentials));
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);
        
        $response = curl_exec($curl);
        
        if ($response === false) {
            throw new Exception('Failed to connect to M-Pesa API: ' . curl_error($curl));
        }
        
        $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        
        if ($httpCode != 200) {
            throw new Exception('Authentication failed with code ' . $httpCode . ': ' . $response);
        }
        
        curl_close($curl);
        
        $result = json_decode($response);
        $this->accessToken = $result->access_token;
        
        return $this->accessToken;
    }
    
    /**
     * Initiate an STK Push request to prompt user for payment
     * 
     * @param string $phoneNumber Customer phone number (format: 254XXXXXXXXX)
     * @param float $amount Amount to be paid
     * @param string $accountReference Account reference
     * @param string $transactionDesc Transaction description
     * @return object API response
     * @throws Exception If the request fails
     */
    public function initiateSTKPush($phoneNumber, $amount, $accountReference, $transactionDesc) {
        // Ensure we have a valid access token
        if (empty($this->accessToken)) {
            $this->authenticate();
        }
        
        $url = $this->baseUrl . '/mpesa/stkpush/v1/processrequest';
        
        // Prepare the STK Push request payload
        $timestamp = date('YmdHis');
        $password = base64_encode($this->shortCode . $this->passKey . $timestamp);
        
        $data = [
            'BusinessShortCode' => $this->shortCode,
            'Password' => $password,
            'Timestamp' => $timestamp,
            'TransactionType' => 'CustomerPayBillOnline',
            'Amount' => $amount,
            'PartyA' => $phoneNumber,
            'PartyB' => $this->shortCode,
            'PhoneNumber' => $phoneNumber,
            'CallBackURL' => $this->callbackUrl,
            'AccountReference' => $accountReference,
            'TransactionDesc' => $transactionDesc
        ];
        
        $response = $this->makeRequest($url, $data);
        
        // Log the transaction initiation for tracking purposes
        $this->logTransaction($phoneNumber, $amount, $response);
        
        return $response;
    }
    
    /**
     * Check the status of an STK Push transaction
     * 
     * @param string $checkoutRequestID The checkout request ID from STK push request
     * @return object API response
     * @throws Exception If the request fails
     */
    public function checkTransactionStatus($checkoutRequestID) {
        // Ensure we have a valid access token
        if (empty($this->accessToken)) {
            $this->authenticate();
        }
        
        $url = $this->baseUrl . '/mpesa/stkpushquery/v1/query';
        
        // Prepare transaction status request payload
        $timestamp = date('YmdHis');
        $password = base64_encode($this->shortCode . $this->passKey . $timestamp);
        
        $data = [
            'BusinessShortCode' => $this->shortCode,
            'Password' => $password,
            'Timestamp' => $timestamp,
            'CheckoutRequestID' => $checkoutRequestID
        ];
        
        return $this->makeRequest($url, $data);
    }
    
    /**
     * Process the callback from M-Pesa API
     * 
     * @param string $callbackData The raw callback data from M-Pesa
     * @return array Processed callback data
     */
    public function processCallback($callbackData) {
        $callbackData = json_decode($callbackData);
        
        if (isset($callbackData->Body->stkCallback)) {
            $resultCode = $callbackData->Body->stkCallback->ResultCode;
            $resultDesc = $callbackData->Body->stkCallback->ResultDesc;
            $merchantRequestID = $callbackData->Body->stkCallback->MerchantRequestID;
            $checkoutRequestID = $callbackData->Body->stkCallback->CheckoutRequestID;
            
            // If the transaction was successful, get the transaction details
            if ($resultCode == 0) {
                $amount = $callbackData->Body->stkCallback->CallbackMetadata->Item[0]->Value;
                $mpesaReceiptNumber = $callbackData->Body->stkCallback->CallbackMetadata->Item[1]->Value;
                $transactionDate = $callbackData->Body->stkCallback->CallbackMetadata->Item[3]->Value;
                $phoneNumber = $callbackData->Body->stkCallback->CallbackMetadata->Item[4]->Value;
                
                // Log the successful transaction in database
                $this->logSuccessfulTransaction($mpesaReceiptNumber, $amount, $phoneNumber);
                
                return [
                    'success' => true,
                    'resultCode' => $resultCode,
                    'resultDesc' => $resultDesc,
                    'merchantRequestID' => $merchantRequestID,
                    'checkoutRequestID' => $checkoutRequestID,
                    'amount' => $amount,
                    'mpesaReceiptNumber' => $mpesaReceiptNumber,
                    'transactionDate' => $transactionDate,
                    'phoneNumber' => $phoneNumber
                ];
            } else {
                // Log the failed transaction
                $this->logFailedTransaction($checkoutRequestID, $resultCode, $resultDesc);
                
                return [
                    'success' => false,
                    'resultCode' => $resultCode,
                    'resultDesc' => $resultDesc,
                    'merchantRequestID' => $merchantRequestID,
                    'checkoutRequestID' => $checkoutRequestID
                ];
            }
        }
        
        return ['success' => false, 'message' => 'Invalid callback data'];
    }
    
    /**
     * Initiate B2C transaction (Business to Customer)
     * Used for sending money to customers (e.g., loan disbursements)
     * 
     * @param string $phoneNumber Recipient phone number (format: 254XXXXXXXXX)
     * @param float $amount Amount to send
     * @param string $commandID Type of transaction (BusinessPayment, SalaryPayment, PromotionPayment)
     * @param string $remarks Transaction remarks
     * @param string $occassion Transaction occasion
     * @return object API response
     * @throws Exception If the request fails
     */
    public function initiateB2CPayment($phoneNumber, $amount, $commandID, $remarks, $occassion = '') {
        // Ensure we have a valid access token
        if (empty($this->accessToken)) {
            $this->authenticate();
        }
        
        $url = $this->baseUrl . '/mpesa/b2c/v1/paymentrequest';
        
        // Prepare B2C payment request payload
        $data = [
            'InitiatorName' => 'YOUR_INITIATOR_NAME',
            'SecurityCredential' => 'YOUR_SECURITY_CREDENTIAL', // Encrypted credential
            'CommandID' => $commandID,
            'Amount' => $amount,
            'PartyA' => $this->shortCode,
            'PartyB' => $phoneNumber,
            'Remarks' => $remarks,
            'QueueTimeOutURL' => 'https://pesaguru.com/api/mpesa/b2c/timeout',
            'ResultURL' => 'https://pesaguru.com/api/mpesa/b2c/result',
            'Occasion' => $occassion
        ];
        
        $response = $this->makeRequest($url, $data);
        
        // Log the B2C transaction initiation
        $this->logB2CTransaction($phoneNumber, $amount, $response);
        
        return $response;
    }
    
    /**
     * Make an HTTP request to the M-Pesa API
     * 
     * @param string $url API endpoint URL
     * @param array $data Request payload
     * @return object API response
     * @throws Exception If the request fails
     */
    private function makeRequest($url, $data) {
        $curl = curl_init();
        curl_setopt($curl, CURLOPT_URL, $url);
        curl_setopt($curl, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer ' . $this->accessToken,
            'Content-Type: application/json'
        ]);
        curl_setopt($curl, CURLOPT_POST, true);
        curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($curl, CURLOPT_SSL_VERIFYPEER, false);
        
        $response = curl_exec($curl);
        
        if ($response === false) {
            throw new Exception('Failed to connect to M-Pesa API: ' . curl_error($curl));
        }
        
        $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        
        if ($httpCode < 200 || $httpCode >= 300) {
            throw new Exception('Request failed with code ' . $httpCode . ': ' . $response);
        }
        
        curl_close($curl);
        
        return json_decode($response);
    }
    
    /**
     * Log transaction initiation for tracking
     * 
     * @param string $phoneNumber Customer phone number
     * @param float $amount Transaction amount
     * @param object $response API response
     */
    private function logTransaction($phoneNumber, $amount, $response) {
        // In a real application, you would save this to a database
        // Here we'll just write to a log file for demonstration
        $logFile = __DIR__ . '/../../logs/mpesa_transactions.log';
        $logData = date('Y-m-d H:i:s') . ' | ' .
                   'Phone: ' . $phoneNumber . ' | ' .
                   'Amount: ' . $amount . ' | ' .
                   'MerchantRequestID: ' . $response->MerchantRequestID . ' | ' .
                   'CheckoutRequestID: ' . $response->CheckoutRequestID . ' | ' .
                   'ResponseCode: ' . $response->ResponseCode . ' | ' .
                   'ResponseDescription: ' . $response->ResponseDescription . "\n";
        
        // Make sure the log directory exists
        if (!file_exists(dirname($logFile))) {
            mkdir(dirname($logFile), 0777, true);
        }
        
        file_put_contents($logFile, $logData, FILE_APPEND);
    }
    
    /**
     * Log successful transaction details
     * 
     * @param string $receiptNumber M-Pesa receipt number
     * @param float $amount Transaction amount
     * @param string $phoneNumber Customer phone number
     */
    private function logSuccessfulTransaction($receiptNumber, $amount, $phoneNumber) {
        // In a real application, you would update transaction in database
        // Here we'll just write to a log file for demonstration
        $logFile = __DIR__ . '/../../logs/mpesa_successful_transactions.log';
        $logData = date('Y-m-d H:i:s') . ' | ' .
                   'Receipt: ' . $receiptNumber . ' | ' .
                   'Phone: ' . $phoneNumber . ' | ' .
                   'Amount: ' . $amount . "\n";
        
        // Make sure the log directory exists
        if (!file_exists(dirname($logFile))) {
            mkdir(dirname($logFile), 0777, true);
        }
        
        file_put_contents($logFile, $logData, FILE_APPEND);
    }
    
    /**
     * Log failed transaction details
     * 
     * @param string $checkoutRequestID Checkout request ID
     * @param int $resultCode Result code from M-Pesa
     * @param string $resultDesc Result description from M-Pesa
     */
    private function logFailedTransaction($checkoutRequestID, $resultCode, $resultDesc) {
        // In a real application, you would update transaction in database
        // Here we'll just write to a log file for demonstration
        $logFile = __DIR__ . '/../../logs/mpesa_failed_transactions.log';
        $logData = date('Y-m-d H:i:s') . ' | ' .
                   'CheckoutRequestID: ' . $checkoutRequestID . ' | ' .
                   'ResultCode: ' . $resultCode . ' | ' .
                   'ResultDesc: ' . $resultDesc . "\n";
        
        // Make sure the log directory exists
        if (!file_exists(dirname($logFile))) {
            mkdir(dirname($logFile), 0777, true);
        }
        
        file_put_contents($logFile, $logData, FILE_APPEND);
    }
    
    /**
     * Log B2C transaction initiation
     * 
     * @param string $phoneNumber Recipient phone number
     * @param float $amount Transaction amount
     * @param object $response API response
     */
    private function logB2CTransaction($phoneNumber, $amount, $response) {
        // In a real application, you would save this to a database
        // Here we'll just write to a log file for demonstration
        $logFile = __DIR__ . '/../../logs/mpesa_b2c_transactions.log';
        $logData = date('Y-m-d H:i:s') . ' | ' .
                   'Phone: ' . $phoneNumber . ' | ' .
                   'Amount: ' . $amount . ' | ' .
                   'ConversationID: ' . $response->ConversationID . ' | ' .
                   'OriginatorConversationID: ' . $response->OriginatorConversationID . ' | ' .
                   'ResponseCode: ' . $response->ResponseCode . ' | ' .
                   'ResponseDescription: ' . $response->ResponseDescription . "\n";
        
        // Make sure the log directory exists
        if (!file_exists(dirname($logFile))) {
            mkdir(dirname($logFile), 0777, true);
        }
        
        file_put_contents($logFile, $logData, FILE_APPEND);
    }
    
    /**
     * Generate a unique transaction reference
     * 
     * @return string Transaction reference
     */
    public function generateTransactionReference() {
        return 'PG' . time() . rand(1000, 9999);
    }
}