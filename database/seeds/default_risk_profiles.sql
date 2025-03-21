-- Base Risk Profiles with Kenya-specific investment strategies
INSERT INTO risk_profiles (
    profile_id,
    risk_level, 
    description, 
    investment_strategy, 
    asset_allocation,
    min_investment_period,
    recommended_products,
    volatility_tolerance,
    income_allocation_percentage,
    reassessment_period,
    kenya_specific_guidance,
    created_at, 
    updated_at
) VALUES 
    (
        'ultra_conservative',
        'Ultra Conservative', 
        'Maximum safety with focus on capital preservation, ideal for emergency funds and short-term goals.',
        'capital_preservation',
        '{"fixed_deposits": 40, "t_bills": 30, "money_market": 25, "stocks": 5}',
        '0-1 years',
        '{"cbk_treasury_bills": "91-day, 182-day Treasury Bills", "money_market_funds": "CIC Money Market Fund, Sanlam Money Market Fund", "fixed_deposits": "Equity Bank, KCB, Co-operative Bank fixed deposits"}',
        'Very Low',
        80,
        3, -- Reassess every 3 months
        'Consider CBK Treasury Bills and Money Market Funds like CIC and Sanlam which offer higher returns than savings accounts with minimal risk',
        GETDATE(), 
        GETDATE()
    ),
    (
        'conservative',
        'Conservative', 
        'Focuses on capital preservation with low-risk investments for stable, modest returns.',
        'fixed_income',
        '{"t_bonds": 40, "fixed_deposits": 25, "money_market": 20, "stocks": 15}',
        '1-3 years',
        '{"cbk_bonds": "2-5 year Treasury Bonds", "corporate_bonds": "Safaricom, EABL, KenGen bonds", "income_funds": "Zimele Personal Pension, CIC Balanced Fund"}',
        'Low',
        60,
        6, -- Reassess every 6 months
        'Kenya Treasury Bonds often provide attractive yields compared to bank deposits, especially the infrastructure bonds which are tax-free',
        GETDATE(), 
        GETDATE()
    ),
    (
        'moderately_conservative',
        'Moderately Conservative', 
        'Primarily focused on preserving capital while seeking modest growth through balanced investments.',
        'income_focus',
        '{"t_bonds": 35, "corporate_bonds": 20, "dividend_stocks": 20, "reits": 15, "money_market": 10}',
        '3-5 years',
        '{"dividend_stocks": "Safaricom, EABL, KCB, Equity Bank, BAT", "income_funds": "Old Mutual Balanced Fund, ICEA Lion Growth Fund", "reits": "ILAM Fahari I-REIT"}',
        'Low to Moderate',
        50,
        6, -- Reassess every 6 months
        'Focus on Nairobi Securities Exchange blue-chip stocks with strong dividend histories like Safaricom, KCB, and EABL',
        GETDATE(), 
        GETDATE()
    ),
    (
        'moderate',
        'Moderate', 
        'Balances risk and return by diversifying assets across multiple sectors and investment types.',
        'balanced',
        '{"stocks": 40, "bonds": 25, "reits": 15, "fixed_deposits": 10, "alternative_investments": 10}',
        '5-7 years',
        '{"balanced_funds": "Britam Balanced Fund, CIC Balanced Fund", "nse_stocks": "Mid and large-cap stocks across sectors", "corporate_bonds": "Medium-term corporate bonds"}',
        'Moderate',
        40,
        12, -- Reassess annually
        'The ILAM Fahari I-REIT offers exposure to Kenya''s commercial real estate market with regular income distributions',
        GETDATE(), 
        GETDATE()
    ),
    (
        'moderately_aggressive',
        'Moderately Aggressive', 
        'Emphasis on growth with higher allocation to equities and alternative investments.',
        'growth_focus',
        '{"stocks": 60, "bonds": 15, "alternative_investments": 15, "reits": 10}',
        '7-10 years',
        '{"growth_stocks": "Growth-oriented companies on NSE", "equity_funds": "Britam Equity Fund, Old Mutual Equity Fund", "etfs": "NewGold ETF"}',
        'Moderate to High',
        30,
        12, -- Reassess annually
        'Consider complementing NSE investments with exposure to neighboring exchanges like Rwanda Stock Exchange and Uganda Securities Exchange for regional diversification',
        GETDATE(), 
        GETDATE()
    ),
    (
        'aggressive',
        'Aggressive', 
        'Seeks high returns through significant market exposure and growth-oriented investments.',
        'growth',
        '{"stocks": 70, "alternative_investments": 20, "bonds": 10}',
        '10+ years',
        '{"equity_funds": "Genghis Capital Equity Fund, Cytonn Aggressive Portfolio", "growth_stocks": "Small and mid-cap growth stocks", "venture_capital": "Private equity opportunities"}',
        'High',
        20,
        12, -- Reassess annually
        'The Nairobi Securities Exchange Growth Enterprise Market Segment (GEMS) offers opportunities to invest in smaller, high-growth companies',
        GETDATE(), 
        GETDATE()
    ),
    (
        'very_aggressive',
        'Very Aggressive', 
        'Maximum growth potential with high volatility and risk exposure across emerging sectors.',
        'high_growth',
        '{"growth_stocks": 60, "crypto": 15, "private_equity": 15, "commodities": 10}',
        '10+ years',
        '{"frontier_markets": "Small-cap NSE stocks, tech startups", "crypto": "Bitcoin, Ethereum, regulated crypto platforms", "commodity_etfs": "NewGold ETF"}',
        'Very High',
        10,
        6, -- Reassess every 6 months due to high volatility
        'When investing in cryptocurrency, consider using regulated platforms like Binance P2P or Paxful that support M-Pesa transactions for easier liquidity',
        GETDATE(), 
        GETDATE()
    );

