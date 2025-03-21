-- Create the table if it doesn't exist
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'financial_product_categories')
BEGIN
    CREATE TABLE financial_product_categories (
        category_id INT IDENTITY(1,1) PRIMARY KEY,
        category_name NVARCHAR(50) NOT NULL,
        category_slug NVARCHAR(50) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        risk_level NVARCHAR(50) NOT NULL,
        typical_volatility DECIMAL(5,2) NOT NULL, -- Score from 1-10
        typical_returns_range NVARCHAR(20) NOT NULL,
        liquidity_rating INT NOT NULL, -- 1-5, with 5 being most liquid
        recommended_investment_horizon NVARCHAR(50) NOT NULL,
        kenya_specific_notes NVARCHAR(MAX) NULL,
        category_icon NVARCHAR(50) NULL,
        display_order INT NOT NULL DEFAULT 0,
        is_active BIT NOT NULL DEFAULT 1,
        parent_category_id INT NULL,
        api_data_endpoint NVARCHAR(255) NULL, -- API endpoint for market data integration
        update_frequency NVARCHAR(50) NOT NULL, -- How often market data is updated
        performance_metrics NVARCHAR(MAX) NULL, -- JSON string of available metrics
        typical_fees NVARCHAR(MAX) NULL, -- JSON string of typical fee structures
        tax_treatment NVARCHAR(MAX) NOT NULL, -- Tax implications in Kenya
        subcategories NVARCHAR(MAX) NULL, -- JSON array of subcategories
        correlation_matrix NVARCHAR(MAX) NULL, -- JSON object of correlations with other categories
        inflation_sensitivity DECIMAL(5,2) NULL, -- Scale from -5 (negative correlation) to 5 (positive)
        currency_sensitivity DECIMAL(5,2) NULL, -- Scale from -5 (negative correlation) to 5 (positive)
        version INT NOT NULL DEFAULT 1, -- For tracking changes over time
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );

    -- Create a unique constraint on category_slug
    ALTER TABLE financial_product_categories ADD CONSTRAINT UQ_category_slug UNIQUE (category_slug);
END

-- Create relationship table for risk profiles to categories mapping
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'risk_profile_category_allocations')
BEGIN
    CREATE TABLE risk_profile_category_allocations (
        allocation_id INT IDENTITY(1,1) PRIMARY KEY,
        risk_profile_id NVARCHAR(50) NOT NULL, -- References profile_id in risk_profiles table
        category_id INT NOT NULL, -- References category_id in financial_product_categories
        recommended_allocation_percentage INT NOT NULL, -- Percentage of portfolio (0-100)
        allocation_description NVARCHAR(MAX) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (category_id) REFERENCES financial_product_categories(category_id)
    );
END

-- Create table to track category performance over time
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'category_performance_history')
BEGIN
    CREATE TABLE category_performance_history (
        performance_id INT IDENTITY(1,1) PRIMARY KEY,
        category_id INT NOT NULL,
        performance_date DATE NOT NULL,
        ytd_return DECIMAL(7,2) NULL,
        one_year_return DECIMAL(7,2) NULL,
        three_year_return DECIMAL(7,2) NULL,
        five_year_return DECIMAL(7,2) NULL,
        benchmark_comparison DECIMAL(7,2) NULL, -- Comparison to relevant benchmark
        data_source NVARCHAR(100) NOT NULL, -- Source of performance data
        created_at DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (category_id) REFERENCES financial_product_categories(category_id)
    );
    
    -- Add index on category_id and performance_date
    CREATE INDEX idx_category_performance ON category_performance_history(category_id, performance_date);
END

