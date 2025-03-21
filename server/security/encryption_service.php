<?php
/**
 * Encryption Service
 * 
 * Handles encryption and decryption of sensitive data for the PesaGuru financial 
 * advisory chatbot. Uses OpenSSL for AES-256-CBC encryption with proper 
 * initialization vector (IV) handling.
 * 
 * @package PesaGuru
 * @subpackage Server\Security
 */

namespace PesaGuru\Server\Security;

class EncryptionService {
    /**
     * Encryption method
     * @var string
     */
    private $method = 'AES-256-CBC';
    
    /**
     * Encryption key
     * @var string|null
     */
    private $key = null;
    
    /**
     * Constructor - initialize encryption key
     */
    public function __construct() {
        $this->initializeKey();
    }
    
    /**
     * Initialize encryption key from environment or config
     */
    private function initializeKey() {
        // Try to get the key from environment variable first
        $key = getenv('ENCRYPTION_KEY');
        
        // If not found in environment, try to get from .env file
        if (!$key) {
            $this->loadFromDotEnv();
            $key = getenv('ENCRYPTION_KEY');
        }
        
        // If still not found, generate and save a new key (development only)
        if (!$key) {
            $key = $this->generateKey();
            $this->saveKeyToEnv($key);
        }
        
        $this->key = $key;
    }
    
    /**
     * Load environment variables from .env file
     */
    private function loadFromDotEnv() {
        $envFile = __DIR__ . '/../../.env';
        
        if (file_exists($envFile)) {
            $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            
            foreach ($lines as $line) {
                // Skip comments
                if (strpos(trim($line), '#') === 0) {
                    continue;
                }
                
                // Parse variable assignment
                if (strpos($line, '=') !== false) {
                    list($name, $value) = explode('=', $line, 2);
                    $name = trim($name);
                    $value = trim($value);
                    
                    // Remove quotes if present
                    if (strpos($value, '"') === 0 && strrpos($value, '"') === strlen($value) - 1) {
                        $value = substr($value, 1, -1);
                    } elseif (strpos($value, "'") === 0 && strrpos($value, "'") === strlen($value) - 1) {
                        $value = substr($value, 1, -1);
                    }
                    
                    // Set environment variable
                    putenv("$name=$value");
                }
            }
        }
    }
    
    /**
     * Generate a new encryption key
     * 
     * @return string Generated key
     */
    private function generateKey() {
        // Generate a cryptographically secure key
        return base64_encode(openssl_random_pseudo_bytes(32));
    }
    
    /**
     * Save a generated key to .env file (for development only)
     * 
     * @param string $key Encryption key to save
     * @return bool Success status
     */
    private function saveKeyToEnv($key) {
        $envFile = __DIR__ . '/../../.env';
        
        // In production, we should NOT automatically write to .env
        // This is for development convenience only
        if (file_exists($envFile) && strpos($_SERVER['SERVER_NAME'] ?? '', 'localhost') !== false) {
            $content = file_get_contents($envFile);
            
            // Check if the ENCRYPTION_KEY is already in the file
            if (strpos($content, 'ENCRYPTION_KEY=') !== false) {
                // Replace existing key
                $content = preg_replace('/ENCRYPTION_KEY=.*(\r?\n|$)/', "ENCRYPTION_KEY=\"$key\"\n", $content);
            } else {
                // Add new key
                $content .= "\n# Auto-generated encryption key\nENCRYPTION_KEY=\"$key\"\n";
            }
            
            // Write updated content back to file
            if (file_put_contents($envFile, $content)) {
                error_log("Generated and saved new encryption key to .env file");
                return true;
            } else {
                error_log("Failed to save encryption key to .env file");
                return false;
            }
        }
        
        // Set environment variable even if we couldn't save it to .env
        putenv("ENCRYPTION_KEY=$key");
        return false;
    }
    
