<?php

namespace PesaGuru\Server\Listeners;

use PesaGuru\Server\Events\FinancialGoalUpdated;
use PesaGuru\Server\Models\FinancialGoal;
use PesaGuru\Server\Models\User;
use PesaGuru\Server\Services\Notifications\EmailService;
use PesaGuru\Server\Services\Notifications\SmsService;
use PesaGuru\Server\Services\Notifications\PushNotificationService;

/**
 * Listener class responsible for sending notifications when users make 
 * progress towards their financial goals.
 */
class SendGoalProgressNotification
{
    /**
     * @var EmailService
     */
    protected $emailService;
    
    /**
     * @var SmsService
     */
    protected $smsService;
    
    /**
     * @var PushNotificationService
     */
    protected $pushNotificationService;
    
    /**
     * Create a new listener instance.
     *
     * @param EmailService $emailService
     * @param SmsService $smsService
     * @param PushNotificationService $pushNotificationService
     * @return void
     */
    public function __construct(
        EmailService $emailService,
        SmsService $smsService,
        PushNotificationService $pushNotificationService
    ) {
        $this->emailService = $emailService;
        $this->smsService = $smsService;
        $this->pushNotificationService = $pushNotificationService;
    }
    
    /**
     * Handle the financial goal updated event.
     *
     * @param FinancialGoalUpdated $event
     * @return void
     */
    public function handle(FinancialGoalUpdated $event)
    {
        $goal = $event->goal;
        $user = $goal->user;
        
        // Check if notification is needed (significant progress made)
        if ($this->shouldSendNotification($goal, $event->previousProgress)) {
            $notificationData = $this->prepareNotificationData($goal, $user);
            $this->sendNotifications($user, $notificationData);
        }
    }
    
