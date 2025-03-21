-- Migration: Create Financial Goals Table
-- Description: Stores user-defined financial goals, tracks progress, and provides AI-powered insights

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[financial_goals]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[financial_goals] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [goal_name] NVARCHAR(255) NOT NULL, -- Short title of the goal
        [goal_description] NVARCHAR(MAX), -- Detailed description of the financial goal
        [goal_category] NVARCHAR(50) NOT NULL, -- Category: savings, investment, debt_payment, retirement, etc.
        [priority_level] NVARCHAR(20) NOT NULL DEFAULT 'medium', -- high, medium, low
        
        -- Financial Target Information
        [target_amount] DECIMAL(19, 4) NOT NULL, -- The total amount the user aims to reach
        [current_amount] DECIMAL(19, 4) NOT NULL DEFAULT 0, -- Amount saved/invested so far
        [currency] NVARCHAR(3) NOT NULL DEFAULT 'KES', -- Currency type (KES, USD, etc.)
        [target_date] DATE NOT NULL, -- Expected date for achieving the goal
        [progress_percentage] DECIMAL(5, 2), -- Will be calculated by trigger
        
        -- Contribution Plan
        [contribution_frequency] NVARCHAR(20) NOT NULL, -- daily, weekly, monthly, etc.
        [contribution_amount] DECIMAL(19, 4) NOT NULL, -- Recurring contribution amount
        [next_contribution_date] DATE, -- Next scheduled contribution
        [contribution_day] TINYINT, -- Day of month/week for contribution (if applicable)
        
        -- AI-Powered Insights & Risk Analysis
        [suggested_adjustments] NVARCHAR(MAX), -- AI-generated recommendations
        [risk_profile] NVARCHAR(50), -- User's financial risk profile
        [investment_strategy] NVARCHAR(50), -- conservative, moderate, aggressive
        [expected_roi] DECIMAL(5, 2), -- Expected return on investment (%)
        [ai_recommendation_updated_at] DATETIME2, -- When AI last updated recommendations
        
        -- Notifications & Reminders
        [enable_notifications] BIT DEFAULT 1, -- Whether to send reminders
        [notification_frequency] NVARCHAR(20) DEFAULT 'weekly', -- How often to send reminders
        [last_notification_sent] DATETIME2, -- Timestamp of last reminder
        
        -- M-Pesa & Payment Integration
        [mpesa_paybill_number] NVARCHAR(20), -- M-Pesa paybill for automated payments
        [mpesa_account_reference] NVARCHAR(50), -- Account reference for M-Pesa
        [external_account_id] NVARCHAR(255), -- ID if linked to bank/investment account
        [external_account_type] NVARCHAR(50), -- Type of external account (bank, brokerage, etc.)
        
        -- Status & Completion
        [goal_status] NVARCHAR(20) NOT NULL DEFAULT 'active', -- active, completed, paused, cancelled
        [completion_date] DATETIME2, -- When goal was achieved
        [completion_percentage] DECIMAL(5, 2) DEFAULT 0, -- Manually adjusted completion percentage
        [is_recurring_goal] BIT DEFAULT 0, -- Whether goal resets after completion
        
        -- Chatbot Interaction
        [created_via_chatbot] BIT DEFAULT 0, -- Whether created through PesaGuru chatbot
        [last_chatbot_interaction] DATETIME2, -- Last time user discussed this goal with chatbot
        
        -- Location Context (Kenya-specific)
        [county] NVARCHAR(50), -- Kenyan county relevant to the goal (if applicable)
        [location_context] NVARCHAR(MAX), -- Additional location information
        
        -- Timestamps
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE()
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_financial_goals_user_id] ON [dbo].[financial_goals] ([user_id]);
    CREATE INDEX [idx_financial_goals_category] ON [dbo].[financial_goals] ([goal_category]);
    CREATE INDEX [idx_financial_goals_status] ON [dbo].[financial_goals] ([goal_status]);
    CREATE INDEX [idx_financial_goals_target_date] ON [dbo].[financial_goals] ([target_date]);
    CREATE INDEX [idx_financial_goals_priority] ON [dbo].[financial_goals] ([priority_level]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores user-defined financial goals, tracks progress, and provides AI-powered insights for the PesaGuru financial advisory chatbot',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'financial_goals';
    
    -- Add foreign key constraint (assuming users table exists)
    -- Note: Uncomment this once the users table is created
    -- ALTER TABLE [dbo].[financial_goals] 
    -- ADD CONSTRAINT [FK_financial_goals_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE;
END
GO

-- Create trigger for updates
IF OBJECT_ID('dbo.trg_financial_goals_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_financial_goals_update;
GO

CREATE TRIGGER dbo.trg_financial_goals_update
ON dbo.financial_goals
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the timestamp and calculate progress percentage
    UPDATE fg
    SET 
        fg.updated_at = GETDATE(),
        fg.progress_percentage = CASE 
                                   WHEN i.target_amount > 0 
                                   THEN (i.current_amount / i.target_amount * 100) 
                                   ELSE 0 
                                 END
    FROM dbo.financial_goals fg
    INNER JOIN inserted i ON fg.id = i.id;
    
    -- Check if any goals are completed
    UPDATE fg
    SET 
        fg.goal_status = CASE 
                           WHEN fg.current_amount >= fg.target_amount AND fg.goal_status <> 'completed' 
                           THEN 'completed'
                           WHEN fg.current_amount < fg.target_amount AND fg.goal_status = 'completed' 
                           THEN 'active'
                           ELSE fg.goal_status
                         END,
        fg.completion_date = CASE 
                               WHEN fg.current_amount >= fg.target_amount AND fg.goal_status <> 'completed' 
                               THEN GETDATE()
                               WHEN fg.current_amount < fg.target_amount AND fg.goal_status = 'completed' 
                               THEN NULL
                               ELSE fg.completion_date
                             END
    FROM dbo.financial_goals fg
    INNER JOIN inserted i ON fg.id = i.id
    WHERE 
        (fg.current_amount >= fg.target_amount AND fg.goal_status <> 'completed')
        OR (fg.current_amount < fg.target_amount AND fg.goal_status = 'completed');
END
GO

-- Create trigger for inserts
IF OBJECT_ID('dbo.trg_financial_goals_insert', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_financial_goals_insert;
GO

CREATE TRIGGER dbo.trg_financial_goals_insert
ON dbo.financial_goals
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Calculate initial progress percentage
    UPDATE fg
    SET fg.progress_percentage = CASE 
                                   WHEN i.target_amount > 0 
                                   THEN (i.current_amount / i.target_amount * 100) 
                                   ELSE 0 
                                 END
    FROM dbo.financial_goals fg
    INNER JOIN inserted i ON fg.id = i.id;
END
GO

-- Create stored procedure
IF OBJECT_ID('dbo.sp_update_goal_progress', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_update_goal_progress;
GO

CREATE PROCEDURE dbo.sp_update_goal_progress
    @goal_id BIGINT,
    @new_amount DECIMAL(19, 4)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the current amount
    UPDATE dbo.financial_goals
    SET current_amount = @new_amount
    WHERE id = @goal_id;
    
    -- Return the updated goal information
    SELECT *
    FROM dbo.financial_goals
    WHERE id = @goal_id;
END
GO