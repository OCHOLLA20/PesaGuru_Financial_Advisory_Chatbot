<?php

class NSEApiService {
    private $db;
    private $apiKey;
    private $apiUrl;
    private $cacheTime = 1800; // 30 minutes in seconds
    
    /**
     * Constructor initializes service
     */
    public function __construct() {
        // Get database connection
        require_once __DIR__ . '/../../config/db.php';
        $this->db = getDbConnection();
        
        // Load API credentials
        require_once __DIR__ . '/../../config/api_keys.php';
        $this->apiKey = $apiKeys['nse_api']['key'] ?? '';
        $this->apiUrl = $apiKeys['nse_api']['url'] ?? 'https://api.nse.co.ke';
    }
    
    /**
     * Get information about a specific stock
     * 
     * @param string $stockCode Stock code (e.g., SCOM for Safaricom)
     * @return array Stock information
     */
    public function getStockInfo($stockCode) {
        try {
            // First try to get from cache
            $cachedData = $this->getFromCache("stock_info_{$stockCode}");
            if ($cachedData) {
                return $cachedData;
            }
            
            // If not in cache, try to get from database
            $stmt = $this->db->prepare("
                SELECT s.*, sect.name as sector
                FROM stocks s
                LEFT JOIN sectors sect ON s.sector_id = sect.id
                WHERE s.code = ?
            ");
            $stmt->bind_param("s", $stockCode);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $stockInfo = $result->fetch_assoc();
                
                // Save to cache and return
                $this->saveToCache("stock_info_{$stockCode}", [
                    'success' => true,
                    'code' => $stockInfo['code'],
                    'name' => $stockInfo['name'],
                    'sector' => $stockInfo['sector'],
                    '52_week_high' => $stockInfo['high_52_week'],
                    '52_week_low' => $stockInfo['low_52_week'],
                    'last_price' => $stockInfo['last_price'],
                    'change' => $stockInfo['change'],
                    'change_percent' => $stockInfo['change_percent'],
                    'volume' => $stockInfo['volume']
                ]);
                
                return [
                    'success' => true,
                    'code' => $stockInfo['code'],
                    'name' => $stockInfo['name'],
                    'sector' => $stockInfo['sector'],
                    '52_week_high' => $stockInfo['high_52_week'],
                    '52_week_low' => $stockInfo['low_52_week'],
                    'last_price' => $stockInfo['last_price'],
                    'change' => $stockInfo['change'],
                    'change_percent' => $stockInfo['change_percent'],
                    'volume' => $stockInfo['volume']
                ];
            }
            
            // If not in database, simulate NSE API call
            if (in_array($stockCode, $this->getKnownStockCodes())) {
                $stockInfo = $this->simulateStockInfo($stockCode);
                
                // Save to cache and return
                $this->saveToCache("stock_info_{$stockCode}", $stockInfo);
                return $stockInfo;
            }
            
            return [
                'success' => false,
                'message' => 'Stock not found'
            ];
        } catch (Exception $e) {
            error_log("Error getting stock info: " . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Error retrieving stock information'
            ];
        }
    }
    
