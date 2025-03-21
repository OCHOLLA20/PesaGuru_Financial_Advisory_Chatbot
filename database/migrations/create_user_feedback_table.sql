-- Migration: Create User Feedback Table
-- Description: Stores user feedback for chatbot interactions, investment recommendations, and platform experience

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[user_feedback]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[user_feedback] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [feedback_code] NVARCHAR(20) NOT NULL, -- Unique reference code for the feedback
        
        -- Related Entity References (optional)
        [chatbot_conversation_id] BIGINT, -- Reference to conversation history
        [recommendation_id] BIGINT, -- Reference to investment recommendation
        [transaction_id] BIGINT, -- Reference to transaction if feedback is about a specific transaction
        [portfolio_id] BIGINT, -- Reference to portfolio if applicable
        
        -- Feedback Content
        [feedback_type] NVARCHAR(50) NOT NULL, -- chatbot, investment_advice, transactions, UI/UX, general
        [feedback_subtype] NVARCHAR(50), -- More specific categorization
        [rating] INT NOT NULL, -- User rating (1-5)
        [comments] NVARCHAR(MAX), -- Textual feedback
        [source_page] NVARCHAR(100), -- Where the feedback was submitted
        [source_feature] NVARCHAR(100), -- Specific feature the feedback relates to
        [source_device] NVARCHAR(50), -- mobile, desktop, tablet
        [submitted_via] NVARCHAR(50) DEFAULT 'web', -- web, mobile_app, chatbot, email
        
        -- Feature-Specific Fields
        [feature_ease_of_use] INT, -- 1-5 rating for ease of use
        [feature_usefulness] INT, -- 1-5 rating for usefulness
        [feature_reliability] INT, -- 1-5 rating for reliability
        [feature_performance] INT, -- 1-5 rating for performance
        [feature_accuracy] INT, -- 1-5 rating for accuracy of information
        
        -- AI Sentiment & Insights
        [sentiment_score] DECIMAL(5, 2), -- AI-generated sentiment score (-1 to 1)
        [sentiment_categories] NVARCHAR(MAX), -- JSON array of detected sentiment categories
        [key_phrases] NVARCHAR(MAX), -- JSON array of key phrases extracted
        [ai_suggested_improvement] NVARCHAR(MAX), -- AI-driven suggestions for enhancement
        [feedback_priority] INT, -- AI-calculated priority (1-10)
        [feedback_impact] NVARCHAR(20), -- low, medium, high - estimated impact on UX
        
        -- Follow-Up & Resolution
        [requires_follow_up] BIT NOT NULL DEFAULT 0, -- Flag for manual intervention
        [follow_up_assigned_to] NVARCHAR(100), -- Team member responsible
        [follow_up_status] NVARCHAR(20) DEFAULT 'pending', -- pending, resolved, in_progress
        [follow_up_priority] NVARCHAR(20) DEFAULT 'normal', -- low, normal, high, critical
        [admin_notes] NVARCHAR(MAX), -- Comments from support team
        [resolution_details] NVARCHAR(MAX), -- How the issue was resolved
        [resolution_date] DATETIME2, -- When the issue was resolved
        [user_satisfaction_with_resolution] INT, -- 1-5 rating of resolution satisfaction
        
        -- Alert & Notification
        [alert_sent] BIT DEFAULT 0, -- Whether an alert was sent for this feedback
        [alert_sent_date] DATETIME2, -- When the alert was sent
        [alert_recipients] NVARCHAR(MAX), -- JSON array of who received alerts
        
        -- Tracking & Implementation
        [feature_request_status] NVARCHAR(20), -- new, under_review, planned, implemented, rejected
        [implemented_in_version] NVARCHAR(20), -- Version where feedback was addressed
        [implementation_date] DATETIME2, -- When the feedback was implemented
        
        -- Kenya-Specific Feedback
        [mpesa_related] BIT DEFAULT 0, -- Whether feedback relates to M-Pesa integration
        [local_market_related] BIT DEFAULT 0, -- Whether feedback relates to Kenyan market features
        [language_preference_issue] BIT DEFAULT 0, -- Related to language settings (e.g., Swahili support)
        
        -- Timestamps
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT [CK_user_feedback_feedback_type] CHECK ([feedback_type] IN ('chatbot', 'investment_advice', 'transactions', 'UI/UX', 'general')),
        CONSTRAINT [CK_user_feedback_rating] CHECK ([rating] BETWEEN 1 AND 5),
        CONSTRAINT [CK_user_feedback_follow_up_status] CHECK ([follow_up_status] IN ('pending', 'in_progress', 'resolved'))
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_user_feedback_user_id] ON [dbo].[user_feedback] ([user_id]);
    CREATE INDEX [idx_user_feedback_type] ON [dbo].[user_feedback] ([feedback_type]);
    CREATE INDEX [idx_user_feedback_rating] ON [dbo].[user_feedback] ([rating]);
    CREATE INDEX [idx_user_feedback_follow_up] ON [dbo].[user_feedback] ([follow_up_status]) WHERE [requires_follow_up] = 1;
    CREATE INDEX [idx_user_feedback_created] ON [dbo].[user_feedback] ([created_at]);
    CREATE INDEX [idx_user_feedback_sentiment] ON [dbo].[user_feedback] ([sentiment_score]);
    CREATE INDEX [idx_user_feedback_conversation] ON [dbo].[user_feedback] ([chatbot_conversation_id]) WHERE [chatbot_conversation_id] IS NOT NULL;
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores user feedback for chatbot interactions, investment recommendations, and platform experience for the PesaGuru financial advisory chatbot',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'user_feedback';
    
    -- Add foreign key constraint (assuming users table exists)
    -- Note: Uncomment this once the users table is created
    -- ALTER TABLE [dbo].[user_feedback] 
    -- ADD CONSTRAINT [FK_user_feedback_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE;
END
GO

-- Create trigger to update timestamps and send alerts
IF OBJECT_ID('dbo.trg_user_feedback_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_user_feedback_update;
GO

CREATE TRIGGER dbo.trg_user_feedback_update
ON dbo.user_feedback
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update timestamps for updated records
    UPDATE uf
    SET uf.updated_at = GETDATE()
    FROM dbo.user_feedback uf
    INNER JOIN inserted i ON uf.id = i.id
    WHERE EXISTS (SELECT 1 FROM deleted d WHERE d.id = i.id); -- Only for updates, not inserts
    
    -- Auto-detect if follow-up is required based on rating and sentiment
    UPDATE uf
    SET 
        uf.requires_follow_up = 
            CASE 
                -- Negative rating (1-2) with comments
                WHEN i.rating <= 2 AND i.comments IS NOT NULL THEN 1
                -- Very negative sentiment
                WHEN i.sentiment_score <= -0.5 THEN 1
                -- Explicit feature request
                WHEN i.feature_request_status = 'new' THEN 1
                -- Keep existing value for updates
                WHEN EXISTS (SELECT 1 FROM deleted d WHERE d.id = i.id) THEN uf.requires_follow_up
                ELSE 0
            END,
        uf.follow_up_priority = 
            CASE
                -- Critical for very negative ratings with comments
                WHEN i.rating = 1 AND i.comments IS NOT NULL THEN 'critical'
                -- High for rating 2 or very negative sentiment
                WHEN (i.rating = 2 AND i.comments IS NOT NULL) OR i.sentiment_score <= -0.7 THEN 'high'
                -- Normal for rating 3 with negative sentiment
                WHEN i.rating = 3 AND i.sentiment_score < 0 THEN 'normal'
                -- Low for everything else requiring follow-up
                WHEN uf.requires_follow_up = 1 THEN 'low'
                -- Keep existing value for updates
                WHEN EXISTS (SELECT 1 FROM deleted d WHERE d.id = i.id) THEN uf.follow_up_priority
                ELSE 'normal'
            END
    FROM dbo.user_feedback uf
    INNER JOIN inserted i ON uf.id = i.id;
    
    -- Mark feedback as needing alerts for negative feedback or high priority issues
    UPDATE uf
    SET 
        uf.alert_sent = 0
    FROM dbo.user_feedback uf
    INNER JOIN inserted i ON uf.id = i.id
    WHERE 
        (i.rating <= 2 OR i.sentiment_score <= -0.5 OR i.follow_up_priority IN ('high', 'critical'))
        AND (NOT EXISTS (SELECT 1 FROM deleted d WHERE d.id = i.id) OR uf.alert_sent = 0); -- Only for new records or if alert not already sent
END
GO

-- Create procedure to submit new feedback
IF OBJECT_ID('dbo.sp_submit_user_feedback', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_submit_user_feedback;
GO

CREATE PROCEDURE dbo.sp_submit_user_feedback
    @user_id BIGINT,
    @feedback_type NVARCHAR(50),
    @rating INT,
    @comments NVARCHAR(MAX) = NULL,
    @source_page NVARCHAR(100) = NULL,
    @chatbot_conversation_id BIGINT = NULL,
    @recommendation_id BIGINT = NULL,
    @transaction_id BIGINT = NULL,
    @sentiment_score DECIMAL(5, 2) = NULL,
    @submitted_via NVARCHAR(50) = 'web'
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate inputs
    IF @feedback_type NOT IN ('chatbot', 'investment_advice', 'transactions', 'UI/UX', 'general')
    BEGIN
        RAISERROR('Invalid feedback type. Must be one of: chatbot, investment_advice, transactions, UI/UX, general.', 16, 1);
        RETURN;
    END
    
    IF @rating < 1 OR @rating > 5
    BEGIN
        RAISERROR('Invalid rating. Must be between 1 and 5.', 16, 1);
        RETURN;
    END
    
    -- Generate a unique feedback code
    DECLARE @feedback_code NVARCHAR(20) = 'FB-' + CONVERT(NVARCHAR(20), NEWID());
    
    -- Set default sentiment score if not provided
    IF @sentiment_score IS NULL
    BEGIN
        -- Simple heuristic based on rating
        SET @sentiment_score = (@rating - 3) * 0.5; -- Maps 1-5 to -1 to 1
    END
    
    -- Auto-detect if feedback is related to M-Pesa
    DECLARE @mpesa_related BIT = 0;
    IF @comments IS NOT NULL AND (
        @comments LIKE '%mpesa%' OR 
        @comments LIKE '%m-pesa%' OR 
        @comments LIKE '%mobile money%' OR
        @comments LIKE '%transaction failed%'
    )
    BEGIN
        SET @mpesa_related = 1;
    END
    
    -- Auto-detect if feedback is related to local markets
    DECLARE @local_market_related BIT = 0;
    IF @comments IS NOT NULL AND (
        @comments LIKE '%nse%' OR 
        @comments LIKE '%nairobi%' OR 
        @comments LIKE '%kenyan%' OR
        @comments LIKE '%local stock%'
    )
    BEGIN
        SET @local_market_related = 1;
    END
    
    -- Auto-detect if feedback is related to language preferences
    DECLARE @language_preference_issue BIT = 0;
    IF @comments IS NOT NULL AND (
        @comments LIKE '%swahili%' OR 
        @comments LIKE '%language%' OR 
        @comments LIKE '%translate%' OR
        @comments LIKE '%english%'
    )
    BEGIN
        SET @language_preference_issue = 1;
    END
    
    -- Insert feedback
    INSERT INTO dbo.user_feedback (
        user_id,
        feedback_code,
        feedback_type,
        rating,
        comments,
        source_page,
        chatbot_conversation_id,
        recommendation_id,
        transaction_id,
        sentiment_score,
        submitted_via,
        mpesa_related,
        local_market_related,
        language_preference_issue
    )
    VALUES (
        @user_id,
        @feedback_code,
        @feedback_type,
        @rating,
        @comments,
        @source_page,
        @chatbot_conversation_id,
        @recommendation_id,
        @transaction_id,
        @sentiment_score,
        @submitted_via,
        @mpesa_related,
        @local_market_related,
        @language_preference_issue
    );
    
    -- Return the newly created feedback
    SELECT *
    FROM dbo.user_feedback
    WHERE id = SCOPE_IDENTITY();
END
GO

-- Create procedure to get recent feedback trends
IF OBJECT_ID('dbo.sp_get_feedback_trends', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_get_feedback_trends;
GO

CREATE PROCEDURE dbo.sp_get_feedback_trends
    @days_back INT = 30,
    @feedback_type NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Set start date
    DECLARE @start_date DATETIME2 = DATEADD(DAY, -@days_back, GETDATE());
    
    -- Overall trends
    SELECT
        CONVERT(DATE, created_at) AS feedback_date,
        feedback_type,
        COUNT(*) AS feedback_count,
        AVG(CAST(rating AS FLOAT)) AS avg_rating,
        AVG(sentiment_score) AS avg_sentiment,
        SUM(CASE WHEN rating <= 2 THEN 1 ELSE 0 END) AS negative_count,
        SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) AS positive_count
    FROM
        dbo.user_feedback
    WHERE
        created_at >= @start_date
        AND (@feedback_type IS NULL OR feedback_type = @feedback_type)
    GROUP BY
        CONVERT(DATE, created_at),
        feedback_type
    ORDER BY
        feedback_date DESC,
        feedback_type;
    
    -- Trending issues (most common low ratings)
    SELECT TOP 10
        source_feature,
        feedback_type,
        COUNT(*) AS issue_count,
        AVG(CAST(rating AS FLOAT)) AS avg_rating
    FROM
        dbo.user_feedback
    WHERE
        created_at >= @start_date
        AND rating <= 3
        AND source_feature IS NOT NULL
        AND (@feedback_type IS NULL OR feedback_type = @feedback_type)
    GROUP BY
        source_feature,
        feedback_type
    ORDER BY
        issue_count DESC,
        avg_rating ASC;
    
    -- Improvement trends (compare current period to previous period)
    SELECT
        feedback_type,
        AVG(CASE WHEN created_at >= DATEADD(DAY, -@days_back/2, GETDATE()) THEN CAST(rating AS FLOAT) ELSE NULL END) AS current_period_avg,
        AVG(CASE WHEN created_at < DATEADD(DAY, -@days_back/2, GETDATE()) AND created_at >= @start_date THEN CAST(rating AS FLOAT) ELSE NULL END) AS previous_period_avg,
        AVG(CASE WHEN created_at >= DATEADD(DAY, -@days_back/2, GETDATE()) THEN CAST(rating AS FLOAT) ELSE NULL END) - 
        AVG(CASE WHEN created_at < DATEADD(DAY, -@days_back/2, GETDATE()) AND created_at >= @start_date THEN CAST(rating AS FLOAT) ELSE NULL END) AS rating_change
    FROM
        dbo.user_feedback
    WHERE
        created_at >= @start_date
        AND (@feedback_type IS NULL OR feedback_type = @feedback_type)
    GROUP BY
        feedback_type
    ORDER BY
        feedback_type;
END
GO

-- Create procedure to process feedback alerts
IF OBJECT_ID('dbo.sp_process_feedback_alerts', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_process_feedback_alerts;
GO

CREATE PROCEDURE dbo.sp_process_feedback_alerts
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get feedback needing alerts
    SELECT
        id,
        user_id,
        feedback_type,
        rating,
        comments,
        sentiment_score,
        follow_up_priority
    FROM
        dbo.user_feedback
    WHERE
        alert_sent = 0
        AND (
            rating <= 2 
            OR sentiment_score <= -0.5 
            OR follow_up_priority IN ('high', 'critical')
        );
    
    -- In a real implementation, this procedure would:
    -- 1. Send emails/notifications to appropriate team members
    -- 2. Log the alert in a notifications table
    -- 3. Update the feedback records to mark alerts as sent
    
    -- For this migration, we'll just mark alerts as processed
    UPDATE dbo.user_feedback
    SET 
        alert_sent = 1,
        alert_sent_date = GETDATE(),
        alert_recipients = '["support@pesaguru.com", "feedback@pesaguru.com"]'
    WHERE
        alert_sent = 0
        AND (
            rating <= 2 
            OR sentiment_score <= -0.5 
            OR follow_up_priority IN ('high', 'critical')
        );
    
    -- Return count of processed alerts
    SELECT @@ROWCOUNT AS alerts_processed;
END
GO