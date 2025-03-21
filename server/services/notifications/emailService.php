<?php

namespace PesaGuru\Server\Services\Notifications;

/**
 * Email notification service
 */
class EmailService
{
    /**
     * @var string
     */
    private $fromEmail;
    
    /**
     * @var string
     */
    private $fromName;
    
    /**
     * Create a new email service instance
     * 
     * @param string $fromEmail
     * @param string $fromName
     */
    public function __construct(string $fromEmail = 'notifications@pesaguru.com', string $fromName = 'PesaGuru')
    {
        $this->fromEmail = $fromEmail;
        $this->fromName = $fromName;
    }
    
    /**
     * Send goal progress email
     *
     * @param string $email
     * @param string $title
     * @param string $message
     * @param array $data
     * @return bool
     */
    public function sendGoalProgressEmail(string $email, string $title, string $message, array $data): bool
    {
        // In a real application, we would use a mail library like PHPMailer or Swift Mailer
        // This is just a placeholder implementation
        
        // Create email body with template
        $body = $this->getEmailTemplate($title, $message, $data);
        
        // Send email (simulated)
        $headers = [
            'From' => "{$this->fromName} <{$this->fromEmail}>",
            'Content-Type' => 'text/html; charset=UTF-8'
        ];
        
        // Log the email sending (simulated)
        $this->logEmail($email, $title, $body);
        
        // In a real implementation, we would return the result of the email sending operation
        return true;
    }
    
    /**
     * Get email template for notification
     * 
     * @param string $title
     * @param string $message
     * @param array $data
     * @return string
     */
    private function getEmailTemplate(string $title, string $message, array $data): string
    {
        // In a real application, we would use a template engine or HTML template
        // This is a simple placeholder implementation
        
        $progress = $data['progress'] ?? 0;
        $progressBar = $this->generateProgressBar($progress);
        
        return '
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>' . htmlspecialchars($title) . '</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <img src="https://pesaguru.com/logo.png" alt="PesaGuru Logo" style="max-width: 150px;">
                    </div>
                    
                    <div style="background-color: #f9f9f9; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                        <h1 style="color: #2c3e50; margin-top: 0;">' . htmlspecialchars($title) . '</h1>
                        <p style="font-size: 16px;">' . htmlspecialchars($message) . '</p>
                        
                        ' . $progressBar . '
                    </div>
                    
                    <div style="margin-top: 30px; text-align: center; color: #888; font-size: 12px;">
                        <p>This is an automated message from PesaGuru. Please do not reply to this email.</p>
                        <p>© ' . date('Y') . ' PesaGuru. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
        ';
    }
    
    /**
     * Generate HTML progress bar
     * 
     * @param float $progress
     * @return string
     */
    private function generateProgressBar(float $progress): string
    {
        $progress = min(100, max(0, $progress));
        
        return '
            <div style="margin: 20px 0;">
                <div style="background-color: #eee; border-radius: 10px; height: 20px; width: 100%; margin-bottom: 5px;">
                    <div style="background-color: #27ae60; border-radius: 10px; height: 20px; width: ' . $progress . '%"></div>
                </div>
                <p style="text-align: center; margin: 0; font-weight: bold;">' . $progress . '% Complete</p>
            </div>
        ';
    }
    
    /**
     * Log email for debugging purposes
     * 
     * @param string $email
     * @param string $subject
     * @param string $body
     * @return void
     */
    private function logEmail(string $email, string $subject, string $body): void
    {
        // In a real application, we would log this to a file or database
        // This is just a placeholder implementation
    }
}