    /**
     * Get current prices for multiple stocks
     * 
     * @param array $stockCodes Array of stock codes
     * @return array Stock prices indexed by stock code
     */
    public function getStockPrices($stockCodes) {
        try {
            $prices = [];
            
            foreach ($stockCodes as $stockCode) {
                // Check cache first
                $cachedData = $this->getFromCache("stock_price_{$stockCode}");
                
                if ($cachedData) {
                    $prices[$stockCode] = $cachedData;
                    continue;
                }
                
                // Try to get from database
                $stmt = $this->db->prepare("
                    SELECT code, last_price as price, change, change_percent, volume, updated_at
                    FROM stocks 
                    WHERE code = ?
                ");
                $stmt->bind_param("s", $stockCode);
                $stmt->execute();
                $result = $stmt->get_result();
                
                if ($result->num_rows > 0) {
                    $stockData = $result->fetch_assoc();
                    
                    $prices[$stockCode] = [
                        'price' => $stockData['price'],
                        'change' => $stockData['change'],
                        'change_percent' => $stockData['change_percent'],
                        'volume' => $stockData['volume'],
                        'updated_at' => $stockData['updated_at']
                    ];
                    
                    // Save to cache
                    $this->saveToCache("stock_price_{$stockCode}", $prices[$stockCode]);
                    continue;
                }
                
                // If not in database, simulate NSE API call
                $stockInfo = $this->simulateStockInfo($stockCode);
                
                if ($stockInfo['success']) {
                    $prices[$stockCode] = [
                        'price' => $stockInfo['last_price'],
                        'change' => $stockInfo['change'],
                        'change_percent' => $stockInfo['change_percent'],
                        'volume' => $stockInfo['volume'],
                        'updated_at' => date('Y-m-d H:i:s')
                    ];
                    
                    // Save to cache
                    $this->saveToCache("stock_price_{$stockCode}", $prices[$stockCode]);
                }
            }
            
            return $prices;
        } catch (Exception $e) {
            error_log("Error getting stock prices: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get recommended stocks based on risk profile
     * 
     * @param string $riskLevel Risk level (conservative, moderate, aggressive)
     * @param int $limit Number of recommendations to return
     * @return array Recommended stocks
     */
    public function getRecommendedStocks($riskLevel = 'moderate', $limit = 5) {
        try {
            // Map risk levels to sectors that match the profile
            $sectorMap = [
                'conservative' => ['Banking', 'Energy', 'Utilities', 'FMCG'],
                'moderate' => ['Banking', 'Manufacturing', 'Commercial', 'Insurance', 'Investment'],
                'aggressive' => ['Technology', 'Construction', 'Agricultural', 'Automobile', 'Investment']
            ];
            
            $sectors = $sectorMap[$riskLevel] ?? $sectorMap['moderate'];
            
            // Get stocks from selected sectors with good performance
            $stmt = $this->db->prepare("
                SELECT s.code, s.name, s.last_price, s.change_percent, sect.name as sector
                FROM stocks s
                LEFT JOIN sectors sect ON s.sector_id = sect.id
                WHERE sect.name IN ('" . implode("','", $sectors) . "')
                ORDER BY 
                    CASE 
                        WHEN ? = 'conservative' THEN s.volatility ASC
                        WHEN ? = 'aggressive' THEN s.change_percent DESC
                        ELSE s.dividend_yield DESC
                    END
                LIMIT ?
            ");
            
            $stmt->bind_param("ssi", $riskLevel, $riskLevel, $limit);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $recommendations = [];
            
            if ($result->num_rows > 0) {
                while ($row = $result->fetch_assoc()) {
                    $recommendations[] = [
                        'code' => $row['code'],
                        'name' => $row['name'],
                        'price' => $row['last_price'],
                        'change_percent' => $row['change_percent'],
                        'sector' => $row['sector']
                    ];
                }
            } else {
                // If no data in database, simulate recommendations
                $recommendations = $this->simulateRecommendations($riskLevel, $limit);
            }
            
            return $recommendations;
        } catch (Exception $e) {
            error_log("Error getting recommended stocks: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get market summary data
     * 
     * @return array Market summary
     */
    public function getMarketSummary() {
        try {
            // Try to get from cache
            $cachedData = $this->getFromCache("market_summary");
            if ($cachedData) {
                return $cachedData;
            }
            
            // Get market data from database
            $stmt = $this->db->prepare("
                SELECT 
                    ms.nse_20_index, 
                    ms.nse_25_index, 
                    ms.nse_all_share_index,
                    ms.market_cap,
                    ms.equity_turnover,
                    ms.bonds_turnover,
                    ms.updated_at
                FROM market_summary ms
                ORDER BY ms.updated_at DESC
                LIMIT 1
            ");
            
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $summary = $result->fetch_assoc();
                
                $marketSummary = [
                    'success' => true,
                    'nse_20_index' => $summary['nse_20_index'],
                    'nse_25_index' => $summary['nse_25_index'],
                    'nse_all_share_index' => $summary['nse_all_share_index'],
                    'market_cap' => $summary['market_cap'],
                    'equity_turnover' => $summary['equity_turnover'],
                    'bonds_turnover' => $summary['bonds_turnover'],
                    'updated_at' => $summary['updated_at']
                ];
                
                // Save to cache
                $this->saveToCache("market_summary", $marketSummary);
                
                return $marketSummary;
            }
            
            // If no data in database, simulate market summary
            $marketSummary = $this->simulateMarketSummary();
            
            // Save to cache
            $this->saveToCache("market_summary", $marketSummary);
            
            return $marketSummary;
        } catch (Exception $e) {
            error_log("Error getting market summary: " . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Error retrieving market summary'
            ];
        }
    }
    
    /**
     * Get sector performance data
     * 
     * @return array Sector performance
     */
    public function getSectorPerformance() {
        try {
            // Try to get from cache
            $cachedData = $this->getFromCache("sector_performance");
            if ($cachedData) {
                return $cachedData;
            }
            
            // Get sector data from database
            $stmt = $this->db->prepare("
                SELECT 
                    s.name, 
                    s.performance_1d, 
                    s.performance_1w,
                    s.performance_1m,
                    s.performance_ytd,
                    s.market_cap,
                    s.updated_at
                FROM sectors s
                ORDER BY s.performance_1m DESC
            ");
            
            $stmt->execute();
            $result = $stmt->get_result();
            
            $sectors = [];
            
            if ($result->num_rows > 0) {
                while ($row = $result->fetch_assoc()) {
                    $sectors[] = [
                        'name' => $row['name'],
                        'performance_1d' => $row['performance_1d'],
                        'performance_1w' => $row['performance_1w'],
                        'performance_1m' => $row['performance_1m'],
                        'performance_ytd' => $row['performance_ytd'],
                        'market_cap' => $row['market_cap']
                    ];
                }
                
                $sectorPerformance = [
                    'success' => true,
                    'sectors' => $sectors,
                    'updated_at' => $row['updated_at']
                ];
                
                // Save to cache
                $this->saveToCache("sector_performance", $sectorPerformance);
                
                return $sectorPerformance;
            }
            
            // If no data in database, simulate sector performance
            $sectorPerformance = $this->simulateSectorPerformance();
            
            // Save to cache
            $this->saveToCache("sector_performance", $sectorPerformance);
            
            return $sectorPerformance;
        } catch (Exception $e) {
            error_log("Error getting sector performance: " . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Error retrieving sector performance'
            ];
        }
    }
    
    /**
     * Get market news
     * 
     * @param int $limit Number of news items to return
     * @return array Market news
     */
    public function getMarketNews($limit = 5) {
        try {
            // Try to get from cache
            $cachedData = $this->getFromCache("market_news_{$limit}");
            if ($cachedData) {
                return $cachedData;
            }
            
            // Get news from database
            $stmt = $this->db->prepare("
                SELECT 
                    n.id,
                    n.title,
                    n.summary,
                    n.source,
                    n.url,
                    n.published_at
                FROM market_news n
                ORDER BY n.published_at DESC
                LIMIT ?
            ");
            
            $stmt->bind_param("i", $limit);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $news = [];
            
            if ($result->num_rows > 0) {
                while ($row = $result->fetch_assoc()) {
                    $news[] = [
                        'id' => $row['id'],
                        'title' => $row['title'],
                        'summary' => $row['summary'],
                        'source' => $row['source'],
                        'url' => $row['url'],
                        'published_at' => $row['published_at']
                    ];
                }
                
                $marketNews = [
                    'success' => true,
                    'news' => $news
                ];
                
                // Save to cache
                $this->saveToCache("market_news_{$limit}", $marketNews);
                
                return $marketNews;
            }
            
            // If no data in database, simulate market news
            $marketNews = $this->simulateMarketNews($limit);
            
            // Save to cache
            $this->saveToCache("market_news_{$limit}", $marketNews);
            
            return $marketNews;
        } catch (Exception $e) {
            error_log("Error getting market news: " . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Error retrieving market news'
            ];
        }
    }
    
    /**
     * Get historical prices for a stock
     * 
     * @param string $stockCode Stock code
     * @param string $period Period (1d, 1w, 1m, 3m, 6m, 1y, 5y)
     * @return array Historical prices
     */
    public function getHistoricalPrices($stockCode, $period = '1m') {
        try {
            // Try to get from cache
            $cachedData = $this->getFromCache("historical_prices_{$stockCode}_{$period}");
            if ($cachedData) {
                return $cachedData;
            }
            
            // Calculate date range based on period
            $endDate = date('Y-m-d');
            $startDate = null;
            
            switch ($period) {
                case '1d':
                    $startDate = date('Y-m-d', strtotime('-1 day'));
                    break;
                case '1w':
                    $startDate = date('Y-m-d', strtotime('-1 week'));
                    break;
                case '1m':
                    $startDate = date('Y-m-d', strtotime('-1 month'));
                    break;
                case '3m':
                    $startDate = date('Y-m-d', strtotime('-3 months'));
                    break;
                case '6m':
                    $startDate = date('Y-m-d', strtotime('-6 months'));
                    break;
                case '1y':
                    $startDate = date('Y-m-d', strtotime('-1 year'));
                    break;
                case '5y':
                    $startDate = date('Y-m-d', strtotime('-5 years'));
                    break;
                default:
                    $startDate = date('Y-m-d', strtotime('-1 month'));
                    break;
            }
            
            // Get historical prices from database
            $stmt = $this->db->prepare("
                SELECT 
                    hp.date,
                    hp.open,
                    hp.high,
                    hp.low,
                    hp.close,
                    hp.volume
                FROM historical_prices hp
                WHERE hp.stock_code = ? AND hp.date BETWEEN ? AND ?
                ORDER BY hp.date ASC
            ");
            
            $stmt->bind_param("sss", $stockCode, $startDate, $endDate);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $prices = [];
            
            if ($result->num_rows > 0) {
                while ($row = $result->fetch_assoc()) {
                    $prices[] = [
                        'date' => $row['date'],
                        'open' => $row['open'],
                        'high' => $row['high'],
                        'low' => $row['low'],
                        'close' => $row['close'],
                        'volume' => $row['volume']
                    ];
                }
                
                $historicalPrices = [
                    'success' => true,
                    'code' => $stockCode,
                    'period' => $period,
                    'start_date' => $startDate,
                    'end_date' => $endDate,
                    'prices' => $prices
                ];
                
                // Save to cache
                $this->saveToCache("historical_prices_{$stockCode}_{$period}", $historicalPrices);
                
                return $historicalPrices;
            }
            
            // If no data in database, simulate historical prices
            $historicalPrices = $this->simulateHistoricalPrices($stockCode, $startDate, $endDate, $period);
            
            // Save to cache
            $this->saveToCache("historical_prices_{$stockCode}_{$period}", $historicalPrices);
            
            return $historicalPrices;
        } catch (Exception $e) {
            error_log("Error getting historical prices: " . $e->getMessage());
            return [
                'success' => false,
                'message' => 'Error retrieving historical prices'
            ];
        }
    }
    
    /**
     * Get data from cache
     * 
     * @param string $key Cache key
     * @return mixed Cached data or null if not found/expired
     */
    private function getFromCache($key) {
        try {
            $stmt = $this->db->prepare("
                SELECT data, created_at
                FROM api_cache
                WHERE cache_key = ?
            ");
            
            $stmt->bind_param("s", $key);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $row = $result->fetch_assoc();
                $createdTime = strtotime($row['created_at']);
                
                // Check if cache is still valid
                if ((time() - $createdTime) < $this->cacheTime) {
                    return json_decode($row['data'], true);
                }
            }
            
            return null;
        } catch (Exception $e) {
            error_log("Error getting from cache: " . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Save data to cache
     * 
     * @param string $key Cache key
     * @param mixed $data Data to cache
     * @return bool Success status
     */
    private function saveToCache($key, $data) {
        try {
            // First delete any existing cache with the same key
            $stmt = $this->db->prepare("DELETE FROM api_cache WHERE cache_key = ?");
            $stmt->bind_param("s", $key);
            $stmt->execute();
            
            // Insert new cache data
            $stmt = $this->db->prepare("
                INSERT INTO api_cache (cache_key, data, created_at)
                VALUES (?, ?, ?)
            ");
            
            $jsonData = json_encode($data);
            $createdAt = date('Y-m-d H:i:s');
            
            $stmt->bind_param("sss", $key, $jsonData, $createdAt);
            return $stmt->execute();
        } catch (Exception $e) {
            error_log("Error saving to cache: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Get known NSE stock codes
     * 
     * @return array Array of known stock codes
     */
    private function getKnownStockCodes() {
        return [
            'SCOM', 'KCB', 'EQTY', 'BAMB', 'COOP', 'SBIC', 'NCBA',
            'EABL', 'BRIT', 'JUB', 'KPLC', 'KGEN', 'KNRE', 'CTUM',
            'SASN', 'PORT', 'NMG', 'SCAN', 'LIMT', 'BAT', 'C&G',
            'TOTL', 'ORCH', 'KUKZ', 'CARB', 'BOC', 'NSE', 'HFCK',
            'DTK', 'ABSA', 'ICDC', 'TCL', 'MSC', 'CFC', 'XPRS',
            'WTK', 'HAFR', 'LKL', 'UNGA', 'EVRD', 'KAPC', 'KCAS',
            'NBV', 'ARM', 'FAHR', 'KENO', 'FTGH', 'EGAD', 'OCH'
        ];
    }
    
    /**
     * Simulate stock information (for development/testing)
     * 
     * @param string $stockCode Stock code
     * @return array Simulated stock information
     */
    private function simulateStockInfo($stockCode) {
        // Map stock codes to known company names and sectors
        $stockMap = [
            'SCOM' => ['name' => 'Safaricom Plc', 'sector' => 'Technology'],
            'KCB' => ['name' => 'KCB Group Plc', 'sector' => 'Banking'],
            'EQTY' => ['name' => 'Equity Group Holdings Plc', 'sector' => 'Banking'],
            'COOP' => ['name' => 'Co-operative Bank of Kenya Plc', 'sector' => 'Banking'],
            'EABL' => ['name' => 'East African Breweries Plc', 'sector' => 'Manufacturing'],
            'BAMB' => ['name' => 'Bamburi Cement Plc', 'sector' => 'Manufacturing'],
            'SBIC' => ['name' => 'Stanbic Holdings Plc', 'sector' => 'Banking'],
            'ABSA' => ['name' => 'Absa Bank Kenya Plc', 'sector' => 'Banking'],
            'NCBA' => ['name' => 'NCBA Group Plc', 'sector' => 'Banking'],
            'BRIT' => ['name' => 'Britam Holdings Plc', 'sector' => 'Insurance'],
            'JUB' => ['name' => 'Jubilee Holdings Ltd', 'sector' => 'Insurance'],
            'KPLC' => ['name' => 'Kenya Power & Lighting Co Plc', 'sector' => 'Energy'],
            'KGEN' => ['name' => 'Kenya Electricity Generating Co Plc', 'sector' => 'Energy']
        ];
        
        // Get stock name and sector if known, otherwise use defaults
        $stockName = $stockMap[$stockCode]['name'] ?? "$stockCode Stock";
        $stockSector = $stockMap[$stockCode]['sector'] ?? "Other";
        
        // Generate realistic price and metrics
        $basePrice = 0;
        
        switch ($stockCode) {
            case 'SCOM':
                $basePrice = 25.50;
                break;
            case 'KCB':
                $basePrice = 42.75;
                break;
            case 'EQTY':
                $basePrice = 50.25;
                break;
            case 'BAMB':
                $basePrice = 34.80;
                break;
            case 'COOP':
                $basePrice = 13.50;
                break;
            case 'EABL':
                $basePrice = 172.25;
                break;
            default:
                // Generate random price between 5 and 200
                $basePrice = mt_rand(500, 20000) / 100;
                break;
        }
        
        // Add some randomness to the price
        $lastPrice = $basePrice * (1 + (mt_rand(-300, 300) / 10000));
        $lastPrice = round($lastPrice, 2);
        
        // Generate realistic change
        $change = round($lastPrice * (mt_rand(-250, 250) / 10000), 2);
        $changePercent = round(($change / ($lastPrice - $change)) * 100, 2);
        
        // Generate 52-week high/low
        $weekHigh = round($lastPrice * (1 + (mt_rand(300, 800) / 10000)), 2);
        $weekLow = round($lastPrice * (1 - (mt_rand(300, 800) / 10000)), 2);
        
        // Ensure high is always higher than low
        if ($weekHigh < $weekLow) {
            $temp = $weekHigh;
            $weekHigh = $weekLow;
            $weekLow = $temp;
        }
        
        // Generate volume
        $volume = mt_rand(10000, 1000000);
        
        return [
            'success' => true,
            'code' => $stockCode,
            'name' => $stockName,
            'sector' => $stockSector,
            'last_price' => $lastPrice,
            'change' => $change,
            'change_percent' => $changePercent,
            'volume' => $volume,
            '52_week_high' => $weekHigh,
            '52_week_low' => $weekLow
        ];
    }
    
    /**
     * Simulate market summary data (for development/testing)
     * 
     * @return array Simulated market summary
     */
    private function simulateMarketSummary() {
        return [
            'success' => true,
            'nse_20_index' => round(1800 + mt_rand(-50, 50), 2),
            'nse_25_index' => round(3600 + mt_rand(-100, 100), 2),
            'nse_all_share_index' => round(160 + mt_rand(-5, 5), 2),
            'market_cap' => round(2000 + mt_rand(-100, 100), 1) . ' Billion',
            'equity_turnover' => round(500 + mt_rand(-50, 50), 1) . ' Million',
            'bonds_turnover' => round(1000 + mt_rand(-100, 100), 1) . ' Million',
            'updated_at' => date('Y-m-d H:i:s')
        ];
    }
    
    /**
     * Simulate sector performance data (for development/testing)
     * 
     * @return array Simulated sector performance
     */
    private function simulateSectorPerformance() {
        $sectors = [
            'Banking', 'Insurance', 'Manufacturing', 'Energy', 'Technology',
            'Agricultural', 'Commercial', 'Investment', 'Construction', 'Automobile'
        ];
        
        $sectorPerformance = [];
        
        foreach ($sectors as $sector) {
            $sectorPerformance[] = [
                'name' => $sector,
                'performance_1d' => round(mt_rand(-200, 200) / 100, 2),
                'performance_1w' => round(mt_rand(-500, 500) / 100, 2),
                'performance_1m' => round(mt_rand(-1000, 1000) / 100, 2),
                'performance_ytd' => round(mt_rand(-2000, 2000) / 100, 2),
                'market_cap' => round(mt_rand(100, 1000), 1) . ' Billion'
            ];
        }
        
        return [
            'success' => true,
            'sectors' => $sectorPerformance,
            'updated_at' => date('Y-m-d H:i:s')
        ];
    }
    
    /**
     * Simulate market news (for development/testing)
     * 
     * @param int $limit Number of news items to generate
     * @return array Simulated market news
     */
    private function simulateMarketNews($limit = 5) {
        $newsTemplates = [
            [
                'title' => 'Safaricom reports strong Q3 earnings, exceeding analyst expectations',
                'summary' => 'Safaricom Plc announced its Q3 earnings with a 15% increase in profit year-over-year, driven by growth in M-Pesa and data services.',
                'source' => 'Business Daily'
            ],
            [
                'title' => 'KCB completes acquisition of Trust Bank Rwanda',
                'summary' => 'KCB Group has finalized the acquisition of Trust Bank Rwanda, strengthening its presence in East Africa\'s banking sector.',
                'source' => 'The Standard'
            ],
            [
                'title' => 'NSE trading volume hits 6-month high as foreign investors return',
                'summary' => 'Trading volume at the Nairobi Securities Exchange reached a 6-month high as foreign investors increased their positions in Kenyan equities.',
                'source' => 'Reuters'
            ],
            [
                'title' => 'EABL launches KSh 11 billion sustainability investment plan',
                'summary' => 'East African Breweries Plc has announced a KSh 11 billion investment plan focused on sustainable production and reducing carbon emissions.',
                'source' => 'Nation Media'
            ],
            [
                'title' => 'Central Bank holds interest rates steady at 7.5%',
                'summary' => 'The Central Bank of Kenya\'s Monetary Policy Committee has maintained the benchmark interest rate at 7.5%, citing stable inflation outlook.',
                'source' => 'Central Bank of Kenya'
            ],
            [
                'title' => 'Equity Group expands digital banking services, sees 30% uptake',
                'summary' => 'Equity Group has reported a 30% increase in digital banking adoption, as it expands its fintech services across East Africa.',
                'source' => 'Business Daily'
            ],
            [
                'title' => 'Kenya\'s inflation rate drops to 5.7% in February',
                'summary' => 'Kenya\'s year-on-year inflation rate decreased to 5.7% in February from 6.2% in January, according to data from the Kenya National Bureau of Statistics.',
                'source' => 'KNBS'
            ],
            [
                'title' => 'Bamburi Cement reports 12% drop in profit amid rising costs',
                'summary' => 'Bamburi Cement Plc announced a 12% decline in profit for FY 2023, citing increased energy costs and currency fluctuations.',
                'source' => 'The Star'
            ],
            [
                'title' => 'NSE launches new derivatives market with index futures',
                'summary' => 'The Nairobi Securities Exchange has launched a derivatives market, introducing NSE 25 Index futures and single stock futures for major companies.',
                'source' => 'NSE'
            ],
            [
                'title' => 'Kenya Power announces KSh 40 billion grid modernization project',
                'summary' => 'Kenya Power has unveiled a KSh 40 billion grid modernization project aimed at reducing outages and improving electricity distribution efficiency.',
                'source' => 'Kenya Power'
            ]
        ];
        
        // Shuffle news items and take limited number
        shuffle($newsTemplates);
        $newsTemplates = array_slice($newsTemplates, 0, min($limit, count($newsTemplates)));
        
        $news = [];
        $currentDate = time();
        
        foreach ($newsTemplates as $index => $template) {
            // Generate random publication date within last 7 days
            $publishedAt = date('Y-m-d H:i:s', $currentDate - mt_rand(0, 7 * 24 * 60 * 60));
            
            $news[] = [
                'id' => $index + 1,
                'title' => $template['title'],
                'summary' => $template['summary'],
                'source' => $template['source'],
                'url' => 'https://example.com/market-news/' . ($index + 1),
                'published_at' => $publishedAt
            ];
        }
        
        return [
            'success' => true,
            'news' => $news
        ];
    }
    
    /**
     * Simulate historical prices for a stock (for development/testing)
     * 
     * @param string $stockCode Stock code
     * @param string $startDate Start date
     * @param string $endDate End date
     * @param string $period Period
     * @return array Simulated historical prices
     */
    private function simulateHistoricalPrices($stockCode, $startDate, $endDate, $period) {
        // Get stock info to base simulation on
        $stockInfo = $this->simulateStockInfo($stockCode);
        $basePrice = $stockInfo['last_price'];
        
        // Calculate date interval based on period
        $interval = '1 day';
        if ($period == '5y' || $period == '1y') {
            $interval = '1 week';
        } else if ($period == '6m' || $period == '3m') {
            $interval = '3 days';
        }
        
        // Generate dates
        $dates = [];
        $currentDate = strtotime($startDate);
        $endTimestamp = strtotime($endDate);
        
        while ($currentDate <= $endTimestamp) {
            $dates[] = date('Y-m-d', $currentDate);
            $currentDate = strtotime("+$interval", $currentDate);
        }
        
        // Generate prices with realistic movement
        $prices = [];
        $currentPrice = $basePrice * (1 - (mt_rand(300, 1500) / 10000)); // Start slightly lower
        $volatility = 0.02; // 2% daily volatility
        
        foreach ($dates as $date) {
            // Generate random movement with slight upward bias
            $change = $currentPrice * (mt_rand(-100, 105) / 10000);
            $currentPrice += $change;
            
            // Ensure price doesn't go negative
            $currentPrice = max(0.1, $currentPrice);
            
            // Calculate high/low/open around close price
            $high = $currentPrice * (1 + (mt_rand(10, 100) / 10000));
            $low = $currentPrice * (1 - (mt_rand(10, 100) / 10000));
            $open = $low + (($high - $low) * (mt_rand(0, 100) / 100));
            
            // Generate volume
            $volume = mt_rand(5000, 1000000);
            
            $prices[] = [
                'date' => $date,
                'open' => round($open, 2),
                'high' => round($high, 2),
                'low' => round($low, 2),
                'close' => round($currentPrice, 2),
                'volume' => $volume
            ];
        }
        
        return [
            'success' => true,
            'code' => $stockCode,
            'period' => $period,
            'start_date' => $startDate,
            'end_date' => $endDate,
            'prices' => $prices
        ];
    }
    
    /**
     * Simulate recommended stocks based on risk profile (for development/testing)
     * 
     * @param string $riskLevel Risk level
     * @param int $limit Number of recommendations
     * @return array Simulated recommendations
     */
    private function simulateRecommendations($riskLevel, $limit) {
        // Define stock codes for different risk profiles
        $riskStocks = [
            'conservative' => ['EQTY', 'KCB', 'SCOM', 'EABL', 'COOP', 'JUB', 'SBIC', 'BRIT', 'KPLC'],
            'moderate' => ['SCOM', 'EQTY', 'KCB', 'BAMB', 'EABL', 'NCBA', 'ABSA'],
            'aggressive' => ['SCOM', 'EABL', 'KGEN', 'CARB', 'BAT', 'SCAN', 'NMG']
        ];
        
        // Get stock codes for the specified risk level, or use moderate as default
        $stockCodes = $riskStocks[$riskLevel] ?? $riskStocks['moderate'];
        
        // Shuffle and take limited number
        shuffle($stockCodes);
        $stockCodes = array_slice($stockCodes, 0, min($limit, count($stockCodes)));
        
        $recommendations = [];
        
        foreach ($stockCodes as $stockCode) {
            $stockInfo = $this->simulateStockInfo($stockCode);
            
            // Adjust performance metrics based on risk level
            $changePercent = $stockInfo['change_percent'];
            
            if ($riskLevel == 'conservative') {
                // Lower but more stable returns
                $changePercent = min($changePercent, 5);
                $changePercent = max($changePercent, -2);
            } else if ($riskLevel == 'aggressive') {
                // Higher potential returns but more volatility
                $changePercent = $changePercent * 1.5;
            }
            
            $recommendations[] = [
                'code' => $stockCode,
                'name' => $stockInfo['name'],
                'price' => $stockInfo['last_price'],
                'change_percent' => round($changePercent, 2),
                'sector' => $stockInfo['sector']
            ];
        }
        
        return $recommendations;
    }
}