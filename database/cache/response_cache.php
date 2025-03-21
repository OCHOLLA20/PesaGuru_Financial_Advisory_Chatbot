<?php

require_once __DIR__ . '/../../vendor/autoload.php';

use PesaGuru\Database\Cache\ResponseCache;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;

// Initialize logger
$logger = new Logger('cache');
$logger->pushHandler(new StreamHandler(__DIR__ . '/../../logs/cache.log', Logger::INFO));

// Create cache instance with default Redis configuration
$cache = new ResponseCache($logger);

// Example 1: Caching and retrieving chatbot responses
function example_chatbot_response_caching($cache) {
    // User query example
    $userQuery = "What are the best investment options for beginners in Kenya?";
    
    // Check if response is already cached
    $cachedResponse = $cache->getChatbotResponse($userQuery);
    
    if ($cachedResponse !== null) {
        echo "Using cached chatbot response\n";
        return $cachedResponse;
    }
    
    // If not cached, generate response from AI model
    $chatbotResponse = [
        'message' => 'For beginners in Kenya, consider these investment options: M-Akiba government bonds, Money Market Funds with companies like CIC and Britam, and unit trusts. These have lower risk and are good starting points.',
        'recommendations' => [
            'M-Akiba Bonds',
            'Money Market Funds',
            'Unit Trusts'
        ],
        'generated_at' => date('Y-m-d H:i:s')
    ];
    
    // Cache the response (default TTL of 24 hours will apply)
    $cache->storeChatbotResponse($userQuery, $chatbotResponse);
    
    return $chatbotResponse;
}

// Example 2: Caching market data
function example_market_data_caching($cache) {
    // Stock symbol
    $symbol = 'SCOM'; // Safaricom
    
    // Check if market data is already cached
    $cachedData = $cache->getMarketData('stocks', $symbol);
    
    if ($cachedData !== null) {
        echo "Using cached market data for {$symbol}\n";
        return $cachedData;
    }
    
    // If not cached, fetch from API
    // Note: This would normally be an actual API call
    $marketData = [
        'symbol' => 'SCOM',
        'name' => 'Safaricom PLC',
        'price' => 29.75,
        'change' => 0.25,
        'change_percent' => 0.85,
        'volume' => 3245678,
        'market_cap' => 1190000000000,
        'updated_at' => time()
    ];
    
    // Cache the market data with a short TTL (5 minutes)
    $cache->storeMarketData('stocks', $symbol, $marketData);
    
    return $marketData;
}

// Example 3: Caching investment recommendations
function example_investment_recommendations($cache, $userId) {
    // Check if recommendations are already cached
    $cachedRecommendations = $cache->getRecommendation($userId, 'investment');
    
    if ($cachedRecommendations !== null) {
        echo "Using cached investment recommendations for user {$userId}\n";
        return $cachedRecommendations;
    }
    
    // If not cached, generate recommendations
    // Note: This would normally involve complex AI-based calculations
    $recommendations = [
        'risk_profile' => 'Moderate',
        'recommended_allocation' => [
            'stocks' => 40,
            'bonds' => 30,
            'money_market' => 20,
            'real_estate' => 10
        ],
        'specific_recommendations' => [
            ['ticker' => 'EABL', 'allocation' => 10, 'reason' => 'Stable dividend performer'],
            ['ticker' => 'SCOM', 'allocation' => 15, 'reason' => 'Growth potential in fintech'],
            ['ticker' => 'KCB', 'allocation' => 15, 'reason' => 'Banking sector growth']
        ],
        'generated_at' => time()
    ];
    
    // Cache the recommendations (default TTL of 1 hour will apply)
    $cache->storeRecommendation($userId, 'investment', $recommendations);
    
    return $recommendations;
}

// Example 4: Caching user portfolio data
function example_portfolio_caching($cache, $userId) {
    // Check if portfolio data is already cached
    $cachedPortfolio = $cache->getPortfolioData($userId);
    
    if ($cachedPortfolio !== null) {
        echo "Using cached portfolio data for user {$userId}\n";
        return $cachedPortfolio;
    }
    
    // If not cached, fetch from database
    // Note: This would normally be a database query
    $portfolioData = [
        'total_value' => 250000,
        'assets' => [
            ['type' => 'stock', 'symbol' => 'SCOM', 'quantity' => 1000, 'value' => 29750],
            ['type' => 'stock', 'symbol' => 'EABL', 'quantity' => 500, 'value' => 75000],
            ['type' => 'bond', 'name' => 'M-Akiba', 'value' => 50000],
            ['type' => 'fund', 'name' => 'CIC Money Market Fund', 'value' => 100000]
        ],
        'performance' => [
            'daily' => 0.5,
            'weekly' => 1.2,
            'monthly' => 3.5,
            'yearly' => 12.4
        ],
        'last_updated' => time()
    ];
    
    // Cache the portfolio data (default TTL of 30 minutes will apply)
    $cache->storePortfolioData($userId, $portfolioData);
    
    return $portfolioData;
}

// Example 5: Clearing cache for a specific user
function example_clear_user_cache($cache, $userId) {
    // This could be called after a user updates their profile, financial goals, or portfolio
    if ($cache->clearUserCache($userId)) {
        echo "Successfully cleared cache for user {$userId}\n";
        return true;
    } else {
        echo "Failed to clear cache for user {$userId}\n";
        return false;
    }
}

// Example 6: Clearing specific cache types
function example_clear_cache_by_type($cache) {
    // Clear market data cache (useful when market closes or during significant market events)
    if ($cache->clearCacheByType('market')) {
        echo "Successfully cleared market data cache\n";
        return true;
    } else {
        echo "Failed to clear market data cache\n";
        return false;
    }
}

// Example 7: Getting cache statistics
function example_cache_stats($cache) {
    $stats = $cache->getCacheStats();
    
    echo "Cache Statistics:\n";
    echo "Total Keys: {$stats['total_keys']}\n";
    echo "Memory Used: {$stats['memory_used']}\n";
    echo "Cache Hits: {$stats['hits']}\n";
    echo "Cache Misses: {$stats['misses']}\n";
    
    echo "Keys by Type:\n";
    foreach ($stats['types'] as $type => $count) {
        echo "  - {$type}: {$count}\n";
    }
    
    return $stats;
}

// Usage examples
try {
    if (!$cache->isConnected()) {
        echo "Redis connection failed. Please check Redis server and configuration.\n";
        exit(1);
    }
    
    // Example user ID
    $userId = 12345;
    
    // Run examples
    $chatbotResponse = example_chatbot_response_caching($cache);
    $marketData = example_market_data_caching($cache);
    $recommendations = example_investment_recommendations($cache, $userId);
    $portfolio = example_portfolio_caching($cache, $userId);
    
    // Get cache statistics
    $stats = example_cache_stats($cache);
    
    // Cleanup
    $cache->disconnect();
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
