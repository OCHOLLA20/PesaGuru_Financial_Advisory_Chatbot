import logging
import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# NLP and model imports
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Internal service imports
from ..models.financial_bert import FinancialBERT
from ..nlp.text_preprocessor import preprocess_text
from ..nlp.language_detector import detect_language
from ..nlp.swahili_processor import process_swahili
from ..nlp.context_manager import ConversationContext
from ..services.sentiment_analysis import analyze_sentiment
from ..services.risk_evaluation import evaluate_risk_profile
from ..services.portfolio_ai import get_portfolio_recommendations
from ..services.market_analysis import get_market_insights
from ..services.market_data_api import get_market_data
from ..services.recommendation_engine import generate_recommendations
from ..services.user_profiler import get_user_profile, update_user_profile

# API integrations
from ..api_integration.nse_api import get_nse_data
from ..api_integration.cbk_api import get_cbk_data
from ..api_integration.mpesa_api import get_mpesa_data
from ..api_integration.crypto_api import get_crypto_data

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    with open(os.path.join(os.path.dirname(__file__), '../../server/config/chatbot_config.php'), 'r') as f:
        CHATBOT_CONFIG = json.load(f)
except Exception as e:
    logger.error(f"Failed to load chatbot configuration: {e}")
    CHATBOT_CONFIG = {
        "model_confidence_threshold": 0.7,
        "default_language": "en",
        "enable_sentiment_analysis": True,
        "enable_multilingual": True,
        "context_memory_turns": 5
    }

# Load financial terms dictionary
try:
    with open(os.path.join(os.path.dirname(__file__), '../data/financial_terms_dictionary.json'), 'r') as f:
        FINANCIAL_TERMS = json.load(f)
except Exception as e:
    logger.error(f"Failed to load financial terms dictionary: {e}")
    FINANCIAL_TERMS = {}


