-- Migration: Create Market Data Cache Table
-- Description: Caches real-time market data for financial products to reduce API calls and improve performance

-- Check if table already exists before creating
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[market_data_cache]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[market_data_cache] (
        -- Primary Identifiers
        [id] BIGINT NOT NULL IDENTITY(1,1) PRIMARY KEY,
        [symbol] NVARCHAR(50) NOT NULL, -- Ticker symbol or identifier (e.g., AAPL, BTC-USD, TSLA)
        [market_source] NVARCHAR(100) NOT NULL, -- Data provider (e.g., NSE, CoinGecko, Yahoo Finance)
        [asset_type] NVARCHAR(50) NOT NULL, -- Type of financial asset (stock, bond, crypto, forex, etc.)
        [asset_name] NVARCHAR(255), -- Full name of the financial asset
        
        -- Market Data Fields
        [price] DECIMAL(19, 6) NOT NULL, -- Current market price of the asset
        [open_price] DECIMAL(19, 6), -- Opening price for the day
        [high_price] DECIMAL(19, 6), -- Highest price recorded within the period
        [low_price] DECIMAL(19, 6), -- Lowest price recorded within the period
        [previous_close] DECIMAL(19, 6), -- Last closing price from previous market session
        [volume] DECIMAL(25, 2), -- Trading volume of the asset
        [market_cap] DECIMAL(25, 2), -- Total market capitalization (if applicable)
        [currency] NVARCHAR(3) NOT NULL, -- Currency in which the asset is traded (KES, USD, EUR)
        [bid_price] DECIMAL(19, 6), -- Current bid price (if available)
        [ask_price] DECIMAL(19, 6), -- Current ask price (if available)
        [spread] DECIMAL(19, 6), -- Difference between bid and ask prices
        
        -- Performance Indicators
        [change_amount] DECIMAL(19, 6), -- Absolute change in price compared to previous close
        [change_percent] DECIMAL(10, 6), -- Percentage change in price compared to previous close
        [week_52_high] DECIMAL(19, 6), -- Highest price recorded in the last 52 weeks
        [week_52_low] DECIMAL(19, 6), -- Lowest price recorded in the last 52 weeks
        [moving_average_50] DECIMAL(19, 6), -- 50-day moving average price
        [moving_average_200] DECIMAL(19, 6), -- 200-day moving average price
        [relative_strength_index] DECIMAL(10, 6), -- RSI value (if available)
        [beta] DECIMAL(10, 6), -- Beta value measuring volatility
        [earnings_per_share] DECIMAL(19, 6), -- EPS for stocks
        [price_to_earnings_ratio] DECIMAL(19, 6), -- P/E ratio for stocks
        [dividend_yield] DECIMAL(10, 6), -- Current dividend yield percentage
        
        -- Kenya-Specific Market Data
        [nse_sector] NVARCHAR(100), -- NSE sector classification (if Kenyan stock)
        [market_segment] NVARCHAR(50), -- Market segment (Main Investment, GEMS, etc.)
        [local_currency_equivalent] DECIMAL(19, 6), -- Equivalent price in KES for foreign assets
        
        -- Technical Indicators (for advanced analysis)
        [support_level] DECIMAL(19, 6), -- Identified support level
        [resistance_level] DECIMAL(19, 6), -- Identified resistance level
        [macd] DECIMAL(10, 6), -- Moving Average Convergence Divergence
        [bollinger_upper] DECIMAL(19, 6), -- Upper Bollinger Band
        [bollinger_lower] DECIMAL(19, 6), -- Lower Bollinger Band
        [trading_signal] NVARCHAR(20), -- Buy, Sell, Hold signals based on technical analysis
        
        -- Timestamp & Validity
        [last_updated] DATETIME2 NOT NULL DEFAULT GETDATE(), -- Timestamp of the last market data update
        [data_valid_until] DATETIME2 NOT NULL, -- Expiry timestamp for cached data
        [trading_day] DATE NOT NULL, -- The trading day this data represents
        [is_market_open] BIT NOT NULL DEFAULT 0, -- Whether the market is currently open
        [next_market_open] DATETIME2, -- When the market opens next
        [refresh_priority] TINYINT DEFAULT 5, -- Priority for refresh (1-10, higher = more frequent)
        
        -- API & Data Source Tracking
        [api_call_id] NVARCHAR(100), -- Reference to the API call that fetched this data
        [api_endpoint] NVARCHAR(255), -- The specific API endpoint used
        [data_quality_score] TINYINT, -- Rating of data quality/reliability (1-10)
        [raw_response] NVARCHAR(MAX), -- Raw API response data (for debugging/auditing)
        
        -- Error Handling
        [fetch_error] BIT DEFAULT 0, -- Flag indicating if there was an error fetching this data
        [error_message] NVARCHAR(MAX), -- Error message if fetch_error is true
        [retry_count] INT DEFAULT 0, -- Number of retried data fetches
        
        -- System Tracking
        [created_at] DATETIME2 NOT NULL DEFAULT GETDATE(), -- When this record was first created
        [created_by] NVARCHAR(100) DEFAULT 'system', -- Who/what created this record
        
        -- Create a unique constraint to avoid duplicate entries for the same symbol on the same day
        CONSTRAINT [UQ_market_data_cache_symbol_source_trading_day] UNIQUE ([symbol], [market_source], [trading_day])
    );

    -- Indexes for efficient querying
    CREATE INDEX [idx_market_data_symbol] ON [dbo].[market_data_cache] ([symbol]);
    CREATE INDEX [idx_market_data_source] ON [dbo].[market_data_cache] ([market_source]);
    CREATE INDEX [idx_market_data_asset_type] ON [dbo].[market_data_cache] ([asset_type]);
    CREATE INDEX [idx_market_data_updated] ON [dbo].[market_data_cache] ([last_updated]);
    CREATE INDEX [idx_market_data_valid_until] ON [dbo].[market_data_cache] ([data_valid_until]);
    CREATE INDEX [idx_market_data_trading_day] ON [dbo].[market_data_cache] ([trading_day]);
    
    -- Add comment to table
    EXEC sys.sp_addextendedproperty 
        @name = N'MS_Description',
        @value = N'Caches real-time market data for financial products, reducing API calls and improving performance for PesaGuru financial advisory services',
        @level0type = N'SCHEMA', @level0name = N'dbo',
        @level1type = N'TABLE', @level1name = N'market_data_cache';
