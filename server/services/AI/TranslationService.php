<?php
namespace App\Services\AI;

class TranslationService {
    // Simple translation dictionaries for demo purposes
    // In a real app, you'd use a proper translation API or service
    private $enToSwDict = [
        'hello' => 'jambo',
        'hi' => 'hujambo',
        'good morning' => 'habari ya asubuhi',
        'good afternoon' => 'habari ya mchana',
        'good evening' => 'habari ya jioni',
        'how are you' => 'habari yako',
        'investment' => 'uwekezaji',
        'money' => 'pesa',
        'loan' => 'mkopo',
        'interest' => 'riba',
        'stock' => 'hisa',
        'price' => 'bei',
        'market' => 'soko',
        'bank' => 'benki',
        'account' => 'akaunti',
        'savings' => 'akiba',
        'financial' => 'kifedha',
        'goal' => 'lengo',
        'retirement' => 'kustaafu',
        'education' => 'elimu',
        'house' => 'nyumba',
        'car' => 'gari',
        'budget' => 'bajeti',
        'expense' => 'gharama',
        'income' => 'mapato',
        'debt' => 'deni',
        'credit' => 'mkopo',
        'payment' => 'malipo',
        'inflation' => 'mfumuko wa bei',
        'tax' => 'kodi',
        'profit' => 'faida',
        'loss' => 'hasara'
    ];
    
    private $swToEnDict = [];
    
    public function __construct() {
        // Create the reverse dictionary for Swahili to English
        $this->swToEnDict = array_flip($this->enToSwDict);
    }
    
    /**
     * Translate text from English to another language
     * @param string $text Text to translate
     * @param string $targetLang Target language code
     * @return string Translated text
     */
    public function translateFromEnglish($text, $targetLang) {
        if ($targetLang === 'en') {
            return $text;
        }
        
        if ($targetLang === 'sw') {
            return $this->translateToSwahili($text);
        }
        
        // Default to original text if language not supported
        return $text;
    }
    
    /**
     * Translate text to English from another language
     * @param string $text Text to translate
     * @param string $sourceLang Source language code
     * @return string Translated text
     */
    public function translateToEnglish($text, $sourceLang) {
        if ($sourceLang === 'en') {
            return $text;
        }
        
        if ($sourceLang === 'sw') {
            return $this->translateFromSwahili($text);
        }
        
        // Default to original text if language not supported
        return $text;
    }
    
    /**
     * Simple English to Swahili translation
     * @param string $text English text
     * @return string Swahili text
     */
    private function translateToSwahili($text) {
        $lcText = strtolower($text);
        
        // Check for exact matches in dictionary
        if (isset($this->enToSwDict[$lcText])) {
            return $this->enToSwDict[$lcText];
        }
        
        // Replace words we know
        foreach ($this->enToSwDict as $en => $sw) {
            $pattern = '/\b' . preg_quote($en, '/') . '\b/i';
            $text = preg_replace($pattern, $sw, $text);
        }
        
        return $text;
    }
    
    /**
     * Simple Swahili to English translation
     * @param string $text Swahili text
     * @return string English text
     */
    private function translateFromSwahili($text) {
        $lcText = strtolower($text);
        
        // Check for exact matches in dictionary
        if (isset($this->swToEnDict[$lcText])) {
            return $this->swToEnDict[$lcText];
        }
        
        // Replace words we know
        foreach ($this->swToEnDict as $sw => $en) {
            $pattern = '/\b' . preg_quote($sw, '/') . '\b/i';
            $text = preg_replace($pattern, $en, $text);
        }
        
        return $text;
    }
}