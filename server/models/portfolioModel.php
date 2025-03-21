<?php
// Add namespace if needed
namespace App\Models;

// Import the Database class from the correct namespace
use App\Config\Database;

class PortfolioModel {
    private $conn;
    
    public function __construct() {
        // Use the static method directly from the imported Database class
        $this->conn = Database::getConnection();
    }
    
    // Fetch user portfolio
    public function fetchPortfolio($userId) {
        $query = "SELECT * FROM portfolio WHERE user_id = :user_id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        $stmt->execute();
        return $stmt->fetchAll(\PDO::FETCH_ASSOC);
    }
    
    // Add new investment
    public function insertInvestment($userId, $assetName, $amount, $category) {
        $query = "INSERT INTO portfolio (user_id, asset_name, amount, category) VALUES (:user_id, :asset_name, :amount, :category)";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        $stmt->bindParam(':asset_name', $assetName);
        $stmt->bindParam(':amount', $amount);
        $stmt->bindParam(':category', $category);
        if ($stmt->execute()) {
            return ["status" => "success", "message" => "Investment added successfully"];
        } else {
            return ["status" => "error", "message" => "Failed to add investment"];
        }
    }
    
    // Update investment
    public function modifyInvestment($investmentId, $amount) {
        $query = "UPDATE portfolio SET amount = :amount WHERE id = :investment_id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':investment_id', $investmentId);
        $stmt->bindParam(':amount', $amount);
        if ($stmt->execute()) {
            return ["status" => "success", "message" => "Investment updated successfully"];
        } else {
            return ["status" => "error", "message" => "Failed to update investment"];
        }
    }
    
    // Delete investment
    public function removeInvestment($investmentId) {
        $query = "DELETE FROM portfolio WHERE id = :investment_id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':investment_id', $investmentId);
        if ($stmt->execute()) {
            return ["status" => "success", "message" => "Investment removed successfully"];
        } else {
            return ["status" => "error", "message" => "Failed to remove investment"];
        }
    }
}