<?php

require_once '../models/FinancialGoal.php';

class FinancialGoalController {
    private $db;
    private $financialGoal;

    public function __construct($db) {
        $this->db = $db;
        $this->financialGoal = new FinancialGoal($this->db);
    }

    // Create a new financial goal
    public function createGoal($data) {
        $this->financialGoal->user_id = $data['user_id'];
        $this->financialGoal->title = $data['title'];
        $this->financialGoal->category = $data['category'];
        $this->financialGoal->target_amount = $data['target_amount'];
        $this->financialGoal->current_amount = $data['current_amount'];
        $this->financialGoal->target_date = $data['target_date'];
        $this->financialGoal->priority = $data['priority'];
        $this->financialGoal->status = $data['status'];
        $this->financialGoal->description = $data['description'];

        $errors = $this->financialGoal->validate();
        if (!empty($errors)) {
            return ['success' => false, 'errors' => $errors];
        }

        if ($this->financialGoal->create()) {
            return ['success' => true, 'id' => $this->financialGoal->id];
        }

        return ['success' => false, 'message' => 'Failed to create financial goal.'];
    }

    // Get all financial goals for a user
    public function getUserGoals($userId) {
        $stmt = $this->financialGoal->getUserGoals($userId);
        $goals = $stmt->fetchAll(PDO::FETCH_ASSOC);
        return ['success' => true, 'goals' => $goals];
    }

    // Update a financial goal
    public function updateGoal($data) {
        $this->financialGoal->id = $data['id'];
        $this->financialGoal->user_id = $data['user_id'];
        $this->financialGoal->title = $data['title'];
        $this->financialGoal->category = $data['category'];
        $this->financialGoal->target_amount = $data['target_amount'];
        $this->financialGoal->current_amount = $data['current_amount'];
        $this->financialGoal->target_date = $data['target_date'];
        $this->financialGoal->priority = $data['priority'];
        $this->financialGoal->status = $data['status'];
        $this->financialGoal->description = $data['description'];

        $errors = $this->financialGoal->validate();
        if (!empty($errors)) {
            return ['success' => false, 'errors' => $errors];
        }

        if ($this->financialGoal->update()) {
            return ['success' => true];
        }

        return ['success' => false, 'message' => 'Failed to update financial goal.'];
    }

    // Delete a financial goal
    public function deleteGoal($id, $userId) {
        $this->financialGoal->id = $id;
        $this->financialGoal->user_id = $userId;

        if ($this->financialGoal->delete()) {
            return ['success' => true];
        }

        return ['success' => false, 'message' => 'Failed to delete financial goal.'];
    }
}
?>