class ChatbotService:
    """
    Main chatbot service class that handles all user interactions, intent recognition,
    and personalized financial advisory responses.
    """

    def __init__(self):
        """Initialize chatbot models, NLP components, and conversation context management."""
        logger.info("Initializing PesaGuru Chatbot Service")
        
        # Load intent classification model
        self.intent_model = None
        self.intent_tokenizer = None
        self.load_intent_model()
        
        # Load entity extraction model
        self.entity_extractor = None
        self.load_entity_extractor()
        
        # Initialize conversation context manager
        self.context_manager = ConversationContext(
            max_turns=CHATBOT_CONFIG.get("context_memory_turns", 5)
        )
        
        # Initialize language detection
        self.language_detector = detect_language
        
        # Load financial terms dictionary
        self.financial_terms = FINANCIAL_TERMS
        
        logger.info("PesaGuru Chatbot Service initialized successfully")
    
    def load_intent_model(self):
        """Load the intent classification model for financial queries."""
        try:
            logger.info("Loading intent classification model")
            # In production, load the fine-tuned model for financial intents
            self.intent_tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
            self.intent_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased")
            logger.info("Intent classification model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load intent model: {e}")
            # Fallback to rule-based if model fails to load
            self.intent_model = None
            self.intent_tokenizer = None
    
    def load_entity_extractor(self):
        """Load entity extraction model for identifying financial entities in text."""
        try:
            logger.info("Loading entity extraction model")
            # In production, this would be a NER model fine-tuned for financial entities
            from transformers import pipeline
            self.entity_extractor = pipeline("ner")
            logger.info("Entity extraction model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load entity extraction model: {e}")
            self.entity_extractor = None
    
    def process_message(self, message: str, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Process an incoming user message and generate a personalized financial response.
        
        Args:
            message: The user's message text
            user_id: Unique identifier for the user
            session_id: Unique identifier for the current conversation session
            
        Returns:
            A dictionary containing the chatbot's response and metadata
        """
        logger.info(f"Processing message from user {user_id}: {message}")
        
        # 1. Preprocess the text
        preprocessed_text = preprocess_text(message)
        
        # 2. Detect language (English or Swahili)
        detected_language = self.language_detector(preprocessed_text)
        
        # 3. Process language-specific considerations (e.g., Sheng/slang for Swahili)
        if detected_language == "sw" and CHATBOT_CONFIG.get("enable_multilingual", True):
            processed_text = process_swahili(preprocessed_text)
        else:
            processed_text = preprocessed_text
        
        # 4. Update conversation context
        self.context_manager.add_user_message(processed_text, session_id)
        
        # 5. Classify user intent (investment advice, loan info, etc.)
        intent, confidence = self._classify_intent(processed_text)
        
        # 6. Extract relevant financial entities (stock names, amounts, etc.)
        entities = self._extract_entities(processed_text)
        
        # 7. Analyze sentiment to provide empathetic responses
        sentiment = None
        if CHATBOT_CONFIG.get("enable_sentiment_analysis", True):
            sentiment = analyze_sentiment(processed_text)
        
        # 8. Generate personalized financial response
        response_data = self._generate_response(
            intent=intent,
            entities=entities,
            user_id=user_id,
            session_id=session_id,
            sentiment=sentiment,
            language=detected_language,
            confidence=confidence
        )
        
        # 9. Update conversation context with the response
        self.context_manager.add_bot_message(response_data["text"], session_id)
        
        # 10. Log interaction for continuous improvement
        self._log_interaction(
            user_id=user_id,
            session_id=session_id,
            message=message,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            response=response_data
        )
        
        return response_data
    
    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """
        Classify the user's financial intent from their message.
        
        Args:
            text: Preprocessed user message
            
        Returns:
            Tuple of (intent_name, confidence_score)
        """
        # Default fallback intent
        default_intent = "general_inquiry"
        default_confidence = 0.0
        
        # Use ML model if available
        if self.intent_model is None or self.intent_tokenizer is None:
            return self._rule_based_intent_classification(text)
        
        try:
            # Use transformer model for intent classification
            inputs = self.intent_tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            outputs = self.intent_model(**inputs)
            
            # Get predicted class and confidence
            predicted_class = outputs.logits.argmax().item()
            confidence = outputs.logits.softmax(dim=1).max().item()
            
            # Map class index to financial intent names
            intent_classes = [
                "investment_advice", "budgeting_help", "loan_information",
                "market_data", "risk_assessment", "savings_goals", 
                "tax_information", "general_inquiry"
            ]
            
            if predicted_class < len(intent_classes):
                intent = intent_classes[predicted_class]
            else:
                intent = default_intent
            
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return default_intent, default_confidence
    
    def _rule_based_intent_classification(self, text: str) -> Tuple[str, float]:
        """
        Fallback rule-based intent classification when the model is unavailable.
        
        Args:
            text: Preprocessed user message
            
        Returns:
            Tuple of (intent_name, confidence_score)
        """
        text_lower = text.lower()
        
        # Financial keyword patterns for each intent
        intent_keywords = {
            "investment_advice": ["invest", "stock", "share", "nse", "return", "profit", "dividend"],
            "budgeting_help": ["budget", "spend", "expense", "track", "money", "income", "salary"],
            "loan_information": ["loan", "borrow", "interest", "repay", "mortgage", "credit", "debt"],
            "market_data": ["market", "price", "rate", "trend", "performance", "index", "chart"],
            "risk_assessment": ["risk", "safe", "secure", "profile", "assessment", "evaluate"],
            "savings_goals": ["save", "goal", "target", "plan", "future", "retirement", "education"],
            "tax_information": ["tax", "kra", "deduct", "return", "file", "vat", "income tax"],
        }
        
        # Count keyword matches for each intent
        intent_scores = {intent: 0 for intent in intent_keywords}
        
        for intent, keywords in intent_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intent_scores[intent] += 1
        
        # Find intent with highest score
        best_intent = "general_inquiry"  # Default
        max_score = 0
        
        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                best_intent = intent
        
        # Calculate confidence score
        confidence = min(max_score / 3, 0.95) if max_score > 0 else 0.3
        
        return best_intent, confidence
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract relevant financial entities from user text.
        
        Args:
            text: Preprocessed user message
            
        Returns:
            List of extracted entities with their types and values
        """
        entities = []
        
        # Use NER model if available
        if self.entity_extractor is not None:
            try:
                model_entities = self.entity_extractor(text)
                
                for entity in model_entities:
                    entities.append({
                        "type": entity["entity"],
                        "value": entity["word"],
                        "confidence": entity["score"],
                        "start": entity["start"],
                        "end": entity["end"]
                    })
                
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")
        
        # Extract financial terms from dictionary
        for term, info in self.financial_terms.items():
            if term.lower() in text.lower():
                entities.append({
                    "type": info.get("type", "FINANCIAL_TERM"),
                    "value": term,
                    "confidence": 1.0,
                    "start": text.lower().find(term.lower()),
                    "end": text.lower().find(term.lower()) + len(term)
                })
        
        return entities
    
    def _generate_response(
        self, 
        intent: str, 
        entities: List[Dict[str, Any]], 
        user_id: str, 
        session_id: str,
        sentiment: Optional[Dict[str, Any]] = None,
        language: str = "en",
        confidence: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generate a personalized financial response based on intent and entities.
        
        Args:
            intent: The classified financial intent
            entities: The extracted financial entities
            user_id: The user's ID
            session_id: The current session ID
            sentiment: Optional sentiment analysis results
            language: The detected language code (en/sw)
            confidence: Confidence score of intent classification
            
        Returns:
            Response data dictionary with financial advice and metadata
        """
        # Get conversation history and user profile
        conversation_history = self.context_manager.get_conversation_history(session_id)
        
        try:
            user_profile = get_user_profile(user_id)
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            user_profile = {"risk_tolerance": "moderate", "financial_goals": [], "preferences": {}}
        
        # Initialize response structure
        response_data = {
            "text": "",
            "intent": intent,
            "confidence": confidence,
            "additional_data": None,
            "suggestions": []
        }
        
        # Route to appropriate handler based on financial intent
        if intent == "investment_advice":
            response_data = self._handle_investment_advice(
                entities, user_profile, conversation_history, language
            )
        elif intent == "budgeting_help":
            response_data = self._handle_budgeting_help(
                entities, user_profile, conversation_history, language
            )
        elif intent == "loan_information":
            response_data = self._handle_loan_information(
                entities, user_profile, conversation_history, language
            )
        elif intent == "market_data":
            response_data = self._handle_market_data(
                entities, user_profile, conversation_history, language
            )
        elif intent == "risk_assessment":
            response_data = self._handle_risk_assessment(
                entities, user_profile, conversation_history, language
            )
        elif intent == "savings_goals":
            response_data = self._handle_savings_goals(
                entities, user_profile, conversation_history, language
            )
        elif intent == "tax_information":
            response_data = self._handle_tax_information(
                entities, user_profile, conversation_history, language
            )
        else:  # general_inquiry or fallback
            response_data = self._handle_general_inquiry(
                entities, user_profile, conversation_history, language
            )
        
        # Adjust response based on user sentiment if available
        if sentiment and CHATBOT_CONFIG.get("enable_sentiment_analysis", True):
            response_data = self._adjust_response_for_sentiment(response_data, sentiment)
        
        # Generate follow-up suggestions
        response_data["suggestions"] = self._generate_follow_up_suggestions(intent, entities, user_profile)
        
        # Add timestamp
        response_data["timestamp"] = datetime.now().isoformat()
        
        return response_data
    
    def _handle_investment_advice(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Generate personalized investment advice based on user profile and market data.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference (en/sw)
            
        Returns:
            Investment advice response with NSE data and recommendations
        """
        response_data = {
            "text": "",
            "intent": "investment_advice",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract investment entities
        investment_type = None
        amount = None
        duration = None
        
        for entity in entities:
            if entity["type"] == "INVESTMENT_TYPE":
                investment_type = entity["value"]
            elif entity["type"] == "MONEY":
                amount = entity["value"]
            elif entity["type"] == "DURATION":
                duration = entity["value"]
        
        # Get real-time NSE stock market data
        market_data = None
        if investment_type in ["stocks", "shares", "equities", "nse"]:
            try:
                market_data = get_nse_data()
            except Exception as e:
                logger.error(f"Failed to get NSE data: {e}")
        
        # Generate AI-powered investment recommendations
        try:
            recommendations = generate_recommendations(
                user_id=user_profile.get("user_id", "unknown"),
                category="investment",
                risk_profile=user_profile.get("risk_tolerance", "moderate"),
                amount=amount,
                duration=duration,
                preferences=user_profile.get("preferences", {})
            )
        except Exception as e:
            logger.error(f"Failed to generate investment recommendations: {e}")
            recommendations = []
        
        # Create multilingual response
        if language == "sw":
            # Swahili response
            if investment_type:
                response_text = f"Kulingana na maelezo yako kuhusu {investment_type}, hapa kuna ushauri wa uwekezaji uliotengenezwa mahususi kwako."
            else:
                response_text = "Hapa kuna mapendekezo ya uwekezaji yanayofaa kwa wasifu wako wa kifedha."
        else:
            # English response
            if investment_type:
                response_text = f"Based on your inquiry about {investment_type}, here is some personalized investment advice for you."
            else:
                response_text = "Here are some investment recommendations that suit your financial profile."
        
        # Add recommendations
        if recommendations:
            response_text += "\n\n"
            for i, rec in enumerate(recommendations[:3], 1):
                if language == "sw":
                    response_text += f"{i}. {rec.get('name_sw', rec.get('name', ''))} - {rec.get('description_sw', rec.get('description', ''))}\n"
                else:
                    response_text += f"{i}. {rec.get('name', '')} - {rec.get('description', '')}\n"
        
        # Add real-time market insights
        if market_data:
            if language == "sw":
                response_text += "\n\nHali ya soko:\n"
                response_text += f"• NSE 20 Share Index: {market_data.get('nse_20_index', 'Haijulikani')}\n"
                response_text += f"• Mabadiliko: {market_data.get('change', 'Haijulikani')}\n"
            else:
                response_text += "\n\nMarket conditions:\n"
                response_text += f"• NSE 20 Share Index: {market_data.get('nse_20_index', 'Unknown')}\n"
                response_text += f"• Change: {market_data.get('change', 'Unknown')}\n"
        
        # Add regulatory disclaimer
        if language == "sw":
            response_text += "\n\nILANI: Uwekezaji wote una hatari. Tafadhali zungumza na mshauri wa kifedha aliyesajiliwa kabla ya kufanya uamuzi wa uwekezaji."
        else:
            response_text += "\n\nDISCLAIMER: All investments carry risk. Please consult with a registered financial advisor before making investment decisions."
        
        response_data["text"] = response_text
        response_data["additional_data"] = {
            "recommendations": recommendations,
            "market_data": market_data
        }
        
        return response_data
    
    def _handle_budgeting_help(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Generate personalized budgeting advice based on user's financial situation.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Budgeting advice response with household budget recommendations
        """
        response_data = {
            "text": "",
            "intent": "budgeting_help",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract income and expense entities
        income = None
        expense_type = None
        
        for entity in entities:
            if entity["type"] == "MONEY" or entity["type"] == "INCOME":
                income = entity["value"]
            elif entity["type"] == "EXPENSE_TYPE":
                expense_type = entity["value"]
        
        # Generate localized budgeting advice
        if language == "sw":
            # Swahili response with Kenyan context
            if income:
                response_text = f"Kwa mapato ya {income}, napendekeza mgawanyo wa bajeti ufuatao:"
                response_text += "\n\n• 50% - Mahitaji muhimu (kodi, chakula, umeme, maji, usafiri)"
                response_text += "\n• 30% - Mahitaji ya kibinafsi (burudani, mavazi, chakula cha nje)"
                response_text += "\n• 20% - Akiba na uwekezaji (akiba ya dharura, malipo ya madeni, uwekezaji)"
            elif expense_type:
                response_text = f"Kuhusu {expense_type}, hapa kuna vidokezo vya kubajeti:"
            else:
                response_text = "Hapa kuna kanuni za bajeti zinazofaa wengi wa Wakenya:"
                response_text += "\n\n• Tengeneza bajeti inayolingana na mapato yako"
                response_text += "\n• Weka akiba ya dharura (angalau mshahara wa miezi 3-6)"
                response_text += "\n• Lipa madeni yenye riba ya juu kwanza"
                response_text += "\n• Tumia kanuni ya 50/30/20 kwa mgawanyo wa mapato"
        else:
            # English response with Kenyan context
            if income:
                response_text = f"For an income of {income}, I recommend the following budget allocation:"
                response_text += "\n\n• 50% - Essential needs (rent, food, utilities, transport)"
                response_text += "\n• 30% - Personal needs (entertainment, clothing, eating out)"
                response_text += "\n• 20% - Savings and investments (emergency fund, debt payments, investments)"
            elif expense_type:
                response_text = f"Regarding {expense_type}, here are some budgeting tips:"
            else:
                response_text = "Here are some budgeting principles that work well for most Kenyans:"
                response_text += "\n\n• Create a budget that matches your income"
                response_text += "\n• Build an emergency fund (at least 3-6 months of expenses)"
                response_text += "\n• Pay off high-interest debt first"
                response_text += "\n• Use the 50/30/20 rule for income allocation"
        
        # Add Kenya-specific M-Pesa tip
        if language == "sw":
            response_text += "\n\nKidokezo: Unaweza kutumia M-Pesa Lock Savings kutenganisha akiba yako na pesa za matumizi ya kila siku."
        else:
            response_text += "\n\nTip: You can use M-Pesa Lock Savings to separate your savings from your everyday spending money."
        
        response_data["text"] = response_text
        
        return response_data
    
    def _handle_loan_information(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Provide information about Kenyan loan options, interest rates, and repayment terms.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Loan information response with current interest rates
        """
        response_data = {
            "text": "",
            "intent": "loan_information",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract loan-related entities
        loan_type = None
        amount = None
        duration = None
        
        for entity in entities:
            if entity["type"] == "LOAN_TYPE":
                loan_type = entity["value"]
            elif entity["type"] == "MONEY":
                amount = entity["value"]
            elif entity["type"] == "DURATION":
                duration = entity["value"]
        
        # Get real-time loan data from CBK
        try:
            loan_rates = get_cbk_data().get("loan_rates", {})
        except Exception as e:
            logger.error(f"Failed to get CBK data: {e}")
            loan_rates = {}
        
        # Get mobile loan information from M-Pesa API
        try:
            mobile_loans = get_mpesa_data().get("loan_products", {})
        except Exception as e:
            logger.error(f"Failed to get M-Pesa data: {e}")
            mobile_loans = {}
        
        # Generate localized response
        if language == "sw":
            # Swahili response
            if loan_type:
                response_text = f"Kuhusu mikopo ya {loan_type}, hapa kuna maelezo muhimu:"
            else:
                response_text = "Hapa kuna maelezo kuhusu aina mbalimbali za mikopo inayopatikana Kenya:"
        else:
            # English response
            if loan_type:
                response_text = f"Regarding {loan_type} loans, here is some important information:"
            else:
                response_text = "Here is information about different types of loans available in Kenya:"
        
        # Add bank loan rates
        if loan_rates:
            response_text += "\n\n"
            if language == "sw":
                response_text += "Viwango vya riba vya sasa:\n"
            else:
                response_text += "Current interest rates:\n"
            
            for bank, rate in loan_rates.items():
                response_text += f"• {bank}: {rate}%\n"
        
        # Add Kenya-specific mobile loan options
        if mobile_loans and (not loan_type or loan_type.lower() in ["mobile", "digital", "fuliza", "m-shwari"]):
            response_text += "\n\n"
            if language == "sw":
                response_text += "Mikopo ya simu:\n"
            else:
                response_text += "Mobile loan options:\n"
            
            for product, details in mobile_loans.items():
                if language == "sw":
                    response_text += f"• {product}: Riba {details.get('interest_rate', 'N/A')}, Muda {details.get('duration', 'N/A')}\n"
                else:
                    response_text += f"• {product}: Interest {details.get('interest_rate', 'N/A')}, Duration {details.get('duration', 'N/A')}\n"
        
        # Add loan calculator tip
        if language == "sw":
            response_text += "\n\nKidokezo: Tumia kikokotoo chetu cha mikopo kukadiria malipo yako ya kila mwezi na jumla ya gharama ya mkopo."
        else:
            response_text += "\n\nTip: Use our loan calculator to estimate your monthly payments and total cost of the loan."
        
        # Add regulatory disclaimer
        if language == "sw":
            response_text += "\n\nILANI: Hakikisha unaelewa masharti na riba kabla ya kuchukua mkopo wowote."
        else:
            response_text += "\n\nDISCLAIMER: Ensure you understand the terms and interest rates before taking any loan."
        
        response_data["text"] = response_text
        response_data["additional_data"] = {
            "loan_rates": loan_rates,
            "mobile_loans": mobile_loans
        }
        
        return response_data
    
    def _handle_market_data(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Provide real-time market data for stocks, forex, or crypto based on user query.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Market data response with current prices and trends
        """
        response_data = {
            "text": "",
            "intent": "market_data",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract market-related entities
        market_type = None
        symbol = None
        
        for entity in entities:
            if entity["type"] == "MARKET_TYPE":
                market_type = entity["value"].lower()
            elif entity["type"] == "SYMBOL" or entity["type"] == "COMPANY_NAME":
                symbol = entity["value"]
        
        # Default to NSE if no market type specified
        if not market_type:
            market_type = "stocks"
        
        # Fetch appropriate market data
        market_data = None
        
        if market_type in ["stocks", "shares", "nse", "equities"]:
            try:
                if symbol:
                    market_data = get_nse_data(symbol=symbol)
                else:
                    market_data = get_nse_data()
            except Exception as e:
                logger.error(f"Failed to get NSE data: {e}")
        
        elif market_type in ["forex", "currency", "exchange", "usd", "dollar"]:
            try:
                market_data = get_cbk_data().get("forex_rates", {})
            except Exception as e:
                logger.error(f"Failed to get forex data: {e}")
        
        elif market_type in ["crypto", "bitcoin", "ethereum", "cryptocurrency"]:
            try:
                if symbol:
                    market_data = get_crypto_data(symbol=symbol)
                else:
                    market_data = get_crypto_data()
            except Exception as e:
                logger.error(f"Failed to get crypto data: {e}")
        
        # Generate response based on available data
        if language == "sw":
            if market_type in ["stocks", "shares", "nse", "equities"]:
                response_text = "Hapa kuna data ya hisa kutoka Soko la Hisa la Nairobi (NSE):"
            elif market_type in ["forex", "currency", "exchange", "usd", "dollar"]:
                response_text = "Hapa kuna viwango vya kubadilisha fedha:"
            elif market_type in ["crypto", "bitcoin", "ethereum", "cryptocurrency"]:
                response_text = "Hapa kuna data ya soko la sarafu za kidijitali:"
            else:
                response_text = "Hapa kuna data ya soko:"
        else:
            if market_type in ["stocks", "shares", "nse", "equities"]:
                response_text = "Here is the latest stock data from the Nairobi Securities Exchange (NSE):"
            elif market_type in ["forex", "currency", "exchange", "usd", "dollar"]:
                response_text = "Here are the current foreign exchange rates:"
            elif market_type in ["crypto", "bitcoin", "ethereum", "cryptocurrency"]:
                response_text = "Here is the latest cryptocurrency market data:"
            else:
                response_text = "Here is the latest market data:"
        
        # Format the data according to market type
        if market_data:
            response_text += "\n\n"
            
            if market_type in ["stocks", "shares", "nse", "equities"]:
                # Format NSE stock data
                if symbol and isinstance(market_data, dict):
                    # Single stock data
                    stock_name = market_data.get("name", symbol)
                    price = market_data.get("price", "N/A")
                    change = market_data.get("change", "N/A")
                    
                    response_text += f"• {stock_name}: KES {price} ({change})\n"
                    response_text += f"• 52-Week High: KES {market_data.get('52_week_high', 'N/A')}\n"
                    response_text += f"• 52-Week Low: KES {market_data.get('52_week_low', 'N/A')}\n"
                    response_text += f"• Volume: {market_data.get('volume', 'N/A')}\n"
                else:
                    # Top stocks
                    for stock in market_data[:5]:
                        response_text += f"• {stock.get('name', 'Unknown')}: KES {stock.get('price', 'N/A')} ({stock.get('change', 'N/A')})\n"
                    
                    response_text += f"\nNSE 20 Index: {market_data[0].get('nse_20_index', 'N/A')} ({market_data[0].get('index_change', 'N/A')})"
            
            elif market_type in ["forex", "currency", "exchange", "usd", "dollar"]:
                # Format forex data
                for currency, rate in market_data.items():
                    response_text += f"• {currency}: KES {rate}\n"
            
            elif market_type in ["crypto", "bitcoin", "ethereum", "cryptocurrency"]:
                # Format crypto data
                if symbol and isinstance(market_data, dict):
                    # Single crypto data
                    crypto_name = market_data.get("name", symbol)
                    price_usd = market_data.get("price_usd", "N/A")
                    price_kes = market_data.get("price_kes", "N/A")
                    change_24h = market_data.get("change_24h", "N/A")
                    
                    response_text += f"• {crypto_name}: ${price_usd} / KES {price_kes} ({change_24h})\n"
                    response_text += f"• Market Cap: ${market_data.get('market_cap', 'N/A')}\n"
                    response_text += f"• 24h Volume: ${market_data.get('volume_24h', 'N/A')}\n"
                else:
                    # Top cryptos
                    for crypto in market_data[:5]:
                        response_text += f"• {crypto.get('name', 'Unknown')}: ${crypto.get('price_usd', 'N/A')} / KES {crypto.get('price_kes', 'N/A')} ({crypto.get('change_24h', 'N/A')})\n"
        else:
            if language == "sw":
                response_text += "\n\nSamahani, data ya soko haipatikani kwa sasa. Tafadhali jaribu tena baadaye."
            else:
                response_text += "\n\nSorry, market data is currently unavailable. Please try again later."
        
        # Add disclaimer
        if language == "sw":
            response_text += "\n\nILANI: Data ya soko hubadilika kila wakati. Data iliyotolewa hapo juu ilikuwa sahihi wakati wa kujibu swali lako."
        else:
            response_text += "\n\nDISCLAIMER: Market data is subject to change. The information provided above was accurate at the time of response."
        
        response_data["text"] = response_text
        response_data["additional_data"] = {"market_data": market_data, "market_type": market_type}
        
        return response_data
    
    def _handle_risk_assessment(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Assess user's risk tolerance and provide investment recommendations accordingly.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Risk assessment response with personalized profile
        """
        response_data = {
            "text": "",
            "intent": "risk_assessment",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Get or calculate user's risk profile
        try:
            risk_profile = evaluate_risk_profile(user_profile)
        except Exception as e:
            logger.error(f"Failed to evaluate risk profile: {e}")
            # Default profile if calculation fails
            risk_profile = {
                "risk_tolerance": user_profile.get("risk_tolerance", "moderate"),
                "investment_horizon": "medium",
                "score": 50,
                "suitable_assets": ["government_bonds", "blue_chip_stocks", "balanced_funds"]
            }
        
        # Generate response based on risk profile
        if language == "sw":
            response_text = "Kulingana na wasifu wako wa kifedha, hapa kuna tathmini ya hatari yako:"
            response_text += f"\n\n• Uvumilivu wa hatari: {_translate_risk_tolerance(risk_profile.get('risk_tolerance', 'moderate'), 'sw')}"
            response_text += f"\n• Muda wa uwekezaji: {_translate_investment_horizon(risk_profile.get('investment_horizon', 'medium'), 'sw')}"
            
            response_text += "\n\nUwekezaji unaofaa:"
            for asset in risk_profile.get("suitable_assets", []):
                response_text += f"\n• {_translate_asset_type(asset, 'sw')}"
        else:
            response_text = "Based on your financial profile, here is your risk assessment:"
            response_text += f"\n\n• Risk tolerance: {risk_profile.get('risk_tolerance', 'Moderate').title()}"
            response_text += f"\n• Investment horizon: {risk_profile.get('investment_horizon', 'Medium').title()}"
            
            response_text += "\n\nSuitable investments:"
            for asset in risk_profile.get("suitable_assets", []):
                response_text += f"\n• {_translate_asset_type(asset, 'en')}"
        
        # Add explanation of risk profile
        if language == "sw":
            response_text += "\n\nEleza zaidi:"
            if risk_profile.get("risk_tolerance") == "conservative":
                response_text += "\nWawekezaji wahafidhina hutafuta kulinda mtaji wao na kupata mapato ya kawaida. Wao huwekeza zaidi katika dhamana za serikali, amana, na hisa za kampuni kubwa na imara."
            elif risk_profile.get("risk_tolerance") == "moderate":
                response_text += "\nWawekezaji wa wastani hutafuta usawazisho kati ya ukuaji na usalama. Wao huwekeza katika mchanganyiko wa hisa, dhamana na rasilimali nyingine."
            elif risk_profile.get("risk_tolerance") == "aggressive":
                response_text += "\nWawekezaji jasiri hutafuta ukuaji wa juu wa mtaji na wako tayari kuchukua hatari kubwa. Wao huwekeza zaidi katika hisa, biashara zinazochipuka, na mali mbadala."
        else:
            response_text += "\n\nExplanation:"
            if risk_profile.get("risk_tolerance") == "conservative":
                response_text += "\nConservative investors seek capital preservation and regular income. They invest more in government securities, deposits, and blue-chip company stocks."
            elif risk_profile.get("risk_tolerance") == "moderate":
                response_text += "\nModerate investors seek a balance between growth and security. They invest in a mix of stocks, bonds, and other assets."
            elif risk_profile.get("risk_tolerance") == "aggressive":
                response_text += "\nAggressive investors seek high capital growth and are willing to take significant risks. They invest more in stocks, emerging businesses, and alternative assets."
        
        # Add disclaimer
        if language == "sw":
            response_text += "\n\nILANI: Tathmini hii ya hatari ni kwa madhumuni ya elimu pekee. Tafadhali zungumza na mshauri wa kifedha aliyesajiliwa kwa ushauri wa kibinafsi zaidi."
        else:
            response_text += "\n\nDISCLAIMER: This risk assessment is for educational purposes only. Please consult with a registered financial advisor for more personalized advice."
        
        response_data["text"] = response_text
        response_data["additional_data"] = {"risk_profile": risk_profile}
        
        return response_data
    
    def _handle_savings_goals(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Provide guidance on setting and achieving financial savings goals.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Savings goals response with personalized recommendations
        """
        response_data = {
            "text": "",
            "intent": "savings_goals",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract savings-related entities
        goal_type = None
        amount = None
        duration = None
        
        for entity in entities:
            if entity["type"] == "GOAL_TYPE":
                goal_type = entity["value"]
            elif entity["type"] == "MONEY":
                amount = entity["value"]
            elif entity["type"] == "DURATION":
                duration = entity["value"]
        
        # Generate Kenya-specific savings advice
        if language == "sw":
            if goal_type:
                response_text = f"Kuhusu lengo lako la kuweka akiba kwa {goal_type}, hapa kuna ushauri:"
            else:
                response_text = "Hapa kuna vidokezo vya kuweka akiba kwa madhumuni mbalimbali:"
        else:
            if goal_type:
                response_text = f"Regarding your {goal_type} savings goal, here's some advice:"
            else:
                response_text = "Here are tips for saving for various purposes:"
        
        # Add specific savings advice based on goal type
        response_text += "\n\n"
        if goal_type and goal_type.lower() in ["emergency", "emergency fund", "dharura"]:
            if language == "sw":
                response_text += "Akiba ya Dharura:\n"
                response_text += "• Lengo: Kuwa na akiba ya matumizi ya miezi 3-6\n"
                response_text += "• Weka akiba katika akaunti inayopatikana kwa urahisi\n"
                response_text += "• Tenganisha akiba hii na akaunti yako ya kawaida\n"
                response_text += "• Tumia M-Pesa Lock Savings au akaunti ya akiba ya benki"
            else:
                response_text += "Emergency Fund:\n"
                response_text += "• Target: 3-6 months of expenses\n"
                response_text += "• Keep savings in an easily accessible account\n"
                response_text += "• Separate this fund from your regular account\n"
                response_text += "• Use M-Pesa Lock Savings or a bank savings account"
        
        elif goal_type and goal_type.lower() in ["education", "school", "college", "university", "elimu", "shule", "chuo"]:
            if language == "sw":
                response_text += "Akiba ya Elimu:\n"
                response_text += "• Anza kuweka akiba mapema iwezekanavyo\n"
                response_text += "• Fikiria akaunti za akiba za elimu zenye kodi nafuu\n"
                response_text += "• Wekeza katika hazina za uwekezaji za muda mrefu kama elimu iko zaidi ya miaka 5\n"
                response_text += "• Chagua SACCO zinazotoa mikopo ya elimu yenye riba nafuu"
            else:
                response_text += "Education Savings:\n"
                response_text += "• Start saving as early as possible\n"
                response_text += "• Consider tax-advantaged education savings accounts\n"
                response_text += "• Invest in long-term funds if education is more than 5 years away\n"
                response_text += "• Look into SACCOs that offer low-interest education loans"
        
        elif goal_type and goal_type.lower() in ["retirement", "pension", "uzeeni", "pensheni"]:
            if language == "sw":
                response_text += "Akiba ya Uzeeni:\n"
                response_text += "• Hakikisha unachangia NSSF kwa ajili ya pensheni ya msingi\n"
                response_text += "• Fikiria mpango wa ziada wa pensheni kupitia mwajiri au binafsi\n"
                response_text += "• Wekeza katika hazina za uwekezaji za muda mrefu\n"
                response_text += "• Jenge portfolio ya uwekezaji iliyolengwa kwa mapato ya uzeeni"
            else:
                response_text += "Retirement Savings:\n"
                response_text += "• Ensure you contribute to NSSF for basic pension\n"
                response_text += "• Consider additional pension plans through employer or individually\n"
                response_text += "• Invest in long-term investment funds\n"
                response_text += "• Build an investment portfolio targeted for retirement income"
        
        elif goal_type and goal_type.lower() in ["home", "house", "nyumba", "apartment", "mortgage"]:
            if language == "sw":
                response_text += "Akiba ya Nyumba:\n"
                response_text += "• Lenga kulipa angalau 10-20% ya bei ya nyumba kama malipo ya awali\n"
                response_text += "• Chapisha historia nzuri ya mikopo kuwezesha kupata mkopo wa nyumba\n"
                response_text += "• Fikiria hazina za uwekezaji za mali isiyohamishika (REITs)\n"
                response_text += "• Angalia programu za nyumba za bei nafuu kutoka serikali"
            else:
                response_text += "Home Purchase Savings:\n"
                response_text += "• Aim to save at least 10-20% of the property price as down payment\n"
                response_text += "• Build a good credit history to qualify for a mortgage\n"
                response_text += "• Consider Real Estate Investment Trusts (REITs)\n"
                response_text += "• Look into affordable housing programs from the government"
        
        else:
            # General savings advice
            if language == "sw":
                response_text += "Vidokezo vya Jumla vya Kuweka Akiba:\n"
                response_text += "• Weka kando angalau 10-20% ya mapato yako kila mwezi\n"
                response_text += "• Tumia mbinu ya 'Jilipe Kwanza' - weka akiba mara tu unapopokea mshahara\n"
                response_text += "• Weka malengo mahususi ya akiba na tarehe za mwisho\n"
                response_text += "• Tumia programu za kibajeti kufuatilia na kuboresha matumizi yako"
            else:
                response_text += "General Savings Tips:\n"
                response_text += "• Set aside at least 10-20% of your income each month\n"
                response_text += "• Use the 'Pay Yourself First' method - save immediately when you receive your salary\n"
                response_text += "• Set specific savings goals with deadlines\n"
                response_text += "• Use budgeting apps to track and improve your spending"
        
        # Add Kenya-specific savings options
        response_text += "\n\n"
        if language == "sw":
            response_text += "Chaguo za Kuweka Akiba nchini Kenya:\n"
            response_text += "• M-Pesa Lock Savings - kwa kuweka akiba kwa muda mfupi\n"
            response_text += "• Akaunti za Akiba za Benki - kwa akiba ya dharura na muda mfupi\n"
            response_text += "• Hazina za Uwekezaji za Pesa za Soko - kwa akiba ya muda wa kati\n"
            response_text += "• SACCO - kwa mikopo nafuu na mapato ya ziada\n"
            response_text += "• Dhamana za Serikali (T-bills, T-bonds) - kwa usalama na mapato ya kawaida"
        else:
            response_text += "Savings Options in Kenya:\n"
            response_text += "• M-Pesa Lock Savings - for short-term savings\n"
            response_text += "• Bank Savings Accounts - for emergency and short-term savings\n"
            response_text += "• Money Market Funds - for medium-term savings\n"
            response_text += "• SACCOs - for affordable loans and additional returns\n"
            response_text += "• Government Securities (T-bills, T-bonds) - for safety and regular income"
        
        response_data["text"] = response_text
        
        # Add calculator suggestion
        if language == "sw":
            response_data["text"] += "\n\nKidokezo: Tumia kikokotoo chetu cha akiba kukadiri ni kiasi gani unahitaji kuweka akiba kila mwezi kufikia lengo lako."
        else:
            response_data["text"] += "\n\nTip: Use our savings calculator to estimate how much you need to save monthly to reach your goal."
        
        return response_data
    
    def _handle_tax_information(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Provide information about Kenyan tax regulations, filing, and compliance.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            Tax information response with Kenyan tax guidelines
        """
        response_data = {
            "text": "",
            "intent": "tax_information",
            "confidence": 0.9,
            "additional_data": None
        }
        
        # Extract tax-related entities
        tax_type = None
        income_type = None
        
        for entity in entities:
            if entity["type"] == "TAX_TYPE":
                tax_type = entity["value"]
            elif entity["type"] == "INCOME_TYPE":
                income_type = entity["value"]
        
        # Generate Kenya-specific tax information
        if language == "sw":
            if tax_type:
                response_text = f"Kuhusu {tax_type}, hapa kuna maelezo muhimu ya kodi:"
            else:
                response_text = "Hapa kuna maelezo muhimu kuhusu mfumo wa kodi nchini Kenya:"
        else:
            if tax_type:
                response_text = f"Regarding {tax_type}, here is important tax information:"
            else:
                response_text = "Here is important information about the tax system in Kenya:"
        
        # Add specific tax information based on tax type
        response_text += "\n\n"
        if tax_type and tax_type.lower() in ["income tax", "paye", "kodi ya mapato"]:
            if language == "sw":
                response_text += "Kodi ya Mapato (PAYE):\n"
                response_text += "• Viwango vya sasa: 10% hadi 30% kulingana na kipato\n"
                response_text += "• Mapato ya chini ya KES 24,000 kwa mwezi hayatozwi kodi\n"
                response_text += "• Waajiri hukata kodi kupitia mfumo wa PAYE\n"
                response_text += "• Marejesho ya kodi yanafaa kuwasilishwa ifikapo Juni 30 kila mwaka"
            else:
                response_text += "Income Tax (PAYE):\n"
                response_text += "• Current rates: 10% to 30% depending on income\n"
                response_text += "• Income below KES 24,000 per month is tax-exempt\n"
                response_text += "• Employers deduct tax through the PAYE system\n"
                response_text += "• Tax returns should be filed by June 30 each year"
        
        elif tax_type and tax_type.lower() in ["vat", "value added tax", "kodi ya ongezeko la thamani"]:
            if language == "sw":
                response_text += "Kodi ya Ongezeko la Thamani (VAT):\n"
                response_text += "• Kiwango cha kawaida: 16%\n"
                response_text += "• Bidhaa na huduma muhimu zimeondolewa kodi au zina kiwango cha chini\n"
                response_text += "• Biashara zinazozalisha mapato ya KES 5 milioni au zaidi kwa mwaka zinahitajika kusajiliwa kwa VAT\n"
                response_text += "• Marejesho ya VAT yanafaa kuwasilishwa kila mwezi au robo mwaka"
            else:
                response_text += "Value Added Tax (VAT):\n"
                response_text += "• Standard rate: 16%\n"
                response_text += "• Essential goods and services are exempt or zero-rated\n"
                response_text += "• Businesses with turnover of KES 5 million or more per year must register for VAT\n"
                response_text += "• VAT returns should be filed monthly or quarterly"
        
        elif tax_type and tax_type.lower() in ["capital gains", "capital gains tax", "kodi ya faida ya mtaji"]:
            if language == "sw":
                response_text += "Kodi ya Faida ya Mtaji:\n"
                response_text += "• Kiwango cha sasa: 15% kwa faida itokanayo na uuzaji wa mali\n"
                response_text += "• Inatumika kwa uuzaji wa hisa, hati za dhamana, mali isiyohamishika, n.k.\n"
                response_text += "• Nyumba ya kibinafsi kwa kawaida imeondolewa kodi\n"
                response_text += "• Inapaswa kulipwa ndani ya siku 20 za mwezi unaofuata uuzaji"
            else:
                response_text += "Capital Gains Tax:\n"
                response_text += "• Current rate: 15% on gains from sale of property\n"
                response_text += "• Applies to sale of shares, securities, real estate, etc.\n"
                response_text += "• Personal residence is typically exempt\n"
                response_text += "• Should be paid within 20 days of the month following the sale"
        
        elif tax_type and tax_type.lower() in ["withholding tax", "kodi ya zuio"]:
            if language == "sw":
                response_text += "Kodi ya Zuio:\n"
                response_text += "• Hulipwa kwenye gawio: 15% kwa wakazi, 20% kwa wasio wakazi\n"
                response_text += "• Hulipwa kwenye riba: 15% kwa wakazi, 15% kwa wasio wakazi\n"
                response_text += "• Hulipwa kwenye mirabaha: 20% kwa wakazi na wasio wakazi\n"
                response_text += "• Hulipwa kwenye ada ya ushauri: 5% kwa wakazi, 20% kwa wasio wakazi"
            else:
                response_text += "Withholding Tax:\n"
                response_text += "• Paid on dividends: 15% for residents, 20% for non-residents\n"
                response_text += "• Paid on interest: 15% for residents, 15% for non-residents\n"
                response_text += "• Paid on royalties: 20% for both residents and non-residents\n"
                response_text += "• Paid on consulting fees: 5% for residents, 20% for non-residents"
        
        else:
            # General tax information
            if language == "sw":
                response_text += "Maelezo ya Jumla ya Kodi nchini Kenya:\n"
                response_text += "• Mwaka wa kodi: Januari 1 hadi Desemba 31\n"
                response_text += "• Mwisho wa kuwasilisha marejesho ya kodi ya mapato: Juni 30\n"
                response_text += "• Usajili wa KRA: Lazima kwa wafanyakazi wote na wafanyabiashara\n"
                response_text += "• Nambari ya utambulisho ya kodi (KRA PIN): Muhimu kwa miamala mingi ya kifedha"
            else:
                response_text += "General Tax Information in Kenya:\n"
                response_text += "• Tax year: January 1 to December 31\n"
                response_text += "• Income tax return filing deadline: June 30\n"
                response_text += "• KRA registration: Mandatory for all employees and business owners\n"
                response_text += "• Tax identification number (KRA PIN): Required for many financial transactions"
        
        # Add Kenya-specific tax compliance advice
        response_text += "\n\n"
        if language == "sw":
            response_text += "Ushauri wa Utiifu wa Kodi:\n"
            response_text += "• Hakikisha umeandikisha KRA PIN kupitia iTax portal\n"
            response_text += "• Wasilisha marejesho ya kodi kwa wakati, hata kama huna mapato\n"
            response_text += "• Weka rekodi bora za mapato na matumizi kwa miaka 7\n"
            response_text += "• Tuma malipo ya kodi kwa wakati kuepuka faini na adhabu"
        else:
            response_text += "Tax Compliance Advice:\n"
            response_text += "• Ensure you register for a KRA PIN through the iTax portal\n"
            response_text += "• File tax returns on time, even if you have no income\n"
            response_text += "• Maintain good records of income and expenses for 7 years\n"
            response_text += "• Make tax payments on time to avoid penalties and fines"
        
        response_data["text"] = response_text
        
        # Add tax disclaimer
        if language == "sw":
            response_data["text"] += "\n\nILANI: Maelezo haya ni kwa madhumuni ya elimu pekee. Tafadhali wasiliana na mtaalamu wa kodi au KRA kwa ushauri mahususi wa kodi."
        else:
            response_data["text"] += "\n\nDISCLAIMER: This information is for educational purposes only. Please contact a tax professional or KRA for specific tax advice."
        
        return response_data
    
    def _handle_general_inquiry(
        self, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        language: str
    ) -> Dict[str, Any]:
        """
        Handle general financial inquiries or fallback when intent is unclear.
        
        Args:
            entities: Extracted financial entities
            user_profile: User's financial profile
            conversation_history: Previous conversation context
            language: The user's language preference
            
        Returns:
            General response with financial information
        """
        response_data = {
            "text": "",
            "intent": "general_inquiry",
            "confidence": 0.7,
            "additional_data": None
        }
        
        # Check if any financial terms were mentioned
        financial_terms_mentioned = []
        for entity in entities:
            if entity["type"] == "FINANCIAL_TERM":
                financial_terms_mentioned.append(entity["value"])
        
        # Generate appropriate response
        if financial_terms_mentioned:
            # Provide information on the financial terms mentioned
            if language == "sw":
                response_text = "Nilikuta istilahi zifuatazo za kifedha katika swali lako:\n\n"
            else:
                response_text = "I found the following financial terms in your question:\n\n"
            
            for term in financial_terms_mentioned:
                term_info = self.financial_terms.get(term, {})
                if language == "sw" and "description_sw" in term_info:
                    response_text += f"• {term}: {term_info['description_sw']}\n\n"
                elif "description" in term_info:
                    response_text += f"• {term}: {term_info['description']}\n\n"
        else:
            # General financial advice or greeting
            previous_messages = [msg["text"] for msg in conversation_history if msg["sender"] == "user"]
            
            if not previous_messages:
                # First message - greeting
                if language == "sw":
                    response_text = "Karibu kwenye PesaGuru! Mimi ni msaidizi wako wa kifedha. Ninaweza kukusaidia na maswali kuhusu uwekezaji, bajeti, mikopo, au mipango ya kifedha. Unataka nikusaidie vipi leo?"
                else:
                    response_text = "Welcome to PesaGuru! I'm your financial assistant. I can help you with questions about investments, budgeting, loans, or financial planning. How can I assist you today?"
            else:
                # Not first message - general financial advice
                if language == "sw":
                    response_text = "Kama msaidizi wako wa kifedha, ninaweza kukusaidia na:\n\n"
                    response_text += "• Ushauri wa uwekezaji kulingana na malengo yako\n"
                    response_text += "• Vidokezo vya bajeti na usimamizi wa pesa\n"
                    response_text += "• Taarifa za mikopo na viwango vya riba\n"
                    response_text += "• Maelezo ya soko la hisa, fedha, na sarafu za kidijitali\n"
                    response_text += "• Tathmini ya hatari ya kifedha\n"
                    response_text += "• Mikakati ya akiba na kuweka malengo\n"
                    response_text += "• Maelezo ya kodi\n\n"
                    response_text += "Tafadhali niulize swali lolote mahususi kuhusu fedha zako."
                else:
                    response_text = "As your financial assistant, I can help you with:\n\n"
                    response_text += "• Investment advice based on your goals\n"
                    response_text += "• Budgeting tips and money management\n"
                    response_text += "• Loan information and interest rates\n"
                    response_text += "• Stock, forex, and cryptocurrency market data\n"
                    response_text += "• Financial risk assessment\n"
                    response_text += "• Savings strategies and goal setting\n"
                    response_text += "• Tax information\n\n"
                    response_text += "Please ask me any specific question about your finances."
        
        response_data["text"] = response_text
        return response_data
    
    def _adjust_response_for_sentiment(
        self, 
        response_data: Dict[str, Any], 
        sentiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust chatbot response based on detected user sentiment.
        
        Args:
            response_data: The current response data
            sentiment: Detected sentiment from sentiment analysis
            
        Returns:
            Updated response with sentiment-appropriate language
        """
        sentiment_score = sentiment.get("score", 0)
        sentiment_label = sentiment.get("label", "neutral")
        current_text = response_data["text"]
        
        # Add sentiment-appropriate opening line
        if sentiment_label == "negative" and sentiment_score < -0.5:
            # Very negative sentiment - add empathetic response
            if "sw" in sentiment.get("language", "en"):
                opening = "Nasikitika kusikia hayo. "
            else:
                opening = "I understand this might be concerning. "
            response_data["text"] = opening + current_text
        
        elif sentiment_label == "negative":
            # Somewhat negative sentiment
            if "sw" in sentiment.get("language", "en"):
                opening = "Ninaelewa wasiwasi wako. "
            else:
                opening = "I understand your concern. "
            response_data["text"] = opening + current_text
        
        elif sentiment_label == "positive" and sentiment_score > 0.5:
            # Very positive sentiment
            if "sw" in sentiment.get("language", "en"):
                opening = "Ninafurahi kusikia hayo! "
            else:
                opening = "That's great to hear! "
            response_data["text"] = opening + current_text
        
        # Add sentiment data to response metadata
        response_data["sentiment"] = sentiment
        return response_data
    
    def _generate_follow_up_suggestions(
        self, 
        intent: str, 
        entities: List[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> List[str]:
        """
        Generate follow-up question suggestions based on the user's intent and context.
        
        Args:
            intent: The classified financial intent
            entities: The extracted financial entities
            user_profile: The user's financial profile
            
        Returns:
            List of suggested follow-up questions
        """
        suggestions = []
        
        # Generate follow-up questions based on intent
        if intent == "investment_advice":
            suggestions = [
                "What stocks are trending on NSE this week?",
                "How much should I invest monthly?",
                "What is the safest investment option?",
                "How do I diversify my portfolio?"
            ]
        
        elif intent == "budgeting_help":
            suggestions = [
                "How can I track my expenses?",
                "What's a good budget for my income?",
                "How can I reduce my monthly expenses?",
                "How much should I save each month?"
            ]
        
        elif intent == "loan_information":
            suggestions = [
                "Which bank has the lowest interest rates?",
                "How does M-Shwari compare to KCB M-Pesa?",
                "How can I improve my credit score?",
                "How much can I afford to borrow?"
            ]
        
        elif intent == "market_data":
            suggestions = [
                "What's the current exchange rate for USD to KES?",
                "How is the NSE performing this week?",
                "What's the price of Bitcoin in Kenya Shillings?",
                "Which stocks have the highest dividends?"
            ]
        
        elif intent == "risk_assessment":
            suggestions = [
                "What investments match my risk profile?",
                "How can I reduce financial risk?",
                "Should I be more aggressive with my investments?",
                "How does my risk tolerance affect my returns?"
            ]
        
        elif intent == "savings_goals":
            suggestions = [
                "How much should I save for retirement?",
                "What's the best way to save for a house?",
                "How can I save for my child's education?",
                "What savings products give the best returns?"
            ]
        
        elif intent == "tax_information":
            suggestions = [
                "When is the tax filing deadline in Kenya?",
                "How can I reduce my tax burden legally?",
                "What expenses are tax-deductible?",
                "How do I file tax returns on iTax?"
            ]
        
        else:  # general_inquiry
            suggestions = [
                "How can I start investing?",
                "Help me create a budget",
                "What loan options are available?",
                "Show me current market data",
                "How can I save for the future?"
            ]
        
        # Customize follow-up questions based on user profile if available
        if user_profile:
            risk_tolerance = user_profile.get("risk_tolerance", "")
            if risk_tolerance == "conservative" and intent == "investment_advice":
                suggestions.append("What are the safest investment options in Kenya?")
            elif risk_tolerance == "aggressive" and intent == "investment_advice":
                suggestions.append("Which high-growth stocks should I consider?")
            
            financial_goals = user_profile.get("financial_goals", [])
            if "retirement" in str(financial_goals).lower():
                suggestions.append("How should I invest for retirement in Kenya?")
            if "house" in str(financial_goals).lower() or "home" in str(financial_goals).lower():
                suggestions.append("What are the best home financing options?")
            if "education" in str(financial_goals).lower():
                suggestions.append("How can I save for education expenses?")
        
        # Limit to 3 suggestions and randomize
        import random
        random.shuffle(suggestions)
        return suggestions[:3]
    
    def _log_interaction(
        self,
        user_id: str,
        session_id: str,
        message: str,
        intent: str,
        entities: List[Dict[str, Any]],
        sentiment: Optional[Dict[str, Any]],
        response: Dict[str, Any]
    ) -> None:
        """
        Log user interaction for analysis and improvement.
        
        Args:
            user_id: The user's ID
            session_id: The current session ID
            message: The user's original message
            intent: The classified intent
            entities: The extracted entities
            sentiment: The detected sentiment
            response: The chatbot's response
        """
        try:
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "message": message,
                "intent": intent,
                "entities": entities,
                "sentiment": sentiment,
                "response": response["text"],
                "confidence": response.get("confidence", 0.0)
            }
            
            # Log to file (for development/debugging)
            if logger.level <= logging.DEBUG:
                logger.debug(f"User interaction: {json.dumps(log_data, default=str)}")
            
            # In production, this would log to a database or analytics service
            # self._save_interaction_to_db(log_data)
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")


# Helper functions for translations

def _translate_risk_tolerance(risk_tolerance: str, language: str) -> str:
    """Translate risk tolerance level to specified language."""
    translations = {
        "conservative": {"en": "Conservative", "sw": "Mhafidhina"},
        "moderate": {"en": "Moderate", "sw": "Wastani"},
        "aggressive": {"en": "Aggressive", "sw": "Jasiri"}
    }
    
    if risk_tolerance.lower() in translations:
        return translations[risk_tolerance.lower()].get(language, risk_tolerance)
    return risk_tolerance

def _translate_investment_horizon(horizon: str, language: str) -> str:
    """Translate investment horizon to specified language."""
    translations = {
        "short": {"en": "Short-term (less than 3 years)", "sw": "Muda mfupi (chini ya miaka 3)"},
        "medium": {"en": "Medium-term (3-7 years)", "sw": "Muda wa kati (miaka 3-7)"},
        "long": {"en": "Long-term (more than 7 years)", "sw": "Muda mrefu (zaidi ya miaka 7)"}
    }
    
    if horizon.lower() in translations:
        return translations[horizon.lower()].get(language, horizon)
    return horizon

def _translate_asset_type(asset_type: str, language: str) -> str:
    """Translate asset types to specified language."""
    translations = {
        "government_bonds": {
            "en": "Government Bonds and Treasury Bills", 
            "sw": "Dhamana za Serikali na Hawala za Hazina"
        },
        "corporate_bonds": {
            "en": "Corporate Bonds", 
            "sw": "Dhamana za Kampuni"
        },
        "blue_chip_stocks": {
            "en": "Blue Chip Stocks (e.g., Safaricom, KCB, Equity)", 
            "sw": "Hisa za Kampuni Kubwa (mfano, Safaricom, KCB, Equity)"
        },
        "growth_stocks": {
            "en": "Growth Stocks", 
            "sw": "Hisa za Ukuaji"
        },
        "money_market_funds": {
            "en": "Money Market Funds", 
            "sw": "Hazina za Uwekezaji za Pesa za Soko"
        },
        "balanced_funds": {
            "en": "Balanced Funds", 
            "sw": "Hazina za Uwekezaji Zilizosawazishwa"
        },
        "real_estate": {
            "en": "Real Estate Investments", 
            "sw": "Uwekezaji wa Mali Isiyohamishika"
        }
    }
    
    if asset_type in translations:
        return translations[asset_type].get(language, asset_type)
    return asset_type
