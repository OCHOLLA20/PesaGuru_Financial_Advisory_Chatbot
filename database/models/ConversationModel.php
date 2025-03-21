<?php

namespace PesaGuru\Database\Models;

use PDO;
use PesaGuru\Server\Config\Database;
use PesaGuru\AI\Services\SentimentAnalysisService;
use PesaGuru\AI\Services\IntentClassificationService;
use PesaGuru\Server\Security\EncryptionService;

// Import required dependencies
require_once __DIR__ . '/../../server/config/db.php';
require_once __DIR__ . '/../../ai/services/sentiment_analysis.php';
require_once __DIR__ . '/../../ai/services/intent_classification.php';
require_once __DIR__ . '/../../server/security/encryption_service.php';

class ConversationModel {
    private $db;
    private $encryptionService;
    private $sentimentAnalysis;
    private $intentClassification;

    /**
     * Constructor - initialize database connection and required services
     */
    public function __construct() {
        $this->db = Database::getConnection();
        $this->encryptionService = new EncryptionService();
        $this->sentimentAnalysis = new SentimentAnalysisService();
        $this->intentClassification = new IntentClassificationService();
    }

    /**
     * Create a new conversation session
     * 
     * @param int $userId User identifier
     * @param string $deviceInfo Device information
     * @param string $language 'en' for English, 'sw' for Swahili
     * @return int|bool The new conversation session ID or false on failure
     */
    public function createConversationSession($userId, $deviceInfo, $language = 'en') {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO conversation_sessions 
                (user_id, start_time, last_activity, device_info, language, status) 
                VALUES (:userId, NOW(), NOW(), :deviceInfo, :language, 'active')
            ");
            
            $stmt->bindParam(':userId', $userId, PDO::PARAM_INT);
            $stmt->bindParam(':deviceInfo', $deviceInfo, PDO::PARAM_STR);
            $stmt->bindParam(':language', $language, PDO::PARAM_STR);
            
            $stmt->execute();
            return $this->db->lastInsertId();
        } catch (\PDOException $e) {
            error_log("Error creating conversation session: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Store a user message and chatbot response
     * 
     * @param int $sessionId Conversation session ID
     * @param int $userId User ID
     * @param string $userMessage User's message
     * @param string $botResponse Chatbot's response
     * @param array $intentData Intent classification data
     * @param array $entities Extracted financial entities
     * @param float $sentimentScore Sentiment analysis score
     * @param array $contextData Conversation context data
     * @return int|bool The message ID or false on failure
     */
    public function storeMessage($sessionId, $userId, $userMessage, $botResponse, $intentData = [], $entities = [], $sentimentScore = 0, $contextData = []) {
        try {
            // Begin transaction
            $this->db->beginTransaction();
            
            // Encrypt sensitive user message for privacy
            $encryptedMessage = $this->encryptionService->encrypt($userMessage);
            
            // Store the user message
            $stmtUser = $this->db->prepare("
                INSERT INTO conversation_messages 
                (session_id, user_id, message_type, message_content, timestamp, 
                intent_type, intent_confidence, entities, sentiment_score, context_data) 
                VALUES 
                (:sessionId, :userId, 'user', :messageContent, NOW(), 
                :intentType, :intentConfidence, :entities, :sentimentScore, :contextData)
            ");
            
            $intentType = isset($intentData['type']) ? $intentData['type'] : null;
            $intentConfidence = isset($intentData['confidence']) ? $intentData['confidence'] : 0;
            $entitiesJson = json_encode($entities);
            $contextDataJson = json_encode($contextData);
            
            $stmtUser->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmtUser->bindParam(':userId', $userId, PDO::PARAM_INT);
            $stmtUser->bindParam(':messageContent', $encryptedMessage, PDO::PARAM_STR);
            $stmtUser->bindParam(':intentType', $intentType, PDO::PARAM_STR);
            $stmtUser->bindParam(':intentConfidence', $intentConfidence, PDO::PARAM_STR);
            $stmtUser->bindParam(':entities', $entitiesJson, PDO::PARAM_STR);
            $stmtUser->bindParam(':sentimentScore', $sentimentScore, PDO::PARAM_STR);
            $stmtUser->bindParam(':contextData', $contextDataJson, PDO::PARAM_STR);
            
            $stmtUser->execute();
            $userMessageId = $this->db->lastInsertId();
            
            // Store the bot response
            $stmtBot = $this->db->prepare("
                INSERT INTO conversation_messages 
                (session_id, user_id, message_type, message_content, timestamp, parent_message_id) 
                VALUES 
                (:sessionId, :userId, 'bot', :messageContent, NOW(), :parentMessageId)
            ");
            
            $stmtBot->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmtBot->bindParam(':userId', $userId, PDO::PARAM_INT);
            $stmtBot->bindParam(':messageContent', $botResponse, PDO::PARAM_STR);
            $stmtBot->bindParam(':parentMessageId', $userMessageId, PDO::PARAM_INT);
            
            $stmtBot->execute();
            
            // Update the last activity time for the session
            $stmtSession = $this->db->prepare("
                UPDATE conversation_sessions 
                SET last_activity = NOW() 
                WHERE id = :sessionId
            ");
            
            $stmtSession->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmtSession->execute();
            
            // Commit transaction
            $this->db->commit();
            
            return $userMessageId;
        } catch (\PDOException $e) {
            // Rollback transaction on error
            $this->db->rollBack();
            error_log("Error storing conversation message: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Process a user message through NLP and return an enhanced representation
     * 
     * @param string $userMessage The user's message text
     * @param string $language Language code (en/sw)
     * @return array Processed message data with intent, entities, and sentiment
     */
    public function processUserMessage($userMessage, $language = 'en') {
        // Process intent classification
        $intentData = $this->intentClassification->classifyIntent($userMessage, $language);
        
        // Extract financial entities
        $entities = $this->intentClassification->extractEntities($userMessage, $language);
        
        // Analyze sentiment
        $sentimentScore = $this->sentimentAnalysis->analyzeSentiment($userMessage, $language);
        
        return [
            'intent' => $intentData,
            'entities' => $entities,
            'sentiment_score' => $sentimentScore
        ];
    }

    /**
     * Get conversation history for a specific user
     * 
     * @param int $userId User identifier
     * @param int $limit Maximum number of conversations to return
     * @param int $offset Pagination offset
     * @return array Array of conversation sessions with messages
     */
    public function getUserConversationHistory($userId, $limit = 10, $offset = 0) {
        try {
            // Get the user's conversation sessions
            $stmtSessions = $this->db->prepare("
                SELECT id, start_time, last_activity, language, status
                FROM conversation_sessions
                WHERE user_id = :userId
                ORDER BY last_activity DESC
                LIMIT :limit OFFSET :offset
            ");
            
            $stmtSessions->bindParam(':userId', $userId, PDO::PARAM_INT);
            $stmtSessions->bindParam(':limit', $limit, PDO::PARAM_INT);
            $stmtSessions->bindParam(':offset', $offset, PDO::PARAM_INT);
            
            $stmtSessions->execute();
            $sessions = $stmtSessions->fetchAll(PDO::FETCH_ASSOC);
            
            // For each session, get the conversation messages
            $result = [];
            foreach ($sessions as $session) {
                $stmtMessages = $this->db->prepare("
                    SELECT id, message_type, message_content, timestamp, 
                    intent_type, entities, sentiment_score, context_data,
                    feedback_rating, feedback_comment
                    FROM conversation_messages
                    WHERE session_id = :sessionId
                    ORDER BY timestamp ASC
                ");
                
                $stmtMessages->bindParam(':sessionId', $session['id'], PDO::PARAM_INT);
                $stmtMessages->execute();
                $messages = $stmtMessages->fetchAll(PDO::FETCH_ASSOC);
                
                // Decrypt user messages
                foreach ($messages as &$message) {
                    if ($message['message_type'] === 'user') {
                        $message['message_content'] = $this->encryptionService->decrypt($message['message_content']);
                    }
                    
                    // Parse JSON fields
                    if (!empty($message['entities'])) {
                        $message['entities'] = json_decode($message['entities'], true);
                    }
                    
                    if (!empty($message['context_data'])) {
                        $message['context_data'] = json_decode($message['context_data'], true);
                    }
                }
                
                $session['messages'] = $messages;
                $result[] = $session;
            }
            
            return $result;
        } catch (\PDOException $e) {
            error_log("Error retrieving conversation history: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Get a specific conversation session with all messages
     * 
     * @param int $sessionId Conversation session ID
     * @return array|bool Conversation data or false on failure
     */
    public function getConversationSession($sessionId) {
        try {
            // Get session details
            $stmtSession = $this->db->prepare("
                SELECT id, user_id, start_time, last_activity, device_info, language, status
                FROM conversation_sessions
                WHERE id = :sessionId
            ");
            
            $stmtSession->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmtSession->execute();
            $session = $stmtSession->fetch(PDO::FETCH_ASSOC);
            
            if (!$session) {
                return false;
            }
            
            // Get messages for this session
            $stmtMessages = $this->db->prepare("
                SELECT id, message_type, message_content, timestamp, 
                intent_type, entities, sentiment_score, context_data,
                feedback_rating, feedback_comment
                FROM conversation_messages
                WHERE session_id = :sessionId
                ORDER BY timestamp ASC
            ");
            
            $stmtMessages->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmtMessages->execute();
            $messages = $stmtMessages->fetchAll(PDO::FETCH_ASSOC);
            
            // Decrypt user messages
            foreach ($messages as &$message) {
                if ($message['message_type'] === 'user') {
                    $message['message_content'] = $this->encryptionService->decrypt($message['message_content']);
                }
                
                // Parse JSON fields
                if (!empty($message['entities'])) {
                    $message['entities'] = json_decode($message['entities'], true);
                }
                
                if (!empty($message['context_data'])) {
                    $message['context_data'] = json_decode($message['context_data'], true);
                }
            }
            
            $session['messages'] = $messages;
            return $session;
        } catch (\PDOException $e) {
            error_log("Error retrieving conversation session: " . $e->getMessage());
            return false;
        }
    }

    /**
     * End a conversation session
     * 
     * @param int $sessionId Conversation session ID
     * @param string $reason Reason for ending the session
     * @return bool Success status
     */
    public function endConversationSession($sessionId, $reason = 'user_closed') {
        try {
            $stmt = $this->db->prepare("
                UPDATE conversation_sessions
                SET status = 'closed', end_time = NOW(), end_reason = :reason
                WHERE id = :sessionId
            ");
            
            $stmt->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmt->bindParam(':reason', $reason, PDO::PARAM_STR);
            
            return $stmt->execute();
        } catch (\PDOException $e) {
            error_log("Error ending conversation session: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Store user feedback for a bot message
     * 
     * @param int $messageId The bot message ID
     * @param int $rating Feedback rating (1-5)
     * @param string $comment User comment (optional)
     * @return bool Success status
     */
    public function storeMessageFeedback($messageId, $rating, $comment = '') {
        try {
            $stmt = $this->db->prepare("
                UPDATE conversation_messages
                SET feedback_rating = :rating, feedback_comment = :comment, feedback_time = NOW()
                WHERE id = :messageId AND message_type = 'bot'
            ");
            
            $stmt->bindParam(':messageId', $messageId, PDO::PARAM_INT);
            $stmt->bindParam(':rating', $rating, PDO::PARAM_INT);
            $stmt->bindParam(':comment', $comment, PDO::PARAM_STR);
            
            return $stmt->execute();
        } catch (\PDOException $e) {
            error_log("Error storing message feedback: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Get conversation context for a specific session
     * 
     * @param int $sessionId Conversation session ID
     * @param int $messageLimit Number of most recent messages to consider
     * @return array Conversation context data
     */
    public function getConversationContext($sessionId, $messageLimit = 5) {
        try {
            // Get the most recent messages
            $stmt = $this->db->prepare("
                SELECT message_type, message_content, intent_type, entities, context_data
                FROM conversation_messages
                WHERE session_id = :sessionId
                ORDER BY timestamp DESC
                LIMIT :messageLimit
            ");
            
            $stmt->bindParam(':sessionId', $sessionId, PDO::PARAM_INT);
            $stmt->bindParam(':messageLimit', $messageLimit, PDO::PARAM_INT);
            
            $stmt->execute();
            $messages = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Process messages to build context
            $context = [
                'recent_intents' => [],
                'recent_entities' => [],
                'last_bot_response' => '',
                'extracted_context' => []
            ];
            
            // Process in reverse to get chronological order
            $messages = array_reverse($messages);
            
            foreach ($messages as $message) {
                // Track intents
                if (!empty($message['intent_type'])) {
                    $context['recent_intents'][] = $message['intent_type'];
                }
                
                // Track entities
                if (!empty($message['entities'])) {
                    $entities = json_decode($message['entities'], true);
                    if (is_array($entities)) {
                        foreach ($entities as $entity) {
                            if (!in_array($entity, $context['recent_entities'])) {
                                $context['recent_entities'][] = $entity;
                            }
                        }
                    }
                }
                
                // Track the most recent bot response
                if ($message['message_type'] === 'bot') {
                    $context['last_bot_response'] = $message['message_content'];
                }
                
                // Merge any existing context data
                if (!empty($message['context_data'])) {
                    $contextData = json_decode($message['context_data'], true);
                    if (is_array($contextData)) {
                        $context['extracted_context'] = array_merge($context['extracted_context'], $contextData);
                    }
                }
            }
            
            return $context;
        } catch (\PDOException $e) {
            error_log("Error retrieving conversation context: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Generate analytics for conversation data
     * 
     * @param int $userId Optional user ID to filter by
     * @param string $startDate Optional start date (YYYY-MM-DD)
     * @param string $endDate Optional end date (YYYY-MM-DD)
     * @return array Analytics data
     */
    public function generateConversationAnalytics($userId = null, $startDate = null, $endDate = null) {
        try {
            // Base query parameters
            $params = [];
            $userFilter = '';
            $dateFilter = '';
            
            // Add user filter if provided
            if ($userId !== null) {
                $userFilter = "AND cs.user_id = :userId";
                $params[':userId'] = $userId;
            }
            
            // Add date filters if provided
            if ($startDate !== null) {
                $dateFilter .= "AND cs.start_time >= :startDate";
                $params[':startDate'] = $startDate . ' 00:00:00';
            }
            
            if ($endDate !== null) {
                $dateFilter .= "AND cs.start_time <= :endDate";
                $params[':endDate'] = $endDate . ' 23:59:59';
            }
            
            // Query for session statistics
            $sessionQuery = "
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(TIMESTAMPDIFF(MINUTE, cs.start_time, COALESCE(cs.end_time, cs.last_activity))) as avg_session_duration,
                    SUM(CASE WHEN cs.status = 'active' THEN 1 ELSE 0 END) as active_sessions,
                    SUM(CASE WHEN cs.status = 'closed' THEN 1 ELSE 0 END) as closed_sessions
                FROM conversation_sessions cs
                WHERE 1=1 {$userFilter} {$dateFilter}
            ";
            
            $stmtSession = $this->db->prepare($sessionQuery);
            foreach ($params as $key => $value) {
                $stmtSession->bindValue($key, $value);
            }
            
            $stmtSession->execute();
            $sessionStats = $stmtSession->fetch(PDO::FETCH_ASSOC);
            
            // Query for message statistics
            $messageQuery = "
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN cm.message_type = 'user' THEN 1 ELSE 0 END) as user_messages,
                    SUM(CASE WHEN cm.message_type = 'bot' THEN 1 ELSE 0 END) as bot_messages,
                    AVG(cm.sentiment_score) as avg_sentiment_score,
                    AVG(cm.feedback_rating) as avg_feedback_rating
                FROM conversation_messages cm
                JOIN conversation_sessions cs ON cm.session_id = cs.id
                WHERE 1=1 {$userFilter} {$dateFilter}
            ";
            
            $stmtMessage = $this->db->prepare($messageQuery);
            foreach ($params as $key => $value) {
                $stmtMessage->bindValue($key, $value);
            }
            
            $stmtMessage->execute();
            $messageStats = $stmtMessage->fetch(PDO::FETCH_ASSOC);
            
            // Query for top intents
            $intentQuery = "
                SELECT 
                    cm.intent_type,
                    COUNT(*) as count
                FROM conversation_messages cm
                JOIN conversation_sessions cs ON cm.session_id = cs.id
                WHERE cm.intent_type IS NOT NULL {$userFilter} {$dateFilter}
                GROUP BY cm.intent_type
                ORDER BY count DESC
                LIMIT 10
            ";
            
            $stmtIntent = $this->db->prepare($intentQuery);
            foreach ($params as $key => $value) {
                $stmtIntent->bindValue($key, $value);
            }
            
            $stmtIntent->execute();
            $topIntents = $stmtIntent->fetchAll(PDO::FETCH_ASSOC);
            
            // Combine all statistics
            return [
                'session_stats' => $sessionStats,
                'message_stats' => $messageStats,
                'top_intents' => $topIntents
            ];
        } catch (\PDOException $e) {
            error_log("Error generating conversation analytics: " . $e->getMessage());
            return [
                'session_stats' => [],
                'message_stats' => [],
                'top_intents' => []
            ];
        }
    }

    /**
     * Extract frequently asked financial topics from conversations
     * 
     * @param int $limit Number of topics to return
     * @param int $daysBack Number of days to look back
     * @return array Top financial topics with frequency
     */
    public function getTopFinancialTopics($limit = 10, $daysBack = 30) {
        try {
            // Create a date for filtering
            $startDate = date('Y-m-d H:i:s', strtotime("-{$daysBack} days"));
            
            $query = "
                SELECT 
                    cm.intent_type as topic,
                    COUNT(*) as frequency
                FROM conversation_messages cm
                JOIN conversation_sessions cs ON cm.session_id = cs.id
                WHERE 
                    cm.intent_type LIKE '%investment%' OR
                    cm.intent_type LIKE '%loan%' OR
                    cm.intent_type LIKE '%budget%' OR
                    cm.intent_type LIKE '%savings%' OR
                    cm.intent_type LIKE '%stock%' OR
                    cm.intent_type LIKE '%insurance%' OR
                    cm.intent_type LIKE '%retirement%' OR
                    cm.intent_type LIKE '%tax%' OR
                    cm.intent_type LIKE '%crypto%' OR
                    cm.intent_type LIKE '%forex%'
                    AND cs.start_time >= :startDate
                GROUP BY cm.intent_type
                ORDER BY frequency DESC
                LIMIT :limit
            ";
            
            $stmt = $this->db->prepare($query);
            $stmt->bindParam(':startDate', $startDate, PDO::PARAM_STR);
            $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
            
            $stmt->execute();
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
        } catch (\PDOException $e) {
            error_log("Error retrieving top financial topics: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Get conversation data for training AI models
     * 
     * @param int $limit Maximum number of conversations to return
     * @param float $minRating Minimum feedback rating threshold
     * @return array Conversation data for AI training
     */
    public function getConversationsForAITraining($limit = 1000, $minRating = 4.0) {
        try {
            // Get high-quality conversations for training
            $query = "
                SELECT 
                    cm_user.message_content as user_message,
                    cm_bot.message_content as bot_response,
                    cm_user.intent_type,
                    cm_user.entities,
                    cm_bot.feedback_rating
                FROM conversation_messages cm_user
                JOIN conversation_messages cm_bot ON cm_user.id = cm_bot.parent_message_id
                WHERE 
                    cm_user.message_type = 'user' AND
                    cm_bot.message_type = 'bot' AND
                    cm_bot.feedback_rating >= :minRating
                ORDER BY cm_bot.feedback_rating DESC, RAND()
                LIMIT :limit
            ";
            
            $stmt = $this->db->prepare($query);
            $stmt->bindParam(':minRating', $minRating, PDO::PARAM_STR);
            $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
            
            $stmt->execute();
            $trainingData = $stmt->fetchAll(PDO::FETCH_ASSOC);
            
            // Decrypt user messages and format data for training
            $formattedData = [];
            foreach ($trainingData as $item) {
                $userMessage = $this->encryptionService->decrypt($item['user_message']);
                $botResponse = $item['bot_response'];
                $intentType = $item['intent_type'];
                $entities = !empty($item['entities']) ? json_decode($item['entities'], true) : [];
                
                $formattedData[] = [
                    'user_input' => $userMessage,
                    'bot_response' => $botResponse,
                    'intent' => $intentType,
                    'entities' => $entities,
                    'rating' => $item['feedback_rating']
                ];
            }
            
            return $formattedData;
        } catch (\PDOException $e) {
            error_log("Error retrieving conversations for AI training: " . $e->getMessage());
            return [];
        }
    }

    /**
     * Get user satisfaction trends over time
     * 
     * @param int $userId Optional user ID to filter by
     * @param int $timeframeMonths Number of months to look back
     * @return array Monthly sentiment and feedback trends
     */
    public function getUserSatisfactionTrends($userId = null, $timeframeMonths = 6) {
        try {
            // Create a date for filtering
            $startDate = date('Y-m-d', strtotime("-{$timeframeMonths} months"));
            
            // Base query parameters
            $params = [':startDate' => $startDate];
            $userFilter = '';
            
            // Add user filter if provided
            if ($userId !== null) {
                $userFilter = "AND cs.user_id = :userId";
                $params[':userId'] = $userId;
            }
            
            $query = "
                SELECT 
                    DATE_FORMAT(cs.start_time, '%Y-%m') as month,
                    AVG(cm.sentiment_score) as avg_sentiment,
                    AVG(cm.feedback_rating) as avg_feedback
                FROM conversation_messages cm
                JOIN conversation_sessions cs ON cm.session_id = cs.id
                WHERE 
                    cs.start_time >= :startDate
                    {$userFilter}
                GROUP BY DATE_FORMAT(cs.start_time, '%Y-%m')
                ORDER BY month ASC
            ";
            
            $stmt = $this->db->prepare($query);
            foreach ($params as $key => $value) {
                $stmt->bindValue($key, $value);
            }
            
            $stmt->execute();
            return $stmt->fetchAll(PDO::FETCH_ASSOC);
        } catch (\PDOException $e) {
            error_log("Error retrieving user satisfaction trends: " . $e->getMessage());
            return [];
        }
    }
}
?>
