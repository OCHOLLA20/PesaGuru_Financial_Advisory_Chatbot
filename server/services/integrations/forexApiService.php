<?php
/**
 * PesaGuru Forex API Service
 * 
 * Provides methods to fetch real-time and historical forex exchange rates
 * with a focus on Kenyan Shilling (KES) conversions.
 * 
 * @package PesaGuru
 * @subpackage Services\Integrations
 */

namespace PesaGuru\Services\Integrations;

class ForexApiService {
    /**
     * @var string RapidAPI key for authentication
     */
    private $apiKey;
    
    /**
     * @var string Exchange Rates API host
     */
    private $apiHost = 'exchange-rates7.p.rapidapi.com';
    
    /**
     * @var object Redis instance for caching
     */
    private $cache;
    
    /**
     * @var int Cache expiry time in seconds (1 hour)
     */
    private $cacheExpiry = 3600;
    
    /**
     * @var array Default base currencies for KES conversion
     */
    private $defaultCurrencies = ['USD', 'EUR', 'GBP', 'CNY', 'ZAR', 'JPY', 'AED'];
    
    /**
     * Constructor
     * 
     * @param string $apiKey RapidAPI key
     * @param object $cache Redis cache instance
     */
    public function __construct($apiKey = null, $cache = null) {
        // Load API key from environment if not provided
        $this->apiKey = $apiKey ?? getenv('RAPIDAPI_KEY') ?? '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581';
        $this->cache = $cache;
        
        // Validate API key
        if (empty($this->apiKey)) {
            throw new \Exception('Forex API key is required');
        }
    }
    
