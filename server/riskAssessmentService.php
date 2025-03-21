<?php
require_once '../config/db.php';

class RiskAssessmentService {
    private $conn;

    public function __construct() {
        $database = new Database();
        $this->conn = $database->connect();
    }

    // Calculate Risk Score Based on User Inputs
    public function assessRisk($userId, $age, $income, $investmentExperience, $riskPreference) {
        $riskScore = 0;

        // Age Factor (Younger investors tend to have higher risk tolerance)
        if ($age < 30) {
            $riskScore += 20;
        } elseif ($age < 50) {
            $riskScore += 15;
        } else {
            $riskScore += 10;
        }

        // Income Factor (Higher income = higher risk tolerance)
        if ($income > 100000) {
            $riskScore += 20;
        } elseif ($income > 50000) {
            $riskScore += 15;
        } else {
            $riskScore += 10;
        }

        // Investment Experience (Experienced investors take more risks)
        switch ($investmentExperience) {
            case "Beginner":
                $riskScore += 10;
                break;
            case "Intermediate":
                $riskScore += 15;
                break;
            case "Advanced":
                $riskScore += 20;
                break;
        }

        // Risk Preference (Self-declared by the user)
        switch ($riskPreference) {
            case "Low":
                $riskScore += 10;
                break;
            case "Medium":
                $riskScore += 15;
                break;
            case "High":
                $riskScore += 20;
                break;
        }

        return $this->saveRiskAssessment($userId, $riskScore);
    }

    // Store or Update Risk Assessment
    private function saveRiskAssessment($userId, $riskScore) {
        $query = "INSERT INTO risk_profiles (user_id, risk_score) VALUES (:user_id, :risk_score)
                  ON DUPLICATE KEY UPDATE risk_score = :risk_score";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        $stmt->bindParam(':risk_score', $riskScore);

        if ($stmt->execute()) {
            return ["status" => "success", "message" => "Risk profile updated successfully", "risk_score" => $riskScore];
        } else {
            return ["status" => "error", "message" => "Failed to update risk profile"];
        }
    }

    // Retrieve Risk Assessment for a User
    public function getRiskProfile($userId) {
        $query = "SELECT risk_score FROM risk_profiles WHERE user_id = :user_id";
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':user_id', $userId);
        $stmt->execute();

        if ($stmt->rowCount() > 0) {
            return $stmt->fetch(PDO::FETCH_ASSOC);
        } else {
            return ["status" => "error", "message" => "No risk profile found"];
        }
    }
}
?>

