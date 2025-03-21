<?php
/**
 * EmailService.php
 * 
 * Handles email notifications for PesaGuru financial advisory platform.
 * Used for sending transactional emails like welcome messages, password resets,
 * financial alerts, and investment recommendations.
 */

namespace App\Services\Notifications;

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;
use PHPMailer\PHPMailer\SMTP;

class EmailService {
    private $mailer;
    private $config;
    private $logger;
    private $templatePath;
    
    /**
     * Constructor - initializes email service with configuration
     * 
     * @param array $config Email configuration parameters
     * @param object $logger Logger instance for error tracking
     */
    public function __construct($config = null, $logger = null) {
        $this->mailer = new PHPMailer(true);
        
        // Load default config if not provided
        if ($config === null) {
            $this->loadDefaultConfig();
        } else {
            $this->config = $config;
        }
        
        $this->logger = $logger;
        $this->templatePath = dirname(__FILE__) . '/../../../assets/email_templates/';
        
        // Configure PHPMailer with settings
        $this->setupMailer();
    }
    
    /**
     * Load default email configuration from config file
     */
    private function loadDefaultConfig() {
        $configFile = dirname(__FILE__) . '/../../config/email_config.php';
        if (file_exists($configFile)) {
            $this->config = include($configFile);
        } else {
            throw new \Exception("Email configuration file not found.");
        }
    }
    
    /**
     * Set up PHPMailer with configuration parameters
     */
    private function setupMailer() {
        try {
            // Server settings
            if ($this->config['debug']) {
                $this->mailer->SMTPDebug = SMTP::DEBUG_SERVER;
            }
            
            $this->mailer->isSMTP();
            $this->mailer->Host = $this->config['host'];
            $this->mailer->SMTPAuth = $this->config['smtp_auth'];
            $this->mailer->Username = $this->config['username'];
            $this->mailer->Password = $this->config['password'];
            $this->mailer->SMTPSecure = $this->config['smtp_secure'];
            $this->mailer->Port = $this->config['port'];
            
            // Default sender
            $this->mailer->setFrom(
                $this->config['from_email'],
                $this->config['from_name']
            );
            
            // Set charset
            $this->mailer->CharSet = 'UTF-8';
            
        } catch (Exception $e) {
            $this->logError("Email service setup failed: " . $e->getMessage());
            throw $e;
        }
    }
    
