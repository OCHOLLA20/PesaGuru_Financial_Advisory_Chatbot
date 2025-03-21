<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use App\Models\SpendingAnalysis;
use App\Services\InvestmentAdapter;
use App\Models\LoanRepaymentTracker;
use Carbon\Carbon;
use App\Events\GoalProgressUpdated;
use Illuminate\Support\Facades\App;
use Illuminate\Support\Facades\Event;

class FinancialGoalModel extends Model
{
    protected $table = 'financial_goals';
    
    protected $fillable = [
        'user_id',
        'name',
        'type',
        'target_amount',
        'current_amount',
        'target_date',
        'contribution_frequency',
        'contribution_amount',
        'progress_percentage',
        'status',
        'investment_allocation',
        'metadata'
    ];
    
    protected $casts = [
        'target_date' => 'date',
        'metadata' => 'array'
    ];
    
    /**
     * Create a new financial goal with integrated features
     * 
     * @param array $goalData
     * @return FinancialGoalModel
     */
    public static function createGoal(array $goalData): self
    {
        // Create base goal
        $goal = new self($goalData);
        $goal->progress_percentage = ($goal->current_amount / $goal->target_amount) * 100;
        $goal->status = 'active';
        
        // Set default investment allocation based on goal type and timeline
        if (in_array($goal->type, ['investment', 'retirement', 'education'])) {
            $goal->investment_allocation = self::getDefaultInvestmentAllocation($goal);
        }
        
        // For debt repayment goals, link with loan
        if ($goal->type === 'debt_repayment' && isset($goalData['loan_id'])) {
            $loanTracker = new LoanRepaymentTracker();
            $loanStats = $loanTracker->trackLoanProgress($goalData['loan_id'], $goal->id);
            
            // Update goal with loan data
            $metadata = $goal->metadata ?? [];
            $metadata['loan_id'] = $goalData['loan_id'];
            $metadata['loan_stats'] = $loanStats;
            $goal->metadata = $metadata;
        }
        
        $goal->save();
        
        // Generate savings suggestions based on spending
        if ($goal->type === 'savings' || $goal->type === 'emergency_fund') {
            $goal->generateSavingsSuggestions();
        }
        
        return $goal;
    }
    
    /**
     * Update goal progress and check for milestones/alerts
     * 
     * @param float $newAmount
     * @return array
     */
    public function updateProgress(float $newAmount): array
    {
        $oldAmount = $this->current_amount;
        $oldPercentage = $this->progress_percentage;
        
        $this->current_amount = $newAmount;
        $this->progress_percentage = min(100, ($newAmount / $this->target_amount) * 100);
        
        // Check if goal is completed
        if ($this->progress_percentage >= 100) {
            $this->status = 'completed';
            $this->markAsComplete();
        }
        
        $this->save();
        
        // Generate alerts if needed
        $alerts = $this->checkProgressAlerts($oldPercentage);
        
        // For investment goals, adjust allocation if needed
        if (in_array($this->type, ['investment', 'retirement', 'education']) && 
            $this->status === 'active') {
            $this->checkAndAdjustInvestments();
        }
        
        // For debt goals, update loan tracking
        if ($this->type === 'debt_repayment' && isset($this->metadata['loan_id'])) {
            $loanTracker = new LoanRepaymentTracker();
            $loanTracker->trackLoanProgress($this->metadata['loan_id'], $this->id);
        }
        
        // Trigger event for notifications
        Event::dispatch(new GoalProgressUpdated($this, $oldAmount, $newAmount));
        
        return [
            'old_amount' => $oldAmount,
            'new_amount' => $newAmount,
            'progress_percentage' => $this->progress_percentage,
            'alerts' => $alerts
        ];
    }
    
