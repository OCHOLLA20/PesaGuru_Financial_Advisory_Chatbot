<?php
/**
 * FinancialGoal Model
 * 
 * Handles all operations related to user financial goals in the PesaGuru system
 * including creating, reading, updating, and deleting financial goals.
 * 
 * @package PesaGuru
 * @author Sharon Bukaya
 */

class FinancialGoal {
    // Database connection
    private $conn;
    private $table = 'financial_goals';

    // Financial Goal properties
    public $id;
    public $user_id;
    public $title;
    public $category;
    public $target_amount;
    public $current_amount;
    public $target_date;
    public $priority;
    public $status;
    public $description;
    public $created_at;
    public $updated_at;

    /**
     * Constructor with DB connection
     * 
     * @param PDO $db Database connection
     */
    public function __construct($db) {
        $this->conn = $db;
    }

    /**
     * Get all financial goals for a specific user
     * 
     * @param int $userId The user ID to fetch goals for
     * @return PDOStatement
     */
    public function getUserGoals($userId) {
        // Create query
        $query = 'SELECT 
                    fg.id, 
                    fg.user_id, 
                    fg.title, 
                    fg.category, 
                    fg.target_amount,
                    fg.current_amount, 
                    fg.target_date, 
                    fg.priority, 
                    fg.status, 
                    fg.description,
                    fg.created_at,
                    fg.updated_at
                FROM 
                    ' . $this->table . ' fg
                WHERE 
                    fg.user_id = :user_id
                ORDER BY
                    fg.priority ASC, fg.target_date ASC';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Bind parameters
        $stmt->bindParam(':user_id', $userId);

        // Execute query
        $stmt->execute();

        return $stmt;
    }

    /**
     * Get a single financial goal by ID
     * 
     * @return boolean
     */
    public function read_single() {
        // Create query
        $query = 'SELECT 
                    fg.id, 
                    fg.user_id, 
                    fg.title, 
                    fg.category, 
                    fg.target_amount,
                    fg.current_amount, 
                    fg.target_date, 
                    fg.priority, 
                    fg.status, 
                    fg.description,
                    fg.created_at,
                    fg.updated_at
                FROM 
                    ' . $this->table . ' fg
                WHERE 
                    fg.id = :id
                LIMIT 0,1';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Bind ID parameter
        $stmt->bindParam(':id', $this->id);

        // Execute query
        $stmt->execute();

        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        // If no goal found, return false
        if (!$row) {
            return false;
        }

        // Set properties
        $this->id = $row['id'];
        $this->user_id = $row['user_id'];
        $this->title = $row['title'];
        $this->category = $row['category'];
        $this->target_amount = $row['target_amount'];
        $this->current_amount = $row['current_amount'];
        $this->target_date = $row['target_date'];
        $this->priority = $row['priority'];
        $this->status = $row['status'];
        $this->description = $row['description'];
        $this->created_at = $row['created_at'];
        $this->updated_at = $row['updated_at'];

        return true;
    }

    /**
     * Create a new financial goal
     * 
     * @return boolean
     */
    public function create() {
        // Create query
        $query = 'INSERT INTO ' . $this->table . ' 
                    (user_id, title, category, target_amount, current_amount, target_date, priority, status, description, created_at) 
                VALUES 
                    (:user_id, :title, :category, :target_amount, :current_amount, :target_date, :priority, :status, :description, NOW())';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Clean data
        $this->user_id = htmlspecialchars(strip_tags($this->user_id));
        $this->title = htmlspecialchars(strip_tags($this->title));
        $this->category = htmlspecialchars(strip_tags($this->category));
        $this->target_amount = htmlspecialchars(strip_tags($this->target_amount));
        $this->current_amount = htmlspecialchars(strip_tags($this->current_amount));
        $this->target_date = htmlspecialchars(strip_tags($this->target_date));
        $this->priority = htmlspecialchars(strip_tags($this->priority));
        $this->status = htmlspecialchars(strip_tags($this->status));
        $this->description = htmlspecialchars(strip_tags($this->description));

        // Bind parameters
        $stmt->bindParam(':user_id', $this->user_id);
        $stmt->bindParam(':title', $this->title);
        $stmt->bindParam(':category', $this->category);
        $stmt->bindParam(':target_amount', $this->target_amount);
        $stmt->bindParam(':current_amount', $this->current_amount);
        $stmt->bindParam(':target_date', $this->target_date);
        $stmt->bindParam(':priority', $this->priority);
        $stmt->bindParam(':status', $this->status);
        $stmt->bindParam(':description', $this->description);

        // Execute query
        if ($stmt->execute()) {
            $this->id = $this->conn->lastInsertId();
            return true;
        }

        // Print error if something goes wrong
        $errorInfo = $stmt->errorInfo();
        printf("Error: %s.\n", $errorInfo[2]);

        return false;
    }

