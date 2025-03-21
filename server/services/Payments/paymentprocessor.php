<?php
/**
 * Payment Processor for PesaGuru Financial Advisory Chatbot
 * 
 * This class handles various payment methods including M-Pesa, PayPal, and credit cards.
 * It provides a standardized interface for processing payments, checking transaction status,
 * and recording payment data.
 * 
 * @package PesaGuru\Services\Payments
 */

namespace PesaGuru\Services\Payments;

use Exception;
use PDO;

class PaymentProcessor {
    /**
     * @var array Supported payment methods
     */
    private $supportedMethods = ['mpesa', 'paypal', 'card'];
    
    /**
     * @var array Configuration for payment gateways
     */
    private $config;
    
    /**
     * @var PDO Database connection
     */
    private $db;
    
    /**
     * @var array Response codes and messages
     */
    private $responseCodes = [
        'success' => 200,
        'invalid_method' => 400,
        'payment_failed' => 402,
        'internal_error' => 500
    ];
    
    /**
     * Constructor
     * 
     * @param PDO $db Database connection
     * @param array $config Payment gateway configuration (optional)
     */
    public function __construct(PDO $db, ?array $config = null) {
        $this->db = $db;
        
        // If config is not provided, load from environment variables
        if ($config === null) {
            $this->config = [
                'mpesa' => [
                    'consumer_key' => getenv('MPESA_CONSUMER_KEY'),
                    'consumer_secret' => getenv('MPESA_CONSUMER_SECRET'),
                    'shortcode' => getenv('MPESA_SHORTCODE'),
                    'passkey' => getenv('MPESA_PASSKEY'),
                    'callback_url' => getenv('MPESA_CALLBACK_URL'),
                    'environment' => getenv('MPESA_ENVIRONMENT')
                ],
                'paypal' => [
                    'client_id' => getenv('PAYPAL_CLIENT_ID'),
                    'client_secret' => getenv('PAYPAL_CLIENT_SECRET'),
                    'environment' => getenv('PAYPAL_ENVIRONMENT')
                ],
                'card' => [
                    'api_key' => getenv('CARD_API_KEY'),
                    'merchant_id' => getenv('CARD_MERCHANT_ID'),
                    'environment' => getenv('CARD_ENVIRONMENT')
                ]
            ];
        } else {
            $this->config = $config;
        }
    }
    
