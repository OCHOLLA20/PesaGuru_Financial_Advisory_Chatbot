<?php
namespace App\Services\Auth;

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

class TokenService {
    private $secretKey;
    private $tokenExpiry;
    private $algorithm;
    private $blacklistedTokens;
    
    public function __construct() {
        // Load configuration from environment or config file
        $this->secretKey = $_ENV['JWT_SECRET_KEY'] ?? 'pesaguru_secret_key_change_in_production';
        $this->tokenExpiry = $_ENV['JWT_EXPIRY'] ?? 3600; // 1 hour by default
        $this->algorithm = 'HS256';
        $this->blacklistedTokens = [];
    }
    
    /**
     * Generate a JWT token
     * @param array $payload Token payload
     * @return string Generated token
     */
    public function generateToken($payload) {
        $issuedAt = time();
        $expirationTime = $issuedAt + $this->tokenExpiry;
        
        $tokenPayload = array_merge(
            $payload,
            [
                'iat' => $issuedAt,        // Issued at: time when the token was generated
                'exp' => $expirationTime,  // Expiration time
                'jti' => uniqid()          // Unique token ID
            ]
        );
        
        return JWT::encode($tokenPayload, $this->secretKey, $this->algorithm);
    }
    
    /**
     * Verify a JWT token
     * @param string $token JWT token
     * @return array|bool Decoded payload if valid, false otherwise
     */
    public function verifyToken($token) {
        try {
            // Check if token is blacklisted
            if ($this->isTokenBlacklisted($token)) {
                return false;
            }
            
            $decoded = JWT::decode($token, new Key($this->secretKey, $this->algorithm));
            return (array) $decoded;
        } catch (\Exception $e) {
            // Token is invalid or expired
            return false;
        }
    }
    
    /**
     * Invalidate a token (add to blacklist)
     * @param string $token JWT token
     * @return bool Success status
     */
    public function invalidateToken($token) {
        try {
            // Decode token to get expiry time
            $decoded = JWT::decode($token, new Key($this->secretKey, $this->algorithm));
            $expiry = $decoded->exp;
            
            // Add token to blacklist
            $this->blacklistedTokens[$token] = $expiry;
            
            // In a real application, you would store this in a database or Redis
            return true;
        } catch (\Exception $e) {
            // Token is already invalid, no need to blacklist
            return false;
        }
    }
    
    /**
     * Invalidate all tokens for a user
     * @param int $userId User ID
     * @return bool Success status
     */
    public function invalidateAllUserTokens($userId) {
        // In a real application, you would query the database for all active tokens
        // and add them to the blacklist
        // For this example, we'll just return true
        return true;
    }
    
    /**
     * Check if a token is blacklisted
     * @param string $token JWT token
     * @return bool Blacklist status
     */
    private function isTokenBlacklisted($token) {
        return isset($this->blacklistedTokens[$token]);
    }
    
    /**
     * Generate a password reset token
     * @param int $userId User ID
     * @return string Reset token
     */
    public function generateResetToken($userId) {
        $payload = [
            'user_id' => $userId,
            'type' => 'password_reset',
            'exp' => time() + 3600 // 1 hour expiry
        ];
        
        return $this->generateToken($payload);
    }
    
    /**
     * Verify a password reset token
     * @param string $token Reset token
     * @return int|bool User ID if valid, false otherwise
     */
    public function verifyResetToken($token) {
        $payload = $this->verifyToken($token);
        
        if (!$payload || $payload['type'] !== 'password_reset') {
            return false;
        }
        
        return $payload['user_id'];
    }
}