<?php

class LocalizationMiddleware {
    // Default language if none is specified
    private $defaultLanguage = 'en';
    
    // Supported languages
    private $supportedLanguages = ['en', 'sw'];
    
    // Current language
    private $currentLanguage;
    
    // Language files cache
    private $translations = [];
    
    // Path to language files
    private $langFilesPath;
    
    /**
     * Constructor
     */
    public function __construct() {
        // Set path to language files
        $this->langFilesPath = __DIR__ . '/../resources/lang/';
        
        // Load configuration
        $this->loadConfig();
    }
    
    /**
     * Load configuration from the localization config file
     */
    private function loadConfig() {
        $configPath = __DIR__ . '/../config/localization.php';
        
        if (file_exists($configPath)) {
            $config = include $configPath;
            
            if (isset($config['default_language'])) {
                $this->defaultLanguage = $config['default_language'];
            }
            
            if (isset($config['supported_languages']) && is_array($config['supported_languages'])) {
                $this->supportedLanguages = $config['supported_languages'];
            }
            
            if (isset($config['lang_files_path'])) {
                $this->langFilesPath = $config['lang_files_path'];
            }
        }
    }
    
    /**
     * Main middleware function to process the request
     * 
     * @param object $request The request object
     * @param callable $next The next middleware function
     * @return mixed
     */
    public function handle($request, $next) {
        // Detect and set the current language
        $this->detectLanguage($request);
        
        // Load translations for the current language
        $this->loadTranslations();
        
        // Set locale for PHP functions
        $this->setLocale();
        
        // Add translation function to the request
        $request->translate = function($key, $replacements = []) {
            return $this->translate($key, $replacements);
        };
        
        // Add language switcher to the request
        $request->switchLanguage = function($lang) {
            return $this->switchLanguage($lang);
        };
        
        // Add language detector for mixed content
        $request->detectTextLanguage = function($text) {
            return $this->detectTextLanguage($text);
        };
        
        // Continue to the next middleware
        return $next($request);
    }
    
    /**
     * Detect the user's preferred language from various sources
     * 
     * @param object $request The request object
     */
    private function detectLanguage($request) {
        // Default to the default language
        $this->currentLanguage = $this->defaultLanguage;
        
        // Priority 1: Explicit language parameter in the request
        if (isset($_GET['lang']) && in_array($_GET['lang'], $this->supportedLanguages)) {
            $this->currentLanguage = $_GET['lang'];
        }
        
        // Priority 2: Language from session if available
        else if (isset($_SESSION['lang']) && in_array($_SESSION['lang'], $this->supportedLanguages)) {
            $this->currentLanguage = $_SESSION['lang'];
        }
        
        // Priority 3: Language from user profile if logged in
        else if (isset($request->user) && 
                 isset($request->user->language) && 
                 in_array($request->user->language, $this->supportedLanguages)) {
            $this->currentLanguage = $request->user->language;
        }
        
        // Priority 4: Language from Accept-Language header
        else if (isset($_SERVER['HTTP_ACCEPT_LANGUAGE'])) {
            $langs = explode(',', $_SERVER['HTTP_ACCEPT_LANGUAGE']);
            foreach ($langs as $lang) {
                $lang = substr($lang, 0, 2); // Get first two characters
                if (in_array($lang, $this->supportedLanguages)) {
                    $this->currentLanguage = $lang;
                    break;
                }
            }
        }
        
        // Store the detected language in the session for future requests
        $_SESSION['lang'] = $this->currentLanguage;
    }
    
    /**
     * Set the PHP locale based on the current language
     */
    private function setLocale() {
        $localeMap = [
            'en' => 'en_US.UTF-8',
            'sw' => 'sw_KE.UTF-8',
        ];
        
        $locale = isset($localeMap[$this->currentLanguage]) ? 
                  $localeMap[$this->currentLanguage] : 
                  $localeMap[$this->defaultLanguage];
        
        // Set the locale for PHP functions
        setlocale(LC_ALL, $locale);
        
        // Set the timezone for Kenya
        date_default_timezone_set('Africa/Nairobi');
    }
    
    /**
     * Load translations for the current language
     */
    private function loadTranslations() {
        // Skip if already loaded
        if (isset($this->translations[$this->currentLanguage])) {
            return;
        }
        
        $langFile = $this->langFilesPath . $this->currentLanguage . '.php';
        
        if (file_exists($langFile)) {
            $this->translations[$this->currentLanguage] = include $langFile;
        } else {
            // Load default language if current language file is missing
            $defaultLangFile = $this->langFilesPath . $this->defaultLanguage . '.php';
            if (file_exists($defaultLangFile)) {
                $this->translations[$this->currentLanguage] = include $defaultLangFile;
            } else {
                $this->translations[$this->currentLanguage] = [];
            }
        }
    }
    
