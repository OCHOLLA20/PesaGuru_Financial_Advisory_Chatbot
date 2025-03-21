<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use App\Models\User;
use App\Models\Loan;
use App\Models\FinancialGoalModel;
use Carbon\Carbon;

class Transaction extends Model
{
    use HasFactory;

    /**
     * The table associated with the model.
     *
     * @var string
     */
    protected $table = 'transactions';

    /**
     * The attributes that are mass assignable.
     *
     * @var array
     */
    protected $fillable = [
        'user_id',
        'loan_id',
        'goal_id',
        'amount',
        'type',
        'category',
        'description',
        'transaction_date',
        'source',
        'destination',
        'reference_number',
        'status',
        'metadata'
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array
     */
    protected $casts = [
        'amount' => 'float',
        'transaction_date' => 'datetime',
        'metadata' => 'array'
    ];

    /**
     * Transaction types
     * 
     * @var array
     */
    public static $TRANSACTION_TYPES = [
        'income',
        'expense',
        'transfer',
        'loan_payment',
        'loan_disbursement',
        'goal_contribution',
        'goal_withdrawal',
        'saving',
        'investment',
        'interest_earned',
        'fee'
    ];

    /**
     * Transaction categories
     * 
     * @var array
     */
    public static $EXPENSE_CATEGORIES = [
        'groceries',
        'rent',
        'utilities',
        'transport',
        'healthcare',
        'dining',
        'entertainment',
        'shopping',
        'travel',
        'education',
        'personal_care',
        'streaming',
        'memberships',
        'software',
        'other'
    ];

    /**
     * Income categories
     * 
     * @var array
     */
    public static $INCOME_CATEGORIES = [
        'salary',
        'business',
        'freelance',
        'investment',
        'rental',
        'gift',
        'refund',
        'other'
    ];

    /**
     * Get the user that owns the transaction.
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the loan associated with the transaction.
     */
    public function loan()
    {
        return $this->belongsTo(Loan::class);
    }

    /**
     * Get the financial goal associated with the transaction.
     */
    public function financialGoal()
    {
        return $this->belongsTo(FinancialGoalModel::class, 'goal_id');
    }

    /**
     * Scope a query to only include transactions of a certain type.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @param  string|array  $types
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeOfType($query, $types)
    {
        if (is_array($types)) {
            return $query->whereIn('type', $types);
        }
        
        return $query->where('type', $types);
    }

    /**
     * Scope a query to only include transactions in a certain category.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @param  string|array  $categories
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeInCategory($query, $categories)
    {
        if (is_array($categories)) {
            return $query->whereIn('category', $categories);
        }
        
        return $query->where('category', $categories);
    }

    /**
     * Scope a query to only include transactions within a date range.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @param  \Carbon\Carbon|string  $startDate
     * @param  \Carbon\Carbon|string  $endDate
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeBetweenDates($query, $startDate, $endDate)
    {
        if (is_string($startDate)) {
            $startDate = Carbon::parse($startDate);
        }
        
        if (is_string($endDate)) {
            $endDate = Carbon::parse($endDate);
        }
        
        return $query->whereBetween('transaction_date', [$startDate, $endDate]);
    }

    /**
     * Scope a query to only include successful transactions.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeSuccessful($query)
    {
        return $query->where('status', 'completed');
    }

    /**
     * Scope a query to only include pending transactions.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopePending($query)
    {
        return $query->where('status', 'pending');
    }

    /**
     * Scope a query to only include failed transactions.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeFailed($query)
    {
        return $query->where('status', 'failed');
    }

    /**
     * Scope a query to only include income transactions.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeIncomeOnly($query)
    {
        return $query->where('type', 'income');
    }

    /**
     * Scope a query to only include expense transactions.
     *
     * @param  \Illuminate\Database\Eloquent\Builder  $query
     * @return \Illuminate\Database\Eloquent\Builder
     */
    public function scopeExpenseOnly($query)
    {
        return $query->where('type', 'expense');
    }

    /**
     * Get the formatted amount with plus/minus sign.
     *
     * @return string
     */
    public function getFormattedAmountAttribute()
    {
        $sign = in_array($this->type, ['income', 'loan_disbursement', 'goal_withdrawal', 'interest_earned']) ? '+' : '-';
        return $sign . number_format(abs($this->amount), 2);
    }

    /**
     * Get the emoji representation of the transaction category.
     *
     * @return string
     */
    public function getCategoryEmojiAttribute()
    {
        $emojiMap = [
            // Expense categories
            'groceries' => '🛒',
            'rent' => '🏠',
            'utilities' => '💡',
            'transport' => '🚗',
            'healthcare' => '⚕️',
            'dining' => '🍽️',
            'entertainment' => '🎭',
            'shopping' => '🛍️',
            'travel' => '✈️',
            'education' => '📚',
            'personal_care' => '💇',
            'streaming' => '📺',
            'memberships' => '🎟️',
            'software' => '💻',
            
            // Income categories
            'salary' => '💼',
            'business' => '🏢',
            'freelance' => '🔧',
            'investment' => '📈',
            'rental' => '🏘️',
            'gift' => '🎁',
            'refund' => '↩️',
            
            // Transaction types
            'income' => '💰',
            'expense' => '💸',
            'transfer' => '↔️',
            'loan_payment' => '🏦',
            'loan_disbursement' => '💵',
            'goal_contribution' => '🎯',
            'goal_withdrawal' => '🔄',
            'saving' => '🏦',
            'interest_earned' => '💹',
            'fee' => '🧾',
            
            // Default
            'other' => '❓'
        ];
        
        // Try to get emoji for category first
        if (isset($emojiMap[$this->category])) {
            return $emojiMap[$this->category];
        }
        
        // Fall back to type emoji
        if (isset($emojiMap[$this->type])) {
            return $emojiMap[$this->type];
        }
        
        return $emojiMap['other'];
    }

    /**
     * Get the principal and interest portions for loan payments.
     *
     * @return array|null
     */
    public function getLoanPaymentDetailsAttribute()
    {
        if ($this->type !== 'loan_payment') {
            return null;
        }
        
        $metadata = is_array($this->metadata) ? $this->metadata : json_decode($this->metadata, true) ?? [];
        
        if (isset($metadata['principal_portion']) && isset($metadata['interest_portion'])) {
            return [
                'principal' => $metadata['principal_portion'],
                'interest' => $metadata['interest_portion'],
                'payment_number' => $metadata['payment_number'] ?? null,
                'balance_before' => $metadata['balance_before'] ?? null,
                'balance_after' => $metadata['balance_after'] ?? null
            ];
        }
        
        return null;
    }

    /**
     * Get payments summary for a given user and period.
     *
     * @param int $userId
     * @param string $period 'day', 'week', 'month', 'year'
     * @param int $limit How many periods to go back
     * @return array
     */
    public static function getPaymentsSummary($userId, $period = 'month', $limit = 6)
    {
        $results = [];
        $now = Carbon::now();
        
        for ($i = 0; $i < $limit; $i++) {
            $periodStart = self::getPeriodStartDate($now, $period, $i);
            $periodEnd = self::getPeriodEndDate($periodStart, $period);
            
            $transactions = self::where('user_id', $userId)
                ->whereBetween('transaction_date', [$periodStart, $periodEnd])
                ->get();
            
            $income = $transactions->whereIn('type', ['income', 'interest_earned'])->sum('amount');
            $expenses = $transactions->where('type', 'expense')->sum('amount');
            $savings = $transactions->whereIn('type', ['saving', 'goal_contribution'])->sum('amount');
            
            $periodLabel = self::getPeriodLabel($periodStart, $period);
            
            $results[] = [
                'period' => $periodLabel,
                'income' => $income,
                'expenses' => $expenses,
                'savings' => $savings,
                'net' => $income - $expenses,
                'start_date' => $periodStart->format('Y-m-d'),
                'end_date' => $periodEnd->format('Y-m-d')
            ];
        }
        
        // Reverse to get chronological order
        return array_reverse($results);
    }
    
    /**
     * Get spending breakdown by category for a user.
     *
     * @param int $userId
     * @param \Carbon\Carbon|string $startDate
     * @param \Carbon\Carbon|string $endDate
     * @return array
     */
    public static function getSpendingByCategory($userId, $startDate, $endDate)
    {
        if (is_string($startDate)) {
            $startDate = Carbon::parse($startDate);
        }
        
        if (is_string($endDate)) {
            $endDate = Carbon::parse($endDate);
        }
        
        $transactions = self::where('user_id', $userId)
            ->where('type', 'expense')
            ->whereBetween('transaction_date', [$startDate, $endDate])
            ->get();
        
        $totalSpending = $transactions->sum('amount');
        $categories = [];
        
        foreach (self::$EXPENSE_CATEGORIES as $category) {
            $amount = $transactions->where('category', $category)->sum('amount');
            
            if ($amount > 0) {
                $categories[] = [
                    'category' => $category,
                    'amount' => $amount,
                    'percentage' => $totalSpending > 0 ? round(($amount / $totalSpending) * 100, 1) : 0,
                    'emoji' => self::getCategoryEmoji($category)
                ];
            }
        }
        
        // Other category for uncategorized expenses
        $otherAmount = $transactions->whereNotIn('category', self::$EXPENSE_CATEGORIES)->sum('amount');
        if ($otherAmount > 0) {
            $categories[] = [
                'category' => 'other',
                'amount' => $otherAmount,
                'percentage' => $totalSpending > 0 ? round(($otherAmount / $totalSpending) * 100, 1) : 0,
                'emoji' => '❓'
            ];
        }
        
        // Sort by amount (highest first)
        usort($categories, function($a, $b) {
            return $b['amount'] <=> $a['amount'];
        });
        
        return [
            'total' => $totalSpending,
            'categories' => $categories,
            'start_date' => $startDate->format('Y-m-d'),
            'end_date' => $endDate->format('Y-m-d')
        ];
    }
    
    /**
     * Process a transaction that contributes to a financial goal.
     *
     * @param int $userId
     * @param int $goalId
     * @param float $amount
     * @param string $source
     * @param string $description
     * @return Transaction
     */
    public static function createGoalContribution($userId, $goalId, $amount, $source = 'manual', $description = null)
    {
        $goal = FinancialGoalModel::findOrFail($goalId);
        
        if (!$description) {
            $description = "Contribution to {$goal->name}";
        }
        
        $transaction = new self([
            'user_id' => $userId,
            'goal_id' => $goalId,
            'amount' => $amount,
            'type' => 'goal_contribution',
            'category' => $goal->type,
            'description' => $description,
            'transaction_date' => Carbon::now(),
            'source' => $source,
            'status' => 'completed',
            'metadata' => json_encode([
                'goal_name' => $goal->name,
                'goal_type' => $goal->type,
                'previous_amount' => $goal->current_amount,
                'new_amount' => $goal->current_amount + $amount
            ])
        ]);
        
        $transaction->save();
        
        // Update goal progress
        $goal->updateProgress($goal->current_amount + $amount);
        
        return $transaction;
    }
    
    /**
     * Get a static category emoji.
     *
     * @param string $category
     * @return string
     */
    public static function getCategoryEmoji($category)
    {
        $emojiMap = [
            // Expense categories
            'groceries' => '🛒',
            'rent' => '🏠',
            'utilities' => '💡',
            'transport' => '🚗',
            'healthcare' => '⚕️',
            'dining' => '🍽️',
            'entertainment' => '🎭',
            'shopping' => '🛍️',
            'travel' => '✈️',
            'education' => '📚',
            'personal_care' => '💇',
            'streaming' => '📺',
            'memberships' => '🎟️',
            'software' => '💻',
            
            // Income categories
            'salary' => '💼',
            'business' => '🏢',
            'freelance' => '🔧',
            'investment' => '📈',
            'rental' => '🏘️',
            'gift' => '🎁',
            'refund' => '↩️',
            
            // Default
            'other' => '❓'
        ];
        
        return $emojiMap[$category] ?? $emojiMap['other'];
    }
    
    /**
     * Get the start date for a given period.
     *
     * @param \Carbon\Carbon $date
     * @param string $period
     * @param int $periodsBack
     * @return \Carbon\Carbon
     */
    private static function getPeriodStartDate($date, $period, $periodsBack)
    {
        $date = $date->copy();
        
        switch ($period) {
            case 'day':
                return $date->subDays($periodsBack)->startOfDay();
            case 'week':
                return $date->subWeeks($periodsBack)->startOfWeek();
            case 'year':
                return $date->subYears($periodsBack)->startOfYear();
            case 'month':
            default:
                return $date->subMonths($periodsBack)->startOfMonth();
        }
    }
    
    /**
     * Get the end date for a given period.
     *
     * @param \Carbon\Carbon $startDate
     * @param string $period
     * @return \Carbon\Carbon
     */
    private static function getPeriodEndDate($startDate, $period)
    {
        $date = $startDate->copy();
        
        switch ($period) {
            case 'day':
                return $date->endOfDay();
            case 'week':
                return $date->endOfWeek();
            case 'year':
                return $date->endOfYear();
            case 'month':
            default:
                return $date->endOfMonth();
        }
    }
    
    /**
     * Get a human-readable label for a period.
     *
     * @param \Carbon\Carbon $date
     * @param string $period
     * @return string
     */
    private static function getPeriodLabel($date, $period)
    {
        switch ($period) {
            case 'day':
                return $date->format('M j');
            case 'week':
                return $date->format('M j') . ' - ' . $date->copy()->endOfWeek()->format('M j');
            case 'year':
                return $date->format('Y');
            case 'month':
            default:
                return $date->format('M Y');
        }
    }
    
    /**
     * Get transaction flow for a user (income vs expenses).
     *
     * @param int $userId
     * @param int $months
     * @return array
     */
    public static function getTransactionFlow($userId, $months = 6)
    {
        $results = [];
        $now = Carbon::now();
        
        for ($i = 0; $i < $months; $i++) {
            $month = $now->copy()->subMonths($i);
            $startOfMonth = $month->copy()->startOfMonth();
            $endOfMonth = $month->copy()->endOfMonth();
            
            $income = self::where('user_id', $userId)
                ->whereIn('type', ['income', 'interest_earned'])
                ->whereBetween('transaction_date', [$startOfMonth, $endOfMonth])
                ->sum('amount');
                
            $expenses = self::where('user_id', $userId)
                ->where('type', 'expense')
                ->whereBetween('transaction_date', [$startOfMonth, $endOfMonth])
                ->sum('amount');
                
            $results[] = [
                'month' => $month->format('M Y'),
                'income' => $income,
                'expenses' => $expenses,
                'net' => $income - $expenses
            ];
        }
        
        return array_reverse($results);
    }
    
    /**
     * Create a batch of transactions from file import.
     *
     * @param int $userId
     * @param array $transactions
     * @return array
     */
    public static function createBatch($userId, $transactions)
    {
        $created = [];
        $failed = [];
        
        foreach ($transactions as $data) {
            try {
                // Set required fields
                $data['user_id'] = $userId;
                $data['status'] = $data['status'] ?? 'completed';
                
                // Parse transaction date if it's a string
                if (isset($data['transaction_date']) && is_string($data['transaction_date'])) {
                    $data['transaction_date'] = Carbon::parse($data['transaction_date']);
                } else {
                    $data['transaction_date'] = Carbon::now();
                }
                
                // Create the transaction
                $transaction = new self($data);
                $transaction->save();
                
                // If it's a goal contribution, update the goal
                if (isset($data['goal_id']) && in_array($data['type'], ['goal_contribution'])) {
                    $goal = FinancialGoalModel::find($data['goal_id']);
                    if ($goal) {
                        $goal->updateProgress($goal->current_amount + $data['amount']);
                    }
                }
                
                $created[] = $transaction;
            } catch (\Exception $e) {
                $failed[] = [
                    'data' => $data,
                    'error' => $e->getMessage()
                ];
            }
        }
        
        return [
            'created' => $created,
            'failed' => $failed
        ];
    }
}