    /**
     * Process a payment
     * 
     * @param string $paymentMethod Payment method (mpesa, paypal, card)
     * @param array $paymentData Payment details
     * @return array Payment response
     */
    public function processPayment(string $paymentMethod, array $paymentData): array {
        try {
            // Validate payment method
            if (!in_array($paymentMethod, $this->supportedMethods)) {
                return $this->formatResponse(
                    false,
                    $this->responseCodes['invalid_method'],
                    "Unsupported payment method: {$paymentMethod}"
                );
            }
            
            // Validate payment data
            $validationResult = $this->validatePaymentData($paymentMethod, $paymentData);
            if (!$validationResult['success']) {
                return $validationResult;
            }
            
            // Process payment based on method
            switch ($paymentMethod) {
                case 'mpesa':
                    return $this->processMpesaPayment($paymentData);
                
                case 'paypal':
                    return $this->processPaypalPayment($paymentData);
                    
                case 'card':
                    return $this->processCardPayment($paymentData);
                
                default:
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Unsupported payment method"
                    );
            }
        } catch (Exception $e) {
            $this->logError('Payment processing error', $e->getMessage(), [
                'payment_method' => $paymentMethod,
                'payment_data' => $this->sanitizePaymentData($paymentData)
            ]);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "Payment processing error: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Process M-Pesa payment
     * 
     * @param array $paymentData Payment details
     * @return array Payment response
     */
    private function processMpesaPayment(array $paymentData): array {
        try {
            // Extract required data
            $phoneNumber = $paymentData['phone_number'];
            $amount = $paymentData['amount'];
            $accountReference = $paymentData['account_reference'] ?? 'PesaGuru Subscription';
            $transactionDesc = $paymentData['transaction_desc'] ?? 'Payment for PesaGuru Service';
            
            // Format phone number to required format (254XXXXXXXXX)
            $phoneNumber = $this->formatPhoneNumber($phoneNumber);
            
            // Get access token
            $accessToken = $this->getMpesaAccessToken();
            
            // Generate timestamp
            $timestamp = date('YmdHis');
            
            // Generate password
            $password = base64_encode($this->config['mpesa']['shortcode'] . $this->config['mpesa']['passkey'] . $timestamp);
            
            // Prepare request data
            $requestData = [
                'BusinessShortCode' => $this->config['mpesa']['shortcode'],
                'Password' => $password,
                'Timestamp' => $timestamp,
                'TransactionType' => 'CustomerPayBillOnline',
                'Amount' => $amount,
                'PartyA' => $phoneNumber,
                'PartyB' => $this->config['mpesa']['shortcode'],
                'PhoneNumber' => $phoneNumber,
                'CallBackURL' => $this->config['mpesa']['callback_url'],
                'AccountReference' => $accountReference,
                'TransactionDesc' => $transactionDesc
            ];
            
            // Determine API URL based on environment
            $apiUrl = ($this->config['mpesa']['environment'] === 'production')
                ? 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
                : 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest';
            
            // Send request to M-Pesa
            $ch = curl_init($apiUrl);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestData));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Parse response
            $responseData = json_decode($response, true);
            
            // Check if request was successful
            if ($httpCode == 200 && isset($responseData['ResponseCode']) && $responseData['ResponseCode'] == '0') {
                // Log successful payment request
                $this->logPaymentRequest(
                    'mpesa',
                    $responseData['CheckoutRequestID'],
                    $amount,
                    $phoneNumber,
                    'pending',
                    $responseData
                );
                
                return $this->formatResponse(
                    true,
                    200,
                    "M-Pesa payment request sent successfully",
                    [
                        'checkout_request_id' => $responseData['CheckoutRequestID'],
                        'response' => $responseData
                    ]
                );
            } else {
                // Log failed payment request
                $this->logPaymentRequest(
                    'mpesa',
                    $responseData['CheckoutRequestID'] ?? null,
                    $amount,
                    $phoneNumber,
                    'failed',
                    $responseData
                );
                
                return $this->formatResponse(
                    false,
                    $this->responseCodes['payment_failed'],
                    "M-Pesa payment request failed",
                    ['response' => $responseData]
                );
            }
        } catch (Exception $e) {
            $this->logError('M-Pesa payment processing error', $e->getMessage(), $paymentData);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "M-Pesa payment processing error: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Get M-Pesa access token
     * 
     * @return string Access token
     * @throws Exception If access token could not be obtained
     */
    private function getMpesaAccessToken(): string {
        // Determine API URL based on environment
        $apiUrl = ($this->config['mpesa']['environment'] === 'production')
            ? 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            : 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials';
        
        // Send request to M-Pesa
        $credentials = base64_encode($this->config['mpesa']['consumer_key'] . ':' . $this->config['mpesa']['consumer_secret']);
        
        $ch = curl_init($apiUrl);
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Authorization: Basic ' . $credentials]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        // Parse response
        $responseData = json_decode($response, true);
        
        // Check if request was successful
        if ($httpCode == 200 && isset($responseData['access_token'])) {
            return $responseData['access_token'];
        } else {
            throw new Exception("Could not get M-Pesa access token: " . json_encode($responseData));
        }
    }
    
    /**
     * Process PayPal payment
     * 
     * @param array $paymentData Payment details
     * @return array Payment response
     */
    private function processPaypalPayment(array $paymentData): array {
        try {
            // Extract required data
            $amount = $paymentData['amount'];
            $currency = $paymentData['currency'] ?? 'USD';
            $returnUrl = $paymentData['return_url'] ?? '';
            $cancelUrl = $paymentData['cancel_url'] ?? '';
            $description = $paymentData['description'] ?? 'PesaGuru Service Payment';
            
            // Get PayPal access token
            $accessToken = $this->getPaypalAccessToken();
            
            // Prepare request data
            $requestData = [
                'intent' => 'CAPTURE',
                'purchase_units' => [
                    [
                        'amount' => [
                            'currency_code' => $currency,
                            'value' => number_format($amount, 2, '.', '')
                        ],
                        'description' => $description
                    ]
                ],
                'application_context' => [
                    'return_url' => $returnUrl,
                    'cancel_url' => $cancelUrl
                ]
            ];
            
            // Determine API URL based on environment
            $apiUrl = ($this->config['paypal']['environment'] === 'production')
                ? 'https://api.paypal.com/v2/checkout/orders'
                : 'https://api.sandbox.paypal.com/v2/checkout/orders';
            
            // Send request to PayPal
            $ch = curl_init($apiUrl);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestData));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Parse response
            $responseData = json_decode($response, true);
            
            // Check if request was successful
            if ($httpCode == 201 && isset($responseData['id'])) {
                // Extract approval URL for redirect
                $approvalUrl = '';
                foreach ($responseData['links'] as $link) {
                    if ($link['rel'] === 'approve') {
                        $approvalUrl = $link['href'];
                        break;
                    }
                }
                
                // Log successful payment request
                $this->logPaymentRequest(
                    'paypal',
                    $responseData['id'],
                    $amount,
                    $paymentData['email'] ?? 'not_provided',
                    'pending',
                    $responseData
                );
                
                return $this->formatResponse(
                    true,
                    200,
                    "PayPal payment request created successfully",
                    [
                        'order_id' => $responseData['id'],
                        'approval_url' => $approvalUrl,
                        'response' => $responseData
                    ]
                );
            } else {
                // Log failed payment request
                $this->logPaymentRequest(
                    'paypal',
                    $responseData['id'] ?? null,
                    $amount,
                    $paymentData['email'] ?? 'not_provided',
                    'failed',
                    $responseData
                );
                
                return $this->formatResponse(
                    false,
                    $this->responseCodes['payment_failed'],
                    "PayPal payment request failed",
                    ['response' => $responseData]
                );
            }
        } catch (Exception $e) {
            $this->logError('PayPal payment processing error', $e->getMessage(), $paymentData);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "PayPal payment processing error: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Get PayPal access token
     * 
     * @return string Access token
     * @throws Exception If access token could not be obtained
     */
    private function getPaypalAccessToken(): string {
        // Determine API URL based on environment
        $apiUrl = ($this->config['paypal']['environment'] === 'production')
            ? 'https://api.paypal.com/v1/oauth2/token'
            : 'https://api.sandbox.paypal.com/v1/oauth2/token';
        
        // Send request to PayPal
        $credentials = base64_encode($this->config['paypal']['client_id'] . ':' . $this->config['paypal']['client_secret']);
        
        $ch = curl_init($apiUrl);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Basic ' . $credentials,
            'Content-Type: application/x-www-form-urlencoded'
        ]);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, 'grant_type=client_credentials');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        // Parse response
        $responseData = json_decode($response, true);
        
        // Check if request was successful
        if ($httpCode == 200 && isset($responseData['access_token'])) {
            return $responseData['access_token'];
        } else {
            throw new Exception("Could not get PayPal access token: " . json_encode($responseData));
        }
    }
    
    /**
     * Process card payment
     * 
     * @param array $paymentData Payment details
     * @return array Payment response
     */
    private function processCardPayment(array $paymentData): array {
        try {
            // Extract required data
            $amount = $paymentData['amount'];
            $currency = $paymentData['currency'] ?? 'KES';
            $cardNumber = $paymentData['card_number'];
            $expiryMonth = $paymentData['expiry_month'];
            $expiryYear = $paymentData['expiry_year'];
            $cvv = $paymentData['cvv'];
            $cardHolderName = $paymentData['card_holder_name'];
            $email = $paymentData['email'] ?? '';
            $description = $paymentData['description'] ?? 'PesaGuru Service Payment';
            
            // Determine API URL based on environment
            $apiUrl = ($this->config['card']['environment'] === 'production')
                ? 'https://api.yourgatewayprovider.com/v1/payments'
                : 'https://sandbox.yourgatewayprovider.com/v1/payments';
            
            // Prepare request data (sanitized for security)
            $requestData = [
                'amount' => number_format($amount, 2, '.', ''),
                'currency' => $currency,
                'description' => $description,
                'metadata' => [
                    'email' => $email
                ],
                'card' => [
                    'number' => $cardNumber,
                    'exp_month' => $expiryMonth,
                    'exp_year' => $expiryYear,
                    'cvc' => $cvv,
                    'name' => $cardHolderName
                ]
            ];
            
            // Send request to payment gateway
            $ch = curl_init($apiUrl);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $this->config['card']['api_key'],
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestData));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Parse response
            $responseData = json_decode($response, true);
            
            // Check if request was successful
            if ($httpCode == 200 && isset($responseData['id']) && $responseData['status'] === 'succeeded') {
                // Log successful payment
                $this->logPaymentRequest(
                    'card',
                    $responseData['id'],
                    $amount,
                    $email,
                    'completed',
                    $responseData
                );
                
                return $this->formatResponse(
                    true,
                    200,
                    "Card payment processed successfully",
                    [
                        'transaction_id' => $responseData['id'],
                        'response' => $responseData
                    ]
                );
            } else {
                // Log failed payment
                $this->logPaymentRequest(
                    'card',
                    $responseData['id'] ?? null,
                    $amount,
                    $email,
                    'failed',
                    $responseData
                );
                
                return $this->formatResponse(
                    false,
                    $this->responseCodes['payment_failed'],
                    "Card payment failed",
                    ['response' => $responseData]
                );
            }
        } catch (Exception $e) {
            $this->logError('Card payment processing error', $e->getMessage(), $this->sanitizePaymentData($paymentData));
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "Card payment processing error: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Check the status of an M-Pesa payment
     * 
     * @param string $checkoutRequestId M-Pesa checkout request ID
     * @return array Status response
     */
    public function checkMpesaPaymentStatus(string $checkoutRequestId): array {
        try {
            // Get access token
            $accessToken = $this->getMpesaAccessToken();
            
            // Generate timestamp
            $timestamp = date('YmdHis');
            
            // Generate password
            $password = base64_encode($this->config['mpesa']['shortcode'] . $this->config['mpesa']['passkey'] . $timestamp);
            
            // Prepare request data
            $requestData = [
                'BusinessShortCode' => $this->config['mpesa']['shortcode'],
                'Password' => $password,
                'Timestamp' => $timestamp,
                'CheckoutRequestID' => $checkoutRequestId
            ];
            
            // Determine API URL based on environment
            $apiUrl = ($this->config['mpesa']['environment'] === 'production')
                ? 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
                : 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query';
            
            // Send request to M-Pesa
            $ch = curl_init($apiUrl);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json'
            ]);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($requestData));
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Parse response
            $responseData = json_decode($response, true);
            
            // Check if request was successful
            if ($httpCode == 200) {
                $resultCode = $responseData['ResultCode'] ?? -1;
                
                if ($resultCode === 0) {
                    // Payment was successful
                    $this->updatePaymentStatus($checkoutRequestId, 'completed', $responseData);
                    
                    return $this->formatResponse(
                        true,
                        200,
                        "Payment completed successfully",
                        ['response' => $responseData]
                    );
                } else if ($resultCode === 1) {
                    // Payment is still being processed
                    return $this->formatResponse(
                        true,
                        200,
                        "Payment is still being processed",
                        ['response' => $responseData]
                    );
                } else {
                    // Payment failed
                    $this->updatePaymentStatus($checkoutRequestId, 'failed', $responseData);
                    
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['payment_failed'],
                        "Payment failed: " . ($responseData['ResultDesc'] ?? "Unknown error"),
                        ['response' => $responseData]
                    );
                }
            } else {
                return $this->formatResponse(
                    false,
                    $this->responseCodes['internal_error'],
                    "Error checking payment status",
                    ['response' => $responseData]
                );
            }
        } catch (Exception $e) {
            $this->logError('Error checking M-Pesa payment status', $e->getMessage(), ['checkout_request_id' => $checkoutRequestId]);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "Error checking payment status: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Handle M-Pesa callback
     * 
     * @param array $callbackData Callback data from M-Pesa
     * @return array Response data
     */
    public function handleMpesaCallback(array $callbackData): array {
        try {
            // Extract necessary data from callback
            $resultCode = $callbackData['Body']['stkCallback']['ResultCode'];
            $checkoutRequestId = $callbackData['Body']['stkCallback']['CheckoutRequestID'];
            
            if ($resultCode === 0) {
                // Payment was successful
                $callbackMetadata = $callbackData['Body']['stkCallback']['CallbackMetadata']['Item'];
                
                // Extract values from callback metadata
                $amount = null;
                $mpesaReceiptNumber = null;
                $transactionDate = null;
                $phoneNumber = null;
                
                foreach ($callbackMetadata as $item) {
                    switch ($item['Name']) {
                        case 'Amount':
                            $amount = $item['Value'];
                            break;
                        case 'MpesaReceiptNumber':
                            $mpesaReceiptNumber = $item['Value'];
                            break;
                        case 'TransactionDate':
                            $transactionDate = $item['Value'];
                            break;
                        case 'PhoneNumber':
                            $phoneNumber = $item['Value'];
                            break;
                    }
                }
                
                // Update payment status
                $this->updatePaymentStatus($checkoutRequestId, 'completed', [
                    'receipt_number' => $mpesaReceiptNumber,
                    'transaction_date' => $transactionDate,
                    'amount' => $amount,
                    'phone_number' => $phoneNumber
                ]);
                
                // TODO: Update user subscription or service access here
                
                return $this->formatResponse(
                    true,
                    200,
                    "Payment completed successfully",
                    [
                        'transaction_id' => $checkoutRequestId,
                        'mpesa_receipt' => $mpesaReceiptNumber
                    ]
                );
            } else {
                // Payment failed
                $this->updatePaymentStatus($checkoutRequestId, 'failed', $callbackData);
                
                return $this->formatResponse(
                    false,
                    $this->responseCodes['payment_failed'],
                    "Payment failed: " . ($callbackData['Body']['stkCallback']['ResultDesc'] ?? "Unknown error")
                );
            }
        } catch (Exception $e) {
            $this->logError('Error handling M-Pesa callback', $e->getMessage(), $callbackData);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "Error handling callback: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Process a PayPal payment capture (after approval)
     * 
     * @param string $orderId PayPal order ID
     * @return array Payment response
     */
    public function capturePaypalPayment(string $orderId): array {
        try {
            // Get PayPal access token
            $accessToken = $this->getPaypalAccessToken();
            
            // Determine API URL based on environment
            $apiUrl = ($this->config['paypal']['environment'] === 'production')
                ? "https://api.paypal.com/v2/checkout/orders/{$orderId}/capture"
                : "https://api.sandbox.paypal.com/v2/checkout/orders/{$orderId}/capture";
            
            // Send request to PayPal
            $ch = curl_init($apiUrl);
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                'Authorization: Bearer ' . $accessToken,
                'Content-Type: application/json',
                'Prefer: return=representation'
            ]);
            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, '{}');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            // Parse response
            $responseData = json_decode($response, true);
            
            // Check if request was successful
            if ($httpCode == 201 && isset($responseData['id']) && $responseData['status'] === 'COMPLETED') {
                // Update payment status
                $this->updatePaymentStatus($orderId, 'completed', $responseData);
                
                // TODO: Update user subscription or service access here
                
                return $this->formatResponse(
                    true,
                    200,
                    "Payment completed successfully",
                    [
                        'transaction_id' => $orderId,
                        'response' => $responseData
                    ]
                );
            } else {
                // Payment failed
                $this->updatePaymentStatus($orderId, 'failed', $responseData);
                
                return $this->formatResponse(
                    false,
                    $this->responseCodes['payment_failed'],
                    "Payment capture failed",
                    ['response' => $responseData]
                );
            }
        } catch (Exception $e) {
            $this->logError('Error capturing PayPal payment', $e->getMessage(), ['order_id' => $orderId]);
            
            return $this->formatResponse(
                false,
                $this->responseCodes['internal_error'],
                "Error capturing payment: " . $e->getMessage()
            );
        }
    }
    
    /**
     * Validate payment data based on payment method
     * 
     * @param string $paymentMethod Payment method
     * @param array $paymentData Payment data
     * @return array Validation result
     */
    private function validatePaymentData(string $paymentMethod, array $paymentData): array {
        $requiredFields = [];
        
        switch ($paymentMethod) {
            case 'mpesa':
                $requiredFields = ['phone_number', 'amount'];
                break;
                
            case 'paypal':
                $requiredFields = ['amount', 'return_url', 'cancel_url'];
                break;
                
            case 'card':
                $requiredFields = ['amount', 'card_number', 'expiry_month', 'expiry_year', 'cvv', 'card_holder_name'];
                break;
        }
        
        // Check if all required fields are present
        foreach ($requiredFields as $field) {
            if (!isset($paymentData[$field]) || empty($paymentData[$field])) {
                return $this->formatResponse(
                    false,
                    $this->responseCodes['invalid_method'],
                    "Missing required field: {$field}"
                );
            }
        }
        
        // Specific validations based on payment method
        switch ($paymentMethod) {
            case 'mpesa':
                // Validate phone number (Kenyan format)
                if (!preg_match('/^(?:\+254|254|0)?[7|1][0-9]{8}$/', $paymentData['phone_number'])) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid phone number format"
                    );
                }
                
                // Validate amount
                if (!is_numeric($paymentData['amount']) || $paymentData['amount'] <= 0) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid amount"
                    );
                }
                break;
                
            case 'card':
                // Validate card number (basic validation)
                if (!preg_match('/^[0-9]{13,19}$/', $paymentData['card_number'])) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid card number"
                    );
                }
                
                // Validate expiry month
                if (!is_numeric($paymentData['expiry_month']) || $paymentData['expiry_month'] < 1 || $paymentData['expiry_month'] > 12) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid expiry month"
                    );
                }
                
                // Validate expiry year
                $currentYear = (int)date('Y');
                if (!is_numeric($paymentData['expiry_year']) || $paymentData['expiry_year'] < $currentYear) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid expiry year"
                    );
                }
                
                // Validate CVV
                if (!preg_match('/^[0-9]{3,4}$/', $paymentData['cvv'])) {
                    return $this->formatResponse(
                        false,
                        $this->responseCodes['invalid_method'],
                        "Invalid CVV"
                    );
                }
                break;
        }
        
        return $this->formatResponse(true, 200, "Validation successful");
    }
    
    /**
     * Format a Kenyan phone number to the required format (254XXXXXXXXX)
     * 
     * @param string $phoneNumber Phone number
     * @return string Formatted phone number
     */
    private function formatPhoneNumber(string $phoneNumber): string {
        // Remove any non-numeric characters
        $phoneNumber = preg_replace('/[^0-9]/', '', $phoneNumber);
        
        // Check if the number starts with '0' (e.g., 0712345678)
        if (strlen($phoneNumber) === 10 && $phoneNumber[0] === '0') {
            $phoneNumber = '254' . substr($phoneNumber, 1);
        }
        
        // Check if the number starts with '7' or '1' (e.g., 712345678)
        if (strlen($phoneNumber) === 9 && ($phoneNumber[0] === '7' || $phoneNumber[0] === '1')) {
            $phoneNumber = '254' . $phoneNumber;
        }
        
        // If the number already starts with '254', return as is
        if (strlen($phoneNumber) === 12 && substr($phoneNumber, 0, 3) === '254') {
            return $phoneNumber;
        }
        
        // If the number starts with '+254', remove the '+' sign
        if (strlen($phoneNumber) === 13 && substr($phoneNumber, 0, 4) === '+254') {
            return substr($phoneNumber, 1);
        }
        
        return $phoneNumber;
    }
    
    /**
     * Log a payment request
     * 
     * @param string $paymentMethod Payment method
     * @param string|null $transactionId Transaction ID
     * @param float $amount Amount
     * @param string $customerReference Customer reference (phone, email, etc.)
     * @param string $status Payment status
     * @param array $responseData Response data from the payment gateway
     * @return bool Success status
     */
    private function logPaymentRequest(string $paymentMethod, ?string $transactionId, float $amount, string $customerReference, string $status, array $responseData): bool {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO payment_transactions (
                    payment_method, 
                    transaction_id, 
                    amount, 
                    customer_reference, 
                    status, 
                    response_data, 
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, NOW())
            ");
            
            return $stmt->execute([
                $paymentMethod,
                $transactionId,
                $amount,
                $customerReference,
                $status,
                json_encode($responseData)
            ]);
        } catch (Exception $e) {
            $this->logError('Error logging payment request', $e->getMessage(), [
                'payment_method' => $paymentMethod,
                'transaction_id' => $transactionId,
                'amount' => $amount,
                'customer_reference' => $customerReference,
                'status' => $status
            ]);
            
            return false;
        }
    }
    
    /**
     * Update payment status
     * 
     * @param string $transactionId Transaction ID
     * @param string $status New status
     * @param array $responseData Response data from the payment gateway
     * @return bool Success status
     */
    private function updatePaymentStatus(string $transactionId, string $status, array $responseData): bool {
        try {
            $stmt = $this->db->prepare("
                UPDATE payment_transactions 
                SET status = ?, 
                    response_data = ?, 
                    updated_at = NOW() 
                WHERE transaction_id = ?
            ");
            
            return $stmt->execute([
                $status,
                json_encode($responseData),
                $transactionId
            ]);
        } catch (Exception $e) {
            $this->logError('Error updating payment status', $e->getMessage(), [
                'transaction_id' => $transactionId,
                'status' => $status
            ]);
            
            return false;
        }
    }
    
    /**
     * Log an error
     * 
     * @param string $errorType Error type
     * @param string $errorMessage Error message
     * @param array $contextData Context data
     * @return bool Success status
     */
    private function logError(string $errorType, string $errorMessage, array $contextData = []): bool {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO error_logs (
                    error_type, 
                    error_message, 
                    context_data, 
                    created_at
                ) VALUES (?, ?, ?, NOW())
            ");
            
            return $stmt->execute([
                $errorType,
                $errorMessage,
                json_encode($contextData)
            ]);
        } catch (Exception $e) {
            // If we can't log to the database, log to the PHP error log
            error_log("Payment Processing Error: {$errorType} - {$errorMessage}");
            
            return false;
        }
    }
    
    /**
     * Format a response
     * 
     * @param bool $success Success status
     * @param int $code Response code
     * @param string $message Response message
     * @param array $data Response data
     * @return array Formatted response
     */
    private function formatResponse(bool $success, int $code, string $message, array $data = []): array {
        return [
            'success' => $success,
            'code' => $code,
            'message' => $message,
            'data' => $data
        ];
    }
    
    /**
     * Sanitize payment data for logging
     * 
     * @param array $paymentData Payment data
     * @return array Sanitized payment data
     */
    private function sanitizePaymentData(array $paymentData): array {
        $sanitized = $paymentData;
        
        // Mask sensitive fields
        if (isset($sanitized['card_number'])) {
            $sanitized['card_number'] = '************' . substr($sanitized['card_number'], -4);
        }
        
        if (isset($sanitized['cvv'])) {
            $sanitized['cvv'] = '***';
        }
        
        return $sanitized;
    }
}