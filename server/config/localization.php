<?php

// Include helper functions
require_once __DIR__ . '/helpers.php';

return [
    /*
    |--------------------------------------------------------------------------
    | Default Locale
    |--------------------------------------------------------------------------
    |
    | The default locale for the application. This will be used when no specific
    | locale is requested by the user.
    |
    */
    'default_locale' => 'en',

    /*
    |--------------------------------------------------------------------------
    | Supported Locales
    |--------------------------------------------------------------------------
    |
    | The list of all supported locales for the application. English and Swahili
    | are official languages in Kenya and are fully supported.
    |
    */
    'supported_locales' => [
        'en' => [
            'name' => 'English',
            'native' => 'English',
            'direction' => 'ltr',
            'flag' => 'gb',
            'enabled' => true,
        ],
        'sw' => [
            'name' => 'Swahili',
            'native' => 'Kiswahili',
            'direction' => 'ltr',
            'flag' => 'ke',
            'enabled' => true,
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Date and Time Formats
    |--------------------------------------------------------------------------
    |
    | Defines the date and time formats for each supported locale.
    |
    */
    'date_formats' => [
        'en' => [
            'date' => 'd/m/Y',
            'time' => 'h:i A',
            'datetime' => 'd/m/Y h:i A',
            'short_date' => 'd/m/y',
        ],
        'sw' => [
            'date' => 'd/m/Y',
            'time' => 'H:i',
            'datetime' => 'd/m/Y H:i',
            'short_date' => 'd/m/y',
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Currency Settings
    |--------------------------------------------------------------------------
    |
    | Currency formatting for each supported locale.
    |
    */
    'currency' => [
        'default' => 'KES',
        'display_symbol' => true,
        'formats' => [
            'en' => [
                'KES' => 'KES {amount}',
                'USD' => 'USD {amount}',
                'EUR' => 'EUR {amount}',
                'GBP' => 'GBP {amount}',
            ],
            'sw' => [
                'KES' => 'KSh {amount}',
                'USD' => 'Dola {amount}',
                'EUR' => 'Yuro {amount}',
                'GBP' => 'Pauni {amount}',
            ],
        ],
        'decimal_separator' => '.',
        'thousand_separator' => ',',
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Numbers Settings
    |--------------------------------------------------------------------------
    |
    | Number formatting for each supported locale.
    |
    */
    'numbers' => [
        'en' => [
            'decimal_separator' => '.',
            'thousand_separator' => ',',
            'precision' => 2,
        ],
        'sw' => [
            'decimal_separator' => '.',
            'thousand_separator' => ',',
            'precision' => 2,
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Language Detection
    |--------------------------------------------------------------------------
    |
    | Settings for language detection and code-switching.
    |
    */
    'language_detection' => [
        'enabled' => true,
        'cookie_name' => 'pesaguru_locale',
        'cookie_lifetime' => 30 * 24 * 60 * 60, // 30 days
        'header_detection' => true,
        'detect_from_url' => true,
        'detect_from_user_setting' => true,
        'code_switching' => [
            'enabled' => true,
            'threshold' => 0.6, // Confidence threshold for code-switching detection
            'fallback' => 'en',
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | NLP & Dialect Support
    |--------------------------------------------------------------------------
    |
    | Settings for dialect support, including Sheng and regional variations.
    |
    */
    'dialect_support' => [
        'sheng' => [
            'enabled' => true,
            'dictionary_path' => storage_path('app/dictionaries/sheng.json'),
            'fallback_language' => 'sw',
        ],
        'regional_variations' => [
            'enabled' => true,
            'regions' => [
                'nairobi' => [
                    'dictionary_path' => storage_path('app/dictionaries/nairobi_dialect.json'),
                ],
                'coastal' => [
                    'dictionary_path' => storage_path('app/dictionaries/coastal_dialect.json'),
                ],
                'western' => [
                    'dictionary_path' => storage_path('app/dictionaries/western_dialect.json'),
                ],
            ],
        ],
        'financial_terms' => [
            'dictionary_path' => storage_path('app/dictionaries/financial_terms.json'),
            'slang_mapping_path' => storage_path('app/dictionaries/financial_slang.json'),
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Voice Recognition Settings
    |--------------------------------------------------------------------------
    |
    | Settings for voice-to-text functionality in English and Swahili.
    |
    */
    'voice_recognition' => [
        'enabled' => true,
        'api_endpoint' => env('VOICE_RECOGNITION_API', 'https://api.pesaguru.com/voice'),
        'english' => [
            'enabled' => true,
            'model' => 'en-KE', // English with Kenyan accent
        ],
        'swahili' => [
            'enabled' => true,
            'model' => 'sw-KE', // Kenyan Swahili
        ],
        'timeout' => 10, // Timeout in seconds
        'max_duration' => 60, // Max recording duration in seconds
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Translation Settings
    |--------------------------------------------------------------------------
    |
    | Configuration for translation service.
    |
    */
    'translation' => [
        'enabled' => true,
        'service' => env('TRANSLATION_SERVICE', 'google'), // Options: google, tessa, local
        'api_key' => env('TRANSLATION_API_KEY', ''),
        'cache_translations' => true,
        'cache_lifetime' => 24 * 60 * 60, // 24 hours
        'fallback' => [
            'enabled' => true,
            'locale' => 'en',
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Financial Term Localization
    |--------------------------------------------------------------------------
    |
    | Specialized financial terminology mapping between languages.
    |
    */
    'financial_terms' => [
        'enabled' => true,
        'dictionary_path' => storage_path('app/dictionaries/financial_dictionary.json'),
        'mapping' => [
            // Common financial terms for both languages
            'investment' => [
                'en' => 'investment',
                'sw' => 'uwekezaji',
            ],
            'savings' => [
                'en' => 'savings',
                'sw' => 'akiba',
            ],
            'loan' => [
                'en' => 'loan',
                'sw' => 'mkopo',
            ],
            'interest' => [
                'en' => 'interest',
                'sw' => 'riba',
            ],
            'budget' => [
                'en' => 'budget',
                'sw' => 'bajeti',
            ],
            'stock' => [
                'en' => 'stock',
                'sw' => 'hisa',
            ],
            'bank' => [
                'en' => 'bank',
                'sw' => 'benki',
            ],
            'mobile_money' => [
                'en' => 'mobile money',
                'sw' => 'pesa ya simu',
            ],
            'exchange_rate' => [
                'en' => 'exchange rate',
                'sw' => 'kiwango cha ubadilishaji',
            ],
            'profit' => [
                'en' => 'profit',
                'sw' => 'faida',
            ],
            'loss' => [
                'en' => 'loss',
                'sw' => 'hasara',
            ],
        ],
    ],
    
    /*
    |--------------------------------------------------------------------------
    | Content Localization Paths
    |--------------------------------------------------------------------------
    |
    | Paths for localized content.
    |
    */
    'content' => [
        'translations_path' => resource_path('lang'),
        'locale_js_path' => public_path('js/locales'),
        'assets_path' => public_path('assets/locales'),
    ],
    
    /*
    |--------------------------------------------------------------------------
    | SEO Localization
    |--------------------------------------------------------------------------
    |
    | Settings for SEO localization.
    |
    */
    'seo' => [
        'add_alternate_links' => true,
        'default_keywords' => [
            'en' => 'financial advisor, Kenyan finance, investment, savings, loans, budget, financial planning',
            'sw' => 'mshauri wa fedha, fedha ya Kenya, uwekezaji, akiba, mikopo, bajeti, mipango ya fedha',
        ],
    ],
];