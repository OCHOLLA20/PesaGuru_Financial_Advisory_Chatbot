<?php
namespace App\Services\Financial;

class LoanService {
    private $loanProducts = [];
    
    public function __construct() {
        // Load loan products data
        $this->loadLoanProducts();
    }
    
    /**
     * Analyze loan options for a user
     * @param int $userId User ID
     * @param float $amount Loan amount
     * @param string $duration Loan duration
     * @return array Analysis results
     */
    public function analyzeLoanOptions($userId, $amount, $duration) {
        // Convert duration to months for calculation
        $months = $this->durationToMonths($duration);
        
        // Filter loan products based on amount and duration
        $eligibleProducts = $this->filterEligibleProducts($amount, $months);
        
        // Calculate monthly payments and total costs
        $analyzedProducts = $this->calculateLoanMetrics($eligibleProducts, $amount, $months);
        
        // Sort by monthly payment (ascending)
        usort($analyzedProducts, function($a, $b) {
            return $a['monthly_payment'] <=> $b['monthly_payment'];
        });
        
        return [
            'loan_amount' => $amount,
            'loan_duration' => $duration,
            'loan_duration_months' => $months,
            'options' => $analyzedProducts,
            'recommendation' => $this->generateRecommendation($analyzedProducts, $amount, $months)
        ];
    }
    
    /**
     * Convert duration string to months
     * @param string $duration Duration string (e.g. "2 years")
     * @return int Duration in months
     */
    private function durationToMonths($duration) {
        $months = 0;
        
        // Extract value and unit from duration string
        if (preg_match('/(\d+)\s*(day|days|week|weeks|month|months|year|years)/', $duration, $matches)) {
            $value = (int) $matches[1];
            $unit = strtolower($matches[2]);
            
            // Convert to months
            switch ($unit) {
                case 'day':
                case 'days':
                    $months = ceil($value / 30);
                    break;
                case 'week':
                case 'weeks':
                    $months = ceil($value / 4);
                    break;
                case 'month':
                case 'months':
                    $months = $value;
                    break;
                case 'year':
                case 'years':
                    $months = $value * 12;
                    break;
            }
        } else {
            // Default to 12 months if format not recognized
            $months = 12;
        }
        
        return max(1, $months); // Ensure at least 1 month
    }
    
    /**
     * Filter eligible loan products based on amount and duration
     * @param float $amount Loan amount
     * @param int $months Loan duration in months
     * @return array Eligible loan products
     */
    private function filterEligibleProducts($amount, $months) {
        $eligible = [];
        
        foreach ($this->loanProducts as $product) {
            if ($amount >= $product['min_amount'] && 
                $amount <= $product['max_amount'] && 
                $months >= $product['min_term_months'] && 
                $months <= $product['max_term_months']) {
                $eligible[] = $product;
            }
        }
        
        return $eligible;
    }
    
    /**
     * Calculate loan metrics for eligible products
     * @param array $products Eligible loan products
     * @param float $amount Loan amount
     * @param int $months Loan duration in months
     * @return array Products with calculated metrics
     */
    private function calculateLoanMetrics($products, $amount, $months) {
        $results = [];
        
        foreach ($products as $product) {
            // Calculate interest rate for the term
            $monthlyRate = $product['interest_rate'] / 12 / 100;
            
            // Calculate monthly payment using loan formula
            $monthlyPayment = $amount * $monthlyRate * pow(1 + $monthlyRate, $months) / 
                             (pow(1 + $monthlyRate, $months) - 1);
            
            // Calculate total payment and interest
            $totalPayment = $monthlyPayment * $months;
            $totalInterest = $totalPayment - $amount;
            
            $results[] = [
                'provider' => $product['provider'],
                'product_name' => $product['product_name'],
                'interest_rate' => $product['interest_rate'],
                'monthly_payment' => round($monthlyPayment, 2),
                'total_payment' => round($totalPayment, 2),
                'total_interest' => round($totalInterest, 2),
                'processing_fee' => $product['processing_fee'],
                'early_repayment_penalty' => $product['early_repayment_penalty'],
                'features' => $product['features'],
                'requirements' => $product['requirements']
            ];
        }
        
        return $results;
    }
    
    /**
     * Generate loan recommendation
     * @param array $analyzedProducts Analyzed loan products
     * @param float $amount Loan amount
     * @param int $months Loan duration in months
     * @return array Recommendation
     */
    private function generateRecommendation($analyzedProducts, $amount, $months) {
        if (empty($analyzedProducts)) {
            return [
                'message' => 'No eligible loan products found for this amount and duration.',
                'suggestion' => 'Try a different loan amount or duration.'
            ];
        }
        
        // Find the loan with the lowest total cost
        $lowestTotal = null;
        $lowestTotalProduct = null;
        
        foreach ($analyzedProducts as $product) {
            $totalCost = $product['total_payment'] + $product['processing_fee'];
            
            if ($lowestTotal === null || $totalCost < $lowestTotal) {
                $lowestTotal = $totalCost;
                $lowestTotalProduct = $product;
            }
        }
        
        // Find the loan with the lowest monthly payment
        $lowestMonthly = null;
        $lowestMonthlyProduct = null;
        
        foreach ($analyzedProducts as $product) {
            if ($lowestMonthly === null || $product['monthly_payment'] < $lowestMonthly) {
                $lowestMonthly = $product['monthly_payment'];
                $lowestMonthlyProduct = $product;
            }
        }
        
        // Generate recommendation
        return [
            'best_overall' => $lowestTotalProduct,
            'lowest_monthly' => $lowestMonthlyProduct,
            'message' => "Based on your loan amount of KES " . number_format($amount) . 
                         " for " . $months . " months, we recommend " . 
                         $lowestTotalProduct['product_name'] . " from " . 
                         $lowestTotalProduct['provider'] . " for the lowest total cost.",
            'affordability_assessment' => [
                'recommended_income' => $lowestMonthlyProduct['monthly_payment'] * 3,
                'debt_burden_ratio' => ($lowestMonthlyProduct['monthly_payment'] / 
                                       ($lowestMonthlyProduct['monthly_payment'] * 3)) * 100
            ]
        ];
    }
    
