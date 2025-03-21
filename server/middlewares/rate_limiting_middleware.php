<?php

// Check if Redis extension is installed
if (!extension_loaded('redis')) {
    error_log('Redis extension is not installed. Rate limiting will use fallback method.');
}

/**
 * Rate Limiting Middleware for PesaGuru API
 * Limits requests based on client identifier (user ID, API key, or IP address)
 */
class RateLimitingMiddleware {
    /**
     * @var \Redis|null Redis client instance
     */
    private $redis = null;
    
    /**
     * @var array Default rate limit configuration
     */
    private $defaultLimits = [
        'default' => [
            'limit' => 60,      // 60 requests
            'window' => 60,     // per 60 seconds (per minute)
        ],
        'auth' => [
            'limit' => 10,      // 10 requests
            'window' => 60,     // per 60 seconds (for auth endpoints)
        ],
        'market_data' => [
            'limit' => 120,     // 120 requests
            'window' => 60,     // per 60 seconds (for market data)
        ],
        'chatbot' => [
            'limit' => 30,      // 30 requests
            'window' => 60,     // per 60 seconds (for chatbot interactions)
        ],
    ];

    /**
     * @var array Custom limits for specific users (by user ID)
     */
    private $userLimits = [
        // Premium users get higher limits
        'premium' => [
            'limit' => 150,     // 150 requests
            'window' => 60,     // per 60 seconds
        ],
    ];

    /**
     * Constructor
     */
    public function __construct() {
        // Initialize Redis connection if extension is available
        if (extension_loaded('redis')) {
            try {
                // Get Redis configuration from environment or config file
                $redisHost = getenv('REDIS_HOST') ?: '127.0.0.1';
                $redisPort = getenv('REDIS_PORT') ?: 6379;
                $redisPassword = getenv('REDIS_PASSWORD') ?: null;
                
                // Create Redis instance
                $this->redis = new \Redis();
                
                // Connect to Redis
                $this->redis->connect($redisHost, $redisPort);
                
                // Authenticate if password is set
                if ($redisPassword) {
                    $this->redis->auth($redisPassword);
                }
                
                // Ping Redis to ensure connection is active
                $this->redis->ping();
                
            } catch (\RedisException $e) {
                // Log Redis connection error
                error_log('Redis connection error: ' . $e->getMessage());
                
                // Fallback to in-memory rate limiting
                $this->redis = null;
            } catch (\Exception $e) {
                // Log general exceptions
                error_log('Redis general error: ' . $e->getMessage());
                
                // Fallback to in-memory rate limiting
                $this->redis = null;
            }
        }
    }

    /**
     * Handle an incoming request
     * 
     * @param array $request The request data
     * @param callable $next The next middleware
     * @return mixed
     */
    public function handle($request, $next) {
        // Get client identifier (user ID for authenticated users, IP for anonymous)
        $identifier = $this->getClientIdentifier();
        
        // Determine which rate limit to apply
        $limitConfig = $this->getLimitConfig();
        
        // Check if request exceeds rate limit
        if ($this->isRateLimited($identifier, $limitConfig)) {
            // Return rate limit exceeded response
            return $this->rateLimitExceededResponse($limitConfig);
        }
        
        // Request is within limits, proceed to next middleware/controller
        return $next($request);
    }
    
    /**
     * Get client identifier (user ID or IP address)
     * 
     * @return string
     */
    private function getClientIdentifier() {
        // If user is authenticated, use user ID
        if (isset($_SESSION['user_id'])) {
            return 'user:' . $_SESSION['user_id'];
        }
        
        // For API consumers with API key
        if (isset($_SERVER['HTTP_X_API_KEY'])) {
            return 'api:' . $_SERVER['HTTP_X_API_KEY'];
        }
        
        // For anonymous users, use IP address
        $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
        
        // If behind proxy, try to get real IP (common in production)
        if (isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
            // Get the first IP in the list
            $ips = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR']);
            $ip = trim($ips[0]);
        }
        
        return 'ip:' . $ip;
    }
    
    /**
     * Determine which rate limit configuration to apply
     * 
     * @return array Rate limit configuration (limit, window)
     */
    private function getLimitConfig() {
        // Check if user has custom limits
        if (isset($_SESSION['user_id']) && isset($_SESSION['user_type'])) {
            $userType = $_SESSION['user_type'];
            
            if (isset($this->userLimits[$userType])) {
                return $this->userLimits[$userType];
            }
        }
        
        // Determine limit based on request path
        $path = $_SERVER['REQUEST_URI'] ?? '';
        
        // Apply specific limits based on endpoint
        if (strpos($path, '/api/auth') === 0) {
            return $this->defaultLimits['auth'];
        } elseif (strpos($path, '/api/market-data') === 0) {
            return $this->defaultLimits['market_data'];
        } elseif (strpos($path, '/api/chatbot') === 0) {
            return $this->defaultLimits['chatbot'];
        }
        
        // Default limit for all other routes
        return $this->defaultLimits['default'];
    }
    
