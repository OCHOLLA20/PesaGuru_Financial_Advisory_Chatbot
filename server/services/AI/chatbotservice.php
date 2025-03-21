<?php
namespace App\Services\AI;

use App\Services\AI\IntentClassifier;
use App\Services\AI\EntityExtractor;
use App\Services\AI\TranslationService;

class ChatbotService {
    private $intentClassifier;
    private $entityExtractor;
    private $translationService;
    
    public function __construct() {
        $this->intentClassifier = new IntentClassifier();
        $this->entityExtractor = new EntityExtractor();
        $this->translationService = new TranslationService();
    }
    
    /**
     * Process user message and generate chatbot response
     * @param string $message User message
     * @param array $userContext User context data
     * @param array $conversationHistory Previous conversation
     * @param string $language Language code (en/sw)
     * @return array Response data
     */
    public function processMessage($message, $userContext, $conversationHistory, $language = 'en') {
        // Translate message if needed
        $processedMessage = $message;
        if ($language !== 'en') {
            $processedMessage = $this->translationService->translateToEnglish($message, $language);
        }
        
        // Classify intent
        $intent = $this->intentClassifier->classify($processedMessage);
        
        // Extract entities
        $entities = $this->entityExtractor->extract($processedMessage, $intent);
        
        // Generate response based on intent and entities
        $response = $this->generateResponse($intent, $entities, $userContext, $conversationHistory);
        
        // Translate response if needed
        if ($language !== 'en' && isset($response['message'])) {
            $response['message'] = $this->translationService->translateFromEnglish(
                $response['message'],
                $language
            );
            
            // Translate suggestions if present
            if (isset($response['suggestions']) && is_array($response['suggestions'])) {
                foreach ($response['suggestions'] as $key => $suggestion) {
                    $response['suggestions'][$key] = $this->translationService->translateFromEnglish(
                        $suggestion,
                        $language
                    );
                }
            }
        }
        
        return array_merge($response, [
            'intent' => $intent,
            'entities' => $entities,
            'context' => $this->updateContext($userContext, $intent, $entities)
        ]);
    }
    
    /**
     * Generate response based on intent and entities
     * @param string $intent Classified intent
     * @param array $entities Extracted entities
     * @param array $userContext User context
     * @param array $conversationHistory Conversation history
     * @return array Response data
     */
    private function generateResponse($intent, $entities, $userContext, $conversationHistory) {
        $response = [
            'message' => 'I don\'t understand that request. Can you please rephrase?',
            'action' => null
        ];
        
        switch ($intent) {
            case 'greeting':
                $response['message'] = $this->generateGreeting($userContext);
                $response['suggestions'] = [
                    'Tell me about investment options',
                    'What is my risk profile?',
                    'Help me set a financial goal'
                ];
                break;
                
            case 'get_stock_price':
                if (isset($entities['stock_symbol'])) {
                    $response['message'] = "Let me check the current price for {$entities['stock_symbol']}.";
                    $response['action'] = 'get_stock_price';
                } else {
                    $response['message'] = "Which stock would you like to check?";
                }
                break;
                
            case 'investment_recommendation':
                if (isset($entities['amount']) && isset($entities['duration'])) {
                    $response['message'] = "Based on your risk profile and a {$entities['amount']} KES investment for {$entities['duration']}, here are my recommendations:";
                    $response['action'] = 'recommend_investment';
                } else if (isset($entities['amount'])) {
                    $response['message'] = "For how long do you plan to invest {$entities['amount']} KES?";
                } else {
                    $response['message'] = "I can help you with investment recommendations. How much would you like to invest?";
                }
                break;
                
            case 'loan_inquiry':
                if (isset($entities['amount']) && isset($entities['duration'])) {
                    $response['message'] = "Let me analyze loan options for {$entities['amount']} KES over {$entities['duration']}.";
                    $response['action'] = 'loan_analysis';
                } else {
                    $response['message'] = "I can help you find the best loan options. How much do you need and for how long?";
                }
                break;
                
            case 'financial_goal':
                $response['message'] = "Let's set up a financial goal. What are you saving for?";
                break;
                
            case 'market_trends':
                $response['message'] = "Here are the current market trends in the Nairobi Securities Exchange:";
                // Add chart data
                $response['charts'] = [
                    [
                        'type' => 'line',
                        'title' => 'NSE 20 Index - Last 7 Days',
                        'data' => $this->getMarketTrendData()
                    ]
                ];
                break;
                
            // Add other intents as needed
        }
        
        return $response;
    }
    
