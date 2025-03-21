<?php

return [
    /*
    |--------------------------------------------------------------------------
    | General Chatbot Settings
    |--------------------------------------------------------------------------
    */
    'general' => [
        'name' => 'PesaGuru',
        'version' => '1.0.0',
        'description' => 'Personalized Financial Advisory and Investment Planning Chatbot for Kenya',
        'default_greeting' => 'Karibu! I\'m PesaGuru, your personal financial advisor. How can I help you today?',
        'max_conversation_history' => 20, // Number of exchanges to keep in memory for context
        'idle_timeout' => 1800, // Session timeout in seconds (30 minutes)
        'save_conversations' => true, // Whether to save conversations to database
    ],

    /*
    |--------------------------------------------------------------------------
    | AI Models Configuration
    |--------------------------------------------------------------------------
    */
    'ai_models' => [
        'enabled' => true,
        
        // Primary NLP model configuration
        'nlp' => [
            'primary_model' => 'financial_bert', // Options: bert, gpt, financial_bert
            'fallback_model' => 'gpt4', // Fallback model if primary fails
            
            // BERT model settings
            'bert' => [
                'model_path' => '/ai/models/financial_bert.pkl',
                'tokenizer_path' => '/ai/models/tokenizer.pkl',
                'max_sequence_length' => 128,
                'confidence_threshold' => 0.75, // Minimum confidence score to accept prediction
            ],
            
            // GPT model settings
            'gpt' => [
                'api_key' => env('OPENAI_API_KEY', ''),
                'model_version' => 'gpt-4',
                'temperature' => 0.7,
                'max_tokens' => 600,
                'request_timeout' => 15, // seconds
            ],
            
            // Specialized financial BERT model
            'financial_bert' => [
                'model_path' => '/ai/models/financial_bert_kenya.pkl',
                'tokenizer_path' => '/ai/models/financial_tokenizer.pkl',
                'max_sequence_length' => 256,
                'confidence_threshold' => 0.8,
            ],
        ],
        
        // Intent detection and classification
        'intent_detection' => [
            'provider' => 'dialogflow', // Options: dialogflow, custom
            'dialogflow' => [
                'project_id' => env('DIALOGFLOW_PROJECT_ID', ''),
                'credentials_json' => env('DIALOGFLOW_CREDENTIALS', ''),
                'language_code' => 'en', // Default language
                'fallback_intent_confidence' => 0.3,
            ],
            'custom' => [
                'model_path' => '/ai/models/intent_classifier.pkl',
                'confidence_threshold' => 0.7,
            ],
        ],
        
        // Entity recognition models
        'entity_extraction' => [
            'enabled' => true,
            'model_path' => '/ai/models/entity_extractor.pkl',
            'financial_entities' => [
                'STOCK', 'FOREX', 'INTEREST_RATE', 'LOAN_TYPE', 
                'INVESTMENT_PRODUCT', 'RISK_LEVEL', 'TIMEFRAME', 'AMOUNT'
            ],
        ],
        
        // Sentiment analysis model
        'sentiment_analysis' => [
            'enabled' => true,
            'model_path' => '/ai/models/sentiment_model.pkl',
        ],
        
        // Recommendation engine models
        'recommendation_engine' => [
            'enabled' => true,
            'model_path' => '/ai/models/recommendation_model.pkl',
            'update_frequency' => 'daily', // How often to update recommendations
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Language and Localization Settings
    |--------------------------------------------------------------------------
    */
    'language' => [
        'default' => 'en', // Default language (English)
        'supported' => ['en', 'sw'], // Supported languages (English, Swahili)
        
        // Language detection settings
        'language_detection' => [
            'enabled' => true,
            'auto_switch' => true, // Auto switch to detected language
        ],
        
        // Swahili language settings
        'swahili' => [
            'enabled' => true,
            'model_path' => '/ai/models/swahili_processor.pkl',
            'dictionary_path' => '/ai/data/swahili_corpus.json',
            'financial_terms_path' => '/ai/data/kenyan_financial_corpus.json',
        ],
        
        // Code-switching support (mixing English and Swahili)
        'code_switching' => [
            'enabled' => true,
            'detection_threshold' => 0.6,
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | External API Integrations
    |--------------------------------------------------------------------------
    */
    'api_integrations' => [
        // Nairobi Securities Exchange (NSE) API
        'nse' => [
            'enabled' => true,
            'api_key' => env('NSE_API_KEY', ''),
            'api_url' => 'https://nairobi-stock-exchange-nse.p.rapidapi.com',
            'cache_ttl' => 900, // Cache timeout in seconds (15 minutes)
            'timeout' => 10, // Request timeout in seconds
        ],
        
        // Central Bank of Kenya (CBK) API
        'cbk' => [
            'enabled' => true,
            'api_key' => env('CBK_API_KEY', ''),
            'api_url' => 'https://cbk-bonds.p.rapidapi.com',
            'oauth_url' => 'https://cbk.go.ke/oauth/token',
            'cache_ttl' => 3600, // Cache timeout in seconds (1 hour)
        ],
        
        // M-Pesa API Integration
        'mpesa' => [
            'enabled' => true,
            'api_key' => env('MPESA_API_KEY', ''),
            'api_secret' => env('MPESA_API_SECRET', ''),
            'api_url' => 'https://m-pesa.p.rapidapi.com',
            'sandbox_url' => 'https://sandbox.safaricom.co.ke',
            'production_url' => 'https://api.safaricom.co.ke',
            'environment' => env('MPESA_ENVIRONMENT', 'sandbox'), // sandbox or production
        ],
        
        // Cryptocurrency data API
        'crypto' => [
            'enabled' => true,
            'provider' => 'coingecko', // Options: coingecko, coinmarketcap
            'api_key' => env('CRYPTO_API_KEY', ''),
            'api_url' => 'https://coingecko.p.rapidapi.com',
            'cache_ttl' => 300, // Cache timeout in seconds (5 minutes)
        ],
        
        // Exchange rates API
        'forex' => [
            'enabled' => true,
            'api_key' => env('FOREX_API_KEY', ''),
            'api_url' => 'https://exchange-rates7.p.rapidapi.com',
            'cache_ttl' => 3600, // Cache timeout in seconds (1 hour)
            'base_currency' => 'KES', // Kenyan Shilling as base currency
        ],
        
        // Financial News API
        'news' => [
            'enabled' => true,
            'api_key' => env('NEWS_API_KEY', ''),
            'api_url' => 'https://news-api14.p.rapidapi.com',
            'cache_ttl' => 1800, // Cache timeout in seconds (30 minutes)
            'topics' => ['finance', 'economy', 'stocks', 'kenya', 'business', 'investment'],
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | User Profiling and Personalization
    |--------------------------------------------------------------------------
    */
    'user_profiling' => [
        'enabled' => true,
        
        // Risk profiling
        'risk_profiling' => [
            'enabled' => true,
            'default_risk_level' => 'moderate', // Options: low, moderate, high
            'reassessment_period' => 90, // Days before prompting for reassessment
        ],
        
        // Financial goal tracking
        'financial_goals' => [
            'enabled' => true,
            'goal_types' => [
                'savings', 'investment', 'retirement', 'education', 
                'home_purchase', 'debt_repayment', 'business_startup'
            ],
        ],
        
        // User behavior tracking
        'user_behavior' => [
            'enabled' => true,
            'track_query_history' => true,
            'track_recommendations' => true,
            'track_feature_usage' => true,
        ],
        
        // Personalized recommendations
        'personalization' => [
            'enabled' => true,
            'min_interactions' => 5, // Minimum interactions before personalization
            'recommendation_frequency' => 'weekly', // How often to generate new recommendations
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Security and Compliance Settings
    |--------------------------------------------------------------------------
    */
    'security' => [
        // Data encryption settings
        'encryption' => [
            'enabled' => true,
            'method' => 'AES-256-CBC',
            'key' => env('ENCRYPTION_KEY', ''),
        ],
        
        // Role-based access control (RBAC)
        'rbac' => [
            'enabled' => true,
            'roles' => [
                'user', 'premium_user', 'admin', 'system'
            ],
        ],
        
        // Request rate limiting
        'rate_limiting' => [
            'enabled' => true,
            'max_requests' => 60, // Maximum requests per minute
            'throttle_threshold' => 80, // Percentage of max requests to start throttling
        ],
        
        // Data Privacy Compliance
        'data_privacy' => [
            'enabled' => true,
            'pdpa_compliant' => true, // Kenya's Data Protection Act
            'data_retention_period' => 365, // Days to keep user data
            'allow_data_deletion' => true, // Allow users to delete their data
        ],
        
        // Audit logging
        'audit_logging' => [
            'enabled' => true,
            'events' => [
                'login', 'logout', 'recommendation', 'transaction', 
                'profile_update', 'sensitive_data_access'
            ],
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Response Templates and Content Settings
    |--------------------------------------------------------------------------
    */
    'response_templates' => [
        // Common phrases and responses
        'greeting' => [
            'en' => 'Hello! I\'m PesaGuru, your personal financial advisor. How can I help you today?',
            'sw' => 'Habari! Mimi ni PesaGuru, mshauri wako wa kibinafsi wa fedha. Nawezaje kukusaidia leo?',
        ],
        
        'farewell' => [
            'en' => 'Thank you for using PesaGuru. Have a great day!',
            'sw' => 'Asante kwa kutumia PesaGuru. Uwe na siku njema!',
        ],
        
        'clarification' => [
            'en' => 'I\'m not sure I understood your question. Could you please rephrase it?',
            'sw' => 'Sijahakikisha kuwa nimeelewa swali lako. Je, unaweza kulieleza tena?',
        ],
        
        // Financial advice disclaimers
        'investment_disclaimer' => [
            'en' => 'Please note that this is general information and not personalized investment advice. Consider consulting a licensed financial advisor for specific investment decisions.',
            'sw' => 'Tafadhali kumbuka kuwa hii ni habari ya jumla na sio ushauri wa uwekezaji wa kibinafsi. Fikiria kushauriana na mshauri wa fedha aliyeidhinishwa kwa maamuzi maalum ya uwekezaji.',
        ],
        
        // Common financial education snippets
        'financial_education' => [
            'risk_explanation' => [
                'en' => 'Risk in investing refers to the possibility of losing money or not meeting your financial goals. Generally, higher potential returns come with higher risks.',
                'sw' => 'Hatari katika uwekezaji inahusu uwezekano wa kupoteza pesa au kutofanikisha malengo yako ya kifedha. Kwa kawaida, faida kubwa za uwekezaji huja na hatari kubwa.',
            ],
            'diversification' => [
                'en' => 'Diversification means spreading your investments across different assets to reduce risk. This is often described as "not putting all your eggs in one basket."',
                'sw' => 'Upanuzi wa uwekezaji inamaanisha kusambaza uwekezaji wako katika mali tofauti ili kupunguza hatari. Hii mara nyingi huelezewa kama "kutoweka mayai yako yote katika kikapu kimoja."',
            ],
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Cache Settings
    |--------------------------------------------------------------------------
    */
    'cache' => [
        'enabled' => true,
        'driver' => 'redis', // Options: redis, file, database
        
        // Redis cache settings
        'redis' => [
            'host' => env('REDIS_HOST', '127.0.0.1'),
            'port' => env('REDIS_PORT', 6379),
            'password' => env('REDIS_PASSWORD', null),
            'database' => env('REDIS_CACHE_DB', 1),
        ],
        
        // Cache TTL for different data types (in seconds)
        'ttl' => [
            'user_profile' => 86400, // 24 hours
            'market_data' => 900,    // 15 minutes
            'forex_rates' => 3600,   // 1 hour
            'interest_rates' => 86400, // 24 hours
            'stock_prices' => 300,   // 5 minutes
            'recommendations' => 86400, // 24 hours
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Logging and Monitoring
    |--------------------------------------------------------------------------
    */
    'logging' => [
        'enabled' => true,
        'level' => env('CHATBOT_LOG_LEVEL', 'info'), // Options: debug, info, warning, error
        'file_path' => storage_path('logs/chatbot.log'),
        
        // Performance monitoring
        'performance_monitoring' => [
            'enabled' => true,
            'track_response_time' => true,
            'track_model_accuracy' => true,
            'track_api_reliability' => true,
        ],
        
        // Error tracking
        'error_tracking' => [
            'enabled' => true,
            'notify_on_error' => true, // Send notifications on critical errors
            'error_threshold' => 5, // Number of errors before notification
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Feature Flags for A/B Testing
    |--------------------------------------------------------------------------
    */
    'feature_flags' => [
        'voice_interface' => false,        // Voice recognition feature
        'financial_calculators' => true,    // Financial calculators
        'crypto_recommendations' => true,   // Cryptocurrency investment recommendations
        'loan_comparison' => true,          // Loan comparison feature
        'retirement_planning' => true,      // Retirement planning module
        'budget_analysis' => true,          // Budget analysis feature
        'stock_alerts' => false,            // Real-time stock alerts feature
        'webinar_integration' => false,     // Webinar registration integration
    ],
];