    /**
     * Determine if a notification should be sent based on goal progress.
     *
     * @param FinancialGoal $goal
     * @param float $previousProgress
     * @return bool
     */
    private function shouldSendNotification(FinancialGoal $goal, float $previousProgress): bool
    {
        // Calculate current progress percentage
        $currentProgress = $this->calculateProgressPercentage($goal);
        
        // Define milestone thresholds (25%, 50%, 75%, 100%)
        $milestones = [25, 50, 75, 100];
        
        // Check if user has crossed a milestone
        foreach ($milestones as $milestone) {
            if ($previousProgress < $milestone && $currentProgress >= $milestone) {
                return true;
            }
        }
        
        // Also notify on consistent small progress (e.g., every 5% after reaching 10%)
        if ($currentProgress >= 10 && $currentProgress - $previousProgress >= 5) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Calculate the progress percentage for a financial goal.
     *
     * @param FinancialGoal $goal
     * @return float
     */
    private function calculateProgressPercentage(FinancialGoal $goal): float
    {
        if ($goal->target_amount <= 0) {
            return 0;
        }
        
        return min(100, round(($goal->current_amount / $goal->target_amount) * 100, 2));
    }
    
    /**
     * Prepare notification data based on goal type and progress.
     *
     * @param FinancialGoal $goal
     * @param User $user
     * @return array
     */
    private function prepareNotificationData(FinancialGoal $goal, User $user): array
    {
        $progress = $this->calculateProgressPercentage($goal);
        $remainingAmount = $goal->target_amount - $goal->current_amount;
        
        // Format currency amounts
        $currentAmount = number_format($goal->current_amount, 2);
        $targetAmount = number_format($goal->target_amount, 2);
        $remaining = number_format($remainingAmount, 2);
        
        // Create notification data based on progress milestone
        if ($progress >= 100) {
            $title = "Congratulations! 🎉";
            $message = "You've achieved your financial goal: {$goal->title}! You saved KES {$targetAmount}.";
            $type = "goal_completed";
        } elseif ($progress >= 75) {
            $title = "Almost there! 🚀";
            $message = "You're 75% of the way to your goal: {$goal->title}. Only KES {$remaining} to go!";
            $type = "goal_milestone";
        } elseif ($progress >= 50) {
            $title = "Halfway there! 👏";
            $message = "You've reached the halfway mark for your goal: {$goal->title}. KES {$currentAmount} saved!";
            $type = "goal_milestone";
        } elseif ($progress >= 25) {
            $title = "Great progress! 👍";
            $message = "You've completed 25% of your goal: {$goal->title}. Keep it up!";
            $type = "goal_milestone";
        } else {
            $title = "Good progress! 💪";
            $message = "You've saved KES {$currentAmount} towards your goal: {$goal->title}. Keep going!";
            $type = "goal_progress";
        }
        
        // Include motivational tip based on goal type
        $tip = $this->getMotivationalTip($goal);
        if ($tip) {
            $message .= " " . $tip;
        }
        
        return [
            'title' => $title,
            'message' => $message,
            'progress' => $progress,
            'type' => $type,
            'goal_id' => $goal->id,
            'goal_title' => $goal->title,
            'target_amount' => $goal->target_amount,
            'current_amount' => $goal->current_amount,
            'remaining_amount' => $remainingAmount,
        ];
    }
    
    /**
     * Get a motivational tip based on the goal type.
     *
     * @param FinancialGoal $goal
     * @return string|null
     */
    private function getMotivationalTip(FinancialGoal $goal): ?string
    {
        $tips = [
            'emergency_fund' => 'An emergency fund is your financial safety net. Aim for 3-6 months of expenses.',
            'retirement' => 'Small consistent contributions to retirement add up significantly over time!',
            'education' => 'Investing in education is one of the best returns on investment you can make.',
            'home_purchase' => 'Homeownership builds equity and financial security for your future.',
            'debt_payment' => 'Paying off debt increases your financial freedom and reduces stress.',
            'vacation' => 'Planning and saving for vacations helps avoid post-trip financial stress.',
            'investment' => 'Regular investing helps your money grow through compound interest.',
            'vehicle' => 'Saving for a vehicle purchase reduces or eliminates the need for costly loans.',
            'business' => 'Having startup capital gives your business the best chance of success.',
            'wedding' => 'A well-planned wedding budget helps start your marriage on solid financial footing.',
        ];
        
        return $tips[$goal->type] ?? null;
    }
    
    /**
     * Send notifications through user's preferred channels.
     *
     * @param User $user
     * @param array $notificationData
     * @return void
     */
    private function sendNotifications(User $user, array $notificationData): void
    {
        // Check user notification preferences
        $preferences = $user->notification_preferences ?? [
            'email' => true,
            'sms' => false,
            'push' => true
        ];
        
        // Send email notification
        if ($preferences['email'] ?? true) {
            $this->emailService->sendGoalProgressEmail(
                $user->email,
                $notificationData['title'],
                $notificationData['message'],
                $notificationData
            );
        }
        
        // Send SMS notification (if user has opted in and has a phone number)
        if (($preferences['sms'] ?? false) && !empty($user->phone)) {
            $this->smsService->sendMessage(
                $user->phone,
                $notificationData['message']
            );
        }
        
        // Send push notification (if enabled)
        if ($preferences['push'] ?? true) {
            $this->pushNotificationService->send(
                $user->id,
                $notificationData['title'],
                $notificationData['message'],
                $notificationData
            );
        }
        
        // Log the notification
        $this->logNotification($user->id, $notificationData);
    }
    
    /**
     * Log the notification for tracking purposes.
     *
     * @param int $userId
     * @param array $notificationData
     * @return void
     */
    private function logNotification(int $userId, array $notificationData): void
    {
        // Here you would typically log to database
        // This is a simplified implementation
        $logData = [
            'user_id' => $userId,
            'notification_type' => 'goal_progress',
            'goal_id' => $notificationData['goal_id'],
            'progress' => $notificationData['progress'],
            'sent_at' => date('Y-m-d H:i:s'),
            'message' => $notificationData['message']
        ];
        
        // Log notification (implementation would depend on your logging system)
        // logger()->info('Goal progress notification sent', $logData);
    }
}