<?php

// Require the Redis connector
require_once __DIR__ . '/redis_connector.php';

class MarketDataCache {
    // Redis connection instance
    private static $redis = null;
    
    // Cache TTL (Time-To-Live) constants in seconds
    const TTL_STOCK_PRICES = 900;        // 15 minutes
    const TTL_FOREX_RATES = 3600;        // 1 hour
    const TTL_CRYPTO_PRICES = 300;       // 5 minutes
    const TTL_MARKET_INDICES = 600;      // 10 minutes
    const TTL_BOND_RATES = 86400;        // 24 hours
    const TTL_HISTORICAL_DATA = 604800;  // 7 days
    
    // Cache key prefixes
    const PREFIX_STOCK = 'stock:';
    const PREFIX_FOREX = 'forex:';
    const PREFIX_CRYPTO = 'crypto:';
    const PREFIX_INDEX = 'index:';
    const PREFIX_BOND = 'bond:';
    const PREFIX_HISTORICAL = 'hist:';
    
    /**
     * Initialize Redis connection
     * 
     * @return void
     */
    public static function init() {
        if (self::$redis === null) {
            self::$redis = redisConnector::getConnection();
            
            // Set up error handler if Redis connection fails
            if (!self::$redis) {
                error_log('MarketDataCache: Failed to connect to Redis');
            }
        }
    }
    
