<?php

namespace PesaGuru\Middlewares;

class ApiValidationMiddleware {
    /**
     * The validation rules for different API endpoints
     */
    private $validationRules = [
        // User-related endpoints
        'user/register' => [
            'email' => ['required', 'email'],
            'password' => ['required', 'min:8', 'password_strength'],
            'name' => ['required', 'string', 'max:100'],
            'phone' => ['required', 'phone:KE'], // Kenyan phone format
        ],
        'user/update' => [
            'name' => ['string', 'max:100'],
            'phone' => ['phone:KE'],
            'risk_profile' => ['in:conservative,moderate,aggressive']
        ],
        
        // Financial advisory endpoints
        'chatbot/query' => [
            'message' => ['required', 'string', 'max:500'],
            'context_id' => ['string'],
            'language' => ['in:en,sw'], // English or Swahili
        ],
        'portfolio/analyze' => [
            'portfolio_data' => ['required', 'json'],
            'time_horizon' => ['required', 'in:short,medium,long'],
        ],
        'investment/recommend' => [
            'amount' => ['required', 'numeric', 'min:1000'],
            'risk_level' => ['required', 'in:low,medium,high'],
            'investment_period' => ['required', 'integer', 'min:1'],
        ],
        'market/data' => [
            'symbol' => ['string', 'max:10'],
            'from_date' => ['date_format:Y-m-d'],
            'to_date' => ['date_format:Y-m-d'],
        ],
        
        // Payment and transaction endpoints
        'payment/process' => [
            'amount' => ['required', 'numeric', 'min:10'],
            'currency' => ['required', 'in:KES,USD'],
            'payment_method' => ['required', 'in:mpesa,card,bank'],
            'phone' => ['required_if:payment_method,mpesa', 'phone:KE'],
        ],
    ];
    
    /**
     * Custom error messages
     */
    private $errorMessages = [
        'required' => 'The :field field is required.',
        'email' => 'The :field must be a valid email address.',
        'min' => 'The :field must be at least :param characters.',
        'max' => 'The :field must not exceed :param characters.',
        'numeric' => 'The :field must be a number.',
        'in' => 'The :field must be one of: :param.',
        'date_format' => 'The :field must be in the format: :param.',
        'phone' => 'The :field must be a valid phone number.',
        'json' => 'The :field must be a valid JSON string.',
        'password_strength' => 'The password must contain at least one uppercase letter, one lowercase letter, and one number.',
    ];
    
    /**
     * Execute the middleware
     * 
     * @param array $request The request data
     * @param callable $next The next middleware
     * @return mixed
     */
    public function __invoke($request, $next) {
        // Get the endpoint from the request URI
        $uri = $_SERVER['REQUEST_URI'];
        $endpoint = $this->extractEndpoint($uri);
        
        // Check if we have validation rules for this endpoint
        if (isset($this->validationRules[$endpoint])) {
            $rules = $this->validationRules[$endpoint];
            $errors = $this->validateRequest($request, $rules);
            
            // If there are validation errors, return them
            if (!empty($errors)) {
                header('Content-Type: application/json');
                http_response_code(422); // Unprocessable Entity
                echo json_encode([
                    'status' => 'error',
                    'message' => 'Validation failed',
                    'errors' => $errors
                ]);
                exit;
            }
            
            // Sanitize the input data
            $request = $this->sanitizeInput($request);
        }
        
        // Call the next middleware or controller
        return $next($request);
    }
    
    /**
     * Extract the endpoint from the URI
     * 
     * @param string $uri The request URI
     * @return string The endpoint
     */
    private function extractEndpoint($uri) {
        // Remove query string
        $uri = strtok($uri, '?');
        
        // Remove API prefix if present
        $uri = preg_replace('/^\/api\//', '', $uri);
        
        // Remove leading and trailing slashes
        $uri = trim($uri, '/');
        
        return $uri;
    }
    
