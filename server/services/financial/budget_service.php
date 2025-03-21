<?php
/**
 * Budget Service
 * 
 * Handles all budget-related functionality for the PesaGuru financial advisory chatbot
 * including creating budgets, tracking expenses, analyzing spending patterns,
 * and providing personalized budget recommendations for Kenyan users.
 * 
 * @package PesaGuru
 * @subpackage Services/Financial
 */

require_once __DIR__ . '/../../config/db.php';
require_once __DIR__ . '/../../models/User.php';
require_once __DIR__ . '/../../models/FinancialGoal.php';

class BudgetService {
    private $db;
    private $user_id;
    private $income_categories = [
        'salary' => 'Primary Employment',
        'business' => 'Business Income',
        'investments' => 'Investment Returns',
        'rental' => 'Rental Income',
        'freelance' => 'Freelance/Side Hustle',
        'gifts' => 'Gifts/Support',
        'other' => 'Other Income'
    ];
    
    private $expense_categories = [
        'housing' => 'Housing & Utilities',
        'food' => 'Food & Groceries',
        'transport' => 'Transportation',
        'education' => 'Education',
        'healthcare' => 'Healthcare',
        'entertainment' => 'Entertainment',
        'savings' => 'Savings & Investments',
        'debt' => 'Debt Repayments',
        'personal' => 'Personal Care',
        'shopping' => 'Shopping',
        'mpesa' => 'Mobile Money Fees',
        'others' => 'Others'
    ];
    
    // Kenyan-specific budget recommendation percentages
    private $recommended_budget_percentages = [
        'housing' => 30, // Housing is expensive in urban Kenya
        'food' => 25,    // Food takes a significant portion in Kenya
        'transport' => 15,
        'education' => 10,
        'healthcare' => 5,
        'entertainment' => 5,
        'savings' => 10,  // Encourage savings
        'debt' => 0,      // This is dynamic based on actual debt
        'personal' => 5,
        'shopping' => 5,
        'mpesa' => 1,
        'others' => 4
    ];
    
    /**
     * Constructor
     * 
     * @param int $user_id The ID of the currently logged-in user
     */
    public function __construct($user_id = null) {
        global $conn;
        $this->db = $conn;
        $this->user_id = $user_id;
    }
    