    /**
     * Generate a personalized greeting
     * @param array $userContext User context
     * @return string Greeting message
     */
    private function generateGreeting($userContext) {
        $hour = (int) date('H');
        $timeOfDay = '';
        
        if ($hour < 12) {
            $timeOfDay = 'morning';
        } else if ($hour < 17) {
            $timeOfDay = 'afternoon';
        } else {
            $timeOfDay = 'evening';
        }
        
        $name = isset($userContext['user']['first_name']) ? $userContext['user']['first_name'] : 'there';
        
        return "Good {$timeOfDay}, {$name}! How can I help you with your finances today?";
    }
    
    /**
     * Update context based on current interaction
     * @param array $currentContext Current context
     * @param string $intent Current intent
     * @param array $entities Current entities
     * @return array Updated context
     */
    private function updateContext($currentContext, $intent, $entities) {
        $context = $currentContext;
        
        // Update context based on intent
        $context['last_intent'] = $intent;
        
        // Store entities in context if relevant
        if (!empty($entities)) {
            foreach ($entities as $key => $value) {
                $context[$key] = $value;
            }
        }
        
        return $context;
    }
    
    /**
     * Get sample market trend data
     * This would normally come from a market data API
     * @return array Market data
     */
    private function getMarketTrendData() {
        // Sample data - would be replaced with real API data
        return [
            'labels' => ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Mon', 'Tue'],
            'datasets' => [
                [
                    'label' => 'NSE 20 Index',
                    'data' => [1820, 1835, 1822, 1840, 1850, 1845, 1860]
                ]
            ]
        ];
    }
    
    /**
     * Get financial assessment questions
     * @param array $user User data
     * @return array Assessment questions
     */
    public function getFinancialAssessmentQuestions($user) {
        // Tailor questions based on user profile
        $experienceLevel = $user['investment_experience'] ?? 'beginner';
        
        $questions = [
            [
                'id' => 'risk_tolerance',
                'question' => 'How would you react if your investment lost 20% of its value in one month?',
                'options' => [
                    ['value' => 'sell_all', 'label' => 'Sell all my investments immediately'],
                    ['value' => 'sell_some', 'label' => 'Sell some of my investments'],
                    ['value' => 'do_nothing', 'label' => 'Do nothing and wait for recovery'],
                    ['value' => 'buy_more', 'label' => 'Buy more at the lower price']
                ]
            ],
            [
                'id' => 'investment_horizon',
                'question' => 'How long do you plan to keep your money invested before you need it?',
                'options' => [
                    ['value' => 'less_than_1_year', 'label' => 'Less than 1 year'],
                    ['value' => '1_to_3_years', 'label' => '1-3 years'],
                    ['value' => '3_to_5_years', 'label' => '3-5 years'],
                    ['value' => 'more_than_5_years', 'label' => 'More than 5 years']
                ]
            ],
            [
                'id' => 'income_stability',
                'question' => 'How stable is your current income?',
                'options' => [
                    ['value' => 'very_unstable', 'label' => 'Very unstable'],
                    ['value' => 'somewhat_unstable', 'label' => 'Somewhat unstable'],
                    ['value' => 'stable', 'label' => 'Stable'],
                    ['value' => 'very_stable', 'label' => 'Very stable']
                ]
            ]
        ];
        
        // Add advanced questions for experienced investors
        if ($experienceLevel === 'advanced' || $experienceLevel === 'expert') {
            $questions[] = [
                'id' => 'portfolio_allocation',
                'question' => 'What is your preferred portfolio allocation?',
                'options' => [
                    ['value' => 'conservative', 'label' => 'Mostly bonds and money market (low risk)'],
                    ['value' => 'balanced', 'label' => 'Mix of stocks and bonds (moderate risk)'],
                    ['value' => 'growth', 'label' => 'Mostly stocks (higher risk)'],
                    ['value' => 'aggressive', 'label' => 'Stocks, real estate, and alternative investments (highest risk)']
                ]
            ];
        }
        
        return $questions;
    }
    
