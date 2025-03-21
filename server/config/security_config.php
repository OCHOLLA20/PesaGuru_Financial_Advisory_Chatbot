<?php

return [
    /**
     * Authentication Security Settings
     */
    'auth' => [
        'jwt_secret' => getenv('JWT_SECRET') ?: 'change_this_to_secure_key_in_production',
        'jwt_expiration' => 3600, // Token expiration time in seconds (1 hour)
        'jwt_refresh_expiration' => 86400, // Refresh token expiration (24 hours)
        'password_hash_algo' => PASSWORD_BCRYPT,
        'password_hash_cost' => 12, // Higher cost means more secure but slower
        'max_login_attempts' => 5, // Maximum failed login attempts before lockout
        'lockout_time' => 900, // Account lockout duration in seconds (15 minutes)
        'require_2fa' => true, // Require two-factor authentication for sensitive operations
    ],
    
    /**
     * API Security Settings
     */
    'api' => [
        'rate_limits' => [
            'default' => [
                'limit' => 60, // 60 requests
                'period' => 60, // per minute
            ],
            'financial_data' => [
                'limit' => 120, // 120 requests
                'period' => 60, // per minute
            ],
            'chatbot' => [
                'limit' => 30, // 30 requests
                'period' => 60, // per minute
            ],
        ],
        'api_key_rotation_days' => 90, // Rotate API keys every 90 days
        'require_https' => true, // Require HTTPS for all API requests
    ],
    
    /**
     * Encryption Settings
     */
    'encryption' => [
        'method' => 'AES-256-CBC', // Encryption algorithm
        'key' => getenv('ENCRYPTION_KEY') ?: 'change_this_to_secure_key_in_production',
        'encrypt_user_data' => true, // Encrypt sensitive user data in database
        'encrypt_financial_data' => true, // Encrypt financial data
    ],
    
    /**
     * Session Security
     */
    'session' => [
        'secure' => true, // Transmit cookie only over HTTPS
        'httponly' => true, // Make cookie accessible only through HTTP protocol
        'samesite' => 'Lax', // Control cross-site request forgery
        'lifetime' => 7200, // Session lifetime in seconds (2 hours)
        'regenerate_id' => true, // Regenerate session ID at login
        'use_only_cookies' => true, // Force use of cookies for session
    ],
    
    /**
     * CSRF Protection
     */
    'csrf' => [
        'enabled' => true,
        'token_lifetime' => 7200, // CSRF token lifetime (2 hours)
    ],
    
    /**
     * Role-Based Access Control (RBAC)
     */
    'rbac' => [
        'default_role' => 'user',
        'roles' => [
            'user' => [
                'permissions' => ['view_own_profile', 'use_chatbot', 'view_public_data']
            ],
            'premium_user' => [
                'permissions' => ['view_own_profile', 'use_chatbot', 'view_public_data', 'access_premium_features']
            ],
            'admin' => [
                'permissions' => ['view_own_profile', 'use_chatbot', 'view_public_data', 
                                 'access_premium_features', 'manage_users', 'view_analytics']
            ],
            'super_admin' => [
                'permissions' => ['*'] // All permissions
            ]
        ]
    ],
    
    /**
     * Security Headers
     */
    'headers' => [
        'X-Content-Type-Options' => 'nosniff',
        'X-Frame-Options' => 'SAMEORIGIN', 
        'X-XSS-Protection' => '1; mode=block',
        'Strict-Transport-Security' => 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy' => "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; img-src 'self' data:; connect-src 'self' https://api.nse.co.ke https://api.safaricom.co.ke https://api.cbk.co.ke; font-src 'self' https://cdnjs.cloudflare.com;"
    ],
    
    /**
     * Data Protection & Privacy (Kenya PDPA Compliance)
     */
    'data_protection' => [
        'consent_required' => true, // Require explicit user consent for data collection
        'data_retention_days' => 730, // Retain personal data for maximum 2 years
        'anonymize_inactive_users' => true, // Anonymize data of inactive users
        'allow_data_export' => true, // Allow users to export their data
        'allow_data_deletion' => true, // Allow users to request data deletion
        'privacy_policy_version' => '1.0.3', // Current privacy policy version
    ],
    
    /**
     * Audit & Logging
     */
    'audit' => [
        'log_user_actions' => true, // Log important user actions for audit
        'log_api_requests' => true, // Log API requests
        'log_auth_attempts' => true, // Log authentication attempts
        'log_admin_actions' => true, // Log all admin actions
        'log_retention_days' => 365, // Keep logs for 1 year
    ],
    
    /**
     * Security Scanning & Intrusion Detection
     */
    'security_monitoring' => [
        'enable_intrusion_detection' => true, // Enable intrusion detection
        'enable_file_scanning' => true, // Scan uploaded files for malware
        'block_suspicious_ips' => true, // Block IPs with suspicious activity
        'notify_on_security_events' => true, // Send notifications on security events
    ],
    
    /**
     * Financial Transaction Security
     */
    'transaction_security' => [
        'require_verification' => true, // Require additional verification for transactions
        'amount_threshold_for_extra_verification' => 50000, // KES amount that triggers extra verification
        'notify_on_transactions' => true, // Send notifications for all transactions
    ]
];