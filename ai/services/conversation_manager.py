import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Import internal NLP components
from ..nlp.text_preprocessor import TextPreprocessor
from ..nlp.intent_classifier import IntentClassifier
from ..nlp.entity_extractor import EntityExtractor
from ..nlp.language_detector import LanguageDetector
from ..nlp.context_manager import ContextManager

# Import financial services
from .sentiment_analysis import SentimentAnalyzer
from .user_profiler import UserProfiler
from .recommendation_engine import RecommendationEngine
from .market_analysis import MarketAnalysis
from .risk_evaluation import RiskEvaluator
from .portfolio_ai import PortfolioOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Main class to manage conversations with PesaGuru users.
    
    This class orchestrates the conversation flow, processes user input,
    maintains context, and generates personalized financial responses.
    """
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the ConversationManager with user information and services.
        
        Args:
            user_id (str, optional): The unique identifier for the user.
        """
        self.user_id = user_id or str(uuid.uuid4())
        
        # Initialize NLP components
        self.text_preprocessor = TextPreprocessor()
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.language_detector = LanguageDetector()
        self.context_manager = ContextManager(user_id=self.user_id)
        
        # Initialize financial advisory services
        self.sentiment_analyzer = SentimentAnalyzer()
        self.user_profiler = UserProfiler(user_id=self.user_id)
        self.recommendation_engine = RecommendationEngine()
        self.market_analyzer = MarketAnalysis()
        self.risk_evaluator = RiskEvaluator()
        self.portfolio_optimizer = PortfolioOptimizer()
        
        # Conversation state tracking
        self.conversation_id = str(uuid.uuid4())
        self.session_start_time = datetime.now()
        self.message_count = 0
        self.current_context = {}
        self.active_flow = None
        
        # Fallback configuration
        self.max_fallback_attempts = 3
        self.fallback_count = 0
        
        logger.info(f"ConversationManager initialized for user {self.user_id}")
    
    def process_message(self, message: str, 
                      session_id: Optional[str] = None,
                      additional_context: Optional[Dict] = None) -> Dict:
        """
        Process a user message and generate a personalized financial response.
        
        Args:
            message (str): The message from the user.
            session_id (str, optional): The session identifier.
            additional_context (dict, optional): Additional context information.
            
        Returns:
            dict: The response from the chatbot with financial advice.
        """
        try:
            # Track message count
            self.message_count += 1
            
            # Detect language (English or Swahili)
            language = self.language_detector.detect_language(message)
            
            # Preprocess the message (tokenization, normalization)
            processed_text = self.text_preprocessor.preprocess(message, language=language)
            
            # Detect user sentiment to adjust response tone
            sentiment = self.sentiment_analyzer.analyze(processed_text, language=language)
            
            # Get user profile for personalized financial advice
            user_profile = self.user_profiler.get_profile()
            
            # Classify financial intent (investment, loans, budgeting, etc.)
            intent_data = self.intent_classifier.classify(processed_text, language=language)
            intent = intent_data['intent']
            confidence = intent_data['confidence']
            
            # Extract financial entities (amounts, financial products, timeframes)
            entities = self.entity_extractor.extract(processed_text, language=language)
            
            # Update conversation context for multi-turn financial discussions
            context = self.context_manager.update_context(
                intent=intent,
                entities=entities,
                message=message,
                sentiment=sentiment,
                additional_context=additional_context
            )
            
            # Generate response based on financial intent
            if confidence < 0.4:
                response = self._handle_low_confidence(processed_text, language)
            else:
                response = self._generate_response(intent, entities, context, user_profile, language)
            
            # Log conversation for analysis and improvement
            self._log_conversation(message, response, intent, entities, sentiment)
            
            # Reset fallback counter if we successfully generated a response
            if "fallback" not in intent:
                self.fallback_count = 0
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'text': "I'm sorry, but I encountered an error processing your financial request. Please try again later.",
                'intent': 'error',
                'confidence': 0.0,
                'conversation_id': self.conversation_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_response(self, intent: str, entities: Dict, 
                         context: Dict, user_profile: Dict,
                         language: str) -> Dict:
        """
        Generate a personalized financial response based on user intent and profile.
        
        Args:
            intent (str): The classified financial intent.
            entities (dict): Extracted financial entities from the message.
            context (dict): Current conversation context.
            user_profile (dict): User's financial profile for personalization.
            language (str): Detected language (en or sw).
            
        Returns:
            dict: The personalized financial response.
        """
        # Update current context
        self.current_context = context
        
        # Handle intents related to financial advisory services
        if intent.startswith('investment_'):
            return self._handle_investment_intent(intent, entities, context, user_profile, language)
        
        elif intent.startswith('loan_'):
            return self._handle_loan_intent(intent, entities, context, user_profile, language)
        
        elif intent.startswith('budget_'):
            return self._handle_budget_intent(intent, entities, context, user_profile, language)
        
        elif intent.startswith('market_'):
            return self._handle_market_intent(intent, entities, context, user_profile, language)
        
        elif intent.startswith('risk_'):
            return self._handle_risk_intent(intent, entities, context, user_profile, language)
        
        elif intent.startswith('goal_'):
            return self._handle_goal_intent(intent, entities, context, user_profile, language)
        
        elif intent == 'greeting':
            return self._handle_greeting(context, user_profile, language)
        
        elif intent == 'farewell':
            return self._handle_farewell(context, user_profile, language)
        
        elif intent == 'help':
            return self._handle_help(context, user_profile, language)
        
        elif intent == 'fallback':
            return self._handle_fallback(context, language)
        
        else:
            # Default response for unhandled intents
            return {
                'text': self._get_localized_response('default_response', language, intent=intent),
                'intent': intent,
                'confidence': 0.5,
                'conversation_id': self.conversation_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _handle_investment_intent(self, intent: str, entities: Dict, 
                                context: Dict, user_profile: Dict,
                                language: str) -> Dict:
        """
        Handle investment-related intents with personalized recommendations.
        
        Args:
            intent (str): The specific investment intent.
            entities (dict): Extracted investment entities from the message.
            context (dict): Current conversation context.
            user_profile (dict): User's investment profile and risk tolerance.
            language (str): Detected language (en or sw).
            
        Returns:
            dict: Investment advice response.
        """
        # Get recommendations based on the specific investment intent
        if intent == 'investment_advice':
            # Generate personalized investment recommendations based on user profile
            recommendations = self.recommendation_engine.get_investment_recommendations(
                user_profile=user_profile,
                entities=entities,
                context=context
            )
            
            response_text = self._get_localized_response(
                'investment_advice',
                language,
                recommendations=recommendations
            )
            
        elif intent == 'investment_performance':
            if 'investment_type' in entities:
                # Get performance data for specific investment (e.g., NSE stocks)
                investment_type = entities['investment_type']
                performance_data = self.market_analyzer.get_investment_performance(investment_type)
                
                response_text = self._get_localized_response(
                    'investment_performance',
                    language,
                    investment_type=investment_type,
                    performance_data=performance_data
                )
            else:
                # Ask for the investment type
                response_text = self._get_localized_response('ask_investment_type', language)
        
        elif intent == 'investment_comparison':
            if 'investment_types' in entities and len(entities['investment_types']) >= 2:
                # Compare different investment options (e.g., stocks vs. treasury bonds)
                comparison = self.market_analyzer.compare_investments(entities['investment_types'])
                
                response_text = self._get_localized_response(
                    'investment_comparison',
                    language,
                    comparison=comparison
                )
            else:
                # Ask for investment types to compare
                response_text = self._get_localized_response('ask_investments_to_compare', language)
        
        elif intent == 'investment_explanation':
            if 'investment_term' in entities:
                term = entities['investment_term']
                explanation = self._get_financial_term_explanation(term, language)
                
                response_text = explanation
            else:
                # Ask for the term to explain
                response_text = self._get_localized_response('ask_investment_term', language)
        
        else:
            # Default investment response
            response_text = self._get_localized_response('default_investment', language)
        
        return {
            'text': response_text,
            'intent': intent,
            'entities': entities,
            'conversation_id': self.conversation_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def _handle_loan_intent(self, intent: str, entities: Dict, 
                          context: Dict, user_profile: Dict,
                          language: str) -> Dict:
        """
        Handle loan-related intents with personalized recommendations.
        
        Args:
            intent (str): The specific loan intent.
            entities (dict): Extracted loan entities (amount, term, etc).
            context (dict): Current conversation context.
            user_profile (dict): User's financial profile for eligibility assessment.
            language (str): Detected language (en or sw).
            
        Returns:
            dict: Loan advice response.
        """
        # Process different loan intents (eligibility, comparison, repayment)
        if intent == 'loan_eligibility':
            # Check if we have necessary entities
            if 'loan_amount' in entities and 'loan_type' in entities:
                # Assess loan eligibility based on user profile
                eligibility = self.recommendation_engine.check_loan_eligibility(
                    loan_amount=entities['loan_amount'],
                    loan_type=entities['loan_type'],
                    user_profile=user_profile
                )
                
                response_text = self._get_localized_response(
                    'loan_eligibility',
                    language,
                    eligibility=eligibility
                )
            else:
                # Ask for more information
                missing_entities = []
                if 'loan_amount' not in entities:
                    missing_entities.append('loan_amount')
                if 'loan_type' not in entities:
                    missing_entities.append('loan_type')
                
                response_text = self._get_localized_response(
                    'ask_loan_details',
                    language,
                    missing_entities=missing_entities
                )
        
        elif intent == 'loan_comparison':
            if 'loan_types' in entities and len(entities['loan_types']) >= 2:
                # Compare different loan options (e.g., M-Shwari vs. KCB-MPesa)
                comparison = self.recommendation_engine.compare_loans(entities['loan_types'])
                
                response_text = self._get_localized_response(
                    'loan_comparison',
                    language,
                    comparison=comparison
                )
            else:
                # Ask for loan types to compare
                response_text = self._get_localized_response('ask_loans_to_compare', language)
        
        elif intent == 'loan_repayment':
            if 'loan_amount' in entities and 'interest_rate' in entities and 'loan_term' in entities:
                # Calculate detailed loan repayment plan
                repayment_plan = self.recommendation_engine.calculate_loan_repayment(
                    loan_amount=entities['loan_amount'],
                    interest_rate=entities['interest_rate'],
                    loan_term=entities['loan_term']
                )
                
                response_text = self._get_localized_response(
                    'loan_repayment',
                    language,
                    repayment_plan=repayment_plan
                )
            else:
                # Ask for necessary details
                missing_entities = []
                if 'loan_amount' not in entities:
                    missing_entities.append('loan_amount')
                if 'interest_rate' not in entities:
                    missing_entities.append('interest_rate')
                if 'loan_term' not in entities:
                    missing_entities.append('loan_term')
                
                response_text = self._get_localized_response(
                    'ask_loan_repayment_details',
                    language,
                    missing_entities=missing_entities
                )
        
        else:
            # Default loan response
            response_text = self._get_localized_response('default_loan', language)
        
        return {
            'text': response_text,
            'intent': intent,
            'entities': entities,
            'conversation_id': self.conversation_id,
            'timestamp': datetime.now().isoformat()
        }
    
    # Additional intent handlers would follow similar patterns for:
    # - _handle_budget_intent
    # - _handle_market_intent
    # - _handle_risk_intent
    # - _handle_goal_intent
    # - _handle_greeting, _handle_farewell, _handle_help, _handle_fallback
    
    def _handle_low_confidence(self, text: str, language: str) -> Dict:
        """
        Handle cases where intent confidence is low.
        
        Args:
            text (str): Processed text from the user.
            language (str): Detected language (en or sw).
            
        Returns:
            dict: Clarification response.
        """
        # Try to clarify what the user meant
        clarification_text = self._get_localized_response('clarification', language)
        
        return {
            'text': clarification_text,
            'intent': 'clarification',
            'conversation_id': self.conversation_id,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_localized_response(self, response_key: str, language: str, **kwargs) -> str:
        """
        Get a localized response template and format it with the provided values.
        
        Args:
            response_key (str): The key for the response template.
            language (str): The language code (en or sw).
            **kwargs: Values to format the template with.
            
        Returns:
            str: The formatted response.
        """
        # Dictionary of response templates in English and Swahili
        responses = {
            'en': {
                'default_response': "I understand you're asking about {intent}. How can I help you with that?",
                'clarification': "I'm not quite sure what financial information you're looking for. Could you provide more details?",
                'fallback': "I'm sorry, I didn't understand that. Could you rephrase your financial question?",
                'fallback_human_support': "I'm having trouble understanding your request. Would you like to speak with a human financial advisor?",
                
                'new_greeting': "Hello! I'm PesaGuru, your personal financial advisor. How can I help you with your finances today?",
                'returning_greeting': "Welcome back, {user_name}! How can I assist you with your finances today?",
                'farewell': "Thank you for chatting with PesaGuru! Have a great day, {user_name}.",
                'help': "I can help you with investment advice, loan options, budgeting, market updates, risk assessment, and financial goal planning. What would you like to know about?",
                
                # Investment responses
                'investment_advice': "Based on your profile, I recommend considering these investments: {recommendations}",
                'investment_performance': "Here's the performance of {investment_type}: {performance_data}",
                # Additional response templates would continue...
            },
            'sw': {
                'default_response': "Ninaelewa unaongea kuhusu {intent}. Nikufanyie nini?",
                'clarification': "Sijaeleweka vizuri unachouliza kuhusu fedha zako. Unaweza kutoa maelezo zaidi?",
                'fallback': "Samahani, sijasikia vizuri. Unaweza kurudia swali lako la kifedha?",
                'fallback_human_support': "Nina shida kuelewa ombi lako. Ungependa kuzungumza na mshauri wa kifedha?",
                
                'new_greeting': "Habari! Mimi ni PesaGuru, mshauri wako wa kifedha. Nikufanyie nini leo?",
                'returning_greeting': "Karibu tena, {user_name}! Nikufanyie nini kuhusu fedha zako leo?",
                # Additional Swahili response templates would continue...
            }
        }
        
        # Get the response template for the specified language
        if language not in responses:
            language = 'en'  # Fallback to English
        
        lang_responses = responses[language]
        
        # Get the response template
        template = lang_responses.get(response_key, lang_responses['default_response'])
        
        # Format the template with the provided values
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing key in response template: {e}")
            return template
    
    def _get_financial_term_explanation(self, term: str, language: str) -> str:
        """
        Get an explanation for a financial term in the specified language.
        
        Args:
            term (str): The financial term to explain.
            language (str): The language code (en or sw).
            
        Returns:
            str: The explanation for the term.
        """
        # This would typically fetch from a financial terms dictionary
        financial_terms = {
            'en': {
                'stock': "A stock (also known as equity) is a security that represents the ownership of a fraction of a corporation.",
                'bond': "A bond is a fixed income instrument that represents a loan made by an investor to a borrower (typically corporate or governmental).",
                'mutual fund': "A mutual fund is a type of financial vehicle made up of a pool of money collected from many investors to invest in securities.",
                # Additional financial terms would continue...
            },
            'sw': {
                'stock': "Hisa (pia inajulikana kama usawa) ni dhamana inayowakilisha umiliki wa sehemu ya shirika.",
                'bond': "Hatifungani ni chombo cha mapato maalum kinachowakilisha mkopo uliofanywa na mwekezaji kwa mkopaji (kawaida wa kampuni au serikali).",
                # Additional Swahili financial terms would continue...
            }
        }
        
        # Get the financial terms for the specified language
        if language not in financial_terms:
            language = 'en'  # Fallback to English
        
        lang_terms = financial_terms[language]
        
        # Look up the term (case-insensitive)
        term_lower = term.lower()
        explanation = lang_terms.get(term_lower)
        
        if explanation:
            return explanation
        else:
            # If term not found, return a generic response
            if language == 'en':
                return f"I don't have an explanation for '{term}' in my database. Would you like me to help you with something else?"
            else:  # Swahili
                return f"Sina ufafanuzi wa '{term}' katika hifadhidata yangu. Ungependa nikufanyie jambo lingine?"
    
    def _log_conversation(self, user_message: str, response: Dict, 
                        intent: str, entities: Dict, sentiment: Dict) -> None:
        """
        Log the conversation for analysis and improvement.
        
        Args:
            user_message (str): The message from the user.
            response (dict): The response from the chatbot.
            intent (str): The classified intent.
            entities (dict): Extracted entities from the message.
            sentiment (dict): Sentiment analysis results.
        """
        # Log conversation data for analysis
        log_entry = {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'response': response,
            'intent': intent,
            'entities': entities,
            'sentiment': sentiment
        }
        
        logger.info(f"Conversation log: {json.dumps(log_entry)}")
    
    def end_conversation(self) -> Dict:
        """
        End the current conversation and provide a summary.
        
        Returns:
            dict: A summary of the conversation.
        """
        # Calculate conversation duration
        duration = datetime.now() - self.session_start_time
        
        # Create conversation summary
        summary = {
            'conversation_id': self.conversation_id,
            'user_id': self.user_id,
            'start_time': self.session_start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': str(duration),
            'message_count': self.message_count
        }
        
        logger.info(f"Conversation ended: {json.dumps(summary)}")
        
        return summary