    /**
     * Check if any progress alerts should be triggered
     * 
     * @param float $oldPercentage
     * @return array
     */
    private function checkProgressAlerts(float $oldPercentage): array
    {
        $alerts = [];
        
        // Milestone alerts (25%, 50%, 75%, 100%)
        $milestones = [25, 50, 75, 100];
        foreach ($milestones as $milestone) {
            if ($oldPercentage < $milestone && $this->progress_percentage >= $milestone) {
                $alerts[] = [
                    'type' => 'milestone',
                    'milestone' => $milestone,
                    'message' => "Congratulations! You've reached {$milestone}% of your '{$this->name}' goal."
                ];
            }
        }
        
        // Timeline alerts
        $today = Carbon::today();
        $targetDate = $this->target_date;
        $daysRemaining = $today->diffInDays($targetDate, false);
        
        // If target date is approaching but progress is behind
        if ($daysRemaining <= 30 && $daysRemaining > 0 && $this->progress_percentage < 90) {
            $alerts[] = [
                'type' => 'timeline_warning',
                'days_remaining' => $daysRemaining,
                'current_progress' => $this->progress_percentage,
                'message' => "Your goal '{$this->name}' is due in {$daysRemaining} days but is only {$this->progress_percentage}% complete."
            ];
        }
        
        // Goal is behind schedule (based on linear progress expectation)
        $totalDays = Carbon::parse($this->created_at)->diffInDays($targetDate);
        $elapsedDays = Carbon::parse($this->created_at)->diffInDays($today);
        $expectedProgress = ($elapsedDays / $totalDays) * 100;
        
        if ($expectedProgress - $this->progress_percentage > 15 && $elapsedDays > 30) {
            $alerts[] = [
                'type' => 'behind_schedule',
                'expected_progress' => round($expectedProgress, 1),
                'current_progress' => $this->progress_percentage,
                'difference' => round($expectedProgress - $this->progress_percentage, 1),
                'message' => "Your goal '{$this->name}' is behind schedule. Expected: {$expectedProgress}%, Actual: {$this->progress_percentage}%."
            ];
        }
        
        return $alerts;
    }
    
    /**
     * Get default investment allocation based on goal type and timeline
     * 
     * @param FinancialGoalModel $goal
     * @return string
     */
    private static function getDefaultInvestmentAllocation($goal): string
    {
        $months = Carbon::now()->diffInMonths($goal->target_date);
        $allocation = [];
        
        if ($months <= 12) {
            // Short-term: Conservative
            $allocation = [
                'equity' => 20,
                'bonds' => 40,
                'money_market' => 40,
                'alternative' => 0
            ];
        } elseif ($months <= 60) {
            // Medium-term: Moderate
            $allocation = [
                'equity' => 50,
                'bonds' => 30,
                'money_market' => 15,
                'alternative' => 5
            ];
        } else {
            // Long-term: Growth-oriented
            $allocation = [
                'equity' => 70,
                'bonds' => 20,
                'money_market' => 5,
                'alternative' => 5
            ];
        }
        
        // Adjust for education goals
        if ($goal->type === 'education') {
            $allocation['bonds'] += 10;
            $allocation['equity'] -= 10;
        }
        
        // Adjust for retirement goals
        if ($goal->type === 'retirement' && $months > 120) {
            $allocation['equity'] += 5;
            $allocation['alternative'] += 5;
            $allocation['bonds'] -= 10;
        }
        
        return json_encode($allocation);
    }
    
    /**
     * Mark goal as complete and trigger completion actions
     * 
     * @return void
     */
    private function markAsComplete(): void
    {
        $this->status = 'completed';
        $this->metadata = array_merge($this->metadata ?? [], [
            'completed_date' => Carbon::now()->format('Y-m-d'),
            'actual_duration_days' => Carbon::parse($this->created_at)->diffInDays(Carbon::now())
        ]);
        
        // Additional completion logic can be added here
    }
    
    /**
     * Check for and apply investment adjustments
     * 
     * @return array|null
     */
    public function checkAndAdjustInvestments(): ?array
    {
        // Skip if no investment allocation or not an investment type goal
        if (!$this->investment_allocation || !in_array($this->type, ['investment', 'retirement', 'education'])) {
            return null;
        }
        
        // Check if we should adjust (e.g., based on last adjustment date)
        $metadata = $this->metadata ?? [];
        $lastAdjustment = $metadata['last_investment_adjustment'] ?? null;
        
        // Only adjust every 30 days or if first time
        if ($lastAdjustment && Carbon::parse($lastAdjustment)->diffInDays(Carbon::now()) < 30) {
            return null;
        }
        
        // Get investment provider from user preferences or default
        $investmentProvider = App::make('InvestmentProviderInterface');
        
        // Create adapter and adjust allocation
        $adapter = new InvestmentAdapter($investmentProvider, $this->user_id);
        $adjustmentResult = $adapter->adjustInvestmentAllocation($this->id);
        
        // Update goal with new allocation
        $this->investment_allocation = json_encode($adjustmentResult['adjusted_allocation']);
        $this->metadata = array_merge($this->metadata ?? [], [
            'last_investment_adjustment' => Carbon::now()->format('Y-m-d H:i:s'),
            'investment_adjustment_summary' => $adjustmentResult['adjustment_summary'],
            'market_factors' => $adjustmentResult['market_factors']
        ]);
        
        $this->save();
        
        return $adjustmentResult;
    }
    
