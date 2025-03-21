<?php
class PortfolioService {
    private $db;
    private $riskProfileModel;
    private $nseApiService;
    private $userProfiler;
    
    /**
     * Constructor initializes service dependencies
     */
    public function __construct() {
        // Get database connection
        require_once __DIR__ . '/../config/db.php';
        $this->db = getDbConnection();
        
        // Load dependent services and models
        require_once __DIR__ . '/../models/RiskProfile.php';
        require_once __DIR__ . '/integrations/nseApiService.php';
        require_once __DIR__ . '/user_profiler.php';
        
        $this->riskProfileModel = new RiskProfile();
        $this->nseApiService = new NSEApiService();
        $this->userProfiler = new UserProfiler();
    }
    
    /**
     * Create a new portfolio for a user
     * 
     * @param int $userId User ID
     * @param string $portfolioName Portfolio name
     * @param string $description Portfolio description
     * @param string $currency Portfolio currency (default: KES)
     * @param string $investmentGoal Investment goal 
     * @param string $riskProfileId Risk profile ID
     * @return array Portfolio creation result
     */
    public function createPortfolio($userId, $portfolioName, $description = '', $currency = 'KES', $investmentGoal = '', $riskProfileId = null) {
        try {
            // Validate input parameters
            if (empty($userId) || empty($portfolioName)) {
                return [
                    'success' => false,
                    'message' => 'User ID and portfolio name are required'
                ];
            }
            
            // Check if user exists
            $stmt = $this->db->prepare("SELECT id FROM users WHERE id = ?");
            $stmt->bind_param("i", $userId);
            $stmt->execute();
            $userResult = $stmt->get_result();
            
            if ($userResult->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'User not found'
                ];
            }
            
            // Check if portfolio with same name already exists for this user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE user_id = ? AND name = ?");
            $stmt->bind_param("is", $userId, $portfolioName);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                return [
                    'success' => false,
                    'message' => 'A portfolio with this name already exists'
                ];
            }
            
            // If no risk profile provided, use default based on user profile
            if (empty($riskProfileId)) {
                $riskProfileId = $this->userProfiler->getDefaultRiskProfile($userId);
            }
            
