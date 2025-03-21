<?php

return [
    // Email server settings
    'host' => 'smtp.gmail.com',
    'port' => 587,
    'smtp_auth' => true,
    'smtp_secure' => 'tls',
    'username' => 'notifications@pesaguru.co.ke',
    'password' => 'your_secure_password_here',
    
    // Sender information
    'from_email' => 'notifications@pesaguru.co.ke',
    'from_name' => 'PesaGuru Financial Advisory',
    
    // General settings
    'debug' => false, // Set to true during development
    
    // Rate limiting
    'max_emails_per_hour' => 100,
    'max_recipients_per_email' => 50,
    
    // Retry settings
    'retry_attempts' => 3,
    'retry_interval' => 300, // 5 minutes
];
?>