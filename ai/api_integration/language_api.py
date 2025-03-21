import os
import re
from typing import Dict, List, Optional, Tuple, Union
import requests
import json
from collections import Counter

# Try importing language processing libraries, with fallbacks
try:
    import nltk
    from nltk.tokenize import word_tokenize
    nltk.download('punkt', quiet=True)
except ImportError:
    print("NLTK not available, using basic tokenization")
    word_tokenize = lambda text: text.split()

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from transformers import AutoModelForTokenClassification, AutoModelForMaskedLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Transformers library not available, using fallback methods")
    TRANSFORMERS_AVAILABLE = False

class LanguageAPI:
    """
    API for language detection, processing, and translation in the PesaGuru chatbot.
    Supports English and Swahili languages for financial advisory.
    """
    
    # Common Swahili words for language detection
    SWAHILI_COMMON_WORDS = {
        "na", "kwa", "ya", "la", "ni", "wa", "hii", "huo", "kuwa", "katika", 
        "kama", "tu", "za", "hapa", "sana", "lakini", "pia", "hadi", "wewe", "kwamba",
        "pesa", "fedha", "akiba", "benki", "faida", "uwekezaji", "mkopo", "biashara"
    }
    
    # Common English words for language detection
    ENGLISH_COMMON_WORDS = {
        "the", "and", "to", "of", "a", "in", "is", "that", "for", "it", 
        "with", "as", "on", "be", "at", "this", "by", "from", "have", "or",
        "money", "bank", "investment", "loan", "interest", "savings", "business", "finance"
    }
    
    # Swahili-English financial terms dictionary
    FINANCIAL_TERMS = {
        # Swahili to English
        "pesa": "money",
        "fedha": "finances",
        "akiba": "savings",
        "benki": "bank",
        "faida": "profit/interest",
        "uwekezaji": "investment",
        "mkopo": "loan",
        "biashara": "business",
        "hisa": "shares",
        "usalama": "security",
        "bima": "insurance",
        "mtaji": "capital",
        "bajeti": "budget",
        "mapato": "income",
        "matumizi": "expenses",
        "malipo": "payment",
        "risiti": "receipt",
        "deni": "debt",
        "riba": "interest rate",
        "amana": "deposit"
    }
    
    def __init__(self, use_transformers: bool = True):
        """
        Initialize the Language API.
        
        Args:
            use_transformers (bool): Whether to use the transformers library for NLP tasks.
                                     If False, will use simpler fallback methods.
        """
        self.use_transformers = use_transformers and TRANSFORMERS_AVAILABLE
        self.models = {}
        
        # Load NLP models if using transformers
        if self.use_transformers:
            self._load_nlp_models()
    
    def _load_nlp_models(self) -> None:
        """Load the required NLP models for language processing."""
        try:
            print("Loading language models...")
            
            # Language detection model
            self.models["lang_detection"] = pipeline(
                "text-classification", 
                model="papluca/xlm-roberta-base-language-detection"
            )
            
            # English sentiment analysis
            self.models["sentiment_en"] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Intent recognition - for financial intents
            self.models["intent"] = pipeline(
                "text-classification",
                model="joeddav/distilbert-base-uncased-go-emotions-student"
            )
            
            # Named entity recognition for English
            self.models["ner_en"] = pipeline(
                "ner",
                model="dslim/bert-base-NER"
            )
            
            # Masked language model for text completion (English)
            self.models["fill_mask_en"] = pipeline(
                "fill-mask",
                model="distilbert-base-uncased"
            )
            
            print("Language models loaded successfully.")
        except Exception as e:
            print(f"Error loading language models: {e}")
            self.use_transformers = False
    
    def detect_language(self, text: str) -> str:
        """
        Detect whether the input text is in English, Swahili, or mixed.
        
        Args:
            text (str): The input text to analyze
            
        Returns:
            str: 'en' for English, 'sw' for Swahili, 'mixed' for code-switching
        """
        if not text:
            return "en"  # Default to English for empty text
        
        if self.use_transformers and "lang_detection" in self.models:
            try:
                result = self.models["lang_detection"](text)[0]
                if result["label"] == "en":
                    return "en"
                elif result["label"] == "sw":
                    return "sw"
                else:
                    # If the model returns another language, use the rule-based approach as a fallback
                    pass
            except Exception as e:
                print(f"Error in language detection model: {e}")
        
        # Fallback to rule-based approach
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return "en"
        
        sw_count = sum(1 for word in words if word in self.SWAHILI_COMMON_WORDS)
        en_count = sum(1 for word in words if word in self.ENGLISH_COMMON_WORDS)
        
        sw_ratio = sw_count / len(words) if words else 0
        en_ratio = en_count / len(words) if words else 0
        
        if sw_ratio > 0.3 and en_ratio > 0.3:
            return "mixed"
        elif sw_ratio > en_ratio:
            return "sw"
        else:
            return "en"
    
    def analyze_sentiment(self, text: str, language: Optional[str] = None) -> Dict:
        """
        Analyze the sentiment of the input text.
        
        Args:
            text (str): The input text to analyze
            language (str, optional): Language code ('en' or 'sw'). If None, will be auto-detected.
            
        Returns:
            Dict: Sentiment analysis result with 'label' and 'score' keys
        """
        if not language:
            language = self.detect_language(text)
        
        if self.use_transformers and "sentiment_en" in self.models:
            try:
                # For Swahili, translate to English first
                if language == "sw" or language == "mixed":
                    text = self.translate_to_english(text)
                
                return self.models["sentiment_en"](text)[0]
            except Exception as e:
                print(f"Error in sentiment analysis: {e}")
        
        # Fallback: Simple rule-based sentiment
        positive_words = {
            "good", "great", "excellent", "amazing", "wonderful", "profit", "gain", "increase",
            "nzuri", "bora", "faida", "zuri", "safi", "kubwa", "zaidi"
        }
        negative_words = {
            "bad", "poor", "terrible", "awful", "failure", "loss", "decrease", "drop",
            "mbaya", "hasara", "hatari", "punguza", "chini", "kushuka", "duni"
        }
        
        words = text.lower().split()
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        
        if pos_count > neg_count:
            return {"label": "POSITIVE", "score": 0.7}
        elif neg_count > pos_count:
            return {"label": "NEGATIVE", "score": 0.7}
        else:
            return {"label": "NEUTRAL", "score": 0.5}
    
    def extract_entities(self, text: str, language: Optional[str] = None) -> List[Dict]:
        """
        Extract named entities from the input text, focusing on financial entities.
        
        Args:
            text (str): The input text to analyze
            language (str, optional): Language code ('en' or 'sw'). If None, will be auto-detected.
            
        Returns:
            List[Dict]: List of extracted entities with their types
        """
        if not language:
            language = self.detect_language(text)
        
        if self.use_transformers and "ner_en" in self.models:
            try:
                # For Swahili, translate to English first
                if language == "sw" or language == "mixed":
                    text = self.translate_to_english(text)
                
                entities = self.models["ner_en"](text)
                
                # Group entities properly
                grouped_entities = []
                current_entity = None
                
                for entity in entities:
                    if current_entity is None or entity["entity"].startswith("B-"):
                        if current_entity:
                            grouped_entities.append(current_entity)
                        current_entity = {
                            "word": entity["word"],
                            "entity": entity["entity"][2:],  # Remove B- or I- prefix
                            "score": entity["score"]
                        }
                    elif entity["entity"].startswith("I-") and current_entity:
                        current_entity["word"] += " " + entity["word"]
                        current_entity["score"] = (current_entity["score"] + entity["score"]) / 2
                
                if current_entity:
                    grouped_entities.append(current_entity)
                
                return grouped_entities
            except Exception as e:
                print(f"Error in entity extraction: {e}")
        
        # Fallback: Simple rule-based entity extraction for financial context
        entities = []
        
        # Extract amounts of money
        money_patterns = r'(\d+(?:,\d+)*(?:\.\d+)?\s*(?:KES|Ksh|Kshs|shillings?|shilingi))|(?:KES|Ksh|Kshs|shillings?|shilingi)\s*(\d+(?:,\d+)*(?:\.\d+)?)'
        money_matches = re.finditer(money_patterns, text, re.IGNORECASE)
        for match in money_matches:
            entities.append({
                "word": match.group(0),
                "entity": "MONEY",
                "score": 0.8
            })
        
        # Extract dates
        date_patterns = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4}'
        date_matches = re.finditer(date_patterns, text, re.IGNORECASE)
        for match in date_matches:
            entities.append({
                "word": match.group(0),
                "entity": "DATE",
                "score": 0.8
            })
        
        # Extract percentages
        percentage_patterns = r'\d+(?:\.\d+)?\s*%'
        percentage_matches = re.finditer(percentage_patterns, text)
        for match in percentage_matches:
            entities.append({
                "word": match.group(0),
                "entity": "PERCENTAGE",
                "score": 0.9
            })
        
        # Extract financial instruments
        financial_terms = ["stock", "bond", "share", "dividend", "interest", "loan", "deposit", "mortgage",
                          "hisa", "dhamana", "faida", "riba", "mkopo", "amana", "rehani"]
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in financial_terms:
                context = words[max(0, i-2):min(len(words), i+3)]
                entities.append({
                    "word": word,
                    "entity": "FINANCIAL_TERM",
                    "score": 0.7
                })
        
        return entities
    
    def identify_intent(self, text: str, language: Optional[str] = None) -> Dict:
        """
        Identify the financial intent in the input text.
        
        Args:
            text (str): The input text to analyze
            language (str, optional): Language code ('en' or 'sw'). If None, will be auto-detected.
            
        Returns:
            Dict: Intent with confidence score
        """
        if not language:
            language = self.detect_language(text)
        
        # Translate to English if needed
        if language == "sw" or language == "mixed":
            text = self.translate_to_english(text)
        
        # Financial intents dictionary with patterns
        financial_intents = {
            "investment_info": [
                r'\b(?:invest|investment|investing|stock|shares|bonds|securities|market|nse|returns|dividend)\b',
                r'\b(?:uwekezaji|kuwekeza|hisa|dhamana|soko|faida)\b'
            ],
            "loan_inquiry": [
                r'\b(?:loan|borrow|borrowing|credit|mortgage|interest.*rate|repayment|term|tenure)\b',
                r'\b(?:mkopo|kukopa|mikopo|riba|malipo|mkopeshaji)\b'
            ],
            "savings_advice": [
                r'\b(?:save|saving|savings|account|deposit|interest|future|goal|plan|budget)\b',
                r'\b(?:akiba|kuweka|amana|faida|lengo|mpango|bajeti)\b'
            ],
            "budget_planning": [
                r'\b(?:budget|plan|planning|expense|expenditure|income|spending|allocation)\b',
                r'\b(?:bajeti|mpango|matumizi|mapato|mgao)\b'
            ],
            "account_info": [
                r'\b(?:account|balance|statement|transaction|history|check|status|details)\b',
                r'\b(?:akaunti|salio|taarifa|muamala|historia|angalia|hali|maelezo)\b'
            ],
            "market_update": [
                r'\b(?:market|stock|price|value|performance|index|trend|outlook|forecast|update|news)\b',
                r'\b(?:soko|hisa|bei|thamani|utendaji|fahirisi|mwelekeo|habari)\b'
            ],
            "insurance_inquiry": [
                r'\b(?:insurance|insure|cover|policy|premium|protection|risk|claim)\b',
                r'\b(?:bima|usalama|sera|malipo|hatari|dai)\b'
            ],
            "tax_advice": [
                r'\b(?:tax|taxation|deduction|return|filing|compliance|kra|income tax)\b',
                r'\b(?:ushuru|kodi|makato|faili|kuwasilisha|mapato|kra)\b'
            ],
            "retirement_planning": [
                r'\b(?:retire|retirement|pension|fund|future|old age|plan)\b',
                r'\b(?:kustaafu|pensheni|hazina|mipango|uzee|mpango)\b'
            ],
            "crypto_inquiry": [
                r'\b(?:crypto|cryptocurrency|bitcoin|ethereum|blockchain|digital currency|token)\b',
                r'\b(?:sarafu ya dijitali|bitcoini|blockchain)\b'
            ],
            "general_greeting": [
                r'\b(?:hello|hi|hey|good morning|good afternoon|good evening|greetings)\b',
                r'\b(?:jambo|habari|hujambo|sijambo|mambo|salama)\b'
            ],
            "general_help": [
                r'\b(?:help|assist|support|guide|how can you|how do I)\b',
                r'\b(?:saidia|nisaidie|usaidizi|elekeza|vipi)\b'
            ]
        }
        
        # Check pattern matches for each intent
        intent_scores = {}
        for intent, patterns in financial_intents.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    intent_scores[intent] = intent_scores.get(intent, 0) + len(matches)
        
        # If no patterns match, use the transformers model if available
        if not intent_scores and self.use_transformers and "intent" in self.models:
            try:
                model_output = self.models["intent"](text)[0]
                # Map the emotion model output to financial intents
                emotion_to_intent = {
                    "admiration": "general_help",
                    "approval": "general_help",
                    "curiosity": "general_inquiry",
                    "desire": "investment_info",
                    "fear": "risk_assessment",
                    "confusion": "general_help",
                    "surprise": "market_update"
                }
                intent = emotion_to_intent.get(model_output["label"], "general_inquiry")
                return {"intent": intent, "confidence": model_output["score"]}
            except Exception as e:
                print(f"Error in intent identification model: {e}")
                return {"intent": "general_inquiry", "confidence": 0.5}
        
        # Return the intent with the highest score, or default to general inquiry
        if intent_scores:
            max_intent = max(intent_scores, key=intent_scores.get)
            # Normalize the confidence score between 0 and 1
            max_score = min(intent_scores[max_intent] / 3, 1.0)
            return {"intent": max_intent, "confidence": max_score}
        else:
            return {"intent": "general_inquiry", "confidence": 0.5}
    
    def translate_to_english(self, text: str) -> str:
        """
        Translate Swahili text to English.
        
        Args:
            text (str): The input text in Swahili or mixed language
            
        Returns:
            str: Translated text in English
        """
        # First try word-by-word translation for financial terms
        words = text.split()
        for i, word in enumerate(words):
            lower_word = word.lower()
            if lower_word in self.FINANCIAL_TERMS:
                words[i] = self.FINANCIAL_TERMS[lower_word]
        
        # If more than 50% of words were translated, return the result
        translated_words = [w for w in words if any(c.isalpha() for c in w)]
        english_words = [w for w in translated_words if w.lower() in self.ENGLISH_COMMON_WORDS 
                         or w.lower() in [v.lower() for v in self.FINANCIAL_TERMS.values()]]
        
        if len(english_words) / len(translated_words) > 0.5 if translated_words else 0:
            return " ".join(words)
        
        # Otherwise, try using a translation API or service
        try:
            # This is a placeholder for an actual API call
            # In a real implementation, you would use Google Translate API, Microsoft Translator, etc.
            # For now, we'll just return the original text
            print("Translation API call would be made here")
            return text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def translate_to_swahili(self, text: str) -> str:
        """
        Translate English text to Swahili.
        
        Args:
            text (str): The input text in English
            
        Returns:
            str: Translated text in Swahili
        """
        # This is similar to translate_to_english but in reverse
        # In a real implementation, you would use a translation API
        print("Translation API call would be made here")
        return text
    
    def handle_sheng_dialect(self, text: str) -> str:
        """
        Process text that may contain Sheng (Swahili-English slang).
        
        Args:
            text (str): The input text that may contain Sheng
            
        Returns:
            str: Standardized text in either Swahili or English
        """
        # Sheng to standard Swahili/English dictionary
        sheng_terms = {
            "pesa": "money",
            "doh": "money",
            "mullah": "money",
            "dala": "money",
            "kitu": "something",
            "fiti": "fit/good",
            "poa": "good/cool",
            "noma": "bad/difficult",
            "dabo": "double",
            "rada": "awareness",
            "moti": "money",
            "chapa": "money",
            "kata": "broke/no money",
            "chapaa": "money",
            "maniado": "money",
            "noti": "banknotes",
            "lipa": "pay",
            "nunua": "buy",
            "stinji": "money"
        }
        
        # Replace Sheng terms with standard terms
        words = text.split()
        for i, word in enumerate(words):
            lower_word = word.lower()
            if lower_word in sheng_terms:
                words[i] = sheng_terms[lower_word]
        
        return " ".join(words)
    
    def process_query(self, text: str) -> Dict:
        """
        Process a user query and return structured information.
        
        Args:
            text (str): The user's input text
            
        Returns:
            Dict: Structured information including language, intent, entities, etc.
        """
        result = {}
        
        # Handle Sheng dialect
        processed_text = self.handle_sheng_dialect(text)
        
        # Detect language
        language = self.detect_language(processed_text)
        result["language"] = language
        result["original_text"] = text
        result["processed_text"] = processed_text
        
        # Identify intent
        intent_info = self.identify_intent(processed_text, language)
        result["intent"] = intent_info
        
        # Extract entities
        entities = self.extract_entities(processed_text, language)
        result["entities"] = entities
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(processed_text, language)
        result["sentiment"] = sentiment
        
        # Translate if needed
        if language == "sw" or language == "mixed":
            result["english_translation"] = self.translate_to_english(processed_text)
        
        return result


# Helper function to test the language API
def test_language_api(text: str):
    """Test the language API with the given text."""
    api = LanguageAPI(use_transformers=True)
    result = api.process_query(text)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    print("PesaGuru Language API")
    
    # Test with some example texts
    examples = [
        "I want to invest in the Nairobi Stock Exchange",
        "Nataka kuwekeza kwenye hisa za Safaricom",
        "How can I get a loan with low interest?",
        "Ninataka kupata mkopo wa riba nafuu",
        "What are the best savings accounts for me?",
        "Kuna akiba gani nzuri kwangu?",
        "Nataka kujua current price ya Safaricom shares",  # Mixed language
        "Can you tell me if Equity Bank stocks are a good investment?"
    ]
    
    for i, example in enumerate(examples):
        print(f"\nExample {i+1}: '{example}'")
        test_language_api(example)