    /**
     * Create a new budget for a user
     * 
     * @param array $budget_data Budget information including income and category allocations
     * @return array Response with status and message
     */
    public function createBudget($budget_data) {
        try {
            // Validate required fields
            if (!isset($budget_data['total_income']) || !isset($budget_data['budget_name'])) {
                return [
                    'status' => 'error',
                    'message' => 'Missing required budget information'
                ];
            }
            
            // Start a transaction
            $this->db->begin_transaction();
            
            // Create the budget
            $stmt = $this->db->prepare("
                INSERT INTO budgets (user_id, budget_name, total_income, start_date, end_date, currency, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ");
            
            // Set default dates to current month if not provided
            $start_date = isset($budget_data['start_date']) ? $budget_data['start_date'] : date('Y-m-01');
            $end_date = isset($budget_data['end_date']) ? $budget_data['end_date'] : date('Y-m-t');
            $currency = isset($budget_data['currency']) ? $budget_data['currency'] : 'KES'; // Default to Kenyan Shilling
            
            $stmt->bind_param(
                "isdssss",
                $this->user_id,
                $budget_data['budget_name'],
                $budget_data['total_income'],
                $start_date,
                $end_date,
                $currency,
                $budget_data['description'] ?? ''
            );
            
            if (!$stmt->execute()) {
                $this->db->rollback();
                return [
                    'status' => 'error',
                    'message' => 'Failed to create budget: ' . $this->db->error
                ];
            }
            
            $budget_id = $this->db->insert_id;
            
            // Add budget categories if specified
            if (isset($budget_data['categories']) && is_array($budget_data['categories'])) {
                foreach ($budget_data['categories'] as $category => $amount) {
                    $category_name = isset($this->expense_categories[$category]) ? 
                                    $this->expense_categories[$category] : $category;
                    
                    $stmt = $this->db->prepare("
                        INSERT INTO budget_categories (budget_id, category, amount)
                        VALUES (?, ?, ?)
                    ");
                    
                    $stmt->bind_param("isd", $budget_id, $category_name, $amount);
                    
                    if (!$stmt->execute()) {
                        $this->db->rollback();
                        return [
                            'status' => 'error',
                            'message' => 'Failed to add budget category: ' . $this->db->error
                        ];
                    }
                }
            } else {
                // If categories not specified, create default allocations based on percentages
                $this->createDefaultBudgetAllocations($budget_id, $budget_data['total_income']);
            }
            
            // Commit the transaction
            $this->db->commit();
            
            return [
                'status' => 'success',
                'message' => 'Budget created successfully',
                'budget_id' => $budget_id
            ];
            
        } catch (Exception $e) {
            $this->db->rollback();
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Create default budget allocations based on recommended percentages
     * 
     * @param int $budget_id Budget ID
     * @param float $total_income Total income amount
     * @return bool Success status
     */
    private function createDefaultBudgetAllocations($budget_id, $total_income) {
        try {
            foreach ($this->recommended_budget_percentages as $category => $percentage) {
                $amount = ($percentage / 100) * $total_income;
                $category_name = $this->expense_categories[$category];
                
                $stmt = $this->db->prepare("
                    INSERT INTO budget_categories (budget_id, category, amount)
                    VALUES (?, ?, ?)
                ");
                
                $stmt->bind_param("isd", $budget_id, $category_name, $amount);
                
                if (!$stmt->execute()) {
                    throw new Exception('Failed to add default category: ' . $this->db->error);
                }
            }
            
            return true;
        } catch (Exception $e) {
            error_log('Error creating default budget allocations: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Add an expense to track against the budget
     * 
     * @param array $expense_data Expense information
     * @return array Response with status and message
     */
    public function addExpense($expense_data) {
        try {
            // Validate required fields
            if (!isset($expense_data['amount']) || !isset($expense_data['category']) || !isset($expense_data['budget_id'])) {
                return [
                    'status' => 'error',
                    'message' => 'Missing required expense information'
                ];
            }
            
            // Create the expense
            $stmt = $this->db->prepare("
                INSERT INTO expenses (user_id, budget_id, category, amount, description, expense_date, payment_method, receipt_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ");
            
            // Set default date to today if not provided
            $expense_date = isset($expense_data['expense_date']) ? $expense_data['expense_date'] : date('Y-m-d');
            
            $stmt->bind_param(
                "iisdsssb",
                $this->user_id,
                $expense_data['budget_id'],
                $expense_data['category'],
                $expense_data['amount'],
                $expense_data['description'] ?? '',
                $expense_date,
                $expense_data['payment_method'] ?? 'M-Pesa', // Default payment method in Kenya
                $expense_data['receipt_image'] ?? null
            );
            
            if (!$stmt->execute()) {
                return [
                    'status' => 'error',
                    'message' => 'Failed to add expense: ' . $this->db->error
                ];
            }
            
            $expense_id = $this->db->insert_id;
            
            // Check if this expense puts the category over budget
            $budget_alert = $this->checkBudgetAlert($expense_data['budget_id'], $expense_data['category']);
            
            $result = [
                'status' => 'success',
                'message' => 'Expense added successfully',
                'expense_id' => $expense_id
            ];
            
            if ($budget_alert) {
                $result['alert'] = $budget_alert;
            }
            
            return $result;
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Check if an expense puts a category over budget and generate alert
     * 
     * @param int $budget_id Budget ID
     * @param string $category Expense category
     * @return array|null Budget alert if over budget, null otherwise
     */
    private function checkBudgetAlert($budget_id, $category) {
        try {
            // Get the budget allocation for this category
            $stmt = $this->db->prepare("
                SELECT amount FROM budget_categories 
                WHERE budget_id = ? AND category = ?
            ");
            
            $stmt->bind_param("is", $budget_id, $category);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return null; // No budget for this category
            }
            
            $budget_row = $result->fetch_assoc();
            $budget_amount = $budget_row['amount'];
            
            // Get total spent in this category
            $stmt = $this->db->prepare("
                SELECT SUM(amount) as total_spent FROM expenses 
                WHERE budget_id = ? AND category = ?
            ");
            
            $stmt->bind_param("is", $budget_id, $category);
            $stmt->execute();
            $result = $stmt->get_result();
            $expense_row = $result->fetch_assoc();
            $total_spent = $expense_row['total_spent'] ?? 0;
            
            // Calculate percentage of budget used
            $percentage_used = ($total_spent / $budget_amount) * 100;
            
            // Generate alert based on percentage used
            if ($percentage_used >= 100) {
                return [
                    'level' => 'danger',
                    'message' => 'You have exceeded your budget for ' . $category . ' by ' . 
                                number_format($total_spent - $budget_amount, 2) . ' KES'
                ];
            } else if ($percentage_used >= 90) {
                return [
                    'level' => 'warning',
                    'message' => 'You have used ' . number_format($percentage_used, 1) . '% of your ' . 
                                $category . ' budget'
                ];
            } else if ($percentage_used >= 75) {
                return [
                    'level' => 'info',
                    'message' => 'You have used ' . number_format($percentage_used, 1) . '% of your ' . 
                                $category . ' budget'
                ];
            }
            
            return null;
            
        } catch (Exception $e) {
            error_log('Error checking budget alert: ' . $e->getMessage());
            return null;
        }
    }
    
    /**
     * Get a user's current budget status
     * 
     * @param int $budget_id Budget ID (optional, gets active budget if not specified)
     * @return array Budget status with allocations and spending
     */
    public function getBudgetStatus($budget_id = null) {
        try {
            // If budget_id not specified, get the most recent active budget
            if ($budget_id === null) {
                $stmt = $this->db->prepare("
                    SELECT id FROM budgets 
                    WHERE user_id = ? AND start_date <= CURRENT_DATE() AND end_date >= CURRENT_DATE()
                    ORDER BY created_at DESC LIMIT 1
                ");
                
                $stmt->bind_param("i", $this->user_id);
                $stmt->execute();
                $result = $stmt->get_result();
                
                if ($result->num_rows === 0) {
                    return [
                        'status' => 'error',
                        'message' => 'No active budget found'
                    ];
                }
                
                $row = $result->fetch_assoc();
                $budget_id = $row['id'];
            }
            
            // Get budget details
            $stmt = $this->db->prepare("
                SELECT * FROM budgets WHERE id = ? AND user_id = ?
            ");
            
            $stmt->bind_param("ii", $budget_id, $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'status' => 'error',
                    'message' => 'Budget not found or access denied'
                ];
            }
            
            $budget = $result->fetch_assoc();
            
            // Get budget categories and allocations
            $stmt = $this->db->prepare("
                SELECT * FROM budget_categories WHERE budget_id = ?
            ");
            
            $stmt->bind_param("i", $budget_id);
            $stmt->execute();
            $categories_result = $stmt->get_result();
            
            $categories = [];
            while ($category = $categories_result->fetch_assoc()) {
                $categories[$category['category']] = [
                    'allocation' => $category['amount'],
                    'spent' => 0,
                    'remaining' => $category['amount']
                ];
            }
            
            // Get expenses for this budget
            $stmt = $this->db->prepare("
                SELECT category, SUM(amount) as total_spent 
                FROM expenses 
                WHERE budget_id = ? 
                GROUP BY category
            ");
            
            $stmt->bind_param("i", $budget_id);
            $stmt->execute();
            $expenses_result = $stmt->get_result();
            
            // Track overall totals
            $total_allocated = 0;
            $total_spent = 0;
            
            // Update categories with spending
            while ($expense = $expenses_result->fetch_assoc()) {
                if (isset($categories[$expense['category']])) {
                    $categories[$expense['category']]['spent'] = $expense['total_spent'];
                    $categories[$expense['category']]['remaining'] = 
                        $categories[$expense['category']]['allocation'] - $expense['total_spent'];
                } else {
                    // Handle expenses in categories not in budget
                    $categories[$expense['category']] = [
                        'allocation' => 0,
                        'spent' => $expense['total_spent'],
                        'remaining' => -$expense['total_spent']
                    ];
                }
            }
            
            // Calculate totals and percentages
            foreach ($categories as &$category) {
                $total_allocated += $category['allocation'];
                $total_spent += $category['spent'];
                
                // Calculate percentage of allocation used
                if ($category['allocation'] > 0) {
                    $category['percentage_used'] = ($category['spent'] / $category['allocation']) * 100;
                } else {
                    $category['percentage_used'] = 0;
                }
            }
            
            // Calculate overall budget usage
            $overall_percentage = $total_allocated > 0 ? ($total_spent / $total_allocated) * 100 : 0;
            
            return [
                'status' => 'success',
                'budget' => $budget,
                'categories' => $categories,
                'total_allocated' => $total_allocated,
                'total_spent' => $total_spent,
                'total_remaining' => $total_allocated - $total_spent,
                'overall_percentage' => $overall_percentage,
                'days_remaining' => $this->getDaysRemaining($budget['end_date'])
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Calculate days remaining in a budget period
     * 
     * @param string $end_date End date of budget period
     * @return int Number of days remaining
     */
    private function getDaysRemaining($end_date) {
        $end = new DateTime($end_date);
        $now = new DateTime();
        
        if ($now > $end) {
            return 0;
        }
        
        return $now->diff($end)->days;
    }
    
    /**
     * Get budget recommendations based on spending patterns
     * 
     * @return array Budget recommendations
     */
    public function getBudgetRecommendations() {
        try {
            // Get user's income
            $stmt = $this->db->prepare("
                SELECT total_income FROM budgets
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                // If no budget exists, use a default income amount
                $income = 50000; // Default Kenyan middle-income salary in KES
            } else {
                $row = $result->fetch_assoc();
                $income = $row['total_income'];
            }
            
            // Get user's spending patterns from the last 3 months
            $stmt = $this->db->prepare("
                SELECT category, AVG(amount) as avg_amount
                FROM expenses
                WHERE user_id = ? AND expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
                GROUP BY category
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $spending_result = $stmt->get_result();
            
            $spending_patterns = [];
            $total_monthly_spending = 0;
            
            while ($spending = $spending_result->fetch_assoc()) {
                $spending_patterns[$spending['category']] = $spending['avg_amount'];
                $total_monthly_spending += $spending['avg_amount'];
            }
            
            // Generate recommendations based on recommended percentages and actual spending
            $recommendations = [];
            $adjustments_needed = [];
            
            foreach ($this->expense_categories as $category_key => $category_name) {
                $recommended_amount = ($this->recommended_budget_percentages[$category_key] / 100) * $income;
                $actual_amount = $spending_patterns[$category_name] ?? 0;
                
                $recommendations[$category_name] = [
                    'recommended_amount' => $recommended_amount,
                    'actual_amount' => $actual_amount,
                    'difference' => $recommended_amount - $actual_amount
                ];
                
                // If actual spending is more than 10% above recommendation, mark for adjustment
                if ($actual_amount > ($recommended_amount * 1.1) && $actual_amount > 0) {
                    $adjustments_needed[$category_name] = [
                        'current' => $actual_amount,
                        'recommended' => $recommended_amount,
                        'savings_potential' => $actual_amount - $recommended_amount,
                        'percentage_over' => (($actual_amount / $recommended_amount) - 1) * 100
                    ];
                }
            }
            
            // Calculate potential savings
            $potential_monthly_savings = 0;
            foreach ($adjustments_needed as $adjustment) {
                $potential_monthly_savings += $adjustment['savings_potential'];
            }
            
            // Add Kenya-specific recommendations
            $kenya_specific_tips = $this->getKenyaSpecificBudgetTips($adjustments_needed);
            
            return [
                'status' => 'success',
                'income' => $income,
                'total_monthly_spending' => $total_monthly_spending,
                'savings_rate' => $income > 0 ? (($income - $total_monthly_spending) / $income) * 100 : 0,
                'category_recommendations' => $recommendations,
                'adjustments_needed' => $adjustments_needed,
                'potential_monthly_savings' => $potential_monthly_savings,
                'potential_annual_savings' => $potential_monthly_savings * 12,
                'kenya_specific_tips' => $kenya_specific_tips
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get Kenya-specific budget tips based on spending patterns
     * 
     * @param array $adjustments_needed Categories needing adjustment
     * @return array Kenya-specific budget tips
     */
    private function getKenyaSpecificBudgetTips($adjustments_needed) {
        $tips = [];
        
        // Housing tips
        if (isset($adjustments_needed['Housing & Utilities'])) {
            $tips[] = "Consider housing in areas like Ruaka, Kikuyu or Athi River where rent is 30-40% cheaper than Westlands or Kilimani.";
            $tips[] = "Use energy-saving bulbs to reduce Kenya Power bills, which can save up to KES 500 monthly.";
            $tips[] = "Water harvesting during rainy seasons can significantly reduce your water bill in Nairobi.";
        }
        
        // Food tips
        if (isset($adjustments_needed['Food & Groceries'])) {
            $tips[] = "Shop at local markets like Wakulima or Marikiti instead of supermarkets to save up to 40% on fresh produce.";
            $tips[] = "Buy maize flour and other staples in bulk during harvest season when prices are lower.";
            $tips[] = "Consider joining a 'Soko Savings' group where members pool resources to buy groceries in bulk.";
        }
        
        // Transport tips
        if (isset($adjustments_needed['Transportation'])) {
            $tips[] = "Using matatus during off-peak hours can save you KES 50-100 daily on your commute.";
            $tips[] = "Carpooling with colleagues can reduce your fuel costs by up to 60% if you drive to work.";
            $tips[] = "Consider relocating closer to your workplace to reduce transportation costs if rents are comparable.";
        }
        
        // Mobile money tips
        if (isset($adjustments_needed['Mobile Money Fees'])) {
            $tips[] = "Keep money in your M-Pesa account rather than withdrawing frequently to avoid transaction fees.";
            $tips[] = "Use Fuliza only for emergencies as the daily fees accumulate quickly.";
            $tips[] = "Send larger amounts less frequently to reduce M-Pesa transaction fees.";
        }
        
        // General tips for everyone
        $tips[] = "Use the M-Pesa Lock feature to set aside savings and prevent impulsive spending.";
        $tips[] = "Join a SACCO for better savings rates than traditional bank accounts.";
        $tips[] = "Consider Treasury Bills through CBK Mobile Direct as an alternative to bank savings accounts.";
        
        return $tips;
    }
    
    /**
     * Analyze spending trends over time
     * 
     * @param int $months Number of months to analyze
     * @return array Spending trend analysis
     */
    public function analyzeSpendingTrends($months = 6) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    DATE_FORMAT(expense_date, '%Y-%m') as month,
                    category,
                    SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND expense_date >= DATE_SUB(CURRENT_DATE(), INTERVAL ? MONTH)
                GROUP BY DATE_FORMAT(expense_date, '%Y-%m'), category
                ORDER BY DATE_FORMAT(expense_date, '%Y-%m')
            ");
            
            $stmt->bind_param("ii", $this->user_id, $months);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $monthly_trends = [];
            $category_totals = [];
            $all_months = [];
            
            // Collect data from query
            while ($row = $result->fetch_assoc()) {
                if (!in_array($row['month'], $all_months)) {
                    $all_months[] = $row['month'];
                }
                
                if (!isset($monthly_trends[$row['month']])) {
                    $monthly_trends[$row['month']] = [];
                }
                
                $monthly_trends[$row['month']][$row['category']] = $row['total'];
                
                if (!isset($category_totals[$row['category']])) {
                    $category_totals[$row['category']] = 0;
                }
                $category_totals[$row['category']] += $row['total'];
            }
            
            // Sort categories by total spent
            arsort($category_totals);
            
            // Get top 5 spending categories
            $top_categories = array_slice(array_keys($category_totals), 0, 5);
            
            // Calculate month-over-month changes
            $monthly_changes = [];
            
            foreach ($all_months as $i => $month) {
                if ($i === 0) continue; // Skip first month as we need a previous month to compare
                
                $prev_month = $all_months[$i-1];
                $monthly_changes[$month] = [];
                
                foreach ($top_categories as $category) {
                    $current = isset($monthly_trends[$month][$category]) ? $monthly_trends[$month][$category] : 0;
                    $previous = isset($monthly_trends[$prev_month][$category]) ? $monthly_trends[$prev_month][$category] : 0;
                    
                    if ($previous > 0) {
                        $change_percentage = (($current - $previous) / $previous) * 100;
                    } else {
                        $change_percentage = $current > 0 ? 100 : 0;
                    }
                    
                    $monthly_changes[$month][$category] = [
                        'current' => $current,
                        'previous' => $previous,
                        'change' => $current - $previous,
                        'change_percentage' => $change_percentage
                    ];
                }
            }
            
            // Calculate average monthly spending by category
            $average_spending = [];
            foreach ($category_totals as $category => $total) {
                $average_spending[$category] = $total / count($all_months);
            }
            
            // Get overall monthly totals
            $monthly_totals = [];
            foreach ($all_months as $month) {
                $monthly_totals[$month] = array_sum($monthly_trends[$month]);
            }
            
            return [
                'status' => 'success',
                'monthly_trends' => $monthly_trends,
                'category_totals' => $category_totals,
                'top_categories' => $top_categories,
                'monthly_changes' => $monthly_changes,
                'average_spending' => $average_spending,
                'monthly_totals' => $monthly_totals,
                'months_analyzed' => $all_months
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get spending breakdown for a specific time period
     * 
     * @param string $start_date Start date (YYYY-MM-DD)
     * @param string $end_date End date (YYYY-MM-DD)
     * @return array Spending breakdown
     */
    public function getSpendingBreakdown($start_date, $end_date) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    category,
                    SUM(amount) as total,
                    COUNT(*) as transaction_count,
                    AVG(amount) as average_transaction,
                    MAX(amount) as largest_transaction,
                    MIN(expense_date) as first_transaction,
                    MAX(expense_date) as last_transaction
                FROM expenses
                WHERE user_id = ? AND expense_date BETWEEN ? AND ?
                GROUP BY category
                ORDER BY total DESC
            ");
            
            $stmt->bind_param("iss", $this->user_id, $start_date, $end_date);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $category_breakdown = [];
            $total_spending = 0;
            
            while ($row = $result->fetch_assoc()) {
                $category_breakdown[$row['category']] = $row;
                $total_spending += $row['total'];
            }
            
            // Calculate percentages of total
            foreach ($category_breakdown as &$category) {
                $category['percentage'] = ($category['total'] / $total_spending) * 100;
            }
            
            // Get spending breakdown by day of week
            $stmt = $this->db->prepare("
                SELECT 
                    DAYNAME(expense_date) as day_of_week,
                    SUM(amount) as total
                FROM expenses
                WHERE user_id = ? AND expense_date BETWEEN ? AND ?
                GROUP BY DAYNAME(expense_date)
                ORDER BY FIELD(DAYNAME(expense_date), 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
            ");
            
            $stmt->bind_param("iss", $this->user_id, $start_date, $end_date);
            $stmt->execute();
            $day_result = $stmt->get_result();
            
            $day_breakdown = [];
            while ($day = $day_result->fetch_assoc()) {
                $day_breakdown[$day['day_of_week']] = $day['total'];
            }
            
            // Get top transactions
            $stmt = $this->db->prepare("
                SELECT *
                FROM expenses
                WHERE user_id = ? AND expense_date BETWEEN ? AND ?
                ORDER BY amount DESC
                LIMIT 10
            ");
            
            $stmt->bind_param("iss", $this->user_id, $start_date, $end_date);
            $stmt->execute();
            $top_transactions_result = $stmt->get_result();
            
            $top_transactions = [];
            while ($transaction = $top_transactions_result->fetch_assoc()) {
                $top_transactions[] = $transaction;
            }
            
            return [
                'status' => 'success',
                'start_date' => $start_date,
                'end_date' => $end_date,
                'total_spending' => $total_spending,
                'category_breakdown' => $category_breakdown,
                'day_of_week_breakdown' => $day_breakdown,
                'top_transactions' => $top_transactions
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Update a budget's categories or total income
     * 
     * @param int $budget_id Budget ID
     * @param array $budget_data Budget data to update
     * @return array Response with status and message
     */
    public function updateBudget($budget_id, $budget_data) {
        try {
            // Verify the budget belongs to this user
            $stmt = $this->db->prepare("
                SELECT id FROM budgets 
                WHERE id = ? AND user_id = ?
            ");
            
            $stmt->bind_param("ii", $budget_id, $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'status' => 'error',
                    'message' => 'Budget not found or access denied'
                ];
            }
            
            // Start a transaction
            $this->db->begin_transaction();
            
            // Update budget details if provided
            if (isset($budget_data['total_income']) || isset($budget_data['budget_name']) || 
                isset($budget_data['start_date']) || isset($budget_data['end_date'])) {
                
                $update_sql = "UPDATE budgets SET ";
                $update_params = [];
                $param_types = "";
                
                if (isset($budget_data['budget_name'])) {
                    $update_sql .= "budget_name = ?, ";
                    $update_params[] = $budget_data['budget_name'];
                    $param_types .= "s";
                }
                
                if (isset($budget_data['total_income'])) {
                    $update_sql .= "total_income = ?, ";
                    $update_params[] = $budget_data['total_income'];
                    $param_types .= "d";
                }
                
                if (isset($budget_data['start_date'])) {
                    $update_sql .= "start_date = ?, ";
                    $update_params[] = $budget_data['start_date'];
                    $param_types .= "s";
                }
                
                if (isset($budget_data['end_date'])) {
                    $update_sql .= "end_date = ?, ";
                    $update_params[] = $budget_data['end_date'];
                    $param_types .= "s";
                }
                
                if (isset($budget_data['description'])) {
                    $update_sql .= "description = ?, ";
                    $update_params[] = $budget_data['description'];
                    $param_types .= "s";
                }
                
                // Remove trailing comma and space
                $update_sql = rtrim($update_sql, ", ");
                
                $update_sql .= " WHERE id = ?";
                $update_params[] = $budget_id;
                $param_types .= "i";
                
                $stmt = $this->db->prepare($update_sql);
                
                // Dynamically bind parameters
                $bind_params = array($param_types);
                foreach ($update_params as $key => $value) {
                    $bind_params[] = &$update_params[$key];
                }
                
                call_user_func_array(array($stmt, 'bind_param'), $bind_params);
                
                if (!$stmt->execute()) {
                    $this->db->rollback();
                    return [
                        'status' => 'error',
                        'message' => 'Failed to update budget: ' . $this->db->error
                    ];
                }
            }
            
            // Update budget categories if provided
            if (isset($budget_data['categories']) && is_array($budget_data['categories'])) {
                foreach ($budget_data['categories'] as $category => $amount) {
                    // Check if this category already exists
                    $stmt = $this->db->prepare("
                        SELECT id FROM budget_categories 
                        WHERE budget_id = ? AND category = ?
                    ");
                    
                    $stmt->bind_param("is", $budget_id, $category);
                    $stmt->execute();
                    $result = $stmt->get_result();
                    
                    if ($result->num_rows > 0) {
                        // Update existing category
                        $row = $result->fetch_assoc();
                        $category_id = $row['id'];
                        
                        $stmt = $this->db->prepare("
                            UPDATE budget_categories 
                            SET amount = ? 
                            WHERE id = ?
                        ");
                        
                        $stmt->bind_param("di", $amount, $category_id);
                        
                        if (!$stmt->execute()) {
                            $this->db->rollback();
                            return [
                                'status' => 'error',
                                'message' => 'Failed to update budget category: ' . $this->db->error
                            ];
                        }
                    } else {
                        // Insert new category
                        $stmt = $this->db->prepare("
                            INSERT INTO budget_categories (budget_id, category, amount)
                            VALUES (?, ?, ?)
                        ");
                        
                        $stmt->bind_param("isd", $budget_id, $category, $amount);
                        
                        if (!$stmt->execute()) {
                            $this->db->rollback();
                            return [
                                'status' => 'error',
                                'message' => 'Failed to add budget category: ' . $this->db->error
                            ];
                        }
                    }
                }
            }
            
            // Commit the transaction
            $this->db->commit();
            
            return [
                'status' => 'success',
                'message' => 'Budget updated successfully'
            ];
            
        } catch (Exception $e) {
            $this->db->rollback();
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Delete a budget
     * 
     * @param int $budget_id Budget ID
     * @return array Response with status and message
     */
    public function deleteBudget($budget_id) {
        try {
            // Verify the budget belongs to this user
            $stmt = $this->db->prepare("
                SELECT id FROM budgets 
                WHERE id = ? AND user_id = ?
            ");
            
            $stmt->bind_param("ii", $budget_id, $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'status' => 'error',
                    'message' => 'Budget not found or access denied'
                ];
            }
            
            // Start a transaction
            $this->db->begin_transaction();
            
            // Delete budget categories
            $stmt = $this->db->prepare("
                DELETE FROM budget_categories 
                WHERE budget_id = ?
            ");
            
            $stmt->bind_param("i", $budget_id);
            
            if (!$stmt->execute()) {
                $this->db->rollback();
                return [
                    'status' => 'error',
                    'message' => 'Failed to delete budget categories: ' . $this->db->error
                ];
            }
            
            // Delete expenses associated with this budget
            $stmt = $this->db->prepare("
                DELETE FROM expenses 
                WHERE budget_id = ?
            ");
            
            $stmt->bind_param("i", $budget_id);
            
            if (!$stmt->execute()) {
                $this->db->rollback();
                return [
                    'status' => 'error',
                    'message' => 'Failed to delete budget expenses: ' . $this->db->error
                ];
            }
            
            // Delete the budget
            $stmt = $this->db->prepare("
                DELETE FROM budgets 
                WHERE id = ?
            ");
            
            $stmt->bind_param("i", $budget_id);
            
            if (!$stmt->execute()) {
                $this->db->rollback();
                return [
                    'status' => 'error',
                    'message' => 'Failed to delete budget: ' . $this->db->error
                ];
            }
            
            // Commit the transaction
            $this->db->commit();
            
            return [
                'status' => 'success',
                'message' => 'Budget deleted successfully'
            ];
            
        } catch (Exception $e) {
            $this->db->rollback();
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get income sources breakdown
     * 
     * @return array Income sources data
     */
    public function getIncomeSources() {
        try {
            $stmt = $this->db->prepare("
                SELECT * FROM income_sources
                WHERE user_id = ?
                ORDER BY amount DESC
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $income_sources = [];
            $total_income = 0;
            
            while ($source = $result->fetch_assoc()) {
                $income_sources[] = $source;
                $total_income += $source['amount'];
            }
            
            // Calculate percentage of total income
            foreach ($income_sources as &$source) {
                $source['percentage'] = ($source['amount'] / $total_income) * 100;
            }
            
            return [
                'status' => 'success',
                'income_sources' => $income_sources,
                'total_income' => $total_income
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Add a new income source
     * 
     * @param array $income_data Income source data
     * @return array Response with status and message
     */
    public function addIncomeSource($income_data) {
        try {
            // Validate required fields
            if (!isset($income_data['name']) || !isset($income_data['amount'])) {
                return [
                    'status' => 'error',
                    'message' => 'Missing required income source information'
                ];
            }
            
            $stmt = $this->db->prepare("
                INSERT INTO income_sources (user_id, name, amount, frequency, description, source_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ");
            
            $stmt->bind_param(
                "isdsss",
                $this->user_id,
                $income_data['name'],
                $income_data['amount'],
                $income_data['frequency'] ?? 'monthly', // Default to monthly
                $income_data['description'] ?? '',
                $income_data['source_type'] ?? 'salary'  // Default to salary
            );
            
            if (!$stmt->execute()) {
                return [
                    'status' => 'error',
                    'message' => 'Failed to add income source: ' . $this->db->error
                ];
            }
            
            $income_id = $this->db->insert_id;
            
            // Update total income in the user's active budget
            $this->updateActiveBudgetIncome();
            
            return [
                'status' => 'success',
                'message' => 'Income source added successfully',
                'income_id' => $income_id
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Update the total income in the user's active budget
     * based on their income sources
     * 
     * @return bool Success status
     */
    private function updateActiveBudgetIncome() {
        try {
            // Get total income from all sources
            $stmt = $this->db->prepare("
                SELECT SUM(amount) as total_income 
                FROM income_sources
                WHERE user_id = ? AND frequency = 'monthly'
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            $row = $result->fetch_assoc();
            $total_income = $row['total_income'] ?? 0;
            
            // Get active budget
            $stmt = $this->db->prepare("
                SELECT id FROM budgets 
                WHERE user_id = ? AND start_date <= CURRENT_DATE() AND end_date >= CURRENT_DATE()
                ORDER BY created_at DESC LIMIT 1
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $row = $result->fetch_assoc();
                $budget_id = $row['id'];
                
                // Update the budget's total income
                $stmt = $this->db->prepare("
                    UPDATE budgets 
                    SET total_income = ? 
                    WHERE id = ?
                ");
                
                $stmt->bind_param("di", $total_income, $budget_id);
                
                return $stmt->execute();
            }
            
            return true;
            
        } catch (Exception $e) {
            error_log('Error updating active budget income: ' . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Get commonly used payment methods
     * 
     * @return array Payment methods data
     */
    public function getPaymentMethods() {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    payment_method,
                    COUNT(*) as transaction_count,
                    SUM(amount) as total_amount,
                    AVG(amount) as average_amount
                FROM expenses
                WHERE user_id = ?
                GROUP BY payment_method
                ORDER BY transaction_count DESC
            ");
            
            $stmt->bind_param("i", $this->user_id);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $payment_methods = [];
            while ($method = $result->fetch_assoc()) {
                $payment_methods[] = $method;
            }
            
            return [
                'status' => 'success',
                'payment_methods' => $payment_methods
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Export budget and expense data (for backup or sharing)
     * 
     * @param int $budget_id Optional budget ID to export specific budget
     * @return array Export data
     */
    public function exportData($budget_id = null) {
        try {
            $export_data = [
                'export_date' => date('Y-m-d H:i:s'),
                'budgets' => [],
                'expenses' => [],
                'income_sources' => []
            ];
            
            // Get budgets
            $sql = "SELECT * FROM budgets WHERE user_id = ?";
            $params = [$this->user_id];
            $types = "i";
            
            if ($budget_id !== null) {
                $sql .= " AND id = ?";
                $params[] = $budget_id;
                $types .= "i";
            }
            
            $stmt = $this->db->prepare($sql);
            $stmt->bind_param($types, ...$params);
            $stmt->execute();
            $result = $stmt->get_result();
            
            while ($budget = $result->fetch_assoc()) {
                $budget_id = $budget['id'];
                
                // Get budget categories
                $cat_stmt = $this->db->prepare("
                    SELECT * FROM budget_categories 
                    WHERE budget_id = ?
                ");
                
                $cat_stmt->bind_param("i", $budget_id);
                $cat_stmt->execute();
                $cat_result = $cat_stmt->get_result();
                
                $categories = [];
                while ($category = $cat_result->fetch_assoc()) {
                    $categories[] = $category;
                }
                
                $budget['categories'] = $categories;
                $export_data['budgets'][] = $budget;
                
                // Get expenses for this budget
                $exp_stmt = $this->db->prepare("
                    SELECT * FROM expenses 
                    WHERE budget_id = ?
                ");
                
                $exp_stmt->bind_param("i", $budget_id);
                $exp_stmt->execute();
                $exp_result = $exp_stmt->get_result();
                
                while ($expense = $exp_result->fetch_assoc()) {
                    $export_data['expenses'][] = $expense;
                }
            }
            
            // Get income sources
            $inc_stmt = $this->db->prepare("
                SELECT * FROM income_sources 
                WHERE user_id = ?
            ");
            
            $inc_stmt->bind_param("i", $this->user_id);
            $inc_stmt->execute();
            $inc_result = $inc_stmt->get_result();
            
            while ($income = $inc_result->fetch_assoc()) {
                $export_data['income_sources'][] = $income;
            }
            
            return [
                'status' => 'success',
                'export_data' => $export_data
            ];
            
        } catch (Exception $e) {
            return [
                'status' => 'error',
                'message' => 'Exception: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get default expense categories
     * 
     * @return array Default expense categories
     */
    public function getDefaultCategories() {
        return [
            'status' => 'success',
            'expense_categories' => $this->expense_categories,
            'income_categories' => $this->income_categories,
            'recommended_percentages' => $this->recommended_budget_percentages
        ];
    }
}