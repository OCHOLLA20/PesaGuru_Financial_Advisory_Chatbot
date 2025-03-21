-- Migration: Create Users Table
-- Description: Stores user account details for authentication, profile management, and financial recommendations

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[users] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [uuid] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(), -- For API authentication
        
        -- User Profile Information
        [full_name] NVARCHAR(255) NOT NULL,
        [email] NVARCHAR(255) NOT NULL,
        [phone_number] NVARCHAR(20) NOT NULL, -- Mobile number (linked to M-Pesa)
        [password_hash] NVARCHAR(255) NOT NULL,
        [date_of_birth] DATE,
        [gender] NVARCHAR(20), -- Optional field
        [profile_picture] NVARCHAR(255), -- URL reference to avatar
        [country] NVARCHAR(100) DEFAULT 'Kenya',
        [county] NVARCHAR(100), -- Kenyan county
        [city] NVARCHAR(100),
        [postal_code] NVARCHAR(20),
        [address] NVARCHAR(255),
        [occupation] NVARCHAR(100),
        [employer] NVARCHAR(100),
        [income_range] NVARCHAR(50), -- Income bracket
        [education_level] NVARCHAR(50),
        
        -- User Preferences & Financial Details
        [risk_profile] NVARCHAR(20) DEFAULT 'moderate', -- conservative, moderate, aggressive
        [preferred_currency] NVARCHAR(3) DEFAULT 'KES', -- Default currency
        [language] NVARCHAR(20) DEFAULT 'English', -- Preferred language
        [investment_experience] NVARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, advanced
        [financial_goal] NVARCHAR(50), -- Primary financial goal (retirement, education, wealth_growth)
        [target_retirement_age] INT, -- For retirement planning
        [monthly_savings_target] DECIMAL(19, 4), -- Target monthly savings amount
        [investment_time_horizon] NVARCHAR(20), -- short-term, mid-term, long-term
        [notification_preferences] NVARCHAR(MAX), -- JSON field for notification settings
        [dashboard_layout_preferences] NVARCHAR(MAX), -- JSON field for UI preferences
        
        -- Account Verification & Security
        [is_verified] BIT NOT NULL DEFAULT 0, -- Boolean flag if email/phone is verified
        [email_verified] BIT NOT NULL DEFAULT 0,
        [phone_verified] BIT NOT NULL DEFAULT 0,
        [verification_token] NVARCHAR(255), -- Token for email verification
        [verification_token_expires_at] DATETIME2,
        [mfa_enabled] BIT NOT NULL DEFAULT 0, -- Multi-factor authentication status
        [mfa_secret] NVARCHAR(255), -- Secret for MFA
        [last_login_at] DATETIME2, -- Last login timestamp
        [login_attempts] INT NOT NULL DEFAULT 0, -- Number of failed login attempts
        [account_locked_until] DATETIME2, -- Timestamp until account is locked
        [password_reset_token] NVARCHAR(255),
        [password_reset_expires_at] DATETIME2,
        [last_password_change] DATETIME2,
        
        -- M-Pesa & Bank Integration
        [mpesa_number] NVARCHAR(20), -- M-Pesa registered mobile number
        [linked_bank_account] NVARCHAR(255), -- Bank account ID for withdrawals
        [wallet_balance] DECIMAL(19, 4) NOT NULL DEFAULT 0, -- Available funds
        [mpesa_linked] BIT NOT NULL DEFAULT 0, -- Whether M-Pesa is linked
        [mpesa_last_linked_at] DATETIME2, -- When M-Pesa was last linked
        [bank_linked] BIT NOT NULL DEFAULT 0, -- Whether bank account is linked
        [bank_name] NVARCHAR(100), -- Name of linked bank
        [bank_account_number] NVARCHAR(50), -- Linked bank account number
        [bank_branch] NVARCHAR(100), -- Bank branch
        
        -- Security & Fraud Detection
        [security_questions] NVARCHAR(MAX), -- JSON array of security questions and answers
        [ip_whitelist] NVARCHAR(MAX), -- Allowed IP addresses
        [device_whitelist] NVARCHAR(MAX), -- Known devices
        [last_device_id] NVARCHAR(255), -- Last device used
        [last_ip_address] NVARCHAR(45), -- Last IP address
        [suspicious_activity_flag] BIT NOT NULL DEFAULT 0, -- Flag for suspicious activity
        [fraud_score] INT, -- AI-calculated fraud risk score (0-100)
        [last_fraud_check] DATETIME2, -- Last fraud check timestamp
        
        -- AI & Engagement Tracking
        [ai_interaction_count] INT NOT NULL DEFAULT 0, -- Number of chatbot interactions
        [engagement_score] INT, -- AI-calculated engagement score (0-100)
        [last_active_at] DATETIME2, -- Last activity timestamp
        [inactive_days_count] INT NOT NULL DEFAULT 0, -- Days since last activity
        [feature_usage_stats] NVARCHAR(MAX), -- JSON object tracking feature usage
        [session_count] INT NOT NULL DEFAULT 0, -- Number of logged sessions
        [average_session_time] INT, -- Average session duration in seconds
        [onboarding_completed] BIT NOT NULL DEFAULT 0, -- Whether onboarding is complete
        [onboarding_step] INT DEFAULT 1, -- Current onboarding step
        
        -- Financial Goal Tracking
        [goals_set_count] INT NOT NULL DEFAULT 0, -- Number of financial goals set
        [goals_achieved_count] INT NOT NULL DEFAULT 0, -- Number of financial goals achieved
        [goal_progress] NVARCHAR(MAX), -- JSON field tracking goal progress
        [next_goal_milestone] DATETIME2, -- Next goal milestone date
        [goal_streak_days] INT NOT NULL DEFAULT 0, -- Consecutive days working toward goals
        
        -- API & Integration
        [api_key] NVARCHAR(255), -- For API access
        [api_key_expires_at] DATETIME2,
        [webhook_url] NVARCHAR(255), -- For external integrations
        [external_user_id] NVARCHAR(255), -- ID in external systems
        [oauth_provider] NVARCHAR(50), -- Google, Facebook, Apple, etc.
        [oauth_id] NVARCHAR(255), -- ID from OAuth provider
        
        -- User Status & Role
        [account_status] NVARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, closed
        [user_role] NVARCHAR(20) NOT NULL DEFAULT 'user', -- user, admin, advisor
        [account_tier] NVARCHAR(20) DEFAULT 'basic', -- basic, premium, platinum
        [subscription_id] NVARCHAR(100), -- Subscription plan ID
        [subscription_expires_at] DATETIME2, -- Subscription expiration
        [is_deleted] BIT NOT NULL DEFAULT 0, -- Soft delete flag
        [deletion_date] DATETIME2, -- When user was soft deleted
        
        -- Referral & Marketing
        [referral_code] NVARCHAR(20), -- Unique referral code
        [referred_by] BIGINT, -- User ID who referred this user
        [referral_count] INT NOT NULL DEFAULT 0, -- Number of successful referrals
        [marketing_consent] BIT NOT NULL DEFAULT 0, -- Marketing consent flag
        [acquisition_source] NVARCHAR(50), -- Where user was acquired from
        [acquisition_campaign] NVARCHAR(100), -- Marketing campaign
        
        -- Timestamps & Tracking
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [created_via] NVARCHAR(50) DEFAULT 'web', -- web, mobile_app, api, chatbot
        [updated_by] NVARCHAR(100), -- Who last updated the user

        -- Constraints
        CONSTRAINT [UQ_users_email] UNIQUE ([email]),
        CONSTRAINT [UQ_users_phone_number] UNIQUE ([phone_number]),
        CONSTRAINT [CK_users_risk_profile] CHECK ([risk_profile] IN ('conservative', 'moderate', 'aggressive')),
        CONSTRAINT [CK_users_investment_experience] CHECK ([investment_experience] IN ('beginner', 'intermediate', 'advanced')),
        CONSTRAINT [CK_users_account_status] CHECK ([account_status] IN ('active', 'suspended', 'closed')),
        CONSTRAINT [CK_users_user_role] CHECK ([user_role] IN ('user', 'admin', 'advisor'))
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_users_email] ON [dbo].[users] ([email]);
    CREATE INDEX [idx_users_phone_number] ON [dbo].[users] ([phone_number]);
    CREATE INDEX [idx_users_risk_profile] ON [dbo].[users] ([risk_profile]);
    CREATE INDEX [idx_users_account_status] ON [dbo].[users] ([account_status]) WHERE [is_deleted] = 0;
    CREATE INDEX [idx_users_user_role] ON [dbo].[users] ([user_role]);
    CREATE INDEX [idx_users_created_at] ON [dbo].[users] ([created_at]);
    CREATE INDEX [idx_users_last_active_at] ON [dbo].[users] ([last_active_at]);
    CREATE INDEX [idx_users_mpesa_number] ON [dbo].[users] ([mpesa_number]) WHERE [mpesa_number] IS NOT NULL;
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores user account details for authentication, profile management, and financial recommendations for the PesaGuru financial advisory chatbot',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'users';
END
GO

