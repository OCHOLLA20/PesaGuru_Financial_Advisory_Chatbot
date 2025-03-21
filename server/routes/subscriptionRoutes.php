<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

require_once '../controllers/subscriptionController.php';

// Read the incoming request
$requestData = json_decode(file_get_contents("php://input"), true);

if (!isset($requestData['action'])) {
    echo json_encode(["error" => "No action specified"]);
    exit;
}

$subscriptionController = new SubscriptionController();
$action = $requestData['action'];

switch ($action) {
    case 'addSubscription':
        echo $subscriptionController->addSubscription(
            $requestData['userId'], 
            $requestData['plan'], 
            $requestData['amount'], 
            $requestData['duration']
        );
        break;

    case 'getSubscription':
        echo $subscriptionController->getSubscription($requestData['userId']);
        break;

    case 'cancelSubscription':
        echo $subscriptionController->cancelSubscription($requestData['userId']);
        break;

    case 'checkSubscriptionStatus':
        echo $subscriptionController->checkSubscriptionStatus($requestData['userId']);
        break;

    default:
        echo json_encode(["error" => "Invalid action"]);
        break;
}
?>

