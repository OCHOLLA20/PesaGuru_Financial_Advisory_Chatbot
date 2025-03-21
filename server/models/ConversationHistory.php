<?php
namespace App\Models;

class ConversationHistory {
    private $db;
    private $table = 'conversation_history';
    
    /**
     * Constructor
     * @param \PDO $db Database connection
     */
    public function __construct(\PDO $db) {
        $this->db = $db;
    }
    
    /**
     * Get recent conversation history for a user
     * @param int $userId User ID
     * @param int $limit Number of records to retrieve
     * @return array Conversation history
     */
    public function getRecentHistory($userId, $limit = 10) {
        $query = "SELECT * FROM {$this->table} 
                  WHERE user_id = :user_id 
                  ORDER BY created_at DESC 
                  LIMIT :limit";
        
        $stmt = $this->db->prepare($query);
        $stmt->bindParam(':user_id', $userId, \PDO::PARAM_INT);
        $stmt->bindParam(':limit', $limit, \PDO::PARAM_INT);
        $stmt->execute();
        
        return $stmt->fetchAll();
    }
    
    /**
     * Get all conversation history for a user
     * @param int $userId User ID
     * @param int $limit Number of records to retrieve
     * @return array Conversation history
     */
    public function getUserHistory($userId, $limit = 50) {
        $query = "SELECT * FROM {$this->table} 
                  WHERE user_id = :user_id 
                  ORDER BY created_at DESC 
                  LIMIT :limit";
        
        $stmt = $this->db->prepare($query);
        $stmt->bindParam(':user_id', $userId, \PDO::PARAM_INT);
        $stmt->bindParam(':limit', $limit, \PDO::PARAM_INT);
        $stmt->execute();
        
        return $stmt->fetchAll();
    }
    
    /**
     * Save conversation to database
     * @param array $data Conversation data
     * @return bool Success status
     */
    public function saveConversation($data) {
        $query = "INSERT INTO {$this->table} 
                  (user_id, user_message, bot_response, intent, entities, context, created_at) 
                  VALUES 
                  (:user_id, :user_message, :bot_response, :intent, :entities, :context, :created_at)";
        
        $stmt = $this->db->prepare($query);
        
        // Bind parameters
        $stmt->bindParam(':user_id', $data['user_id'], \PDO::PARAM_INT);
        $stmt->bindParam(':user_message', $data['user_message'], \PDO::PARAM_STR);
        $stmt->bindParam(':bot_response', $data['bot_response'], \PDO::PARAM_STR);
        $stmt->bindParam(':intent', $data['intent'], \PDO::PARAM_STR);
        $stmt->bindParam(':entities', $data['entities'], \PDO::PARAM_STR);
        $stmt->bindParam(':context', $data['context'], \PDO::PARAM_STR);
        $stmt->bindParam(':created_at', $data['created_at'], \PDO::PARAM_STR);
        
        return $stmt->execute();
    }
    
    /**
     * Delete conversation history for a user
     * @param int $userId User ID
     * @return bool Success status
     */
    public function deleteUserHistory($userId) {
        $query = "DELETE FROM {$this->table} WHERE user_id = :user_id";
        
        $stmt = $this->db->prepare($query);
        $stmt->bindParam(':user_id', $userId, \PDO::PARAM_INT);
        
        return $stmt->execute();
    }
}