    /**
     * Update a financial goal
     * 
     * @return boolean
     */
    public function update() {
        // Create query
        $query = 'UPDATE ' . $this->table . ' 
                SET 
                    title = :title, 
                    category = :category, 
                    target_amount = :target_amount, 
                    current_amount = :current_amount, 
                    target_date = :target_date, 
                    priority = :priority, 
                    status = :status, 
                    description = :description, 
                    updated_at = NOW()
                WHERE 
                    id = :id AND user_id = :user_id';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Clean data
        $this->id = htmlspecialchars(strip_tags($this->id));
        $this->user_id = htmlspecialchars(strip_tags($this->user_id));
        $this->title = htmlspecialchars(strip_tags($this->title));
        $this->category = htmlspecialchars(strip_tags($this->category));
        $this->target_amount = htmlspecialchars(strip_tags($this->target_amount));
        $this->current_amount = htmlspecialchars(strip_tags($this->current_amount));
        $this->target_date = htmlspecialchars(strip_tags($this->target_date));
        $this->priority = htmlspecialchars(strip_tags($this->priority));
        $this->status = htmlspecialchars(strip_tags($this->status));
        $this->description = htmlspecialchars(strip_tags($this->description));

        // Bind parameters
        $stmt->bindParam(':id', $this->id);
        $stmt->bindParam(':user_id', $this->user_id);
        $stmt->bindParam(':title', $this->title);
        $stmt->bindParam(':category', $this->category);
        $stmt->bindParam(':target_amount', $this->target_amount);
        $stmt->bindParam(':current_amount', $this->current_amount);
        $stmt->bindParam(':target_date', $this->target_date);
        $stmt->bindParam(':priority', $this->priority);
        $stmt->bindParam(':status', $this->status);
        $stmt->bindParam(':description', $this->description);

        // Execute query
        if ($stmt->execute()) {
            return true;
        }

        // Print error if something goes wrong
        $errorInfo = $stmt->errorInfo();
        printf("Error: %s.\n", $errorInfo[2]);

        return false;
    }

    /**
     * Update current amount for a financial goal
     * 
     * @return boolean
     */
    public function updateAmount() {
        // Create query
        $query = 'UPDATE ' . $this->table . ' 
                SET 
                    current_amount = :current_amount, 
                    updated_at = NOW(),
                    status = CASE WHEN current_amount >= target_amount THEN "completed" ELSE status END
                WHERE 
                    id = :id AND user_id = :user_id';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Clean data
        $this->id = htmlspecialchars(strip_tags($this->id));
        $this->user_id = htmlspecialchars(strip_tags($this->user_id));
        $this->current_amount = htmlspecialchars(strip_tags($this->current_amount));

        // Bind parameters
        $stmt->bindParam(':id', $this->id);
        $stmt->bindParam(':user_id', $this->user_id);
        $stmt->bindParam(':current_amount', $this->current_amount);

        // Execute query
        if ($stmt->execute()) {
            return true;
        }

        // Print error if something goes wrong
        $errorInfo = $stmt->errorInfo();
        printf("Error: %s.\n", $errorInfo[2]);

        return false;
    }

    /**
     * Delete a financial goal
     * 
     * @return boolean
     */
    public function delete() {
        // Create query
        $query = 'DELETE FROM ' . $this->table . ' WHERE id = :id AND user_id = :user_id';

        // Prepare statement
        $stmt = $this->conn->prepare($query);

        // Clean data
        $this->id = htmlspecialchars(strip_tags($this->id));
        $this->user_id = htmlspecialchars(strip_tags($this->user_id));

        // Bind parameters
        $stmt->bindParam(':id', $this->id);
        $stmt->bindParam(':user_id', $this->user_id);

        // Execute query
        if ($stmt->execute()) {
            return true;
        }

        // Print error if something goes wrong
        $errorInfo = $stmt->errorInfo();
        printf("Error: %s.\n", $errorInfo[2]);

        return false;
    }

