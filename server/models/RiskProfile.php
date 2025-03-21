<?php

class RiskProfile {
    private $userId;
    private $riskLevel; // low, moderate, high
    private $riskScore;

    public function __construct($userId, $riskLevel, $riskScore) {
        $this->userId = $userId;
        $this->riskLevel = $riskLevel;
        $this->riskScore = $riskScore;
    }

    public function getUserId() {
        return $this->userId;
    }

    public function getRiskLevel() {
        return $this->riskLevel;
    }

    public function getRiskScore() {
        return $this->riskScore;
    }

    public function setRiskLevel($riskLevel) {
        $this->riskLevel = $riskLevel;
    }

    public function setRiskScore($riskScore) {
        $this->riskScore = $riskScore;
    }
}

?>
