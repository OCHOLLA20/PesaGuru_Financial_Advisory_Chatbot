<?php

class redisConnector {
    // Connection singleton
    private static $instance = null;
    
    // Connection configurations
    private static $config = [
        'host' => '127.0.0.1',
        'port' => 6379,
        'password' => null,
        'database' => 0,
        'timeout' => 2.0,
        'read_timeout' => 2.0,
        'retry_interval' => 100, // milliseconds
        'read_write_timeout' => 0,
    ];
    
    // Active connection
    private static $connection = null;
    
    // Connection type
    private static $connectionType = null;
    
    // Whether initialization was attempted
    private static $initAttempted = false;
    
    /**
     * Initialize the Redis connection
     * 
     * @param array $config Optional configuration parameters
     * @return bool Whether initialization was successful
     */
    public static function init($config = []) {
        // Only try to initialize once
        if (self::$initAttempted) {
            return self::$connection !== null;
        }
        
        self::$initAttempted = true;
        
        // Merge provided configuration with defaults
        if (!empty($config)) {
            self::$config = array_merge(self::$config, $config);
        }
        
        // Load configuration from environment if available
        self::loadEnvConfig();
        
        // Try to establish connection using available methods
        if (self::connectWithPhpRedis()) {
            self::$connectionType = 'phpredis';
            return true;
        } else if (self::connectWithPredis()) {
            self::$connectionType = 'predis';
            return true;
        } else {
            // Log the failure to connect
            error_log('redisConnector: Failed to connect to Redis server. Using no-op implementation.');
            self::$connectionType = 'noop';
            self::$connection = new RedisNoOpConnector();
            return false;
        }
    }
    
    /**
     * Load Redis configuration from environment variables
     */
    private static function loadEnvConfig() {
        $envVars = [
            'REDIS_HOST' => 'host',
            'REDIS_PORT' => 'port',
            'REDIS_PASSWORD' => 'password',
            'REDIS_DATABASE' => 'database',
            'REDIS_TIMEOUT' => 'timeout',
            'REDIS_READ_TIMEOUT' => 'read_timeout',
        ];
        
        foreach ($envVars as $env => $config) {
            if (getenv($env) !== false) {
                self::$config[$config] = getenv($env);
            }
        }
    }
    
