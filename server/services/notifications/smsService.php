<?php

namespace PesaGuru\Server\Services\Notifications;

/**
 * SMS notification service
 */
class SmsService
{
    /**
     * @var string
     */
    private $apiKey;
    
    /**
     * @var string
     */
    private $senderId;
    
    /**
     * Create a new SMS service instance
     * 
     * @param string $apiKey
     * @param string $senderId
     */
    /**
     * Send SMS message
     *
     * @param string $phone
     * @param string $message
     * @return bool
     */
    public function sendMessage(string $phone, string $message): bool
    {
        // Normalize phone number (ensure it has international format for Kenya)
        $phone = $this->normalizePhoneNumber($phone);
        
        // Truncate message if it's too long (SMS typically has a 160 character limit)
        $message = $this->truncateMessage($message);
        
        // In a real application, we would use an SMS gateway API
        // This is just a placeholder implementation
        
        // Prepare API request parameters for Africa's Talking or similar service
        $params = [
            'username' => 'pesaguru',
            'to' => $phone,
            'message' => $message,
            'from' => $this->senderId
        ];
        
        // Log the SMS sending attempt
        $this->logSms($phone, $message);
        
        // In a real implementation, we would send the SMS and return the result
        return true;
    }
    
    /**
     * Normalize phone number to international format for Kenya
     * 
     * @param string $phone
     * @return string
     */
    private function normalizePhoneNumber(string $phone): string
    {
        // Remove any non-numeric characters
        $phone = preg_replace('/[^0-9]/', '', $phone);
        
        // If the number starts with 0, replace it with Kenya's country code
        if (substr($phone, 0, 1) === '0') {
            $phone = '254' . substr($phone, 1);
        }
        
        // If the number doesn't have a country code, add Kenya's country code
        if (strlen($phone) === 9) {
            $phone = '254' . $phone;
        }
        
        return $phone;
    }
    
    /**
     * Truncate message to fit SMS character limit
     * 
     * @param string $message
     * @param int $limit
     * @return string
     */
    private function truncateMessage(string $message, int $limit = 160): string
    {
        if (strlen($message) <= $limit) {
            return $message;
        }
        
        return substr($message, 0, $limit - 3) . '...';
    }
    
    /**
     * Log SMS for debugging purposes
     * 
     * @param string $phone
     * @param string $message
     * @return void
     */
    private function logSms(string $phone, string $message): void
    {
        // In a real application, we would log this to a file or database
        // This is just a placeholder implementation
    }
}