import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages the conversation context for the PesaGuru chatbot.
    
    This class handles storage and retrieval of conversation history, 
    maintains the state of ongoing conversations, and provides
    context-aware processing for financial advisory interactions.
    """
    
    def __init__(self, max_context_length: int = 10, context_expiry_minutes: int = 30):
        """
        Initialize the context manager.
        
        Args:
            max_context_length: Maximum number of conversation turns to retain in context
            context_expiry_minutes: Time in minutes after which context expires if inactive
        """
        self.contexts = {}  # Dictionary to store all active conversation contexts
        self.max_context_length = max_context_length
        self.context_expiry_minutes = context_expiry_minutes
        logger.info("Context Manager initialized with max_length=%d, expiry=%d minutes", 
                   max_context_length, context_expiry_minutes)
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new conversation session.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        # Initialize empty context with metadata
        self.contexts[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_updated': datetime.now(),
            'messages': [],
            'current_intent': None,
            'entities': {},
            'user_profile': {
                'risk_tolerance': None,
                'investment_horizon': None,
                'financial_goals': [],
                'preferred_language': None
            },
            'active_topics': [],
            'sentiment_history': []
        }
        
        logger.info(f"Created new session {session_id} for user {user_id}")
        return session_id
    
    def add_message(self, session_id: str, message: str, is_user_message: bool, 
                   intent: Optional[str] = None, entities: Optional[Dict] = None,
                   sentiment: Optional[str] = None) -> bool:
        """
        Add a new message to the conversation context.
        
        Args:
            session_id: Session identifier
            message: Message text
            is_user_message: True if message is from user, False if from chatbot
            intent: Classified intent for the message (if available)
            entities: Extracted entities from the message (if available)
            sentiment: Detected sentiment of the message (if available)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to add message to non-existent session {session_id}")
            return False
        
        # Update session timestamp
        self.contexts[session_id]['last_updated'] = datetime.now()
        
        # Create message object
        message_obj = {
            'text': message,
            'timestamp': datetime.now(),
            'is_user_message': is_user_message,
            'intent': intent,
            'entities': entities or {},
            'sentiment': sentiment
        }
        
        # Add message to context
        self.contexts[session_id]['messages'].append(message_obj)
        
        # Update current intent if this is a user message with intent
        if is_user_message and intent:
            self.contexts[session_id]['current_intent'] = intent
            
            # Add to active topics if not already present
            if intent not in self.contexts[session_id]['active_topics']:
                self.contexts[session_id]['active_topics'].append(intent)
        
        # Update entities
        if entities:
            for entity_type, entity_values in entities.items():
                # Merge with existing entities of the same type
                existing = self.contexts[session_id]['entities'].get(entity_type, [])
                # Add new unique entities
                if isinstance(entity_values, list):
                    for value in entity_values:
                        if value not in existing:
                            existing.append(value)
                else:
                    if entity_values not in existing:
                        existing.append(entity_values)
                
                self.contexts[session_id]['entities'][entity_type] = existing
        
        # Add sentiment to history if available
        if sentiment:
            self.contexts[session_id]['sentiment_history'].append(sentiment)
        
        # Trim context if it exceeds maximum length
        if len(self.contexts[session_id]['messages']) > self.max_context_length:
            self.contexts[session_id]['messages'] = self.contexts[session_id]['messages'][-self.max_context_length:]
            
        logger.debug(f"Added message to session {session_id}: {message[:50]}...")
        return True
    
    def get_conversation_history(self, session_id: str, max_turns: Optional[int] = None) -> List[Dict]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            max_turns: Optional maximum number of turns to retrieve (newest first)
            
        Returns:
            List of message objects, empty list if session doesn't exist
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to get history for non-existent session {session_id}")
            return []
        
        messages = self.contexts[session_id]['messages']
        
        if max_turns is not None:
            return messages[-max_turns:]
        
        return messages
    
    def get_active_intent(self, session_id: str) -> Optional[str]:
        """
        Get the current active intent for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current intent string or None
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to get intent for non-existent session {session_id}")
            return None
        
        return self.contexts[session_id].get('current_intent')
    
    def get_entities(self, session_id: str, entity_type: Optional[str] = None) -> Dict:
        """
        Get entities from the conversation context.
        
        Args:
            session_id: Session identifier
            entity_type: Optional entity type to filter by
            
        Returns:
            Dictionary of entity_type -> values, or specific entity values if type provided
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to get entities for non-existent session {session_id}")
            return {}
        
        entities = self.contexts[session_id].get('entities', {})
        
        if entity_type:
            return {entity_type: entities.get(entity_type, [])}
        
        return entities
    
    def update_user_profile(self, session_id: str, profile_data: Dict) -> bool:
        """
        Update user profile information in the context.
        
        Args:
            session_id: Session identifier
            profile_data: Dictionary of profile attributes to update
            
        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to update profile for non-existent session {session_id}")
            return False
        
        for key, value in profile_data.items():
            self.contexts[session_id]['user_profile'][key] = value
        
        logger.info(f"Updated user profile for session {session_id}")
        return True
    
    def get_user_profile(self, session_id: str) -> Dict:
        """
        Get user profile information from the context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            User profile dictionary or empty dict if session doesn't exist
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to get profile for non-existent session {session_id}")
            return {}
        
        return dict(self.contexts[session_id]['user_profile'])
    
    def detect_topic_change(self, session_id: str, current_intent: str) -> bool:
        """
        Detect if there's been a topic change in the conversation.
        
        Args:
            session_id: Session identifier
            current_intent: The current detected intent
            
        Returns:
            True if the intent represents a topic change, False otherwise
        """
        if session_id not in self.contexts:
            return False
        
        previous_intent = self.contexts[session_id].get('current_intent')
        
        # If there's no previous intent, or the intent is the same, not a topic change
        if not previous_intent or previous_intent == current_intent:
            return False
        
        # Check if we're switching between related intents
        # For example, investment.stocks and investment.bonds are related
        previous_intent_base = previous_intent.split('.')[0] if '.' in previous_intent else previous_intent
        current_intent_base = current_intent.split('.')[0] if '.' in current_intent else current_intent
        
        return previous_intent_base != current_intent_base
    
    def get_relevant_context(self, session_id: str, intent: Optional[str] = None, 
                           entities: Optional[Dict] = None) -> Dict:
        """
        Get context relevant to a specific intent or entities.
        This is useful for generating context-aware responses.
        
        Args:
            session_id: Session identifier
            intent: Optional intent to filter context by
            entities: Optional entities to include in context
            
        Returns:
            Dictionary containing relevant context elements
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to get relevant context for non-existent session {session_id}")
            return {}
        
        full_context = self.contexts[session_id]
        relevant = {
            'user_profile': full_context['user_profile'],
            'current_intent': full_context['current_intent'],
            'recent_messages': full_context['messages'][-3:],  # Last 3 messages
        }
        
        # If specific intent requested, filter messages by that intent
        if intent:
            relevant['intent_related_messages'] = [
                msg for msg in full_context['messages'] 
                if msg.get('intent') == intent
            ]
        
        # If entities specified, include relevant entity information
        if entities:
            relevant_entities = {}
            for entity_type in entities:
                if entity_type in full_context['entities']:
                    relevant_entities[entity_type] = full_context['entities'][entity_type]
            relevant['entities'] = relevant_entities
        else:
            relevant['entities'] = full_context['entities']
        
        return relevant
    
    def extract_financial_context(self, session_id: str) -> Dict:
        """
        Extract key financial information from conversation context
        that might be relevant for generating financial advice.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary of financial information extracted from conversation
        """
        if session_id not in self.contexts:
            return {}
        
        financial_context = {
            'mentioned_amounts': [],
            'investment_types': [],
            'loan_types': [],
            'financial_goals': self.contexts[session_id]['user_profile'].get('financial_goals', []),
            'risk_tolerance': self.contexts[session_id]['user_profile'].get('risk_tolerance'),
            'investment_horizon': self.contexts[session_id]['user_profile'].get('investment_horizon'),
        }
        
        # Extract financial entities
        entities = self.contexts[session_id].get('entities', {})
        
        # Get monetary amounts
        if 'money' in entities:
            financial_context['mentioned_amounts'] = entities['money']
            
        # Get investment types
        if 'investment_type' in entities:
            financial_context['investment_types'] = entities['investment_type']
            
        # Get loan types
        if 'loan_type' in entities:
            financial_context['loan_types'] = entities['loan_type']
        
        return financial_context
    
    def clear_context(self, session_id: str) -> bool:
        """
        Clear all context for a session, maintaining only the session metadata.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to clear non-existent session {session_id}")
            return False
        
        # Preserve user ID and timestamps
        user_id = self.contexts[session_id]['user_id']
        created_at = self.contexts[session_id]['created_at']
        
        # Reset context to initial state
        self.contexts[session_id] = {
            'user_id': user_id,
            'created_at': created_at,
            'last_updated': datetime.now(),
            'messages': [],
            'current_intent': None,
            'entities': {},
            'user_profile': {
                'risk_tolerance': None,
                'investment_horizon': None, 
                'financial_goals': [],
                'preferred_language': None
            },
            'active_topics': [],
            'sentiment_history': []
        }
        
        logger.info(f"Cleared context for session {session_id}")
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Completely delete a session and all its context.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False if session didn't exist
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to delete non-existent session {session_id}")
            return False
        
        del self.contexts[session_id]
        logger.info(f"Deleted session {session_id}")
        return True
    
    def cleanup_expired_contexts(self) -> int:
        """
        Remove expired conversation contexts to free up memory.
        
        Returns:
            Number of expired contexts removed
        """
        current_time = datetime.now()
        expired_session_ids = []
        
        for session_id, context in self.contexts.items():
            last_updated = context['last_updated']
            expiry_time = last_updated + timedelta(minutes=self.context_expiry_minutes)
            
            if current_time > expiry_time:
                expired_session_ids.append(session_id)
        
        # Delete expired sessions
        for session_id in expired_session_ids:
            del self.contexts[session_id]
            
        if expired_session_ids:
            logger.info(f"Cleaned up {len(expired_session_ids)} expired contexts")
            
        return len(expired_session_ids)
    
    def save_to_database(self, session_id: str, db_connector) -> bool:
        """
        Save the current context to a persistent database.
        
        Args:
            session_id: Session identifier
            db_connector: Database connector object with save method
            
        Returns:
            True if save was successful, False otherwise
        """
        if session_id not in self.contexts:
            logger.warning(f"Attempted to save non-existent session {session_id}")
            return False
        
        try:
            # Convert datetime objects to strings for database storage
            context_copy = self._prepare_context_for_storage(session_id)
            db_connector.save_conversation_context(session_id, context_copy)
            logger.info(f"Saved context for session {session_id} to database")
            return True
        except Exception as e:
            logger.error(f"Failed to save context to database: {str(e)}")
            return False
    
    def load_from_database(self, session_id: str, db_connector) -> bool:
        """
        Load a conversation context from the database.
        
        Args:
            session_id: Session identifier
            db_connector: Database connector object with load method
            
        Returns:
            True if load was successful, False otherwise
        """
        try:
            context_data = db_connector.load_conversation_context(session_id)
            
            if not context_data:
                logger.warning(f"No context found in database for session {session_id}")
                return False
            
            # Convert string timestamps back to datetime objects
            context_data = self._prepare_loaded_context(context_data)
            self.contexts[session_id] = context_data
            
            logger.info(f"Loaded context for session {session_id} from database")
            return True
        except Exception as e:
            logger.error(f"Failed to load context from database: {str(e)}")
            return False
    
    def _prepare_context_for_storage(self, session_id: str) -> Dict:
        """
        Prepare context for database storage by converting datetime objects to strings.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Context dictionary with serializable values
        """
        context = dict(self.contexts[session_id])
        
        # Convert datetime objects to ISO format strings
        context['created_at'] = context['created_at'].isoformat()
        context['last_updated'] = context['last_updated'].isoformat()
        
        for message in context['messages']:
            if 'timestamp' in message:
                message['timestamp'] = message['timestamp'].isoformat()
        
        return context
    
    def _prepare_loaded_context(self, context_data: Dict) -> Dict:
        """
        Prepare loaded context by converting string timestamps to datetime objects.
        
        Args:
            context_data: Context data loaded from database
            
        Returns:
            Context dictionary with proper datetime objects
        """
        # Convert ISO format strings back to datetime objects
        context_data['created_at'] = datetime.fromisoformat(context_data['created_at'])
        context_data['last_updated'] = datetime.fromisoformat(context_data['last_updated'])
        
        for message in context_data['messages']:
            if 'timestamp' in message:
                message['timestamp'] = datetime.fromisoformat(message['timestamp'])
        
        return context_data
    
    def get_dominant_sentiment(self, session_id: str, last_n: int = 3) -> Optional[str]:
        """
        Get the dominant sentiment from recent conversation history.
        
        Args:
            session_id: Session identifier
            last_n: Number of recent messages to consider
            
        Returns:
            Dominant sentiment or None if unavailable
        """
        if session_id not in self.contexts:
            return None
        
        sentiment_history = self.contexts[session_id].get('sentiment_history', [])
        
        if not sentiment_history:
            return None
        
        # Get the most recent n sentiments
        recent_sentiments = sentiment_history[-last_n:]
        
        # Count sentiment occurrences
        sentiment_counts = {}
        for sentiment in recent_sentiments:
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Return the most common sentiment
        if sentiment_counts:
            return max(sentiment_counts, key=sentiment_counts.get)
        
        return None# Conversation context manager 