    /**
     * Translate a key from the language file
     * 
     * @param string $key The translation key
     * @param array $replacements Replacements for placeholders
     * @return string The translated string
     */
    public function translate($key, $replacements = []) {
        // Split the key by dots to access nested translations
        $keys = explode('.', $key);
        
        // Get the translations array
        $translation = $this->translations[$this->currentLanguage];
        
        // Navigate through the keys
        foreach ($keys as $nestedKey) {
            if (isset($translation[$nestedKey])) {
                $translation = $translation[$nestedKey];
            } else {
                // Key not found, return the original key
                return $key;
            }
        }
        
        // If translation is an array, return it as JSON
        if (is_array($translation)) {
            return json_encode($translation);
        }
        
        // Replace placeholders
        foreach ($replacements as $placeholder => $value) {
            $translation = str_replace(':' . $placeholder, $value, $translation);
        }
        
        return $translation;
    }
    
    /**
     * Switch to a different language
     * 
     * @param string $lang The language code to switch to
     * @return bool Success of the operation
     */
    public function switchLanguage($lang) {
        if (in_array($lang, $this->supportedLanguages)) {
            $this->currentLanguage = $lang;
            $_SESSION['lang'] = $lang;
            $this->loadTranslations();
            $this->setLocale();
            return true;
        }
        
        return false;
    }
    
    /**
     * Detect the language of a given text
     * Includes code-switching detection (mixture of English and Swahili)
     * 
     * @param string $text The text to analyze
     * @return array The detected languages and their confidence scores
     */
    public function detectTextLanguage($text) {
        // Initialize result
        $result = [
            'primary_language' => $this->defaultLanguage,
            'confidence' => 0,
            'is_mixed' => false,
            'languages' => [
                'en' => 0,
                'sw' => 0
            ]
        ];
        
        // If text is empty, return default
        if (empty($text)) {
            return $result;
        }
        
        // Load common Swahili words for detection
        $commonSwahiliWords = $this->getCommonSwahiliWords();
        
        // Load common English words for detection
        $commonEnglishWords = $this->getCommonEnglishWords();
        
        // Load sheng/slang dictionary for Kenyan financial context
        $shengDictionary = $this->getShengDictionary();
        
        // Prepare text for analysis
        $text = strtolower($text);
        $words = preg_split('/\s+/', $text);
        
        // Count matches for each language
        $enCount = 0;
        $swCount = 0;
        $shengCount = 0;
        
        foreach ($words as $word) {
            // Clean the word
            $word = preg_replace('/[^\p{L}\p{N}]/u', '', $word);
            
            if (empty($word)) continue;
            
            // Check if it's a common Swahili word
            if (in_array($word, $commonSwahiliWords)) {
                $swCount++;
            }
            // Check if it's a common English word
            else if (in_array($word, $commonEnglishWords)) {
                $enCount++;
            }
            // Check if it's a sheng/slang word
            else if (array_key_exists($word, $shengDictionary)) {
                $shengCount++;
                // Add to the language count based on sheng origin
                if ($shengDictionary[$word]['origin'] === 'sw') {
                    $swCount += 0.5;
                } else {
                    $enCount += 0.5;
                }
            }
            // Basic heuristic for unrecognized words
            else {
                // Words ending with vowels are more likely to be Swahili
                if (preg_match('/[aeiou]$/i', $word)) {
                    $swCount += 0.2;
                } else {
                    $enCount += 0.2;
                }
            }
        }
        
        // Calculate total and percentages
        $totalWords = count($words);
        $enPercent = ($totalWords > 0) ? ($enCount / $totalWords) * 100 : 0;
        $swPercent = ($totalWords > 0) ? ($swCount / $totalWords) * 100 : 0;
        
        // Determine primary language and if it's mixed
        $isPrimarilyEnglish = $enPercent > $swPercent;
        $isMixed = ($enPercent > 20 && $swPercent > 20) || $shengCount > 0;
        
        $result['primary_language'] = $isPrimarilyEnglish ? 'en' : 'sw';
        $result['confidence'] = $isPrimarilyEnglish ? $enPercent : $swPercent;
        $result['is_mixed'] = $isMixed;
        $result['languages']['en'] = $enPercent;
        $result['languages']['sw'] = $swPercent;
        $result['sheng_count'] = $shengCount;
        
        return $result;
    }
    
    /**
     * Get a list of common Swahili words for language detection
     * Focused on financial terminology for the PesaGuru context
     * 
     * @return array List of common Swahili words
     */
    private function getCommonSwahiliWords() {
        return [
            // Common Swahili words
            'na', 'ya', 'wa', 'kwa', 'ni', 'katika', 'za', 'kuwa', 'kama',
            'lakini', 'pia', 'hata', 'au', 'hii', 'hiyo', 'huu', 'huo',
            'mimi', 'wewe', 'yeye', 'sisi', 'nyinyi', 'wao', 'huyu', 'huyo',
            'nataka', 'unataka', 'anataka', 'tunataka', 'mnataka', 'wanataka',
            'ndiyo', 'hapana', 'kwaheri', 'asante', 'pole', 'tafadhali',
            
            // Financial terms in Swahili
            'pesa', 'fedha', 'biashara', 'benki', 'akaunti', 'bima',
            'faida', 'hasara', 'deni', 'mkopo', 'riba', 'malipo',
            'bajeti', 'matumizi', 'mapato', 'gharama', 'bei', 'soko',
            'hisa', 'uwekezaji', 'mtaji', 'mfanyabiashara', 'kodi',
            'kuhifadhi', 'kutuma', 'kupokea', 'mauzo', 'ununuzi',
            'mnada', 'mwenye', 'hati', 'amana', 'hazina', 'thamani'
        ];
    }
    