-- Dynamic Risk Assessment Rules
-- These rules help the AI chatbot adjust risk profiles based on user behavior
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'risk_assessment_rules')
BEGIN
    CREATE TABLE risk_assessment_rules (
        rule_id INT IDENTITY(1,1) PRIMARY KEY,
        rule_name NVARCHAR(100) NOT NULL,
        rule_description NVARCHAR(MAX) NOT NULL,
        rule_condition NVARCHAR(MAX) NOT NULL,
        risk_adjustment INT NOT NULL, -- Positive means increase risk, negative means decrease
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
END

TRUNCATE TABLE risk_assessment_rules;

INSERT INTO risk_assessment_rules (
    rule_name, 
    rule_description, 
    rule_condition, 
    risk_adjustment,
    created_at, 
    updated_at
) VALUES
    (
        'age_under_30',
        'Younger investors can typically take on more risk due to longer investment horizons',
        'user.age < 30',
        1, -- Increase risk profile by 1 level
        GETDATE(),
        GETDATE()
    ),
    (
        'age_over_55',
        'Older investors approaching retirement should generally reduce risk exposure',
        'user.age > 55',
        -1, -- Decrease risk profile by 1 level
        GETDATE(),
        GETDATE()
    ),
    (
        'dependent_count_high',
        'Users with many dependents may need to be more conservative',
        'user.dependent_count > 3',
        -1,
        GETDATE(),
        GETDATE()
    ),
    (
        'income_volatile',
        'Users with inconsistent income should maintain lower risk',
        'user.income_stability = ''volatile''',
        -1,
        GETDATE(),
        GETDATE()
    ),
    (
        'emergency_fund_adequate',
        'Users with adequate emergency funds can take more investment risk',
        'user.emergency_fund_months >= 6',
        1,
        GETDATE(),
        GETDATE()
    ),
    (
        'high_debt_ratio',
        'High debt-to-income ratio requires more conservative approach',
        'user.debt_to_income_ratio > 0.4',
        -2, -- Significantly decrease risk
        GETDATE(),
        GETDATE()
    ),
    (
        'investment_knowledge_advanced',
        'Users with advanced investment knowledge can handle more complex strategies',
        'user.investment_knowledge = ''advanced''',
        1,
        GETDATE(),
        GETDATE()
    ),
    (
        'investment_knowledge_beginner',
        'Beginners should start with more conservative approaches',
        'user.investment_knowledge = ''beginner''',
        -1,
        GETDATE(),
        GETDATE()
    ),
    (
        'short_term_goals',
        'Users with important short-term financial goals should be more conservative',
        'user.nearest_financial_goal_years < 2',
        -1,
        GETDATE(),
        GETDATE()
    ),
    (
        'market_downturn_reactive',
        'Users who panic sell during market downturns need more conservative profiles',
        'user.market_downturn_behavior = ''sell''',
        -2,
        GETDATE(),
        GETDATE()
    );

-- Reassessment Triggers Table
-- Defines events that should trigger risk profile reassessment
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'reassessment_triggers')
BEGIN
    CREATE TABLE reassessment_triggers (
        trigger_id INT IDENTITY(1,1) PRIMARY KEY,
        trigger_name NVARCHAR(100) NOT NULL,
        trigger_description NVARCHAR(MAX) NOT NULL,
        reassessment_priority INT NOT NULL, -- 1 = highest priority
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
END

TRUNCATE TABLE reassessment_triggers;

INSERT INTO reassessment_triggers (
    trigger_name,
    trigger_description,
    reassessment_priority,
    created_at,
    updated_at
) VALUES
    (
        'major_life_event',
        'Marriage, birth of child, job change, or retirement requires reassessment of risk tolerance',
        1,
        GETDATE(),
        GETDATE()
    ),
    (
        'significant_income_change',
        'Income increase or decrease of more than 20% may alter risk capacity',
        1,
        GETDATE(),
        GETDATE()
    ),
    (
        'major_market_event',
        'Significant market corrections or economic events may require strategy adjustment',
        2,
        GETDATE(),
        GETDATE()
    ),
    (
        'age_milestone',
        'Reaching age milestones (30, 40, 50, 60) should trigger reassessment',
        3,
        GETDATE(),
        GETDATE()
    ),
    (
        'regular_interval',
        'Regular scheduled reassessment based on risk profile (3, 6, or 12 months)',
        4,
        GETDATE(),
        GETDATE()
    ),
    (
        'goal_achievement',
        'Achieving a financial goal requires reassessment for new objectives',
        2,
        GETDATE(),
        GETDATE()
    ),
    (
        'unusual_trading_activity',
        'Pattern of trades inconsistent with current risk profile',
        3,
        GETDATE(),
        GETDATE()
    ),
    (
        'account_inactivity',
        'No activity for extended period may indicate need for engagement and reassessment',
        5,
        GETDATE(),
        GETDATE()
    );

-- Kenya-Specific Investment Products Table
-- Local financial products for recommendations
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'kenya_investment_products')
BEGIN
    CREATE TABLE kenya_investment_products (
        product_id INT IDENTITY(1,1) PRIMARY KEY,
        product_name NVARCHAR(100) NOT NULL,
        product_type NVARCHAR(50) NOT NULL,
        risk_level NVARCHAR(50) NOT NULL,
        min_investment DECIMAL(10,2) NOT NULL,
        expected_return_range NVARCHAR(20) NOT NULL,
        liquidity_rating INT NOT NULL, -- 1-5, with 5 being most liquid
        provider NVARCHAR(100) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        suitable_profiles NVARCHAR(MAX) NOT NULL, -- Comma-separated list of profile_ids
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
END

TRUNCATE TABLE kenya_investment_products;

INSERT INTO kenya_investment_products (
    product_name,
    product_type,
    risk_level,
    min_investment,
    expected_return_range,
    liquidity_rating,
    provider,
    description,
    suitable_profiles,
    created_at,
    updated_at
) VALUES
    (
        'CBK 91-Day Treasury Bill',
        'government_security',
        'Very Low',
        50000.00,
        '7-9%',
        3,
        'Central Bank of Kenya',
        'Short-term government security with 91-day maturity. Interest is discounted upfront.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK 182-Day Treasury Bill',
        'government_security',
        'Very Low',
        50000.00,
        '8-10%',
        3,
        'Central Bank of Kenya',
        'Short-term government security with 182-day maturity. Interest is discounted upfront.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK 364-Day Treasury Bill',
        'government_security',
        'Very Low',
        50000.00,
        '9-11%',
        2,
        'Central Bank of Kenya',
        'Short-term government security with 364-day maturity. Interest is discounted upfront.',
        'ultra_conservative,conservative,moderately_conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK 2-Year Treasury Bond',
        'government_security',
        'Low',
        50000.00,
        '10-12%',
        2,
        'Central Bank of Kenya',
        'Medium-term government security with coupon payments every 6 months.',
        'conservative,moderately_conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK 5-Year Treasury Bond',
        'government_security',
        'Low',
        50000.00,
        '11-13%',
        2,
        'Central Bank of Kenya',
        'Medium-term government security with coupon payments every 6 months.',
        'conservative,moderately_conservative,moderate',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK 10-Year Treasury Bond',
        'government_security',
        'Low to Moderate',
        50000.00,
        '12-14%',
        1,
        'Central Bank of Kenya',
        'Long-term government security with coupon payments every 6 months.',
        'moderate,moderately_aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'CBK Infrastructure Bond',
        'government_security',
        'Low to Moderate',
        50000.00,
        '11-14%',
        1,
        'Central Bank of Kenya',
        'Tax-free government bond specifically for infrastructure development.',
        'conservative,moderately_conservative,moderate',
        GETDATE(),
        GETDATE()
    ),
    (
        'CIC Money Market Fund',
        'money_market',
        'Very Low',
        5000.00,
        '8-10%',
        5,
        'CIC Asset Management',
        'Low-risk fund investing in short-term money market instruments.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'Sanlam Money Market Fund',
        'money_market',
        'Very Low',
        2500.00,
        '8-10%',
        5,
        'Sanlam Investments',
        'Low-risk fund investing in short-term money market instruments.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'NCBA Fixed Deposit',
        'fixed_deposit',
        'Very Low',
        100000.00,
        '6-8%',
        1,
        'NCBA Bank',
        'Fixed deposit account with interest paid at maturity.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'Equity Bank Fixed Deposit',
        'fixed_deposit',
        'Very Low',
        100000.00,
        '6-8%',
        1,
        'Equity Bank',
        'Fixed deposit account with interest paid at maturity.',
        'ultra_conservative,conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'CIC Balanced Fund',
        'mutual_fund',
        'Moderate',
        5000.00,
        '9-12%',
        4,
        'CIC Asset Management',
        'Fund that invests in both stocks and bonds to balance risk and return.',
        'moderate,moderately_conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'Old Mutual Balanced Fund',
        'mutual_fund',
        'Moderate',
        5000.00,
        '9-12%',
        4,
        'Old Mutual Investment Group',
        'Fund that invests in both stocks and bonds to balance risk and return.',
        'moderate,moderately_conservative',
        GETDATE(),
        GETDATE()
    ),
    (
        'Britam Equity Fund',
        'equity_fund',
        'High',
        1000.00,
        '10-15%',
        4,
        'Britam Asset Managers',
        'Fund that primarily invests in stocks listed on the Nairobi Securities Exchange.',
        'moderately_aggressive,aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'Cytonn Aggressive Portfolio',
        'managed_portfolio',
        'Very High',
        100000.00,
        '14-18%',
        2,
        'Cytonn Investments',
        'Aggressive portfolio with high allocation to stocks and alternative investments.',
        'aggressive,very_aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'ILAM Fahari I-REIT',
        'reit',
        'Moderate',
        10000.00,
        '8-12%',
        3,
        'ICEA Lion Asset Management',
        'Kenya''s first REIT, investing in income-generating real estate properties.',
        'moderately_conservative,moderate,moderately_aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'Safaricom PLC Stock',
        'equity',
        'Moderate to High',
        3000.00,
        '8-15%',
        5,
        'Nairobi Securities Exchange',
        'Shares of Kenya''s largest telecommunications company with consistent dividend history.',
        'moderate,moderately_aggressive,aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'East African Breweries Ltd Stock',
        'equity',
        'Moderate to High',
        3000.00,
        '8-15%',
        5,
        'Nairobi Securities Exchange',
        'Shares of East Africa''s largest beverage company with strong dividend policy.',
        'moderate,moderately_aggressive,aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'KCB Group Stock',
        'equity',
        'Moderate to High',
        3000.00,
        '8-15%',
        5,
        'Nairobi Securities Exchange',
        'Shares of one of Kenya''s largest banking groups with consistent dividend payouts.',
        'moderate,moderately_aggressive,aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'NewGold ETF',
        'etf',
        'Moderate',
        5000.00,
        '5-10%',
        5,
        'Absa Asset Management',
        'Exchange-traded fund that tracks the price of gold, traded on the NSE.',
        'moderate,moderately_aggressive,aggressive,very_aggressive',
        GETDATE(),
        GETDATE()
    ),
    (
        'Local Bitcoin P2P',
        'cryptocurrency',
        'Very High',
        1000.00,
        '-20-100%',
        4,
        'Various P2P Platforms',
        'Peer-to-peer trading of Bitcoin using M-Pesa or bank transfers.',
        'very_aggressive',
        GETDATE(),
        GETDATE()
    );

-- Create index for faster lookups
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_risk_profiles_level' AND object_id = OBJECT_ID('risk_profiles'))
BEGIN
    CREATE INDEX idx_risk_profiles_level ON risk_profiles(risk_level);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_kenya_products_risk' AND object_id = OBJECT_ID('kenya_investment_products'))
BEGIN
    CREATE INDEX idx_kenya_products_risk ON kenya_investment_products(risk_level);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_kenya_products_type' AND object_id = OBJECT_ID('kenya_investment_products'))
BEGIN
    CREATE INDEX idx_kenya_products_type ON kenya_investment_products(product_type);
END