-- Populate the financial product categories table with comprehensive data
INSERT INTO financial_product_categories (
    category_name,
    category_slug,
    description,
    risk_level,
    typical_volatility,
    typical_returns_range,
    liquidity_rating,
    recommended_investment_horizon,
    kenya_specific_notes,
    category_icon,
    display_order,
    api_data_endpoint,
    update_frequency,
    performance_metrics,
    typical_fees,
    tax_treatment,
    subcategories,
    correlation_matrix,
    inflation_sensitivity,
    currency_sensitivity,
    created_at,
    updated_at
) VALUES 
    (
        'Stocks',
        'stocks',
        'Equity investments in publicly traded companies that represent ownership shares. Stock prices fluctuate based on company performance, market conditions, and investor sentiment.',
        'Moderate to High',
        7.5,
        '8-15%',
        5, -- Highly liquid
        '5+ years',
        'The Nairobi Securities Exchange (NSE) has approximately 65 listed companies across 11 sectors. Blue-chip stocks like Safaricom, EABL, and KCB are most liquid. NSE operates Monday-Friday, 9:30 AM-3:00 PM EAT.',
        'fa-chart-line',
        1,
        'https://api.pesaguru.com/market/categories/stocks',
        'Real-time during trading hours',
        '{"nse_20_index": "NSE 20-Share Index", "nasi": "NSE All-Share Index", "market_cap": "Total market capitalization", "pe_ratio": "Average price-to-earnings ratio", "dividend_yield": "Average dividend yield", "sector_performance": "Performance by sector"}',
        '{"brokerage_fees": "1.5-2.1% per transaction", "statutory_fees": "0.12% (NSE 0.06%, CMA 0.06%)", "cdsc_fee": "0.08% of transaction value", "withholding_tax": "5% on dividends"}',
        'Dividend income subject to 5% withholding tax for Kenyan residents. Capital gains on securities traded on the NSE are exempt from capital gains tax.',
        '[{"name": "Blue Chip Stocks", "description": "Large, established companies with stable earnings"}, {"name": "Growth Stocks", "description": "Companies expected to grow faster than market average"}, {"name": "Dividend Stocks", "description": "Companies that regularly distribute earnings to shareholders"}, {"name": "GEMS Stocks", "description": "Growth Enterprise Market Segment for smaller companies"}]',
        '{"bonds": -0.2, "mutual_funds": 0.7, "etfs": 0.8, "real_estate": 0.3, "cryptocurrency": 0.1, "commodities": 0.2, "fixed_deposits": -0.3, "alternative_investments": 0.4}',
        3.2, -- Moderate positive correlation with inflation
        2.8, -- Moderate positive correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Bonds',
        'bonds',
        'Fixed-income securities where investors lend money to an entity (government or corporation) that borrows funds for a defined period at a fixed interest rate.',
        'Low to Moderate',
        3.5,
        '7-14%',
        3, -- Moderately liquid
        '2-10 years',
        'Kenyan government bonds (Treasury bonds) are issued by the Central Bank of Kenya (CBK) and typically offer higher yields compared to developed markets. Corporate bonds are less common but available from blue-chip companies like Safaricom and EABL. Infrastructure bonds offer tax-free returns.',
        'fa-landmark',
        2,
        'https://api.pesaguru.com/market/categories/bonds',
        'Daily updates',
        '{"yield_curve": "Current yield curve", "average_yields": "Average yields by maturity", "bond_indices": "Bond market indices", "credit_spreads": "Spreads between government and corporate bonds"}',
        '{"placement_fees": "0-0.5% for primary market", "brokerage_fees": "0.05-0.3% for secondary market", "custody_fees": "0-0.1% per annum"}',
        'Interest income subject to 15% withholding tax for Kenyan residents. Infrastructure bond interest is tax-exempt.',
        '[{"name": "Treasury Bills", "description": "Short-term government securities (91, 182, 364 days)"}, {"name": "Treasury Bonds", "description": "Medium to long-term government securities (2-30 years)"}, {"name": "Corporate Bonds", "description": "Debt securities issued by corporations"}, {"name": "Infrastructure Bonds", "description": "Government bonds for infrastructure projects, tax-exempt"}]',
        '{"stocks": -0.2, "mutual_funds": 0.5, "etfs": 0.3, "real_estate": 0.2, "cryptocurrency": -0.3, "commodities": 0.0, "fixed_deposits": 0.8, "alternative_investments": 0.1}',
        -1.5, -- Negative correlation with inflation
        -2.0, -- Negative correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Mutual Funds',
        'mutual_funds',
        'Pooled investments managed by professional fund managers who allocate the fund''s assets and attempt to generate income or capital appreciation for investors.',
        'Varies by Fund Type',
        5.0,
        '6-14%',
        4, -- Highly liquid (but not immediate)
        '1-7+ years',
        'Kenyan unit trusts are regulated by the Capital Markets Authority (CMA). Major fund managers include Genghis Capital, CIC Asset Management, Old Mutual, Britam, and Sanlam. Money market funds are most popular for their low risk and liquidity.',
        'fa-hand-holding-usd',
        3,
        'https://api.pesaguru.com/market/categories/mutual-funds',
        'Daily updates',
        '{"nav": "Net Asset Value trends", "fund_flows": "Inflows/outflows data", "performance_by_type": "Returns by fund category", "expense_ratios": "Average management fees"}',
        '{"management_fees": "2-5% per annum", "entry_fees": "0-5% of investment amount", "exit_fees": "0-3% of withdrawal amount", "performance_fees": "0-20% of returns above benchmark"}',
        'Dividend and interest income within funds is not taxed at the fund level. Distributions to investors are subject to withholding tax at 5% for dividends and 15% for interest.',
        '[{"name": "Money Market Funds", "description": "Low-risk funds investing in short-term debt instruments"}, {"name": "Equity Funds", "description": "Funds primarily investing in stocks"}, {"name": "Bond Funds", "description": "Funds primarily investing in bonds"}, {"name": "Balanced Funds", "description": "Funds investing in a mix of stocks and bonds"}]',
        '{"stocks": 0.7, "bonds": 0.5, "etfs": 0.9, "real_estate": 0.4, "cryptocurrency": 0.1, "commodities": 0.2, "fixed_deposits": 0.4, "alternative_investments": 0.3}',
        1.8, -- Moderate positive correlation with inflation
        1.0, -- Slight positive correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'ETFs',
        'etfs',
        'Exchange-traded funds that track an index, sector, commodity, or asset class and trade on exchanges like stocks, offering diversified exposure with lower fees than mutual funds.',
        'Moderate',
        5.5,
        '5-12%',
        5, -- Highly liquid
        '3-7 years',
        'ETFs are limited in Kenya, with NewGold ETF being the primary option listed on the NSE. It tracks gold prices and allows Kenyan investors to gain exposure to gold without owning physical bullion. More ETFs are expected as the market develops.',
        'fa-exchange-alt',
        4,
        'https://api.pesaguru.com/market/categories/etfs',
        'Real-time during trading hours',
        '{"nav": "Net Asset Value vs market price", "tracking_error": "Deviation from underlying index/asset", "trading_volume": "Daily trading volume", "assets_under_management": "Total AUM"}',
        '{"management_fees": "0.4-0.8% per annum", "brokerage_fees": "1.5-2.1% per transaction", "bid_ask_spread": "Varies by ETF liquidity"}',
        'ETF distributions may be subject to withholding tax at 5% for equity-based ETFs and 15% for bond-based ETFs. NewGold ETF is treated as a commodity and does not distribute dividends.',
        '[{"name": "Gold ETFs", "description": "Track gold prices, like NewGold ETF"}, {"name": "Index ETFs", "description": "Track stock market indices (limited availability in Kenya)"}]',
        '{"stocks": 0.8, "bonds": 0.3, "mutual_funds": 0.9, "real_estate": 0.4, "cryptocurrency": 0.3, "commodities": 0.7, "fixed_deposits": 0.1, "alternative_investments": 0.4}',
        2.5, -- Moderate positive correlation with inflation
        1.5, -- Slight positive correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Real Estate',
        'real_estate',
        'Investment in property and real estate assets, including direct ownership, Real Estate Investment Trusts (REITs), and real estate development projects.',
        'Moderate to High',
        6.0,
        '8-15%',
        1, -- Low liquidity for direct property, higher for REITs
        '7+ years',
        'Kenya''s real estate market has seen significant growth in major urban centers like Nairobi and Mombasa. REITs are relatively new, with ILAM Fahari I-REIT being the first listed on the NSE. Land remains a culturally important investment, though prices have stabilized after years of rapid appreciation.',
        'fa-building',
        5,
        'https://api.pesaguru.com/market/categories/real-estate',
        'Monthly updates',
        '{"price_indices": "Property price indices by region", "rental_yields": "Average rental yields by property type", "vacancy_rates": "Vacancy rates by sector", "reit_performance": "REIT price and dividend data"}',
        '{"agent_fees": "3-6% for property transactions", "legal_fees": "1-2% of property value", "stamp_duty": "2-4% of property value", "management_fees": "10-15% of rental income or 1-2% for REITs"}',
        'Rental income subject to standard income tax rates. Capital gains tax at 5% of net gain on property transfer. REIT distributions typically taxed at 5% withholding tax rate.',
        '[{"name": "Residential Property", "description": "Houses, apartments for living or rental income"}, {"name": "Commercial Property", "description": "Office spaces, retail outlets, industrial properties"}, {"name": "REITs", "description": "Real Estate Investment Trusts traded on the NSE"}, {"name": "Land", "description": "Undeveloped land for appreciation or development"}]',
        '{"stocks": 0.3, "bonds": 0.2, "mutual_funds": 0.4, "etfs": 0.4, "cryptocurrency": 0.0, "commodities": 0.3, "fixed_deposits": 0.1, "alternative_investments": 0.5}',
        4.0, -- Strong positive correlation with inflation
        1.0, -- Slight positive correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Cryptocurrency',
        'cryptocurrency',
        'Digital or virtual currencies that use cryptography for security and operate on decentralized networks based on blockchain technology.',
        'Very High',
        9.5,
        '-30-100%',
        4, -- Highly liquid on exchanges
        '3-7+ years',
        'While the Central Bank of Kenya has issued warnings about cryptocurrencies, they are not illegal. Kenyans trade through peer-to-peer platforms like Paxful and Binance P2P, often using M-Pesa for transactions. Local crypto awareness is growing, but regulatory clarity remains limited.',
        'fa-coins',
        6,
        'https://api.pesaguru.com/market/categories/cryptocurrency',
        'Real-time 24/7',
        '{"price_data": "Current prices in KES and USD", "trading_volume": "Local and global trading volumes", "market_dominance": "Share of total crypto market", "adoption_metrics": "Usage statistics in Kenya"}',
        '{"exchange_fees": "0.1-3% per transaction", "network_fees": "Variable based on blockchain congestion", "p2p_premiums": "1-5% above global market rates", "withdrawal_fees": "Fixed or percentage-based for fiat conversion"}',
        'No specific tax framework for cryptocurrencies in Kenya. Potentially taxable as capital gains or income, but enforcement is limited. Users should consult tax professionals for guidance.',
        '[{"name": "Bitcoin (BTC)", "description": "The original and largest cryptocurrency by market cap"}, {"name": "Ethereum (ETH)", "description": "Platform for decentralized applications and smart contracts"}, {"name": "Stablecoins", "description": "Cryptocurrencies pegged to stable assets like USD"}, {"name": "Altcoins", "description": "Alternative cryptocurrencies beyond Bitcoin and Ethereum"}]',
        '{"stocks": 0.1, "bonds": -0.3, "mutual_funds": 0.1, "etfs": 0.3, "real_estate": 0.0, "commodities": 0.4, "fixed_deposits": -0.4, "alternative_investments": 0.5}',
        2.0, -- Moderate positive correlation with inflation
        -3.0, -- Strong negative correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Commodities',
        'commodities',
        'Physical goods such as gold, silver, oil, agricultural products and other raw materials that are bought and sold in standardized contracts.',
        'Moderate to High',
        7.0,
        '3-15%',
        3, -- Moderately liquid, varies by commodity
        '1-5+ years',
        'Kenyan commodity investing is primarily through the NewGold ETF for gold exposure or agricultural investments. Direct commodity trading remains limited for retail investors. Agricultural commodities have cultural significance with opportunities in coffee, tea, and other export crops.',
        'fa-gem',
        7,
        'https://api.pesaguru.com/market/categories/commodities',
        'Daily updates',
        '{"gold_prices": "Local gold prices in KES", "agricultural_indices": "Agricultural commodity indices", "global_benchmarks": "Global commodity benchmark prices", "newgold_etf": "NewGold ETF performance"}',
        '{"etf_fees": "0.4-0.8% for gold ETFs", "storage_fees": "0.5-1.5% for physical commodities", "brokerage_fees": "1-3% for commodity-related securities"}',
        'ETF investments like NewGold follow security taxation. Physical commodity gains taxed as capital gains at applicable rates. Agricultural income subject to standard income tax.',
        '[{"name": "Precious Metals", "description": "Gold, silver, platinum investments"}, {"name": "Agricultural Commodities", "description": "Coffee, tea, maize, wheat investments"}, {"name": "Energy", "description": "Oil, natural gas, coal investments"}, {"name": "Industrial Metals", "description": "Copper, aluminum, iron investments"}]',
        '{"stocks": 0.2, "bonds": 0.0, "mutual_funds": 0.2, "etfs": 0.7, "real_estate": 0.3, "cryptocurrency": 0.4, "fixed_deposits": -0.1, "alternative_investments": 0.4}',
        4.5, -- Strong positive correlation with inflation
        -2.0, -- Moderate negative correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Fixed Deposits',
        'fixed_deposits',
        'Interest-bearing deposit accounts with a specified fixed term and interest rate, including bank term deposits, SACCOs, and mobile money saving products.',
        'Very Low',
        1.0,
        '5-13%',
        2, -- Low liquidity until maturity
        '3 months - 5 years',
        'Fixed deposits in Kenya include traditional bank term deposits, SACCO deposits, and mobile-based products like M-Shwari and KCB M-Pesa. SACCOs typically offer higher rates than banks. Deposit Insurance covers bank deposits up to KES 500,000 per depositor per institution.',
        'fa-piggy-bank',
        8,
        'https://api.pesaguru.com/market/categories/fixed-deposits',
        'Weekly updates',
        '{"average_rates": "Average rates by term length", "bank_comparison": "Rate comparison across institutions", "sacco_rates": "SACCO dividend and interest rates", "mobile_savings_rates": "Rates for mobile-based savings products"}',
        '{"early_withdrawal_penalties": "Typically loss of interest or fees", "account_maintenance_fees": "0-500 KES per account", "minimum_deposit_requirements": "Varies by institution"}',
        'Interest income from banks and deposit-taking institutions subject to 15% withholding tax. SACCO dividends exempt from withholding tax but may be subject to income tax.',
        '[{"name": "Bank Fixed Deposits", "description": "Term deposits offered by commercial banks"}, {"name": "SACCO Deposits", "description": "Savings in Savings and Credit Cooperatives"}, {"name": "Mobile Money Savings", "description": "M-Shwari, KCB M-Pesa, and similar products"}, {"name": "Corporate Fixed Deposits", "description": "Term deposits with corporations"}]',
        '{"stocks": -0.3, "bonds": 0.8, "mutual_funds": 0.4, "etfs": 0.1, "real_estate": 0.1, "cryptocurrency": -0.4, "commodities": -0.1, "alternative_investments": -0.2}',
        -2.0, -- Negative correlation with inflation
        0.5, -- Slight positive correlation with KES strength
        GETDATE(),
        GETDATE()
    ),
    (
        'Alternative Investments',
        'alternative_investments',
        'Non-traditional assets beyond conventional stocks, bonds, and cash, including private equity, venture capital, hedge funds, and specialized investments.',
        'High to Very High',
        8.5,
        '10-25%',
        1, -- Low liquidity
        '5-10+ years',
        'Alternative investments in Kenya include private equity funds, venture capital, specialized agricultural investments (like greenhouse farming), and high-yield solutions from firms like Cytonn. These often require higher minimum investments and longer commitment periods.',
        'fa-chart-pie',
        9,
        'https://api.pesaguru.com/market/categories/alternative-investments',
        'Monthly or quarterly updates',
        '{"private_equity_returns": "PE fund performance metrics", "venture_capital_activity": "VC deal flow and returns", "specialty_investments": "Performance of niche investment vehicles", "agricultural_returns": "Returns on agricultural investments"}',
        '{"management_fees": "2-3% per annum", "performance_fees": "20-30% of profits above hurdle rate", "entry_fees": "1-5% of investment", "exit_fees": "0-5% for early redemption"}',
        'Income typically taxed as capital gains or business income at applicable rates. Specific tax treatment varies by investment structure and may require professional guidance.',
        '[{"name": "Private Equity", "description": "Direct investment in private companies"}, {"name": "Venture Capital", "description": "Funding for early-stage high-potential companies"}, {"name": "Agricultural Investments", "description": "Greenhouse farming, crop financing"}, {"name": "Specialty Finance", "description": "High-yield structured products, project financing"}]',
        '{"stocks": 0.4, "bonds": 0.1, "mutual_funds": 0.3, "etfs": 0.4, "real_estate": 0.5, "cryptocurrency": 0.5, "commodities": 0.4, "fixed_deposits": -0.2}',
        3.0, -- Moderate positive correlation with inflation
        -1.0, -- Slight negative correlation with KES strength
        GETDATE(),
        GETDATE()
    );

