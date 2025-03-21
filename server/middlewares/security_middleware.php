<?php
/**
 * PesaGuru Security Middleware
 * 
 * This middleware implements security measures for the PesaGuru financial advisory chatbot,
 * including protection against common web vulnerabilities, secure headers,
 * input sanitization, and compliance with Kenyan data protection regulations.
 * 
 * @package PesaGuru
 * @subpackage Middleware
 */

class SecurityMiddleware
{
    /**
     * Security settings loaded from configuration
     */
    private $securityConfig;
    
    /**
     * Request method
     */
    private $method;
    
    /**
     * Request URI
     */
    private $uri;
    
    /**
     * CSRF token from session
     */
    private $csrfToken;
    
    /**
     * Paths that are exempt from CSRF protection
     */
    private $csrfExemptPaths = [
        '/api/webhook/', // External service webhooks
        '/api/chatbot/interactions/' // Chatbot interactions
    ];
    
    /**
     * Initialize the security middleware
     */
    public function __construct()
    {
        // Load security configuration
        $this->loadSecurityConfig();
        
        // Setup request info
        $this->method = $_SERVER['REQUEST_METHOD'] ?? '';
        $this->uri = $_SERVER['REQUEST_URI'] ?? '';
        
        // Initialize session if not already started
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }
        
        // Initialize CSRF token if needed
        if (!isset($_SESSION['csrf_token'])) {
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        }
        
