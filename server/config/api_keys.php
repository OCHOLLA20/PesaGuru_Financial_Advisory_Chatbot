<?php

namespace PesaGuru\Server\Config;

class APIKeys
{
    /**
     * @var bool Enable fallback keys in development (disable in production)
     */
    private static $allowFallback = true;
    
    /**
     * @var array Cache for API keys to avoid repeated lookups
     */
    private static $keyCache = [];
    
    /**
     * @var array Fallback keys for development ONLY
     * NEVER store actual production keys here, these are placeholders
     */
    private static $devFallbackKeys = [
        // Sentiment Analysis API Keys
        'SENTIMENT_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        
        // Translation API Keys
        'TRANSLATION_API_KEY' => 'dev_translation_key_placeholder',
        
        // Stock Market API Keys
        'NSE_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        'YAHOO_FINANCE_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        'ALPHA_VANTAGE_API_KEY' => '08HAWE6C99AGWNEZ',
        
        // Central Bank & Forex API Keys
        'CBK_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        'FOREX_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        
        // Mobile Money API Keys (Safaricom M-Pesa)
        'MPESA_CONSUMER_KEY' => 'dev_mpesa_consumer_key_placeholder',
        'MPESA_CONSUMER_SECRET' => 'dev_mpesa_consumer_secret_placeholder',
        
        // Crypto API Keys
        'COINGECKO_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        'BINANCE_API_KEY' => 'dev_binance_api_key_placeholder',
        'BINANCE_SECRET_KEY' => 'dev_binance_secret_key_placeholder',
        
        // News API Keys
        'NEWS_API_KEY' => '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581',
        
        // OpenAI API Keys
        'OPENAI_API_KEY' => 'dev_openai_api_key_placeholder',
        
        // Payment Gateway API Keys
        'PAYPAL_CLIENT_ID' => 'dev_paypal_client_id_placeholder',
        'PAYPAL_SECRET' => 'dev_paypal_secret_placeholder',
        
        // Dialogflow API Keys
        'DIALOGFLOW_PROJECT_ID' => 'dev_dialogflow_project_id',
        
        // Firebase API Keys
        'FIREBASE_API_KEY' => 'AIzaSyBDkDJ79JdnqYziW8KePngYrLPvGZoIjYo',
        'FIREBASE_AUTH_DOMAIN' => 'pesaguru-ff00b.firebaseapp.com',
        'FIREBASE_PROJECT_ID' => 'pesaguru-ff00b',
        'FIREBASE_STORAGE_BUCKET' => 'pesaguru-ff00b.firebasestorage.app',
        'FIREBASE_MESSAGING_SENDER_ID' => '19758550442',
        'FIREBASE_APP_ID' => '1:19758550442:web:d6fb9a4b3937b231952fd3',
        'FIREBASE_MEASUREMENT_ID' => 'G-L17TBTCF3Z',
    ];
    
    /**
     * Initialize the API Keys configuration
     * Sets appropriate fallback behavior based on environment
     */
    public static function init()
    {
        // In production, disable fallback keys for security
        $env = getenv('APP_ENV');
        if ($env && strtolower($env) === 'production') {
            self::$allowFallback = false;
        }
        
        // Load API key pairs from .env file if available
        if (file_exists(dirname(dirname(dirname(__FILE__))) . '/.env')) {
            self::loadEnvFile();
        }
    }
    
    /**
     * Load environment variables from .env file
     */
    private static function loadEnvFile()
    {
        $envFile = dirname(dirname(dirname(__FILE__))) . '/.env';
        
        if (file_exists($envFile)) {
            $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            
            foreach ($lines as $line) {
                // Skip comments
                if (strpos(trim($line), '#') === 0) {
                    continue;
                }
                
                // Parse KEY=VALUE format
                if (strpos($line, '=') !== false) {
                    list($key, $value) = explode('=', $line, 2);
                    $key = trim($key);
                    $value = trim($value);
                    
                    // Remove quotes if present
                    if (preg_match('/^([\'"])(.*)\1$/', $value, $matches)) {
                        $value = $matches[2];
                    }
                    
                    // Set environment variable if not already set
                    if (!getenv($key)) {
                        putenv("$key=$value");
                    }
                }
            }
        }
    }
    
    /**
     * Get an API key securely
     * 
     * @param string $keyName Name of the API key
     * @return string|null API key or null if not found
     */
    private static function getKey($keyName)
    {
        // Return from cache if available
        if (isset(self::$keyCache[$keyName])) {
            return self::$keyCache[$keyName];
        }
        
        // First check environment variables (most secure method)
        $key = getenv($keyName);
        
        // If environment variable not set, try fallback (only in development)
        if ((!$key || empty($key)) && self::$allowFallback) {
            $key = self::$devFallbackKeys[$keyName] ?? null;
            
            // Log warning about using fallback keys in development
            if ($key && class_exists('\\PesaGuru\\Utils\\Logger')) {
                $logger = new \PesaGuru\Utils\Logger('api-keys');
                $logger->warning("Using fallback dev key for {$keyName}. Set environment variable in production!");
            }
        }
        
        // Cache the key to avoid repeated lookups
        self::$keyCache[$keyName] = $key;
        
        return $key;
    }
    
    /**
     * Get Sentiment Analysis API Key
     * 
     * @return string|null API key
     */
    public static function getSentimentAPIKey()
    {
        return self::getKey('SENTIMENT_API_KEY');
    }
    
    /**
     * Get Translation API Key
     * 
     * @return string|null API key
     */
    public static function getTranslationAPIKey()
    {
        return self::getKey('TRANSLATION_API_KEY');
    }
    
