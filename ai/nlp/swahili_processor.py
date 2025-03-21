import re
import os
import json
import logging
from typing import List, Dict, Tuple, Set, Optional, Union

import nltk
import numpy as np
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("spaCy not available. Some NER features will be limited.")

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. Using simplified language processing.")

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Paths to data resources
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'ai', 'data')
SWAHILI_CORPUS_PATH = os.path.join(DATA_DIR, 'swahili_corpus.json')

# Load Swahili resources
def load_swahili_resources():
    """Load Swahili language resources for processing"""
    try:
        with open(SWAHILI_CORPUS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to load Swahili corpus: {str(e)}")
        # Return basic fallback data
        return {
            "stopwords": ["na", "kwa", "ya", "la", "wa", "ni", "za", "katika", 
                         "kama", "hii", "huo", "huu", "hiyo", "lakini", "pia", 
                         "au", "je", "hata", "sana", "tu"],
            "financial_terms": {
                "akiba": {"english": "savings", "category": "banking"},
                "benki": {"english": "bank", "category": "institution"},
                "mkopo": {"english": "loan", "category": "credit"},
                "riba": {"english": "interest", "category": "banking"},
                "hisa": {"english": "shares", "category": "investment"},
                "uwekezaji": {"english": "investment", "category": "investment"},
                "faida": {"english": "profit", "category": "business"},
                "hasara": {"english": "loss", "category": "business"},
                "M-Pesa": {"english": "M-Pesa", "category": "mobile_money"},
                "Fuliza": {"english": "Fuliza", "category": "mobile_credit"}
            },
            "financial_definitions": {},
            "common_words": [],
            "stemming_rules": {}
        }

# Load resources
SWAHILI_CORPUS = load_swahili_resources()
SWAHILI_STOPWORDS = set(SWAHILI_CORPUS.get("stopwords", []))
SWAHILI_FINANCIAL_TERMS = SWAHILI_CORPUS.get("financial_terms", {})
SWAHILI_STEMMING_RULES = SWAHILI_CORPUS.get("stemming_rules", {})

# Initialize NLP models if available
if TRANSFORMERS_AVAILABLE:
    try:
        # Use multilingual model that supports Swahili
        tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
        sentiment_model = pipeline(
            "sentiment-analysis",
            model="bert-base-multilingual-cased",
            tokenizer=tokenizer
        )
        MODELS_LOADED = True
    except Exception as e:
        logger.error(f"Failed to load transformer models: {str(e)}")
        MODELS_LOADED = False
else:
    MODELS_LOADED = False

# Initialize spaCy if available
if SPACY_AVAILABLE:
    try:
        # Use multilingual model
        nlp = spacy.load("xx_ent_wiki_sm")
        SPACY_LOADED = True
    except (OSError, IOError) as e:
        logger.error(f"Failed to load spaCy model: {str(e)}")
        SPACY_LOADED = False
else:
    SPACY_LOADED = False

class SwahiliProcessor:
    """
    Main class for processing Swahili text in the PesaGuru chatbot.
    Handles tokenization, normalization, and specialized financial text processing.
    """
    
    def __init__(self, use_stemming=True, remove_stopwords=True):
        """
        Initialize the Swahili processor.
        
        Args:
            use_stemming: Whether to apply stemming to Swahili words
            remove_stopwords: Whether to remove stopwords
        """
        self.use_stemming = use_stemming
        self.remove_stopwords = remove_stopwords
        self.stopwords = SWAHILI_STOPWORDS
        self.financial_terms = SWAHILI_FINANCIAL_TERMS
        
        # Load specialized Kenyan financial dictionaries
        self._load_kenyan_financial_data()
        
    def _load_kenyan_financial_data(self):
        """Load Kenya-specific financial data"""
        self.kenyan_banks = [
            "equity", "kcb", "cooperative bank", "benki ya Cooperative", 
            "absa", "stanbic", "ncba", "dtb", "family bank", "benki ya familia"
        ]
        
        self.mobile_money = [
            "m-pesa", "mpesa", "airtel money", "t-kash", "fuliza", 
            "m-shwari", "kcb-mpesa", "M-shwari"
        ]
        
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess Swahili text by cleaning and normalizing.
        
        Args:
            text: Input text in Swahili
            
        Returns:
            Preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Clean whitespace
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common Swahili contractions
        text = text.replace("s'na", "sina")
        text = text.replace("s'kui", "sikui")
        
        # Format currency mentions 
        text = re.sub(r'ksh\.?\s*(\d+[\d\,\.]*)', r'shilingi \1', text, flags=re.IGNORECASE)
        text = re.sub(r'kes\.?\s*(\d+[\d\,\.]*)', r'shilingi \1', text, flags=re.IGNORECASE)
        
        # Normalize M-Pesa variations
        text = re.sub(r'[mM]\s*[-]?\s*[pP][eE][sS][aA]', 'M-Pesa', text)
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Swahili text into words.
        
        Args:
            text: Preprocessed Swahili text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Apply preprocessing
        text = self.preprocess_text(text)
        
        # Simple tokenization by whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stopwords if enabled
        if self.remove_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords]
        
        # Apply stemming if enabled
        if self.use_stemming:
            tokens = [self.stem_word(t) for t in tokens]
            
        return tokens
    
    def stem_word(self, word: str) -> str:
        """
        Apply stemming to a Swahili word to get its root form.
        
        Args:
            word: A single Swahili word
            
        Returns:
            Stemmed form of the word
        """
        if not word or len(word) < 3:
            return word
            
        # Check if it's a known word with defined stem
        if word in SWAHILI_STEMMING_RULES:
            return SWAHILI_STEMMING_RULES[word]
        
        # Apply basic Swahili stemming rules
        # Common verb suffixes
        suffixes = ['wa', 'na', 'ni', 'ia', 'ika', 'isha', 'ea', 'lia', 'ana']
        
        for suffix in suffixes:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        
        return word
    
    def detect_language_mix(self, text: str) -> Dict[str, float]:
        """
        Detect the mix of Swahili and English in the input text.
        Useful for handling code-switching common in Kenyan communication.
        
        Args:
            text: Input text which may contain both Swahili and English
            
        Returns:
            Dictionary with estimated language percentages
        """
        if not text:
            return {"swahili": 0, "english": 0, "unknown": 100}
        
        tokens = re.findall(r'\b\w+\b', text.lower())
        if not tokens:
            return {"swahili": 0, "english": 0, "unknown": 100}
        
        # Count tokens that appear in Swahili word lists
        swahili_words = set(SWAHILI_CORPUS.get('common_words', []))
        swahili_words.update(self.stopwords)
        swahili_words.update(SWAHILI_FINANCIAL_TERMS.keys())
        
        swahili_count = sum(1 for t in tokens if t in swahili_words)
        
        # Simple English detection
        try:
            english_words = set(nltk.corpus.words.words()) if nltk.data.find('corpora/words') else set()
            english_count = sum(1 for t in tokens if t in english_words)
        except (LookupError, ImportError):
            # Fallback to basic English word detection
            common_english = {"the", "a", "an", "of", "in", "and", "is", "to", "for", "with", 
                             "bank", "money", "loan", "investment", "savings", "interest"}
            english_count = sum(1 for t in tokens if t in common_english)
        
        # Calculate percentages
        total = len(tokens)
        swahili_percent = (swahili_count / total) * 100
        english_percent = (english_count / total) * 100
        unknown_percent = 100 - swahili_percent - english_percent
        
        return {
            "swahili": round(swahili_percent, 1),
            "english": round(english_percent, 1),
            "unknown": round(unknown_percent, 1)
        }
    
    def identify_financial_entities(self, text: str) -> List[Dict[str, str]]:
        """
        Identify financial entities in Swahili text.
        
        Args:
            text: Preprocessed Swahili text
            
        Returns:
            List of identified entities with type and value
        """
        entities = []
        
        # Use spaCy for entity recognition if available
        if SPACY_LOADED:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append({"type": ent.label_, "text": ent.text})
        
        # Currency patterns (KES, Shilingi)
        currency_pattern = r'(shilingi|kes|ksh)[\s]*(\d[\d\,\.]*)'
        matches = re.finditer(currency_pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "type": "CURRENCY",
                "text": match.group(0),
                "amount": match.group(2),
                "currency": "KES"
            })
        
        # Percentage patterns
        percentage_pattern = r'(asilimia[\s]*(\d[\d\,\.]*)|(\d[\d\,\.]*)[\s]*asilimia|(\d[\d\,\.]*)[\s]*\%)'
        matches = re.finditer(percentage_pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "type": "PERCENTAGE",
                "text": match.group(0)
            })
        
        # Detect financial institutions
        for bank in self.kenyan_banks:
            if bank in text.lower():
                entities.append({
                    "type": "FINANCIAL_INSTITUTION",
                    "text": bank
                })
        
        # Detect mobile money services
        for service in self.mobile_money:
            if service in text.lower():
                entities.append({
                    "type": "MOBILE_MONEY",
                    "text": service
                })
        
        # Detect financial terms
        for term, details in self.financial_terms.items():
            if term.lower() in text.lower():
                entities.append({
                    "type": "FINANCIAL_TERM",
                    "text": term,
                    "category": details.get("category", "")
                })
        
        return entities
    
    def analyze_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        """
        Analyze sentiment in Swahili text, focused on financial context.
        
        Args:
            text: Swahili text to analyze
            
        Returns:
            Dictionary with sentiment label and confidence score
        """
        # Default response
        default_response = {"label": "neutral", "score": 0.5}
        
        if not text or not MODELS_LOADED:
            return default_response
            
        try:
            # Use transformer-based sentiment analysis if available
            result = sentiment_model(text)
            
            if result and isinstance(result, list) and len(result) > 0:
                label = result[0]["label"]
                score = result[0]["score"]
                
                # Map to simpler categories
                simplified_label = "neutral"
                if "positive" in label.lower():
                    simplified_label = "positive"
                elif "negative" in label.lower():
                    simplified_label = "negative"
                
                return {
                    "label": simplified_label,
                    "score": score
                }
                
            return default_response
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return default_response
    
    def translate_financial_term(self, term: str, target_lang: str = "en") -> str:
        """
        Translate financial term between Swahili and English.
        
        Args:
            term: Financial term to translate
            target_lang: Target language code ('en' or 'sw')
            
        Returns:
            Translated term if available, otherwise the original term
        """
        term = term.lower()
        
        # Swahili to English
        if target_lang == "en":
            # Check financial terms dictionary
            for sw_term, details in self.financial_terms.items():
                if sw_term.lower() == term:
                    return details.get("english", term)
            
            # Common financial terms mapping
            sw_to_en = {
                "benki": "bank",
                "akiba": "savings",
                "mkopo": "loan",
                "riba": "interest",
                "hisa": "shares/stocks",
                "uwekezaji": "investment",
                "faida": "profit",
                "hasara": "loss",
                "fedha": "money",
                "malipo": "payment",
                "ushuru": "tax",
                "bima": "insurance",
                "mfuko wa uwekezaji": "investment fund",
                "hati ya dhamana": "bond",
                "bajeti": "budget",
                "mtaji": "capital",
                "sarafu": "currency"
            }
            
            return sw_to_en.get(term, term)
            
        # English to Swahili
        elif target_lang == "sw":
            # Create reverse mapping
            en_to_sw = {}
            for sw_term, details in self.financial_terms.items():
                if "english" in details:
                    en_to_sw[details["english"].lower()] = sw_term
            
            # Add common terms
            basic_en_to_sw = {
                "bank": "benki",
                "savings": "akiba",
                "loan": "mkopo",
                "interest": "riba",
                "shares": "hisa",
                "stocks": "hisa",
                "investment": "uwekezaji",
                "profit": "faida",
                "loss": "hasara",
                "money": "fedha",
                "payment": "malipo",
                "tax": "ushuru",
                "insurance": "bima",
                "investment fund": "mfuko wa uwekezaji",
                "bond": "hati ya dhamana", 
                "budget": "bajeti",
                "capital": "mtaji",
                "currency": "sarafu"
            }
            
            # Combine both dictionaries
            en_to_sw.update(basic_en_to_sw)
            
            return en_to_sw.get(term, term)
            
        return term
    
    def get_financial_term_definition(self, term: str, language: str = "sw") -> Optional[str]:
        """
        Get definition for a financial term in Swahili or English.
        
        Args:
            term: Financial term to define
            language: Language for the definition ('sw' or 'en')
            
        Returns:
            Definition of the term if available, otherwise None
        """
        term = term.lower()
        
        # Check financial dictionary
        financial_definitions = SWAHILI_CORPUS.get("financial_definitions", {})
        if term in financial_definitions:
            term_data = financial_definitions[term]
            
            # Return definition in requested language
            if language == "sw" and "definition_sw" in term_data:
                return term_data["definition_sw"]
            elif language == "en" and "definition_en" in term_data:
                return term_data["definition_en"]
            
        # Basic Swahili financial definitions
        sw_financial_definitions = {
            "akiba": {
                "sw": "Fedha ambazo mtu huweka kwa matumizi ya baadaye.",
                "en": "Money that one sets aside for future use."
            },
            "riba": {
                "sw": "Malipo ya ziada yanayolipwa kwa kutumia pesa za mtu mwingine, haswa katika mkopo.",
                "en": "Additional payment made for using someone else's money, especially in a loan."
            },
            "uwekezaji": {
                "sw": "Kitendo cha kutumia fedha katika biashara au mradi kwa matarajio ya kupata faida.",
                "en": "The act of putting money into business or projects with the expectation of profit."
            },
            "hisa": {
                "sw": "Sehemu ya umiliki katika kampuni, inayompa mmiliki haki ya kupokea gawio.",
                "en": "A portion of ownership in a company, giving the owner the right to receive dividends."
            },
            "mkopo": {
                "sw": "Fedha ambazo mtu au taasisi hukopa na kuzilipa baadaye, mara nyingi na riba.",
                "en": "Money that a person or institution borrows and repays later, often with interest."
            },
            "m-pesa": {
                "sw": "Huduma ya fedha ya simu ya mkononi inayoruhusu watumiaji kutuma na kupokea pesa.",
                "en": "Mobile money service that allows users to send and receive money via mobile phone."
            },
            "fuliza": {
                "sw": "Huduma ya M-Pesa inayoruhusu watumiaji kukopa fedha wakati akaunti zao zimeishiwa.",
                "en": "M-Pesa service that allows users to borrow money when their accounts are depleted."
            }
        }
        
        # Check basic dictionary
        if term in sw_financial_definitions:
            return sw_financial_definitions[term].get(language, None)
            
        return None

    def correct_spelling(self, text: str) -> str:
        """
        Correct common spelling errors in Swahili financial terms.
        
        Args:
            text: Input text that might contain spelling errors
            
        Returns:
            Text with corrected spelling
        """
        # Common misspellings in Swahili financial terms
        corrections = {
            # General financial terms
            "bengi": "benki",
            "akyba": "akiba",
            "mkopu": "mkopo",
            "reba": "riba",
            "uwekesaji": "uwekezaji",
            "bejeti": "bajeti",
            
            # M-Pesa related terms
            "empesa": "M-Pesa",
            "fulisa": "Fuliza",
            "mpeza": "M-Pesa",
            
            # Banks
            "ekwiti": "Equity",
            "kcb benki": "KCB Bank",
            "koperativ": "Cooperative",
            
            # Investment terms
            "hiza": "hisa",
            "hizazako": "hisa zako"
        }
        
        # Replace misspelled words
        for error, correction in corrections.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(error) + r'\b'
            text = re.sub(pattern, correction, text, flags=re.IGNORECASE)
            
        return text
    
    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process a financial query in Swahili, extracting meaningful information.
        
        Args:
            query: User's query in Swahili
            
        Returns:
            Dictionary with processed information about the query
        """
        # Check if input is valid
        if not query or not isinstance(query, str):
            return {"error": "Invalid input"}
            
        # Correct spelling
        corrected_query = self.correct_spelling(query)
        
        # Preprocess text
        preprocessed = self.preprocess_text(corrected_query)
        
        # Tokenize
        tokens = self.tokenize(preprocessed)
        
        # Detect language mix
        language_mix = self.detect_language_mix(preprocessed)
        
        # Identify financial entities
        entities = self.identify_financial_entities(preprocessed)
        
        # Analyze sentiment
        sentiment = self.analyze_sentiment(preprocessed)
        
        # Return processed data
        return {
            "original_query": query,
            "corrected_query": corrected_query,
            "preprocessed": preprocessed,
            "tokens": tokens,
            "language_mix": language_mix,
            "entities": entities,
            "sentiment": sentiment
        }
    
    def handle_code_switching(self, text: str) -> Dict[str, any]:
        """
        Handle code-switching (mixing Swahili and English) in financial conversations.
        
        Args:
            text: Input text with potential code-switching
            
        Returns:
            Dictionary with processed information for chatbot response
        """
        # Detect language mix
        language_mix = self.detect_language_mix(text)
        dominant_language = max(language_mix.items(), key=lambda x: x[1] if x[0] != "unknown" else 0)[0]
        
        # Process based on dominant language
        if dominant_language == "swahili":
            # Process as primarily Swahili
            tokens = self.tokenize(text)
            
            # Identify any English financial terms that need translation
            english_terms = []
            for token in tokens:
                # If token might be English (not in Swahili dictionary)
                if token not in SWAHILI_CORPUS.get('common_words', []) and token not in self.stopwords:
                    # Try to translate it
                    swahili_equivalent = self.translate_financial_term(token, "sw")
                    if swahili_equivalent != token:
                        english_terms.append((token, swahili_equivalent))
        
            return {
                "dominant_language": "swahili",
                "english_terms": english_terms,
                "language_mix": language_mix
            }
            
        elif dominant_language == "english":
            # Process as primarily English with some Swahili
            # Identify Swahili terms that might need explanation
            tokens = text.lower().split()
            swahili_terms = []
            
            for token in tokens:
                if token in self.financial_terms:
                    english_equivalent = self.translate_financial_term(token, "en")
                    swahili_terms.append((token, english_equivalent))
            
            return {
                "dominant_language": "english",
                "swahili_terms": swahili_terms,
                "language_mix": language_mix
            }
        
        return {
            "dominant_language": "unknown",
            "language_mix": language_mix
        }

    def get_kenya_specific_context(self, text: str) -> Dict[str, any]:
        """
        Extract Kenya-specific financial context from text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with Kenya-specific financial context
        """
        context = {"kenya_specific_terms": []}
        
        # Check for Kenya-specific financial terms
        kenya_specific_terms = {
            "M-Pesa": "Mobile money service by Safaricom",
            "Fuliza": "Overdraft facility for M-Pesa",
            "M-Shwari": "Mobile savings and loan product",
            "KCB-M-Pesa": "Mobile loan product by KCB and Safaricom",
            "Stawi": "Digital credit for SMEs in Kenya",
            "chama": "Savings group or investment club",
            "harambee": "Community fundraising",
            "NSE": "Nairobi Securities Exchange",
            "CBK": "Central Bank of Kenya",
            "bodaboda": "Motorcycle transportation business"
        }
        
        for term, description in kenya_specific_terms.items():
            if term.lower() in text.lower():
                context["kenya_specific_terms"].append({
                    "term": term,
                    "description": description
                })
        
        return context


# Create a singleton instance for easy import
swahili_processor = SwahiliProcessor()

# Helper functions for easier usage in the chatbot
def preprocess(text: str) -> str:
    """Preprocess Swahili text"""
    return swahili_processor.preprocess_text(text)

def tokenize(text: str) -> List[str]:
    """Tokenize Swahili text"""
    return swahili_processor.tokenize(text)

def analyze(query: str) -> Dict[str, any]:
    """Analyze a Swahili query"""
    return swahili_processor.process_query(query)

def get_financial_definition(term: str, language: str = "sw") -> Optional[str]:
    """Get definition for a financial term"""
    return swahili_processor.get_financial_term_definition(term, language)

def translate_term(term: str, target_lang: str = "en") -> str:
    """Translate a financial term"""
    return swahili_processor.translate_financial_term(term, target_lang)

def detect_languages(text: str) -> Dict[str, float]:
    """Detect language mix in text"""
    return swahili_processor.detect_language_mix(text)

def handle_code_switching(text: str) -> Dict[str, any]:
    """Process code-switching text"""
    return swahili_processor.handle_code_switching(text)

def kenya_specific_context(text: str) -> Dict[str, any]:
    """Extract Kenya-specific financial context"""
    return swahili_processor.get_kenya_specific_context(text)