    /**
     * Store stock price data in cache
     * 
     * @param string $symbol Stock symbol (e.g., 'SCOM' for Safaricom)
     * @param array $data Stock data including price, volume, change, etc.
     * @param bool $is_historical Whether this is historical data (affects TTL)
     * @return bool Success status
     */
    public static function setStockData($symbol, $data, $is_historical = false) {
        self::init();
        
        // Validate data before caching
        if (!self::validateStockData($data)) {
            error_log("MarketDataCache: Invalid stock data for symbol: $symbol");
            return false;
        }
        
        // Add timestamp to data
        $data['cached_at'] = time();
        $data['is_cached'] = true;
        
        // Prepare key and determine TTL
        $key = self::PREFIX_STOCK . strtoupper($symbol);
        $ttl = $is_historical ? self::TTL_HISTORICAL_DATA : self::TTL_STOCK_PRICES;
        
        // Log cache operation for auditing
        self::logCacheOperation('SET', $key, $data);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, $ttl, json_encode($data));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching stock data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve stock price data from cache
     * 
     * @param string $symbol Stock symbol
     * @return array|null Stock data or null if not found/expired
     */
    public static function getStockData($symbol) {
        self::init();
        
        $key = self::PREFIX_STOCK . strtoupper($symbol);
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                // Log cache hit for analytics
                self::logCacheOperation('GET', $key, null, true);
                return json_decode($data, true);
            } else {
                // Log cache miss for analytics
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving stock data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Store forex exchange rate data
     * 
     * @param string $baseCurrency Base currency code (e.g., 'KES')
     * @param string $targetCurrency Target currency code (e.g., 'USD')
     * @param array $data Exchange rate data
     * @return bool Success status
     */
    public static function setForexData($baseCurrency, $targetCurrency, $data) {
        self::init();
        
        // Validate data
        if (!isset($data['rate']) || !is_numeric($data['rate'])) {
            error_log("MarketDataCache: Invalid forex data for $baseCurrency/$targetCurrency");
            return false;
        }
        
        // Add timestamp
        $data['cached_at'] = time();
        $data['is_cached'] = true;
        
        // Prepare key
        $key = self::PREFIX_FOREX . strtoupper($baseCurrency) . '_' . strtoupper($targetCurrency);
        
        // Log operation
        self::logCacheOperation('SET', $key, $data);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, self::TTL_FOREX_RATES, json_encode($data));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching forex data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve forex exchange rate data
     * 
     * @param string $baseCurrency Base currency code
     * @param string $targetCurrency Target currency code
     * @return array|null Exchange rate data or null if not found/expired
     */
    public static function getForexData($baseCurrency, $targetCurrency) {
        self::init();
        
        $key = self::PREFIX_FOREX . strtoupper($baseCurrency) . '_' . strtoupper($targetCurrency);
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                self::logCacheOperation('GET', $key, null, true);
                return json_decode($data, true);
            } else {
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving forex data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Store cryptocurrency price data
     * 
     * @param string $symbol Crypto symbol (e.g., 'BTC')
     * @param array $data Cryptocurrency data
     * @return bool Success status
     */
    public static function setCryptoData($symbol, $data) {
        self::init();
        
        // Validate data
        if (!isset($data['price_kes']) || !is_numeric($data['price_kes'])) {
            error_log("MarketDataCache: Invalid crypto data for symbol: $symbol");
            return false;
        }
        
        // Add timestamp
        $data['cached_at'] = time();
        $data['is_cached'] = true;
        
        // Prepare key
        $key = self::PREFIX_CRYPTO . strtoupper($symbol);
        
        // Log operation
        self::logCacheOperation('SET', $key, $data);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, self::TTL_CRYPTO_PRICES, json_encode($data));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching crypto data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve cryptocurrency price data
     * 
     * @param string $symbol Crypto symbol
     * @return array|null Cryptocurrency data or null if not found/expired
     */
    public static function getCryptoData($symbol) {
        self::init();
        
        $key = self::PREFIX_CRYPTO . strtoupper($symbol);
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                self::logCacheOperation('GET', $key, null, true);
                return json_decode($data, true);
            } else {
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving crypto data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Store market index data (e.g., NSE 20)
     * 
     * @param string $indexName Index name (e.g., 'NSE20')
     * @param array $data Index data
     * @return bool Success status
     */
    public static function setMarketIndexData($indexName, $data) {
        self::init();
        
        // Validate data
        if (!isset($data['value']) || !is_numeric($data['value'])) {
            error_log("MarketDataCache: Invalid market index data for: $indexName");
            return false;
        }
        
        // Add timestamp
        $data['cached_at'] = time();
        $data['is_cached'] = true;
        
        // Prepare key
        $key = self::PREFIX_INDEX . strtoupper($indexName);
        
        // Log operation
        self::logCacheOperation('SET', $key, $data);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, self::TTL_MARKET_INDICES, json_encode($data));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching market index data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve market index data
     * 
     * @param string $indexName Index name
     * @return array|null Index data or null if not found/expired
     */
    public static function getMarketIndexData($indexName) {
        self::init();
        
        $key = self::PREFIX_INDEX . strtoupper($indexName);
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                self::logCacheOperation('GET', $key, null, true);
                return json_decode($data, true);
            } else {
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving market index data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Store bond rate data
     * 
     * @param string $bondType Bond type (e.g., 'T-BILL-91DAY')
     * @param array $data Bond data
     * @return bool Success status
     */
    public static function setBondData($bondType, $data) {
        self::init();
        
        // Validate data
        if (!isset($data['rate']) || !is_numeric($data['rate'])) {
            error_log("MarketDataCache: Invalid bond data for: $bondType");
            return false;
        }
        
        // Add timestamp
        $data['cached_at'] = time();
        $data['is_cached'] = true;
        
        // Prepare key
        $key = self::PREFIX_BOND . strtoupper($bondType);
        
        // Log operation
        self::logCacheOperation('SET', $key, $data);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, self::TTL_BOND_RATES, json_encode($data));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching bond data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve bond rate data
     * 
     * @param string $bondType Bond type
     * @return array|null Bond data or null if not found/expired
     */
    public static function getBondData($bondType) {
        self::init();
        
        $key = self::PREFIX_BOND . strtoupper($bondType);
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                self::logCacheOperation('GET', $key, null, true);
                return json_decode($data, true);
            } else {
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving bond data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Store historical market data (with longer TTL)
     * 
     * @param string $dataType Data type (stock, forex, crypto, etc.)
     * @param string $symbol Symbol or identifier
     * @param string $timeframe Timeframe (1d, 1w, 1m, etc.)
     * @param array $data Historical data points
     * @return bool Success status
     */
    public static function setHistoricalData($dataType, $symbol, $timeframe, $data) {
        self::init();
        
        // Validate data
        if (!is_array($data) || empty($data)) {
            error_log("MarketDataCache: Invalid historical data for $dataType:$symbol:$timeframe");
            return false;
        }
        
        // Prepare data wrapper
        $wrapper = [
            'data' => $data,
            'cached_at' => time(),
            'is_cached' => true,
            'count' => count($data)
        ];
        
        // Prepare key
        $key = self::PREFIX_HISTORICAL . strtoupper($dataType) . ':' . strtoupper($symbol) . ':' . $timeframe;
        
        // Log operation
        self::logCacheOperation('SET', $key, $wrapper);
        
        // Store in Redis
        try {
            return self::$redis->setex($key, self::TTL_HISTORICAL_DATA, json_encode($wrapper));
        } catch (Exception $e) {
            error_log("MarketDataCache: Error caching historical data: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Retrieve historical market data
     * 
     * @param string $dataType Data type
     * @param string $symbol Symbol or identifier
     * @param string $timeframe Timeframe
     * @return array|null Historical data or null if not found/expired
     */
    public static function getHistoricalData($dataType, $symbol, $timeframe) {
        self::init();
        
        $key = self::PREFIX_HISTORICAL . strtoupper($dataType) . ':' . strtoupper($symbol) . ':' . $timeframe;
        
        try {
            $data = self::$redis->get($key);
            
            if ($data) {
                self::logCacheOperation('GET', $key, null, true);
                $wrapper = json_decode($data, true);
                return $wrapper['data'];
            } else {
                self::logCacheOperation('GET', $key, null, false);
                return null;
            }
        } catch (Exception $e) {
            error_log("MarketDataCache: Error retrieving historical data: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Batch update multiple market data entries
     * 
     * @param array $dataItems Array of data items to cache
     * @return array Results with success/failure status
     */
    public static function batchUpdate($dataItems) {
        self::init();
        
        $results = [];
        
        foreach ($dataItems as $item) {
            $result = false;
            
            if (!isset($item['type']) || !isset($item['data'])) {
                $results[] = [
                    'status' => 'error',
                    'message' => 'Invalid data item format'
                ];
                continue;
            }
            
            switch ($item['type']) {
                case 'stock':
                    $result = self::setStockData($item['symbol'], $item['data']);
                    break;
                case 'forex':
                    $result = self::setForexData($item['base'], $item['target'], $item['data']);
                    break;
                case 'crypto':
                    $result = self::setCryptoData($item['symbol'], $item['data']);
                    break;
                case 'index':
                    $result = self::setMarketIndexData($item['index'], $item['data']);
                    break;
                case 'bond':
                    $result = self::setBondData($item['bond'], $item['data']);
                    break;
                case 'historical':
                    $result = self::setHistoricalData($item['dataType'], $item['symbol'], $item['timeframe'], $item['data']);
                    break;
                default:
                    $results[] = [
                        'status' => 'error',
                        'message' => 'Unknown data type: ' . $item['type']
                    ];
                    continue;
            }
            
            $results[] = [
                'status' => $result ? 'success' : 'error',
                'type' => $item['type'],
                'identifier' => isset($item['symbol']) ? $item['symbol'] : (isset($item['index']) ? $item['index'] : '')
            ];
        }
        
        return $results;
    }
    
    /**
     * Check if cached data is still valid or needs refresh
     * 
     * @param array $data Cached data
     * @param int $maxAge Maximum age in seconds
     * @return bool True if data is still valid
     */
    public static function isDataValid($data, $maxAge = null) {
        if (!isset($data['cached_at'])) {
            return false;
        }
        
        if ($maxAge === null) {
            return true; // Use TTL mechanism in Redis instead
        }
        
        $age = time() - $data['cached_at'];
        return $age <= $maxAge;
    }
    
    /**
     * Clear expired market data from cache
     * 
     * @return int Number of items cleared
     */
    public static function clearExpiredData() {
        // Redis handles TTL expiration automatically
        return 0;
    }
    
    /**
     * Get cache statistics
     * 
     * @return array Statistics about cache usage
     */
    public static function getCacheStats() {
        self::init();
        
        try {
            $info = self::$redis->info();
            
            return [
                'hits' => isset($info['keyspace_hits']) ? $info['keyspace_hits'] : 0,
                'misses' => isset($info['keyspace_misses']) ? $info['keyspace_misses'] : 0,
                'memory_used' => isset($info['used_memory_human']) ? $info['used_memory_human'] : 'unknown',
                'uptime' => isset($info['uptime_in_seconds']) ? $info['uptime_in_seconds'] : 0,
                'total_connections' => isset($info['total_connections_received']) ? $info['total_connections_received'] : 0,
                'market_data_keys' => self::countMarketDataKeys()
            ];
        } catch (Exception $e) {
            error_log("MarketDataCache: Error getting cache stats: " . $e->getMessage());
            return [
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Count all market data keys in cache
     * 
     * @return array Count of keys by type
     */
    public static function countMarketDataKeys() {
        self::init();
        
        $counts = [
            'stock' => 0,
            'forex' => 0,
            'crypto' => 0,
            'index' => 0,
            'bond' => 0,
            'historical' => 0,
            'total' => 0
        ];
        
        try {
            // Count stock keys
            $stockKeys = self::$redis->keys(self::PREFIX_STOCK . '*');
            $counts['stock'] = count($stockKeys);
            
            // Count forex keys
            $forexKeys = self::$redis->keys(self::PREFIX_FOREX . '*');
            $counts['forex'] = count($forexKeys);
            
            // Count crypto keys
            $cryptoKeys = self::$redis->keys(self::PREFIX_CRYPTO . '*');
            $counts['crypto'] = count($cryptoKeys);
            
            // Count index keys
            $indexKeys = self::$redis->keys(self::PREFIX_INDEX . '*');
            $counts['index'] = count($indexKeys);
            
            // Count bond keys
            $bondKeys = self::$redis->keys(self::PREFIX_BOND . '*');
            $counts['bond'] = count($bondKeys);
            
            // Count historical keys
            $historicalKeys = self::$redis->keys(self::PREFIX_HISTORICAL . '*');
            $counts['historical'] = count($historicalKeys);
            
            // Calculate total
            $counts['total'] = $counts['stock'] + $counts['forex'] + $counts['crypto'] + 
                               $counts['index'] + $counts['bond'] + $counts['historical'];
            
            return $counts;
        } catch (Exception $e) {
            error_log("MarketDataCache: Error counting keys: " . $e->getMessage());
            return $counts;
        }
    }
    
    /**
     * Validate stock data before caching
     * 
     * @param array $data Stock data to validate
     * @return bool Validation result
     */
    private static function validateStockData($data) {
        // Required fields
        $required = ['price', 'change', 'change_percent', 'volume'];
        
        foreach ($required as $field) {
            if (!isset($data[$field])) {
                return false;
            }
        }
        
        // Validate numeric fields
        if (!is_numeric($data['price']) || !is_numeric($data['change']) || 
            !is_numeric($data['change_percent']) || !is_numeric($data['volume'])) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Log cache operations for analytics and auditing
     * 
     * @param string $operation Operation (SET, GET, etc.)
     * @param string $key Cache key
     * @param mixed $data Data (for SET operations)
     * @param bool $hit Whether operation was a cache hit (for GET)
     * @return void
     */
    private static function logCacheOperation($operation, $key, $data = null, $hit = null) {
        // In production, this could log to a database or file
        // For this implementation, we'll just use error_log
        
        $logData = [
            'timestamp' => date('Y-m-d H:i:s'),
            'operation' => $operation,
            'key' => $key
        ];
        
        if ($operation === 'GET' && $hit !== null) {
            $logData['hit'] = $hit ? 'yes' : 'no';
        }
        
        // For debugging only - in production, don't log sensitive data
        // if ($data !== null && $operation === 'SET') {
        //     $logData['data_size'] = strlen(json_encode($data));
        // }
        
        // Log to your preferred location
        // error_log("CacheOperation: " . json_encode($logData));
    }
    
    /**
     * Get the time-to-live (TTL) of a cached item
     * 
     * @param string $key Cache key
     * @return int|bool TTL in seconds or false if key doesn't exist
     */
    public static function getTTL($key) {
        self::init();
        
        try {
            return self::$redis->ttl($key);
        } catch (Exception $e) {
            error_log("MarketDataCache: Error getting TTL: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Manually invalidate cache entry
     * 
     * @param string $key Cache key to invalidate
     * @return bool Success status
     */
    public static function invalidateCache($key) {
        self::init();
        
        try {
            self::logCacheOperation('INVALIDATE', $key);
            return self::$redis->del($key);
        } catch (Exception $e) {
            error_log("MarketDataCache: Error invalidating cache: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Implement market alert detection based on cached data
     * 
     * @param string $symbol Symbol to check for alerts
     * @param array $thresholds Threshold values that trigger alerts
     * @return array|null Alert data if threshold exceeded, null otherwise
     */
    public static function checkAlertThresholds($symbol, $thresholds) {
        // Get current data
        $data = self::getStockData($symbol);
        
        if (!$data) {
            return null;
        }
        
        $alerts = [];
        
        // Check price thresholds
        if (isset($thresholds['price'])) {
            if ($thresholds['price']['direction'] === 'above' && $data['price'] > $thresholds['price']['value']) {
                $alerts[] = [
                    'type' => 'price_above',
                    'current' => $data['price'],
                    'threshold' => $thresholds['price']['value'],
                    'symbol' => $symbol
                ];
            } elseif ($thresholds['price']['direction'] === 'below' && $data['price'] < $thresholds['price']['value']) {
                $alerts[] = [
                    'type' => 'price_below',
                    'current' => $data['price'],
                    'threshold' => $thresholds['price']['value'],
                    'symbol' => $symbol
                ];
            }
        }
        
        // Check percent change thresholds
        if (isset($thresholds['change_percent'])) {
            $changeValue = abs($data['change_percent']);
            $thresholdValue = abs($thresholds['change_percent']['value']);
            
            if ($changeValue >= $thresholdValue) {
                $alerts[] = [
                    'type' => $data['change_percent'] > 0 ? 'percent_gain' : 'percent_loss',
                    'current' => $data['change_percent'],
                    'threshold' => $thresholds['change_percent']['value'],
                    'symbol' => $symbol
                ];
            }
        }
        
        // Check volume thresholds
        if (isset($thresholds['volume']) && $data['volume'] > $thresholds['volume']['value']) {
            $alerts[] = [
                'type' => 'volume_spike',
                'current' => $data['volume'],
                'threshold' => $thresholds['volume']['value'],
                'symbol' => $symbol
            ];
        }
        
        return empty($alerts) ? null : $alerts;
    }
    
    /**
     * Get historical trend data for visualization
     * 
     * @param string $symbol Symbol to get trend data for
     * @param string $timeframe Timeframe (1d, 1w, 1m, etc.)
     * @return array Formatted data for chart visualization
     */
    public static function getTrendData($symbol, $timeframe) {
        // Try to get from cache first
        $data = self::getHistoricalData('stock', $symbol, $timeframe);
        
        if (!$data) {
            // If not in cache, return empty array
            // In a real implementation, you might fetch from API and then cache
            return [];
        }
        
        // Format data for visualization
        $chartData = [];
        
        foreach ($data as $point) {
            $chartData[] = [
                'date' => date('Y-m-d', $point['timestamp']),
                'value' => $point['price'],
                'volume' => $point['volume']
            ];
        }
        
        return $chartData;
    }
}
?>