    /**
     * Generate savings suggestions based on spending analysis
     * 
     * @return array
     */
    public function generateSavingsSuggestions(): array
    {
        $spendingAnalysis = new SpendingAnalysis($this->user_id);
        
        // Get savings opportunities
        $opportunities = $spendingAnalysis->generateSavingsOpportunities();
        
        // Get automated savings rules
        $rules = $spendingAnalysis->generateSavingsRules();
        
        // Update goal metadata with suggestions
        $this->metadata = array_merge($this->metadata ?? [], [
            'savings_opportunities' => $opportunities,
            'savings_rules' => $rules,
            'savings_analysis_date' => Carbon::now()->format('Y-m-d')
        ]);
        
        $this->save();
        
        return [
            'opportunities' => $opportunities,
            'rules' => $rules
        ];
    }
    
    /**
     * Calculate if goal is achievable with current contribution rate
     * 
     * @return array
     */
    public function calculateGoalFeasibility(): array
    {
        $currentAmount = $this->current_amount;
        $targetAmount = $this->target_amount;
        $remaining = $targetAmount - $currentAmount;
        
        if ($remaining <= 0) {
            return [
                'is_achievable' => true,
                'status' => 'already_achieved',
                'surplus' => abs($remaining)
            ];
        }
        
        $today = Carbon::today();
        $targetDate = $this->target_date;
        $monthsRemaining = $today->diffInMonths($targetDate);
        
        if ($monthsRemaining <= 0) {
            return [
                'is_achievable' => false,
                'status' => 'deadline_passed',
                'deficit' => $remaining
            ];
        }
        
        // Calculate required monthly contribution
        $requiredMonthly = $remaining / $monthsRemaining;
        $currentMonthly = $this->contribution_amount;
        
        // For investment goals, add estimated returns
        $estimatedReturns = 0;
        if (in_array($this->type, ['investment', 'retirement', 'education'])) {
            $allocation = json_decode($this->investment_allocation, true) ?? [];
            $expectedRate = $this->calculateExpectedReturnRate($allocation);
            
            // Simple future value calculation with monthly compounding
            $estimatedFutureValue = $currentAmount * pow(1 + $expectedRate/12, $monthsRemaining);
            $estimatedReturns = $estimatedFutureValue - $currentAmount;
            
            // Adjust required monthly contribution
            $requiredMonthly = max(0, ($remaining - $estimatedReturns) / $monthsRemaining);
        }
        
        $isAchievable = $currentMonthly >= $requiredMonthly;
        
        return [
            'is_achievable' => $isAchievable,
            'status' => $isAchievable ? 'on_track' : 'needs_adjustment',
            'current_monthly_contribution' => $currentMonthly,
            'required_monthly_contribution' => $requiredMonthly,
            'contribution_gap' => $isAchievable ? 0 : ($requiredMonthly - $currentMonthly),
            'months_remaining' => $monthsRemaining,
            'estimated_investment_returns' => $estimatedReturns
        ];
    }
    
    /**
     * Calculate expected return rate based on asset allocation
     * 
     * @param array $allocation
     * @return float
     */
    private function calculateExpectedReturnRate(array $allocation): float
    {
        // Simplified expected returns for asset classes
        $expectedReturns = [
            'equity' => 0.08, // 8% annually
            'bonds' => 0.04,  // 4% annually
            'money_market' => 0.015, // 1.5% annually
            'alternative' => 0.06  // 6% annually
        ];
        
        $weightedReturn = 0;
        foreach ($allocation as $asset => $percentage) {
            if (isset($expectedReturns[$asset])) {
                $weightedReturn += ($percentage / 100) * $expectedReturns[$asset];
            }
        }
        
        return $weightedReturn;
    }
    
    /**
     * Get debt repayment strategies for user
     * 
     * @return array|null
     */
    public function getDebtRepaymentStrategies(): ?array
    {
        if ($this->type !== 'debt_repayment') {
            return null;
        }
        
        $loanTracker = new LoanRepaymentTracker();
        return $loanTracker->generateDebtRepaymentStrategies($this->user_id);
    }
}
