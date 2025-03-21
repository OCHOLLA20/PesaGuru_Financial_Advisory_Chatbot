<?php
/**
 * PesaGuru - Financial Goal Planning Service
 * 
 * This service provides functionalities for creating, managing, and tracking financial goals,
 * as well as providing personalized recommendations to help users achieve their financial objectives.
 * 
 * @author PesaGuru Team
 * @version 1.0
 */

class GoalPlanningService {
    private $db;
    private $userId;
    private $logger;
    
    /**
     * Constructor initializes the service with database connection
     * 
     * @param PDO $db Database connection
     * @param int $userId Current user ID
     * @param Logger $logger Logger instance
     */
    public function __construct($db, $userId = null, $logger = null) {
        $this->db = $db;
        $this->userId = $userId;
        $this->logger = $logger;
    }
    
    /**
     * Set current user ID
     * 
     * @param int $userId User ID
     */
    public function setUserId($userId) {
        $this->userId = $userId;
    }
    
    /**
     * Create a new financial goal for a user
     * 
     * @param array $goalData Goal details (name, target_amount, current_amount, deadline, goal_type, priority)
     * @return array|bool Created goal or false on failure
     */
    public function createGoal($goalData) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to create a goal");
            }
            
            // Validate required fields
            $requiredFields = ['name', 'target_amount', 'deadline', 'goal_type'];
            foreach ($requiredFields as $field) {
                if (!isset($goalData[$field]) || empty($goalData[$field])) {
                    throw new Exception("Missing required field: {$field}");
                }
            }
            
            // Set default values if not provided
            $goalData['current_amount'] = isset($goalData['current_amount']) ? $goalData['current_amount'] : 0;
            $goalData['priority'] = isset($goalData['priority']) ? $goalData['priority'] : 'medium';
            $goalData['created_at'] = date('Y-m-d H:i:s');
            
            // Calculate goal metrics
            $metrics = $this->calculateGoalMetrics($goalData);
            
            // Insert goal into database
            $sql = "INSERT INTO financial_goals (
                    user_id, name, target_amount, current_amount, 
                    deadline, monthly_contribution, goal_type, 
                    priority, progress_percentage, created_at, status
                ) VALUES (
                    :user_id, :name, :target_amount, :current_amount, 
                    :deadline, :monthly_contribution, :goal_type, 
                    :priority, :progress_percentage, :created_at, :status
                )";
            
            $stmt = $this->db->prepare($sql);
            $stmt->bindParam(':user_id', $this->userId);
            $stmt->bindParam(':name', $goalData['name']);
            $stmt->bindParam(':target_amount', $goalData['target_amount']);
            $stmt->bindParam(':current_amount', $goalData['current_amount']);
            $stmt->bindParam(':deadline', $goalData['deadline']);
            $stmt->bindParam(':monthly_contribution', $metrics['monthly_contribution']);
            $stmt->bindParam(':goal_type', $goalData['goal_type']);
            $stmt->bindParam(':priority', $goalData['priority']);
            $stmt->bindParam(':progress_percentage', $metrics['progress_percentage']);
            $stmt->bindParam(':created_at', $goalData['created_at']);
            $stmt->bindParam(':status', $metrics['status']);
            
            if ($stmt->execute()) {
                $goalId = $this->db->lastInsertId();
                
                // Log goal creation
                if ($this->logger) {
                    $this->logger->info("Financial goal created", [
                        'goal_id' => $goalId,
                        'user_id' => $this->userId,
                        'goal_type' => $goalData['goal_type']
                    ]);
                }
                
                // Return the created goal with ID
                return $this->getGoalById($goalId);
            }
            
            return false;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error creating financial goal: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Update an existing financial goal
     * 
     * @param int $goalId Goal ID
     * @param array $updatedData Updated goal details
     * @return array|bool Updated goal or false on failure
     */
    public function updateGoal($goalId, $updatedData) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to update a goal");
            }
            
            // Verify goal exists and belongs to current user
            $existingGoal = $this->getGoalById($goalId);
            if (!$existingGoal) {
                throw new Exception("Goal not found or doesn't belong to current user");
            }
            
            // Prepare update data
            $allowedFields = [
                'name', 'target_amount', 'current_amount', 'deadline', 
                'goal_type', 'priority', 'status'
            ];
            
            $updateData = [];
            $params = [':goal_id' => $goalId, ':user_id' => $this->userId];
            
            foreach ($allowedFields as $field) {
                if (isset($updatedData[$field])) {
                    $updateData[] = "{$field} = :{$field}";
                    $params[":{$field}"] = $updatedData[$field];
                }
            }
            
            if (empty($updateData)) {
                throw new Exception("No valid fields to update");
            }
            
            // Recalculate metrics if financial values changed
            $recalculateMetrics = false;
            $metricsFields = ['target_amount', 'current_amount', 'deadline'];
            foreach ($metricsFields as $field) {
                if (isset($updatedData[$field])) {
                    $recalculateMetrics = true;
                    break;
                }
            }
            
            if ($recalculateMetrics) {
                $goalData = array_merge((array)$existingGoal, $updatedData);
                $metrics = $this->calculateGoalMetrics($goalData);
                
                $updateData[] = "monthly_contribution = :monthly_contribution";
                $params[':monthly_contribution'] = $metrics['monthly_contribution'];
                
                $updateData[] = "progress_percentage = :progress_percentage";
                $params[':progress_percentage'] = $metrics['progress_percentage'];
                
                if (!isset($updatedData['status'])) {
                    $updateData[] = "status = :status";
                    $params[':status'] = $metrics['status'];
                }
            }
            
            // Update the goal
            $sql = "UPDATE financial_goals SET " . implode(', ', $updateData) . 
                   " WHERE id = :goal_id AND user_id = :user_id";
            
            $stmt = $this->db->prepare($sql);
            foreach ($params as $key => $value) {
                $stmt->bindValue($key, $value);
            }
            
            if ($stmt->execute()) {
                // Log goal update
                if ($this->logger) {
                    $this->logger->info("Financial goal updated", [
                        'goal_id' => $goalId,
                        'user_id' => $this->userId
                    ]);
                }
                
                // Return the updated goal
                return $this->getGoalById($goalId);
            }
            
            return false;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error updating financial goal: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Delete a financial goal
     * 
     * @param int $goalId Goal ID
     * @return bool Success status
     */
    public function deleteGoal($goalId) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to delete a goal");
            }
            
            $sql = "DELETE FROM financial_goals WHERE id = :goal_id AND user_id = :user_id";
            $stmt = $this->db->prepare($sql);
            $stmt->bindParam(':goal_id', $goalId);
            $stmt->bindParam(':user_id', $this->userId);
            
            $result = $stmt->execute();
            
            // Log goal deletion
            if ($result && $this->logger) {
                $this->logger->info("Financial goal deleted", [
                    'goal_id' => $goalId,
                    'user_id' => $this->userId
                ]);
            }
            
            return $result;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error deleting financial goal: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Get a specific goal by ID
     * 
     * @param int $goalId Goal ID
     * @return object|bool Goal data or false if not found
     */
    public function getGoalById($goalId) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to get a goal");
            }
            
            $sql = "SELECT * FROM financial_goals WHERE id = :goal_id AND user_id = :user_id";
            $stmt = $this->db->prepare($sql);
            $stmt->bindParam(':goal_id', $goalId);
            $stmt->bindParam(':user_id', $this->userId);
            $stmt->execute();
            
            return $stmt->fetch(PDO::FETCH_OBJ);
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error retrieving financial goal: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Get all financial goals for a user
     * 
     * @param string $status Filter by status (optional)
     * @param string $goalType Filter by goal type (optional)
     * @return array|bool List of goals or false on failure
     */
    public function getUserGoals($status = null, $goalType = null) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to get user goals");
            }
            
            $sql = "SELECT * FROM financial_goals WHERE user_id = :user_id";
            $params = [':user_id' => $this->userId];
            
            // Add filters if provided
            if ($status) {
                $sql .= " AND status = :status";
                $params[':status'] = $status;
            }
            
            if ($goalType) {
                $sql .= " AND goal_type = :goal_type";
                $params[':goal_type'] = $goalType;
            }
            
            $sql .= " ORDER BY priority ASC, deadline ASC";
            
            $stmt = $this->db->prepare($sql);
            foreach ($params as $key => $value) {
                $stmt->bindValue($key, $value);
            }
            
            $stmt->execute();
            
            return $stmt->fetchAll(PDO::FETCH_OBJ);
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error retrieving user goals: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Update goal progress with a new contribution
     * 
     * @param int $goalId Goal ID
     * @param float $amount Contribution amount
     * @return array|bool Updated goal or false on failure
     */
    public function addContribution($goalId, $amount) {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to add a contribution");
            }
            
            // Get current goal data
            $goal = $this->getGoalById($goalId);
            if (!$goal) {
                throw new Exception("Goal not found or doesn't belong to current user");
            }
            
            // Calculate new current amount
            $newAmount = $goal->current_amount + $amount;
            
            // Update the goal with new amount
            return $this->updateGoal($goalId, ['current_amount' => $newAmount]);
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error adding contribution to goal: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Calculate metrics for a financial goal (monthly contribution, progress, etc.)
     * 
     * @param array $goalData Goal data
     * @return array Calculated metrics
     */
    private function calculateGoalMetrics($goalData) {
        $metrics = [];
        
        // Calculate progress percentage
        $targetAmount = floatval($goalData['target_amount']);
        $currentAmount = floatval($goalData['current_amount']);
        
        if ($targetAmount > 0) {
            $metrics['progress_percentage'] = min(100, ($currentAmount / $targetAmount) * 100);
        } else {
            $metrics['progress_percentage'] = 0;
        }
        
        // Determine goal status
        if ($metrics['progress_percentage'] >= 100) {
            $metrics['status'] = 'completed';
        } else {
            $metrics['status'] = 'in_progress';
        }
        
        // Calculate monthly contribution needed
        $deadline = new DateTime($goalData['deadline']);
        $today = new DateTime();
        
        if ($deadline > $today) {
            $monthsRemaining = $today->diff($deadline)->m + ($today->diff($deadline)->y * 12);
            if ($monthsRemaining > 0) {
                $amountNeeded = $targetAmount - $currentAmount;
                $metrics['monthly_contribution'] = $amountNeeded / $monthsRemaining;
            } else {
                // Less than a month remaining, full amount needed
                $metrics['monthly_contribution'] = $targetAmount - $currentAmount;
            }
        } else {
            // Deadline has passed
            $metrics['monthly_contribution'] = $targetAmount - $currentAmount;
            $metrics['status'] = 'overdue';
        }
        
        // Ensure monthly contribution is not negative
        $metrics['monthly_contribution'] = max(0, $metrics['monthly_contribution']);
        
        return $metrics;
    }
    
    /**
     * Get personalized goal recommendations based on user profile
     * 
     * @param array $userProfile User profile data
     * @return array List of recommended goals
     */
    public function getGoalRecommendations($userProfile) {
        try {
            $recommendations = [];
            
            // Age-based recommendations
            $age = isset($userProfile['age']) ? intval($userProfile['age']) : 30;
            $income = isset($userProfile['monthly_income']) ? floatval($userProfile['monthly_income']) : 0;
            $hasDebt = isset($userProfile['has_debt']) ? $userProfile['has_debt'] : false;
            $hasEmergencyFund = isset($userProfile['has_emergency_fund']) ? $userProfile['has_emergency_fund'] : false;
            
            // Priority 1: Emergency Fund (if they don't have one)
            if (!$hasEmergencyFund) {
                $emergencyFundTarget = $income * 6; // 6 months of income
                $recommendations[] = [
                    'goal_type' => 'emergency_fund',
                    'name' => 'Emergency Fund',
                    'description' => 'Build an emergency fund covering 6 months of expenses for financial security.',
                    'target_amount' => $emergencyFundTarget,
                    'priority' => 'high',
                    'suggested_timeline' => '12-24 months',
                    'monthly_contribution' => $emergencyFundTarget / 18 // Over 18 months
                ];
            }
            
            // Priority 2: Debt Repayment (if they have debt)
            if ($hasDebt) {
                $recommendations[] = [
                    'goal_type' => 'debt_repayment',
                    'name' => 'Debt Freedom',
                    'description' => 'Pay off all high-interest debt to improve your financial health.',
                    'priority' => 'high',
                    'suggested_timeline' => '12-36 months',
                    'strategy' => 'Focus on high-interest debt first while maintaining minimum payments on others.'
                ];
            }
            
            // Age-based recommendations
            if ($age < 35) {
                // Young adults (18-35)
                $recommendations[] = [
                    'goal_type' => 'education',
                    'name' => 'Skills Development',
                    'description' => 'Invest in education or skills to increase your earning potential.',
                    'priority' => 'medium',
                    'suggested_timeline' => '12-24 months'
                ];
                
                $recommendations[] = [
                    'goal_type' => 'investment',
                    'name' => 'Start Investing',
                    'description' => 'Begin a long-term investment portfolio focusing on growth.',
                    'priority' => 'medium',
                    'suggested_timeline' => 'Ongoing',
                    'strategy' => 'Consider index funds, stocks, or Unit Trusts from trusted Kenyan investment firms.'
                ];
            } elseif ($age >= 35 && $age < 50) {
                // Mid-career (35-50)
                $recommendations[] = [
                    'goal_type' => 'retirement',
                    'name' => 'Retirement Planning',
                    'description' => 'Accelerate retirement savings to ensure comfortable retirement.',
                    'priority' => 'high',
                    'suggested_timeline' => 'Ongoing',
                    'strategy' => 'Maximize contributions to pension plans and diversify investments.'
                ];
                
                $recommendations[] = [
                    'goal_type' => 'education',
                    'name' => "Children's Education Fund",
                    'description' => 'Save for your children\'s future education expenses.',
                    'priority' => 'medium',
                    'suggested_timeline' => '5-15 years'
                ];
            } else {
                // Pre-retirement (50+)
                $recommendations[] = [
                    'goal_type' => 'retirement',
                    'name' => 'Retirement Readiness',
                    'description' => 'Ensure you have adequate savings for retirement within 5-15 years.',
                    'priority' => 'high',
                    'suggested_timeline' => '5-15 years',
                    'strategy' => 'Shift to more conservative investments to preserve capital.'
                ];
                
                $recommendations[] = [
                    'goal_type' => 'healthcare',
                    'name' => 'Healthcare Fund',
                    'description' => 'Set aside funds for potential healthcare costs in retirement.',
                    'priority' => 'high',
                    'suggested_timeline' => 'Ongoing'
                ];
            }
            
            // Universal recommendations
            $recommendations[] = [
                'goal_type' => 'investment',
                'name' => 'Passive Income Sources',
                'description' => 'Develop passive income streams through dividends, rental property, or business.',
                'priority' => 'medium',
                'suggested_timeline' => '3-10 years',
                'strategy' => 'Research Kenyan investment opportunities like NSE dividend stocks, rental properties, or SME startups.'
            ];
            
            // Add Kenya-specific recommendations
            $recommendations[] = [
                'goal_type' => 'investment',
                'name' => 'NSE Investment Portfolio',
                'description' => 'Build a diversified portfolio of Kenyan stocks for long-term growth.',
                'priority' => 'medium',
                'suggested_timeline' => 'Ongoing',
                'strategy' => 'Focus on blue-chip companies like Safaricom, KCB, Equity Bank, and EABL.'
            ];
            
            $recommendations[] = [
                'goal_type' => 'real_estate',
                'name' => 'Property Investment',
                'description' => 'Save for investment in Kenyan real estate for appreciation and rental income.',
                'priority' => 'medium',
                'suggested_timeline' => '5-10 years',
                'strategy' => 'Consider emerging areas with growth potential and good infrastructure development.'
            ];
            
            return $recommendations;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error generating goal recommendations: " . $e->getMessage());
            }
            return [];
        }
    }
    
    /**
     * Generate a financial goal tracker report
     * 
     * @return array Report data
     */
    public function generateGoalReport() {
        try {
            if (!$this->userId) {
                throw new Exception("User ID is required to generate goal report");
            }
            
            // Get all user goals
            $goals = $this->getUserGoals();
            
            if (!$goals) {
                return [
                    'total_goals' => 0,
                    'goals_by_status' => [],
                    'goals_by_type' => [],
                    'upcoming_deadlines' => [],
                    'overall_progress' => 0
                ];
            }
            
            // Initialize report data
            $report = [
                'total_goals' => count($goals),
                'goals_by_status' => [
                    'completed' => 0,
                    'in_progress' => 0,
                    'overdue' => 0
                ],
                'goals_by_type' => [],
                'upcoming_deadlines' => [],
                'overall_progress' => 0
            ];
            
            $totalTargetAmount = 0;
            $totalCurrentAmount = 0;
            
            // Process each goal
            foreach ($goals as $goal) {
                // Count by status
                if (isset($report['goals_by_status'][$goal->status])) {
                    $report['goals_by_status'][$goal->status]++;
                } else {
                    $report['goals_by_status'][$goal->status] = 1;
                }
                
                // Count by type
                if (isset($report['goals_by_type'][$goal->goal_type])) {
                    $report['goals_by_type'][$goal->goal_type]++;
                } else {
                    $report['goals_by_type'][$goal->goal_type] = 1;
                }
                
                // Check for upcoming deadlines (within 30 days)
                $deadline = new DateTime($goal->deadline);
                $today = new DateTime();
                $daysUntilDeadline = $today->diff($deadline)->days;
                
                if ($goal->status != 'completed' && $deadline > $today && $daysUntilDeadline <= 30) {
                    $report['upcoming_deadlines'][] = [
                        'goal_id' => $goal->id,
                        'name' => $goal->name,
                        'deadline' => $goal->deadline,
                        'days_remaining' => $daysUntilDeadline,
                        'progress_percentage' => $goal->progress_percentage
                    ];
                }
                
                // Sum up target and current amounts for overall progress
                $totalTargetAmount += $goal->target_amount;
                $totalCurrentAmount += $goal->current_amount;
            }
            
            // Calculate overall progress percentage
            if ($totalTargetAmount > 0) {
                $report['overall_progress'] = min(100, ($totalCurrentAmount / $totalTargetAmount) * 100);
            }
            
            // Add financial wellness score
            $report['financial_wellness_score'] = $this->calculateFinancialWellnessScore($goals);
            
            return $report;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error generating goal report: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Calculate a financial wellness score based on goals and progress
     * 
     * @param array $goals User's financial goals
     * @return int Score from 0-100
     */
    private function calculateFinancialWellnessScore($goals) {
        // Default score
        $score = 50;
        
        // No goals is neutral
        if (empty($goals)) {
            return $score;
        }
        
        // Points for having goals of different types
        $goalTypes = [];
        foreach ($goals as $goal) {
            $goalTypes[$goal->goal_type] = true;
        }
        
        // Critical financial health goals
        $criticalGoalTypes = ['emergency_fund', 'debt_repayment', 'retirement'];
        $hasCriticalGoals = false;
        
        foreach ($criticalGoalTypes as $type) {
            if (isset($goalTypes[$type])) {
                $hasCriticalGoals = true;
                $score += 5; // Points for each critical goal type
            }
        }
        
        // If no critical financial health goals, reduce score
        if (!$hasCriticalGoals) {
            $score -= 15;
        }
        
        // Points for diversity of goals (up to 15 points)
        $score += min(15, count($goalTypes) * 3);
        
        // Points for progress on goals
        $totalProgress = 0;
        $completedGoals = 0;
        
        foreach ($goals as $goal) {
            $totalProgress += $goal->progress_percentage;
            if ($goal->status == 'completed') {
                $completedGoals++;
            } elseif ($goal->status == 'overdue') {
                $score -= 5; // Penalty for each overdue goal
            }
        }
        
        // Average progress bonus (up to 10 points)
        if (count($goals) > 0) {
            $avgProgress = $totalProgress / count($goals);
            $score += min(10, $avgProgress / 10);
        }
        
        // Completed goals bonus
        $score += min(15, $completedGoals * 5);
        
        // Ensure score is between 0-100
        return max(0, min(100, $score));
    }
    
    /**
     * Generate financial goal forecast based on current progress
     * 
     * @param int $goalId Goal ID
     * @param float $monthlyContribution Optional custom monthly contribution
     * @return array Forecast data
     */
    public function generateGoalForecast($goalId, $monthlyContribution = null) {
        try {
            // Get current goal data
            $goal = $this->getGoalById($goalId);
            if (!$goal) {
                throw new Exception("Goal not found or doesn't belong to current user");
            }
            
            // Use provided monthly contribution or default to current goal setting
            $monthlyAmount = $monthlyContribution ?? $goal->monthly_contribution;
            
            // Calculate months to completion
            $amountNeeded = $goal->target_amount - $goal->current_amount;
            
            if ($amountNeeded <= 0) {
                return [
                    'goal_id' => $goal->id,
                    'name' => $goal->name,
                    'status' => 'completed',
                    'completion_date' => 'Now',
                    'months_to_completion' => 0,
                    'progress_percentage' => 100
                ];
            }
            
            if ($monthlyAmount <= 0) {
                return [
                    'goal_id' => $goal->id,
                    'name' => $goal->name,
                    'status' => 'stalled',
                    'completion_date' => 'Undetermined',
                    'months_to_completion' => null,
                    'progress_percentage' => $goal->progress_percentage,
                    'message' => 'Increase monthly contribution to make progress'
                ];
            }
            
            // Calculate months to completion
            $monthsToCompletion = ceil($amountNeeded / $monthlyAmount);
            
            // Calculate expected completion date
            $completionDate = new DateTime();
            $completionDate->modify("+{$monthsToCompletion} months");
            
            // Determine if goal will be met by deadline
            $deadline = new DateTime($goal->deadline);
            $willMeetDeadline = $completionDate <= $deadline;
            
            // Generate monthly forecast
            $forecast = [
                'goal_id' => $goal->id,
                'name' => $goal->name,
                'current_amount' => $goal->current_amount,
                'target_amount' => $goal->target_amount,
                'monthly_contribution' => $monthlyAmount,
                'months_to_completion' => $monthsToCompletion,
                'expected_completion_date' => $completionDate->format('Y-m-d'),
                'deadline' => $goal->deadline,
                'will_meet_deadline' => $willMeetDeadline,
                'progress_percentage' => $goal->progress_percentage,
                'monthly_projection' => []
            ];
            
            // Generate monthly projections
            $projectedAmount = $goal->current_amount;
            $currentDate = new DateTime();
            
            for ($i = 1; $i <= min(36, $monthsToCompletion); $i++) {
                $projectedAmount += $monthlyAmount;
                $projectionDate = clone $currentDate;
                $projectionDate->modify("+{$i} months");
                
                $forecast['monthly_projection'][] = [
                    'month' => $i,
                    'date' => $projectionDate->format('Y-m-d'),
                    'amount' => min($projectedAmount, $goal->target_amount),
                    'progress_percentage' => min(100, ($projectedAmount / $goal->target_amount) * 100)
                ];
                
                // Stop once goal is reached
                if ($projectedAmount >= $goal->target_amount) {
                    break;
                }
            }
            
            // Add advice based on forecast
            if (!$willMeetDeadline) {
                $shortfall = $goal->target_amount - $projectedAmount;
                $monthsToDeadline = $currentDate->diff($deadline)->m + ($currentDate->diff($deadline)->y * 12);
                
                if ($monthsToDeadline > 0) {
                    $requiredMonthlyContribution = $amountNeeded / $monthsToDeadline;
                    
                    $forecast['advice'] = [
                        'message' => 'At your current contribution rate, you will not meet your goal by the deadline.',
                        'required_monthly_contribution' => $requiredMonthlyContribution,
                        'increase_needed' => $requiredMonthlyContribution - $monthlyAmount,
                        'alternative_options' => [
                            'Extend deadline by ' . ($monthsToCompletion - $monthsToDeadline) . ' months',
                            'Reduce target amount by ' . $shortfall,
                            'Make a one-time contribution of ' . $shortfall
                        ]
                    ];
                } else {
                    $forecast['advice'] = [
                        'message' => 'Your deadline has passed or is too soon to meet your goal.',
                        'options' => [
                            'Set a new realistic deadline',
                            'Adjust your target amount',
                            'Increase your contributions significantly'
                        ]
                    ];
                }
            } else {
                $forecast['advice'] = [
                    'message' => 'You are on track to meet your goal by the deadline.',
                    'options' => [
                        'Continue with your current contributions',
                        'Consider increasing contributions to reach your goal sooner'
                    ]
                ];
            }
            
            return $forecast;
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error generating goal forecast: " . $e->getMessage());
            }
            throw $e;
        }
    }
    
    /**
     * Get investment options suitable for a specific goal
     * 
     * @param int $goalId Goal ID
     * @return array List of investment options
     */
    public function getGoalInvestmentOptions($goalId) {
        try {
            // Get goal data
            $goal = $this->getGoalById($goalId);
            if (!$goal) {
                throw new Exception("Goal not found or doesn't belong to current user");
            }
            
            // Calculate time horizon in years
            $deadline = new DateTime($goal->deadline);
            $today = new DateTime();
            $timeHorizonYears = max(0, ($today->diff($deadline)->days / 365));
            
            // Investment options based on goal type and time horizon
            $options = [];
            
            // Short-term options (< 2 years)
            if ($timeHorizonYears < 2) {
                $options[] = [
                    'name' => 'Money Market Fund',
                    'description' => 'Low-risk fund investing in short-term interest-bearing securities.',
                    'risk_level' => 'Low',
                    'expected_return' => '7-9%',
                    'min_investment' => 'KES 1,000',
                    'liquidity' => 'High - funds accessible within 2-3 business days',
                    'providers' => [
                        'CIC Money Market Fund',
                        'Sanlam Money Market Fund',
                        'NCBA Money Market Fund'
                    ]
                ];
                
                $options[] = [
                    'name' => 'Treasury Bills',
                    'description' => 'Short-term government securities with fixed interest rates.',
                    'risk_level' => 'Very Low',
                    'expected_return' => '6-9%',
                    'min_investment' => 'KES 100,000',
                    'liquidity' => 'Medium - Maturity ranges from 91 to 364 days',
                    'providers' => ['Central Bank of Kenya']
                ];
                
                $options[] = [
                    'name' => 'Fixed Deposit Account',
                    'description' => 'Bank account with fixed interest rate for a specified period.',
                    'risk_level' => 'Very Low',
                    'expected_return' => '5-7%',
                    'min_investment' => 'KES 10,000 - 100,000 (varies by bank)',
                    'liquidity' => 'Low - Funds locked for the term period',
                    'providers' => [
                        'KCB Bank',
                        'Equity Bank',
                        'Co-operative Bank',
                        'ABSA Bank Kenya'
                    ]
                ];
            }
            // Medium-term options (2-5 years)
            elseif ($timeHorizonYears >= 2 && $timeHorizonYears < 5) {
                $options[] = [
                    'name' => 'Treasury Bonds',
                    'description' => 'Medium to long-term government securities.',
                    'risk_level' => 'Low',
                    'expected_return' => '10-13%',
                    'min_investment' => 'KES 50,000',
                    'liquidity' => 'Medium - Can be sold in secondary market',
                    'providers' => ['Central Bank of Kenya']
                ];
                
                $options[] = [
                    'name' => 'Balanced Funds',
                    'description' => 'Mutual funds investing in a mix of stocks and bonds.',
                    'risk_level' => 'Medium',
                    'expected_return' => '9-12%',
                    'min_investment' => 'KES 5,000',
                    'liquidity' => 'Medium-High - Redeemable within 3-5 business days',
                    'providers' => [
                        'Old Mutual Balanced Fund',
                        'Britam Balanced Fund',
                        'CIC Balanced Fund'
                    ]
                ];
                
                $options[] = [
                    'name' => 'Corporate Bonds',
                    'description' => 'Debt securities issued by corporations.',
                    'risk_level' => 'Medium',
                    'expected_return' => '12-15%',
                    'min_investment' => 'KES 100,000',
                    'liquidity' => 'Medium - Can be traded on NSE',
                    'providers' => [
                        'Safaricom',
                        'East African Breweries',
                        'Family Bank'
                    ]
                ];
            }
            // Long-term options (>= 5 years)
            else {
                $options[] = [
                    'name' => 'Equity Funds',
                    'description' => 'Mutual funds investing primarily in stocks.',
                    'risk_level' => 'High',
                    'expected_return' => '12-18%',
                    'min_investment' => 'KES 5,000',
                    'liquidity' => 'Medium-High - Redeemable within 3-5 business days',
                    'providers' => [
                        'Cytonn Money Market Fund',
                        'ICEA Lion Growth Fund',
                        'Britam Equity Fund'
                    ]
                ];
                
                $options[] = [
                    'name' => 'NSE Stocks',
                    'description' => 'Direct investment in shares listed on Nairobi Securities Exchange.',
                    'risk_level' => 'High',
                    'expected_return' => '15-25%',
                    'min_investment' => 'Varies by stock',
                    'liquidity' => 'Medium-High - Can be sold during trading hours',
                    'recommended_stocks' => [
                        'Safaricom (SCOM)',
                        'Equity Group (EQTY)',
                        'KCB Group (KCB)',
                        'East African Breweries (EABL)'
                    ]
                ];
                
                if ($timeHorizonYears >= 10) {
                    $options[] = [
                        'name' => 'Real Estate Investment',
                        'description' => 'Investment in physical property or REITs.',
                        'risk_level' => 'Medium',
                        'expected_return' => '10-15%',
                        'min_investment' => 'KES 1,000,000+ for physical property, KES 5,000 for REITs',
                        'liquidity' => 'Low for physical property, Medium for REITs',
                        'options' => [
                            'STANLIB Fahari I-REIT',
                            'Property in emerging areas like Kitengela, Juja, or Kangundo Road',
                            'Real estate crowdfunding platforms'
                        ]
                    ];
                }
            }
            
            // Customize options based on goal type
            if ($goal->goal_type == 'retirement') {
                $options[] = [
                    'name' => 'Pension Schemes',
                    'description' => 'Long-term retirement savings with tax benefits.',
                    'risk_level' => 'Low to Medium',
                    'expected_return' => '8-12%',
                    'tax_benefits' => 'Contributions are tax-deductible up to KES 20,000 per month',
                    'providers' => [
                        'NSSF (National Social Security Fund)',
                        'Personal Pension Plans (Various insurance companies)',
                        'Occupational Retirement Benefit Schemes'
                    ]
                ];
            } elseif ($goal->goal_type == 'education') {
                $options[] = [
                    'name' => 'Education Savings Plans',
                    'description' => 'Specialized savings plans for education expenses.',
                    'risk_level' => 'Low to Medium',
                    'expected_return' => '8-10%',
                    'features' => 'Structured savings with insurance benefits',
                    'providers' => [
                        'Britam Education Plan',
                        'CIC Education Plan',
                        'ICEA Lion Education Plan'
                    ]
                ];
            }
            
            return [
                'goal_id' => $goalId,
                'goal_name' => $goal->name,
                'time_horizon_years' => $timeHorizonYears,
                'investment_options' => $options
            ];
        } catch (Exception $e) {
            if ($this->logger) {
                $this->logger->error("Error getting goal investment options: " . $e->getMessage());
            }
            throw $e;
        }
    }
}