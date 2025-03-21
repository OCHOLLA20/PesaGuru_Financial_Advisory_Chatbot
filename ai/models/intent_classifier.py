import numpy as np
import pandas as pd
import pickle
import os
import json
import re
from typing import Dict, List, Tuple, Union, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
import joblib

# Conditionally import torch and transformers
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class IntentClassifier:
    """
    Intent classification model for PesaGuru chatbot.
    Detects user intentions from financial queries in English and Swahili.
    
    The classifier uses a hybrid approach:
    1. Rule-based classification for simple, common patterns
    2. ML models (RandomForest, SVM, etc.) for more complex queries
    3. Transformer models (BERT) for context-aware, multilingual intent detection
    """
    
    def __init__(self, model_path: str = None, 
                 bert_model_path: str = None,
                 use_rules: bool = True,
                 use_traditional_ml: bool = True,
                 use_bert: bool = True,
                 language: str = 'en',
                 confidence_threshold: float = 0.7,
                 context_aware: bool = True):
        """
        Initialize the intent classifier with specified models and settings.
        
        Args:
            model_path: Path to the traditional ML model (pickle file)
            bert_model_path: Path to the fine-tuned BERT model
            use_rules: Whether to use rule-based classification
            use_traditional_ml: Whether to use traditional ML models
            use_bert: Whether to use BERT model (requires transformers)
            language: Default language ('en' for English, 'sw' for Swahili)
            confidence_threshold: Minimum confidence score to accept a classification
            context_aware: Whether to use conversation context for classification
        """
        self.logger = logging.getLogger(__name__)
        self.use_rules = use_rules
        self.use_traditional_ml = use_traditional_ml
        self.use_bert = use_bert and TRANSFORMERS_AVAILABLE
        self.language = language
        self.confidence_threshold = confidence_threshold
        self.context_aware = context_aware
        
        # Set up paths relative to current file
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Load intent definitions
        self.load_intent_definitions()
        
        # Load rule-based patterns
        if self.use_rules:
            self.load_rule_patterns()
        
        # Load traditional ML model
        if self.use_traditional_ml and model_path:
            try:
                self.ml_model = joblib.load(model_path)
                self.vectorizer = joblib.load(os.path.join(os.path.dirname(model_path), 'vectorizer.pkl'))
                self.logger.info("Traditional ML model loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading traditional ML model: {e}")
                self.use_traditional_ml = False
        else:
            self.use_traditional_ml = False
        
        # Load BERT model if transformers is available
        if self.use_bert and bert_model_path:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(bert_model_path)
                self.bert_model = AutoModelForSequenceClassification.from_pretrained(bert_model_path)
                self.bert_model.eval()  # Set to evaluation mode
                self.logger.info("BERT model loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading BERT model: {e}")
                self.use_bert = False
        elif self.use_bert:
            try:
                # Use pre-trained model if custom model not provided
                model_name = 'distilbert-base-uncased'
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.bert_model = AutoModelForSequenceClassification.from_pretrained(model_name)
                self.bert_model.eval()
                self.logger.info(f"Pre-trained model {model_name} loaded as fallback")
            except Exception as e:
                self.logger.error(f"Error loading pre-trained model: {e}")
                self.use_bert = False
    
    def load_intent_definitions(self):
        """Load the intent definitions from configuration file or define defaults"""
        intent_file = os.path.join(self.base_path, '../data/intent_definitions.json')
        
        if os.path.exists(intent_file):
            try:
                with open(intent_file, 'r', encoding='utf-8') as f:
                    self.intents = json.load(f)
                self.logger.info(f"Loaded intent definitions from {intent_file}")
                return
            except Exception as e:
                self.logger.error(f"Error loading intent definitions: {e}")
        
        # Default intent definitions if file not found
        self.intents = {
            "investment_advice": {
                "description": "Questions about investment strategies and recommendations",
                "examples": ["Where should I invest my money?", "What are good investment options in Kenya?", 
                            "Best stocks to buy on NSE", "Is real estate a good investment?"],
                "swahili_examples": ["Niwekeze wapi pesa yangu?", "Uwekezaji gani ni bora nchini Kenya?", 
                                    "Hisa bora za kununua kwenye NSE", "Je, mali isiyohamishika ni uwekezaji mzuri?"]
            },
            "market_trends": {
                "description": "Queries about current market conditions and trends",
                "examples": ["How is the NSE performing today?", "What's happening with crypto prices?",
                            "Current interest rates in Kenya", "Forex exchange rates"],
                "swahili_examples": ["Je, NSE inafanya vipi leo?", "Bei ya cryptocurrency ikoje?",
                                    "Viwango vya riba nchini Kenya kwa sasa", "Viwango vya ubadilishaji wa fedha"]
            },
            "risk_assessment": {
                "description": "Questions about risk evaluation for investments",
                "examples": ["How risky is investing in stocks?", "What is my risk profile?",
                            "Is Bitcoin too risky?", "Safe investment options"],
                "swahili_examples": ["Hatari ya kuwekeza katika hisa ni gani?", "Wasifu wangu wa hatari ni upi?",
                                    "Je, Bitcoin ina hatari kubwa?", "Chaguo salama za uwekezaji"]
            },
            "loan_advice": {
                "description": "Queries about loans, interest rates, and repayment",
                "examples": ["What loan should I take?", "Compare interest rates for home loans",
                            "M-Shwari vs KCB M-Pesa", "How to pay off my loan faster"],
                "swahili_examples": ["Nikope wapi?", "Linganisha viwango vya riba kwa mikopo ya nyumba",
                                    "M-Shwari dhidi ya KCB M-Pesa", "Jinsi ya kulipa mkopo wangu haraka"]
            },
            "budget_planning": {
                "description": "Help with budgeting and expense management",
                "examples": ["Help me create a budget", "How can I save more money?",
                            "50/30/20 rule explanation", "Track my expenses"],
                "swahili_examples": ["Nisaidie kuunda bajeti", "Ninawezaje kuhifadhi pesa zaidi?",
                                    "Ufafanuzi wa kanuni ya 50/30/20", "Fuatilia matumizi yangu"]
            },
            "account_info": {
                "description": "Questions about account status and management",
                "examples": ["Show me my account balance", "Update my profile",
                            "Change my risk preferences", "Link my M-Pesa account"],
                "swahili_examples": ["Nionyeshe salio langu", "Sasisha wasifu wangu",
                                    "Badilisha mapendeleo yangu ya hatari", "Unganisha akaunti yangu ya M-Pesa"]
            },
            "general_query": {
                "description": "General questions about financial concepts",
                "examples": ["What is compound interest?", "Explain mutual funds",
                            "How does the NSE work?", "What are treasury bonds?"],
                "swahili_examples": ["Riba inayoongezeka ni nini?", "Eleza hazina za pamoja",
                                    "NSE inafanya kazi vipi?", "Hati za hazina ni nini?"]
            },
            "calculator_request": {
                "description": "Requests to use financial calculators",
                "examples": ["Calculate my retirement savings", "Use loan calculator",
                            "Show me investment growth calculator", "Calculate mortgage payment"],
                "swahili_examples": ["Kokotoa akiba yangu ya uzeeni", "Tumia kikokotoo cha mkopo",
                                    "Nionyeshe kikokotoo cha ukuaji wa uwekezaji", "Kokotoa malipo ya rehani"]
            },
            "greeting": {
                "description": "Simple greetings",
                "examples": ["Hello", "Hi there", "Good morning", "Hey PesaGuru"],
                "swahili_examples": ["Habari", "Hujambo", "Habari za asubuhi", "Mambo PesaGuru"]
            },
            "farewell": {
                "description": "Ending the conversation",
                "examples": ["Goodbye", "Thanks, bye", "See you later", "That's all for now"],
                "swahili_examples": ["Kwaheri", "Asante, kwaheri", "Tutaonana baadaye", "Hiyo tu kwa sasa"]
            }
        }
        
        self.logger.info("Using default intent definitions")
    
    def load_rule_patterns(self):
        """Load rule-based patterns for intent matching"""
        # Try to load from file first
        patterns_file = os.path.join(self.base_path, '../data/intent_patterns.json')
        
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
                self.logger.info(f"Loaded intent patterns from {patterns_file}")
                return
            except Exception as e:
                self.logger.error(f"Error loading intent patterns: {e}")
        
        # Default patterns if file not found
        self.rules = {
            "greeting": [
                r"\b(hello|hi|hey|good morning|good afternoon|good evening|greetings)\b",
                r"\b(habari|hujambo|jambo|mambo|salamu)\b"
            ],
            "farewell": [
                r"\b(bye|goodbye|see you|later|take care|thank you for your help)\b",
                r"\b(kwaheri|tutaonana|baadaye|asante kwa msaada wako)\b"
            ],
            "investment_advice": [
                r"\b(invest|investing|investment|stock|shares|bonds|mutual funds|etf|portfolio|diversify)\b",
                r"\b(wekeza|uwekezaji|hisa|hazina|msawa|mgao|faida|dhamana|soko|nse)\b"
            ],
            "market_trends": [
                r"\b(market|trend|stock price|exchange|rate|performance|nse|index|bear|bull|rally|crash)\b",
                r"\b(soko|bei|hisa|ubadilishaji|fedha|utendaji|mshamiri|anguka|panda)\b"
            ],
            "risk_assessment": [
                r"\b(risk|profile|assessment|evaluate|tolerance|volatility|conservative|aggressive)\b",
                r"\b(hatari|tathmini|vumilia|wasifu wa hatari|tahadhari|ghasia)\b"
            ],
            "loan_advice": [
                r"\b(loan|borrow|interest rate|mortgage|credit|repayment|term|installment|m-shwari|m-pesa|fuliza)\b",
                r"\b(mkopo|kopa|riba|rehani|mikopo|malipo|awamu|deni)\b"
            ],
            "budget_planning": [
                r"\b(budget|saving|expense|spend|track|plan|goal|emergency fund|income|salary)\b",
                r"\b(bajeti|kuhifadhi|matumizi|gharama|mpango|lengo|mshahara|mapato|matumizi)\b"
            ],
            "account_info": [
                r"\b(account|profile|settings|preferences|balance|update|password|security|details)\b",
                r"\b(akaunti|wasifu|mipangilio|salio|sasisha|nywila|usalama|maelezo)\b"
            ],
            "calculator_request": [
                r"\b(calculate|calculator|compute|simulation|estimate|project|forecast|predict)\b",
                r"\b(kokotoa|hesabu|simulisha|kikokotoo|kadiria|tabiri)\b"
            ],
            "general_query": [
                r"\b(what is|how does|explain|define|meaning of|difference between|compare|tell me about)\b",
                r"\b(ni nini|inafanyaje|eleza|maana ya|tofauti kati ya|linganisha|niambie kuhusu)\b"
            ]
        }
        
        self.logger.info("Using default intent patterns")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess the input text for classification
        
        Args:
            text: Input user query
            
        Returns:
            Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove extra whitespaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def predict_intent_rules(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict intent using rule-based pattern matching
        
        Args:
            text: Preprocessed user query
            
        Returns:
            List of (intent, confidence) tuples
        """
        results = []
        
        for intent, patterns in self.rules.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Calculate a simple confidence score based on the 
                    # ratio of matched words to total words
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    match_count = sum(len(match.split()) for match in matches)
                    total_words = len(text.split())
                    confidence = min(match_count / max(total_words, 1) * 1.5, 0.9)
                    
                    results.append((intent, confidence))
        
        # Sort by confidence
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:3]  # Return top 3 matches
    
    def predict_intent_ml(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict intent using traditional ML models
        
        Args:
            text: Preprocessed user query
            
        Returns:
            List of (intent, confidence) tuples
        """
        if not self.use_traditional_ml:
            return []
        
        try:
            # Transform text using vectorizer
            features = self.vectorizer.transform([text])
            
            # Get probabilities for each class
            probabilities = self.ml_model.predict_proba(features)[0]
            
            # Get class names
            class_names = self.ml_model.classes_
            
            # Create list of (intent, confidence) tuples
            results = [(intent, float(prob)) for intent, prob in zip(class_names, probabilities)]
            
            # Sort by confidence
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:3]  # Return top 3 matches
            
        except Exception as e:
            self.logger.error(f"Error in ML prediction: {e}")
            return []
    
    def predict_intent_bert(self, text: str) -> List[Tuple[str, float]]:
        """
        Predict intent using BERT model
        
        Args:
            text: Preprocessed user query
            
        Returns:
            List of (intent, confidence) tuples
        """
        if not self.use_bert:
            return []
        
        try:
            # Tokenize input
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
            
            # Make prediction
            with torch.no_grad():
                outputs = self.bert_model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=1)[0]
            
            # Convert to intent-confidence pairs
            results = []
            for i, prob in enumerate(probabilities):
                intent = self.bert_model.config.id2label[i]
                confidence = float(prob)
                results.append((intent, confidence))
            
            # Sort by confidence
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results[:3]  # Return top 3 matches
            
        except Exception as e:
            self.logger.error(f"Error in BERT prediction: {e}")
            return []
    
    def detect_language(self, text: str) -> str:
        """
        Detect whether the text is in English or Swahili
        
        Args:
            text: User query
            
        Returns:
            Language code ('en' or 'sw')
        """
        # Common Swahili words to detect language
        swahili_markers = [
            'habari', 'jambo', 'nini', 'sasa', 'kwaheri', 'asante', 'tafadhali', 
            'ndiyo', 'hapana', 'mimi', 'wewe', 'sisi', 'nyinyi', 'wao', 'hapa',
            'kwa', 'na', 'ya', 'wa', 'ni', 'tu', 'je', 'kuhusu', 'nataka', 'ninataka',
            'unataka', 'anasema', 'kutoka', 'mpaka', 'karibu', 'mbali', 'kwamba'
        ]
        
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        if not words:
            return self.language  # Default language if no words found
            
        # Count Swahili marker words
        swahili_count = sum(1 for word in words if word in swahili_markers)
        
        # If more than 15% of the words are Swahili markers, classify as Swahili
        if swahili_count > 0 and swahili_count / len(words) >= 0.15:
            return 'sw'
        
        return 'en'
    
    def ensemble_predictions(self, rule_results: List[Tuple[str, float]], 
                            ml_results: List[Tuple[str, float]],
                            bert_results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """
        Combine predictions from different methods
        
        Args:
            rule_results: Predictions from rule-based approach
            ml_results: Predictions from traditional ML
            bert_results: Predictions from BERT
            
        Returns:
            Combined list of (intent, confidence) tuples
        """
        # Combine all results into a dictionary
        intent_scores = {}
        
        # Determine weights based on available models
        methods_count = sum([bool(rule_results), bool(ml_results), bool(bert_results)])
        
        if methods_count == 0:
            return []
            
        # Adjust weights based on which methods are used
        if methods_count == 1:
            weights = {
                'rule': 1.0 if rule_results else 0,
                'ml': 1.0 if ml_results else 0,
                'bert': 1.0 if bert_results else 0
            }
        elif methods_count == 2:
            if rule_results and ml_results:
                weights = {'rule': 0.4, 'ml': 0.6, 'bert': 0}
            elif rule_results and bert_results:
                weights = {'rule': 0.3, 'ml': 0, 'bert': 0.7}
            else:  # ml and bert
                weights = {'rule': 0, 'ml': 0.4, 'bert': 0.6}
        else:  # All three methods
            weights = {'rule': 0.2, 'ml': 0.3, 'bert': 0.5}
        
        # Process rule-based results
        for intent, score in rule_results:
            if intent not in intent_scores:
                intent_scores[intent] = 0
            intent_scores[intent] += score * weights['rule']
        
        # Process ML results
        for intent, score in ml_results:
            if intent not in intent_scores:
                intent_scores[intent] = 0
            intent_scores[intent] += score * weights['ml']
        
        # Process BERT results
        for intent, score in bert_results:
            if intent not in intent_scores:
                intent_scores[intent] = 0
            intent_scores[intent] += score * weights['bert']
        
        # Convert back to list of tuples and sort
        results = [(intent, score) for intent, score in intent_scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def apply_context(self, results: List[Tuple[str, float]], context: Dict) -> List[Tuple[str, float]]:
        """
        Adjust intent predictions based on conversation context
        
        Args:
            results: List of (intent, confidence) tuples
            context: Conversation context
            
        Returns:
            Adjusted list of (intent, confidence) tuples
        """
        if not self.context_aware or not context:
            return results
        
        # Get the previous intents from context
        prev_intents = context.get('prev_intents', [])
        
        # If no previous intents, return original results
        if not prev_intents:
            return results
        
        # Define intent flow probabilities
        # This represents the likelihood of transitioning from one intent to another
        intent_flow = {
            'greeting': {
                'investment_advice': 0.3,
                'loan_advice': 0.3,
                'budget_planning': 0.2,
                'account_info': 0.1,
                'general_query': 0.1
            },
            'investment_advice': {
                'market_trends': 0.4,
                'risk_assessment': 0.3,
                'calculator_request': 0.2,
                'general_query': 0.1
            },
            'market_trends': {
                'investment_advice': 0.5,
                'general_query': 0.3,
                'farewell': 0.2
            },
            'risk_assessment': {
                'investment_advice': 0.4,
                'calculator_request': 0.3,
                'general_query': 0.2,
                'farewell': 0.1
            },
            'loan_advice': {
                'calculator_request': 0.4,
                'budget_planning': 0.3,
                'general_query': 0.2,
                'farewell': 0.1
            },
            'budget_planning': {
                'calculator_request': 0.4,
                'loan_advice': 0.3,
                'account_info': 0.2,
                'farewell': 0.1
            },
            'account_info': {
                'investment_advice': 0.3,
                'budget_planning': 0.3,
                'general_query': 0.2,
                'farewell': 0.2
            },
            'general_query': {
                'investment_advice': 0.2,
                'loan_advice': 0.2,
                'budget_planning': 0.2,
                'calculator_request': 0.2,
                'farewell': 0.2
            },
            'calculator_request': {
                'investment_advice': 0.3,
                'budget_planning': 0.3,
                'general_query': 0.2,
                'farewell': 0.2
            },
            'farewell': {
                'greeting': 0.6,
                'general_query': 0.4
            }
        }
        
        # Get the most recent intent
        last_intent = prev_intents[-1]
        
        # Get the flow probabilities for the last intent
        flow_probs = intent_flow.get(last_intent, {})
        
        # Adjust the confidence scores based on the flow probabilities
        adjusted_results = []
        for intent, confidence in results:
            # Get the flow probability from the last intent to this one
            flow_prob = flow_probs.get(intent, 0.1)
            
            # Adjust confidence: 70% original + 30% from flow probability
            adjusted_confidence = (0.7 * confidence) + (0.3 * flow_prob)
            
            adjusted_results.append((intent, adjusted_confidence))
        
        # Sort by adjusted confidence
        adjusted_results.sort(key=lambda x: x[1], reverse=True)
        
        return adjusted_results
    
    def classify(self, text: str, context: Dict = None) -> Dict:
        """
        Classify the user query to determine the intent
        
        Args:
            text: User query
            context: Conversation context (optional)
            
        Returns:
            Dictionary with classification results
        """
        # Empty text check
        if not text or not text.strip():
            return {
                "input": text,
                "language": self.language,
                "top_intents": [],
                "matched_intents": 0,
                "rule_based_results": [],
                "ml_results": [],
                "bert_results": []
            }
        
        # Detect language if not specified
        detected_lang = self.detect_language(text)
        
        # Preprocess the text
        preprocessed_text = self.preprocess_text(text)
        
        # Initialize results
        rule_results = []
        ml_results = []
        bert_results = []
        
        # Rule-based prediction
        if self.use_rules:
            rule_results = self.predict_intent_rules(preprocessed_text)
        
        # ML-based prediction
        if self.use_traditional_ml:
            ml_results = self.predict_intent_ml(preprocessed_text)
        
        # BERT-based prediction
        if self.use_bert:
            bert_results = self.predict_intent_bert(preprocessed_text)
        
        # Combine predictions from different methods
        combined_results = self.ensemble_predictions(rule_results, ml_results, bert_results)
        
        # Apply context if available
        if context and self.context_aware:
            final_results = self.apply_context(combined_results, context)
        else:
            final_results = combined_results
        
        # Get the top intents
        top_intents = []
        for intent, confidence in final_results:
            if confidence >= self.confidence_threshold:
                top_intents.append({
                    "intent": intent,
                    "confidence": confidence
                })
            
            # Only keep top 3 intents
            if len(top_intents) >= 3:
                break
        
        # If no intents match the threshold, use the top one anyway if available
        if not top_intents and final_results:
            top_intent, confidence = final_results[0]
            top_intents.append({
                "intent": top_intent,
                "confidence": confidence
            })
        
        # Format the response
        result = {
            "input": text,
            "language": detected_lang,
            "top_intents": top_intents,
            "matched_intents": len(top_intents),
            "rule_based_results": rule_results[:3] if rule_results else [],
            "ml_results": ml_results[:3] if ml_results else [],
            "bert_results": bert_results[:3] if bert_results else []
        }
        
        return result
    
    def train(self, training_data_path: str, output_path: str, model_type: str = 'rf', bert_model_name: str = None):
        """
        Train the intent classifier using labeled data
        
        Args:
            training_data_path: Path to the training data CSV file
            output_path: Directory to save the trained model
            model_type: Type of traditional ML model ('rf', 'svm', 'nb')
            bert_model_name: Base BERT model name for fine-tuning
        
        Returns:
            Boolean indicating success or failure
        """
        self.logger.info(f"Starting training with data from {training_data_path}")
        
        try:
            # Load training data
            data = pd.read_csv(training_data_path)
            
            # Check if required columns exist
            if 'text' not in data.columns or 'intent' not in data.columns:
                self.logger.error("Training data must have 'text' and 'intent' columns")
                return False
            
            # Preprocess text
            data['processed_text'] = data['text'].apply(self.preprocess_text)
            
            # Train traditional ML model
            if model_type in ['rf', 'svm', 'nb']:
                self.logger.info(f"Training {model_type} model")
                
                # Create TF-IDF vectorizer
                vectorizer = TfidfVectorizer(max_features=5000)
                X = vectorizer.fit_transform(data['processed_text'])
                y = data['intent']
                
                # Train model based on type
                if model_type == 'rf':
                    model = RandomForestClassifier(n_estimators=100, random_state=42)
                elif model_type == 'svm':
                    model = SVC(probability=True, random_state=42)
                else:  # 'nb'
                    model = MultinomialNB()
                
                model.fit(X, y)
                
                # Save model and vectorizer
                os.makedirs(output_path, exist_ok=True)
                joblib.dump(model, os.path.join(output_path, f'intent_classifier_{model_type}.pkl'))
                joblib.dump(vectorizer, os.path.join(output_path, 'vectorizer.pkl'))
                
                self.logger.info(f"Model saved to {output_path}")
                
                # Update current model
                self.ml_model = model
                self.vectorizer = vectorizer
                self.use_traditional_ml = True
            
            # Train/fine-tune BERT model
            if bert_model_name and TRANSFORMERS_AVAILABLE:
                self.logger.info(f"Fine-tuning BERT model {bert_model_name}")
                
                # This is a simplified example, actual BERT fine-tuning would use the
                # transformers library's Trainer class with a proper training loop
                try:
                    # Load base model and tokenizer
                    tokenizer = AutoTokenizer.from_pretrained(bert_model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(
                        bert_model_name, 
                        num_labels=len(data['intent'].unique())
                    )
                    
                    # Create label mapping
                    label_dict = {label: i for i, label in enumerate(data['intent'].unique())}
                    id2label = {i: label for label, i in label_dict.items()}
                    model.config.id2label = id2label
                    model.config.label2id = label_dict
                    
                    # Save label mapping
                    os.makedirs(output_path, exist_ok=True)
                    with open(os.path.join(output_path, 'label_mapping.json'), 'w') as f:
                        json.dump(label_dict, f)
                    
                    # Save tokenizer and model
                    bert_model_path = os.path.join(output_path, 'bert_model')
                    os.makedirs(bert_model_path, exist_ok=True)
                    tokenizer.save_pretrained(bert_model_path)
                    model.save_pretrained(bert_model_path)
                    
                    self.logger.info(f"BERT model saved to {bert_model_path}")
                    
                    # Update current BERT model
                    self.tokenizer = tokenizer
                    self.bert_model = model
                    self.use_bert = True
                    
                except Exception as e:
                    self.logger.error(f"Error in BERT fine-tuning: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in training: {e}")
            return False
    
    def evaluate(self, test_data_path: str) -> Dict:
        """
        Evaluate the classifier on test data
        
        Args:
            test_data_path: Path to the test data CSV file
            
        Returns:
            Dictionary with evaluation metrics
        """
        self.logger.info(f"Evaluating model with test data from {test_data_path}")
        
        try:
            # Load test data
            data = pd.read_csv(test_data_path)
            
            # Check if required columns exist
            if 'text' not in data.columns or 'intent' not in data.columns:
                self.logger.error("Test data must have 'text' and 'intent' columns")
                return {}
            
            # Classify each example
            predictions = []
            for i, row in data.iterrows():
                result = self.classify(row['text'])
                if result['top_intents']:
                    predicted_intent = result['top_intents'][0]['intent']
                else:
                    predicted_intent = 'unknown'
                
                predictions.append({
                    'text': row['text'],
                    'true_intent': row['intent'],
                    'predicted_intent': predicted_intent,
                    'correct': row['intent'] == predicted_intent
                })
            
            # Calculate accuracy
            correct = sum(1 for p in predictions if p['correct'])
            accuracy = correct / len(predictions) if predictions else 0
            
            # Calculate per-intent metrics
            intent_metrics = {}
            for intent in data['intent'].unique():
                intent_preds = [p for p in predictions if p['true_intent'] == intent]
                if intent_preds:
                    correct_intent = sum(1 for p in intent_preds if p['correct'])
                    intent_accuracy = correct_intent / len(intent_preds)
                    intent_metrics[intent] = {
                        'accuracy': intent_accuracy,
                        'count': len(intent_preds)
                    }
            
            # Calculate confusion matrix
            intents = sorted(list(data['intent'].unique()))
            confusion = {}
            for true_intent in intents:
                confusion[true_intent] = {}
                for pred_intent in intents:
                    confusion[true_intent][pred_intent] = 0
            
            for p in predictions:
                true_intent = p['true_intent']
                pred_intent = p['predicted_intent']
                if pred_intent in confusion.get(true_intent, {}):
                    confusion[true_intent][pred_intent] += 1
            
            # Return evaluation metrics
            return {
                'overall_accuracy': accuracy,
                'total_samples': len(predictions),
                'correct_predictions': correct,
                'intent_metrics': intent_metrics,
                'confusion_matrix': confusion
            }
            
        except Exception as e:
            self.logger.error(f"Error in evaluation: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize classifier with rule-based approach only (for demonstration)
    classifier = IntentClassifier(
        use_rules=True,
        use_traditional_ml=False,
        use_bert=False,
        confidence_threshold=0.6
    )
    
    # Test with English examples
    print("\nTesting English examples:")
    english_examples = [
        "What are the best investment options in Kenya?",
        "Compare interest rates between KCB and Equity Bank",
        "How is the NSE performing today?",
        "Help me create a monthly budget",
        "What's my risk profile?",
        "Calculate how much I need to save for retirement"
    ]
    
    for example in english_examples:
        result = classifier.classify(example)
        intents = [f"{i['intent']} ({i['confidence']:.2f})" for i in result['top_intents']]
        print(f"Query: {example}\nIntents: {', '.join(intents)}\n")
    
    # Test with Swahili examples
    print("\nTesting Swahili examples:")
    swahili_examples = [
        "Niwekeze wapi pesa yangu?",
        "Linganisha viwango vya riba kati ya KCB na Equity Bank",
        "Je, NSE inafanya vipi leo?",
        "Nisaidie kuunda bajeti ya kila mwezi",
        "Wasifu wangu wa hatari ni upi?",
        "Kokotoa kiasi ninahitaji kuhifadhi kwa ajili ya kustaafu"
    ]
    
    for example in swahili_examples:
        result = classifier.classify(example)
        intents = [f"{i['intent']} ({i['confidence']:.2f})" for i in result['top_intents']]
        print(f"Query: {example}\nIntents: {', '.join(intents)}\n")
