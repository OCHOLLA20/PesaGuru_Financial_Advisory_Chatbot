<?php

/**
 * Load environment variables from .env file
 * 
 * @param string $envFile Path to the .env file
 * @return bool True if the .env file was loaded successfully
 */
function loadEnvFile($envFile) {
    if (!file_exists($envFile)) {
        return false;
    }
    
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        // Skip comments
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        
        // Parse environment variable
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        
        // Remove quotes if they exist
        if (strpos($value, '"') === 0 || strpos($value, "'") === 0) {
            $value = substr($value, 1, -1);
        }
        
        // Set environment variable
        putenv("{$name}={$value}");
        $_ENV[$name] = $value;
        $_SERVER[$name] = $value;
    }
    
    return true;
}

// Load environment variables from .env file
$envFile = __DIR__ . '/../../.env';
$loaded = loadEnvFile($envFile);

if (!$loaded) {
    // Log error but don't exit to allow defaults to be used
    error_log('Error: .env file not found or could not be loaded.');
}

// Define default environment variables if they're not set
$defaultEnvVars = [
    'DB_HOST' => 'localhost',
    'DB_NAME' => 'pesaguru_db',
    'DB_USER' => 'root',
    'DB_PASS' => '',
    'JWT_SECRET' => 'pesaguru_default_secret_key_change_in_production',
    'JWT_EXPIRATION' => '3600', // 1 hour in seconds
    'API_RATE_LIMIT' => '100', // Requests per minute
    'DEBUG_MODE' => 'true', // Enable debugging in development
    'LOG_LEVEL' => 'error',
    'MPESA_CONSUMER_KEY' => '',
    'MPESA_CONSUMER_SECRET' => '',
    'NSE_API_KEY' => '',
    'CHATGPT_API_KEY' => '',
    'COINGECKO_API_KEY' => '',
    'CBK_API_KEY' => ''
];

// Set default environment variables if they're not already set
foreach ($defaultEnvVars as $key => $value) {
    if (!getenv($key)) {
        putenv("{$key}={$value}");
        $_ENV[$key] = $value;
        $_SERVER[$key] = $value;
    }
}

// Define constants for frequently used environment variables
define('DEBUG_MODE', getenv('DEBUG_MODE') === 'true');
define('JWT_SECRET', getenv('JWT_SECRET'));
define('JWT_EXPIRATION', (int)getenv('JWT_EXPIRATION'));
define('API_RATE_LIMIT', (int)getenv('API_RATE_LIMIT'));