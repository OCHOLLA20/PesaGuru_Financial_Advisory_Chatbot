<?php

namespace PesaGuru\Server\Middlewares;

// Adjust require paths based on your actual file structure
require_once __DIR__ . '/../config/auth.php';

class AuthMiddleware {
    /**
     * JWT secret key - should come from config
     */
    private $jwtSecretKey;
    
    /**
     * Database connection
     */
    private $db;
    
    /**
     * Constructor
     */
    public function __construct() {
        global $config;
        $this->jwtSecretKey = $config['jwt_secret'] ?? 'pesaguru-secret-key';
        $this->db = require_once __DIR__ . '/../config/db.php';
    }
    
    /**
     * Handle authentication check
     * 
     * Verifies the JWT token from Authorization header and ensures user is authenticated
     * 
     * @param object $request The request object
     * @param object $response The response object
     * @param callable $next The next middleware
     * @return mixed
     */
    public function handle($request, $response, $next) {
        // Get authorization header
        $authHeader = $this->getAuthorizationHeader();
        
        if (!$authHeader) {
            return $this->respondUnauthorized($response, 'Authorization header is missing');
        }
        
        // Extract token from Bearer format
        $token = $this->extractTokenFromHeader($authHeader);
        
        if (!$token) {
            return $this->respondUnauthorized($response, 'Invalid token format');
        }
        
        try {
            // Verify and decode the token
            $decodedToken = $this->verifyToken($token);
            
            if (!$decodedToken) {
                return $this->respondUnauthorized($response, 'Invalid token');
            }
            
            // Check if token is expired
            if ($this->isTokenExpired($decodedToken)) {
                return $this->respondUnauthorized($response, 'Token has expired');
            }
            
            // Fetch user from database
            $userId = $decodedToken->user_id;
            $user = $this->getUserById($userId);
            
            if (!$user) {
                return $this->respondUnauthorized($response, 'User not found');
            }
            
            // Add user to request for route handlers
            $request->user = $user;
            
            // Check if user is active
            if (!$user['is_active']) {
                return $this->respondUnauthorized($response, 'User account is inactive');
            }
            
            // Log the authentication for audit purposes
            $this->logAuthentication($userId);
            
            // Proceed to next middleware or route handler
            return $next($request, $response);
            
        } catch (\Exception $e) {
            // Log the error
            error_log('Authentication error: ' . $e->getMessage());
            return $this->respondUnauthorized($response, 'Authentication failed');
        }
    }
    
    /**
     * Get the Authorization header
     * 
     * @return string|null
     */
    private function getAuthorizationHeader() {
        $headers = null;
        
        if (isset($_SERVER['Authorization'])) {
            $headers = trim($_SERVER['Authorization']);
        } elseif (isset($_SERVER['HTTP_AUTHORIZATION'])) {
            $headers = trim($_SERVER['HTTP_AUTHORIZATION']);
        } elseif (function_exists('apache_request_headers')) {
            $requestHeaders = apache_request_headers();
            if (isset($requestHeaders['Authorization'])) {
                $headers = trim($requestHeaders['Authorization']);
            }
        }
        
        return $headers;
    }
    
    /**
     * Extract token from Authorization header
     * 
     * @param string $authHeader
     * @return string|null
     */
    private function extractTokenFromHeader($authHeader) {
        if (!empty($authHeader)) {
            if (preg_match('/Bearer\s(\S+)/', $authHeader, $matches)) {
                return $matches[1];
            }
        }
        
        return null;
    }
    
    /**
     * Verify and decode JWT token
     * 
     * @param string $token
     * @return object|bool Decoded token payload or false if invalid
     */
    private function verifyToken($token) {
        list($header, $payload, $signature) = explode('.', $token);
        
        // Decode header and payload
        $headerDecoded = json_decode(base64_decode($header));
        $payloadDecoded = json_decode(base64_decode($payload));
        
        // Generate a signature to verify
        $dataToSign = $header . '.' . $payload;
        $expectedSignature = hash_hmac('sha256', $dataToSign, $this->jwtSecretKey, true);
        $expectedSignature = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($expectedSignature));
        
        // Verify signature
        if ($signature !== $expectedSignature) {
            return false;
        }
        