END
GO

-- Create procedure to refresh market data
IF OBJECT_ID('dbo.sp_refresh_market_data', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_refresh_market_data;
GO

CREATE PROCEDURE dbo.sp_refresh_market_data
    @symbol NVARCHAR(50),
    @market_source NVARCHAR(100) = NULL,
    @force_refresh BIT = 0
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get records that need refreshing
    -- Either the specific symbol or all expired data
    DECLARE @records_to_refresh TABLE (
        id BIGINT,
        symbol NVARCHAR(50),
        market_source NVARCHAR(100),
        last_updated DATETIME2
    );
    
    IF @symbol IS NOT NULL
    BEGIN
        -- Refresh specific symbol (optionally from specific source)
        INSERT INTO @records_to_refresh (id, symbol, market_source, last_updated)
        SELECT id, symbol, market_source, last_updated
        FROM dbo.market_data_cache
        WHERE symbol = @symbol
        AND (@market_source IS NULL OR market_source = @market_source)
        AND (@force_refresh = 1 OR data_valid_until <= GETDATE());
    END
    ELSE
    BEGIN
        -- Refresh all expired data, prioritized by refresh_priority
        INSERT INTO @records_to_refresh (id, symbol, market_source, last_updated)
        SELECT id, symbol, market_source, last_updated
        FROM dbo.market_data_cache
        WHERE data_valid_until <= GETDATE()
        ORDER BY refresh_priority DESC, data_valid_until ASC;
    END
    
    -- Return the list of records that need refreshing
    -- The application will handle the actual API calls and updates
    SELECT * FROM @records_to_refresh;
END
GO

-- Create procedure to update market data after API fetch
IF OBJECT_ID('dbo.sp_update_market_data', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_update_market_data;
GO

CREATE PROCEDURE dbo.sp_update_market_data
    @symbol NVARCHAR(50),
    @market_source NVARCHAR(100),
    @price DECIMAL(19, 6),
    @currency NVARCHAR(3),
    @asset_type NVARCHAR(50),
    @trading_day DATE,
    @cache_duration_minutes INT = 15,
    -- Optional parameters for additional market data
    @open_price DECIMAL(19, 6) = NULL,
    @high_price DECIMAL(19, 6) = NULL,
    @low_price DECIMAL(19, 6) = NULL,
    @previous_close DECIMAL(19, 6) = NULL,
    @volume DECIMAL(25, 2) = NULL,
    @market_cap DECIMAL(25, 2) = NULL,
    @change_percent DECIMAL(10, 6) = NULL,
    @asset_name NVARCHAR(255) = NULL,
    @is_market_open BIT = 0,
    @api_call_id NVARCHAR(100) = NULL,
    @raw_response NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @data_valid_until DATETIME2 = DATEADD(MINUTE, @cache_duration_minutes, GETDATE());
    
    -- Calculate change amount if previous_close is provided but change_percent isn't
    DECLARE @change_amount DECIMAL(19, 6) = NULL;
    IF @previous_close IS NOT NULL AND @price IS NOT NULL
    BEGIN
        SET @change_amount = @price - @previous_close;
        
        -- Calculate change_percent if not provided
        IF @change_percent IS NULL AND @previous_close <> 0
        BEGIN
            SET @change_percent = (@change_amount / @previous_close) * 100;
        END
    END
    
    -- Try to update existing record for today
    UPDATE dbo.market_data_cache
    SET 
        price = @price,
        open_price = COALESCE(@open_price, open_price),
        high_price = COALESCE(@high_price, high_price),
        low_price = COALESCE(@low_price, low_price),
        previous_close = COALESCE(@previous_close, previous_close),
        volume = COALESCE(@volume, volume),
        market_cap = COALESCE(@market_cap, market_cap),
        currency = @currency,
        change_amount = COALESCE(@change_amount, change_amount),
        change_percent = COALESCE(@change_percent, change_percent),
        asset_name = COALESCE(@asset_name, asset_name),
        last_updated = GETDATE(),
        data_valid_until = @data_valid_until,
        is_market_open = @is_market_open,
        api_call_id = COALESCE(@api_call_id, api_call_id),
        raw_response = COALESCE(@raw_response, raw_response),
        fetch_error = 0,
        error_message = NULL
    WHERE 
        symbol = @symbol 
        AND market_source = @market_source
        AND trading_day = @trading_day;
    
    -- If no record exists for today, insert a new one
    IF @@ROWCOUNT = 0
    BEGIN
        INSERT INTO dbo.market_data_cache (
            symbol, market_source, asset_type, asset_name, price, open_price, 
            high_price, low_price, previous_close, volume, market_cap, currency,
            change_amount, change_percent, last_updated, data_valid_until, 
            trading_day, is_market_open, api_call_id, raw_response
        )
        VALUES (
            @symbol, @market_source, @asset_type, @asset_name, @price, @open_price, 
            @high_price, @low_price, @previous_close, @volume, @market_cap, @currency,
            @change_amount, @change_percent, GETDATE(), @data_valid_until, 
            @trading_day, @is_market_open, @api_call_id, @raw_response
        );
    END
    
    -- Return the updated/inserted record
    SELECT *
    FROM dbo.market_data_cache
    WHERE 
        symbol = @symbol 
        AND market_source = @market_source
        AND trading_day = @trading_day;
END
GO

-- Create procedure to record fetch errors
IF OBJECT_ID('dbo.sp_record_market_data_error', 'P') IS NOT NULL
    DROP PROCEDURE dbo.sp_record_market_data_error;
GO

CREATE PROCEDURE dbo.sp_record_market_data_error
    @symbol NVARCHAR(50),
    @market_source NVARCHAR(100),
    @error_message NVARCHAR(MAX),
    @api_call_id NVARCHAR(100) = NULL,
    @trading_day DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default to current trading day if not specified
    IF @trading_day IS NULL
        SET @trading_day = CAST(GETDATE() AS DATE);
    
    -- Try to update existing record
    UPDATE dbo.market_data_cache
    SET 
        fetch_error = 1,
        error_message = @error_message,
        api_call_id = COALESCE(@api_call_id, api_call_id),
        last_updated = GETDATE(),
        retry_count = retry_count + 1
    WHERE 
        symbol = @symbol 
        AND market_source = @market_source
        AND trading_day = @trading_day;
    
    -- If no record exists, create a placeholder with error info
    IF @@ROWCOUNT = 0
    BEGIN
        INSERT INTO dbo.market_data_cache (
            symbol, market_source, asset_type, price, currency,
            last_updated, data_valid_until, trading_day,
            fetch_error, error_message, api_call_id, retry_count
        )
        VALUES (
            @symbol, @market_source, 'unknown', 0, 'N/A',
            GETDATE(), DATEADD(MINUTE, 5, GETDATE()), @trading_day,
            1, @error_message, @api_call_id, 1
        );
    END
END
GO