    /**
     * Analyze financial assessment answers
     * @param int $userId User ID
     * @param array $answers Assessment answers
     * @return array Analysis results
     */
    public function analyzeFinancialAssessment($userId, $answers) {
        // Calculate risk score based on answers
        $riskScore = 0;
        
        // Risk tolerance
        if (isset($answers['risk_tolerance'])) {
            switch ($answers['risk_tolerance']) {
                case 'sell_all': $riskScore += 0; break;
                case 'sell_some': $riskScore += 1; break;
                case 'do_nothing': $riskScore += 2; break;
                case 'buy_more': $riskScore += 3; break;
            }
        }
        
        // Investment horizon
        if (isset($answers['investment_horizon'])) {
            switch ($answers['investment_horizon']) {
                case 'less_than_1_year': $riskScore += 0; break;
                case '1_to_3_years': $riskScore += 1; break;
                case '3_to_5_years': $riskScore += 2; break;
                case 'more_than_5_years': $riskScore += 3; break;
            }
        }
        
        // Income stability
        if (isset($answers['income_stability'])) {
            switch ($answers['income_stability']) {
                case 'very_unstable': $riskScore += 0; break;
                case 'somewhat_unstable': $riskScore += 1; break;
                case 'stable': $riskScore += 2; break;
                case 'very_stable': $riskScore += 3; break;
            }
        }
        
        // Portfolio allocation (if answered)
        if (isset($answers['portfolio_allocation'])) {
            switch ($answers['portfolio_allocation']) {
                case 'conservative': $riskScore += 0; break;
                case 'balanced': $riskScore += 1; break;
                case 'growth': $riskScore += 2; break;
                case 'aggressive': $riskScore += 3; break;
            }
        }
        
        // Determine risk profile based on score
        $maxPossibleScore = isset($answers['portfolio_allocation']) ? 12 : 9;
        $riskPercentage = ($riskScore / $maxPossibleScore) * 100;
        
        $riskProfileId = 1; // Default: Conservative
        $riskProfileName = 'Conservative';
        
        if ($riskPercentage >= 75) {
            $riskProfileId = 4;
            $riskProfileName = 'Aggressive';
        } else if ($riskPercentage >= 50) {
            $riskProfileId = 3;
            $riskProfileName = 'Growth';
        } else if ($riskPercentage >= 25) {
            $riskProfileId = 2;
            $riskProfileName = 'Balanced';
        }
        
        return [
            'risk_score' => $riskScore,
            'risk_percentage' => $riskPercentage,
            'risk_profile_id' => $riskProfileId,
            'risk_profile_name' => $riskProfileName,
            'assessment_date' => date('Y-m-d H:i:s'),
            'recommendations' => $this->getRecommendationsForRiskProfile($riskProfileId)
        ];
    }
    
    /**
     * Get investment recommendations based on risk profile
     * @param int $riskProfileId Risk profile ID
     * @return array Recommendations
     */
    private function getRecommendationsForRiskProfile($riskProfileId) {
        $recommendations = [];
        
        switch ($riskProfileId) {
            case 1: // Conservative
                $recommendations = [
                    'asset_allocation' => [
                        'money_market' => 40,
                        'bonds' => 40,
                        'stocks' => 15,
                        'alternatives' => 5
                    ],
                    'suggestions' => [
                        'Consider Treasury Bills and Money Market Funds for stability',
                        'Focus on dividend-paying stocks rather than growth stocks',
                        'Set up an emergency fund covering 6-9 months of expenses',
                        'Prioritize paying off high-interest debt'
                    ]
                ];
                break;
                
            case 2: // Balanced
                $recommendations = [
                    'asset_allocation' => [
                        'money_market' => 20,
                        'bonds' => 30,
                        'stocks' => 40,
                        'alternatives' => 10
                    ],
                    'suggestions' => [
                        'Maintain a balanced portfolio between stocks and bonds',
                        'Consider index funds for stock market exposure',
                        'Explore government and corporate bonds for income',
                        'Set aside emergency funds covering 3-6 months of expenses'
                    ]
                ];
                break;
                
            case 3: // Growth
                $recommendations = [
                    'asset_allocation' => [
                        'money_market' => 10,
                        'bonds' => 20,
                        'stocks' => 60,
                        'alternatives' => 10
                    ],
                    'suggestions' => [
                        'Focus on growth stocks and equity funds',
                        'Consider international market exposure',
                        'Maintain some bonds for diversification',
                        'Explore REIT investments for real estate exposure'
                    ]
                ];
                break;
                
            case 4: // Aggressive
                $recommendations = [
                    'asset_allocation' => [
                        'money_market' => 5,
                        'bonds' => 10,
                        'stocks' => 70,
                        'alternatives' => 15
                    ],
                    'suggestions' => [
                        'Focus on high-growth sectors and emerging markets',
                        'Consider individual stocks and specialized ETFs',
                        'Explore alternative investments like real estate and commodities',
                        'Keep a small cash reserve for opportunity investments'
                    ]
                ];
                break;
        }
        
        return $recommendations;
    }
}