-- Create trigger to update timestamps
IF OBJECT_ID('dbo.trg_users_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_users_update;
GO

CREATE TRIGGER dbo.trg_users_update
ON dbo.users
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the updated_at timestamp
    UPDATE u
    SET u.updated_at = GETDATE()
    FROM dbo.users u
    INNER JOIN inserted i ON u.id = i.id;
    
    -- Track login attempts and lock account if needed
    IF UPDATE(login_attempts)
    BEGIN
        UPDATE u
        SET 
            u.account_locked_until = 
                CASE 
                    WHEN i.login_attempts >= 5 AND i.account_locked_until IS NULL -- 5 failed attempts
                    THEN DATEADD(MINUTE, 15, GETDATE()) -- Lock for 15 minutes
                    WHEN i.login_attempts >= 10 -- 10 failed attempts
                    THEN DATEADD(HOUR, 1, GETDATE()) -- Lock for 1 hour
                    ELSE u.account_locked_until
                END
        FROM dbo.users u
        INNER JOIN inserted i ON u.id = i.id
        INNER JOIN deleted d ON i.id = d.id
        WHERE i.login_attempts > d.login_attempts;
    END
    
    -- Track user activity and engagement
    IF UPDATE(last_active_at)
    BEGIN
        UPDATE u
        SET 
            u.inactive_days_count = DATEDIFF(DAY, i.last_active_at, GETDATE()),
            u.session_count = u.session_count + 1
        FROM dbo.users u
        INNER JOIN inserted i ON u.id = i.id
        WHERE i.last_active_at IS NOT NULL;
    END
    
    -- Reset login attempts on successful login
    IF UPDATE(last_login_at)
    BEGIN
        UPDATE u
        SET 
            u.login_attempts = 0,
            u.account_locked_until = NULL
        FROM dbo.users u
        INNER JOIN inserted i ON u.id = i.id
        WHERE i.last_login_at IS NOT NULL;
    END
END
GO

-- Create procedure to register a new user
IF OBJECT_ID('dbo.sp_register_user', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_register_user;
GO

CREATE PROCEDURE dbo.sp_register_user
    @full_name NVARCHAR(255),
    @email NVARCHAR(255),
    @phone_number NVARCHAR(20),
    @password_hash NVARCHAR(255),
    @date_of_birth DATE = NULL,
    @risk_profile NVARCHAR(20) = 'moderate',
    @investment_experience NVARCHAR(20) = 'beginner',
    @created_via NVARCHAR(50) = 'web',
    @referral_code NVARCHAR(20) = NULL,
    @verification_token NVARCHAR(255) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate email is unique
    IF EXISTS (SELECT 1 FROM dbo.users WHERE email = @email)
    BEGIN
        RAISERROR('Email address is already registered.', 16, 1);
        RETURN;
    END
    
    -- Validate phone number is unique
    IF EXISTS (SELECT 1 FROM dbo.users WHERE phone_number = @phone_number)
    BEGIN
        RAISERROR('Phone number is already registered.', 16, 1);
        RETURN;
    END
    
    -- Validate risk profile
    IF @risk_profile NOT IN ('conservative', 'moderate', 'aggressive')
    BEGIN
        SET @risk_profile = 'moderate'; -- Default to moderate if invalid
    END
    
    -- Validate investment experience
    IF @investment_experience NOT IN ('beginner', 'intermediate', 'advanced')
    BEGIN
        SET @investment_experience = 'beginner'; -- Default to beginner if invalid
    END
    
    -- Generate a unique referral code for the new user
    DECLARE @new_referral_code NVARCHAR(20) = 'REF-' + CONVERT(NVARCHAR(10), ABS(CHECKSUM(NEWID())) % 10000000);
    
    -- If user was referred, find the referrer ID
    DECLARE @referred_by BIGINT = NULL;
    IF @referral_code IS NOT NULL
    BEGIN
        SELECT @referred_by = id FROM dbo.users WHERE referral_code = @referral_code;
    END
    
    -- Generate verification token if not provided
    IF @verification_token IS NULL
    BEGIN
        SET @verification_token = CONVERT(NVARCHAR(255), NEWID());
    END
    
    -- Insert new user
    INSERT INTO dbo.users (
        full_name,
        email,
        phone_number,
        password_hash,
        date_of_birth,
        risk_profile,
        investment_experience,
        verification_token,
        verification_token_expires_at,
        referral_code,
        referred_by,
        created_via,
        mpesa_number,
        last_active_at
    )
    VALUES (
        @full_name,
        @email,
        @phone_number,
        @password_hash,
        @date_of_birth,
        @risk_profile,
        @investment_experience,
        @verification_token,
        DATEADD(DAY, 1, GETDATE()), -- Token expires in 24 hours
        @new_referral_code,
        @referred_by,
        @created_via,
        @phone_number, -- Default mpesa_number to phone_number
        GETDATE() -- Set last active at to now
    );
    
    -- If this user was referred, update the referrer's count
    IF @referred_by IS NOT NULL
    BEGIN
        UPDATE dbo.users
        SET referral_count = referral_count + 1
        WHERE id = @referred_by;
    END
    
    -- Return the new user
    SELECT *
    FROM dbo.users
    WHERE id = SCOPE_IDENTITY();
END
GO

-- Create procedure to verify user email
IF OBJECT_ID('dbo.sp_verify_user_email', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_verify_user_email;
GO

CREATE PROCEDURE dbo.sp_verify_user_email
    @email NVARCHAR(255),
    @verification_token NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if token is valid and not expired
    IF NOT EXISTS (
        SELECT 1 
        FROM dbo.users 
        WHERE 
            email = @email 
            AND verification_token = @verification_token
            AND verification_token_expires_at > GETDATE()
            AND email_verified = 0
    )
    BEGIN
        RAISERROR('Invalid or expired verification token.', 16, 1);
        RETURN;
    END
    
    -- Update user verification status
    UPDATE dbo.users
    SET 
        email_verified = 1,
        verification_token = NULL,
        verification_token_expires_at = NULL,
        is_verified = CASE WHEN phone_verified = 1 THEN 1 ELSE 0 END, -- Mark as verified if phone is also verified
        updated_at = GETDATE()
    WHERE 
        email = @email 
        AND verification_token = @verification_token;
    
    -- Return the updated user
    SELECT *
    FROM dbo.users
    WHERE email = @email;
END
GO

-- Create procedure to check for suspicious activity
IF OBJECT_ID('dbo.sp_check_suspicious_activity', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_check_suspicious_activity;
GO

CREATE PROCEDURE dbo.sp_check_suspicious_activity
    @user_id BIGINT,
    @ip_address NVARCHAR(45),
    @device_id NVARCHAR(255),
    @location NVARCHAR(100) = NULL,
    @transaction_amount DECIMAL(19, 4) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get user's security information
    DECLARE @last_ip_address NVARCHAR(45);
    DECLARE @last_device_id NVARCHAR(255);
    DECLARE @ip_whitelist NVARCHAR(MAX);
    DECLARE @device_whitelist NVARCHAR(MAX);
    DECLARE @fraud_score INT = 0;
    
    SELECT 
        @last_ip_address = last_ip_address,
        @last_device_id = last_device_id,
        @ip_whitelist = ip_whitelist,
        @device_whitelist = device_whitelist
    FROM dbo.users
    WHERE id = @user_id;
    
    -- Check for IP address change
    IF @last_ip_address IS NOT NULL AND @last_ip_address <> @ip_address
    BEGIN
        SET @fraud_score = @fraud_score + 20; -- +20 points for IP change
    END
    
    -- Check for device change
    IF @last_device_id IS NOT NULL AND @last_device_id <> @device_id
    BEGIN
        SET @fraud_score = @fraud_score + 15; -- +15 points for device change
    END
    
    -- Check if IP is in whitelist
    IF @ip_whitelist IS NOT NULL AND CHARINDEX('"' + @ip_address + '"', @ip_whitelist) = 0
    BEGIN
        SET @fraud_score = @fraud_score + 10; -- +10 points for unknown IP
    END
    
    -- Check if device is in whitelist
    IF @device_whitelist IS NOT NULL AND CHARINDEX('"' + @device_id + '"', @device_whitelist) = 0
    BEGIN
        SET @fraud_score = @fraud_score + 10; -- +10 points for unknown device
    END
    
    -- Check for large transaction (if provided)
    IF @transaction_amount IS NOT NULL AND @transaction_amount > 100000 -- KES 100,000
    BEGIN
        SET @fraud_score = @fraud_score + 25; -- +25 points for large transaction
    END
    
    -- Update user's security information
    UPDATE dbo.users
    SET 
        last_ip_address = @ip_address,
        last_device_id = @device_id,
        fraud_score = @fraud_score,
        last_fraud_check = GETDATE(),
        suspicious_activity_flag = CASE WHEN @fraud_score >= 50 THEN 1 ELSE 0 END
    WHERE id = @user_id;
    
    -- Return fraud assessment
    SELECT 
        @fraud_score AS fraud_score,
        CASE 
            WHEN @fraud_score >= 75 THEN 'high'
            WHEN @fraud_score >= 50 THEN 'medium'
            WHEN @fraud_score >= 25 THEN 'low'
            ELSE 'none'
        END AS risk_level,
        CASE WHEN @fraud_score >= 50 THEN 1 ELSE 0 END AS requires_verification
END
GO

-- Create procedure to update user activity
IF OBJECT_ID('dbo.sp_update_user_activity', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_update_user_activity;
GO

CREATE PROCEDURE dbo.sp_update_user_activity
    @user_id BIGINT,
    @activity_type NVARCHAR(50), -- login, transaction, chatbot, etc.
    @activity_details NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update user's last activity timestamp
    UPDATE dbo.users
    SET 
        last_active_at = GETDATE(),
        inactive_days_count = 0
    WHERE id = @user_id;
    
    -- Increment AI interaction count if chatbot activity
    IF @activity_type = 'chatbot'
    BEGIN
        UPDATE dbo.users
        SET ai_interaction_count = ai_interaction_count + 1
        WHERE id = @user_id;
    END
    
    -- Track feature usage
    DECLARE @feature_usage NVARCHAR(MAX);
    SELECT @feature_usage = feature_usage_stats FROM dbo.users WHERE id = @user_id;
    
    IF @feature_usage IS NULL
    BEGIN
        -- Initialize feature usage JSON if not exists
        SET @feature_usage = '{
            "login": 0,
            "transaction": 0,
            "chatbot": 0,
            "portfolio": 0,
            "investment": 0,
            "reports": 0
        }';
    END
    
    -- Update the count for this activity type
    IF @activity_type IN ('login', 'transaction', 'chatbot', 'portfolio', 'investment', 'reports')
    BEGIN
        SET @feature_usage = JSON_MODIFY(
            @feature_usage,
            '$.' + @activity_type,
            ISNULL(CAST(JSON_VALUE(@feature_usage, '$.' + @activity_type) AS INT), 0) + 1
        );
        
        UPDATE dbo.users
        SET feature_usage_stats = @feature_usage
        WHERE id = @user_id;
    END
    
    -- Calculate engagement score based on activity frequency
    -- Higher scores for users who use multiple features and use them frequently
    UPDATE u
    SET 
        u.engagement_score = (
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.login') AS INT), 0) / 10) +
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.transaction') AS INT), 0) * 2) +
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.chatbot') AS INT), 0) * 3) +
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.portfolio') AS INT), 0) * 2) +
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.investment') AS INT), 0) * 3) +
            (ISNULL(CAST(JSON_VALUE(u.feature_usage_stats, '$.reports') AS INT), 0) * 1)
        ) / 5, -- Normalize to 0-100 scale (roughly)
        
        u.average_session_time = 
            CASE 
                WHEN u.average_session_time IS NULL THEN 300 -- Default 5 minutes
                ELSE (u.average_session_time * 0.8) + 
                     (CASE 
                         WHEN @activity_type = 'login' THEN 60 -- 1 minute
                         WHEN @activity_type = 'transaction' THEN 180 -- 3 minutes
                         WHEN @activity_type = 'chatbot' THEN 300 -- 5 minutes
                         WHEN @activity_type = 'portfolio' THEN 240 -- 4 minutes
                         WHEN @activity_type = 'investment' THEN 360 -- 6 minutes
                         WHEN @activity_type = 'reports' THEN 240 -- 4 minutes
                         ELSE 180 -- 3 minutes default
                      END * 0.2) -- Weighted average (80% old, 20% new)
            END
    FROM dbo.users u
    WHERE u.id = @user_id;
    
    -- Return updated user information
    SELECT
        id,
        engagement_score,
        ai_interaction_count,
        last_active_at,
        inactive_days_count,
        feature_usage_stats,
        session_count,
        average_session_time
    FROM dbo.users
    WHERE id = @user_id;
END
GO