        return $payloadDecoded;
    }
    
    /**
     * Check if token is expired
     * 
     * @param object $decodedToken
     * @return bool
     */
    private function isTokenExpired($decodedToken) {
        $now = time();
        return isset($decodedToken->exp) && $decodedToken->exp < $now;
    }
    
    /**
     * Get user by ID from database
     * 
     * @param int $userId
     * @return array|bool User data or false if not found
     */
    private function getUserById($userId) {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE id = ? AND is_deleted = 0');
        $stmt->execute([$userId]);
        $user = $stmt->fetch(\PDO::FETCH_ASSOC);
        
        return $user ?: false;
    }
    
    /**
     * Log authentication attempt
     * 
     * @param int $userId
     * @return void
     */
    private function logAuthentication($userId) {
        // Get client IP address
        $ipAddress = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        
        // Get user agent
        $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
        
        // Log authentication in database
        $stmt = $this->db->prepare(
            'INSERT INTO user_activity_logs (user_id, activity_type, description, ip_address, user_agent, created_at) 
             VALUES (?, ?, ?, ?, ?, NOW())'
        );
        
        $stmt->execute([
            $userId,
            'authentication',
            'User authenticated',
            $ipAddress,
            $userAgent
        ]);
    }
    
    /**
     * Respond with unauthorized status
     * 
     * @param object $response
     * @param string $message
     * @return object
     */
    private function respondUnauthorized($response, $message) {
        $response->setStatusCode(401);
        $response->setHeader('Content-Type', 'application/json');
        $response->setBody(json_encode([
            'status' => 'error',
            'message' => $message
        ]));
        
        return $response;
    }
    
    /**
     * Check if user has required permission
     * 
     * @param object $request
     * @param object $response
     * @param string $permission
     * @return bool
     */
    public function hasPermission($request, $response, $permission) {
        if (!isset($request->user)) {
            return false;
        }
        
        // Get user permissions from database
        $stmt = $this->db->prepare(
            'SELECT p.permission_name 
             FROM user_permissions up
             JOIN permissions p ON up.permission_id = p.id
             WHERE up.user_id = ?'
        );
        
        $stmt->execute([$request->user['id']]);
        $permissions = $stmt->fetchAll(\PDO::FETCH_COLUMN);
        
        return in_array($permission, $permissions);
    }
    
    /**
     * Middleware for admin-only routes
     * 
     * @param object $request
     * @param object $response
     * @param callable $next
     * @return mixed
     */
    public function adminOnly($request, $response, $next) {
        if (!isset($request->user) || $request->user['role'] !== 'admin') {
            $response->setStatusCode(403);
            $response->setHeader('Content-Type', 'application/json');
            $response->setBody(json_encode([
                'status' => 'error',
                'message' => 'Access denied. Admin privileges required.'
            ]));
            
            return $response;
        }
        
        return $next($request, $response);
    }
    
    /**
     * Generate a new JWT token
     * 
     * @param array $payload The token payload data
     * @param int $expiry Expiration time in seconds (default: 3600 = 1 hour)
     * @return string The JWT token
     */
    public function generateToken($payload, $expiry = 3600) {
        // Add issued at and expiration timestamps
        $payload['iat'] = time();
        $payload['exp'] = time() + $expiry;
        
        // Encode Header
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $header = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($header));
        
        // Encode Payload
        $payloadEncoded = json_encode($payload);
        $payloadEncoded = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($payloadEncoded));
        
        // Create Signature
        $signature = hash_hmac('sha256', $header . '.' . $payloadEncoded, $this->jwtSecretKey, true);
        $signature = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($signature));
        
        // Create JWT
        return $header . '.' . $payloadEncoded . '.' . $signature;
    }
    
    /**
     * Refresh the token if needed
     * 
     * @param object $response
     * @param object $decodedToken
     * @return object
     */
    public function refreshTokenIfNeeded($response, $decodedToken) {
        // Check if token is close to expiration (less than 15 minutes)
        $tokenExp = $decodedToken->exp ?? 0;
        $timeUntilExpiration = $tokenExp - time();
        
        // If token will expire in less than 15 minutes, refresh it
        if ($timeUntilExpiration > 0 && $timeUntilExpiration < 900) {
            $userId = $decodedToken->user_id;
            $newToken = $this->generateToken(['user_id' => $userId]);
            
            // Add refreshed token to response header
            $response->setHeader('X-Refresh-Token', $newToken);
        }
        
        return $response;
    }
}