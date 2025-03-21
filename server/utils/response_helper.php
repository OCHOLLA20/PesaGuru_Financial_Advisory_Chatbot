<?php
/**
 * PesaGuru - Response Helper Utility Functions
 * 
 * Functions to format and send API responses
 */

/**
 * Send a success response
 * 
 * @param mixed $data Response data
 * @param string $message Success message
 * @param int $statusCode HTTP status code
 */
function sendSuccessResponse($data = [], $message = 'Success', $statusCode = 200) {
    $response = [
        'status' => 'success',
        'message' => $message,
        'data' => $data
    ];
    
    // Set HTTP response code
    http_response_code($statusCode);
    
    // Output JSON response
    echo json_encode($response);
    exit();
}

/**
 * Send an error response
 * 
 * @param string $message Error message
 * @param int $statusCode HTTP status code
 * @param array $errors Detailed error information
 */
function sendErrorResponse($message = 'Error', $statusCode = 400, $errors = []) {
    $response = [
        'status' => 'error',
        'message' => $message
    ];
    
    // Add detailed errors if provided
    if (!empty($errors)) {
        $response['errors'] = $errors;
    }
    
    // Set HTTP response code
    http_response_code($statusCode);
    
    // Output JSON response
    echo json_encode($response);
    exit();
}

/**
 * Send a validation error response for form validation failures
 * 
 * @param array $validationErrors Array of validation errors
 * @param string $message Error message
 */
function sendValidationErrorResponse($validationErrors, $message = 'Validation failed') {
    sendErrorResponse($message, 422, $validationErrors);
}

/**
 * Log API errors for debugging and monitoring
 * 
 * @param string $message Error message
 * @param mixed $data Additional data for logging
 */
function logApiError($message, $data = null) {
    $logDir = __DIR__ . '/../logs';
    
    // Create logs directory if it doesn't exist
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }
    
    // Format log entry
    $logEntry = date('[Y-m-d H:i:s]') . ' - ' . $message;
    
    // Add data as JSON if provided
    if ($data !== null) {
        $logEntry .= ' - Data: ' . json_encode($data);
    }
    
    // Add request information
    $logEntry .= ' - IP: ' . $_SERVER['REMOTE_ADDR'];
    $logEntry .= ' - URI: ' . $_SERVER['REQUEST_URI'];
    $logEntry .= PHP_EOL;
    
    // Write to log file
    error_log($logEntry, 3, $logDir . '/api_errors.log');
}

/**
 * Format paginated response
 * 
 * @param array $data Data items
 * @param int $page Current page number
 * @param int $perPage Items per page
 * @param int $totalItems Total number of items
 * @param string $message Success message
 * @return array Formatted paginated response
 */
function formatPaginatedResponse($data, $page, $perPage, $totalItems, $message = 'Success') {
    $totalPages = ceil($totalItems / $perPage);
    
    return [
        'data' => $data,
        'pagination' => [
            'total_items' => $totalItems,
            'total_pages' => $totalPages,
            'current_page' => $page,
            'per_page' => $perPage,
            'has_previous' => $page > 1,
            'has_next' => $page < $totalPages
        ],
        'message' => $message
    ];
}