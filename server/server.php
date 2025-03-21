<?php

// Enable error reporting during development
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Set headers for CORS and JSON responses
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json; charset=UTF-8");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With");

// Handle preflight OPTIONS requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header("HTTP/1.1 200 OK");
    exit();
}

// Load environment variables
require_once __DIR__ . '/config/env_loader.php';

// Load database configuration
require_once __DIR__ . '/config/db.php';

// Load authentication services
require_once __DIR__ . '/services/auth/tokenService.php';

// Load utility functions
require_once __DIR__ . '/utils/response_helper.php';
require_once __DIR__ . '/utils/request_parser.php';

// Load controllers
require_once __DIR__ . '/controllers/authController.php';
require_once __DIR__ . '/controllers/chatbotController.php';
require_once __DIR__ . '/controllers/portfolioController.php';
require_once __DIR__ . '/controllers/riskProfileController.php';
require_once __DIR__ . '/controllers/marketDataController.php';
require_once __DIR__ . '/controllers/userController.php';
require_once __DIR__ . '/controllers/financialGoalController.php';
require_once __DIR__ . '/controllers/userController.php';

require_once __DIR__ . '/controllers/feedbackController.php';

// Parse request URI and HTTP method
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$uri = explode('/', $uri);

// Remove the first segments that might include the project directory
// For example: /PesaGuru/server/api/v1/auth/login -> ['api', 'v1', 'auth', 'login']
$apiIndex = array_search('api', $uri);
if ($apiIndex !== false) {
    $uri = array_slice($uri, $apiIndex);
}

// Expecting URI pattern: /api/v1/resource/action
if (!isset($uri[0]) || $uri[0] != 'api') {
    sendErrorResponse('Invalid API endpoint', 404);
    exit();
}

// Check API version
if (!isset($uri[1]) || $uri[1] != 'v1') {
    sendErrorResponse('Invalid API version', 404);
    exit();
}

// Get the resource and action from URI
$resource = isset($uri[2]) ? $uri[2] : null;
$action = isset($uri[3]) ? $uri[3] : null;
$id = isset($uri[4]) ? $uri[4] : null;

// Parse request data
$requestData = parseRequestData();

// API routing logic
try {
    // Route to the appropriate controller based on the resource
    switch ($resource) {
        case 'auth':
            $authController = new AuthController($db);
            
            switch ($action) {
                case 'login':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $authController->login($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'register':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $authController->register($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'refresh':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $authController->refreshToken($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'logout':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $authController->logout($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid auth endpoint', 404);
                    break;
            }
            break;
            
        case 'chatbot':
            // Authenticate user for protected routes
            $token = getBearerToken();
            if (!validateToken($token)) {
                sendErrorResponse('Unauthorized access', 401);
                break;
            }
            
            $chatbotController = new ChatbotController($db);
            
            switch ($action) {
                case 'message':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $chatbotController->processMessage($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'history':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $chatbotController->getConversationHistory($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'feedback':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $chatbotController->submitFeedback($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid chatbot endpoint', 404);
                    break;
            }
            break;
            
        case 'portfolio':
            // Authenticate user for protected routes
            $token = getBearerToken();
            if (!validateToken($token)) {
                sendErrorResponse('Unauthorized access', 401);
                break;
            }
            
            $portfolioController = new PortfolioController($db);
            
            switch ($action) {
                case 'summary':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $portfolioController->getPortfolioSummary($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'recommendations':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $portfolioController->getRecommendations($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'update':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $portfolioController->updatePortfolio($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid portfolio endpoint', 404);
                    break;
            }
            break;
            
        case 'risk':
            // Authenticate user for protected routes
            $token = getBearerToken();
            if (!validateToken($token)) {
                sendErrorResponse('Unauthorized access', 401);
                break;
            }
            
            $riskProfileController = new RiskProfileController($db);
            
            switch ($action) {
                case 'assessment':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $riskProfileController->submitAssessment($requestData);
                    } else if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $riskProfileController->getAssessmentQuestions();
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'profile':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $riskProfileController->getUserRiskProfile($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid risk assessment endpoint', 404);
                    break;
            }
            break;
            
        case 'market':
            $marketDataController = new MarketDataController($db);
            
            switch ($action) {
                case 'stocks':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $marketDataController->getStockData($id);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'sectors':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $marketDataController->getSectorData();
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'forex':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $marketDataController->getForexRates();
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'crypto':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $marketDataController->getCryptoData();
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid market data endpoint', 404);
                    break;
            }
            break;
            
case 'user':
    // Authenticate user for protected routes
    $token = getBearerToken();
    if (!validateToken($token)) {
        sendErrorResponse('Unauthorized access', 401);
        break;
    }
    
    $userController = new UserController($db);
    
    switch ($action) {
        case 'profile':
            if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                $userController->getUserProfile($requestData);
            } else if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
                $userController->updateUserProfile($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;
            
        case 'preferences':
            if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                $userController->getUserPreferences($requestData);
            } else if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
                $userController->updateUserPreferences($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'register':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->register($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'login':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->login($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'logout':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->logout($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'reset-password':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->resetPassword($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'enable-2fa':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->enableTwoFactorAuth($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        case 'deactivate':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                $userController->deactivateAccount($requestData);
            } else {
                sendErrorResponse('Method not allowed', 405);
            }
            break;

        default:
            sendErrorResponse('Invalid user endpoint', 404);
            break;
    }

            break;
            
        case 'goals':
            // Authenticate user for protected routes
            $token = getBearerToken();
            if (!validateToken($token)) {
                sendErrorResponse('Unauthorized access', 401);
                break;
            }
            
            $financialGoalController = new FinancialGoalController($db);
            
            switch ($action) {
                case 'list':
                    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
                        $financialGoalController->getUserGoals($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'create':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $financialGoalController->createGoal($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'update':
                    if ($_SERVER['REQUEST_METHOD'] === 'PUT') {
                        $financialGoalController->updateGoal($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                case 'delete':
                    if ($_SERVER['REQUEST_METHOD'] === 'DELETE') {
                        $financialGoalController->deleteGoal($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid financial goals endpoint', 404);
                    break;
            }
            break;
            
        case 'feedback':
            // Authenticate user for protected routes
            $token = getBearerToken();
            if (!validateToken($token)) {
                sendErrorResponse('Unauthorized access', 401);
                break;
            }
            
            $feedbackController = new FeedbackController($db);
            
            switch ($action) {
                case 'submit':
                    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                        $feedbackController->submitFeedback($requestData);
                    } else {
                        sendErrorResponse('Method not allowed', 405);
                    }
                    break;
                    
                default:
                    sendErrorResponse('Invalid feedback endpoint', 404);
                    break;
            }
            break;
            
        default:
            sendErrorResponse('Invalid API resource', 404);
            break;
    }
} catch (Exception $e) {
    sendErrorResponse('Server error: ' . $e->getMessage(), 500);
}

/**
 * Get the bearer token from the Authorization header
 * 
 * @return string|null The bearer token or null if not found
 */
function getBearerToken() {
    $headers = getallheaders();
    if (isset($headers['Authorization'])) {
        if (preg_match('/Bearer\s(\S+)/', $headers['Authorization'], $matches)) {
            return $matches[1];
        }
    }
    return null;
}