    /**
     * Get current exchange rates for KES (Kenyan Shilling)
     * 
     * @param string $base Base currency (default KES)
     * @param array $currencies List of currencies to convert to/from
     * @return array Exchange rates data
     */
    public function getCurrentExchangeRates($base = 'KES', $currencies = []) {
        // If no currencies specified, use defaults
        if (empty($currencies)) {
            $currencies = $this->defaultCurrencies;
        }
        
        // Generate cache key
        $cacheKey = "forex_rates:{$base}:" . implode(',', $currencies);
        
        // Try to get from cache first
        if ($this->cache) {
            $cachedData = $this->cache->get($cacheKey);
            if ($cachedData) {
                return json_decode($cachedData, true);
            }
        }
        
        // Prepare currencies string
        $currenciesStr = implode(',', $currencies);
        
        try {
            // Make API request
            $response = $this->makeApiRequest('/latest', [
                'base' => $base,
                'symbols' => $currenciesStr
            ]);
            
            // Process response
            $result = [
                'base' => $response['base'] ?? $base,
                'date' => $response['date'] ?? date('Y-m-d'),
                'rates' => $response['rates'] ?? [],
                'timestamp' => time(),
                'source' => 'Exchange Rates API'
            ];
            
            // Cache the result
            if ($this->cache) {
                $this->cache->setex($cacheKey, $this->cacheExpiry, json_encode($result));
            }
            
            return $result;
        } catch (\Exception $e) {
            $this->logError('Error fetching current exchange rates: ' . $e->getMessage());
            return [
                'error' => true,
                'message' => 'Failed to fetch exchange rates',
                'details' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Get historical exchange rates for a specific date
     * 
     * @param string $date Date in YYYY-MM-DD format
     * @param string $base Base currency (default KES)
     * @param array $currencies List of currencies to convert to/from
     * @return array Historical exchange rates data
     */
    public function getHistoricalExchangeRates($date, $base = 'KES', $currencies = []) {
        // Validate date format
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) {
            return ['error' => true, 'message' => 'Invalid date format. Use YYYY-MM-DD'];
        }
        
        // If no currencies specified, use defaults
        if (empty($currencies)) {
            $currencies = $this->defaultCurrencies;
        }
        
        // Generate cache key
        $cacheKey = "forex_historical:{$date}:{$base}:" . implode(',', $currencies);
        
        // Try to get from cache first
        if ($this->cache) {
            $cachedData = $this->cache->get($cacheKey);
            if ($cachedData) {
                return json_decode($cachedData, true);
            }
        }
        
        // Prepare currencies string
        $currenciesStr = implode(',', $currencies);
        
        try {
            // Make API request
            $response = $this->makeApiRequest('/' . $date, [
                'base' => $base,
                'symbols' => $currenciesStr
            ]);
            
            // Process response
            $result = [
                'base' => $response['base'] ?? $base,
                'date' => $response['date'] ?? $date,
                'rates' => $response['rates'] ?? [],
                'timestamp' => time(),
                'source' => 'Exchange Rates API'
            ];
            
            // Cache the result (historical data can be cached longer)
            if ($this->cache) {
                $this->cache->setex($cacheKey, $this->cacheExpiry * 24, json_encode($result));
            }
            
            return $result;
        } catch (\Exception $e) {
            $this->logError('Error fetching historical exchange rates: ' . $e->getMessage());
            return [
                'error' => true,
                'message' => 'Failed to fetch historical exchange rates',
                'details' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Convert amount from one currency to another
     * 
     * @param float $amount Amount to convert
     * @param string $from Source currency code
     * @param string $to Target currency code
     * @return array Conversion result
     */
    public function convertCurrency($amount, $from = 'KES', $to = 'USD') {
        if (!is_numeric($amount) || $amount <= 0) {
            return ['error' => true, 'message' => 'Invalid amount'];
        }
        
        // Generate cache key
        $cacheKey = "forex_convert:{$from}:{$to}";
        
        // Try to get exchange rate from cache first
        $rate = null;
        if ($this->cache) {
            $cachedRate = $this->cache->get($cacheKey);
            if ($cachedRate) {
                $rate = (float)$cachedRate;
            }
        }
        
        // If rate not in cache, fetch it
        if ($rate === null) {
            try {
                $response = $this->makeApiRequest('/latest', [
                    'base' => $from,
                    'symbols' => $to
                ]);
                
                if (isset($response['rates'][$to])) {
                    $rate = (float)$response['rates'][$to];
                    
                    // Cache the rate
                    if ($this->cache) {
                        $this->cache->setex($cacheKey, $this->cacheExpiry, (string)$rate);
                    }
                } else {
                    return [
                        'error' => true,
                        'message' => 'Exchange rate not available'
                    ];
                }
            } catch (\Exception $e) {
                $this->logError('Error fetching exchange rate for conversion: ' . $e->getMessage());
                return [
                    'error' => true,
                    'message' => 'Failed to fetch exchange rate',
                    'details' => $e->getMessage()
                ];
            }
        }
        
        // Calculate converted amount
        $convertedAmount = $amount * $rate;
        
        return [
            'from' => [
                'currency' => $from,
                'amount' => $amount
            ],
            'to' => [
                'currency' => $to,
                'amount' => $convertedAmount
            ],
            'rate' => $rate,
            'timestamp' => time()
        ];
    }
    
    /**
     * Get time series data for a currency pair
     * 
     * @param string $startDate Start date (YYYY-MM-DD)
     * @param string $endDate End date (YYYY-MM-DD)
     * @param string $base Base currency (default KES)
     * @param array $currencies List of currencies to include
     * @return array Time series data
     */
    public function getTimeSeriesData($startDate, $endDate, $base = 'KES', $currencies = []) {
        // Validate date formats
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $startDate) || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $endDate)) {
            return ['error' => true, 'message' => 'Invalid date format. Use YYYY-MM-DD'];
        }
        
        // If no currencies specified, use USD as default
        if (empty($currencies)) {
            $currencies = ['USD'];
        }
        
        // Generate cache key
        $cacheKey = "forex_timeseries:{$startDate}:{$endDate}:{$base}:" . implode(',', $currencies);
        
        // Try to get from cache first
        if ($this->cache) {
            $cachedData = $this->cache->get($cacheKey);
            if ($cachedData) {
                return json_decode($cachedData, true);
            }
        }
        
        // Prepare currencies string
        $currenciesStr = implode(',', $currencies);
        
        try {
            // Make API request
            $response = $this->makeApiRequest('/timeseries', [
                'start_date' => $startDate,
                'end_date' => $endDate,
                'base' => $base,
                'symbols' => $currenciesStr
            ]);
            
            // Process response
            $result = [
                'base' => $response['base'] ?? $base,
                'start_date' => $startDate,
                'end_date' => $endDate,
                'rates' => $response['rates'] ?? [],
                'timestamp' => time(),
                'source' => 'Exchange Rates API'
            ];
            
            // Cache the result (time series data can be cached longer)
            if ($this->cache) {
                $this->cache->setex($cacheKey, $this->cacheExpiry * 24, json_encode($result));
            }
            
            return $result;
        } catch (\Exception $e) {
            $this->logError('Error fetching time series data: ' . $e->getMessage());
            return [
                'error' => true,
                'message' => 'Failed to fetch time series data',
                'details' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Get all available currency codes
     * 
     * @return array List of currency codes and names
     */
    public function getCurrencyCodes() {
        // Generate cache key
        $cacheKey = "forex_currencies";
        
        // Try to get from cache first
        if ($this->cache) {
            $cachedData = $this->cache->get($cacheKey);
            if ($cachedData) {
                return json_decode($cachedData, true);
            }
        }
        
        try {
            // Make API request
            $response = $this->makeApiRequest('/codes');
            
            if (isset($response['supported_codes']) && is_array($response['supported_codes'])) {
                $currencies = [];
                
                // Format the response
                foreach ($response['supported_codes'] as $currency) {
                    if (is_array($currency) && count($currency) >= 2) {
                        $currencies[$currency[0]] = $currency[1];
                    }
                }
                
                $result = [
                    'currencies' => $currencies,
                    'count' => count($currencies),
                    'timestamp' => time()
                ];
                
                // Cache the result (currency codes change rarely)
                if ($this->cache) {
                    $this->cache->setex($cacheKey, $this->cacheExpiry * 24 * 7, json_encode($result));
                }
                
                return $result;
            } else {
                return [
                    'error' => true,
                    'message' => 'Invalid response format for currency codes'
                ];
            }
        } catch (\Exception $e) {
            $this->logError('Error fetching currency codes: ' . $e->getMessage());
            return [
                'error' => true,
                'message' => 'Failed to fetch currency codes',
                'details' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Get common Kenyan exchange rates formatted for display
     * 
     * @return array Formatted exchange rates for common currencies
     */
    public function getKenyanForexRates() {
        // Get current rates
        $ratesFromKES = $this->getCurrentExchangeRates('KES');
        $ratesToKES = $this->getCurrentExchangeRates('USD', ['KES']);
        
        if (isset($ratesFromKES['error']) || isset($ratesToKES['error'])) {
            return [
                'error' => true,
                'message' => 'Failed to fetch Kenyan forex rates'
            ];
        }
        
        // Format the response for the frontend
        $formattedRates = [
            'date' => $ratesFromKES['date'],
            'timestamp' => time(),
            'base_currency' => 'KES',
            'rates' => []
        ];
        
        // Format rates from KES to other currencies
        foreach ($this->defaultCurrencies as $currency) {
            if (isset($ratesFromKES['rates'][$currency])) {
                $rate = $ratesFromKES['rates'][$currency];
                $inverseRate = 1 / $rate;
                
                $formattedRates['rates'][$currency] = [
                    'code' => $currency,
                    'name' => $this->getCurrencyName($currency),
                    'kes_to_foreign' => $rate,
                    'foreign_to_kes' => $inverseRate,
                    'formatted' => [
                        'kes_to_foreign' => "1 KES = " . number_format($rate, 4) . " $currency",
                        'foreign_to_kes' => "1 $currency = " . number_format($inverseRate, 2) . " KES"
                    ]
                ];
            }
        }
        
        return $formattedRates;
    }
    
    /**
     * Make API request to the Exchange Rates API
     * 
     * @param string $endpoint API endpoint
     * @param array $params Query parameters
     * @return array API response
     * @throws \Exception If API request fails
     */
    private function makeApiRequest($endpoint, $params = []) {
        // Build request URL
        $url = "https://{$this->apiHost}{$endpoint}";
        
        // Add query parameters if any
        if (!empty($params)) {
            $url .= '?' . http_build_query($params);
        }
        
        // Initialize cURL
        $curl = curl_init();
        
        // Set cURL options
        curl_setopt_array($curl, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_ENCODING => "",
            CURLOPT_MAXREDIRS => 10,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
            CURLOPT_CUSTOMREQUEST => "GET",
            CURLOPT_HTTPHEADER => [
                "x-rapidapi-host: {$this->apiHost}",
                "x-rapidapi-key: {$this->apiKey}"
            ],
        ]);
        
        // Execute cURL request
        $response = curl_exec($curl);
        $err = curl_error($curl);
        $statusCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        
        // Close cURL
        curl_close($curl);
        
        // Handle cURL errors
        if ($err) {
            throw new \Exception("cURL Error: " . $err);
        }
        
        // Parse JSON response
        $responseData = json_decode($response, true);
        
        // Handle API errors
        if ($statusCode >= 400 || !$responseData || isset($responseData['error'])) {
            $errorMessage = isset($responseData['error']['message']) 
                ? $responseData['error']['message'] 
                : "API Error (HTTP $statusCode)";
            
            throw new \Exception($errorMessage);
        }
        
        return $responseData;
    }
    
    /**
     * Get currency name from currency code
     * 
     * @param string $code Currency code
     * @return string Currency name
     */
    private function getCurrencyName($code) {
        $currencyNames = [
            'USD' => 'US Dollar',
            'EUR' => 'Euro',
            'GBP' => 'British Pound',
            'JPY' => 'Japanese Yen',
            'CHF' => 'Swiss Franc',
            'CAD' => 'Canadian Dollar',
            'AUD' => 'Australian Dollar',
            'NZD' => 'New Zealand Dollar',
            'ZAR' => 'South African Rand',
            'CNY' => 'Chinese Yuan',
            'INR' => 'Indian Rupee',
            'BRL' => 'Brazilian Real',
            'RUB' => 'Russian Ruble',
            'KRW' => 'South Korean Won',
            'SGD' => 'Singapore Dollar',
            'HKD' => 'Hong Kong Dollar',
            'MXN' => 'Mexican Peso',
            'AED' => 'UAE Dirham',
            'KES' => 'Kenyan Shilling',
            'TZS' => 'Tanzanian Shilling',
            'UGX' => 'Ugandan Shilling',
            'RWF' => 'Rwandan Franc',
            'ETB' => 'Ethiopian Birr',
            'NGN' => 'Nigerian Naira'
        ];
        
        return $currencyNames[$code] ?? $code;
    }
    
    /**
     * Log error message
     * 
     * @param string $message Error message
     */
    private function logError($message) {
        // Log to file
        $logFile = __DIR__ . '/../../../../logs/forex_api_errors.log';
        $timestamp = date('Y-m-d H:i:s');
        $logMessage = "[$timestamp] $message" . PHP_EOL;
        
        // Ensure directory exists
        $logDir = dirname($logFile);
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }
        
        // Append to log file
        file_put_contents($logFile, $logMessage, FILE_APPEND);
    }
}