-- Populate the risk profile category allocations table with recommended allocations
-- These allocations serve as starting points for AI recommendations
INSERT INTO risk_profile_category_allocations (
    risk_profile_id,
    category_id,
    recommended_allocation_percentage,
    allocation_description,
    created_at,
    updated_at
)
VALUES
    -- Ultra Conservative profile allocations
    ('ultra_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 40, 'Focus on short-term government securities (91-day to 1-year T-bills)', GETDATE(), GETDATE()),
    ('ultra_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'fixed_deposits'), 40, 'Bank deposits and M-Shwari/KCB M-Pesa savings', GETDATE(), GETDATE()),
    ('ultra_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 20, 'Money market funds only', GETDATE(), GETDATE()),
    
    -- Conservative profile allocations
    ('conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 50, 'Mix of T-bills and medium-term government bonds', GETDATE(), GETDATE()),
    ('conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'fixed_deposits'), 25, 'Fixed deposits and SACCO savings', GETDATE(), GETDATE()),
    ('conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 15, 'Primarily money market funds with small allocation to balanced funds', GETDATE(), GETDATE()),
    ('conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 10, 'Blue-chip dividend stocks only', GETDATE(), GETDATE()),
    
    -- Moderately Conservative profile allocations
    ('moderately_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 40, 'Government bonds and high-quality corporate bonds', GETDATE(), GETDATE()),
    ('moderately_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 20, 'Established dividend-paying companies', GETDATE(), GETDATE()),
    ('moderately_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 20, 'Balanced funds and bond funds', GETDATE(), GETDATE()),
    ('moderately_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'fixed_deposits'), 10, 'Bank and SACCO deposits', GETDATE(), GETDATE()),
    ('moderately_conservative', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), 10, 'REITs and income-generating real estate', GETDATE(), GETDATE()),
    
    -- Moderate profile allocations
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 35, 'Diversified portfolio of blue-chip and select growth stocks', GETDATE(), GETDATE()),
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 25, 'Mix of government and corporate bonds', GETDATE(), GETDATE()),
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 15, 'Equity and balanced funds', GETDATE(), GETDATE()),
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), 15, 'REITs and select property investments', GETDATE(), GETDATE()),
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'fixed_deposits'), 5, 'Short-term deposits for liquidity', GETDATE(), GETDATE()),
    ('moderate', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'etfs'), 5, 'Gold ETF for diversification', GETDATE(), GETDATE()),
    
    -- Moderately Aggressive profile allocations
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 50, 'Mix of blue-chip and growth-oriented stocks', GETDATE(), GETDATE()),
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 15, 'Primarily equity funds', GETDATE(), GETDATE()),
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 10, 'Higher-yielding corporate and infrastructure bonds', GETDATE(), GETDATE()),
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), 10, 'Growth-oriented real estate and REITs', GETDATE(), GETDATE()),
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'alternative_investments'), 10, 'Selected alternative investments', GETDATE(), GETDATE()),
    ('moderately_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'etfs'), 5, 'Commodity ETFs', GETDATE(), GETDATE()),
    
    -- Aggressive profile allocations
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 60, 'Growth-focused stocks including mid-cap opportunities', GETDATE(), GETDATE()),
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'alternative_investments'), 15, 'Private equity and high-yield investment vehicles', GETDATE(), GETDATE()),
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), 10, 'Development projects and high-growth real estate', GETDATE(), GETDATE()),
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), 5, 'Aggressive equity funds', GETDATE(), GETDATE()),
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'etfs'), 5, 'Sector and commodity ETFs', GETDATE(), GETDATE()),
    ('aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), 5, 'High-yield bonds only', GETDATE(), GETDATE()),
    
    -- Very Aggressive profile allocations
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), 50, 'High-growth stocks including small caps and GEMS', GETDATE(), GETDATE()),
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'alternative_investments'), 20, 'Venture capital, private equity, and high-yield opportunities', GETDATE(), GETDATE()),
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'cryptocurrency'), 10, 'Selected cryptocurrencies (Bitcoin, Ethereum)', GETDATE(), GETDATE()),
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), 10, 'Speculative real estate and development projects', GETDATE(), GETDATE()),
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'commodities'), 5, 'Commodities exposure for diversification', GETDATE(), GETDATE()),
    ('very_aggressive', (SELECT category_id FROM financial_product_categories WHERE category_slug = 'etfs'), 5, 'Specialized ETFs', GETDATE(), GETDATE());