    /**
     * Get suggested financial goals based on user profile
     * 
     * @param int $userId User ID
     * @return array Suggested goals
     */
    public function getSuggestedGoals($userId) {
        // This method would integrate with the AI chatbot to recommend
        // financial goals based on user profiles and financial situations
        
        // For now, return standard goal templates
        $standardGoals = [
            [
                'title' => 'Emergency Fund',
                'category' => 'savings',
                'description' => 'Build an emergency fund covering 3-6 months of expenses',
                'priority' => 'high'
            ],
            [
                'title' => 'Debt Repayment',
                'category' => 'debt',
                'description' => 'Pay off high-interest debt like credit cards or personal loans',
                'priority' => 'high'
            ],
            [
                'title' => 'Retirement Savings',
                'category' => 'retirement',
                'description' => 'Start contributing to a retirement plan or NSSF',
                'priority' => 'medium'
            ],
            [
                'title' => 'Home Purchase',
                'category' => 'investment',
                'description' => 'Save for a down payment on a home in Kenya',
                'priority' => 'medium'
            ],
            [
                'title' => 'Education Fund',
                'category' => 'education',
                'description' => 'Build a savings fund for your education or children\'s education',
                'priority' => 'medium'
            ]
        ];
        
        return $standardGoals;
    }

    /**
     * Calculate progress percentage for a financial goal
     * 
     * @return float Progress percentage
     */
    public function calculateProgress() {
        if ($this->target_amount <= 0) {
            return 0;
        }
        return min(100, ($this->current_amount / $this->target_amount) * 100);
    }

    /**
     * Check if a goal is on track to meet the target date
     * 
     * @return boolean|null True if on track, false if behind, null if no target date
     */
    public function isOnTrack() {
        if (empty($this->target_date) || $this->target_amount <= 0) {
            return null;
        }

        // Calculate expected progress based on time elapsed
        $today = new DateTime();
        $targetDate = new DateTime($this->target_date);
        $createdDate = new DateTime($this->created_at);
        
        // If target date is in the past
        if ($today > $targetDate) {
            return $this->current_amount >= $this->target_amount;
        }
        
        // Calculate total duration and elapsed duration
        $totalDuration = $targetDate->diff($createdDate)->days;
        $elapsedDuration = $today->diff($createdDate)->days;
        
        if ($totalDuration <= 0) {
            return null;
        }
        
        // Calculate expected progress percentage
        $expectedProgress = ($elapsedDuration / $totalDuration) * $this->target_amount;
        
        // Compare actual progress with expected progress
        return $this->current_amount >= $expectedProgress;
    }

    /**
     * Get remaining amount to reach goal
     * 
     * @return float Remaining amount
     */
    public function getRemainingAmount() {
        return max(0, $this->target_amount - $this->current_amount);
    }

    /**
     * Validate goal data
     * 
     * @return array Validation errors or empty array if valid
     */
    public function validate() {
        $errors = [];
        
        if (empty($this->user_id)) {
            $errors[] = 'User ID is required';
        }
        
        if (empty($this->title)) {
            $errors[] = 'Title is required';
        } elseif (strlen($this->title) < 3) {
            $errors[] = 'Title must be at least 3 characters';
        }
        
        if (empty($this->target_amount)) {
            $errors[] = 'Target amount is required';
        } elseif (!is_numeric($this->target_amount) || $this->target_amount <= 0) {
            $errors[] = 'Target amount must be a positive number';
        }
        
        if (!empty($this->target_date)) {
            $targetDate = DateTime::createFromFormat('Y-m-d', $this->target_date);
            $today = new DateTime();
            
            if (!$targetDate) {
                $errors[] = 'Target date must be in YYYY-MM-DD format';
            } elseif ($targetDate < $today) {
                $errors[] = 'Target date must be in the future';
            }
        }
        
        return $errors;
    }
}