        $this->csrfToken = $_SESSION['csrf_token'];
    }
    
    /**
     * Load security configuration
     */
    private function loadSecurityConfig()
    {
        $configPath = __DIR__ . '/../config/security_config.php';
        
        if (file_exists($configPath)) {
            $this->securityConfig = require $configPath;
        } else {
            // Default settings if config file not found
            $this->securityConfig = [
                'enable_xss_protection' => true,
                'enable_csrf_protection' => true,
                'enable_clickjacking_protection' => true,
                'enable_content_type_protection' => true,
                'enable_strict_transport_security' => true,
                'enable_content_security_policy' => true,
                'allowed_origins' => ['https://pesaguru.co.ke'],
                'jwt_secret' => getenv('JWT_SECRET') ?: 'default_jwt_secret_replace_in_production',
                'aes_encryption_key' => getenv('AES_ENCRYPTION_KEY') ?: 'default_aes_key_replace_in_production',
                'auth_timeout' => 3600, // 1 hour
                'enable_rate_limiting' => true,
                'max_requests_per_minute' => 60
            ];
        }
    }
    
    /**
     * Process the request through the security middleware
     * 
     * @return bool True if the request passes security checks, false otherwise
     */
    public function process()
    {
        // Set secure headers
        $this->setSecureHeaders();
        
        // Sanitize input
        $this->sanitizeInput();
        
        // Verify CSRF token for state-changing requests
        if (!$this->verifyCsrfToken()) {
            $this->respondWithError(403, 'CSRF token validation failed');
            return false;
        }
        
        // Validate content type for API requests
        if (!$this->validateContentType()) {
            $this->respondWithError(415, 'Unsupported content type');
            return false;
        }
        
        // Log security-relevant information
        $this->logSecurityEvent('SecurityMiddleware passed', 'info');
        
        return true;
    }
    
    /**
     * Set security-related HTTP headers
     */
    private function setSecureHeaders()
    {
        // Prevent browsers from MIME-sniffing
        header('X-Content-Type-Options: nosniff');
        
        // Strict Transport Security
        if ($this->securityConfig['enable_strict_transport_security']) {
            header('Strict-Transport-Security: max-age=31536000; includeSubDomains');
        }
        
        // Cross-Site Scripting (XSS) Protection
        if ($this->securityConfig['enable_xss_protection']) {
            header('X-XSS-Protection: 1; mode=block');
        }
        
        // Clickjacking Protection
        if ($this->securityConfig['enable_clickjacking_protection']) {
            header('X-Frame-Options: SAMEORIGIN');
        }
        
        // Content Security Policy
        if ($this->securityConfig['enable_content_security_policy']) {
            header("Content-Security-Policy: default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; connect-src 'self' https://api.pesaguru.co.ke; img-src 'self' data:; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com");
        }
        
        // CORS headers for API
        if (strpos($this->uri, '/api/') === 0) {
            $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
            
            if (in_array($origin, $this->securityConfig['allowed_origins'])) {
                header("Access-Control-Allow-Origin: $origin");
                header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
                header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");
                header("Access-Control-Allow-Credentials: true");
                header("Access-Control-Max-Age: 86400"); // 24 hours
            }
            
            // Handle preflight requests
            if ($this->method === 'OPTIONS') {
                http_response_code(204);
                exit;
            }
        }
        
        // Ensure no caching of sensitive data
        if (strpos($this->uri, '/api/user/') === 0 || 
            strpos($this->uri, '/api/financial/') === 0 || 
            strpos($this->uri, '/api/chatbot/') === 0) {
            header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
            header("Pragma: no-cache");
            header("Expires: 0");
        }
    }
    
    /**
     * Sanitize input data to prevent XSS and SQL injection
     */
    private function sanitizeInput()
    {
        // Sanitize GET parameters
        foreach ($_GET as $key => $value) {
            $_GET[$key] = $this->sanitizeValue($value);
        }
        
        // Sanitize POST parameters
        foreach ($_POST as $key => $value) {
            $_POST[$key] = $this->sanitizeValue($value);
        }
        
        // Handle JSON input for API requests
        $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
        if (strpos($contentType, 'application/json') !== false) {
            $jsonInput = file_get_contents('php://input');
            if (!empty($jsonInput)) {
                $jsonData = json_decode($jsonInput, true);
                if (json_last_error() === JSON_ERROR_NONE && is_array($jsonData)) {
                    $_POST = array_merge($_POST, $this->sanitizeArray($jsonData));
                }
            }
        }
    }
    
    /**
     * Sanitize a value to prevent XSS attacks
     * 
     * @param mixed $value The value to sanitize
     * @return mixed The sanitized value
     */
    private function sanitizeValue($value)
    {
        if (is_array($value)) {
            return $this->sanitizeArray($value);
        }
        
        if (is_string($value)) {
            // Convert special characters to HTML entities
            return htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
        }
        
        return $value;
    }
    
    /**
     * Recursively sanitize an array of values
     * 
     * @param array $array The array to sanitize
     * @return array The sanitized array
     */
    private function sanitizeArray(array $array)
    {
        foreach ($array as $key => $value) {
            $array[$key] = $this->sanitizeValue($value);
        }
        
        return $array;
    }
    
    /**
     * Verify CSRF token for state-changing requests
     * 
     * @return bool True if CSRF validation passes or is not required, false otherwise
     */
    private function verifyCsrfToken()
    {
        // Skip CSRF verification for exempt paths
        foreach ($this->csrfExemptPaths as $path) {
            if (strpos($this->uri, $path) === 0) {
                return true;
            }
        }
        
        // Skip CSRF check for GET, HEAD, OPTIONS requests (they should be idempotent)
        if (in_array($this->method, ['GET', 'HEAD', 'OPTIONS'])) {
            return true;
        }
        
        // For state-changing requests, verify the CSRF token
        if ($this->securityConfig['enable_csrf_protection']) {
            $requestToken = $_POST['csrf_token'] ?? $_SERVER['HTTP_X_CSRF_TOKEN'] ?? null;
            
            if (!$requestToken || !hash_equals($this->csrfToken, $requestToken)) {
                $this->logSecurityEvent('CSRF token validation failed', 'warning');
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Validate the content type for API requests
     * 
     * @return bool True if content type is valid or check is not needed, false otherwise
     */
    private function validateContentType()
    {
        // Only check content type for API requests with a body
        if (strpos($this->uri, '/api/') === 0 && 
            in_array($this->method, ['POST', 'PUT', 'PATCH']) && 
            $this->securityConfig['enable_content_type_protection']) {
            
            $contentType = $_SERVER['CONTENT_TYPE'] ?? '';
            
            // Accept application/json or multipart/form-data (for file uploads)
            if (strpos($contentType, 'application/json') === false && 
                strpos($contentType, 'multipart/form-data') === false && 
                strpos($contentType, 'application/x-www-form-urlencoded') === false) {
                
                $this->logSecurityEvent('Invalid content type: ' . $contentType, 'warning');
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Encrypt sensitive data using AES-256-GCM
     * 
     * @param string $data The data to encrypt
     * @return string The encrypted data (base64 encoded)
     */
    public function encryptData($data)
    {
        if (empty($data)) {
            return '';
        }
        
        $key = base64_decode($this->securityConfig['aes_encryption_key']);
        $iv = random_bytes(12); // GCM recommends 12 bytes for IV
        
        // Encrypt the data
        $encrypted = openssl_encrypt(
            $data,
            'aes-256-gcm',
            $key,
            OPENSSL_RAW_DATA,
            $iv,
            $tag
        );
        
        // Combine IV, ciphertext, and tag for storage/transmission
        $result = base64_encode($iv . $encrypted . $tag);
        
        return $result;
    }
    
    /**
     * Decrypt AES-256-GCM encrypted data
     * 
     * @param string $encryptedData The encrypted data (base64 encoded)
     * @return string|false The decrypted data, or false on failure
     */
    public function decryptData($encryptedData)
    {
        if (empty($encryptedData)) {
            return '';
        }
        
        $key = base64_decode($this->securityConfig['aes_encryption_key']);
        $decoded = base64_decode($encryptedData);
        
        // Extract components
        $iv = substr($decoded, 0, 12);
        $tag = substr($decoded, -16);
        $ciphertext = substr($decoded, 12, -16);
        
        // Decrypt the data
        $decrypted = openssl_decrypt(
            $ciphertext,
            'aes-256-gcm',
            $key,
            OPENSSL_RAW_DATA,
            $iv,
            $tag
        );
        
        return $decrypted;
    }
    
    /**
     * Verify JWT token from Authorization header
     * 
     * @return array|false The decoded token payload, or false if verification fails
     */
    public function verifyJwtToken()
    {
        $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        
        if (empty($authHeader) || strpos($authHeader, 'Bearer ') !== 0) {
            return false;
        }
        
        $token = substr($authHeader, 7);
        
        // Split the token
        $tokenParts = explode('.', $token);
        if (count($tokenParts) != 3) {
            return false;
        }
        
        $header = json_decode(base64_decode($tokenParts[0]), true);
        $payload = json_decode(base64_decode($tokenParts[1]), true);
        $signature = $tokenParts[2];
        
        // Verify expiration
        if (isset($payload['exp']) && $payload['exp'] < time()) {
            $this->logSecurityEvent('JWT token expired', 'warning');
            return false;
        }
        
        // Verify signature
        $base64UrlHeader = $this->base64UrlEncode(json_encode($header));
        $base64UrlPayload = $this->base64UrlEncode(json_encode($payload));
        $data = $base64UrlHeader . '.' . $base64UrlPayload;
        $signature = $this->base64UrlDecode($signature);
        
        $expectedSignature = hash_hmac('sha256', $data, $this->securityConfig['jwt_secret'], true);
        
        if (!hash_equals($expectedSignature, $signature)) {
            $this->logSecurityEvent('JWT signature verification failed', 'warning');
            return false;
        }
        
        return $payload;
    }
    
    /**
     * Generate a JWT token
     * 
     * @param array $payload Data to include in the token
     * @param int $expiry Expiry time in seconds from now
     * @return string The JWT token
     */
    public function generateJwtToken(array $payload, $expiry = null)
    {
        if ($expiry === null) {
            $expiry = $this->securityConfig['auth_timeout'];
        }
        
        // Set standard claims
        $payload = array_merge($payload, [
            'iss' => 'pesaguru.co.ke',
            'iat' => time(),
            'exp' => time() + $expiry
        ]);
        
        // Create JWT parts
        $header = [
            'typ' => 'JWT',
            'alg' => 'HS256'
        ];
        
        $base64UrlHeader = $this->base64UrlEncode(json_encode($header));
        $base64UrlPayload = $this->base64UrlEncode(json_encode($payload));
        $data = $base64UrlHeader . '.' . $base64UrlPayload;
        $signature = hash_hmac('sha256', $data, $this->securityConfig['jwt_secret'], true);
        $base64UrlSignature = $this->base64UrlEncode($signature);
        
        return $data . '.' . $base64UrlSignature;
    }
    
    /**
     * Base64Url encode data
     * 
     * @param string $data The data to encode
     * @return string The encoded data
     */
    private function base64UrlEncode($data)
    {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    /**
     * Base64Url decode data
     * 
     * @param string $data The data to decode
     * @return string The decoded data
     */
    private function base64UrlDecode($data)
    {
        return base64_decode(strtr($data, '-_', '+/'));
    }
    
    /**
     * Log security-related events
     * 
     * @param string $message The message to log
     * @param string $level The log level (info, warning, error, critical)
     * @param array $context Additional context data
     */
    public function logSecurityEvent($message, $level = 'info', array $context = [])
    {
        // Basic context information
        $baseContext = [
            'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
            'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
            'uri' => $this->uri,
            'method' => $this->method,
            'timestamp' => date('Y-m-d H:i:s')
        ];
        
        $context = array_merge($baseContext, $context);
        
        // Format log entry
        $logEntry = json_encode([
            'level' => $level,
            'message' => $message,
            'context' => $context
        ]);
        
        // Write to security log file
        $logDir = __DIR__ . '/../../logs/security';
        
        // Create log directory if it doesn't exist
        if (!file_exists($logDir)) {
            mkdir($logDir, 0755, true);
        }
        
        $logFile = $logDir . '/' . date('Y-m-d') . '_security.log';
        file_put_contents($logFile, $logEntry . PHP_EOL, FILE_APPEND);
        
        // For critical events, also send an alert (implement this based on your notification system)
        if ($level === 'critical') {
            $this->sendSecurityAlert($message, $context);
        }
    }
    
    /**
     * Send a security alert for critical events
     * 
     * @param string $message The alert message
     * @param array $context Additional context data
     */
    private function sendSecurityAlert($message, array $context)
    {
        // Implementation depends on your notification system
        // For example, email, SMS, or integration with a security monitoring service
        
        // Placeholder for demonstration
        if (function_exists('error_log')) {
            error_log('SECURITY ALERT: ' . $message . ' - ' . json_encode($context));
        }
        
        // In a real implementation, you would call your notification service here
        // Example: $notificationService->sendAlert('security', $message, $context);
    }
    
    /**
     * Respond with an error in the appropriate format
     * 
     * @param int $statusCode HTTP status code
     * @param string $message Error message
     */
    private function respondWithError($statusCode, $message)
    {
        http_response_code($statusCode);
        
        // Determine response format based on Accept header or URI
        if (strpos($this->uri, '/api/') === 0 || 
            (isset($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false)) {
            
            header('Content-Type: application/json');
            echo json_encode([
                'status' => 'error',
                'code' => $statusCode,
                'message' => $message
            ]);
        } else {
            // HTML response for web pages
            echo "<!DOCTYPE html>
            <html>
            <head>
                <title>Error $statusCode</title>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }
                    .error-container { max-width: 600px; margin: 0 auto; background: #f8f8f8; padding: 20px; border-radius: 5px; border-left: 5px solid #e74c3c; }
                    h1 { margin-top: 0; color: #e74c3c; }
                </style>
            </head>
            <body>
                <div class='error-container'>
                    <h1>Error $statusCode</h1>
                    <p>$message</p>
                    <p><a href='/'>&larr; Return to Homepage</a></p>
                </div>
            </body>
            </html>";
        }
        
        exit;
    }
    
    /**
     * Generate a strong random token
     * 
     * @param int $length The length of the token
     * @return string The generated token
     */
    public function generateSecureToken($length = 32)
    {
        return bin2hex(random_bytes($length / 2));
    }
    
    /**
     * Get the CSRF token for the current session
     * 
     * @return string The CSRF token
     */
    public function getCsrfToken()
    {
        return $this->csrfToken;
    }
    
    /**
     * Render a CSRF token field for inclusion in forms
     * 
     * @return string HTML for a hidden input field with the CSRF token
     */
    public function renderCsrfTokenField()
    {
        return '<input type="hidden" name="csrf_token" value="' . $this->csrfToken . '">';
    }
    
    /**
     * Check if the current user has the required role or permission
     * 
     * @param string|array $requiredRole The role or permission required
     * @return bool True if the user has the required role, false otherwise
     */
    public function checkUserRole($requiredRole)
    {
        // Get JWT payload
        $payload = $this->verifyJwtToken();
        
        if (!$payload || !isset($payload['role'])) {
            return false;
        }
        
        $userRole = $payload['role'];
        
        // Check if user has the required role
        if (is_array($requiredRole)) {
            return in_array($userRole, $requiredRole);
        }
        
        return $userRole === $requiredRole;
    }
    
    /**
     * Enforce HTTPS - redirect to HTTPS if the request is HTTP
     */
    public function enforceHttps()
    {
        if (empty($_SERVER['HTTPS']) || $_SERVER['HTTPS'] === 'off') {
            $httpsUrl = 'https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
            header('Location: ' . $httpsUrl, true, 301);
            exit;
        }
    }
    
    /**
     * Implementation of Kenya's Data Protection Act, 2019 compliance
     * 
     * @param string $dataType Type of data being processed
     * @param string $purpose Purpose for processing the data
     * @return bool True if processing is compliant, false otherwise
     */
    public function checkPdpaCompliance($dataType, $purpose)
    {
        // Types of personal data as per Kenya's Data Protection Act
        $sensitiveDataTypes = [
            'health', 'biometric', 'genetic', 'ethnic_origin', 'political_opinion',
            'religious_belief', 'financial_data', 'id_numbers'
        ];
        
        // Valid purposes for data processing as per the Act
        $validPurposes = [
            'consent', 'contract', 'legal_obligation', 'vital_interests',
            'public_interest', 'legitimate_interests'
        ];
        
        // Check if user consent is obtained for sensitive data
        $isSensitiveData = in_array($dataType, $sensitiveDataTypes);
        $hasConsent = $purpose === 'consent' && isset($_SESSION['data_consent']) && $_SESSION['data_consent'] === true;
        
        // For sensitive data, explicit consent is required
        if ($isSensitiveData && !$hasConsent) {
            $this->logSecurityEvent("PDPA compliance failed: No consent for sensitive data type '$dataType'", 'warning');
            return false;
        }
        
        // Check if purpose is valid
        if (!in_array($purpose, $validPurposes)) {
            $this->logSecurityEvent("PDPA compliance failed: Invalid purpose '$purpose'", 'warning');
            return false;
        }
        
        return true;
    }
}