-- Add initial category performance data (for demonstration purposes)
INSERT INTO category_performance_history (
    category_id,
    performance_date,
    ytd_return,
    one_year_return,
    three_year_return,
    five_year_return,
    benchmark_comparison,
    data_source,
    created_at
)
VALUES
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'stocks'), DATEADD(day, -1, GETDATE()), 5.2, 9.8, 24.5, 32.1, 1.2, 'NSE Market Data', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'bonds'), DATEADD(day, -1, GETDATE()), 2.1, 10.5, 35.2, 62.8, 0.8, 'CBK Treasury Data', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'mutual_funds'), DATEADD(day, -1, GETDATE()), 3.8, 9.1, 28.7, 42.3, 1.0, 'CMA Fund Reports', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'etfs'), DATEADD(day, -1, GETDATE()), 2.9, 11.2, 22.4, 37.8, 0.9, 'NSE ETF Data', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'real_estate'), DATEADD(day, -1, GETDATE()), 1.2, 8.5, 31.2, 58.5, 1.5, 'HassConsult Index', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'cryptocurrency'), DATEADD(day, -1, GETDATE()), 21.5, 42.8, 112.5, 587.2, 3.2, 'CoinGecko API', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'commodities'), DATEADD(day, -1, GETDATE()), 3.7, 7.2, 18.5, 28.9, 0.7, 'World Bank Commodity Data', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'fixed_deposits'), DATEADD(day, -1, GETDATE()), 1.8, 7.5, 23.4, 39.2, 1.0, 'CBK Banking Sector Report', GETDATE()),
    ((SELECT category_id FROM financial_product_categories WHERE category_slug = 'alternative_investments'), DATEADD(day, -1, GETDATE()), 4.2, 14.8, 42.5, 81.2, 1.8, 'Private Equity & VC Reports', GETDATE());