    /**
     * Get Nairobi Stock Exchange (NSE) API Key
     * 
     * @return string|null API key
     */
    public static function getNSEAPIKey()
    {
        return self::getKey('NSE_API_KEY');
    }
    
    /**
     * Get Yahoo Finance API Key
     * 
     * @return string|null API key
     */
    public static function getYahooFinanceAPIKey()
    {
        return self::getKey('YAHOO_FINANCE_API_KEY');
    }
    
    /**
     * Get Alpha Vantage API Key
     * 
     * @return string|null API key
     */
    public static function getAlphaVantageAPIKey()
    {
        return self::getKey('ALPHA_VANTAGE_API_KEY');
    }
    
    /**
     * Get Central Bank of Kenya (CBK) API Key
     * 
     * @return string|null API key
     */
    public static function getCBKAPIKey()
    {
        return self::getKey('CBK_API_KEY');
    }
    
    /**
     * Get Forex API Key
     * 
     * @return string|null API key
     */
    public static function getForexAPIKey()
    {
        return self::getKey('FOREX_API_KEY');
    }
    
    /**
     * Get M-Pesa Consumer Key
     * 
     * @return string|null API key
     */
    public static function getMpesaConsumerKey()
    {
        return self::getKey('MPESA_CONSUMER_KEY');
    }
    
    /**
     * Get M-Pesa Consumer Secret
     * 
     * @return string|null API key
     */
    public static function getMpesaConsumerSecret()
    {
        return self::getKey('MPESA_CONSUMER_SECRET');
    }
    
    /**
     * Get CoinGecko API Key
     * 
     * @return string|null API key
     */
    public static function getCoinGeckoAPIKey()
    {
        return self::getKey('COINGECKO_API_KEY');
    }
    
    /**
     * Get Binance API Key
     * 
     * @return string|null API key
     */
    public static function getBinanceAPIKey()
    {
        return self::getKey('BINANCE_API_KEY');
    }
    
    /**
     * Get Binance Secret Key
     * 
     * @return string|null API key
     */
    public static function getBinanceSecretKey()
    {
        return self::getKey('BINANCE_SECRET_KEY');
    }
    
    /**
     * Get News API Key
     * 
     * @return string|null API key
     */
    public static function getNewsAPIKey()
    {
        return self::getKey('NEWS_API_KEY');
    }
    
    /**
     * Get OpenAI API Key
     * 
     * @return string|null API key
     */
    public static function getOpenAIAPIKey()
    {
        return self::getKey('OPENAI_API_KEY');
    }
    
    /**
     * Get PayPal Client ID
     * 
     * @return string|null API key
     */
    public static function getPayPalClientID()
    {
        return self::getKey('PAYPAL_CLIENT_ID');
    }
    
    /**
     * Get PayPal Secret
     * 
     * @return string|null API key
     */
    public static function getPayPalSecret()
    {
        return self::getKey('PAYPAL_SECRET');
    }
    
    /**
     * Get Dialogflow Project ID
     * 
     * @return string|null Project ID
     */
    public static function getDialogflowProjectID()
    {
        return self::getKey('DIALOGFLOW_PROJECT_ID');
    }
    
    /**
     * Get Firebase configuration as an array
     * 
     * @return array Firebase configuration
     */
    public static function getFirebaseConfig()
    {
        return [
            'apiKey' => self::getKey('FIREBASE_API_KEY'),
            'authDomain' => self::getKey('FIREBASE_AUTH_DOMAIN'),
            'projectId' => self::getKey('FIREBASE_PROJECT_ID'),
            'storageBucket' => self::getKey('FIREBASE_STORAGE_BUCKET'),
            'messagingSenderId' => self::getKey('FIREBASE_MESSAGING_SENDER_ID'),
            'appId' => self::getKey('FIREBASE_APP_ID'),
            'measurementId' => self::getKey('FIREBASE_MEASUREMENT_ID')
        ];
    }
    
    /**
     * Add or update a key in fallback keys (development only)
     * 
     * @param string $keyName Name of the key
     * @param string $value Key value
     * @return bool Success status
     */
    public static function setFallbackKey($keyName, $value)
    {
        // Only allow in development
        if (!self::$allowFallback) {
            return false;
        }
        
        self::$devFallbackKeys[$keyName] = $value;
        self::$keyCache[$keyName] = $value; // Update cache
        
        return true;
    }
    
    /**
     * Check if an API service is configured with valid credentials
     * 
     * @param string $service Service name
     * @return bool True if service is configured
     */
    public static function isServiceConfigured($service)
    {
        switch ($service) {
            case 'sentiment':
                return !empty(self::getSentimentAPIKey());
                
            case 'mpesa':
                return !empty(self::getMpesaConsumerKey()) && !empty(self::getMpesaConsumerSecret());
                
            case 'nse':
                return !empty(self::getNSEAPIKey());
                
            case 'cbk':
                return !empty(self::getCBKAPIKey());
                
            case 'crypto':
                return !empty(self::getCoinGeckoAPIKey()) || !empty(self::getBinanceAPIKey());
                
            case 'news':
                return !empty(self::getNewsAPIKey());
                
            case 'openai':
                return !empty(self::getOpenAIAPIKey());
                
            case 'paypal':
                return !empty(self::getPayPalClientID()) && !empty(self::getPayPalSecret());
                
            case 'dialogflow':
                return !empty(self::getDialogflowProjectID());
                
            case 'firebase':
                $config = self::getFirebaseConfig();
                return !empty($config['apiKey']) && !empty($config['projectId']);
                
            default:
                return false;
        }
    }
}

// Initialize the API Keys configuration
APIKeys::init();