<?php

namespace PesaGuru\Models;

use PDO;
use PDOException;
use Exception;

class UserModel {
    /**
     * Database connection
     * @var PDO
     */
    private $db;
    
    /**
     * User data
     * @var array
     */
    private $userData = [];
    
    /**
     * Error message
     * @var string
     */
    private $error = '';
    
    /**
     * Constructor
     * 
     * @param PDO $dbConnection Database connection
     */
    public function __construct(PDO $dbConnection) {
        $this->db = $dbConnection;
    }
    
    /**
     * Create a new user
     * 
     * @param array $userData User data array containing registration information
     * @return bool|int Returns user ID on success, false on failure
     */
    public function createUser(array $userData) {
        try {
            // Validate required fields
            $requiredFields = ['email', 'password', 'first_name', 'last_name', 'phone_number'];
            foreach ($requiredFields as $field) {
                if (empty($userData[$field])) {
                    $this->error = "Missing required field: $field";
                    return false;
                }
            }
            
            // Check if email already exists
            if ($this->emailExists($userData['email'])) {
                $this->error = "Email already registered";
                return false;
            }
            
            // Hash password
            $hashedPassword = password_hash($userData['password'], PASSWORD_BCRYPT);
            
            // Generate verification token
            $verificationToken = bin2hex(random_bytes(32));
            
            // Prepare SQL statement
            $stmt = $this->db->prepare(
                "INSERT INTO users (
                    email, password, first_name, last_name, phone_number, 
                    date_of_birth, gender, location, occupation, 
                    verification_token, is_verified, created_at, updated_at
                ) VALUES (
                    :email, :password, :first_name, :last_name, :phone_number,
                    :date_of_birth, :gender, :location, :occupation,
                    :verification_token, 0, NOW(), NOW()
                )"
            );
            
            // Bind parameters
            $stmt->bindParam(':email', $userData['email']);
            $stmt->bindParam(':password', $hashedPassword);
            $stmt->bindParam(':first_name', $userData['first_name']);
            $stmt->bindParam(':last_name', $userData['last_name']);
            $stmt->bindParam(':phone_number', $userData['phone_number']);
            
            // Optional fields
            $dateOfBirth = $userData['date_of_birth'] ?? null;
            $gender = $userData['gender'] ?? null;
            $location = $userData['location'] ?? null;
            $occupation = $userData['occupation'] ?? null;
            
            $stmt->bindParam(':date_of_birth', $dateOfBirth);
            $stmt->bindParam(':gender', $gender);
            $stmt->bindParam(':location', $location);
            $stmt->bindParam(':occupation', $occupation);
            $stmt->bindParam(':verification_token', $verificationToken);
            
            // Execute the query
            $stmt->execute();
            
            // Get the new user ID
            $userId = $this->db->lastInsertId();
            
            // Create default user settings
            $this->createUserSettings($userId);
            
            // Return the user ID
            return $userId;
            
        } catch (PDOException $e) {
            $this->error = "Database error: " . $e->getMessage();
            return false;
        } catch (Exception $e) {
            $this->error = "Error creating user: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Create default user settings
     * 
     * @param int $userId User ID
     * @return bool Success or failure
     */
    private function createUserSettings($userId) {
        try {
            $stmt = $this->db->prepare(
                "INSERT INTO user_settings (
                    user_id, language_preference, notification_preference, 
                    theme_preference, created_at, updated_at
                ) VALUES (
                    :user_id, 'english', 'email', 'light', NOW(), NOW()
                )"
            );
            $stmt->bindParam(':user_id', $userId);
            return $stmt->execute();
        } catch (PDOException $e) {
            $this->error = "Error creating user settings: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Check if email already exists
     * 
     * @param string $email Email to check
     * @return bool True if email exists, false if not
     */
    public function emailExists($email) {
        $stmt = $this->db->prepare("SELECT COUNT(*) FROM users WHERE email = :email");
        $stmt->bindParam(':email', $email);
        $stmt->execute();
        return $stmt->fetchColumn() > 0;
    }
    
    /**
     * Authenticate user
     * 
     * @param string $email User email
     * @param string $password User password
     * @return bool|int Returns user ID on success, false on failure
     */
    public function authenticateUser($email, $password) {
        try {
            // Get user by email
            $stmt = $this->db->prepare("SELECT id, password, is_verified, is_active FROM users WHERE email = :email");
            $stmt->bindParam(':email', $email);
            $stmt->execute();
            
            $user = $stmt->fetch(PDO::FETCH_ASSOC);
            
            // Check if user exists
            if (!$user) {
                $this->error = "Invalid email or password";
                return false;
            }
            
            // Verify password
            if (!password_verify($password, $user['password'])) {
                $this->error = "Invalid email or password";
                return false;
            }
            
            // Check if user is verified
            if (!$user['is_verified']) {
                $this->error = "Account not verified. Please check your email for verification instructions.";
                return false;
            }
            
            // Check if user is active
            if (!$user['is_active']) {
                $this->error = "Account is inactive. Please contact support.";
                return false;
            }
            
            // Update last login timestamp
            $this->updateLastLogin($user['id']);
            
            // Return user ID
            return $user['id'];
            
        } catch (PDOException $e) {
            $this->error = "Authentication error: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Update last login timestamp
     * 
     * @param int $userId User ID
     * @return bool Success or failure
     */
    private function updateLastLogin($userId) {
        try {
            $stmt = $this->db->prepare("UPDATE users SET last_login = NOW() WHERE id = :id");
            $stmt->bindParam(':id', $userId);
            return $stmt->execute();
        } catch (PDOException $e) {
            $this->error = "Error updating last login: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Get user by ID
     * 
     * @param int $userId User ID
     * @return array|bool User data array or false on failure
     */
    public function getUserById($userId) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    u.id, u.email, u.first_name, u.last_name, u.phone_number,
                    u.date_of_birth, u.gender, u.location, u.occupation,
                    u.is_verified, u.is_active, u.created_at, u.last_login,
                    us.language_preference, us.notification_preference, us.theme_preference
                FROM 
                    users u
                LEFT JOIN 
                    user_settings us ON u.id = us.user_id
                WHERE 
                    u.id = :id
            ");
            $stmt->bindParam(':id', $userId);
            $stmt->execute();
            
            $userData = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$userData) {
                $this->error = "User not found";
                return false;
            }
            
            $this->userData = $userData;
            return $userData;
            
        } catch (PDOException $e) {
            $this->error = "Error retrieving user: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Update user profile
     * 
     * @param int $userId User ID
     * @param array $userData User data to update
     * @return bool Success or failure
     */
    public function updateUser($userId, array $userData) {
        try {
            // Build update fields
            $updateFields = [];
            $params = [':id' => $userId];
            
            // Fields that can be updated
            $allowedFields = [
                'first_name', 'last_name', 'phone_number', 
                'date_of_birth', 'gender', 'location', 'occupation'
            ];
            
            foreach ($allowedFields as $field) {
                if (isset($userData[$field])) {
                    $updateFields[] = "$field = :$field";
                    $params[":$field"] = $userData[$field];
                }
            }
            
            // If no fields to update
            if (empty($updateFields)) {
                $this->error = "No fields to update";
                return false;
            }
            
            // Add updated_at field
            $updateFields[] = "updated_at = NOW()";
            
            // Build and execute query
            $sql = "UPDATE users SET " . implode(', ', $updateFields) . " WHERE id = :id";
            $stmt = $this->db->prepare($sql);
            
            foreach ($params as $key => &$val) {
                $stmt->bindParam($key, $val);
            }
            
            return $stmt->execute();
            
        } catch (PDOException $e) {
            $this->error = "Error updating user: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Update user settings
     * 
     * @param int $userId User ID
     * @param array $settings Settings to update
     * @return bool Success or failure
     */
    public function updateUserSettings($userId, array $settings) {
        try {
            // Build update fields
            $updateFields = [];
            $params = [':user_id' => $userId];
            
            // Fields that can be updated
            $allowedFields = [
                'language_preference', 'notification_preference', 'theme_preference'
            ];
            
            foreach ($allowedFields as $field) {
                if (isset($settings[$field])) {
                    $updateFields[] = "$field = :$field";
                    $params[":$field"] = $settings[$field];
                }
            }
            
            // If no fields to update
            if (empty($updateFields)) {
                $this->error = "No settings to update";
                return false;
            }
            
            // Add updated_at field
            $updateFields[] = "updated_at = NOW()";
            
            // Check if settings exist for user
            $stmt = $this->db->prepare("SELECT COUNT(*) FROM user_settings WHERE user_id = :user_id");
            $stmt->bindParam(':user_id', $userId);
            $stmt->execute();
            
            if ($stmt->fetchColumn() > 0) {
                // Update existing settings
                $sql = "UPDATE user_settings SET " . implode(', ', $updateFields) . " WHERE user_id = :user_id";
            } else {
                // Create new settings
                return $this->createUserSettings($userId);
            }
            
            $stmt = $this->db->prepare($sql);
            
            foreach ($params as $key => &$val) {
                $stmt->bindParam($key, $val);
            }
            
            return $stmt->execute();
            
        } catch (PDOException $e) {
            $this->error = "Error updating user settings: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Change user password
     * 
     * @param int $userId User ID
     * @param string $currentPassword Current password
     * @param string $newPassword New password
     * @return bool Success or failure
     */
    public function changePassword($userId, $currentPassword, $newPassword) {
        try {
            // Get current password
            $stmt = $this->db->prepare("SELECT password FROM users WHERE id = :id");
            $stmt->bindParam(':id', $userId);
            $stmt->execute();
            
            $currentHash = $stmt->fetchColumn();
            
            // Verify current password
            if (!password_verify($currentPassword, $currentHash)) {
                $this->error = "Current password is incorrect";
                return false;
            }
            
            // Hash new password
            $newHash = password_hash($newPassword, PASSWORD_BCRYPT);
            
            // Update password
            $stmt = $this->db->prepare("UPDATE users SET password = :password, updated_at = NOW() WHERE id = :id");
            $stmt->bindParam(':password', $newHash);
            $stmt->bindParam(':id', $userId);
            
            return $stmt->execute();
            
        } catch (PDOException $e) {
            $this->error = "Error changing password: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Reset password
     * 
     * @param string $email User email
     * @return bool|string Returns reset token on success, false on failure
     */
    public function resetPassword($email) {
        try {
            // Check if email exists
            if (!$this->emailExists($email)) {
                $this->error = "Email not found";
                return false;
            }
            
            // Generate reset token
            $resetToken = bin2hex(random_bytes(32));
            $tokenExpiry = date('Y-m-d H:i:s', strtotime('+24 hours'));
            
            // Save reset token
            $stmt = $this->db->prepare("
                UPDATE users 
                SET reset_token = :reset_token, 
                    reset_token_expiry = :token_expiry, 
                    updated_at = NOW() 
                WHERE email = :email
            ");
            
            $stmt->bindParam(':reset_token', $resetToken);
            $stmt->bindParam(':token_expiry', $tokenExpiry);
            $stmt->bindParam(':email', $email);
            
            if ($stmt->execute()) {
                return $resetToken;
            } else {
                $this->error = "Failed to generate reset token";
                return false;
            }
            
        } catch (PDOException $e) {
            $this->error = "Error in password reset: " . $e->getMessage();
            return false;
        } catch (Exception $e) {
            $this->error = "Error generating reset token: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Verify reset token and set new password
     * 
     * @param string $token Reset token
     * @param string $newPassword New password
     * @return bool Success or failure
     */
    public function confirmResetPassword($token, $newPassword) {
        try {
            // Check if token exists and is valid
            $stmt = $this->db->prepare("
                SELECT id FROM users 
                WHERE reset_token = :token 
                AND reset_token_expiry > NOW()
            ");
            $stmt->bindParam(':token', $token);
            $stmt->execute();
            
            $userId = $stmt->fetchColumn();
            
            if (!$userId) {
                $this->error = "Invalid or expired reset token";
                return false;
            }
            
            // Hash new password
            $hashedPassword = password_hash($newPassword, PASSWORD_BCRYPT);
            
            // Update password and clear token
            $stmt = $this->db->prepare("
                UPDATE users 
                SET password = :password, 
                    reset_token = NULL, 
                    reset_token_expiry = NULL, 
                    updated_at = NOW() 
                WHERE id = :id
            ");
            
            $stmt->bindParam(':password', $hashedPassword);
            $stmt->bindParam(':id', $userId);
            
            return $stmt->execute();
            
        } catch (PDOException $e) {
            $this->error = "Error confirming password reset: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Verify user account
     * 
     * @param string $token Verification token
     * @return bool Success or failure
     */
    public function verifyAccount($token) {
        try {
            // Check if token exists
            $stmt = $this->db->prepare("
                SELECT id FROM users 
                WHERE verification_token = :token 
                AND is_verified = 0
            ");
            $stmt->bindParam(':token', $token);
            $stmt->execute();
            
            $userId = $stmt->fetchColumn();
            
            if (!$userId) {
                $this->error = "Invalid verification token";
                return false;
            }
            
            // Update user verification status
            $stmt = $this->db->prepare("
                UPDATE users 
                SET is_verified = 1, 
                    verification_token = NULL, 
                    updated_at = NOW() 
                WHERE id = :id
            ");
            $stmt->bindParam(':id', $userId);
            
            return $stmt->execute();
            
        } catch (PDOException $e) {
            $this->error = "Error verifying account: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Delete user account
     * 
     * @param int $userId User ID
     * @param string $password User password for verification
     * @return bool Success or failure
     */
    public function deleteUser($userId, $password) {
        try {
            // Begin transaction
            $this->db->beginTransaction();
            
            // Verify password
            $stmt = $this->db->prepare("SELECT password FROM users WHERE id = :id");
            $stmt->bindParam(':id', $userId);
            $stmt->execute();
            
            $currentHash = $stmt->fetchColumn();
            
            if (!password_verify($password, $currentHash)) {
                $this->error = "Invalid password";
                $this->db->rollBack();
                return false;
            }
            
            // Delete related data (settings, goals, etc.)
            $tables = [
                'user_settings',
                'financial_goals',
                'risk_profiles',
                'portfolios',
                'conversation_history'
            ];
            
            foreach ($tables as $table) {
                $stmt = $this->db->prepare("DELETE FROM $table WHERE user_id = :user_id");
                $stmt->bindParam(':user_id', $userId);
                $stmt->execute();
            }
            
            // Delete user
            $stmt = $this->db->prepare("DELETE FROM users WHERE id = :id");
            $stmt->bindParam(':id', $userId);
            $result = $stmt->execute();
            
            if ($result) {
                $this->db->commit();
                return true;
            } else {
                $this->db->rollBack();
                $this->error = "Failed to delete user";
                return false;
            }
            
        } catch (PDOException $e) {
            $this->db->rollBack();
            $this->error = "Error deleting user: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Get financial risk profile for user
     * 
     * @param int $userId User ID
     * @return array|bool Risk profile data or false on failure
     */
    public function getUserRiskProfile($userId) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    rp.id, rp.risk_level, rp.risk_score, rp.investment_horizon,
                    rp.income_stability, rp.emergency_funds, rp.debt_ratio,
                    rp.created_at, rp.updated_at
                FROM 
                    risk_profiles rp
                WHERE 
                    rp.user_id = :user_id
                ORDER BY 
                    rp.created_at DESC
                LIMIT 1
            ");
            
            $stmt->bindParam(':user_id', $userId);
            $stmt->execute();
            
            $riskProfile = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$riskProfile) {
                return [
                    'risk_level' => 'Not Assessed',
                    'risk_score' => 0,
                    'investment_horizon' => null,
                    'income_stability' => null,
                    'emergency_funds' => null,
                    'debt_ratio' => null
                ];
            }
            
            return $riskProfile;
            
        } catch (PDOException $e) {
            $this->error = "Error retrieving risk profile: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Get user's financial goals
     * 
     * @param int $userId User ID
     * @return array|bool Array of financial goals or false on failure
     */
    public function getUserFinancialGoals($userId) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    id, goal_type, goal_name, target_amount, current_amount,
                    target_date, priority, status, created_at, updated_at
                FROM 
                    financial_goals
                WHERE 
                    user_id = :user_id
                ORDER BY 
                    priority ASC, target_date ASC
            ");
            
            $stmt->bindParam(':user_id', $userId);
            $stmt->execute();
            
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
            
        } catch (PDOException $e) {
            $this->error = "Error retrieving financial goals: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Get error message
     * 
     * @return string Last error message
     */
    public function getError() {
        return $this->error;
    }
    
    /**
     * Check if user exists
     * 
     * @param int $userId User ID
     * @return bool True if user exists, false if not
     */
    public function userExists($userId) {
        $stmt = $this->db->prepare("SELECT COUNT(*) FROM users WHERE id = :id");
        $stmt->bindParam(':id', $userId);
        $stmt->execute();
        return $stmt->fetchColumn() > 0;
    }
    
    /**
     * Get recent conversation history for a user
     * 
     * @param int $userId User ID
     * @param int $limit Number of conversations to retrieve
     * @return array|bool Array of conversations or false on failure
     */
    public function getRecentConversations($userId, $limit = 10) {
        try {
            $stmt = $this->db->prepare("
                SELECT 
                    id, conversation_type, topic, summary, 
                    created_at, updated_at
                FROM 
                    conversation_history
                WHERE 
                    user_id = :user_id
                ORDER BY 
                    updated_at DESC
                LIMIT :limit
            ");
            
            $stmt->bindParam(':user_id', $userId);
            $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
            
        } catch (PDOException $e) {
            $this->error = "Error retrieving conversations: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Get all users with pagination
     * 
     * @param int $page Page number
     * @param int $perPage Records per page
     * @return array|bool Array of users or false on failure
     */
    public function getAllUsers($page = 1, $perPage = 20) {
        try {
            $offset = ($page - 1) * $perPage;
            
            // Get users
            $stmt = $this->db->prepare("
                SELECT 
                    id, email, first_name, last_name, 
                    is_verified, is_active, created_at, last_login
                FROM 
                    users
                ORDER BY 
                    created_at DESC
                LIMIT :limit OFFSET :offset
            ");
            
            $stmt->bindParam(':limit', $perPage, PDO::PARAM_INT);
            $stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
            $stmt->execute();
            
            $users = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Get total count
            $stmt = $this->db->prepare("SELECT COUNT(*) FROM users");
            $stmt->execute();
            $totalUsers = $stmt->fetchColumn();
            
            return [
                'users' => $users,
                'total' => $totalUsers,
                'page' => $page,
                'per_page' => $perPage,
                'total_pages' => ceil($totalUsers / $perPage)
            ];
            
        } catch (PDOException $e) {
            $this->error = "Error retrieving users: " . $e->getMessage();
            return false;
        }
    }
    
    /**
     * Search users
     * 
     * @param string $query Search query
     * @param int $limit Result limit
     * @return array|bool Array of matching users or false on failure
     */
    public function searchUsers($query, $limit = 20) {
        try {
            $searchTerm = "%$query%";
            
            $stmt = $this->db->prepare("
                SELECT 
                    id, email, first_name, last_name, 
                    is_verified, is_active, created_at
                FROM 
                    users
                WHERE 
                    email LIKE :term OR
                    first_name LIKE :term OR
                    last_name LIKE :term OR
                    phone_number LIKE :term
                ORDER BY 
                    created_at DESC
                LIMIT :limit
            ");
            
            $stmt->bindParam(':term', $searchTerm);
            $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
            $stmt->execute();
            
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
            
        } catch (PDOException $e) {
            $this->error = "Error searching users: " . $e->getMessage();
            return false;
        }
    }
}
