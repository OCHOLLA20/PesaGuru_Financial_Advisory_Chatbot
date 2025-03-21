-- Migration: Create Transactions Table
-- Description: Stores financial transactions including investments, deposits, withdrawals, loan payments, and transfers

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[transactions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[transactions] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [user_id] BIGINT NOT NULL, -- Foreign key to users table
        [portfolio_id] BIGINT, -- Foreign key to portfolios table (optional)
        [financial_goal_id] BIGINT, -- Foreign key to financial_goals table (optional)
        [transaction_code] NVARCHAR(50) NOT NULL, -- Unique transaction reference code
        
        -- Transaction Details
        [transaction_type] NVARCHAR(50) NOT NULL, -- investment, deposit, withdrawal, loan_payment, transfer
        [transaction_subtype] NVARCHAR(50), -- buy, sell, interest_payment, dividend, etc.
        [amount] DECIMAL(19, 4) NOT NULL, -- Monetary value of the transaction
        [currency] NVARCHAR(3) NOT NULL DEFAULT 'KES', -- Currency used (KES, USD, etc.)
        [exchange_rate] DECIMAL(19, 6), -- Exchange rate if currency conversion was involved
        [amount_in_kes] DECIMAL(19, 4), -- Amount converted to KES (for reporting)
        [transaction_fee] DECIMAL(19, 4), -- Fee charged for the transaction
        [payment_method] NVARCHAR(50), -- M-Pesa, bank_transfer, credit_card, crypto_wallet
        [transaction_status] NVARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, completed, failed, reversed
        [reference_number] NVARCHAR(100), -- Transaction reference from payment provider
        [transaction_notes] NVARCHAR(MAX), -- Additional details
        
        -- M-Pesa & Bank Integrations
        [mpesa_transaction_id] NVARCHAR(50), -- M-Pesa transaction reference
        [mpesa_phone_number] NVARCHAR(20), -- Phone number used for M-Pesa
        [mpesa_receipt_number] NVARCHAR(50), -- M-Pesa receipt number
        [bank_transaction_id] NVARCHAR(50), -- Bank reference number
        [bank_account_number] NVARCHAR(50), -- Bank account number
        [bank_name] NVARCHAR(100), -- Name of the bank
        [bank_branch] NVARCHAR(100), -- Bank branch
        
        -- Investment-Specific Data
        [asset_type] NVARCHAR(50), -- stocks, bonds, crypto, mutual_funds
        [asset_symbol] NVARCHAR(20), -- Ticker symbol (e.g., TSLA, BTC-USD)
        [asset_name] NVARCHAR(255), -- Full name of the asset
        [units_transacted] DECIMAL(19, 6), -- Number of shares/units involved
        [unit_price] DECIMAL(19, 6), -- Price per unit at transaction time
        [total_value] DECIMAL(19, 4), -- Total value of investment (units * price)
        [transaction_direction] NVARCHAR(10), -- in (buy/deposit) or out (sell/withdraw)
        
        -- Loan-Specific Data
        [loan_id] BIGINT, -- Associated loan if this is a loan payment
        [loan_payment_type] NVARCHAR(20), -- principal, interest, fees
        [remaining_balance] DECIMAL(19, 4), -- Remaining loan balance after payment
        
        -- Approval & Verification
        [requires_approval] BIT NOT NULL DEFAULT 0, -- Whether transaction needs manual approval
        [approved_by] NVARCHAR(100), -- Who approved the transaction
        [approval_date] DATETIME2, -- When the transaction was approved
        [verification_attempts] INT DEFAULT 0, -- Number of verification attempts
        [verification_status] NVARCHAR(20), -- verified, unverified, verification_failed
        
        -- Tax & Compliance
        [tax_applicable] BIT NOT NULL DEFAULT 0, -- Whether the transaction is taxable
        [tax_amount] DECIMAL(19, 4), -- Amount of tax applied
        [tax_type] NVARCHAR(50), -- Type of tax (capital_gains, income, etc.)
        [tax_reference] NVARCHAR(50), -- Tax reference number
        
        -- Related Parties
        [merchant_name] NVARCHAR(255), -- Merchant or counterparty name
        [merchant_category] NVARCHAR(100), -- Category of merchant
        [receiver_account] NVARCHAR(100), -- Destination account for transfers
        [sender_account] NVARCHAR(100), -- Source account for incoming transfers
        
        -- AI & Chatbot Integration
        [created_via_chatbot] BIT NOT NULL DEFAULT 0, -- Whether initiated via chatbot
        [ai_recommendation_id] BIGINT, -- If transaction was based on AI recommendation
        [ai_confidence_score] DECIMAL(5, 2), -- AI confidence in this transaction (0-100)
        
        -- Location & Device Data
        [ip_address] NVARCHAR(45), -- IP address used for transaction
        [device_id] NVARCHAR(100), -- Device identifier
        [location] NVARCHAR(255), -- Location of transaction
        [county] NVARCHAR(50), -- Kenyan county (if applicable)
        
        -- Timestamps
        [transaction_date] DATETIME2 NOT NULL, -- When the transaction occurred
        [transaction_initiated_at] DATETIME2 NOT NULL, -- When the transaction was initiated
        [transaction_completed_at] DATETIME2, -- When the transaction was completed
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(), -- When the record was created
        [updated_at] DATETIME2 NOT NULL DEFAULT GETDATE() -- When the record was last updated
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_transactions_user_id] ON [dbo].[transactions] ([user_id]);
    CREATE INDEX [idx_transactions_portfolio_id] ON [dbo].[transactions] ([portfolio_id]) WHERE [portfolio_id] IS NOT NULL;
    CREATE INDEX [idx_transactions_type] ON [dbo].[transactions] ([transaction_type]);
    CREATE INDEX [idx_transactions_status] ON [dbo].[transactions] ([transaction_status]);
    CREATE INDEX [idx_transactions_date] ON [dbo].[transactions] ([transaction_date]);
    CREATE INDEX [idx_transactions_mpesa] ON [dbo].[transactions] ([mpesa_transaction_id]) WHERE [mpesa_transaction_id] IS NOT NULL;
    CREATE INDEX [idx_transactions_asset] ON [dbo].[transactions] ([asset_symbol], [asset_type]) WHERE [asset_symbol] IS NOT NULL;
    CREATE INDEX [idx_transactions_payment_method] ON [dbo].[transactions] ([payment_method]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Stores all financial transactions including investments, deposits, withdrawals, loan payments, and transfers for the PesaGuru financial advisory chatbot',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'transactions';
    
    -- Add foreign key constraints (assuming related tables exist)
    -- Note: Uncomment these once the respective tables are created
    -- ALTER TABLE [dbo].[transactions] 
    -- ADD CONSTRAINT [FK_transactions_users] 
    -- FOREIGN KEY ([user_id]) REFERENCES [dbo].[users]([id]);
    
    -- ALTER TABLE [dbo].[transactions] 
    -- ADD CONSTRAINT [FK_transactions_portfolios] 
    -- FOREIGN KEY ([portfolio_id]) REFERENCES [dbo].[portfolios]([id]);
    
    -- ALTER TABLE [dbo].[transactions] 
    -- ADD CONSTRAINT [FK_transactions_financial_goals] 
    -- FOREIGN KEY ([financial_goal_id]) REFERENCES [dbo].[financial_goals]([id]);
END
GO

-- Create trigger to update timestamps
IF OBJECT_ID('dbo.trg_transactions_update', 'TR') IS NOT NULL
    DROP TRIGGER dbo.trg_transactions_update;
GO

CREATE TRIGGER dbo.trg_transactions_update
ON dbo.transactions
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Update the updated_at timestamp
    UPDATE t
    SET t.updated_at = GETDATE()
    FROM dbo.transactions t
    INNER JOIN inserted i ON t.id = i.id;
    
    -- Set completion timestamp if status changes to completed
    UPDATE t
    SET t.transaction_completed_at = CASE 
                                       WHEN i.transaction_status = 'completed' AND 
                                            (d.transaction_status <> 'completed' OR d.transaction_status IS NULL)
                                       THEN GETDATE()
                                       ELSE t.transaction_completed_at
                                     END
    FROM dbo.transactions t
    INNER JOIN inserted i ON t.id = i.id
    INNER JOIN deleted d ON i.id = d.id
    WHERE i.transaction_status = 'completed' AND (d.transaction_status <> 'completed' OR d.transaction_status IS NULL);
END
GO

-- Create procedure to record a new transaction
IF OBJECT_ID('dbo.sp_record_transaction', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_record_transaction;
GO

CREATE PROCEDURE dbo.sp_record_transaction
    @user_id BIGINT,
    @transaction_type NVARCHAR(50),
    @amount DECIMAL(19, 4),
    @currency NVARCHAR(3) = 'KES',
    @payment_method NVARCHAR(50) = NULL,
    @transaction_notes NVARCHAR(MAX) = NULL,
    @portfolio_id BIGINT = NULL,
    @asset_symbol NVARCHAR(20) = NULL,
    @asset_type NVARCHAR(50) = NULL,
    @units_transacted DECIMAL(19, 6) = NULL,
    @unit_price DECIMAL(19, 6) = NULL,
    @mpesa_transaction_id NVARCHAR(50) = NULL,
    @mpesa_phone_number NVARCHAR(20) = NULL,
    @bank_transaction_id NVARCHAR(50) = NULL,
    @reference_number NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Generate a unique transaction code
    DECLARE @transaction_code NVARCHAR(50) = 'TXN-' + CONVERT(NVARCHAR(20), NEWID());
    
    -- Calculate total value for investment transactions
    DECLARE @total_value DECIMAL(19, 4) = NULL;
    IF @units_transacted IS NOT NULL AND @unit_price IS NOT NULL
        SET @total_value = @units_transacted * @unit_price;
    
    -- Determine transaction direction
    DECLARE @transaction_direction NVARCHAR(10);
    IF @transaction_type IN ('deposit', 'loan_disbursement') OR
       (@transaction_type = 'investment' AND @units_transacted > 0)
        SET @transaction_direction = 'in';
    ELSE
        SET @transaction_direction = 'out';
    
    -- Insert the transaction
    INSERT INTO dbo.transactions (
        user_id,
        portfolio_id,
        transaction_code,
        transaction_type,
        amount,
        currency,
        payment_method,
        transaction_notes,
        transaction_status,
        asset_symbol,
        asset_type,
        units_transacted,
        unit_price,
        total_value,
        transaction_direction,
        mpesa_transaction_id,
        mpesa_phone_number,
        bank_transaction_id,
        reference_number,
        transaction_date,
        transaction_initiated_at
    )
    VALUES (
        @user_id,
        @portfolio_id,
        @transaction_code,
        @transaction_type,
        @amount,
        @currency,
        @payment_method,
        @transaction_notes,
        'pending', -- Default status
        @asset_symbol,
        @asset_type,
        @units_transacted,
        @unit_price,
        @total_value,
        @transaction_direction,
        @mpesa_transaction_id,
        @mpesa_phone_number,
        @bank_transaction_id,
        @reference_number,
        GETDATE(), -- Current timestamp for transaction date
        GETDATE()  -- Transaction initiated now
    );
    
    -- Return the newly created transaction
    SELECT *
    FROM dbo.transactions
    WHERE id = SCOPE_IDENTITY();
END
GO

-- Create procedure to update transaction status
IF OBJECT_ID('dbo.sp_update_transaction_status', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_update_transaction_status;
GO

CREATE PROCEDURE dbo.sp_update_transaction_status
    @transaction_id BIGINT,
    @new_status NVARCHAR(20),
    @notes NVARCHAR(MAX) = NULL,
    @approved_by NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate the status
    IF @new_status NOT IN ('pending', 'completed', 'failed', 'reversed')
    BEGIN
        RAISERROR('Invalid transaction status. Must be one of: pending, completed, failed, reversed.', 16, 1);
        RETURN;
    END
    
    -- Update the transaction status
    UPDATE dbo.transactions
    SET 
        transaction_status = @new_status,
        approved_by = CASE WHEN @new_status = 'completed' THEN @approved_by ELSE approved_by END,
        approval_date = CASE WHEN @new_status = 'completed' AND @approved_by IS NOT NULL THEN GETDATE() ELSE approval_date END,
        transaction_notes = CASE 
                              WHEN @notes IS NOT NULL 
                              THEN COALESCE(transaction_notes + CHAR(13) + CHAR(10) + 'Status Update: ' + @notes, 'Status Update: ' + @notes)
                              ELSE transaction_notes
                            END
    WHERE id = @transaction_id;
    
    -- Return the updated transaction
    SELECT *
    FROM dbo.transactions
    WHERE id = @transaction_id;
END
GO