-- Migration: Create Risk Profiles Table
-- Description: Stores user risk profiles for personalized investment recommendations and portfolio management

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[risk_profiles]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[risk_profiles] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [profile_code] NVARCHAR(20) NOT NULL, -- Unique identifier code for the risk profile
        
        -- Risk Assessment Metrics
        [risk_level] NVARCHAR(20) NOT NULL, -- conservative, moderate, aggressive
        [risk_score] INT NOT NULL, -- Numerical score (e.g., 1-100) for more granular analysis
        [investment_experience] NVARCHAR(20) NOT NULL, -- beginner, intermediate, advanced
        [income_stability] NVARCHAR(20) NOT NULL, -- low, medium, high
        [liquidity_needs] NVARCHAR(20) NOT NULL, -- low, medium, high
        [volatility_tolerance] NVARCHAR(20) NOT NULL, -- low, medium, high
        [investment_horizon] NVARCHAR(20) NOT NULL, -- short-term, mid-term, long-term
        [age_group] NVARCHAR(20), -- 18-25, 26-35, 36-45, 46-55, 56-65, 65+
        [retirement_timeline] INT, -- Years until retirement
        [financial_dependents] INT, -- Number of financial dependents
        [emergency_fund_months] INT, -- Months of expenses in emergency funds
        
        -- Asset Allocation Preferences
        [preferred_assets] NVARCHAR(MAX), -- JSON field storing user asset preferences
        [diversification_preference] BIT NOT NULL DEFAULT 1, -- Whether user prefers a diversified portfolio
        [geographical_preference] NVARCHAR(MAX), -- JSON field for preferred investment regions
        [ethical_investing_preference] BIT DEFAULT 0, -- Whether user prefers ethical/ESG investments
        [sector_preferences] NVARCHAR(MAX), -- JSON field for preferred industry sectors
        [max_allocation_per_asset] INT, -- Maximum percentage to allocate to a single asset
        [min_expected_return] DECIMAL(5, 2), -- Minimum expected annual return percentage
        
        -- AI-Driven Insights
        [suggested_strategy] NVARCHAR(50), -- growth, income, balanced, value, etc.
        [market_sentiment_score] DECIMAL(5, 2), -- AI-generated sentiment score (-1 to 1)
        [historical_risk_score] NVARCHAR(MAX), -- JSON array of past risk scores with dates
        [risk_trend] NVARCHAR(20), -- increasing, stable, decreasing
        [peer_comparison_percentile] INT, -- Percentile relative to similar profiles
        [recommended_portfolio_turnover] NVARCHAR(20), -- low, medium, high
        [optimal_rebalancing_frequency] NVARCHAR(20), -- monthly, quarterly, semi-annually, annually
        
        -- Kenya-Specific Factors
        [nse_comfort_level] NVARCHAR(20), -- Comfort with Nairobi Securities Exchange
        [forex_exposure_preference] NVARCHAR(20), -- Preference for foreign currency exposure
        [local_market_confidence] INT, -- 1-10 confidence in local Kenyan markets
        [mpesa_integration_preference] BIT DEFAULT 1, -- Preference for M-Pesa integration
        
        -- Questionnaire & Assessment Data
        [assessment_version] NVARCHAR(20), -- Version of risk assessment used
        [questionnaire_responses] NVARCHAR(MAX), -- JSON field with responses to risk questions
        [questionnaire_completion_date] DATETIME2, -- When the user completed the assessment
        [override_reason] NVARCHAR(MAX), -- Reason if risk profile was manually overridden
        [assessment_score_breakdown] NVARCHAR(MAX), -- JSON field with score breakdown
        
        -- Notification Preferences
        [alert_on_market_volatility] BIT DEFAULT 1, -- Alert when market volatility increases
        [alert_on_risk_profile_change] BIT DEFAULT 1, -- Alert when risk profile changes
        [alert_on_asset_reallocation] BIT DEFAULT 1, -- Alert when asset allocation changes
        [notification_frequency] NVARCHAR(20) DEFAULT 'weekly', -- daily, weekly, monthly
        [last_alert_sent] DATETIME2, -- When the last alert was sent
        [next_scheduled_review] DATETIME2, -- When the risk profile should be reassessed
        
        -- AI & Chatbot Integration
        [created_via_chatbot] BIT DEFAULT 0, -- Whether created through chatbot
        [last_chatbot_interaction] DATETIME2, -- Last discussion about risk with chatbot
        [chatbot_advice_delivered] NVARCHAR(MAX), -- Advice given by chatbot about risk
        
        -- Status & Tracking
        [profile_status] NVARCHAR(20) NOT NULL DEFAULT 'active', -- active, under_review, archived
        [created_by] NVARCHAR(100) DEFAULT 'self', -- self, advisor, system
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [last_full_review] DATETIME2, -- When a comprehensive review was last performed
        
        -- Constraints
        CONSTRAINT [CK_risk_profiles_risk_level] CHECK ([risk_level] IN ('conservative', 'moderate', 'aggressive')),
        CONSTRAINT [CK_risk_profiles_investment_experience] CHECK ([investment_experience] IN ('beginner', 'intermediate', 'advanced')),
        CONSTRAINT [CK_risk_profiles_stability_liquidity_volatility] 
            CHECK ([income_stability] IN ('low', 'medium', 'high') 
                   AND [liquidity_needs] IN ('low', 'medium', 'high') 
                   AND [volatility_tolerance] IN ('low', 'medium', 'high')),
        CONSTRAINT [CK_risk_profiles_investment_horizon] CHECK ([investment_horizon] IN ('short-term', 'mid-term', 'long-term')),
        CONSTRAINT [CK_risk_profiles_profile_status] CHECK ([profile_status] IN ('active', 'under_review', 'archived'))
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_risk_profiles_user_id] ON [dbo].[risk_profiles] ([user_id]);
    CREATE INDEX [idx_risk_profiles_risk_level] ON [dbo].[risk_profiles] ([risk_level]);
    CREATE INDEX [idx_risk_profiles_investment_experience] ON [dbo].[risk_profiles] ([investment_experience]);
    CREATE INDEX [idx_risk_profiles_income_stability] ON [dbo].[risk_profiles] ([income_stability]);
    CREATE INDEX [idx_risk_profiles_status] ON [dbo].[risk_profiles] ([profile_status]);
    CREATE INDEX [idx_risk_profiles_created_at] ON [dbo].[risk_profiles] ([created_at]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores user risk profiles for personalized investment recommendations, portfolio management, and AI-driven insights',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'risk_profiles';
    
    -- Add foreign key constraint (assuming users table exists)
    -- Note: Uncomment this once the users table is created
    -- ALTER TABLE [dbo].[risk_profiles] 
    -- ADD CONSTRAINT [FK_risk_profiles_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE;
END
GO

-- Create trigger to update timestamps and track changes
IF OBJECT_ID('dbo.trg_risk_profiles_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_risk_profiles_update;
GO

CREATE TRIGGER dbo.trg_risk_profiles_update
ON dbo.risk_profiles
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the updated_at timestamp
    UPDATE rp
    SET rp.updated_at = GETDATE()
    FROM dbo.risk_profiles rp
    INNER JOIN inserted i ON rp.id = i.id;
    
    -- Detect and record risk level changes
    DECLARE @risk_changed BIT = 0;
    
    -- Check if risk level has changed
    IF EXISTS (
        SELECT 1 FROM inserted i
        JOIN deleted d ON i.id = d.id
        WHERE i.risk_level <> d.risk_level
    )
    BEGIN
        SET @risk_changed = 1;
        
        -- Update the historical_risk_score JSON array
        UPDATE rp
        SET 
            historical_risk_score = 
                CASE 
                    WHEN rp.historical_risk_score IS NULL THEN 
                        '[{"date":"' + CONVERT(NVARCHAR(20), GETDATE(), 120) + '","old_level":"' + d.risk_level + '","new_level":"' + i.risk_level + '","score":' + CAST(i.risk_score AS NVARCHAR(10)) + '}]'
                    ELSE
                        JSON_MODIFY(
                            rp.historical_risk_score, 
                            'append $', 
                            JSON_QUERY('{"date":"' + CONVERT(NVARCHAR(20), GETDATE(), 120) + '","old_level":"' + d.risk_level + '","new_level":"' + i.risk_level + '","score":' + CAST(i.risk_score AS NVARCHAR(10)) + '}')
                        )
                END
        FROM dbo.risk_profiles rp
        INNER JOIN inserted i ON rp.id = i.id
        INNER JOIN deleted d ON i.id = d.id
        WHERE i.risk_level <> d.risk_level;
        
        -- Determine risk trend
        UPDATE rp
        SET 
            risk_trend = 
                CASE 
                    WHEN i.risk_score > d.risk_score THEN 'increasing'
                    WHEN i.risk_score < d.risk_score THEN 'decreasing'
                    ELSE 'stable'
                END
        FROM dbo.risk_profiles rp
        INNER JOIN inserted i ON rp.id = i.id
        INNER JOIN deleted d ON i.id = d.id
        WHERE i.risk_score <> d.risk_score;
    END
END
GO

-- Create procedure to generate a new risk profile
IF OBJECT_ID('dbo.sp_create_risk_profile', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_create_risk_profile;
GO

CREATE PROCEDURE dbo.sp_create_risk_profile
    @user_id BIGINT,
    @risk_level NVARCHAR(20),
    @risk_score INT,
    @investment_experience NVARCHAR(20),
    @income_stability NVARCHAR(20),
    @liquidity_needs NVARCHAR(20),
    @volatility_tolerance NVARCHAR(20),
    @investment_horizon NVARCHAR(20),
    @preferred_assets NVARCHAR(MAX) = NULL,
    @questionnaire_responses NVARCHAR(MAX) = NULL,
    @created_via_chatbot BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate inputs
    IF @risk_level NOT IN ('conservative', 'moderate', 'aggressive')
    BEGIN
        RAISERROR('Invalid risk level. Must be conservative, moderate, or aggressive.', 16, 1);
        RETURN;
    END
    
    IF @investment_experience NOT IN ('beginner', 'intermediate', 'advanced')
    BEGIN
        RAISERROR('Invalid investment experience. Must be beginner, intermediate, or advanced.', 16, 1);
        RETURN;
    END
    
    IF @income_stability NOT IN ('low', 'medium', 'high')
    BEGIN
        RAISERROR('Invalid income stability. Must be low, medium, or high.', 16, 1);
        RETURN;
    END
    
    IF @liquidity_needs NOT IN ('low', 'medium', 'high')
    BEGIN
        RAISERROR('Invalid liquidity needs. Must be low, medium, or high.', 16, 1);
        RETURN;
    END
    
    IF @volatility_tolerance NOT IN ('low', 'medium', 'high')
    BEGIN
        RAISERROR('Invalid volatility tolerance. Must be low, medium, or high.', 16, 1);
        RETURN;
    END
    
    IF @investment_horizon NOT IN ('short-term', 'mid-term', 'long-term')
    BEGIN
        RAISERROR('Invalid investment horizon. Must be short-term, mid-term, or long-term.', 16, 1);
        RETURN;
    END
    
    -- Generate a unique profile code
    DECLARE @profile_code NVARCHAR(20) = 'RP-' + CONVERT(NVARCHAR(20), NEWID());
    
    -- Determine suggested strategy based on risk profile
    DECLARE @suggested_strategy NVARCHAR(50);
    
    IF @risk_level = 'conservative'
    BEGIN
        IF @investment_horizon = 'short-term'
            SET @suggested_strategy = 'income';
        ELSE
            SET @suggested_strategy = 'balanced-income';
    END
    ELSE IF @risk_level = 'moderate'
    BEGIN
        IF @investment_horizon = 'short-term'
            SET @suggested_strategy = 'balanced';
        ELSE
            SET @suggested_strategy = 'growth-balanced';
    END
    ELSE -- aggressive
    BEGIN
        IF @investment_horizon = 'short-term'
            SET @suggested_strategy = 'growth';
        ELSE
            SET @suggested_strategy = 'aggressive-growth';
    END
    
    -- Calculate next scheduled review based on risk level
    DECLARE @next_scheduled_review DATETIME2;
    
    IF @risk_level = 'conservative'
        SET @next_scheduled_review = DATEADD(MONTH, 12, GETDATE()); -- Annual review
    ELSE IF @risk_level = 'moderate'
        SET @next_scheduled_review = DATEADD(MONTH, 6, GETDATE()); -- Semi-annual review
    ELSE -- aggressive
        SET @next_scheduled_review = DATEADD(MONTH, 3, GETDATE()); -- Quarterly review
    
    -- Check if user already has an active profile
    IF EXISTS (SELECT 1 FROM dbo.risk_profiles WHERE user_id = @user_id AND profile_status = 'active')
    BEGIN
        -- Archive the existing profile
        UPDATE dbo.risk_profiles
        SET 
            profile_status = 'archived',
            updated_at = GETDATE()
        WHERE 
            user_id = @user_id AND 
            profile_status = 'active';
    END
    
    -- Create new risk profile
    INSERT INTO dbo.risk_profiles (
        user_id,
        profile_code,
        risk_level,
        risk_score,
        investment_experience,
        income_stability,
        liquidity_needs,
        volatility_tolerance,
        investment_horizon,
        preferred_assets,
        suggested_strategy,
        questionnaire_responses,
        questionnaire_completion_date,
        created_via_chatbot,
        next_scheduled_review,
        historical_risk_score
    )
    VALUES (
        @user_id,
        @profile_code,
        @risk_level,
        @risk_score,
        @investment_experience,
        @income_stability,
        @liquidity_needs,
        @volatility_tolerance,
        @investment_horizon,
        @preferred_assets,
        @suggested_strategy,
        @questionnaire_responses,
        GETDATE(),
        @created_via_chatbot,
        @next_scheduled_review,
        '[{"date":"' + CONVERT(NVARCHAR(20), GETDATE(), 120) + '","level":"' + @risk_level + '","score":' + CAST(@risk_score AS NVARCHAR(10)) + '}]'
    );
    
    -- Return the newly created risk profile
    SELECT *
    FROM dbo.risk_profiles
    WHERE id = SCOPE_IDENTITY();
END
GO

-- Create procedure to find similar risk profiles
IF OBJECT_ID('dbo.sp_find_similar_risk_profiles', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_find_similar_risk_profiles;
GO

CREATE PROCEDURE dbo.sp_find_similar_risk_profiles
    @profile_id BIGINT,
    @max_results INT = 10
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the target profile
    DECLARE @target_risk_level NVARCHAR(20);
    DECLARE @target_experience NVARCHAR(20);
    DECLARE @target_horizon NVARCHAR(20);
    DECLARE @target_user_id BIGINT;
    
    SELECT 
        @target_risk_level = risk_level,
        @target_experience = investment_experience,
        @target_horizon = investment_horizon,
        @target_user_id = user_id
    FROM dbo.risk_profiles
    WHERE id = @profile_id;
    
    -- Find similar profiles (excluding the user's own profiles)
    SELECT TOP (@max_results)
        rp.*,
        CASE
            WHEN rp.risk_level = @target_risk_level THEN 30
            ELSE 0
        END +
        CASE
            WHEN rp.investment_experience = @target_experience THEN 25
            ELSE 0
        END +
        CASE
            WHEN rp.investment_horizon = @target_horizon THEN 20
            ELSE 0
        END +
        CASE
            WHEN rp.income_stability = (SELECT income_stability FROM dbo.risk_profiles WHERE id = @profile_id) THEN 10
            ELSE 0
        END +
        CASE
            WHEN rp.volatility_tolerance = (SELECT volatility_tolerance FROM dbo.risk_profiles WHERE id = @profile_id) THEN 15
            ELSE 0
        END AS similarity_score
    FROM dbo.risk_profiles rp
    WHERE 
        rp.user_id <> @target_user_id AND
        rp.profile_status = 'active'
    ORDER BY similarity_score DESC, rp.created_at DESC;
END
GO