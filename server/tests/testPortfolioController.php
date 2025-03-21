<?php

require_once __DIR__ . '/../controllers/portfolioController.php';

$portfolioController = new PortfolioController();

// Test the listPortfolios method
$userId = 1; // Example user ID
$result = $portfolioController->listPortfolios($userId);
echo $result;

?>
