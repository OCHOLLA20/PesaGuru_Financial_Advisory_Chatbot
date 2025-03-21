<?php
namespace App\Services\Auth;

class PasswordService {
    private $hashAlgorithm;
    private $hashOptions;
    
    public function __construct() {
        // Use a strong hashing algorithm with appropriate options
        $this->hashAlgorithm = PASSWORD_BCRYPT;
        $this->hashOptions = [
            'cost' => 12 // Higher cost = more secure but slower
        ];
    }
    
    /**
     * Hash a password
     * @param string $password Plain text password
     * @return string Hashed password
     */
    public function hashPassword($password) {
        return password_hash($password, $this->hashAlgorithm, $this->hashOptions);
    }
    
    /**
     * Verify a password against a hash
     * @param string $password Plain text password
     * @param string $hash Hashed password
     * @return bool Verification result
     */
    public function verifyPassword($password, $hash) {
        return password_verify($password, $hash);
    }
    
    /**
     * Check if a password needs rehashing
     * @param string $hash Hashed password
     * @return bool Rehashing needed
     */
    public function needsRehash($hash) {
        return password_needs_rehash($hash, $this->hashAlgorithm, $this->hashOptions);
    }
    
    /**
     * Generate a random password
     * @param int $length Password length
     * @return string Generated password
     */
    public function generateRandomPassword($length = 12) {
        $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_-=+;:,.?';
        $password = '';
        $charLength = strlen($chars) - 1;
        
        // Ensure password contains at least one character from each group
        $password .= $chars[rand(0, 25)]; // lowercase
        $password .= $chars[rand(26, 51)]; // uppercase
        $password .= $chars[rand(52, 61)]; // digit
        $password .= $chars[rand(62, $charLength)]; // special char
        
        // Fill the rest with random characters
        for ($i = 0; $i < $length - 4; $i++) {
            $password .= $chars[rand(0, $charLength)];
        }
        
        // Shuffle the password
        return str_shuffle($password);
    }
    
    /**
     * Validate password strength
     * @param string $password Password to validate
     * @return array Validation result
     */
    public function validatePasswordStrength($password) {
        $result = [
            'valid' => true,
            'errors' => []
        ];
        
        // Check minimum length
        if (strlen($password) < 8) {
            $result['valid'] = false;
            $result['errors'][] = 'Password must be at least 8 characters long';
        }
        
        // Check for uppercase
        if (!preg_match('/[A-Z]/', $password)) {
            $result['valid'] = false;
            $result['errors'][] = 'Password must contain at least one uppercase letter';
        }
        
        // Check for lowercase
        if (!preg_match('/[a-z]/', $password)) {
            $result['valid'] = false;
            $result['errors'][] = 'Password must contain at least one lowercase letter';
        }
        
        // Check for digits
        if (!preg_match('/[0-9]/', $password)) {
            $result['valid'] = false;
            $result['errors'][] = 'Password must contain at least one digit';
        }
        
        // Check for special characters
        if (!preg_match('/[^A-Za-z0-9]/', $password)) {
            $result['valid'] = false;
            $result['errors'][] = 'Password must contain at least one special character';
        }
        
        return $result;
    }
}