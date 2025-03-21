-- Migration: Create Investment Recommendations Table
-- Description: Stores AI-generated personalized investment recommendations for PesaGuru users

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[investment_recommendations]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[investment_recommendations] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [recommendation_code] NVARCHAR(20) NOT NULL, -- Unique code for tracking this recommendation
        
        -- Investment Details
        [investment_type] NVARCHAR(50) NOT NULL, -- stocks, bonds, real_estate, mutual_funds, crypto, etc.
        [recommended_product_id] BIGINT, -- ID of the specific financial product
        [recommended_product_name] NVARCHAR(255) NOT NULL, -- Name of the recommended investment product
        [expected_return] DECIMAL(5, 2), -- Estimated return percentage (ROI)
        [expected_return_timeframe] NVARCHAR(20), -- Monthly, quarterly, yearly, 5-year
        [risk_level] NVARCHAR(20) NOT NULL, -- low, moderate, high
        [minimum_investment_amount] DECIMAL(19, 4) NOT NULL, -- Minimum amount required
        [recommended_investment_amount] DECIMAL(19, 4) NOT NULL, -- AI-suggested optimal amount
        [currency] NVARCHAR(3) NOT NULL DEFAULT 'KES', -- Currency for the investment
        
        -- User Context
        [risk_profile] NVARCHAR(50) NOT NULL, -- conservative, moderate, aggressive
        [investment_goal] NVARCHAR(100), -- retirement, education, wealth_accumulation, etc.
        [target_horizon] NVARCHAR(20) NOT NULL, -- short-term, mid-term, long-term
        [financial_goal_id] BIGINT, -- If linked to a specific user goal
        
        -- Market Analysis
        [market_conditions] NVARCHAR(MAX), -- AI-assessed market trends
        [last_market_update] DATETIME2, -- Timestamp of latest market analysis
        [investment_strategy] NVARCHAR(50), -- growth, value, income, diversified
        [market_sentiment] NVARCHAR(20), -- bullish, bearish, neutral
        [volatility_assessment] NVARCHAR(50), -- stable, fluctuating, volatile
        [related_economic_factors] NVARCHAR(MAX), -- Economic indicators affecting this investment
        
        -- AI Analysis
        [confidence_score] DECIMAL(5, 2), -- AI confidence in this recommendation (0-100)
        [recommendation_basis] NVARCHAR(MAX), -- Explanation of why this was recommended
        [alternative_recommendations] NVARCHAR(MAX), -- Other options considered
        [recommendation_source] NVARCHAR(100), -- Algorithm, model, or source of recommendation
        
        -- Kenya-Specific Factors
        [local_market_relevance] NVARCHAR(MAX), -- How this investment relates to Kenyan markets
        [mpesa_compatible] BIT DEFAULT 0, -- Whether investment can be purchased via M-Pesa
        [kenyan_tax_implications] NVARCHAR(MAX), -- Tax considerations for Kenyan investors
        
        -- Performance Tracking
        [status] NVARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, invested, declined
        [investment_date] DATETIME2, -- When user invested (if they did)
        [investment_amount] DECIMAL(19, 4), -- Actual amount user invested
        [transaction_reference] NVARCHAR(100), -- Reference code for the transaction
        [feedback_rating] TINYINT, -- User rating (1-5)
        [feedback_comments] NVARCHAR(MAX), -- User comments on this recommendation
        [actual_performance] DECIMAL(5, 2), -- Actual return percentage (if tracked)
        [outperformed_expectation] BIT, -- Whether it performed better than expected
        
        -- Display & Notification
        [recommendation_priority] TINYINT DEFAULT 5, -- Priority level for display (1-10)
        [expiration_date] DATETIME2, -- When this recommendation expires
        [has_been_viewed] BIT DEFAULT 0, -- Whether user has seen this recommendation
        [notification_sent] BIT DEFAULT 0, -- Whether user was notified
        [notification_date] DATETIME2, -- When notification was sent
        
        -- Timestamps & Tracking
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [created_via_chatbot] BIT DEFAULT 0, -- Whether created through conversation
        [last_chatbot_interaction] DATETIME2 -- Last time discussed in chatbot
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_investment_recs_user_id] ON [dbo].[investment_recommendations] ([user_id]);
    CREATE INDEX [idx_investment_recs_type] ON [dbo].[investment_recommendations] ([investment_type]);
    CREATE INDEX [idx_investment_recs_risk] ON [dbo].[investment_recommendations] ([risk_level]);
    CREATE INDEX [idx_investment_recs_status] ON [dbo].[investment_recommendations] ([status]);
    CREATE INDEX [idx_investment_recs_created] ON [dbo].[investment_recommendations] ([created_at]);
    CREATE INDEX [idx_investment_recs_product] ON [dbo].[investment_recommendations] ([recommended_product_id]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores AI-generated personalized investment recommendations for PesaGuru users based on financial goals, risk tolerance, and market conditions',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'investment_recommendations';
    
    -- Add foreign key constraint (assuming users table exists)
    -- Note: Uncomment this once the users table is created
    -- ALTER TABLE [dbo].[investment_recommendations] 
    -- ADD CONSTRAINT [FK_investment_recommendations_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE;
    
    -- Add foreign key constraint (assuming financial_goals table exists)
    -- Note: Uncomment this once the financial_goals table is created
    -- ALTER TABLE [dbo].[investment_recommendations] 
    -- ADD CONSTRAINT [FK_investment_recommendations_financial_goals] 
    -- FOREIGN KEY ([financial_goal_id]) REFERENCES [dbo].[financial_goals]([id]) ON DELETE SET NULL;
    
    -- Add foreign key constraint (assuming financial_products table exists)
    -- Note: Uncomment this once the financial_products table is created
    -- ALTER TABLE [dbo].[investment_recommendations] 
    -- ADD CONSTRAINT [FK_investment_recommendations_financial_products] 
    -- FOREIGN KEY ([recommended_product_id]) REFERENCES [dbo].[financial_products]([id]) ON DELETE SET NULL;
END
GO

-- Create trigger to update timestamps
IF OBJECT_ID('dbo.trg_investment_recommendations_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_investment_recommendations_update;
GO

CREATE TRIGGER dbo.trg_investment_recommendations_update
ON dbo.investment_recommendations
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the updated_at timestamp
    UPDATE ir
    SET ir.updated_at = GETDATE()
    FROM dbo.investment_recommendations ir
    INNER JOIN inserted i ON ir.id = i.id;
    
    -- Set investment_date when status changes to 'invested'
    UPDATE ir
    SET ir.investment_date = CASE 
                               WHEN i.status = 'invested' AND (d.status <> 'invested' OR d.status IS NULL)
                               THEN GETDATE()
                               ELSE ir.investment_date
                             END
    FROM dbo.investment_recommendations ir
    INNER JOIN inserted i ON ir.id = i.id
    INNER JOIN deleted d ON i.id = d.id
    WHERE i.status = 'invested' AND (d.status <> 'invested' OR d.status IS NULL);
END
GO

-- Create procedure to record user feedback
IF OBJECT_ID('dbo.sp_record_recommendation_feedback', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_record_recommendation_feedback;
GO

CREATE PROCEDURE dbo.sp_record_recommendation_feedback
    @recommendation_id BIGINT,
    @rating TINYINT,
    @comments NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate rating range
    IF @rating < 1 OR @rating > 5
    BEGIN
        RAISERROR('Rating must be between 1 and 5', 16, 1);
        RETURN;
    END
    
    -- Update the recommendation with feedback
    UPDATE dbo.investment_recommendations
    SET 
        feedback_rating = @rating,
        feedback_comments = @comments,
        updated_at = GETDATE()
    WHERE id = @recommendation_id;
    
    -- Return the updated recommendation
    SELECT *
    FROM dbo.investment_recommendations
    WHERE id = @recommendation_id;
END
GO