-- Create views for simplified querying
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_category_performance_current')
BEGIN
    DROP VIEW v_category_performance_current;
END

GO

CREATE VIEW v_category_performance_current AS
SELECT 
    fpc.category_name,
    fpc.category_slug,
    fpc.risk_level,
    cph.ytd_return,
    cph.one_year_return,
    cph.three_year_return,
    cph.five_year_return,
    cph.performance_date
FROM 
    financial_product_categories fpc
JOIN 
    (SELECT 
        category_id,
        MAX(performance_date) as latest_date
     FROM 
        category_performance_history
     GROUP BY 
        category_id) latest
ON 
    fpc.category_id = latest.category_id
JOIN 
    category_performance_history cph
ON 
    latest.category_id = cph.category_id AND
    latest.latest_date = cph.performance_date
WHERE
    fpc.is_active = 1;

GO

-- Create view for risk profile allocations
IF EXISTS (SELECT * FROM sys.views WHERE name = 'v_risk_profile_allocations')
BEGIN
    DROP VIEW v_risk_profile_allocations;
END

GO

CREATE VIEW v_risk_profile_allocations AS
SELECT 
    rp.risk_profile_id,
    fpc.category_name,
    fpc.category_slug,
    rca.recommended_allocation_percentage,
    rca.allocation_description