    /**
     * Send welcome email to new users
     * 
     * @param string $email Recipient email address
     * @param string $name Recipient name
     * @param array $data Additional template data
     * @return bool Success status
     */
    public function sendWelcomeEmail($email, $name, $data = []) {
        $subject = "Welcome to PesaGuru - Your Personal Financial Advisor";
        $template = "welcome.html";
        
        $templateData = array_merge([
            'name' => $name,
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ], $data);
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * Send password reset email with token link
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param string $resetToken Password reset token
     * @param string $resetUrl Reset link URL
     * @return bool Success status
     */
    public function sendPasswordResetEmail($email, $name, $resetToken, $resetUrl) {
        $subject = "PesaGuru Password Reset Request";
        $template = "password_reset.html";
        
        $templateData = [
            'name' => $name,
            'reset_token' => $resetToken,
            'reset_url' => $resetUrl,
            'expiry_time' => '1 hour',
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ];
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * Send financial alert email (stock movements, investment opportunities)
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param string $alertType Type of financial alert
     * @param array $alertData Alert specific data
     * @return bool Success status
     */
    public function sendFinancialAlertEmail($email, $name, $alertType, $alertData) {
        $subject = "PesaGuru Financial Alert: " . $this->getAlertSubject($alertType);
        $template = "financial_alert.html";
        
        $templateData = array_merge([
            'name' => $name,
            'alert_type' => $alertType,
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ], $alertData);
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * Send personalized investment recommendations
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param array $recommendations Investment recommendations
     * @return bool Success status
     */
    public function sendInvestmentRecommendationsEmail($email, $name, $recommendations) {
        $subject = "Your Personalized Investment Recommendations from PesaGuru";
        $template = "investment_recommendations.html";
        
        $templateData = [
            'name' => $name,
            'recommendations' => $recommendations,
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ];
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * Send notification about upcoming financial webinar
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param array $eventData Webinar details
     * @return bool Success status
     */
    public function sendWebinarNotificationEmail($email, $name, $eventData) {
        $subject = "Upcoming Financial Webinar: " . $eventData['title'];
        $template = "webinar_notification.html";
        
        $templateData = array_merge([
            'name' => $name,
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ], $eventData);
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * Get alert subject based on alert type
     * 
     * @param string $alertType Type of financial alert
     * @return string Alert subject
     */
    private function getAlertSubject($alertType) {
        $subjects = [
            'stock_price' => 'Stock Price Update',
            'investment_opportunity' => 'New Investment Opportunity',
            'market_volatility' => 'Market Volatility Alert',
            'goal_progress' => 'Financial Goal Progress Update',
            'savings_reminder' => 'Savings Reminder',
            'budget_alert' => 'Budget Alert'
        ];
        
        return isset($subjects[$alertType]) ? $subjects[$alertType] : 'Important Financial Update';
    }
    
    /**
     * Send email verification link
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param string $verificationToken Verification token
     * @param string $verificationUrl Verification URL
     * @return bool Success status
     */
    public function sendVerificationEmail($email, $name, $verificationToken, $verificationUrl) {
        $subject = "Verify Your PesaGuru Account";
        $template = "email_verification.html";
        
        $templateData = [
            'name' => $name,
            'verification_token' => $verificationToken,
            'verification_url' => $verificationUrl,
            'expiry_time' => '24 hours',
            'app_name' => 'PesaGuru',
            'current_year' => date('Y')
        ];
        
        return $this->sendEmail($email, $name, $subject, $template, $templateData);
    }
    
    /**
     * General method to send any email using a template
     * 
     * @param string $email Recipient email
     * @param string $name Recipient name
     * @param string $subject Email subject
     * @param string $template Template filename
     * @param array $templateData Template data
     * @return bool Success status
     */
    public function sendEmail($email, $name, $subject, $template, $templateData = []) {
        try {
            // Reset mailer for new message
            $this->mailer->clearAddresses();
            $this->mailer->clearAttachments();
            
            // Set recipient
            $this->mailer->addAddress($email, $name);
            
            // Set email subject
            $this->mailer->Subject = $subject;
            
            // Set email content from template
            $content = $this->renderTemplate($template, $templateData);
            $this->mailer->isHTML(true);
            $this->mailer->Body = $content;
            
            // Generate plain text version
            $this->mailer->AltBody = $this->stripHtmlTags($content);
            
            // Send the email
            $this->mailer->send();
            return true;
            
        } catch (Exception $e) {
            $this->logError("Failed to send email to {$email}: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Render email template with provided data
     * 
     * @param string $template Template filename
     * @param array $data Template data
     * @return string Rendered template content
     */
    private function renderTemplate($template, $data) {
        $templateFile = $this->templatePath . $template;
        
        if (!file_exists($templateFile)) {
            throw new \Exception("Email template not found: {$template}");
        }
        
        // Get template content
        $content = file_get_contents($templateFile);
        
        // Replace placeholders with actual data
        foreach ($data as $key => $value) {
            // Skip arrays and objects
            if (is_array($value) || is_object($value)) {
                continue;
            }
            $content = str_replace('{{' . $key . '}}', $value, $content);
        }
        
        // Handle special content like investment recommendations
        if (isset($data['recommendations']) && is_array($data['recommendations'])) {
            $recHtml = $this->renderRecommendations($data['recommendations']);
            $content = str_replace('{{recommendations_list}}', $recHtml, $content);
        }
        
        return $content;
    }
    
    /**
     * Render investment recommendations as HTML
     * 
     * @param array $recommendations Recommendation data
     * @return string HTML content
     */
    private function renderRecommendations($recommendations) {
        $html = '<ul style="padding-left: 20px;">';
        
        foreach ($recommendations as $rec) {
            $html .= '<li style="margin-bottom: 15px;">';
            $html .= '<strong>' . htmlspecialchars($rec['title']) . '</strong><br>';
            $html .= htmlspecialchars($rec['description']) . '<br>';
            
            if (isset($rec['risk_level'])) {
                $html .= 'Risk Level: ' . htmlspecialchars($rec['risk_level']) . '<br>';
            }
            
            if (isset($rec['potential_return'])) {
                $html .= 'Potential Return: ' . htmlspecialchars($rec['potential_return']) . '<br>';
            }
            
            $html .= '</li>';
        }
        
        $html .= '</ul>';
        return $html;
    }
    
    /**
     * Strip HTML tags for plain text email version
     * 
     * @param string $html HTML content
     * @return string Plain text content
     */
    private function stripHtmlTags($html) {
        // Replace HTML elements with text equivalents
        $text = preg_replace('/<br\s*\/?>/i', "\n", $html);
        $text = preg_replace('/<hr\s*\/?>/i', "\n----------\n", $text);
        $text = preg_replace('/<li>/i', "- ", $text);
        $text = preg_replace('/<\/li>/i', "\n", $text);
        $text = preg_replace('/<\/p>/i', "\n\n", $text);
        
        // Remove remaining HTML tags
        $text = strip_tags($text);
        
        // Decode HTML entities
        $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
        
        // Normalize line breaks
        $text = str_replace(["\r\n", "\r"], "\n", $text);
        
        // Remove extra line breaks
        $text = preg_replace('/\n\s+\n/', "\n\n", $text);
        $text = preg_replace('/[\n]{3,}/', "\n\n", $text);
        
        return trim($text);
    }
    
    /**
     * Send bulk emails to multiple recipients
     * 
     * @param array $recipients Array of recipient data [email, name, data]
     * @param string $subject Email subject
     * @param string $template Template filename
     * @return array Array of success statuses by email
     */
    public function sendBulkEmail($recipients, $subject, $template) {
        $results = [];
        
        foreach ($recipients as $recipient) {
            $email = $recipient['email'];
            $name = $recipient['name'];
            $data = isset($recipient['data']) ? $recipient['data'] : [];
            
            $results[$email] = $this->sendEmail($email, $name, $subject, $template, $data);
        }
        
        return $results;
    }
    
    /**
     * Log error message
     * 
     * @param string $message Error message
     */
    private function logError($message) {
        if ($this->logger) {
            $this->logger->error($message);
        } else {
            error_log("[EmailService] " . $message);
        }
    }
    
    /**
     * Add attachment to email
     * 
     * @param string $path File path
     * @param string $name File name (optional)
     * @return bool Success status
     */
    public function addAttachment($path, $name = '') {
        try {
            $this->mailer->addAttachment($path, $name);
            return true;
        } catch (Exception $e) {
            $this->logError("Failed to add attachment: " . $e->getMessage());
            return false;
        }
    }
}
?>