    /**
     * Attempt to connect using the PHP Redis extension
     * 
     * @return bool Connection success
     */
    private static function connectWithPhpRedis() {
        // Check if PHP Redis extension is available
        if (!extension_loaded('redis')) {
            return false;
        }
        
        try {
            // Use fully qualified class name with leading backslash to avoid namespace issues
            $redis = new \Redis();
            
            // Connect with timeout
            $connectResult = $redis->connect(
                self::$config['host'],
                self::$config['port'],
                self::$config['timeout'],
                null,
                self::$config['retry_interval']
            );
            
            if (!$connectResult) {
                return false;
            }
            
            // Set read timeout - use proper constant with the correct case
            $redis->setOption(\Redis::OPT_READ_TIMEOUT, self::$config['read_timeout']);
            
            // Authenticate if password is provided
            if (!empty(self::$config['password'])) {
                if (!$redis->auth(self::$config['password'])) {
                    error_log('redisConnector: Authentication failed');
                    return false;
                }
            }
            
            // Select database
            if (self::$config['database'] !== 0) {
                $redis->select(self::$config['database']);
            }
            
            // Test connection
            if (!$redis->ping()) {
                error_log('redisConnector: Ping failed');
                return false;
            }
            
            self::$connection = $redis;
            return true;
        } catch (\Exception $e) {
            error_log('redisConnector: PHP Redis extension error: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Attempt to connect using the Predis library
     * 
     * @return bool Connection success
     */
    private static function connectWithPredis() {
        // Check if Predis is available
        if (!class_exists('\Predis\Client')) {
            return false;
        }
        
        try {
            $parameters = [
                'scheme' => 'tcp',
                'host' => self::$config['host'],
                'port' => self::$config['port'],
                'database' => self::$config['database'],
                'timeout' => self::$config['timeout'],
                'read_write_timeout' => self::$config['read_timeout'],
            ];
            
            if (!empty(self::$config['password'])) {
                $parameters['password'] = self::$config['password'];
            }
            
            $options = [
                'exceptions' => true,
            ];
            
            // Use fully qualified class name with leading backslash
            $redis = new \Predis\Client($parameters, $options);
            
            // Test connection
            $redis->ping();
            
            self::$connection = $redis;
            return true;
        } catch (\Exception $e) {
            error_log('redisConnector: Predis library error: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Get Redis connection instance
     * 
     * @return object Redis connection (Redis, Predis\Client, or RedisNoOpConnector)
     */
    public static function getConnection() {
        // Initialize if not already done
        if (!self::$initAttempted) {
            self::init();
        }
        
        return self::$connection;
    }
    
    /**
     * Get connection type
     * 
     * @return string Connection type ('phpredis', 'predis', or 'noop')
     */
    public static function getConnectionType() {
        if (!self::$initAttempted) {
            self::init();
        }
        
        return self::$connectionType;
    }
    
    /**
     * Check if Redis is available
     * 
     * @return bool Whether Redis is available
     */
    public static function isAvailable() {
        if (!self::$initAttempted) {
            self::init();
        }
        
        return self::$connectionType !== 'noop';
    }
    
    /**
     * Close Redis connection
     */
    public static function close() {
        if (self::$connection !== null) {
            if (self::$connectionType === 'phpredis' && method_exists(self::$connection, 'close')) {
                self::$connection->close();
            } else if (self::$connectionType === 'predis' && method_exists(self::$connection, 'disconnect')) {
                self::$connection->disconnect();
            }
            
            self::$connection = null;
        }
    }
}

/**
 * Redis No-Op Connector
 * 
 * Fallback implementation when Redis is unavailable.
 * All methods are no-op implementations that mimic Redis behavior
 * but actually do nothing, allowing the application to continue functioning.
 */
class RedisNoOpConnector {
    private $inMemoryCache = [];
    
    /**
     * Set a key with expiration
     */
    public function setex($key, $ttl, $value) {
        return true;
    }
    
    /**
     * Get a key's value
     */
    public function get($key) {
        return isset($this->inMemoryCache[$key]) ? $this->inMemoryCache[$key] : null;
    }
    
    /**
     * Delete a key
     */
    public function del($key) {
        if (isset($this->inMemoryCache[$key])) {
            unset($this->inMemoryCache[$key]);
            return 1;
        }
        return 0;
    }
    
    /**
     * Get time-to-live for a key
     */
    public function ttl($key) {
        return -2; // Key does not exist
    }
    
    /**
     * Get Redis info
     */
    public function info() {
        return [
            'redis_version' => 'noop',
            'keyspace_hits' => 0,
            'keyspace_misses' => 0,
            'used_memory_human' => '0B',
            'uptime_in_seconds' => 0,
            'total_connections_received' => 0,
        ];
    }
    
    /**
     * Find keys matching a pattern
     */
    public function keys($pattern) {
        return [];
    }
    
    /**
     * Ping the server
     */
    public function ping() {
        return 'PONG';
    }
    
    /**
     * Set a key-value pair
     */
    public function set($key, $value) {
        $this->inMemoryCache[$key] = $value;
        return true;
    }
    
    /**
     * Check if a key exists
     */
    public function exists($key) {
        return isset($this->inMemoryCache[$key]) ? 1 : 0;
    }
    
    /**
     * Method to satisfy close() calls
     */
    public function close() {
        // No-op implementation
        return true;
    }
    
    /**
     * Method to satisfy disconnect() calls
     */
    public function disconnect() {
        // No-op implementation
        return true;
    }
}
?>
