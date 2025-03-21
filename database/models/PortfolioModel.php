<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use App\Models\User;
use App\Models\RiskProfileModel;
use App\Models\TransactionModel;
use Carbon\Carbon; // Add Carbon import for datetime handling

class PortfolioModel extends Model
{
    use HasFactory;

    /**
     * The table associated with the model.
     *
     * @var string
     */
    protected $table = 'portfolios';

    /**
     * The attributes that are mass assignable.
     *
     * @var array
     */
    protected $fillable = [
        'user_id',
        'risk_profile_id',
        'name',
        'description',
        'total_value',
        'initial_investment',
        'current_return',
        'return_percentage',
        'last_rebalanced',
        'currency',
        'status',
        'created_at',
        'updated_at',
        'diversification_score',
        'performance_score',
        'investment_composition',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array
     */
    protected $casts = [
        'total_value' => 'float',
        'initial_investment' => 'float',
        'current_return' => 'float',
        'return_percentage' => 'float',
        'diversification_score' => 'float',
        'performance_score' => 'float',
        'last_rebalanced' => 'datetime',
        'investment_composition' => 'json',
        'created_at' => 'datetime',
        'updated_at' => 'datetime',
    ];

    /**
     * The default attributes values.
     *
     * @var array
     */
    protected $attributes = [
        'currency' => 'KES',
        'status' => 'active',
        'diversification_score' => 0,
        'performance_score' => 0,
    ];

    /**
     * Get the user that owns the portfolio.
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the risk profile associated with this portfolio.
     */
    public function riskProfile()
    {
        return $this->belongsTo(RiskProfileModel::class, 'risk_profile_id');
    }

    /**
     * Get the transactions associated with this portfolio.
     */
    public function transactions()
    {
        return $this->hasMany(Transaction::class, 'portfolio_id');
    }

    /**
     * Calculate the current value of the portfolio based on investment composition.
     *
     * @return float Updated portfolio value
     */
    public function calculateCurrentValue()
    {
        $total = 0;
        $composition = $this->investment_composition;

        if (empty($composition)) {
            return $total;
        }

        foreach ($composition as $investment) {
            $total += $investment['current_value'] ?? 0;
        }

        $this->total_value = $total;
        $this->calculateReturn();
        
        return $total;
    }

    /**
     * Calculate return on investment.
     *
     * @return array Return metrics
     */
    public function calculateReturn()
    {
        if ($this->initial_investment <= 0) {
            $this->current_return = 0;
            $this->return_percentage = 0;
            return [
                'current_return' => 0,
                'return_percentage' => 0
            ];
        }

        $this->current_return = $this->total_value - $this->initial_investment;
        $this->return_percentage = ($this->current_return / $this->initial_investment) * 100;

        return [
            'current_return' => $this->current_return,
            'return_percentage' => $this->return_percentage
        ];
    }

    /**
     * Add a new investment to the portfolio.
     *
     * @param array $investment Investment details
     * @return bool Success status
     */
    public function addInvestment(array $investment)
    {
        $requiredKeys = ['type', 'name', 'amount', 'purchase_price', 'current_value', 'purchase_date'];
        
        // Validate investment data
        foreach ($requiredKeys as $key) {
            if (!isset($investment[$key])) {
                return false;
            }
        }

        $composition = $this->investment_composition ?? [];
        
        // Add unique investment ID
        $investment['id'] = uniqid('inv_');
        $composition[] = $investment;
        
        $this->investment_composition = $composition;
        $this->initial_investment += $investment['amount'];
        
        // Update portfolio metrics
        $this->calculateCurrentValue();
        $this->calculateDiversificationScore();
        
        return true;
    }

    /**
     * Update an existing investment in the portfolio.
     *
     * @param string $investmentId ID of the investment to update
     * @param array $data Updated investment data
     * @return bool Success status
     */
    public function updateInvestment(string $investmentId, array $data)
    {
        $composition = $this->investment_composition ?? [];
        $updated = false;
        
        foreach ($composition as $key => $investment) {
            if ($investment['id'] === $investmentId) {
                // Update investment data
                foreach ($data as $field => $value) {
                    $composition[$key][$field] = $value;
                }
                $updated = true;
                break;
            }
        }
        
        if ($updated) {
            $this->investment_composition = $composition;
            $this->calculateCurrentValue();
            $this->calculateDiversificationScore();
            return true;
        }
        
        return false;
    }

    /**
     * Remove an investment from the portfolio.
     *
     * @param string $investmentId ID of the investment to remove
     * @return bool Success status
     */
    public function removeInvestment(string $investmentId)
    {
        $composition = $this->investment_composition ?? [];
        $initialAmount = 0;
        $removed = false;
        
        foreach ($composition as $key => $investment) {
            if ($investment['id'] === $investmentId) {
                $initialAmount = $investment['amount'];
                unset($composition[$key]);
                $removed = true;
                break;
            }
        }
        
        if ($removed) {
            $this->investment_composition = array_values($composition); // Reindex array
            $this->initial_investment -= $initialAmount;
            $this->calculateCurrentValue();
            $this->calculateDiversificationScore();
            return true;
        }
        
        return false;
    }

    /**
     * Calculate the portfolio's diversification score.
     *
     * @return float Diversification score (0-100)
     */
    public function calculateDiversificationScore()
    {
        $composition = $this->investment_composition ?? [];
        
        if (empty($composition) || $this->total_value <= 0) {
            $this->diversification_score = 0;
            return 0;
        }
        
        // Group investments by type
        $typeGroups = [];
        foreach ($composition as $investment) {
            $type = $investment['type'] ?? 'unknown';
            if (!isset($typeGroups[$type])) {
                $typeGroups[$type] = 0;
            }
            $typeGroups[$type] += $investment['current_value'] ?? 0;
        }
        
        // Calculate percentage of each type
        $percentages = [];
        foreach ($typeGroups as $type => $value) {
            $percentages[$type] = ($value / $this->total_value) * 100;
        }
        
        // Ideal diversification based on number of types (equal distribution)
        $idealPercentage = 100 / count($typeGroups);
        
        // Calculate deviation from ideal
        $totalDeviation = 0;
        foreach ($percentages as $percentage) {
            $totalDeviation += abs($percentage - $idealPercentage);
        }
        
        // Convert to a score (0-100)
        // Higher deviation = lower score
        $maxPossibleDeviation = 200 - (200 / count($typeGroups));
        $score = 100 - (($totalDeviation / $maxPossibleDeviation) * 100);
        
        // Bonus points for having more than 3 different investment types
        if (count($typeGroups) >= 3) {
            $score += min((count($typeGroups) - 2) * 5, 15);
        }
        
        // Cap score at 100
        $score = min($score, 100);
        
        $this->diversification_score = $score;
        return $score;
    }

    /**
     * Suggest portfolio rebalancing based on risk profile.
     *
     * @return array Rebalancing suggestions
     */
    public function suggestRebalancing()
    {
        if (!$this->riskProfile) {
            return [
                'error' => 'No risk profile associated with this portfolio'
            ];
        }
        
        $recommendations = $this->riskProfile->getInvestmentRecommendations();
        $composition = $this->investment_composition ?? [];
        $suggestions = [];
        
        if (empty($composition)) {
            return [
                'error' => 'Empty portfolio'
            ];
        }
        
        // Current allocation by investment type
        $currentAllocation = [];
        foreach ($composition as $investment) {
            $type = $investment['type'] ?? 'Unknown';
            if (!isset($currentAllocation[$type])) {
                $currentAllocation[$type] = 0;
            }
            $currentAllocation[$type] += $investment['current_value'] ?? 0;
        }
        
        // Calculate percentage allocation
        foreach ($currentAllocation as $type => $value) {
            $currentAllocation[$type] = ($value / $this->total_value) * 100;
        }
        
        // Compare with recommended allocation
        foreach ($recommendations as $type => $recommendedPercentage) {
            $currentPercentage = 0;
            
            // Find matching investment type
            foreach ($currentAllocation as $currentType => $percentage) {
                if (stripos($currentType, $type) !== false || stripos($type, $currentType) !== false) {
                    $currentPercentage = $percentage;
                    break;
                }
            }
            
            $difference = $recommendedPercentage - $currentPercentage;
            
            // If difference is significant, add suggestion
            if (abs($difference) >= 5) {
                $action = $difference > 0 ? 'increase' : 'decrease';
                $suggestions[] = [
                    'type' => $type,
                    'current_percentage' => $currentPercentage,
                    'recommended_percentage' => $recommendedPercentage,
                    'difference' => abs($difference),
                    'action' => $action,
                    'amount_to_adjust' => abs($difference * $this->total_value / 100)
                ];
            }
        }
        
        // Sort suggestions by largest difference first
        usort($suggestions, function($a, $b) {
            return $b['difference'] <=> $a['difference'];
        });
        
        return [
            'last_rebalanced' => $this->last_rebalanced,
            'suggestions' => $suggestions
        ];
    }

    /**
     * Execute portfolio rebalancing based on recommendations.
     *
     * @return bool Success status
     */
    public function rebalancePortfolio()
    {
        $rebalancing = $this->suggestRebalancing();
        
        if (isset($rebalancing['error']) || empty($rebalancing['suggestions'])) {
            return false;
        }
        
        // In a real system, this would execute trades or suggest specific actions
        // For simulation purposes, we'll just mark the portfolio as rebalanced
        
        $this->last_rebalanced = Carbon::now(); // Fixed: Use Carbon::now() instead of now()
        return true;
    }

    /**
     * Calculate portfolio performance over time.
     *
     * @param string $timeframe daily|weekly|monthly|yearly
     * @return array Performance data
     */
    public function getPerformanceHistory($timeframe = 'monthly')
    {
        // In a real system, this would query historical data points
        // For simulation, we'll return placeholder data
        
        $periods = 12; // Default for monthly
        
        switch ($timeframe) {
            case 'daily':
                $periods = 30;
                break;
            case 'weekly':
                $periods = 12;
                break;
            case 'yearly':
                $periods = 5;
                break;
        }
        
        $history = [];
        $baseValue = $this->initial_investment;
        $currentValue = $this->total_value;
        $now = Carbon::now(); // Fixed: Use Carbon::now() instead of now()
        
        // Generate simulated historical data
        for ($i = 0; $i <= $periods; $i++) {
            // Determine the method to subtract time periods based on timeframe
            $date = clone $now;
            switch ($timeframe) {
                case 'daily':
                    $date = $date->subDays($periods - $i);
                    break;
                case 'weekly':
                    $date = $date->subWeeks($periods - $i);
                    break;
                case 'monthly':
                    $date = $date->subMonths($periods - $i);
                    break;
                case 'yearly':
                    $date = $date->subYears($periods - $i);
                    break;
            }
            
            $point = [
                'period' => $i,
                'value' => $baseValue + (($currentValue - $baseValue) * $i / $periods),
                'date' => $date->format('Y-m-d')
            ];
            $history[] = $point;
        }
        
        return [
            'timeframe' => $timeframe,
            'initial_value' => $baseValue,
            'current_value' => $currentValue,
            'growth' => $this->return_percentage,
            'history' => $history
        ];
    }

    /**
     * Get Kenya-specific investment opportunities relevant to this portfolio.
     *
     * @return array Investment opportunities
     */
    public function getKenyanInvestmentOpportunities()
    {
        // In a real system, this would query current market opportunities from APIs
        // We'll return placeholder data for common Kenyan investments
        
        $riskCategory = $this->riskProfile ? $this->riskProfile->risk_category : 'Moderate';
        
        $opportunities = [
            'Treasury Bills' => [
                'name' => 'CBK Treasury Bills (91-day)',
                'current_rate' => '13.5%',
                'min_investment' => 'KES 50,000',
                'risk_level' => 'Very Low',
                'suitable_for' => ['Very Conservative', 'Conservative', 'Moderate']
            ],
            'Treasury Bonds' => [
                'name' => 'CBK Treasury Bonds (2-year)',
                'current_rate' => '14.2%',
                'min_investment' => 'KES 50,000',
                'risk_level' => 'Low',
                'suitable_for' => ['Conservative', 'Moderate', 'Aggressive']
            ],
            'NSE Stocks' => [
                'name' => 'Safaricom PLC',
                'current_price' => 'KES 38.50',
                'annual_dividend' => '5.2%',
                'risk_level' => 'Medium',
                'suitable_for' => ['Moderate', 'Aggressive', 'Very Aggressive']
            ],
            'Money Market Funds' => [
                'name' => 'CIC Money Market Fund',
                'current_rate' => '11.8%',
                'min_investment' => 'KES 5,000',
                'risk_level' => 'Low',
                'suitable_for' => ['Very Conservative', 'Conservative', 'Moderate']
            ],
            'REITs' => [
                'name' => 'ILAM Fahari I-REIT',
                'current_price' => 'KES 7.20',
                'annual_yield' => '8.5%',
                'risk_level' => 'Medium-High',
                'suitable_for' => ['Aggressive', 'Very Aggressive']
            ],
            'Unit Trusts' => [
                'name' => 'Britam Equity Fund',
                'performance_ytd' => '12.3%',
                'min_investment' => 'KES 1,000',
                'risk_level' => 'Medium-High',
                'suitable_for' => ['Moderate', 'Aggressive', 'Very Aggressive']
            ]
        ];
        
        // Filter opportunities by risk profile suitability
        $filtered = [];
        foreach ($opportunities as $type => $details) {
            if (in_array($riskCategory, $details['suitable_for'])) {
                $filtered[$type] = $details;
            }
        }
        
        return $filtered;
    }
}