    /**
     * Check if the request exceeds rate limit
     * 
     * @param string $identifier Client identifier
     * @param array $limitConfig Rate limit configuration
     * @return bool True if rate limited, false otherwise
     */
    private function isRateLimited($identifier, $limitConfig) {
        // If Redis is not available, fallback to allow requests
        if ($this->redis === null) {
            // Simple in-memory rate limiting using session
            // This is less effective but provides some protection
            return $this->inMemoryRateLimiting($identifier, $limitConfig);
        }
        
        $limit = $limitConfig['limit'];
        $window = $limitConfig['window'];
        
        // Redis key for this client
        $key = "rate_limit:{$identifier}";
        
        // Current timestamp
        $now = time();
        
        try {
            // Clean up old data outside the current window
            $this->redis->zRemRangeByScore($key, 0, $now - $window);
            
            // Count requests in current window
            $requestCount = $this->redis->zCard($key);
            
            // If under limit, add this request and allow
            if ($requestCount < $limit) {
                // Add current request timestamp to sorted set
                $this->redis->zAdd($key, $now, $now . ':' . microtime(true));
                
                // Set expiry on the sorted set to auto-cleanup
                $this->redis->expire($key, $window * 2);
                
                // Request is within limit
                return false;
            }
            
            // Request exceeds limit
            return true;
        } catch (\RedisException $e) {
            // Log Redis operation error
            error_log('Redis operation error: ' . $e->getMessage());
            
            // Fallback to in-memory on Redis errors
            return $this->inMemoryRateLimiting($identifier, $limitConfig);
        }
    }
    
    /**
     * Simple in-memory rate limiting using session storage
     * Only used as fallback when Redis is unavailable
     * 
     * @param string $identifier Client identifier
     * @param array $limitConfig Rate limit configuration
     * @return bool True if rate limited, false otherwise
     */
    private function inMemoryRateLimiting($identifier, $limitConfig) {
        // Start session if not already started
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }
        
        $limit = $limitConfig['limit'];
        $window = $limitConfig['window'];
        $now = time();
        
        // Initialize rate limiting array in session if not exists
        if (!isset($_SESSION['rate_limiting'])) {
            $_SESSION['rate_limiting'] = [];
        }
        
        if (!isset($_SESSION['rate_limiting'][$identifier])) {
            $_SESSION['rate_limiting'][$identifier] = [
                'requests' => [],
                'last_cleanup' => $now
            ];
        }
        
        $data = &$_SESSION['rate_limiting'][$identifier];
        
        // Clean up old requests (perform periodically to avoid doing this on every request)
        if ($now - $data['last_cleanup'] > 60) {
            $data['requests'] = array_filter($data['requests'], function($timestamp) use ($now, $window) {
                return $timestamp > ($now - $window);
            });
            $data['last_cleanup'] = $now;
        }
        
        // Count requests in current window
        $requestCount = count($data['requests']);
        
        // If under limit, add this request and allow
        if ($requestCount < $limit) {
            $data['requests'][] = $now;
            return false;
        }
        
        // Request exceeds limit
        return true;
    }
    
    /**
     * Generate response for rate limit exceeded
     * 
     * @param array $limitConfig Rate limit configuration
     * @return string Response with 429 status code
     */
    private function rateLimitExceededResponse($limitConfig) {
        // Set rate limit exceeded status code
        http_response_code(429); // Too Many Requests
        
        // Set headers with rate limit info
        header('X-RateLimit-Limit: ' . $limitConfig['limit']);
        header('X-RateLimit-Window: ' . $limitConfig['window'] . ' seconds');
        header('Retry-After: ' . $limitConfig['window']);
        header('Content-Type: application/json');
        
        // Return error response
        $response = [
            'status' => 'error',
            'code' => 429,
            'message' => 'Rate limit exceeded. Please try again later.',
            'limit' => $limitConfig['limit'],
            'window' => $limitConfig['window'] . ' seconds',
            'retry_after' => $limitConfig['window'],
        ];
        
        // Log rate limit exceeded
        error_log("Rate limit exceeded for client: {$this->getClientIdentifier()}");
        
        echo json_encode($response);
        exit;
    }
}

/**
 * Usage example:
 * 
 * In your index.php or API routes file:
 * 
 * // Initialize middleware
 * $rateLimitingMiddleware = new RateLimitingMiddleware();
 * 
 * // Apply middleware to request
 * $response = $rateLimitingMiddleware->handle($_REQUEST, function($request) {
 *     // Your controller or next middleware
 *     return handleRequest($request);
 * });
 */
?>