<?php

namespace App\Events;

use App\Models\FinancialGoalModel;

class GoalProgressUpdated
{
    /**
     * The financial goal model instance.
     *
     * @var \App\Models\FinancialGoalModel
     */
    public $goal;

    /**
     * The previous amount before update.
     *
     * @var float
     */
    public $oldAmount;

    /**
     * The new updated amount.
     *
     * @var float
     */
    public $newAmount;

    /**
     * Create a new event instance.
     *
     * @param  \App\Models\FinancialGoalModel  $goal
     * @param  float  $oldAmount
     * @param  float  $newAmount
     * @return void
     */
    public function __construct(FinancialGoalModel $goal, float $oldAmount, float $newAmount)
    {
        $this->goal = $goal;
        $this->oldAmount = $oldAmount;
        $this->newAmount = $newAmount;
    }

    /**
     * Get the event data as an array.
     *
     * @return array
     */
    public function toArray()
    {
        return [
            'goal_id' => $this->goal->id,
            'goal_name' => $this->goal->name,
            'old_amount' => $this->oldAmount,
            'new_amount' => $this->newAmount,
            'progress_percentage' => $this->goal->progress_percentage,
            'status' => $this->goal->status,
            'timestamp' => date('c') // ISO 8601 date format
        ];
    }
    
    /**
     * Get the user ID associated with this event.
     *
     * @return int
     */
    public function getUserId()
    {
        return $this->goal->user_id;
    }
}