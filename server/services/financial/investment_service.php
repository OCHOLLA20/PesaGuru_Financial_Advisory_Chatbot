<?php
namespace App\Services\Financial;

use App\Models\RiskProfile;

class InvestmentService {
    private $riskProfileModel;
    
    public function __construct() {
        $this->riskProfileModel = new RiskProfile();
    }
    
    /**
     * Get investment recommendations based on risk profile
     * @param int $profileId Risk profile ID
     * @return array Investment recommendations
     */
    public function getRecommendationsByRiskProfile($profileId) {
        // Get suitable products based on risk profile
        $products = $this->riskProfileModel->getSuitableProducts($profileId);
        
        // Get asset allocation
        $allocation = $this->riskProfileModel->getAssetAllocation($profileId);
        
        // Prepare recommendations
        $recommendations = [
            'products' => $products,
            'allocation' => $allocation,
            'general_advice' => $this->getGeneralAdvice($profileId)
        ];
        
        return $recommendations;
    }
    
    /**
     * Get personalized recommendations for a user
     * @param int $userId User ID
     * @param int $profileId Risk profile ID
     * @param string|null $category Product category (optional)
     * @return array Personalized recommendations
     */
    public function getPersonalizedRecommendations($userId, $profileId, $category = null) {
        // Get suitable products
        $products = $this->riskProfileModel->getSuitableProducts($profileId, $category);
        
        // In a real implementation, would analyze user behavior and preferences
        // to provide more targeted recommendations
        
        // For this implementation, just return top products with a personalized message
        $topProducts = array_slice($products, 0, 3);
        
        return [
            'top_picks' => $topProducts,
            'personalized_message' => 'Based on your risk profile and financial goals, here are our top recommendations for you.',
            'diversification_advice' => $this->getDiversificationAdvice($profileId)
        ];
    }
    
    /**
     * Get portfolio recommendations
     * @param int $userId User ID
     * @param array $riskProfile User's risk profile
     * @param array $portfolio User's current portfolio
     * @return array Portfolio recommendations
     */
    public function getPortfolioRecommendations($userId, $riskProfile, $portfolio) {
        // Calculate current allocation
        $currentAllocation = $this->calculateCurrentAllocation($portfolio);
        
        // Get target allocation
        $targetAllocation = $this->riskProfileModel->getAssetAllocation($riskProfile['id']);
        
        // Calculate allocation differences
        $allocationDiff = $this->calculateAllocationDifference($currentAllocation, $targetAllocation);
        
        // Generate recommendations based on differences
        $recommendations = $this->generateRebalancingRecommendations($allocationDiff, $targetAllocation);
        
        return [
            'current_allocation' => $currentAllocation,
            'target_allocation' => $targetAllocation,
            'allocation_difference' => $allocationDiff,
            'rebalancing_recommendations' => $recommendations
        ];
    }
    
    /**
     * Get diversification recommendations
     * @param array $allocation Current allocation
     * @param array $riskConcentration Risk concentration
     * @param array $sectorAllocation Sector allocation
     * @return array Diversification recommendations
     */
    public function getDiversificationRecommendations($allocation, $riskConcentration, $sectorAllocation) {
        // This would involve complex calculations to determine diversification needs
        // Simplified version for this implementation
        
        $recommendations = [
            'allocation_advice' => 'Your portfolio appears to be properly diversified across asset classes.',
            'sector_advice' => 'Consider reducing exposure to technology sector and increasing allocation to healthcare.',
            'geographic_advice' => 'Increase international exposure to reduce country-specific risk.',
            'suggested_actions' => [
                'Add international equity fund to increase global diversification',
                'Reduce individual stock holdings and increase fund-based investments',
                'Consider adding bonds to balance equity exposure'
            ]
        ];
        
        return $recommendations;
    }
    
    /**
     * Calculate current portfolio allocation
     * @param array $portfolio Portfolio data
     * @return array Current allocation
     */
    private function calculateCurrentAllocation($portfolio) {
        // In a real implementation, would analyze the portfolio to determine 
        // actual allocation across asset classes
        
        // Sample implementation
        return [
            'cash' => 10,
            'fixed_income' => 30,
            'local_equity' => 40,
            'international_equity' => 15,
            'alternative_investments' => 5
        ];
    }
    
    /**
     * Calculate allocation difference
     * @param array $currentAllocation Current allocation
     * @param array $targetAllocation Target allocation
     * @return array Allocation differences
     */
    private function calculateAllocationDifference($currentAllocation, $targetAllocation) {
        $differences = [];
        
        foreach ($targetAllocation as $asset => $targetPercentage) {
            $currentPercentage = $currentAllocation[$asset] ?? 0;
            $differences[$asset] = $targetPercentage - $currentPercentage;
        }
        
        return $differences;
    }
    