FROM 
    risk_profile_category_allocations rca
JOIN 
    financial_product_categories fpc
ON 
    rca.category_id = fpc.category_id
ORDER BY 
    rp.risk_profile_id,
    rca.recommended_allocation_percentage DESC;

GO

-- Add a stored procedure for updating category performance data
IF EXISTS (SELECT * FROM sys.objects WHERE type = 'P' AND name = 'usp_update_category_performance')
BEGIN
    DROP PROCEDURE usp_update_category_performance;
END

GO

CREATE PROCEDURE usp_update_category_performance
    @category_slug NVARCHAR(50),
    @ytd_return DECIMAL(7,2),
    @one_year_return DECIMAL(7,2),
    @three_year_return DECIMAL(7,2) = NULL,
    @five_year_return DECIMAL(7,2) = NULL,
    @benchmark_comparison DECIMAL(7,2) = NULL,
    @data_source NVARCHAR(100)
AS
BEGIN
    DECLARE @category_id INT;
    
    SELECT @category_id = category_id 
    FROM financial_product_categories 
    WHERE category_slug = @category_slug;
    
    IF @category_id IS NULL
    BEGIN
        RAISERROR('Category slug not found', 16, 1);
        RETURN;
    END
    
    INSERT INTO category_performance_history (
        category_id,
        performance_date,
        ytd_return,
        one_year_return,
        three_year_return,
        five_year_return,
        benchmark_comparison,
        data_source,
        created_at
    )
    VALUES (
        @category_id,
        GETDATE(),
        @ytd_return,
        @one_year_return,
        @three_year_return,
        @five_year_return,
        @benchmark_comparison,
        @data_source,
        GETDATE()
    );
    
    -- Return the newly inserted data
    SELECT 
        fpc.category_name,
        fpc.category_slug,
        cph.performance_date,
        cph.ytd_return,
        cph.one_year_return,
        cph.three_year_return,
        cph.five_year_return,
        cph.benchmark_comparison,
        cph.data_source
    FROM 
        category_performance_history cph
    JOIN 
        financial_product_categories fpc
    ON 
        cph.category_id = fpc.category_id
    WHERE 
        cph.category_id = @category_id AND
        cph.performance_date = CONVERT(DATE, GETDATE());
END

GO

-- Create indexes for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_category_slug' AND object_id = OBJECT_ID('financial_product_categories'))
BEGIN
    CREATE INDEX idx_category_slug ON financial_product_categories(category_slug);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_risk_level' AND object_id = OBJECT_ID('financial_product_categories'))
BEGIN
    CREATE INDEX idx_risk_level ON financial_product_categories(risk_level);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_profile_allocations' AND object_id = OBJECT_ID('risk_profile_category_allocations'))
BEGIN
    CREATE INDEX idx_profile_allocations ON risk_profile_category_allocations(risk_profile_id, category_id);
END