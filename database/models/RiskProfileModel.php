<?php
namespace App\Models;

class RiskProfile {
    private $db;
    
    public function __construct() {
        // Initialize database connection
        // In a real implementation, this would connect to your database
        $this->db = null; // Replace with your actual database connection
    }
    
    /**
     * Find risk profile by ID
     * @param int $id Risk profile ID
     * @return array|null Risk profile data or null if not found
     */
    public function findById($id) {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM risk_profiles WHERE id = :id
        
        // Sample implementation with mock data
        $profiles = $this->getSampleProfiles();
        
        foreach ($profiles as $profile) {
            if ($profile['id'] == $id) {
                return $profile;
            }
        }
        
        return null;
    }
    
    /**
     * Find risk profile by type
     * @param string $type Risk profile type
     * @return array|null Risk profile data or null if not found
     */
    public function findByType($type) {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM risk_profiles WHERE type = :type
        
        // Sample implementation with mock data
        $profiles = $this->getSampleProfiles();
        
        foreach ($profiles as $profile) {
            if ($profile['type'] == $type) {
                return $profile;
            }
        }
        
        return null;
    }
    
    /**
     * Get all risk profiles
     * @return array List of all risk profiles
     */
    public function getAllProfiles() {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM risk_profiles
        
        // Sample implementation with mock data
        return $this->getSampleProfiles();
    }
    
    /**
     * Get profile ID by tolerance level
     * @param string $tolerance Tolerance level (conservative, moderate, aggressive)
     * @return int|null Profile ID or null if not found
     */
    public function getProfileIdByTolerance($tolerance) {
        // In a real implementation, this would query the database
        // Example query: SELECT id FROM risk_profiles WHERE type = :tolerance
        
        // Sample implementation with mock data
        $profiles = $this->getSampleProfiles();
        
        foreach ($profiles as $profile) {
            if ($profile['type'] == $tolerance) {
                return $profile['id'];
            }
        }
        
        return null;
    }
    
    /**
     * Get assessment questions
     * @return array Assessment questions
     */
    public function getAssessmentQuestions() {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM risk_assessment_questions
        
        // Sample implementation with mock data
        return [
            [
                'id' => 1,
                'question' => 'How long do you plan to invest?',
                'options' => [
                    'Less than 1 year',
                    '1-3 years',
                    '3-5 years',
                    '5-10 years',
                    'More than 10 years'
                ],
                'weight' => 2
            ],
            [
                'id' => 2,
                'question' => 'How would you react if your investment lost 20% of its value in a month?',
                'options' => [
                    'Sell everything immediately',
                    'Sell a portion',
                    'Do nothing and wait',
                    'Buy more at the lower price'
                ],
                'weight' => 3
            ],
            [
                'id' => 3,
                'question' => 'What is your primary investment goal?',
                'options' => [
                    'Preserve capital',
                    'Generate income',
                    'Balanced growth and income',
                    'Growth',
                    'Aggressive growth'
                ],
                'weight' => 2
            ],
            [
                'id' => 4,
                'question' => 'What percentage of your monthly income can you comfortably save or invest?',
                'options' => [
                    'Less than 5%',
                    '5-10%',
                    '10-20%',
                    '20-30%',
                    'More than 30%'
                ],
                'weight' => 1
            ],
            [
                'id' => 5,
                'question' => 'What is your knowledge level regarding investments?',
                'options' => [
                    'None',
                    'Limited',
                    'Good',
                    'Extensive'
                ],
                'weight' => 1
            ]
        ];
    }
    
    /**
     * Get asset allocation recommendations based on risk profile
     * @param int $profileId Risk profile ID
     * @return array Asset allocation recommendations
     */
    public function getAssetAllocation($profileId) {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM asset_allocations WHERE profile_id = :profileId
        
        // Sample implementation with mock data
        $allocations = [
            1 => [ // Conservative
                'cash' => 15,
                'fixed_income' => 60,
                'local_equity' => 15,
                'international_equity' => 5,
                'alternative_investments' => 5
            ],
            2 => [ // Moderate
                'cash' => 10,
                'fixed_income' => 40,
                'local_equity' => 25,
                'international_equity' => 15,
                'alternative_investments' => 10
            ],
            3 => [ // Aggressive
                'cash' => 5,
                'fixed_income' => 20,
                'local_equity' => 35,
                'international_equity' => 25,
                'alternative_investments' => 15
            ]
        ];
        
        return $allocations[$profileId] ?? [];
    }
    
