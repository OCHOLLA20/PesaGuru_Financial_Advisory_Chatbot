<?php
namespace App\Services\AI;

class IntentClassifier {
    private $intents = [];
    
    public function __construct() {
        // Load intent patterns from configuration
        $this->loadIntentPatterns();
    }
    
    /**
     * Classify user message to an intent
     * @param string $message User message
     * @return string Classified intent
     */
    public function classify($message) {
        $message = strtolower(trim($message));
        
        // Check for exact matches and patterns
        foreach ($this->intents as $intent => $patterns) {
            foreach ($patterns as $pattern) {
                if (preg_match($pattern, $message)) {
                    return $intent;
                }
            }
        }
        
        // Check for keyword matches if no pattern matches
        $keywords = [
            'greeting' => ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
            'get_stock_price' => ['stock', 'price', 'shares', 'ticker', 'trading at', 'how much is', 'stock price'],
            'investment_recommendation' => ['invest', 'investment', 'portfolio', 'recommend', 'suggestion', 'advice', 'where should i put', 'where to invest'],
            'loan_inquiry' => ['loan', 'borrow', 'credit', 'financing', 'interest rate', 'repayment', 'mortgage'],
            'financial_goal' => ['goal', 'target', 'saving for', 'save for', 'planning for', 'want to buy', 'retirement'],
            'market_trends' => ['market', 'trend', 'performance', 'index', 'nse', 'stock market', 'bull', 'bear']
        ];
        
        $maxScore = 0;
        $matchedIntent = 'fallback';
        
        foreach ($keywords as $intent => $intentKeywords) {
            $score = 0;
            foreach ($intentKeywords as $keyword) {
                if (strpos($message, $keyword) !== false) {
                    $score++;
                }
            }
            
            if ($score > $maxScore) {
                $maxScore = $score;
                $matchedIntent = $intent;
            }
        }
        
        return $matchedIntent;
    }
    
    /**
     * Load intent patterns from configuration
     */
    private function loadIntentPatterns() {
        // These would typically be loaded from a database or file
        // Using regex patterns for more precise matching
        $this->intents = [
            'greeting' => [
                '/^(hello|hi|hey|howdy|good (morning|afternoon|evening)|hujambo|habari)/i'
            ],
            'get_stock_price' => [
                '/(?:what(?:\'s| is) the (?:price|value) of|how (?:much|many) is|stock price for) ([A-Za-z0-9\.\-]+)(?:\s+stock)?/i',
                '/([A-Za-z0-9\.\-]+) (?:stock|share)(?:s)? price/i'
            ],
            'investment_recommendation' => [
                '/(?:how|where) (?:should|can|do) I invest/i',
                '/(?:recommend|suggest)(?:ation for)? (?:an |some )?investment/i',
                '/invest(?:ing|ment)? (?:advice|options|opportunities)/i'
            ],
            'loan_inquiry' => [
                '/(?:get|apply for|qualify for|interest rate on) (?:a |the )?loan/i',
                '/(?:borrow|loan) (?:money|cash|funds)/i',
                '/compare (?:loan|interest) rates/i'
            ],
            'financial_goal' => [
                '/(?:set|create|establish|plan) (?:a |my )?(?:financial |money |savings )?goal/i',
                '/(?:save|saving) for/i',
                '/(?:plan|planning) for (?:retirement|college|education|house|car|wedding)/i'
            ],
            'market_trends' => [
                '/(?:current|latest|recent) (?:market|stock) (?:trends|performance|movement)/i',
                '/how (?:is|are) the (?:market|stocks) (?:doing|performing)/i',
                '/(?:nse|nairobi stock exchange) (?:index|performance)/i'
            ]
        ];
    }
}