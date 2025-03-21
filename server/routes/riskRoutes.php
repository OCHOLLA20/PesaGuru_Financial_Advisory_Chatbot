<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

require_once '../controllers/riskProfileController.php';

// Read the incoming request
$requestData = json_decode(file_get_contents("php://input"), true);

if (!isset($requestData['action'])) {
    echo json_encode(["error" => "No action specified"]);
    exit;
}

$riskProfileController = new RiskProfileController();
$action = $requestData['action'];

switch ($action) {
    case 'calculateRisk':
        echo $riskProfileController->processRiskProfile(
            $requestData['userId'], 
            $requestData['age'], 
            $requestData['income'], 
            $requestData['investmentExperience'], 
            $requestData['riskPreference']
        );
        break;

    case 'getRiskProfile':
        echo $riskProfileController->getRiskProfile($requestData['userId']);
        break;

    default:
        echo json_encode(["error" => "Invalid action"]);
        break;
}
?>
