<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

require_once '../controllers/portfolioController.php';

// Read the incoming request
$requestData = json_decode(file_get_contents("php://input"), true);

if (!isset($requestData['action'])) {
    echo json_encode(["error" => "No action specified"]);
    exit;
}

$portfolioController = new PortfolioController();
$action = $requestData['action'];

switch ($action) {
    case 'getPortfolio':
        echo $portfolioController->getPortfolio($requestData['userId']);
        break;

    case 'addInvestment':
        echo $portfolioController->addInvestment(
            $requestData['userId'], 
            $requestData['assetName'], 
            $requestData['amount'], 
            $requestData['category']
        );
        break;

    case 'updateInvestment':
        echo $portfolioController->updateInvestment(
            $requestData['investmentId'], 
            $requestData['amount']
        );
        break;

    case 'deleteInvestment':
        echo $portfolioController->deleteInvestment($requestData['investmentId']);
        break;

    default:
        echo json_encode(["error" => "Invalid action"]);
        break;
}
?>

