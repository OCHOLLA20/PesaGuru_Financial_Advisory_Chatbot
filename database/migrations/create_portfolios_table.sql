-- Migration: Create Portfolios Table
-- Description: Stores user investment portfolios, tracking financial assets, performance, and risk levels

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[portfolios]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[portfolios] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [portfolio_code] NVARCHAR(20) NOT NULL, -- Unique code for tracking this portfolio
        
        -- Portfolio Metadata
        [portfolio_name] NVARCHAR(255) NOT NULL, -- User-defined name (e.g., "Retirement Fund")
        [portfolio_type] NVARCHAR(50) NOT NULL, -- Type: stocks, mutual_funds, crypto, real_estate, bonds, mixed
        [risk_profile] NVARCHAR(50) NOT NULL, -- conservative, moderate, aggressive
        [investment_goal] NVARCHAR(100), -- wealth_accumulation, retirement, education_fund, etc.
        [target_amount] DECIMAL(19, 4), -- Target amount to achieve
        [target_date] DATE, -- Target date to achieve goal
        [currency] NVARCHAR(3) NOT NULL DEFAULT 'KES', -- Portfolio currency (KES, USD, etc.)
        [description] NVARCHAR(MAX), -- User description of portfolio purpose
        
        -- Portfolio Composition
        [total_invested] DECIMAL(19, 4) NOT NULL DEFAULT 0, -- Total amount invested
        [current_value] DECIMAL(19, 4) NOT NULL DEFAULT 0, -- Current portfolio value
        [profit_loss] DECIMAL(19, 4) NOT NULL DEFAULT 0, -- Difference between current_value and total_invested
        [roi_percentage] DECIMAL(10, 6) NOT NULL DEFAULT 0, -- Return on investment percentage
        [market_exposure] NVARCHAR(MAX), -- JSON field storing asset allocation percentages
        [asset_count] INT NOT NULL DEFAULT 0, -- Number of different assets in portfolio
        [last_rebalancing_date] DATETIME2, -- Last time assets were rebalanced
        [rebalancing_frequency] NVARCHAR(20), -- monthly, quarterly, annually
        
        -- Performance Metrics & AI Insights
        [expected_return] DECIMAL(10, 6), -- AI-predicted return percentage
        [volatility_index] DECIMAL(10, 6), -- AI-calculated risk level
        [investment_strategy] NVARCHAR(50), -- growth, income, balanced
        [market_sentiment] DECIMAL(5, 2), -- AI-driven sentiment score (-1 bearish to 1 bullish)
        [diversification_score] DECIMAL(5, 2), -- How well diversified (1-10)
        [recommended_actions] NVARCHAR(MAX), -- AI-suggested portfolio adjustments
        [risk_assessment] NVARCHAR(MAX), -- Detailed risk analysis
        [last_ai_analysis] DATETIME2, -- When AI last analyzed the portfolio
        
        -- Historical Performance
        [inception_date] DATE NOT NULL, -- When the portfolio was started
        [best_performing_asset] NVARCHAR(100), -- Current best performer
        [worst_performing_asset] NVARCHAR(100), -- Current worst performer
        [highest_value] DECIMAL(19, 4), -- Historical highest portfolio value
        [highest_value_date] DATETIME2, -- When highest value was reached
        [performance_history] NVARCHAR(MAX), -- JSON field with historical valuations
        [monthly_contribution] DECIMAL(19, 4), -- Regular monthly contribution amount
        
        -- Kenya-Specific Features
        [nse_exposure_percentage] DECIMAL(5, 2) DEFAULT 0, -- Percentage in Nairobi Securities Exchange
        [foreign_exposure_percentage] DECIMAL(5, 2) DEFAULT 0, -- Percentage in foreign markets
        [local_tax_implications] NVARCHAR(MAX), -- Tax considerations for Kenyan investors
        
        -- Portfolio Status
        [status] NVARCHAR(20) NOT NULL DEFAULT 'active', -- active, closed, paused
        [visibility] NVARCHAR(20) NOT NULL DEFAULT 'private', -- private, shared, public
        [linked_mpesa_account] BIT NOT NULL DEFAULT 0, -- Whether linked to M-Pesa
        [mpesa_paybill_number] NVARCHAR(20), -- M-Pesa paybill for contributions
        [linked_bank_account] NVARCHAR(255), -- Reference to connected bank account
        [auto_invest_enabled] BIT NOT NULL DEFAULT 0, -- Whether auto-investing is enabled
        [next_auto_invest_date] DATETIME2, -- When next auto-investment occurs
        
        -- Chatbot Interaction
        [created_via_chatbot] BIT NOT NULL DEFAULT 0, -- Whether created through PesaGuru chatbot
        [last_chatbot_interaction] DATETIME2, -- Last time discussed with chatbot
        [chatbot_advice_followed] DECIMAL(5, 2) DEFAULT 0, -- Percentage of advice followed (0-100)
        
        -- Notifications & Alerts
        [alert_threshold_gain] DECIMAL(5, 2), -- Alert when gain exceeds this percentage
        [alert_threshold_loss] DECIMAL(5, 2), -- Alert when loss exceeds this percentage
        [enable_performance_alerts] BIT NOT NULL DEFAULT 1, -- Whether to send performance alerts
        [enable_rebalancing_alerts] BIT NOT NULL DEFAULT 1, -- Whether to send rebalancing alerts
        
        -- Timestamps
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE(),
        [last_valuation_date] DATETIME2 NOT NULL DEFAULT GETDATE() -- When last valued
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_portfolios_user_id] ON [dbo].[portfolios] ([user_id]);
    CREATE INDEX [idx_portfolios_type] ON [dbo].[portfolios] ([portfolio_type]);
    CREATE INDEX [idx_portfolios_risk] ON [dbo].[portfolios] ([risk_profile]);
    CREATE INDEX [idx_portfolios_status] ON [dbo].[portfolios] ([status]);
    CREATE INDEX [idx_portfolios_created] ON [dbo].[portfolios] ([created_at]);
    CREATE INDEX [idx_portfolios_inception] ON [dbo].[portfolios] ([inception_date]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores user investment portfolios, tracking financial assets, performance, and risk levels for the PesaGuru financial advisory chatbot',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'portfolios';
    
    -- Add foreign key constraint (assuming users table exists)
    -- Note: Uncomment this once the users table is created
    -- ALTER TABLE [dbo].[portfolios] 
    -- ADD CONSTRAINT [FK_portfolios_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]) ON DELETE CASCADE;