    /**
     * Load loan products data
     * In a real application, this would come from a database
     */
    private function loadLoanProducts() {
        $this->loanProducts = [
            [
                'provider' => 'KCB',
                'product_name' => 'KCB Personal Loan',
                'interest_rate' => 13.0,
                'min_amount' => 50000,
                'max_amount' => 7000000,
                'min_term_months' => 6,
                'max_term_months' => 84,
                'processing_fee' => 3000,
                'early_repayment_penalty' => true,
                'features' => ['Insurance cover', 'Flexible repayment', 'Quick processing'],
                'requirements' => ['Bank statement', 'KRA PIN', 'ID', 'Proof of income']
            ],
            [
                'provider' => 'Equity Bank',
                'product_name' => 'Equity Personal Loan',
                'interest_rate' => 13.5,
                'min_amount' => 100000,
                'max_amount' => 10000000,
                'min_term_months' => 12,
                'max_term_months' => 72,
                'processing_fee' => 2500,
                'early_repayment_penalty' => false,
                'features' => ['No hidden charges', 'Flexible terms', '24-hour processing'],
                'requirements' => ['6 months bank statements', 'KRA PIN', 'ID']
            ],
            [
                'provider' => 'Co-operative Bank',
                'product_name' => 'Co-op Personal Loan',
                'interest_rate' => 12.5,
                'min_amount' => 50000,
                'max_amount' => 5000000,
                'min_term_months' => 12,
                'max_term_months' => 60,
                'processing_fee' => 3500,
                'early_repayment_penalty' => true,
                'features' => ['Competitive rates', 'Flexible repayment', 'Online application'],
                'requirements' => ['3 months bank statements', 'KRA PIN', 'ID', 'Payslip']
            ],
            [
                'provider' => 'NCBA',
                'product_name' => 'NCBA Personal Loan',
                'interest_rate' => 14.0,
                'min_amount' => 100000,
                'max_amount' => 8000000,
                'min_term_months' => 12,
                'max_term_months' => 60,
                'processing_fee' => 2000,
                'early_repayment_penalty' => false,
                'features' => ['Quick approval', 'No guarantor required', 'Preferential rates for existing customers'],
                'requirements' => ['Bank statements', 'KRA PIN', 'ID', 'Proof of income']
            ],
            [
                'provider' => 'Absa Bank',
                'product_name' => 'Absa Personal Loan',
                'interest_rate' => 12.9,
                'min_amount' => 50000,
                'max_amount' => 6000000,
                'min_term_months' => 12,
                'max_term_months' => 72,
                'processing_fee' => 3000,
                'early_repayment_penalty' => true,
                'features' => ['Loan insurance', 'Flexible terms', 'Fast disbursement'],
                'requirements' => ['3 months bank statements', 'KRA PIN', 'ID', 'Proof of residence']
            ],
            [
                'provider' => 'M-Shwari',
                'product_name' => 'M-Shwari Loan',
                'interest_rate' => 7.5,
                'min_amount' => 500,
                'max_amount' => 50000,
                'min_term_months' => 1,
                'max_term_months' => 1,
                'processing_fee' => 0,
                'early_repayment_penalty' => false,
                'features' => ['Mobile-based', 'Instant disbursement', 'No paperwork'],
                'requirements' => ['M-Pesa account', 'Good M-Shwari history']
            ],
            [
                'provider' => 'KCB M-Pesa',
                'product_name' => 'KCB M-Pesa Loan',
                'interest_rate' => 8.64,
                'min_amount' => 500,
                'max_amount' => 100000,
                'min_term_months' => 1,
                'max_term_months' => 6,
                'processing_fee' => 0,
                'early_repayment_penalty' => false,
                'features' => ['Mobile-based', 'Instant approval', '24/7 access'],
                'requirements' => ['M-Pesa account', 'Good KCB M-Pesa history']
            ],
            [
                'provider' => 'Tala',
                'product_name' => 'Tala Loan',
                'interest_rate' => 15.0,
                'min_amount' => 500,
                'max_amount' => 50000,
                'min_term_months' => 1,
                'max_term_months' => 1,
                'processing_fee' => 0,
                'early_repayment_penalty' => false,
                'features' => ['App-based', 'No collateral', 'Instant decision'],
                'requirements' => ['Smartphone', 'ID', 'M-Pesa account']
            ],
            [
                'provider' => 'Branch',
                'product_name' => 'Branch Loan',
                'interest_rate' => 14.0,
                'min_amount' => 500,
                'max_amount' => 70000,
                'min_term_months' => 1,
                'max_term_months' => 12,
                'processing_fee' => 0,
                'early_repayment_penalty' => false,
                'features' => ['App-based', 'Flexible terms', 'Increasing limits'],
                'requirements' => ['Smartphone', 'ID', 'M-Pesa account']
            ]
        ];
    }
}