    /**
     * Encrypt data
     * 
     * @param string $data Data to encrypt
     * @return string Encrypted data (base64 encoded)
     * @throws \Exception If encryption fails
     */
    public function encrypt($data) {
        if (empty($data)) {
            return '';
        }
        
        try {
            // Generate initialization vector
            $ivSize = openssl_cipher_iv_length($this->method);
            $iv = openssl_random_pseudo_bytes($ivSize);
            
            // Encrypt the data
            $encrypted = openssl_encrypt(
                $data,
                $this->method,
                base64_decode($this->key),
                OPENSSL_RAW_DATA,
                $iv
            );
            
            if ($encrypted === false) {
                throw new \Exception('Encryption failed: ' . openssl_error_string());
            }
            
            // Combine IV and encrypted data
            $combined = $iv . $encrypted;
            
            // Base64 encode for storage
            return base64_encode($combined);
        } catch (\Exception $e) {
            error_log('Encryption error: ' . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Decrypt data
     * 
     * @param string $data Encrypted data (base64 encoded)
     * @return string Decrypted data
     * @throws \Exception If decryption fails
     */
    public function decrypt($data) {
        if (empty($data)) {
            return '';
        }
        
        try {
            // Decode from base64
            $combined = base64_decode($data);
            
            // Extract initialization vector
            $ivSize = openssl_cipher_iv_length($this->method);
            $iv = substr($combined, 0, $ivSize);
            
            // Extract encrypted data
            $encrypted = substr($combined, $ivSize);
            
            // Decrypt the data
            $decrypted = openssl_decrypt(
                $encrypted,
                $this->method,
                base64_decode($this->key),
                OPENSSL_RAW_DATA,
                $iv
            );
            
            if ($decrypted === false) {
                throw new \Exception('Decryption failed: ' . openssl_error_string());
            }
            
            return $decrypted;
        } catch (\Exception $e) {
            error_log('Decryption error: ' . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Hash a string using a strong algorithm (for passwords, etc.)
     * 
     * @param string $data String to hash
     * @return string Hashed string
     */
    public function hash($data) {
        return password_hash($data, PASSWORD_ARGON2ID, [
            'memory_cost' => 1024,
            'time_cost' => 2,
            'threads' => 2
        ]);
    }
    
    /**
     * Verify a string against a hash
     * 
     * @param string $data String to verify
     * @param string $hash Hash to verify against
     * @return bool Whether the string matches the hash
     */
    public function verifyHash($data, $hash) {
        return password_verify($data, $hash);
    }
    
    /**
     * Generate a secure random token
     * 
     * @param int $length Length of the token
     * @return string Generated token
     */
    public function generateToken($length = 32) {
        return bin2hex(random_bytes($length / 2));
    }
    
    /**
     * Encrypt data with public key (asymmetric encryption)
     * 
     * @param string $data Data to encrypt
     * @param string $publicKey PEM formatted public key
     * @return string Encrypted data (base64 encoded)
     * @throws \Exception If encryption fails
     */
    public function publicEncrypt($data, $publicKey) {
        if (empty($data)) {
            return '';
        }
        
        try {
            // Encrypt data with public key
            if (!openssl_public_encrypt($data, $encrypted, $publicKey)) {
                throw new \Exception('Public key encryption failed: ' . openssl_error_string());
            }
            
            // Base64 encode for storage
            return base64_encode($encrypted);
        } catch (\Exception $e) {
            error_log('Public key encryption error: ' . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Decrypt data with private key (asymmetric encryption)
     * 
     * @param string $data Encrypted data (base64 encoded)
     * @param string $privateKey PEM formatted private key
     * @param string $passphrase Optional passphrase for private key
     * @return string Decrypted data
     * @throws \Exception If decryption fails
     */
    public function privateDecrypt($data, $privateKey, $passphrase = null) {
        if (empty($data)) {
            return '';
        }
        
        try {
            // Decode from base64
            $encrypted = base64_decode($data);
            
            // Decrypt data with private key
            if (!openssl_private_decrypt($encrypted, $decrypted, $privateKey, $passphrase)) {
                throw new \Exception('Private key decryption failed: ' . openssl_error_string());
            }
            
            return $decrypted;
        } catch (\Exception $e) {
            error_log('Private key decryption error: ' . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Validate the encryption key's strength
     * 
     * @return bool Whether the key meets strength requirements
     */
    public function validateKeyStrength() {
        $decodedKey = base64_decode($this->key);
        
        // Check key length (32 bytes / 256 bits for AES-256)
        if (strlen($decodedKey) !== 32) {
            error_log('Encryption key length invalid: ' . strlen($decodedKey) . ' bytes (expected 32)');
            return false;
        }
        
        // Check entropy (randomness)
        $entropy = 0;
        $frequencies = [];
        
        // Count byte frequencies
        for ($i = 0; $i < strlen($decodedKey); $i++) {
            $byte = ord($decodedKey[$i]);
            if (!isset($frequencies[$byte])) {
                $frequencies[$byte] = 0;
            }
            $frequencies[$byte]++;
        }
        
        // Calculate Shannon entropy
        foreach ($frequencies as $count) {
            $probability = $count / strlen($decodedKey);
            $entropy -= $probability * log($probability, 2);
        }
        
        // For truly random 256-bit key, entropy should be close to 8
        // (maximum entropy for a byte is 8 bits)
        if ($entropy < 7.5) {
            error_log('Encryption key entropy too low: ' . $entropy);
            return false;
        }
        
        return true;
    }
}
?>