END
GO

-- Create trigger to update timestamps and calculated fields
IF OBJECT_ID('dbo.trg_portfolios_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_portfolios_update;
GO

CREATE TRIGGER dbo.trg_portfolios_update
ON dbo.portfolios
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the updated_at timestamp
    UPDATE p
    SET 
        p.updated_at = GETDATE(),
        -- Calculate profit/loss based on current value and total invested
        p.profit_loss = p.current_value - p.total_invested,
        -- Calculate ROI percentage if total_invested > 0
        p.roi_percentage = CASE 
                            WHEN p.total_invested > 0 
                            THEN ((p.current_value - p.total_invested) / p.total_invested) * 100
                            ELSE 0
                          END
    FROM dbo.portfolios p
    INNER JOIN inserted i ON p.id = i.id;
    
    -- Update highest_value if current_value is higher
    UPDATE p
    SET 
        p.highest_value = p.current_value,
        p.highest_value_date = GETDATE()
    FROM dbo.portfolios p
    INNER JOIN inserted i ON p.id = i.id
    WHERE p.current_value > ISNULL(p.highest_value, 0);
END
GO

-- Create procedure to update portfolio valuation
IF OBJECT_ID('dbo.sp_update_portfolio_valuation', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_update_portfolio_valuation;
GO

CREATE PROCEDURE dbo.sp_update_portfolio_valuation
    @portfolio_id BIGINT,
    @current_value DECIMAL(19, 4),
    @asset_details NVARCHAR(MAX) = NULL -- JSON with asset allocations
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the portfolio with new valuation
    UPDATE dbo.portfolios
    SET 
        current_value = @current_value,
        market_exposure = COALESCE(@asset_details, market_exposure),
        last_valuation_date = GETDATE()
    WHERE id = @portfolio_id;
    
    -- Return the updated portfolio
    SELECT *
    FROM dbo.portfolios
    WHERE id = @portfolio_id;
END
GO

-- Create procedure to record portfolio contribution/withdrawal
IF OBJECT_ID('dbo.sp_record_portfolio_transaction', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_record_portfolio_transaction;
GO

CREATE PROCEDURE dbo.sp_record_portfolio_transaction
    @portfolio_id BIGINT,
    @transaction_type NVARCHAR(20), -- 'contribution' or 'withdrawal'
    @amount DECIMAL(19, 4),
    @transaction_date DATETIME2 = NULL,
    @transaction_reference NVARCHAR(100) = NULL,
    @notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default transaction date to current time if not provided
    IF @transaction_date IS NULL
        SET @transaction_date = GETDATE();
    
    -- Update portfolio based on transaction type
    IF @transaction_type = 'contribution'
    BEGIN
        UPDATE dbo.portfolios
        SET 
            total_invested = total_invested + @amount
        WHERE id = @portfolio_id;
    END
    ELSE IF @transaction_type = 'withdrawal'
    BEGIN
        UPDATE dbo.portfolios
        SET 
            total_invested = total_invested - @amount
        WHERE id = @portfolio_id;
    END
    ELSE
    BEGIN
        RAISERROR('Invalid transaction type. Must be "contribution" or "withdrawal".', 16, 1);
        RETURN;
    END
    
    -- Note: In a real implementation, we would also record this transaction
    -- in a separate portfolio_transactions table for historical tracking
    
    -- Return the updated portfolio
    SELECT *
    FROM dbo.portfolios
    WHERE id = @portfolio_id;
END
GO