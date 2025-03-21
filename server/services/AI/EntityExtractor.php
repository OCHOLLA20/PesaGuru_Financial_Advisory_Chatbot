<?php
namespace App\Services\AI;

class EntityExtractor {
    // Kenyan stock symbols for entity recognition
    private $stockSymbols = [
        'SCOM' => 'Safaricom',
        'EQTY' => 'Equity Group',
        'KCB' => 'KCB Group',
        'COOP' => 'Co-operative Bank',
        'EABL' => 'East African Breweries',
        'KNRE' => 'Kenya Re',
        'BAMB' => 'Bamburi Cement',
        'KPLC' => 'Kenya Power',
        'NMG' => 'Nation Media Group',
        'JUB' => 'Jubilee Insurance'
    ];
    
    /**
     * Extract entities from user message based on intent
     * @param string $message User message
     * @param string $intent Classified intent
     * @return array Extracted entities
     */
    public function extract($message, $intent) {
        $entities = [];
        
        // Use different extraction methods based on intent
        switch ($intent) {
            case 'get_stock_price':
                $entities = array_merge($entities, $this->extractStockSymbols($message));
                break;
                
            case 'investment_recommendation':
            case 'loan_inquiry':
                $entities = array_merge($entities, $this->extractAmounts($message));
                $entities = array_merge($entities, $this->extractDuration($message));
                break;
                
            case 'financial_goal':
                $entities = array_merge($entities, $this->extractGoalType($message));
                $entities = array_merge($entities, $this->extractAmounts($message));
                $entities = array_merge($entities, $this->extractDuration($message));
                break;
        }
        
        return $entities;
    }
    
    /**
     * Extract stock symbols from message
     * @param string $message User message
     * @return array Extracted stock symbols
     */
    private function extractStockSymbols($message) {
        $entities = [];
        $message = strtoupper($message);
        
        // Check for stock symbols
        foreach ($this->stockSymbols as $symbol => $name) {
            if (strpos($message, $symbol) !== false || 
                stripos($message, $name) !== false) {
                $entities['stock_symbol'] = $symbol;
                $entities['company_name'] = $name;
                break;
            }
        }
        
        // If no match found, look for common company references
        if (!isset($entities['stock_symbol'])) {
            $companyMatches = [
                'safaricom' => 'SCOM',
                'equity' => 'EQTY',
                'kcb' => 'KCB',
                'co-operative' => 'COOP',
                'coop' => 'COOP',
                'cooperative' => 'COOP',
                'eabl' => 'EABL',
                'breweries' => 'EABL',
                'kenya re' => 'KNRE',
                'bamburi' => 'BAMB',
                'cement' => 'BAMB',
                'kenya power' => 'KPLC',
                'kplc' => 'KPLC',
                'nation media' => 'NMG',
                'jubilee' => 'JUB'
            ];
            
            foreach ($companyMatches as $term => $symbol) {
                if (stripos($message, $term) !== false) {
                    $entities['stock_symbol'] = $symbol;
                    $entities['company_name'] = $this->stockSymbols[$symbol];
                    break;
                }
            }
        }
        
        return $entities;
    }
    
    /**
     * Extract monetary amounts from message
     * @param string $message User message
     * @return array Extracted amounts
     */
    private function extractAmounts($message) {
        $entities = [];
        
        // Check for KES amounts
        $patterns = [
            '/(?:KES|KSh|Ksh|Kshs|Sh|shillings?)\s*([0-9,]+(\.[0-9]{1,2})?)/i',
            '/([0-9,]+(\.[0-9]{1,2})?)\s*(?:KES|KSh|Ksh|Kshs|Sh|shillings?)/i',
            '/([0-9,]+(\.[0-9]{1,2})?)\s*(?:thousand|million|billion)/i'
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match($pattern, $message, $matches)) {
                $amount = str_replace(',', '', $matches[1]);
                
                // Handle "thousand", "million", etc.
                if (stripos($matches[0], 'thousand') !== false) {
                    $amount *= 1000;
                } else if (stripos($matches[0], 'million') !== false) {
                    $amount *= 1000000;
                } else if (stripos($matches[0], 'billion') !== false) {
                    $amount *= 1000000000;
                }
                
                $entities['amount'] = $amount;
                break;
            }
        }
        
        // If no amount with currency found, try to find numeric values
        if (!isset($entities['amount']) && preg_match('/\b([0-9,]+(\.[0-9]{1,2})?)\b/', $message, $matches)) {
            $entities['amount'] = str_replace(',', '', $matches[1]);
        }
        
        return $entities;
    }
    
    /**
     * Extract time duration from message
     * @param string $message User message
     * @return array Extracted duration
     */
    private function extractDuration($message) {
        $entities = [];
        
        // Check for durations
        $patterns = [
            '/([0-9]+)\s*(?:day|days)/i' => 'days',
            '/([0-9]+)\s*(?:week|weeks)/i' => 'weeks',
            '/([0-9]+)\s*(?:month|months)/i' => 'months',
            '/([0-9]+)\s*(?:year|years)/i' => 'years',
            '/([0-9]+)\s*(?:decade|decades)/i' => 'decades'
        ];
        
        foreach ($patterns as $pattern => $unit) {
            if (preg_match($pattern, $message, $matches)) {
                $value = $matches[1];
                $entities['duration'] = "$value $unit";
                $entities['duration_value'] = $value;
                $entities['duration_unit'] = $unit;
                break;
            }
        }
        
        // Check for common duration phrases
        $durationPhrases = [
            '/(?:short|near)\s*term/i' => '1 year',
            '/medium\s*term/i' => '3 years',
            '/(?:long|longer)\s*term/i' => '5 years',
            '/retirement/i' => '20 years' // Assumption
        ];
        
        if (!isset($entities['duration'])) {
            foreach ($durationPhrases as $pattern => $duration) {
                if (preg_match($pattern, $message)) {
                    $entities['duration'] = $duration;
                    if (strpos($duration, 'year') !== false) {
                        $value = (int) $duration;
                        $entities['duration_value'] = $value;
                        $entities['duration_unit'] = 'years';
                    }
                    break;
                }
            }
        }
        
        return $entities;
    }
    
    /**
     * Extract financial goal type from message
     * @param string $message User message
     * @return array Extracted goal type
     */
    private function extractGoalType($message) {
        $entities = [];
        
        // Check for goal types
        $goalTypes = [
            'emergency' => ['/emergency\s*fund/i', '/rainy\s*day/i', '/unexpected\s*expense/i'],
            'retirement' => ['/retirement/i', '/retire/i', '/pension/i'],
            'education' => ['/education/i', '/school/i', '/college/i', '/university/i', '/tuition/i'],
            'home' => ['/home/i', '/house/i', '/apartment/i', '/mortgage/i', '/down\s*payment/i'],
            'car' => ['/car/i', '/vehicle/i', '/automobile/i'],
            'vacation' => ['/vacation/i', '/holiday/i', '/trip/i', '/travel/i'],
            'wedding' => ['/wedding/i', '/marriage/i'],
            'business' => ['/business/i', '/startup/i', '/entrepreneurship/i', '/venture/i'],
            'debt_repayment' => ['/debt/i', '/loan\s*repayment/i', '/pay\s*off/i']
        ];
        
        foreach ($goalTypes as $type => $patterns) {
            foreach ($patterns as $pattern) {
                if (preg_match($pattern, $message)) {
                    $entities['goal_type'] = $type;
                    break 2;
                }
            }
        }
        
        return $entities;
    }
}