    /**
     * Validate the request against the rules
     * 
     * @param array $request The request data
     * @param array $rules The validation rules
     * @return array Validation errors
     */
    private function validateRequest($request, $rules) {
        $errors = [];
        
        foreach ($rules as $field => $fieldRules) {
            foreach ($fieldRules as $rule) {
                // Check if rule has parameters
                $param = null;
                if (strpos($rule, ':') !== false) {
                    list($rule, $param) = explode(':', $rule, 2);
                }
                
                // Skip if field is not required and not present
                if ($rule !== 'required' && !isset($request[$field])) {
                    continue;
                }
                
                // Validate based on rule
                $error = $this->validateField($field, $request[$field] ?? null, $rule, $param, $request);
                if ($error) {
                    $errors[$field][] = $this->formatErrorMessage($field, $rule, $param);
                }
            }
        }
        
        return $errors;
    }
    
    /**
     * Validate a field against a rule
     * 
     * @param string $field The field name
     * @param mixed $value The field value
     * @param string $rule The validation rule
     * @param mixed $param The rule parameter
     * @param array $request The complete request data (for rules that need to check other fields)
     * @return bool True if validation fails
     */
    private function validateField($field, $value, $rule, $param = null, $request = []) {
        switch ($rule) {
            case 'required':
                return empty($value) && $value !== '0';
                
            case 'email':
                return !filter_var($value, FILTER_VALIDATE_EMAIL);
                
            case 'min':
                if (is_string($value)) {
                    return mb_strlen($value) < (int)$param;
                } elseif (is_numeric($value)) {
                    return $value < (int)$param;
                }
                return true;
                
            case 'max':
                if (is_string($value)) {
                    return mb_strlen($value) > (int)$param;
                }
                return true;
                
            case 'numeric':
                return !is_numeric($value);
                
            case 'in':
                $allowed = explode(',', $param);
                return !in_array($value, $allowed);
                
            case 'date_format':
                $date = \DateTime::createFromFormat($param, $value);
                return !$date || $date->format($param) !== $value;
                
            case 'phone':
                // Simple Kenyan phone validation (supports +254... and 07... formats)
                if ($param === 'KE') {
                    $pattern = '/^(?:\+254|0)[17][0-9]{8}$/';
                    return !preg_match($pattern, $value);
                }
                return false;
                
            case 'json':
                if (!is_string($value)) return true;
                json_decode($value);
                return json_last_error() !== JSON_ERROR_NONE;
                
            case 'password_strength':
                // Check for at least one uppercase, one lowercase, and one number
                return !preg_match('/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$/', $value);
                
            case 'required_if':
                list($otherField, $otherValue) = explode(',', $param, 2);
                if (isset($request[$otherField]) && $request[$otherField] === $otherValue) {
                    return empty($value);
                }
                return false;
                
            default:
                return false;
        }
    }
    
    /**
     * Format an error message
     * 
     * @param string $field The field name
     * @param string $rule The validation rule
     * @param mixed $param The rule parameter
     * @return string The formatted error message
     */
    private function formatErrorMessage($field, $rule, $param = null) {
        $message = $this->errorMessages[$rule] ?? 'The :field field is invalid.';
        $message = str_replace(':field', $field, $message);
        
        if ($param !== null) {
            $message = str_replace(':param', $param, $message);
        }
        
        return $message;
    }
    
    /**
     * Sanitize the input data to prevent XSS and injection attacks
     * 
     * @param array $data The input data
     * @return array The sanitized data
     */
    private function sanitizeInput($data) {
        $sanitized = [];
        
        foreach ($data as $key => $value) {
            if (is_array($value)) {
                $sanitized[$key] = $this->sanitizeInput($value);
            } else if (is_string($value)) {
                // Sanitize strings
                $sanitized[$key] = htmlspecialchars($value, ENT_QUOTES, 'UTF-8');
            } else {
                // Keep other data types as is
                $sanitized[$key] = $value;
            }
        }
        
        return $sanitized;
    }
}

// Example usage in a router or middleware handler
/*
$middleware = new ApiValidationMiddleware();
$response = $middleware($request, function($request) {
    // Next middleware or controller
    return handleRequest($request);
});
*/