            // Create new portfolio
            $createdAt = date('Y-m-d H:i:s');
            $stmt = $this->db->prepare("
                INSERT INTO portfolios (user_id, name, description, currency, investment_goal, risk_profile_id, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->bind_param("isssssss", $userId, $portfolioName, $description, $currency, $investmentGoal, $riskProfileId, $createdAt, $createdAt);
            
            if ($stmt->execute()) {
                $portfolioId = $stmt->insert_id;
                
                // Log portfolio creation
                $this->logPortfolioActivity($portfolioId, 'create', 'Portfolio created');
                
                return [
                    'success' => true,
                    'message' => 'Portfolio created successfully',
                    'portfolio_id' => $portfolioId
                ];
            } else {
                return [
                    'success' => false,
                    'message' => 'Failed to create portfolio: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get a user's portfolio by ID
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @param bool $withHoldings Include stock holdings in response
     * @return array Portfolio data
     */
    public function getPortfolio($userId, $portfolioId, $withHoldings = true) {
        try {
            // Get portfolio details
            $stmt = $this->db->prepare("
                SELECT p.*, rp.name as risk_profile_name, rp.description as risk_profile_description 
                FROM portfolios p
                LEFT JOIN risk_profiles rp ON p.risk_profile_id = rp.id
                WHERE p.id = ? AND p.user_id = ?
            ");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            $portfolio = $result->fetch_assoc();
            
            // Include portfolio holdings if requested
            if ($withHoldings) {
                $portfolio['holdings'] = $this->getPortfolioHoldings($portfolioId);
                $portfolio['performance'] = $this->calculatePortfolioPerformance($portfolioId);
                $portfolio['diversification'] = $this->analyzePortfolioDiversification($portfolioId);
            }
            
            return [
                'success' => true,
                'portfolio' => $portfolio
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get all portfolios for a user
     * 
     * @param int $userId User ID
     * @param bool $withSummary Include performance summary
     * @return array User portfolios
     */
    public function getUserPortfolios($userId, $withSummary = true) {
        try {
            // Get all portfolios for user
            $stmt = $this->db->prepare("
                SELECT p.*, rp.name as risk_profile_name 
                FROM portfolios p
                LEFT JOIN risk_profiles rp ON p.risk_profile_id = rp.id
                WHERE p.user_id = ?
                ORDER BY p.created_at DESC
            ");
            $stmt->bind_param("i", $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $portfolios = [];
            
            while ($row = $result->fetch_assoc()) {
                $portfolio = $row;
                
                if ($withSummary) {
                    // Get summary data
                    $portfolio['total_value'] = $this->getPortfolioValue($row['id']);
                    $portfolio['total_gain_loss'] = $this->getPortfolioGainLoss($row['id']);
                    $portfolio['stock_count'] = $this->getPortfolioStockCount($row['id']);
                }
                
                $portfolios[] = $portfolio;
            }
            
            return [
                'success' => true,
                'portfolios' => $portfolios,
                'count' => count($portfolios)
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Update portfolio details
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @param array $data Update data
     * @return array Update result
     */
    public function updatePortfolio($userId, $portfolioId, $data) {
        try {
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            // Build update query based on provided data
            $updates = [];
            $types = '';
            $values = [];
            
            $allowedFields = [
                'name' => 's', 
                'description' => 's', 
                'currency' => 's', 
                'investment_goal' => 's',
                'risk_profile_id' => 's'
            ];
            
            foreach ($allowedFields as $field => $type) {
                if (isset($data[$field])) {
                    $updates[] = "$field = ?";
                    $types .= $type;
                    $values[] = $data[$field];
                }
            }
            
            if (empty($updates)) {
                return [
                    'success' => false,
                    'message' => 'No valid fields to update'
                ];
            }
            
            // Add updated_at timestamp
            $updates[] = "updated_at = ?";
            $types .= "s";
            $values[] = date('Y-m-d H:i:s');
            
            // Add portfolio ID and user ID to values array
            $types .= "ii";
            $values[] = $portfolioId;
            $values[] = $userId;
            
            // Prepare and execute update query
            $query = "UPDATE portfolios SET " . implode(", ", $updates) . " WHERE id = ? AND user_id = ?";
            $stmt = $this->db->prepare($query);
            
            // Create parameter array for bind_param
            $bindParams = array_merge([$types], $values);
            $bindParamsRef = [];
            
            foreach ($bindParams as $key => $value) {
                $bindParamsRef[$key] = &$bindParams[$key];
            }
            
            call_user_func_array([$stmt, 'bind_param'], $bindParamsRef);
            
            if ($stmt->execute()) {
                // Log portfolio update
                $this->logPortfolioActivity($portfolioId, 'update', 'Portfolio details updated');
                
                return [
                    'success' => true,
                    'message' => 'Portfolio updated successfully'
                ];
            } else {
                return [
                    'success' => false,
                    'message' => 'Failed to update portfolio: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Delete a portfolio
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @return array Delete result
     */
    public function deletePortfolio($userId, $portfolioId) {
        try {
            // Start transaction
            $this->db->begin_transaction();
            
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                $this->db->rollback();
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            // Delete portfolio holdings first
            $stmt = $this->db->prepare("DELETE FROM portfolio_holdings WHERE portfolio_id = ?");
            $stmt->bind_param("i", $portfolioId);
            $stmt->execute();
            
            // Delete portfolio transactions
            $stmt = $this->db->prepare("DELETE FROM portfolio_transactions WHERE portfolio_id = ?");
            $stmt->bind_param("i", $portfolioId);
            $stmt->execute();
            
            // Delete portfolio
            $stmt = $this->db->prepare("DELETE FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            
            if ($stmt->execute()) {
                // Commit transaction
                $this->db->commit();
                
                return [
                    'success' => true,
                    'message' => 'Portfolio deleted successfully'
                ];
            } else {
                $this->db->rollback();
                return [
                    'success' => false,
                    'message' => 'Failed to delete portfolio: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            // Rollback transaction in case of error
            $this->db->rollback();
            
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Add a stock to a portfolio
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @param string $stockCode Stock code (e.g., SCOM for Safaricom)
     * @param float $quantity Number of shares
     * @param float $purchasePrice Purchase price per share
     * @param string $purchaseDate Purchase date (YYYY-MM-DD)
     * @param string $notes Transaction notes
     * @return array Operation result
     */
    public function addStock($userId, $portfolioId, $stockCode, $quantity, $purchasePrice, $purchaseDate = null, $notes = '') {
        try {
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            // Validate and format the purchase date
            if (empty($purchaseDate)) {
                $purchaseDate = date('Y-m-d');
            } else {
                $purchaseTimestamp = strtotime($purchaseDate);
                if ($purchaseTimestamp === false) {
                    return [
                        'success' => false,
                        'message' => 'Invalid purchase date format. Use YYYY-MM-DD.'
                    ];
                }
                $purchaseDate = date('Y-m-d', $purchaseTimestamp);
            }
            
            // Verify stock exists in NSE
            $stockInfo = $this->nseApiService->getStockInfo($stockCode);
            if (!$stockInfo || $stockInfo['success'] === false) {
                return [
                    'success' => false,
                    'message' => 'Invalid stock code or stock information not available'
                ];
            }
            
            // Calculate total cost
            $totalCost = $quantity * $purchasePrice;
            
            // Start transaction
            $this->db->begin_transaction();
            
            // Check if stock already exists in portfolio
            $stmt = $this->db->prepare("
                SELECT id, quantity, average_price 
                FROM portfolio_holdings 
                WHERE portfolio_id = ? AND stock_code = ?
            ");
            $stmt->bind_param("is", $portfolioId, $stockCode);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $transactionType = 'buy';
            
            if ($result->num_rows > 0) {
                // Update existing holding
                $holding = $result->fetch_assoc();
                $holdingId = $holding['id'];
                $existingQuantity = $holding['quantity'];
                $existingAvgPrice = $holding['average_price'];
                
                // Calculate new average price
                $newTotalQuantity = $existingQuantity + $quantity;
                $newAveragePrice = (($existingQuantity * $existingAvgPrice) + ($quantity * $purchasePrice)) / $newTotalQuantity;
                
                // Update holding
                $stmt = $this->db->prepare("
                    UPDATE portfolio_holdings 
                    SET quantity = ?, average_price = ?, updated_at = ? 
                    WHERE id = ?
                ");
                $updatedAt = date('Y-m-d H:i:s');
                $stmt->bind_param("ddsi", $newTotalQuantity, $newAveragePrice, $updatedAt, $holdingId);
                $stmt->execute();
            } else {
                // Create new holding
                $stmt = $this->db->prepare("
                    INSERT INTO portfolio_holdings 
                    (portfolio_id, stock_code, stock_name, quantity, average_price, sector, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ");
                $timestamp = date('Y-m-d H:i:s');
                $stockName = $stockInfo['name'] ?? $stockCode;
                $sector = $stockInfo['sector'] ?? 'Unknown';
                
                $stmt->bind_param("issddsss", 
                    $portfolioId, 
                    $stockCode, 
                    $stockName, 
                    $quantity, 
                    $purchasePrice, 
                    $sector,
                    $timestamp, 
                    $timestamp
                );
                $stmt->execute();
                $holdingId = $stmt->insert_id;
            }
            
            // Record transaction
            $stmt = $this->db->prepare("
                INSERT INTO portfolio_transactions 
                (portfolio_id, stock_code, transaction_type, quantity, price, total_amount, transaction_date, notes, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ");
            $createdAt = date('Y-m-d H:i:s');
            
            $stmt->bind_param("issdddss", 
                $portfolioId, 
                $stockCode, 
                $transactionType, 
                $quantity, 
                $purchasePrice, 
                $totalCost, 
                $purchaseDate, 
                $notes, 
                $createdAt
            );
            
            if ($stmt->execute()) {
                // Commit transaction
                $this->db->commit();
                
                // Log portfolio activity
                $this->logPortfolioActivity(
                    $portfolioId, 
                    'add_stock', 
                    "Added $quantity shares of $stockCode at KES $purchasePrice per share"
                );
                
                return [
                    'success' => true,
                    'message' => "Successfully added $quantity shares of $stockCode to portfolio",
                    'holding_id' => $holdingId
                ];
            } else {
                $this->db->rollback();
                return [
                    'success' => false,
                    'message' => 'Failed to record transaction: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            // Rollback transaction in case of error
            if ($this->db->errno) { 
                $this->db->rollback(); 
            }

            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Sell stocks from a portfolio
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @param string $stockCode Stock code
     * @param float $quantity Number of shares to sell
     * @param float $sellPrice Selling price per share
     * @param string $sellDate Sell date (YYYY-MM-DD)
     * @param string $notes Transaction notes
     * @return array Operation result
     */
    public function sellStock($userId, $portfolioId, $stockCode, $quantity, $sellPrice, $sellDate = null, $notes = '') {
        try {
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            // Validate and format the sell date
            if (empty($sellDate)) {
                $sellDate = date('Y-m-d');
            } else {
                $sellTimestamp = strtotime($sellDate);
                if ($sellTimestamp === false) {
                    return [
                        'success' => false,
                        'message' => 'Invalid sell date format. Use YYYY-MM-DD.'
                    ];
                }
                $sellDate = date('Y-m-d', $sellTimestamp);
            }
            
            // Check if stock exists in portfolio
            $stmt = $this->db->prepare("
                SELECT id, quantity, average_price 
                FROM portfolio_holdings 
                WHERE portfolio_id = ? AND stock_code = ?
            ");
            $stmt->bind_param("is", $portfolioId, $stockCode);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => "Stock $stockCode not found in portfolio"
                ];
            }
            
            $holding = $result->fetch_assoc();
            $holdingId = $holding['id'];
            $existingQuantity = $holding['quantity'];
            $averagePrice = $holding['average_price'];
            
            // Verify enough shares to sell
            if ($existingQuantity < $quantity) {
                return [
                    'success' => false,
                    'message' => "Not enough shares to sell. You have $existingQuantity shares, but trying to sell $quantity."
                ];
            }
            
            // Calculate total sale amount and profit/loss
            $totalSaleAmount = $quantity * $sellPrice;
            $totalCost = $quantity * $averagePrice;
            $profitLoss = $totalSaleAmount - $totalCost;
            $profitLossPercentage = ($profitLoss / $totalCost) * 100;
            
            // Start transaction
            $this->db->begin_transaction();
            
            // Update holding quantity or remove if selling all
            $newQuantity = $existingQuantity - $quantity;
            
            if ($newQuantity > 0) {
                // Update quantity
                $stmt = $this->db->prepare("
                    UPDATE portfolio_holdings 
                    SET quantity = ?, updated_at = ? 
                    WHERE id = ?
                ");
                $updatedAt = date('Y-m-d H:i:s');
                $stmt->bind_param("dsi", $newQuantity, $updatedAt, $holdingId);
                $stmt->execute();
            } else {
                // Remove holding if selling all shares
                $stmt = $this->db->prepare("DELETE FROM portfolio_holdings WHERE id = ?");
                $stmt->bind_param("i", $holdingId);
                $stmt->execute();
            }
            
            // Record transaction
            $stmt = $this->db->prepare("
                INSERT INTO portfolio_transactions 
                (portfolio_id, stock_code, transaction_type, quantity, price, total_amount, profit_loss, profit_loss_percentage, transaction_date, notes, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ");
            $transactionType = 'sell';
            $createdAt = date('Y-m-d H:i:s');
            
            $stmt->bind_param("issdddddss", 
                $portfolioId, 
                $stockCode, 
                $transactionType, 
                $quantity, 
                $sellPrice, 
                $totalSaleAmount, 
                $profitLoss,
                $profitLossPercentage,
                $sellDate, 
                $notes, 
                $createdAt
            );
            
            if ($stmt->execute()) {
                // Commit transaction
                $this->db->commit();
                
                // Log portfolio activity
                $this->logPortfolioActivity(
                    $portfolioId, 
                    'sell_stock', 
                    "Sold $quantity shares of $stockCode at KES $sellPrice per share. Profit/Loss: KES " . number_format($profitLoss, 2)
                );
                
                return [
                    'success' => true,
                    'message' => "Successfully sold $quantity shares of $stockCode",
                    'profit_loss' => $profitLoss,
                    'profit_loss_percentage' => $profitLossPercentage
                ];
            } else {
                $this->db->rollback();
                return [
                    'success' => false,
                    'message' => 'Failed to record transaction: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            // Rollback transaction in case of error
            if ($this->db->errno) { 
                $this->db->rollback(); 
            }            
            return [
                'success' => false,
                'message' => 'An error occurred: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get all holdings in a portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @param bool $withCurrentPrices Include current market prices
     * @return array Portfolio holdings
     */
    public function getPortfolioHoldings($portfolioId, $withCurrentPrices = true) {
        try {
            // Get all holdings in portfolio
            $stmt = $this->db->prepare("
                SELECT * FROM portfolio_holdings
                WHERE portfolio_id = ?
                ORDER BY created_at DESC
            ");
            $stmt->bind_param("i", $portfolioId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $holdings = [];
            $stockCodes = [];
            
            while ($row = $result->fetch_assoc()) {
                $holdings[] = $row;
                $stockCodes[] = $row['stock_code'];
            }
            
            // Get current prices if requested
            if ($withCurrentPrices && !empty($stockCodes)) {
                $currentPrices = $this->nseApiService->getStockPrices($stockCodes);
                
                // Add current prices and calculate gains/losses
                foreach ($holdings as &$holding) {
                    $stockCode = $holding['stock_code'];
                    
                    if (isset($currentPrices[$stockCode])) {
                        $currentPrice = $currentPrices[$stockCode]['price'];
                        $holding['current_price'] = $currentPrice;
                        $holding['current_value'] = $currentPrice * $holding['quantity'];
                        $holding['gain_loss'] = ($currentPrice - $holding['average_price']) * $holding['quantity'];
                        $holding['gain_loss_percentage'] = (($currentPrice - $holding['average_price']) / $holding['average_price']) * 100;
                    } else {
                        // If current price not available, use average price
                        $holding['current_price'] = $holding['average_price'];
                        $holding['current_value'] = $holding['average_price'] * $holding['quantity'];
                        $holding['gain_loss'] = 0;
                        $holding['gain_loss_percentage'] = 0;
                    }
                }
            }
            
            return $holdings;
        } catch (Exception $e) {
            error_log("Error getting portfolio holdings: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get portfolio transactions
     * 
     * @param int $portfolioId Portfolio ID
     * @param string $stockCode Optional stock code to filter by
     * @param string $transactionType Optional transaction type (buy, sell, dividend)
     * @param string $startDate Optional start date (YYYY-MM-DD)
     * @param string $endDate Optional end date (YYYY-MM-DD)
     * @return array Portfolio transactions
     */
    public function getPortfolioTransactions($portfolioId, $stockCode = null, $transactionType = null, $startDate = null, $endDate = null) {
        try {
            // Build query with various filters
            $query = "SELECT * FROM portfolio_transactions WHERE portfolio_id = ?";
            $params = [$portfolioId];
            $types = "i";
            
            if (!empty($stockCode)) {
                $query .= " AND stock_code = ?";
                $params[] = $stockCode;
                $types .= "s";
            }
            
            if (!empty($transactionType)) {
                $query .= " AND transaction_type = ?";
                $params[] = $transactionType;
                $types .= "s";
            }
            
            if (!empty($startDate)) {
                $query .= " AND transaction_date >= ?";
                $params[] = $startDate;
                $types .= "s";
            }
            
            if (!empty($endDate)) {
                $query .= " AND transaction_date <= ?";
                $params[] = $endDate;
                $types .= "s";
            }
            
            $query .= " ORDER BY transaction_date DESC";
            
            // Prepare and execute query
            $stmt = $this->db->prepare($query);
            
            if ($stmt) {
                // Dynamic binding of parameters
                if (!empty($params)) {
                    $bindParams = array($types);
                    foreach ($params as $param) {
                        $bindParams[] = $param;
                    }
                    
                    // Create references for bind_param
                    $tmp = [];
                    foreach ($bindParams as $key => $value) {
                        $tmp[$key] = &$bindParams[$key];
                    }
                    
                    call_user_func_array(array($stmt, 'bind_param'), $tmp);
                }
                
                $stmt->execute();
                $result = $stmt->get_result();
                
                $transactions = [];
                while ($row = $result->fetch_assoc()) {
                    $transactions[] = $row;
                }
                
                return $transactions;
            } else {
                error_log("Error preparing statement: " . $this->db->error);
                return [];
            }
        } catch (Exception $e) {
            error_log("Error getting portfolio transactions: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Calculate portfolio performance
     * 
     * @param int $portfolioId Portfolio ID
     * @param string $period Period for analysis (1d, 1w, 1m, 3m, 6m, 1y, all)
     * @return array Performance metrics
     */
    public function calculatePortfolioPerformance($portfolioId, $period = 'all') {
        try {
            // Get holdings with current prices
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            // Initialize performance metrics
            $performance = [
                'total_value' => 0,
                'total_cost' => 0,
                'total_gain_loss' => 0,
                'total_gain_loss_percentage' => 0,
                'best_performing_stock' => null,
                'worst_performing_stock' => null
            ];
            
            if (empty($holdings)) {
                return $performance;
            }
            
            // Calculate performance metrics
            $bestPerformancePercent = -999;
            $worstPerformancePercent = 999;
            
            foreach ($holdings as $holding) {
                // Add to totals
                $performance['total_value'] += $holding['current_value'] ?? 0;
                $totalCost = $holding['average_price'] * $holding['quantity'];
                $performance['total_cost'] += $totalCost;
                $performance['total_gain_loss'] += $holding['gain_loss'] ?? 0;
                
                // Check for best/worst performing stocks
                $gainLossPercent = $holding['gain_loss_percentage'] ?? 0;
                
                if ($gainLossPercent > $bestPerformancePercent) {
                    $bestPerformancePercent = $gainLossPercent;
                    $performance['best_performing_stock'] = [
                        'stock_code' => $holding['stock_code'],
                        'stock_name' => $holding['stock_name'],
                        'gain_loss_percentage' => $gainLossPercent
                    ];
                }
                
                if ($gainLossPercent < $worstPerformancePercent) {
                    $worstPerformancePercent = $gainLossPercent;
                    $performance['worst_performing_stock'] = [
                        'stock_code' => $holding['stock_code'],
                        'stock_name' => $holding['stock_name'],
                        'gain_loss_percentage' => $gainLossPercent
                    ];
                }
            }
            
            // Calculate total gain/loss percentage
            if ($performance['total_cost'] > 0) {
                $performance['total_gain_loss_percentage'] = ($performance['total_gain_loss'] / $performance['total_cost']) * 100;
            }
            
            // Get historical performance based on period
            $performance['historical'] = $this->getHistoricalPerformance($portfolioId, $period);
            
            return $performance;
        } catch (Exception $e) {
            error_log("Error calculating portfolio performance: " . $e->getMessage());
            return [
                'total_value' => 0,
                'total_cost' => 0,
                'total_gain_loss' => 0,
                'total_gain_loss_percentage' => 0,
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Analyze portfolio diversification
     * 
     * @param int $portfolioId Portfolio ID
     * @return array Diversification analysis
     */
    public function analyzePortfolioDiversification($portfolioId) {
        try {
            // Get holdings with current prices
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            if (empty($holdings)) {
                return [
                    'sector_allocation' => [],
                    'stock_allocation' => [],
                    'diversification_score' => 0,
                    'recommendation' => 'Your portfolio is empty. Consider adding stocks from different sectors.'
                ];
            }
            
            // Calculate sector and stock allocations
            $sectorAllocation = [];
            $stockAllocation = [];
            $totalValue = 0;
            
            foreach ($holdings as $holding) {
                $currentValue = $holding['current_value'] ?? 0;
                $totalValue += $currentValue;
                
                // Add to sector allocation
                $sector = $holding['sector'] ?? 'Unknown';
                if (!isset($sectorAllocation[$sector])) {
                    $sectorAllocation[$sector] = 0;
                }
                $sectorAllocation[$sector] += $currentValue;
                
                // Add to stock allocation
                $stockAllocation[$holding['stock_code']] = [
                    'stock_code' => $holding['stock_code'],
                    'stock_name' => $holding['stock_name'],
                    'value' => $currentValue,
                    'percentage' => 0 // To be calculated after total is known
                ];
            }
            
            // Calculate percentages
            if ($totalValue > 0) {
                foreach ($sectorAllocation as $sector => $value) {
                    $sectorAllocation[$sector] = [
                        'sector' => $sector,
                        'value' => $value,
                        'percentage' => ($value / $totalValue) * 100
                    ];
                }
                
                foreach ($stockAllocation as $code => $data) {
                    $stockAllocation[$code]['percentage'] = ($data['value'] / $totalValue) * 100;
                }
            }
            
            // Convert to arrays for easier JSON encoding
            $sectorAllocationArray = array_values($sectorAllocation);
            $stockAllocationArray = array_values($stockAllocation);
            
            // Calculate diversification score
            $diversificationScore = $this->calculateDiversificationScore($sectorAllocationArray, $stockAllocationArray);
            
            // Generate recommendation
            $recommendation = $this->generateDiversificationRecommendation($diversificationScore, $sectorAllocationArray, $stockAllocationArray);
            
            return [
                'sector_allocation' => $sectorAllocationArray,
                'stock_allocation' => $stockAllocationArray,
                'diversification_score' => $diversificationScore,
                'recommendation' => $recommendation
            ];
        } catch (Exception $e) {
            error_log("Error analyzing portfolio diversification: " . $e->getMessage());
            return [
                'sector_allocation' => [],
                'stock_allocation' => [],
                'diversification_score' => 0,
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Generate portfolio recommendations based on risk profile and goals
     * 
     * @param int $portfolioId Portfolio ID
     * @return array Recommendations
     */
    public function generatePortfolioRecommendations($portfolioId) {
        try {
            // Get portfolio details with risk profile
            $stmt = $this->db->prepare("
                SELECT p.*, rp.name as risk_profile_name, rp.risk_level
                FROM portfolios p
                LEFT JOIN risk_profiles rp ON p.risk_profile_id = rp.id
                WHERE p.id = ?
            ");
            $stmt->bind_param("i", $portfolioId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found'
                ];
            }
            
            $portfolio = $result->fetch_assoc();
            $riskLevel = $portfolio['risk_level'] ?? 'moderate';
            
            // Get current holdings
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            // Get diversification analysis
            $diversification = $this->analyzePortfolioDiversification($portfolioId);
            
            // Get portfolio performance
            $performance = $this->calculatePortfolioPerformance($portfolioId);
            
            // Generate recommendations based on analysis
            $recommendations = [];
            
            // 1. Diversification recommendations
            if ($diversification['diversification_score'] < 50) {
                $recommendations[] = [
                    'type' => 'diversification',
                    'priority' => 'high',
                    'recommendation' => 'Improve portfolio diversification by investing in a broader range of sectors.',
                    'details' => $diversification['recommendation']
                ];
            }
            
            // 2. Risk-based recommendations
            $overweightSectors = [];
            foreach ($diversification['sector_allocation'] as $sector) {
                if ($sector['percentage'] > 30) {
                    $overweightSectors[] = $sector['sector'];
                }
            }
            
            if (!empty($overweightSectors)) {
                $recommendations[] = [
                    'type' => 'risk',
                    'priority' => 'medium',
                    'recommendation' => 'Your portfolio is overweight in the following sectors: ' . implode(', ', $overweightSectors),
                    'details' => 'Consider rebalancing to reduce sector-specific risk.'
                ];
            }
            
            // 3. Performance-based recommendations
            if ($performance['total_gain_loss_percentage'] < -10) {
                $recommendations[] = [
                    'type' => 'performance',
                    'priority' => 'medium',
                    'recommendation' => 'Your portfolio is underperforming with a loss of ' . number_format(abs($performance['total_gain_loss_percentage']), 2) . '%.',
                    'details' => 'Consider reviewing and potentially rebalancing your investments.'
                ];
            }
            
            // 4. Stock-specific recommendations
            if (isset($performance['worst_performing_stock']) && $performance['worst_performing_stock']['gain_loss_percentage'] < -15) {
                $worstStock = $performance['worst_performing_stock'];
                $recommendations[] = [
                    'type' => 'stock_specific',
                    'priority' => 'medium',
                    'recommendation' => $worstStock['stock_name'] . ' (' . $worstStock['stock_code'] . ') is your worst performing stock.',
                    'details' => 'Consider evaluating its long-term prospects or reducing your position.'
                ];
            }
            
            // 5. Recommended stocks based on risk profile
            $recommendedStocks = $this->getRecommendedStocks($riskLevel);
            
            if (!empty($recommendedStocks)) {
                $recommendations[] = [
                    'type' => 'new_investment',
                    'priority' => 'low',
                    'recommendation' => 'Based on your risk profile, consider these stocks:',
                    'details' => $recommendedStocks
                ];
            }
            
            return [
                'success' => true,
                'portfolio_id' => $portfolioId,
                'risk_profile' => $riskLevel,
                'recommendations' => $recommendations
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Error generating recommendations: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get recommended stocks based on risk profile
     * 
     * @param string $riskLevel Risk level (conservative, moderate, aggressive)
     * @return array Recommended stocks
     */
    private function getRecommendedStocks($riskLevel) {
        try {
            // Get top performing stocks from NSE based on risk profile
            $recommendations = $this->nseApiService->getRecommendedStocks($riskLevel);
            
            return $recommendations;
        } catch (Exception $e) {
            error_log("Error getting recommended stocks: " . $e->getMessage());
            return [];
        }
    }
    
    /**
     * Get historical performance of portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @param string $period Period for analysis (1d, 1w, 1m, 3m, 6m, 1y, all)
     * @return array Historical performance data
     */
    private function getHistoricalPerformance($portfolioId, $period = 'all') {
        try {
            // Calculate date range based on period
            $endDate = date('Y-m-d');
            $startDate = null;
            
            switch ($period) {
                case '1d':
                    $startDate = date('Y-m-d', strtotime('-1 day'));
                    break;
                case '1w':
                    $startDate = date('Y-m-d', strtotime('-1 week'));
                    break;
                case '1m':
                    $startDate = date('Y-m-d', strtotime('-1 month'));
                    break;
                case '3m':
                    $startDate = date('Y-m-d', strtotime('-3 months'));
                    break;
                case '6m':
                    $startDate = date('Y-m-d', strtotime('-6 months'));
                    break;
                case '1y':
                    $startDate = date('Y-m-d', strtotime('-1 year'));
                    break;
                case 'all':
                default:
                    // Get portfolio creation date
                    $stmt = $this->db->prepare("SELECT created_at FROM portfolios WHERE id = ?");
                    $stmt->bind_param("i", $portfolioId);
                    $stmt->execute();
                    $result = $stmt->get_result();
                    
                    if ($result->num_rows > 0) {
                        $row = $result->fetch_assoc();
                        $startDate = date('Y-m-d', strtotime($row['created_at']));
                    } else {
                        $startDate = date('Y-m-d', strtotime('-1 year'));
                    }
                    break;
            }
            
            // Get transactions for the period
            $transactions = $this->getPortfolioTransactions($portfolioId, null, null, $startDate, $endDate);
            
            // TODO: Get historical stock prices and calculate portfolio value over time
            // For now, return a simplified version
            
            return [
                'period' => $period,
                'start_date' => $startDate,
                'end_date' => $endDate,
                'transaction_count' => count($transactions)
            ];
        } catch (Exception $e) {
            error_log("Error getting historical performance: " . $e->getMessage());
            return [
                'period' => $period,
                'error' => $e->getMessage()
            ];
        }
    }
    
    /**
     * Calculate diversification score based on sector and stock allocations
     * 
     * @param array $sectorAllocation Sector allocation data
     * @param array $stockAllocation Stock allocation data
     * @return float Diversification score (0-100)
     */
    private function calculateDiversificationScore($sectorAllocation, $stockAllocation) {
        // Count number of sectors and stocks
        $sectorCount = count($sectorAllocation);
        $stockCount = count($stockAllocation);
        
        // Calculate sector concentration
        $sectorConcentration = 0;
        foreach ($sectorAllocation as $sector) {
            if ($sector['percentage'] > 30) {
                $sectorConcentration += ($sector['percentage'] - 30) / 2;
            }
        }
        
        // Calculate stock concentration
        $stockConcentration = 0;
        foreach ($stockAllocation as $stock) {
            if ($stock['percentage'] > 20) {
                $stockConcentration += ($stock['percentage'] - 20) / 2;
            }
        }
        
        // Calculate base score based on counts
        $sectorScore = min(($sectorCount / 5) * 50, 50);
        $stockScore = min(($stockCount / 10) * 50, 50);
        
        // Adjust scores based on concentration
        $sectorScore = max(0, $sectorScore - $sectorConcentration);
        $stockScore = max(0, $stockScore - $stockConcentration);
        
        // Calculate final score
        $finalScore = $sectorScore + $stockScore;
        
        return round($finalScore);
    }
    
    /**
     * Generate diversification recommendation
     * 
     * @param float $diversificationScore Diversification score
     * @param array $sectorAllocation Sector allocation data
     * @param array $stockAllocation Stock allocation data
     * @return string Recommendation
     */
    private function generateDiversificationRecommendation($diversificationScore, $sectorAllocation, $stockAllocation) {
        $recommendation = '';
        
        // Check for overweight sectors
        $overweightSectors = [];
        foreach ($sectorAllocation as $sector) {
            if ($sector['percentage'] > 30) {
                $overweightSectors[] = $sector['sector'];
            }
        }
        
        // Check for overweight stocks
        $overweightStocks = [];
        foreach ($stockAllocation as $stock) {
            if ($stock['percentage'] > 20) {
                $overweightStocks[] = $stock['stock_name'] . ' (' . $stock['stock_code'] . ')';
            }
        }
        
        // Generate recommendation based on score
        if ($diversificationScore < 30) {
            $recommendation = "Your portfolio has poor diversification. ";
        } elseif ($diversificationScore < 60) {
            $recommendation = "Your portfolio has moderate diversification. ";
        } else {
            $recommendation = "Your portfolio has good diversification. ";
        }
        
        // Add specific recommendations
        if (!empty($overweightSectors)) {
            $recommendation .= "Consider reducing exposure to the following sectors: " . implode(', ', $overweightSectors) . ". ";
        }
        
        if (!empty($overweightStocks)) {
            $recommendation .= "Consider reducing positions in these stocks: " . implode(', ', $overweightStocks) . ". ";
        }
        
        if (count($sectorAllocation) < 3) {
            $recommendation .= "Add stocks from different sectors to improve diversification. ";
        }
        
        if (count($stockAllocation) < 5) {
            $recommendation .= "Increase the number of stocks in your portfolio to spread risk. ";
        }
        
        return $recommendation;
    }
    
    /**
     * Get total value of portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @return float Total value
     */
    private function getPortfolioValue($portfolioId) {
        try {
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            $totalValue = 0;
            foreach ($holdings as $holding) {
                $totalValue += $holding['current_value'] ?? 0;
            }
            
            return $totalValue;
        } catch (Exception $e) {
            error_log("Error getting portfolio value: " . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Get total gain/loss of portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @return float Total gain/loss
     */
    private function getPortfolioGainLoss($portfolioId) {
        try {
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            $totalGainLoss = 0;
            foreach ($holdings as $holding) {
                $totalGainLoss += $holding['gain_loss'] ?? 0;
            }
            
            return $totalGainLoss;
        } catch (Exception $e) {
            error_log("Error getting portfolio gain/loss: " . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Get number of stocks in portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @return int Number of stocks
     */
    private function getPortfolioStockCount($portfolioId) {
        try {
            $stmt = $this->db->prepare("SELECT COUNT(*) as count FROM portfolio_holdings WHERE portfolio_id = ?");
            $stmt->bind_param("i", $portfolioId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $row = $result->fetch_assoc();
                return $row['count'];
            }
            
            return 0;
        } catch (Exception $e) {
            error_log("Error getting portfolio stock count: " . $e->getMessage());
            return 0;
        }
    }
    
    /**
     * Log portfolio activity
     * 
     * @param int $portfolioId Portfolio ID
     * @param string $activityType Activity type
     * @param string $description Activity description
     * @return bool Success status
     */
    private function logPortfolioActivity($portfolioId, $activityType, $description) {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO portfolio_activity_log 
                (portfolio_id, activity_type, description, created_at) 
                VALUES (?, ?, ?, ?)
            ");
            $createdAt = date('Y-m-d H:i:s');
            
            $stmt->bind_param("isss", $portfolioId, $activityType, $description, $createdAt);
            return $stmt->execute();
        } catch (Exception $e) {
            error_log("Error logging portfolio activity: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Import portfolio data from CSV
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @param string $csvContent CSV content
     * @return array Import result
     */
    public function importPortfolioFromCSV($userId, $portfolioId, $csvContent) {
        try {
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT id FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            // Parse CSV content
            $rows = explode("\n", $csvContent);
            $header = str_getcsv(array_shift($rows));
            
            // Validate header
            $requiredColumns = ['stock_code', 'quantity', 'purchase_price', 'purchase_date'];
            foreach ($requiredColumns as $column) {
                if (!in_array($column, $header)) {
                    return [
                        'success' => false,
                        'message' => "CSV is missing required column: $column"
                    ];
                }
            }
            
            // Process each row
            $imported = 0;
            $errors = [];
            
            foreach ($rows as $row) {
                if (empty(trim($row))) continue;
                
                $data = str_getcsv($row);
                
                if (count($data) !== count($header)) {
                    $errors[] = "Row has incorrect number of columns: " . implode(',', $data);
                    continue;
                }
                
                // Create associative array from row data
                $stockData = array_combine($header, $data);
                
                // Add stock to portfolio
                $result = $this->addStock(
                    $userId,
                    $portfolioId,
                    $stockData['stock_code'],
                    floatval($stockData['quantity']),
                    floatval($stockData['purchase_price']),
                    $stockData['purchase_date'],
                    $stockData['notes'] ?? ''
                );
                
                if ($result['success']) {
                    $imported++;
                } else {
                    $errors[] = "Error importing {$stockData['stock_code']}: {$result['message']}";
                }
            }
            
            // Log portfolio activity
            $this->logPortfolioActivity(
                $portfolioId, 
                'import_csv', 
                "Imported $imported stocks from CSV"
            );
            
            return [
                'success' => true,
                'message' => "Successfully imported $imported stocks",
                'imported_count' => $imported,
                'errors' => $errors
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Error importing portfolio: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Export portfolio to CSV
     * 
     * @param int $userId User ID
     * @param int $portfolioId Portfolio ID
     * @return array Export result with CSV content
     */
    public function exportPortfolioToCSV($userId, $portfolioId) {
        try {
            // Check if portfolio exists and belongs to user
            $stmt = $this->db->prepare("SELECT name FROM portfolios WHERE id = ? AND user_id = ?");
            $stmt->bind_param("ii", $portfolioId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Portfolio not found or access denied'
                ];
            }
            
            $portfolio = $result->fetch_assoc();
            
            // Get holdings
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            if (empty($holdings)) {
                return [
                    'success' => false,
                    'message' => 'Portfolio is empty'
                ];
            }
            
            // Create CSV content
            $csvHeader = [
                'stock_code', 'stock_name', 'quantity', 'average_price', 
                'current_price', 'current_value', 'gain_loss', 
                'gain_loss_percentage', 'sector'
            ];
            
            $csvContent = implode(',', $csvHeader) . "\n";
            
            foreach ($holdings as $holding) {
                $row = [
                    $holding['stock_code'],
                    str_replace(',', '', $holding['stock_name']),
                    $holding['quantity'],
                    $holding['average_price'],
                    $holding['current_price'] ?? $holding['average_price'],
                    $holding['current_value'] ?? ($holding['quantity'] * $holding['average_price']),
                    $holding['gain_loss'] ?? 0,
                    $holding['gain_loss_percentage'] ?? 0,
                    str_replace(',', '', $holding['sector'] ?? 'Unknown')
                ];
                
                $csvContent .= implode(',', $row) . "\n";
            }
            
            // Log portfolio activity
            $this->logPortfolioActivity(
                $portfolioId, 
                'export_csv', 
                "Exported portfolio to CSV"
            );
            
            return [
                'success' => true,
                'portfolio_name' => $portfolio['name'],
                'csv_content' => $csvContent,
                'filename' => strtolower(str_replace(' ', '_', $portfolio['name'])) . '_portfolio.csv'
            ];
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Error exporting portfolio: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get stock alerts for a portfolio
     * 
     * @param int $portfolioId Portfolio ID
     * @return array Stock alerts
     */
    public function getStockAlerts($portfolioId) {
        try {
            // Get holdings with current prices
            $holdings = $this->getPortfolioHoldings($portfolioId);
            
            $alerts = [];
            
            if (empty($holdings)) {
                return $alerts;
            }
            
            // Check for various alert conditions
            foreach ($holdings as $holding) {
                $stockCode = $holding['stock_code'];
                $stockName = $holding['stock_name'];
                $gainLossPercent = $holding['gain_loss_percentage'] ?? 0;
                $currentPrice = $holding['current_price'] ?? 0;
                $averagePrice = $holding['average_price'] ?? 0;
                
                // Alert for stocks with significant gains (potential sell opportunity)
                if ($gainLossPercent >= 15) {
                    $alerts[] = [
                        'type' => 'gain',
                        'priority' => 'medium',
                        'stock_code' => $stockCode,
                        'stock_name' => $stockName,
                        'message' => "$stockName ($stockCode) has gained " . number_format($gainLossPercent, 2) . "%. Consider taking profits."
                    ];
                }
                
                // Alert for stocks with significant losses
                if ($gainLossPercent <= -15) {
                    $alerts[] = [
                        'type' => 'loss',
                        'priority' => 'high',
                        'stock_code' => $stockCode,
                        'stock_name' => $stockName,
                        'message' => "$stockName ($stockCode) has lost " . number_format(abs($gainLossPercent), 2) . "%. Consider reviewing your position."
                    ];
                }
                
                // Alert for stocks near 52-week high (if available)
                if (isset($holding['52_week_high']) && $currentPrice >= ($holding['52_week_high'] * 0.95)) {
                    $alerts[] = [
                        'type' => 'near_high',
                        'priority' => 'low',
                        'stock_code' => $stockCode,
                        'stock_name' => $stockName,
                        'message' => "$stockName ($stockCode) is trading near its 52-week high."
                    ];
                }
                
                // Alert for stocks near 52-week low (if available)
                if (isset($holding['52_week_low']) && $currentPrice <= ($holding['52_week_low'] * 1.05)) {
                    $alerts[] = [
                        'type' => 'near_low',
                        'priority' => 'low',
                        'stock_code' => $stockCode,
                        'stock_name' => $stockName,
                        'message' => "$stockName ($stockCode) is trading near its 52-week low."
                    ];
                }
            }
            
            return $alerts;
        } catch (Exception $e) {
            error_log("Error getting stock alerts: " . $e->getMessage());
            return [];
        }
    }
}