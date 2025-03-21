<?php
/**
 * PesaGuru - Request Parser Utility Functions
 * 
 * Functions to parse and validate incoming API requests
 */

/**
 * Parse request data from different HTTP methods
 * 
 * @return array Request data
 */
function parseRequestData() {
    $contentType = isset($_SERVER["CONTENT_TYPE"]) ? trim($_SERVER["CONTENT_TYPE"]) : '';
    $requestMethod = $_SERVER['REQUEST_METHOD'];
    $data = [];
    
    // Handle different request methods
    switch ($requestMethod) {
        case 'GET':
            $data = $_GET;
            break;
            
        case 'POST':
            // Parse JSON input
            if (stripos($contentType, 'application/json') !== false) {
                $input = file_get_contents('php://input');
                $data = json_decode($input, true);
                
                // Check for JSON parsing errors
                if (json_last_error() !== JSON_ERROR_NONE) {
                    sendErrorResponse('Invalid JSON format', 400);
                    exit();
                }
            } else {
                // Regular form data
                $data = $_POST;
            }
            break;
            
        case 'PUT':
        case 'DELETE':
            // Parse JSON input for PUT and DELETE
            $input = file_get_contents('php://input');
            $data = json_decode($input, true);
            
            // Check for JSON parsing errors
            if (json_last_error() !== JSON_ERROR_NONE) {
                sendErrorResponse('Invalid JSON format', 400);
                exit();
            }
            break;
    }
    
    return $data;
}

/**
 * Validate required fields in request data
 * 
 * @param array $data The request data to validate
 * @param array $requiredFields Array of required field names
 * @return bool True if all required fields are present and not empty
 */
function validateRequiredFields($data, $requiredFields) {
    foreach ($requiredFields as $field) {
        if (!isset($data[$field]) || empty($data[$field])) {
            sendErrorResponse("Missing required field: {$field}", 400);
            return false;
        }
    }
    return true;
}

/**
 * Sanitize input data to prevent SQL injection and XSS attacks
 * 
 * @param mixed $data The data to sanitize
 * @return mixed Sanitized data
 */
function sanitizeInput($data) {
    if (is_array($data)) {
        foreach ($data as $key => $value) {
            $data[$key] = sanitizeInput($value);
        }
    } else {
        // Remove whitespace
        $data = trim($data);
        
        // Remove backslashes
        $data = stripslashes($data);
        
        // Convert special characters to HTML entities
        $data = htmlspecialchars($data, ENT_QUOTES, 'UTF-8');
    }
    
    return $data;
}

/**
 * Validate email format
 * 
 * @param string $email Email to validate
 * @return bool True if email is valid
 */
function validateEmail($email) {
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}

/**
 * Validate password strength
 * 
 * @param string $password Password to validate
 * @return bool True if password meets required strength
 */
function validatePasswordStrength($password) {
    // Password must be at least 8 characters long and include at least one
    // uppercase letter, one lowercase letter, one number, and one special character
    $uppercase = preg_match('@[A-Z]@', $password);
    $lowercase = preg_match('@[a-z]@', $password);
    $number = preg_match('@[0-9]@', $password);
    $specialChar = preg_match('@[^\w]@', $password);
    
    return strlen($password) >= 8 && $uppercase && $lowercase && $number && $specialChar;
}