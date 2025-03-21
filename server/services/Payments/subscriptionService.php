<?php
/**
 * Subscription Service for PesaGuru
 * Handles user subscriptions, plan management, and status checks
 */

// Database connection class
class Database {
    private $host = "localhost";
    private $db_name = "pesaguru_db";
    private $username = "root";
    private $password = "";
    private $conn;
    
    // Database connection
    public function connect() {
        $this->conn = null;
        
        try {
            $this->conn = new PDO(
                "mysql:host=" . $this->host . ";dbname=" . $this->db_name,
                $this->username,
                $this->password
            );
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $e) {
            echo "Connection Error: " . $e->getMessage();
        }
        
        return $this->conn;
    }
}

class SubscriptionService {
    private $conn;
    
    public function __construct() {
        $database = new Database();
        $this->conn = $database->connect();
    }
    
    /**
     * Add a new subscription for a user
     * 
     * @param int $userId - ID of the user
     * @param string $plan - Subscription plan name
     * @param float $amount - Subscription amount
     * @param int $duration - Duration in months
     * @return array - Status and message
     */
    public function addSubscription($userId, $plan, $amount, $duration) {
        $expiryDate = date('Y-m-d H:i:s', strtotime("+$duration months"));
        
        $query = "INSERT INTO subscriptions (user_id, plan, amount, start_date, expiry_date, status)
                  VALUES (:user_id, :plan, :amount, NOW(), :expiry_date, 'active')";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        $stmt->bindParam(':plan', $plan);
        $stmt->bindParam(':amount', $amount);
        $stmt->bindParam(':expiry_date', $expiryDate);
        
        try {
            if ($stmt->execute()) {
                return ["status" => "success", "message" => "Subscription activated successfully"];
            } else {
                return ["status" => "error", "message" => "Subscription activation failed"];
            }
        } catch (PDOException $e) {
            return ["status" => "error", "message" => "Database error: " . $e->getMessage()];
        }
    }
    
    /**
     * Get user subscription details
     * 
     * @param int $userId - ID of the user
     * @return array - Subscription details or error message
     */
    public function getSubscription($userId) {
        $query = "SELECT * FROM subscriptions WHERE user_id = :user_id ORDER BY expiry_date DESC LIMIT 1";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        
        try {
            $stmt->execute();
            
            if ($stmt->rowCount() > 0) {
                return $stmt->fetch(PDO::FETCH_ASSOC);
            } else {
                return ["status" => "error", "message" => "No active subscription found"];
            }
        } catch (PDOException $e) {
            return ["status" => "error", "message" => "Database error: " . $e->getMessage()];
        }
    }
    
    /**
     * Cancel an active subscription
     * 
     * @param int $userId - ID of the user
     * @return array - Status and message
     */
    public function cancelSubscription($userId) {
        $query = "UPDATE subscriptions SET status = 'cancelled' WHERE user_id = :user_id AND status = 'active'";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        
        try {
            if ($stmt->execute()) {
                return ["status" => "success", "message" => "Subscription cancelled"];
            } else {
                return ["status" => "error", "message" => "Failed to cancel subscription"];
            }
        } catch (PDOException $e) {
            return ["status" => "error", "message" => "Database error: " . $e->getMessage()];
        }
    }
    
    /**
     * Check if user has an active subscription
     * 
     * @param int $userId - ID of the user
     * @return array - Status and subscription information
     */
    public function checkSubscriptionStatus($userId) {
        $query = "SELECT status FROM subscriptions 
                 WHERE user_id = :user_id AND expiry_date > NOW() 
                 ORDER BY expiry_date DESC LIMIT 1";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        
        try {
            $stmt->execute();
            
            if ($stmt->rowCount() > 0) {
                $subscription = $stmt->fetch(PDO::FETCH_ASSOC);
                return ["status" => "success", "subscription_status" => $subscription['status']];
            } else {
                return ["status" => "error", "message" => "No active subscription"];
            }
        } catch (PDOException $e) {
            return ["status" => "error", "message" => "Database error: " . $e->getMessage()];
        }
    }
    
    /**
     * Get all subscription plans
     * 
     * @return array - Available subscription plans
     */
    public function getSubscriptionPlans() {
        $query = "SELECT * FROM subscription_plans WHERE active = 1";
        $stmt = $this->conn->prepare($query);
        
        try {
            $stmt->execute();
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            return ["status" => "error", "message" => "Database error: " . $e->getMessage()];
        }
    }
}
?>