    /**
     * Generate rebalancing recommendations
     * @param array $allocationDiff Allocation differences
     * @param array $targetAllocation Target allocation
     * @return array Rebalancing recommendations
     */
    private function generateRebalancingRecommendations($allocationDiff, $targetAllocation) {
        $recommendations = [];
        
        foreach ($allocationDiff as $asset => $difference) {
            if ($difference > 5) {
                $recommendations[] = "Increase {$asset} allocation by approximately {$difference}% to reach target of {$targetAllocation[$asset]}%";
            } else if ($difference < -5) {
                $recommendations[] = "Decrease {$asset} allocation by approximately " . abs($difference) . "% to reach target of {$targetAllocation[$asset]}%";
            }
        }
        
        if (empty($recommendations)) {
            $recommendations[] = "Your portfolio is well-balanced and aligned with your risk profile. No significant changes needed at this time.";
        }
        
        return $recommendations;
    }
    
    /**
     * Get general investment advice based on risk profile
     * @param int $profileId Risk profile ID
     * @return string General advice
     */
    private function getGeneralAdvice($profileId) {
        $advice = [
            1 => "Focus on capital preservation with stable investments like money market funds, treasury bills, and fixed deposits. Maintain an emergency fund covering 3-6 months of expenses.",
            2 => "Balance growth and income with a mix of bonds, dividend stocks, and some growth investments. Consider regular investing through a systematic investment plan.",
            3 => "Maximize long-term growth through a diversified portfolio of equities and alternative investments. Take advantage of market dips to add quality stocks at lower prices."
        ];
        
        return $advice[$profileId] ?? "Maintain a diversified portfolio aligned with your financial goals and risk tolerance.";
    }
    
    /**
     * Get diversification advice based on risk profile
     * @param int $profileId Risk profile ID
     * @return string Diversification advice
     */
    private function getDiversificationAdvice($profileId) {
        $advice = [
            1 => "Maintain a conservative mix with emphasis on high-quality fixed income investments across different issuers to minimize risk.",
            2 => "Balance your portfolio with 40-60% in fixed income and the remainder in equities and alternatives, spread across sectors and geographies.",
            3 => "Diversify your growth-oriented portfolio across different sectors, market caps, and geographies to manage volatility while pursuing higher returns."
        ];
        
        return $advice[$profileId] ?? "Diversify across asset classes, sectors, and geographies to reduce risk while achieving your financial goals.";
    }
    
    /**
     * Get recommendations for a specific investment amount
     * @param int $userId User ID
     * @param float $amount Investment amount
     * @param int $duration Investment duration in months
     * @return array Investment recommendations
     */
    public function getRecommendations($userId, $amount, $duration) {
        // In a real implementation, this would consider user's risk profile,
        // financial goals, and current market conditions
        
        // Sample implementation
        $shortTerm = $duration <= 12;
        $mediumTerm = $duration > 12 && $duration <= 36;
        $longTerm = $duration > 36;
        
        $recommendations = [];
        
        if ($shortTerm) {
            $recommendations[] = [
                'product_name' => 'Money Market Fund',
                'expected_return' => '7-9% p.a.',
                'risk_level' => 'Low',
                'suitability' => 'High',
                'reason' => 'Provides liquidity and stable returns for short-term investments'
            ];
            $recommendations[] = [
                'product_name' => 'Fixed Deposit',
                'expected_return' => '6-8% p.a.',
                'risk_level' => 'Low',
                'suitability' => 'High',
                'reason' => 'Guaranteed returns for your short investment horizon'
            ];
        } else if ($mediumTerm) {
            $recommendations[] = [
                'product_name' => 'Balanced Fund',
                'expected_return' => '9-12% p.a.',
                'risk_level' => 'Medium',
                'suitability' => 'High',
                'reason' => 'Good balance of growth and stability for medium-term goals'
            ];
            $recommendations[] = [
                'product_name' => 'Corporate Bonds',
                'expected_return' => '12-14% p.a.',
                'risk_level' => 'Medium',
                'suitability' => 'Medium-High',
                'reason' => 'Higher yields than government securities with moderate risk'
            ];
        } else if ($longTerm) {
            $recommendations[] = [
                'product_name' => 'Equity Fund',
                'expected_return' => '15-20% p.a.',
                'risk_level' => 'High',
                'suitability' => 'High',
                'reason' => 'Strong growth potential for long-term investment horizon'
            ];
            $recommendations[] = [
                'product_name' => 'REIT',
                'expected_return' => '12-18% p.a.',
                'risk_level' => 'Medium-High',
                'suitability' => 'Medium-High',
                'reason' => 'Exposure to real estate market with regular income and growth potential'
            ];
        }
        
        return [
            'amount' => $amount,
            'duration' => $duration,
            'recommendations' => $recommendations
        ];
    }
}