    /**
     * Get a list of common English words for language detection
     * Focused on financial terminology for the PesaGuru context
     * 
     * @return array List of common English words
     */
    private function getCommonEnglishWords() {
        return [
            // Common English words
            'the', 'and', 'to', 'of', 'a', 'in', 'is', 'that', 'for', 'it',
            'with', 'as', 'was', 'be', 'by', 'on', 'not', 'this', 'but', 'from',
            'i', 'you', 'he', 'she', 'we', 'they', 'my', 'your', 'his', 'her',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'can', 'could',
            
            // Financial terms in English
            'money', 'bank', 'account', 'investment', 'loan', 'credit', 'debit',
            'finance', 'financial', 'budget', 'income', 'expense', 'savings',
            'interest', 'profit', 'loss', 'debt', 'stock', 'market', 'payment',
            'transaction', 'balance', 'wealth', 'portfolio', 'capital', 'dividend',
            'mortgage', 'insurance', 'tax', 'retirement', 'pension', 'deposit',
            'withdraw', 'transfer', 'equity', 'bond', 'fund', 'rate', 'share',
            'invest', 'save', 'spend', 'borrow', 'lend', 'cost', 'price'
        ];
    }
    
    /**
     * Get a dictionary of Sheng/slang terms used in Kenyan financial context
     * 
     * @return array Dictionary of sheng terms with meanings and language origins
     */
    private function getShengDictionary() {
        return [
            // Financial sheng/slang terminology from Kenya
            'kula' => ['meaning' => 'to invest', 'origin' => 'sw'],
            'moneypesa' => ['meaning' => 'funds', 'origin' => 'mixed'],
            'kuomoka' => ['meaning' => 'to grow/profit', 'origin' => 'sw'],
            'kadapa' => ['meaning' => 'small money', 'origin' => 'sw'],
            'ndai' => ['meaning' => 'money', 'origin' => 'sw'],
            'mula' => ['meaning' => 'money', 'origin' => 'en'],
            'mbao' => ['meaning' => '20 shillings', 'origin' => 'sw'],
            'mangwaru' => ['meaning' => 'coins', 'origin' => 'sw'],
            'kamwewe' => ['meaning' => 'ATM', 'origin' => 'sw'],
            'cashbeka' => ['meaning' => 'withdraw money', 'origin' => 'mixed'],
            'cheza kama wewe' => ['meaning' => 'invest confidently', 'origin' => 'sw'],
            'kuchimba hazina' => ['meaning' => 'to save money', 'origin' => 'sw'],
            'kupiga deve' => ['meaning' => 'to default on a loan', 'origin' => 'sw'],
            'kupata kaloans' => ['meaning' => 'to get small loans', 'origin' => 'mixed'],
            'kuna stock haijajam' => ['meaning' => 'reliable stock', 'origin' => 'mixed'],
            'kushika pesa' => ['meaning' => 'to save money', 'origin' => 'sw'],
            'kutengeneza barubaru' => ['meaning' => 'to make profit', 'origin' => 'sw'],
            'nipe mashapu' => ['meaning' => 'give me options', 'origin' => 'sw'],
            'hizi rates ni za juu' => ['meaning' => 'these rates are high', 'origin' => 'mixed'],
            'hii investment itanisort' => ['meaning' => 'this investment will help me', 'origin' => 'mixed'],
            'nafurahi kula hii nsacoo' => ['meaning' => 'glad to join this SACCO', 'origin' => 'mixed'],
            'ninataka kuloan' => ['meaning' => 'I want to take a loan', 'origin' => 'mixed'],
            'hii interest inakulenga' => ['meaning' => 'this interest targets you', 'origin' => 'mixed']
        ];
    }
    
    /**
     * Get the current language
     * 
     * @return string Current language code
     */
    public function getCurrentLanguage() {
        return $this->currentLanguage;
    }
    
    /**
     * Get list of supported languages
     * 
     * @return array List of supported language codes
     */
    public function getSupportedLanguages() {
        return $this->supportedLanguages;
    }
}

// For standalone usage
if (!function_exists('t')) {
    /**
     * Global translation helper function
     * 
     * @param string $key The translation key
     * @param array $replacements Replacements for placeholders
     * @return string The translated string
     */
    function t($key, $replacements = []) {
        global $localizationMiddleware;
        
        if (isset($localizationMiddleware) && $localizationMiddleware instanceof LocalizationMiddleware) {
            return $localizationMiddleware->translate($key, $replacements);
        }
        
        return $key;
    }
}