    /**
     * Get suitable investment products for a risk profile
     * @param int $profileId Risk profile ID
     * @param string|null $category Product category (optional)
     * @return array Investment products
     */
    public function getSuitableProducts($profileId, $category = null) {
        // In a real implementation, this would query the database
        // Example query: SELECT * FROM investment_products 
        //                WHERE risk_level <= (SELECT risk_level FROM risk_profiles WHERE id = :profileId)
        //                AND (category = :category OR :category IS NULL)
        
        // Sample implementation with mock data
        $allProducts = [
            // Conservative products (profile ID 1)
            [
                'id' => 1,
                'name' => 'Money Market Fund',
                'category' => 'fixed_income',
                'risk_level' => 1,
                'min_investment' => 1000,
                'expected_return' => '7-9%',
                'profile_id' => 1,
                'description' => 'Low-risk fund investing in short-term debt instruments'
            ],
            [
                'id' => 2,
                'name' => 'Treasury Bills',
                'category' => 'fixed_income',
                'risk_level' => 1,
                'min_investment' => 100000,
                'expected_return' => '10-11%',
                'profile_id' => 1,
                'description' => 'Government-backed short-term securities'
            ],
            [
                'id' => 3,
                'name' => 'Fixed Deposit',
                'category' => 'fixed_income',
                'risk_level' => 1,
                'min_investment' => 10000,
                'expected_return' => '6-8%',
                'profile_id' => 1,
                'description' => 'Bank deposits with fixed term and interest rate'
            ],
            
            // Moderate products (profile ID 2)
            [
                'id' => 4,
                'name' => 'Balanced Fund',
                'category' => 'mixed',
                'risk_level' => 2,
                'min_investment' => 5000,
                'expected_return' => '9-12%',
                'profile_id' => 2,
                'description' => 'Balanced mix of stocks and bonds'
            ],
            [
                'id' => 5,
                'name' => 'Corporate Bonds',
                'category' => 'fixed_income',
                'risk_level' => 2,
                'min_investment' => 50000,
                'expected_return' => '12-14%',
                'profile_id' => 2,
                'description' => 'Debt securities issued by corporations'
            ],
            [
                'id' => 6,
                'name' => 'Blue Chip Stocks',
                'category' => 'equity',
                'risk_level' => 2,
                'min_investment' => 10000,
                'expected_return' => '10-15%',
                'profile_id' => 2,
                'description' => 'Shares in stable, established companies'
            ],
            
            // Aggressive products (profile ID 3)
            [
                'id' => 7,
                'name' => 'Equity Fund',
                'category' => 'equity',
                'risk_level' => 3,
                'min_investment' => 5000,
                'expected_return' => '15-20%',
                'profile_id' => 3,
                'description' => 'Fund investing primarily in stocks'
            ],
            [
                'id' => 8,
                'name' => 'Growth Stocks',
                'category' => 'equity',
                'risk_level' => 3,
                'min_investment' => 20000,
                'expected_return' => '15-25%',
                'profile_id' => 3,
                'description' => 'Shares in companies with high growth potential'
            ],
            [
                'id' => 9,
                'name' => 'Real Estate Investment Trust',
                'category' => 'alternative',
                'risk_level' => 3,
                'min_investment' => 50000,
                'expected_return' => '12-18%',
                'profile_id' => 3,
                'description' => 'Investment in real estate properties'
            ]
        ];
        
        // Filter products based on profile ID and category
        $suitableProducts = [];
        foreach ($allProducts as $product) {
            if ($product['profile_id'] <= $profileId) {
                if ($category === null || $product['category'] === $category) {
                    $suitableProducts[] = $product;
                }
            }
        }
        
        return $suitableProducts;
    }
    
    /**
     * Sample risk profiles for demo purposes
     * @return array Risk profiles
     */
    private function getSampleProfiles() {
        return [
            [
                'id' => 1,
                'name' => 'Conservative',
                'type' => 'conservative',
                'description' => 'Focus on preserving capital with minimal risk',
                'expected_return' => '6-10%',
                'volatility' => 'Low',
                'time_horizon' => 'Short-term (1-3 years)',
                'risk_level' => 1,
                'features' => json_encode([
                    ['id' => 'basic_advice', 'name' => 'Basic Investment Advice'],
                    ['id' => 'budget_tools', 'name' => 'Budgeting Tools'],
                    ['id' => 'financial_education', 'name' => 'Financial Education Resources']
                ])
            ],
            [
                'id' => 2,
                'name' => 'Moderate',
                'type' => 'moderate',
                'description' => 'Balanced approach between growth and capital preservation',
                'expected_return' => '8-14%',
                'volatility' => 'Medium',
                'time_horizon' => 'Medium-term (3-7 years)',
                'risk_level' => 2,
                'features' => json_encode([
                    ['id' => 'advanced_advice', 'name' => 'Advanced Investment Advice'],
                    ['id' => 'portfolio_analysis', 'name' => 'Portfolio Analysis'],
                    ['id' => 'market_insights', 'name' => 'Market Insights']
                ])
            ],
            [
                'id' => 3,
                'name' => 'Aggressive',
                'type' => 'aggressive',
                'description' => 'Focus on maximizing growth with higher risk tolerance',
                'expected_return' => '12-20%',
                'volatility' => 'High',
                'time_horizon' => 'Long-term (7+ years)',
                'risk_level' => 3,
                'features' => json_encode([
                    ['id' => 'expert_advice', 'name' => 'Expert Investment Advice'],
                    ['id' => 'advanced_analytics', 'name' => 'Advanced Analytics'],
                    ['id' => 'premium_research', 'name' => 'Premium Research']
                ])
            ]
        ];
    }
}
