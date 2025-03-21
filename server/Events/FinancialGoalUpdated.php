<?php

namespace PesaGuru\Server\Events;

use PesaGuru\Server\Models\FinancialGoal;

/**
 * Event triggered when a financial goal is updated
 */
class FinancialGoalUpdated
{
    /**
     * @var FinancialGoal
     */
    public $goal;
    
    /**
     * @var float
     */
    public $previousProgress;
    
    /**
     * Create a new event instance.
     *
     * @param FinancialGoal $goal
     * @param float $previousProgress
     */
    public function __construct(FinancialGoal $goal, float $previousProgress)
    {
        $this->goal = $goal;
        $this->previousProgress = $previousProgress;
    }
}