<?php
namespace PesaGuru\Models;

use PDO;
use PDOException;

class UserFeedback {
    private $db;
    private static $table_name = "feedback";

    public function __construct($dbConnection) {
        $this->db = $dbConnection;
    }

    /**
     * Get feedback by user ID with filtering and pagination
     */
    public function getUserFeedback($user_id, $filters = [], $sort_by = 'created_at', $sort_dir = 'DESC', $limit = 20, $offset = 0) {
        $query = "SELECT f.*, c.message_id FROM " . self::$table_name . " f
                  LEFT JOIN conversation_history c ON f.conversation_id = c.id
                  WHERE f.user_id = :user_id";
        
        $params = ['user_id' => $user_id];
        
        // Apply filters dynamically
        foreach ($filters as $key => $value) {
            if (in_array($key, ['feedback_type', 'feature_area', 'rating', 'resolution_status'])) {
                $query .= " AND f.$key = :$key";
                $params[$key] = $value;
            }
            if ($key === 'start_date' && isset($filters['end_date'])) {
                $query .= " AND f.created_at BETWEEN :start_date AND :end_date";
                $params['start_date'] = $filters['start_date'];
                $params['end_date'] = $filters['end_date'];
            }
        }
        
        // Sorting and pagination
        $query .= " ORDER BY f." . htmlspecialchars(strip_tags($sort_by)) . " " . htmlspecialchars(strip_tags($sort_dir));
        $query .= " LIMIT :limit OFFSET :offset";
        
        try {
            $stmt = $this->db->prepare($query);
            foreach ($params as $key => $value) {
                $stmt->bindValue(":$key", $value, is_int($value) ? PDO::PARAM_INT : PDO::PARAM_STR);
            }
            $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
            $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
            $stmt->execute();
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
        } catch (PDOException $e) {
            return ['error' => $e->getMessage()];
        }
    }

    /**
     * Create new user feedback
     */
    public function create($data) {
        $query = "INSERT INTO " . self::$table_name . " 
                  (user_id, feedback_type, rating, comment, conversation_id, feature_area, resolution_status, created_at) 
                  VALUES (:user_id, :feedback_type, :rating, :comment, :conversation_id, :feature_area, :resolution_status, NOW())";
        
        try {
            $stmt = $this->db->prepare($query);
            foreach ($data as $key => $value) {
                $stmt->bindValue(":$key", $value, is_int($value) ? PDO::PARAM_INT : PDO::PARAM_STR);
            }
            return $stmt->execute() ? $this->db->lastInsertId() : false;
        } catch (PDOException $e) {
            return ['error' => $e->getMessage()];
        }
    }

    /**
     * Update user feedback
     */
    public function update($id, $data) {
        $setFields = [];
        foreach ($data as $key => $value) {
            $setFields[] = "$key = :$key";
        }
        $query = "UPDATE " . self::$table_name . " SET " . implode(', ', $setFields) . ", updated_at = NOW() WHERE id = :id";
        
        try {
            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':id', $id, PDO::PARAM_INT);
            foreach ($data as $key => $value) {
                $stmt->bindValue(":$key", $value, is_int($value) ? PDO::PARAM_INT : PDO::PARAM_STR);
            }
            return $stmt->execute();
        } catch (PDOException $e) {
            return ['error' => $e->getMessage()];
        }
    }

    /**
     * Delete feedback entry
     */
    public function delete($id) {
        $query = "DELETE FROM " . self::$table_name . " WHERE id = :id";
        try {
            $stmt = $this->db->prepare($query);
            $stmt->bindValue(':id', $id, PDO::PARAM_INT);
            return $stmt->execute();
        } catch (PDOException $e) {
            return ['error' => $e->getMessage()];
        }
    }
}
?>