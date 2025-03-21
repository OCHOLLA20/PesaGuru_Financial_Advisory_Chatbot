<?php
/**
 * UserProfiler Class
 * 
 * This service analyzes user data, preferences, and behavior to
 * build financial profiles and provide personalized recommendations.
 */

class UserProfiler {
    private $db;
    private $userId;
    private $userProfile = null;
    
    /**
     * Constructor initializes service
     * 
     * @param int $userId Optional user ID to load profile immediately
     */
    public function __construct($userId = null) {
        // Get database connection
        require_once __DIR__ . '/../config/db.php';
        $this->db = getDbConnection();
        
        // Load user profile if ID is provided
        if ($userId) {
            $this->userId = $userId;
            $this->loadUserProfile($userId);
        }
    }
    
    /**
     * Load a user's profile data
     * 
     * @param int $userId User ID
     * @return bool Success status
     */
    public function loadUserProfile($userId) {
        try {
            $this->userId = $userId;
            
            // Fetch user data from multiple tables
            $stmt = $this->db->prepare("
                SELECT 
                    u.id,
                    u.name,
                    u.email,
                    u.date_of_birth,
                    u.gender,
                    u.created_at as registration_date,
                    up.income_level,
                    up.employment_status,
                    up.financial_goals,
                    up.investment_experience,
                    up.risk_tolerance,
                    up.time_horizon,
                    rp.id as risk_profile_id,
                    rp.name as risk_profile_name,
                    rp.risk_level
                FROM users u
                LEFT JOIN user_preferences up ON u.id = up.user_id
                LEFT JOIN risk_profiles rp ON up.risk_profile_id = rp.id
                WHERE u.id = ?
            ");
            
            $stmt->bind_param("i", $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                $this->userProfile = null;
                return false;
            }
            
            // Populate user profile
            $this->userProfile = $result->fetch_assoc();
            
            // Add additional profile data
            $this->loadFinancialGoals();
            $this->loadActivitySummary();
            
            return true;
        } catch (Exception $e) {
            error_log("Error loading user profile: " . $e->getMessage());
            $this->userProfile = null;
            return false;
        }
    }
    
    /**
     * Get default risk profile for a user based on their preferences
     * 
     * @param int $userId User ID
     * @return string Default risk profile ID
     */
    public function getDefaultRiskProfile($userId) {
        // Load user profile if not already loaded
        if ($this->userId != $userId || $this->userProfile === null) {
            $this->loadUserProfile($userId);
        }
        
        // If user profile not found, return moderate risk profile
        if ($this->userProfile === null) {
            return $this->getModerateRiskProfileId();
        }
        
        // If user already has a risk profile, return it
        if (isset($this->userProfile['risk_profile_id']) && !empty($this->userProfile['risk_profile_id'])) {
            return $this->userProfile['risk_profile_id'];
        }
        
        // Otherwise, determine risk profile based on preferences
        $riskProfileId = $this->determineRiskProfile();
        
        // If risk profile couldn't be determined, return moderate
        if (empty($riskProfileId)) {
            return $this->getModerateRiskProfileId();
        }
        
        return $riskProfileId;
    }
    
    /**
     * Get user's risk tolerance level
     * 
     * @param int $userId User ID
     * @return string Risk tolerance level (low, moderate, high)
     */
    public function getRiskTolerance($userId = null) {
        // Use provided user ID or current user ID
        $userId = $userId ?? $this->userId;
        
        // Load user profile if not already loaded
        if ($this->userId != $userId || $this->userProfile === null) {
            $this->loadUserProfile($userId);
        }
        
        // If user profile not found, return moderate risk
        if ($this->userProfile === null) {
            return 'moderate';
        }
        
        // Get risk tolerance from user profile
        return $this->userProfile['risk_tolerance'] ?? 'moderate';
    }
    
    /**
     * Get user's financial goals
     * 
     * @param int $userId User ID
     * @return array Financial goals
     */
    public function getFinancialGoals($userId = null) {
        // Use provided user ID or current user ID
        $userId = $userId ?? $this->userId;
        
        // Load user profile if not already loaded
        if ($this->userId != $userId || $this->userProfile === null) {
            $this->loadUserProfile($userId);
        }
        
        // If user profile not found, return empty array
        if ($this->userProfile === null) {
            return [];
        }
        
        // Return financial goals
        return $this->userProfile['goals'] ?? [];
    }
    
    /**
     * Get user's investment preferences
     * 
     * @param int $userId User ID
     * @return array Investment preferences
     */
    public function getInvestmentPreferences($userId = null) {
        // Use provided user ID or current user ID
        $userId = $userId ?? $this->userId;
        
        try {
            // Get investment preferences from database
            $stmt = $this->db->prepare("
                SELECT
                    preferred_sectors,
                    preferred_investment_types,
                    preferred_time_horizon,
                    dividend_preference,
                    esg_preference
                FROM user_investment_preferences
                WHERE user_id = ?
            ");
            
            $stmt->bind_param("i", $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return $this->getDefaultInvestmentPreferences();
            }
            
            $preferences = $result->fetch_assoc();
            
            // Convert JSON strings to arrays
            if (isset($preferences['preferred_sectors'])) {
                $preferences['preferred_sectors'] = json_decode($preferences['preferred_sectors'], true) ?? [];
            }
            
            if (isset($preferences['preferred_investment_types'])) {
                $preferences['preferred_investment_types'] = json_decode($preferences['preferred_investment_types'], true) ?? [];
            }
            
            return $preferences;
        } catch (Exception $e) {
            error_log("Error getting investment preferences: " . $e->getMessage());
            return $this->getDefaultInvestmentPreferences();
        }
    }
    
    /**
     * Update user's risk profile based on survey responses
     * 
     * @param int $userId User ID
     * @param array $surveyResponses Survey responses
     * @return array Update result
     */
    public function updateRiskProfile($userId, $surveyResponses) {
        try {
            // Calculate risk score based on survey responses
            $riskScore = $this->calculateRiskScore($surveyResponses);
            
            // Map risk score to risk profile
            $riskProfileId = $this->mapRiskScoreToProfile($riskScore);
            
            // Get risk profile details
            $stmt = $this->db->prepare("SELECT id, name, risk_level FROM risk_profiles WHERE id = ?");
            $stmt->bind_param("s", $riskProfileId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'success' => false,
                    'message' => 'Risk profile not found'
                ];
            }
            
            $riskProfile = $result->fetch_assoc();
            
            // Update user preferences
            $stmt = $this->db->prepare("
                INSERT INTO user_preferences
                (user_id, risk_profile_id, risk_tolerance, investment_experience, time_horizon, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE
                risk_profile_id = VALUES(risk_profile_id),
                risk_tolerance = VALUES(risk_tolerance),
                investment_experience = VALUES(investment_experience),
                time_horizon = VALUES(time_horizon),
                updated_at = VALUES(updated_at)
            ");
            
            $riskTolerance = $surveyResponses['risk_tolerance'] ?? $riskProfile['risk_level'];
            $investmentExperience = $surveyResponses['investment_experience'] ?? 'moderate';
            $timeHorizon = $surveyResponses['time_horizon'] ?? 'medium';
            $updatedAt = date('Y-m-d H:i:s');
            
            $stmt->bind_param("isssss", 
                $userId, 
                $riskProfileId, 
                $riskTolerance, 
                $investmentExperience, 
                $timeHorizon, 
                $updatedAt
            );
            
            if ($stmt->execute()) {
                // Reload user profile
                $this->loadUserProfile($userId);
                
                return [
                    'success' => true,
                    'message' => 'Risk profile updated successfully',
                    'risk_profile' => [
                        'id' => $riskProfile['id'],
                        'name' => $riskProfile['name'],
                        'risk_level' => $riskProfile['risk_level']
                    ],
                    'risk_score' => $riskScore
                ];
            } else {
                return [
                    'success' => false,
                    'message' => 'Failed to update risk profile: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Error updating risk profile: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Update user's investment preferences
     * 
     * @param int $userId User ID
     * @param array $preferences Investment preferences
     * @return array Update result
     */
    public function updateInvestmentPreferences($userId, $preferences) {
        try {
            // Validate preferences
            $validatedPreferences = $this->validateInvestmentPreferences($preferences);
            
            // Convert arrays to JSON
            if (isset($validatedPreferences['preferred_sectors'])) {
                $validatedPreferences['preferred_sectors'] = json_encode($validatedPreferences['preferred_sectors']);
            }
            
            if (isset($validatedPreferences['preferred_investment_types'])) {
                $validatedPreferences['preferred_investment_types'] = json_encode($validatedPreferences['preferred_investment_types']);
            }
            
            // Build query dynamically based on provided preferences
            $fields = [];
            $values = [];
            $types = '';
            
            foreach ($validatedPreferences as $field => $value) {
                $fields[] = $field;
                $values[] = $value;
                
                // Determine parameter type
                if (is_bool($value)) {
                    $types .= 'i';
                } else {
                    $types .= 's';
                }
            }
            
            // Add user ID and updated timestamp
            $fields[] = 'user_id';
            $values[] = $userId;
            $types .= 'i';
            
            $fields[] = 'updated_at';
            $values[] = date('Y-m-d H:i:s');
            $types .= 's';
            
            // Build INSERT ... ON DUPLICATE KEY UPDATE query
            $insertFields = implode(', ', $fields);
            $insertPlaceholders = implode(', ', array_fill(0, count($fields), '?'));
            
            $updateFields = [];
            foreach ($fields as $field) {
                if ($field != 'user_id') {
                    $updateFields[] = "$field = VALUES($field)";
                }
            }
            $updateClause = implode(', ', $updateFields);
            
            $query = "
                INSERT INTO user_investment_preferences ($insertFields)
                VALUES ($insertPlaceholders)
                ON DUPLICATE KEY UPDATE $updateClause
            ";
            
            // Execute query
            $stmt = $this->db->prepare($query);
            
            // Create parameter array for bind_param
            $bindParams = array_merge([$types], $values);
            $bindParamsRef = [];
            
            foreach ($bindParams as $key => $value) {
                $bindParamsRef[$key] = &$bindParams[$key];
            }
            
            call_user_func_array([$stmt, 'bind_param'], $bindParamsRef);
            
            if ($stmt->execute()) {
                return [
                    'success' => true,
                    'message' => 'Investment preferences updated successfully'
                ];
            } else {
                return [
                    'success' => false,
                    'message' => 'Failed to update investment preferences: ' . $stmt->error
                ];
            }
        } catch (Exception $e) {
            return [
                'success' => false,
                'message' => 'Error updating investment preferences: ' . $e->getMessage()
            ];
        }
    }
    
    /**
     * Get personalized investment recommendations based on user profile
     * 
     * @param int $userId User ID
     * @param int $limit Number of recommendations to return
     * @return array Investment recommendations
     */
    public function getInvestmentRecommendations($userId = null, $limit = 5) {
        // Use provided user ID or current user ID
        $userId = $userId ?? $this->userId;
        
        try {
            // Get user's risk profile and preferences
            $riskTolerance = $this->getRiskTolerance($userId);
            $preferences = $this->getInvestmentPreferences($userId);
            
            // Get recommendations from database based on risk profile and preferences
            $query = "
                SELECT r.id, r.type, r.title, r.description, r.risk_level, r.potential_return,
                       r.time_horizon, r.min_investment, r.categories
                FROM investment_recommendations r
                WHERE r.risk_level = ? OR r.risk_level = 'all'
            ";
            
            $params = [$riskTolerance];
            $types = 's';
            
            // Add sector filter if preferred sectors are specified
            if (!empty($preferences['preferred_sectors'])) {
                $sectorFilter = [];
                foreach ($preferences['preferred_sectors'] as $sector) {
                    $sectorFilter[] = "r.categories LIKE ?";
                    $params[] = "%$sector%";
                    $types .= 's';
                }
                
                if (!empty($sectorFilter)) {
                    $query .= " AND (" . implode(' OR ', $sectorFilter) . ")";
                }
            }
            
            // Add time horizon filter if specified
            if (!empty($preferences['preferred_time_horizon'])) {
                $query .= " AND (r.time_horizon = ? OR r.time_horizon = 'any')";
                $params[] = $preferences['preferred_time_horizon'];
                $types .= 's';
            }
            
            // Add ESG preference filter if specified
            if (!empty($preferences['esg_preference']) && $preferences['esg_preference']) {
                $query .= " AND r.categories LIKE ?";
                $params[] = "%ESG%";
                $types .= 's';
            }
            
            // Limit results
            $query .= " ORDER BY r.potential_return DESC LIMIT ?";
            $params[] = $limit;
            $types .= 'i';
            
            // Execute query
            $stmt = $this->db->prepare($query);
            
            // Create parameter array for bind_param
            $bindParams = array_merge([$types], $params);
            $bindParamsRef = [];
            
            foreach ($bindParams as $key => $value) {
                $bindParamsRef[$key] = &$bindParams[$key];
            }
            
            call_user_func_array([$stmt, 'bind_param'], $bindParamsRef);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $recommendations = [];
            
            if ($result->num_rows > 0) {
                while ($row = $result->fetch_assoc()) {
                    // Convert categories JSON to array
                    if (isset($row['categories'])) {
                        $row['categories'] = json_decode($row['categories'], true) ?? [];
                    }
                    
                    $recommendations[] = $row;
                }
                
                return $recommendations;
            }
            
            // If no recommendations found, return simulated recommendations
            return $this->getSimulatedRecommendations($riskTolerance, $limit);
        } catch (Exception $e) {
            error_log("Error getting investment recommendations: " . $e->getMessage());
            return $this->getSimulatedRecommendations($riskTolerance, $limit);
        }
    }
    
    /**
     * Get user activity summary
     * 
     * @param int $userId User ID
     * @return array Activity summary
     */
    public function getActivitySummary($userId = null) {
        // Use provided user ID or current user ID
        $userId = $userId ?? $this->userId;
        
        try {
            // If user profile is loaded and has activity summary, return it
            if ($this->userProfile !== null && isset($this->userProfile['activity'])) {
                return $this->userProfile['activity'];
            }
            
            // Get user activity from database
            $stmt = $this->db->prepare("
                SELECT
                    (SELECT COUNT(*) FROM portfolios WHERE user_id = ?) as portfolio_count,
                    (SELECT COUNT(*) FROM portfolio_holdings ph
                        JOIN portfolios p ON ph.portfolio_id = p.id
                        WHERE p.user_id = ?) as stock_count,
                    (SELECT COUNT(*) FROM portfolio_transactions pt
                        JOIN portfolios p ON pt.portfolio_id = p.id
                        WHERE p.user_id = ?) as transaction_count,
                    (SELECT COUNT(*) FROM user_alerts WHERE user_id = ?) as alert_count,
                    (SELECT COUNT(*) FROM user_goals WHERE user_id = ?) as goal_count,
                    (SELECT MAX(created_at) FROM user_activity_log WHERE user_id = ?) as last_activity
            ");
            
            $stmt->bind_param("iiiiii", $userId, $userId, $userId, $userId, $userId, $userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows === 0) {
                return [
                    'portfolio_count' => 0,
                    'stock_count' => 0,
                    'transaction_count' => 0,
                    'alert_count' => 0,
                    'goal_count' => 0,
                    'last_activity' => null
                ];
            }
            
            $activity = $result->fetch_assoc();
            
            // If user profile is loaded, add activity summary to it
            if ($this->userProfile !== null) {
                $this->userProfile['activity'] = $activity;
            }
            
            return $activity;
        } catch (Exception $e) {
            error_log("Error getting activity summary: " . $e->getMessage());
            return [
                'portfolio_count' => 0,
                'stock_count' => 0,
                'transaction_count' => 0,
                'alert_count' => 0,
                'goal_count' => 0,
                'last_activity' => null
            ];
        }
    }
    
    /**
     * Get user's financial goals from database
     */
    private function loadFinancialGoals() {
        try {
            if ($this->userProfile === null) {
                return;
            }
            
            $stmt = $this->db->prepare("
                SELECT id, name, target_amount, current_amount, target_date, priority, status
                FROM user_goals
                WHERE user_id = ?
                ORDER BY priority DESC, target_date ASC
            ");
            
            $stmt->bind_param("i", $this->userId);
            $stmt->execute();
            $result = $stmt->get_result();
            
            $goals = [];
            
            while ($row = $result->fetch_assoc()) {
                $goals[] = $row;
            }
            
            $this->userProfile['goals'] = $goals;
        } catch (Exception $e) {
            error_log("Error loading financial goals: " . $e->getMessage());
            $this->userProfile['goals'] = [];
        }
    }
    
    /**
     * Load user activity summary
     */
    private function loadActivitySummary() {
        $this->userProfile['activity'] = $this->getActivitySummary($this->userId);
    }
    
    /**
     * Calculate risk score based on survey responses
     * 
     * @param array $surveyResponses Survey responses
     * @return int Risk score (0-100)
     */
    private function calculateRiskScore($surveyResponses) {
        // Define question weights
        $weights = [
            'age' => 15,
            'income_stability' => 10,
            'investment_horizon' => 15,
            'investment_knowledge' => 10,
            'risk_attitude' => 20,
            'loss_tolerance' => 15,
            'emergency_fund' => 5,
            'investment_goals' => 10
        ];
        
        // Define scoring for each question
        $scoring = [
            'age' => [
                'under_25' => 100,
                '26_35' => 90,
                '36_45' => 75,
                '46_55' => 50,
                '56_65' => 30,
                'over_65' => 10
            ],
            'income_stability' => [
                'very_stable' => 100,
                'stable' => 75,
                'average' => 50,
                'unstable' => 25,
                'very_unstable' => 0
            ],
            'investment_horizon' => [
                'less_than_1_year' => 10,
                '1_3_years' => 30,
                '3_5_years' => 60,
                '5_10_years' => 80,
                'more_than_10_years' => 100
            ],
            'investment_knowledge' => [
                'very_knowledgeable' => 100,
                'knowledgeable' => 75,
                'average' => 50,
                'limited' => 25,
                'none' => 0
            ],
            'risk_attitude' => [
                'very_aggressive' => 100,
                'aggressive' => 80,
                'moderate' => 60,
                'conservative' => 30,
                'very_conservative' => 0
            ],
            'loss_tolerance' => [
                'high' => 100,
                'moderate' => 60,
                'low' => 20
            ],
            'emergency_fund' => [
                'yes' => 100,
                'no' => 0
            ],
            'investment_goals' => [
                'high_growth' => 100,
                'growth' => 80,
                'balanced' => 60,
                'income' => 40,
                'capital_preservation' => 20
            ]
        ];
        
        // Calculate weighted score
        $totalScore = 0;
        $totalWeight = 0;
        
        foreach ($weights as $question => $weight) {
            if (isset($surveyResponses[$question]) && isset($scoring[$question][$surveyResponses[$question]])) {
                $totalScore += $scoring[$question][$surveyResponses[$question]] * $weight;
                $totalWeight += $weight;
            }
        }
        
        // Calculate final score (0-100)
        $finalScore = $totalWeight > 0 ? round($totalScore / $totalWeight) : 50;
        
        return max(0, min(100, $finalScore));
    }
    
    /**
     * Map risk score to risk profile ID
     * 
     * @param int $riskScore Risk score (0-100)
     * @return string Risk profile ID
     */
    private function mapRiskScoreToProfile($riskScore) {
        // Define risk profile ranges
        $ranges = [
            'very_conservative' => [0, 20],
            'conservative' => [21, 40],
            'moderate' => [41, 60],
            'growth' => [61, 80],
            'aggressive' => [81, 100]
        ];
        
        // Find matching risk profile
        foreach ($ranges as $profile => $range) {
            if ($riskScore >= $range[0] && $riskScore <= $range[1]) {
                return $this->getRiskProfileId($profile);
            }
        }
        
        // Default to moderate
        return $this->getModerateRiskProfileId();
    }
    
    /**
     * Get risk profile ID by name
     * 
     * @param string $profileName Risk profile name
     * @return string Risk profile ID
     */
    private function getRiskProfileId($profileName) {
        try {
            $stmt = $this->db->prepare("SELECT id FROM risk_profiles WHERE name = ?");
            $stmt->bind_param("s", $profileName);
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $row = $result->fetch_assoc();
                return $row['id'];
            }
            
            // If not found, return default
            return $this->getModerateRiskProfileId();
        } catch (Exception $e) {
            error_log("Error getting risk profile ID: " . $e->getMessage());
            return $this->getModerateRiskProfileId();
        }
    }
    
    /**
     * Get moderate risk profile ID
     * 
     * @return string Moderate risk profile ID
     */
    private function getModerateRiskProfileId() {
        try {
            $stmt = $this->db->prepare("SELECT id FROM risk_profiles WHERE risk_level = 'moderate' LIMIT 1");
            $stmt->execute();
            $result = $stmt->get_result();
            
            if ($result->num_rows > 0) {
                $row = $result->fetch_assoc();
                return $row['id'];
            }
            
            // If not found, return a default ID
            return 3; // Assuming ID 3 is moderate
        } catch (Exception $e) {
            error_log("Error getting moderate risk profile ID: " . $e->getMessage());
            return 3; // Assuming ID 3 is moderate
        }
    }
    
    /**
     * Determine risk profile based on user preferences
     * 
     * @return string Risk profile ID
     */
    private function determineRiskProfile() {
        if ($this->userProfile === null) {
            return $this->getModerateRiskProfileId();
        }
        
        // Define factors to consider
        $factors = [];
        
        // Age factor
        if (isset($this->userProfile['date_of_birth'])) {
            $birthDate = new DateTime($this->userProfile['date_of_birth']);
            $today = new DateTime();
            $age = $birthDate->diff($today)->y;
            
            if ($age < 30) {
                $factors[] = 'aggressive';
            } else if ($age < 45) {
                $factors[] = 'growth';
            } else if ($age < 60) {
                $factors[] = 'moderate';
            } else {
                $factors[] = 'conservative';
            }
        }
        
        // Investment experience factor
        if (isset($this->userProfile['investment_experience'])) {
            switch ($this->userProfile['investment_experience']) {
                case 'none':
                case 'beginner':
                    $factors[] = 'conservative';
                    break;
                case 'moderate':
                    $factors[] = 'moderate';
                    break;
                case 'experienced':
                case 'expert':
                    $factors[] = 'aggressive';
                    break;
            }
        }
        
        // Time horizon factor
        if (isset($this->userProfile['time_horizon'])) {
            switch ($this->userProfile['time_horizon']) {
                case 'short':
                    $factors[] = 'conservative';
                    break;
                case 'medium':
                    $factors[] = 'moderate';
                    break;
                case 'long':
                    $factors[] = 'aggressive';
                    break;
            }
        }
        
        // Risk tolerance factor (if explicitly set)
        if (isset($this->userProfile['risk_tolerance'])) {
            $factors[] = $this->userProfile['risk_tolerance'];
        }
        
        // Count occurrences of each profile
        $profileCounts = array_count_values($factors);
        
        // Find the most common profile
        arsort($profileCounts);
        $mostCommonProfile = key($profileCounts);
        
        // Get risk profile ID
        return $this->getRiskProfileId($mostCommonProfile);
    }
    
    /**
     * Validate investment preferences
     * 
     * @param array $preferences Investment preferences
     * @return array Validated preferences
     */
    private function validateInvestmentPreferences($preferences) {
        $validatedPreferences = [];
        
        // Validate preferred sectors
        if (isset($preferences['preferred_sectors'])) {
            $validSectors = [
                'Banking', 'Insurance', 'Manufacturing', 'Energy', 'Technology',
                'Agricultural', 'Commercial', 'Investment', 'Construction', 'Automobile',
                'FMCG', 'Healthcare', 'Real Estate', 'Telecommunications', 'Utilities'
            ];
            
            $preferredSectors = [];
            
            foreach ($preferences['preferred_sectors'] as $sector) {
                if (in_array($sector, $validSectors)) {
                    $preferredSectors[] = $sector;
                }
            }
            
            $validatedPreferences['preferred_sectors'] = $preferredSectors;
        }
        
        // Validate preferred investment types
        if (isset($preferences['preferred_investment_types'])) {
            $validTypes = [
                'Stocks', 'Bonds', 'Mutual Funds', 'ETFs', 'Real Estate',
                'Money Market', 'Treasury Bonds', 'Fixed Deposits', 'Cryptocurrency'
            ];
            
            $preferredTypes = [];
            
            foreach ($preferences['preferred_investment_types'] as $type) {
                if (in_array($type, $validTypes)) {
                    $preferredTypes[] = $type;
                }
            }
            
            $validatedPreferences['preferred_investment_types'] = $preferredTypes;
        }
        
        // Validate preferred time horizon
        if (isset($preferences['preferred_time_horizon'])) {
            $validTimeHorizons = ['short', 'medium', 'long'];
            
            if (in_array($preferences['preferred_time_horizon'], $validTimeHorizons)) {
                $validatedPreferences['preferred_time_horizon'] = $preferences['preferred_time_horizon'];
            }
        }
        
        // Validate dividend preference
        if (isset($preferences['dividend_preference'])) {
            $validatedPreferences['dividend_preference'] = (bool)$preferences['dividend_preference'];
        }
        
        // Validate ESG preference
        if (isset($preferences['esg_preference'])) {
            $validatedPreferences['esg_preference'] = (bool)$preferences['esg_preference'];
        }
        
        return $validatedPreferences;
    }
    
    /**
     * Get default investment preferences
     * 
     * @return array Default investment preferences
     */
    private function getDefaultInvestmentPreferences() {
        return [
            'preferred_sectors' => ['Banking', 'Technology', 'Energy'],
            'preferred_investment_types' => ['Stocks', 'Treasury Bonds'],
            'preferred_time_horizon' => 'medium',
            'dividend_preference' => false,
            'esg_preference' => false
        ];
    }
    
    /**
     * Get simulated investment recommendations (for development/testing)
     * 
     * @param string $riskLevel Risk level
     * @param int $limit Number of recommendations
     * @return array Simulated recommendations
     */
    private function getSimulatedRecommendations($riskLevel, $limit) {
        // Define recommendations for different risk levels
        $recommendationTemplates = [
            'conservative' => [
                [
                    'type' => 'stock',
                    'title' => 'Safaricom (SCOM)',
                    'description' => 'Leading telecommunications company with strong dividend history.',
                    'risk_level' => 'conservative',
                    'potential_return' => '8-12%',
                    'time_horizon' => 'long',
                    'min_investment' => 5000,
                    'categories' => ['Technology', 'Dividend']
                ],
                [
                    'type' => 'bond',
                    'title' => 'Kenya Government Treasury Bonds',
                    'description' => 'Government-backed bonds with stable returns.',
                    'risk_level' => 'conservative',
                    'potential_return' => '9-11%',
                    'time_horizon' => 'medium',
                    'min_investment' => 50000,
                    'categories' => ['Government', 'Fixed Income']
                ],
                [
                    'type' => 'stock',
                    'title' => 'Kenya Power (KPLC)',
                    'description' => 'Utility company with stable cash flows and dividend potential.',
                    'risk_level' => 'conservative',
                    'potential_return' => '7-10%',
                    'time_horizon' => 'long',
                    'min_investment' => 5000,
                    'categories' => ['Utilities', 'Dividend']
                ]
            ],
            'moderate' => [
                [
                    'type' => 'stock',
                    'title' => 'Equity Group Holdings (EQTY)',
                    'description' => 'Leading banking group with strong growth potential.',
                    'risk_level' => 'moderate',
                    'potential_return' => '12-18%',
                    'time_horizon' => 'medium',
                    'min_investment' => 10000,
                    'categories' => ['Banking', 'Growth']
                ],
                [
                    'type' => 'stock',
                    'title' => 'East African Breweries (EABL)',
                    'description' => 'Dominant beverage company with established market presence.',
                    'risk_level' => 'moderate',
                    'potential_return' => '10-15%',
                    'time_horizon' => 'medium',
                    'min_investment' => 15000,
                    'categories' => ['Manufacturing', 'Consumer Goods']
                ],
                [
                    'type' => 'mutual_fund',
                    'title' => 'CIC Balanced Fund',
                    'description' => 'Diversified fund with mix of stocks and bonds.',
                    'risk_level' => 'moderate',
                    'potential_return' => '10-14%',
                    'time_horizon' => 'medium',
                    'min_investment' => 5000,
                    'categories' => ['Diversified', 'Balanced']
                ]
            ],
            'aggressive' => [
                [
                    'type' => 'stock',
                    'title' => 'Bamburi Cement (BAMB)',
                    'description' => 'Leading cement manufacturer with growth potential from infrastructure projects.',
                    'risk_level' => 'aggressive',
                    'potential_return' => '15-25%',
                    'time_horizon' => 'long',
                    'min_investment' => 10000,
                    'categories' => ['Manufacturing', 'Construction']
                ],
                [
                    'type' => 'stock',
                    'title' => 'Carbacid Investments (CARB)',
                    'description' => 'Carbon dioxide manufacturing company with growth potential.',
                    'risk_level' => 'aggressive',
                    'potential_return' => '18-30%',
                    'time_horizon' => 'long',
                    'min_investment' => 5000,
                    'categories' => ['Manufacturing', 'Growth']
                ],
                [
                    'type' => 'etf',
                    'title' => 'NewGold ETF',
                    'description' => 'Gold-backed ETF offering exposure to gold price movements.',
                    'risk_level' => 'aggressive',
                    'potential_return' => '15-25%',
                    'time_horizon' => 'medium',
                    'min_investment' => 10000,
                    'categories' => ['Commodity', 'Alternative']
                ]
            ]
        ];
        
        // Get recommendations for the specified risk level
        $recommendations = $recommendationTemplates[$riskLevel] ?? $recommendationTemplates['moderate'];
        
        // Add some from other risk levels for diversity
        if ($riskLevel == 'moderate') {
            $recommendations = array_merge(
                $recommendations,
                array_slice($recommendationTemplates['conservative'], 0, 1),
                array_slice($recommendationTemplates['aggressive'], 0, 1)
            );
        } else if ($riskLevel == 'aggressive') {
            $recommendations = array_merge(
                $recommendations,
                array_slice($recommendationTemplates['moderate'], 0, 2)
            );
        } else if ($riskLevel == 'conservative') {
            $recommendations = array_merge(
                $recommendations,
                array_slice($recommendationTemplates['moderate'], 0, 2)
            );
        }
        
        // Add unique IDs
        foreach ($recommendations as $key => $recommendation) {
            $recommendations[$key]['id'] = $key + 1;
        }
        
        // Shuffle and limit
        shuffle($recommendations);
        return array_slice($recommendations, 0, $limit);
    }
}