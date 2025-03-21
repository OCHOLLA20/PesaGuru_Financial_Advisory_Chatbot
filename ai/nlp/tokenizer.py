import re
import string
import json
import logging
from typing import List, Dict, Tuple, Set, Optional, Union, Any
from pathlib import Path
import os

# NLP libraries
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import spacy
from transformers import AutoTokenizer

# Cache management
from functools import lru_cache

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Initialize stemmers and lemmatizers
porter_stemmer = PorterStemmer()
wordnet_lemmatizer = WordNetLemmatizer()

# Initialize spaCy models
try:
    nlp_en = spacy.load("en_core_web_sm")
    logger.info("Successfully loaded English spaCy model")
except OSError:
    logger.warning("English spaCy model not found. Some features may be limited.")
    nlp_en = None

# Load BERT tokenizers
try:
    bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
    financial_bert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    logger.info("Successfully loaded BERT tokenizers")
except Exception as e:
    logger.warning(f"Could not load BERT tokenizers: {e}")
    bert_tokenizer = None
    financial_bert_tokenizer = None

# Load custom financial terms dictionary
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

try:
    with open(DATA_DIR / "financial_terms_dictionary.json", "r", encoding="utf-8") as f:
        FINANCIAL_TERMS = json.load(f)
    logger.info("Successfully loaded financial terms dictionary")
except FileNotFoundError:
    logger.warning("Financial terms dictionary not found. Using empty dictionary.")
    FINANCIAL_TERMS = {}

# Load Swahili corpus
try:
    with open(DATA_DIR / "swahili_corpus.json", "r", encoding="utf-8") as f:
        SWAHILI_CORPUS = json.load(f)
    logger.info("Successfully loaded Swahili corpus")
except FileNotFoundError:
    logger.warning("Swahili corpus not found. Swahili support will be limited.")
    SWAHILI_CORPUS = {"stopwords": []}

# Load Kenyan financial corpus
try:
    with open(DATA_DIR / "kenyan_financial_corpus.json", "r", encoding="utf-8") as f:
        KENYAN_FINANCIAL_CORPUS = json.load(f)
    logger.info("Successfully loaded Kenyan financial corpus")
except FileNotFoundError:
    logger.warning("Kenyan financial corpus not found. Using empty dictionary.")
    KENYAN_FINANCIAL_CORPUS = {"terms": {}, "abbreviations": {}}

# Initialize stopwords
STOPWORDS = {
    "english": set(stopwords.words('english')),
    "swahili": set(SWAHILI_CORPUS.get("stopwords", []))
}

# Add financial stopwords to exclude (these are often important in financial context)
FINANCIAL_STOPWORDS_TO_EXCLUDE = {
    "investment", "stock", "bond", "market", "price", "rate", "interest", 
    "dividend", "portfolio", "risk", "return", "profit", "loss", "fund",
    "equity", "debt", "credit", "loan", "mortgage", "deposit", "withdraw"
}

# Remove financial terms from stopwords
STOPWORDS["english"] = STOPWORDS["english"] - FINANCIAL_STOPWORDS_TO_EXCLUDE

# Common Kenyan financial abbreviations and their expansions
KENYAN_FINANCIAL_ABBR = KENYAN_FINANCIAL_CORPUS.get("abbreviations", {})
if not KENYAN_FINANCIAL_ABBR:
    # Fallback to hardcoded abbreviations if corpus is unavailable
    KENYAN_FINANCIAL_ABBR = {
        "NSE": "Nairobi Securities Exchange",
        "CMA": "Capital Markets Authority",
        "CBK": "Central Bank of Kenya",
        "CDSC": "Central Depository & Settlement Corporation",
        "KRA": "Kenya Revenue Authority",
        "NSSF": "National Social Security Fund",
        "NHIF": "National Hospital Insurance Fund",
        "KYC": "Know Your Customer",
        "T-Bill": "Treasury Bill",
        "T-Bond": "Treasury Bond",
    }


class FinancialTokenizer:
    """
    A tokenizer class specialized for financial text processing in English and Swahili.
    """
    
    def __init__(self, language: str = "english"):
        """
        Initialize the tokenizer with specified language.
        
        Args:
            language (str): The language for tokenization ("english" or "swahili")
        """
        self.language = language.lower()
        if self.language not in ["english", "swahili"]:
            logger.warning(f"Unsupported language: {language}. Defaulting to English.")
            self.language = "english"
        
        # Set language-specific resources
        self.stopwords = STOPWORDS.get(self.language, set())
        
        # Initialize caches
        self._cache_clear()
    
    def _cache_clear(self):
        """Clear all internal caches."""
        # Clear LRU cache decorators
        self.detect_language.cache_clear()
        self.tokenize_text.cache_clear()
        self.preprocess_text.cache_clear()
    
    @lru_cache(maxsize=1000)
    def detect_language(self, text: str) -> str:
        """
        Detect if the input text is in English or Swahili.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Detected language ("english" or "swahili")
        """
        # Implement a simple language detection based on common words
        # This is a basic approach and could be enhanced with a proper LID model
        text = text.lower()
        
        # Common English and Swahili words
        en_common = {"the", "is", "and", "of", "to", "in", "that", "for", "it", "with"}
        sw_common = {"na", "ni", "ya", "wa", "kwa", "katika", "hii", "huo", "hapa", "sasa"}
        
        words = set(re.findall(r'\b\w+\b', text))
        
        en_count = len(words.intersection(en_common))
        sw_count = len(words.intersection(sw_common))
        
        # Check for code-switching (mixed language)
        if sw_count > 0 and en_count > 0:
            # If mixed, return the dominant language
            return "swahili" if sw_count > en_count else "english"
        elif sw_count > 0:
            return "swahili"
        else:
            return "english"
    
    def set_language(self, language: str):
        """
        Set the tokenizer language.
        
        Args:
            language (str): The language for tokenization ("english" or "swahili")
        """
        if language.lower() not in ["english", "swahili"]:
            logger.warning(f"Unsupported language: {language}. Language unchanged.")
            return
        
        self.language = language.lower()
        self.stopwords = STOPWORDS.get(self.language, set())
        self._cache_clear()
    
    @lru_cache(maxsize=1000)
    def preprocess_text(self, text: str, remove_punctuation: bool = True,
                       lower_case: bool = True, expand_abbreviations: bool = True) -> str:
        """
        Preprocess text for tokenization.
        
        Args:
            text (str): Input text
            remove_punctuation (bool): Whether to remove punctuation
            lower_case (bool): Whether to convert text to lowercase
            expand_abbreviations (bool): Whether to expand common abbreviations
            
        Returns:
            str: Preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Sanitize input for security
        text = self.sanitize_input(text)
        
        # Convert to lowercase if requested
        if lower_case:
            text = text.lower()
        
        # Expand abbreviations if requested
        if expand_abbreviations:
            for abbr, expansion in KENYAN_FINANCIAL_ABBR.items():
                # Use word boundary to avoid partial matches
                pattern = r'\b' + re.escape(abbr) + r'\b'
                if lower_case:
                    text = re.sub(pattern, expansion.lower(), text, flags=re.IGNORECASE)
                else:
                    text = re.sub(pattern, expansion, text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove punctuation if requested
        if remove_punctuation:
            text = text.translate(str.maketrans('', '', string.punctuation))
        
        return text
    
    @lru_cache(maxsize=1000)
    def tokenize_text(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        Tokenize text into a list of tokens.
        
        Args:
            text (str): Input text to tokenize
            remove_stopwords (bool): Whether to remove stopwords
            
        Returns:
            List[str]: List of tokens
        """
        if not text:
            return []
        
        # Detect language if not specified
        detected_lang = self.detect_language(text)
        
        # Tokenize based on language
        if detected_lang == "swahili":
            # Fallback to English tokenizer for Swahili
            tokens = word_tokenize(text, language='english')
        else:
            tokens = word_tokenize(text)
        
        # Remove stopwords if requested
        if remove_stopwords:
            stopword_set = STOPWORDS.get(detected_lang, set())
            tokens = [token for token in tokens if token.lower() not in stopword_set]
        
        return tokens
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming to tokens.
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Stemmed tokens
        """
        # Currently only supporting English stemming
        if self.language == "english":
            return [porter_stemmer.stem(token) for token in tokens]
        # For Swahili, we would need a custom stemmer
        return tokens
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply lemmatization to tokens.
        
        Args:
            tokens (List[str]): List of tokens
            
        Returns:
            List[str]: Lemmatized tokens
        """
        # Currently only supporting English lemmatization
        if self.language == "english":
            return [wordnet_lemmatizer.lemmatize(token) for token in tokens]
        # For Swahili, we would need a custom lemmatizer
        return tokens
    
    def extract_financial_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from text.
        
        Args:
            text (str): Input text
            
        Returns:
            Dict[str, List[str]]: Dictionary of entity types and values
        """
        entities = {
            "money": [],
            "percentage": [],
            "company": [],
            "stock_symbol": [],
            "financial_term": []
        }
        
        # Use spaCy for named entity recognition if available
        if nlp_en is not None and self.language == "english":
            doc = nlp_en(text)
            
            for ent in doc.ents:
                if ent.label_ == "MONEY":
                    entities["money"].append(ent.text)
                elif ent.label_ == "PERCENT":
                    entities["percentage"].append(ent.text)
                elif ent.label_ == "ORG":
                    entities["company"].append(ent.text)
        
        # Extract Kenyan currency mentions
        money_pattern = r'(?i)\b(KES|KSh|Ksh|Kshs)\.?\s*\d[\d,.]*'
        money_matches = re.findall(money_pattern, text)
        entities["money"].extend(money_matches)
        
        # Extract stock symbols (simple approach)
        stock_pattern = r'\b[A-Z]{2,5}\b'  # Simple pattern for stock symbols
        potential_symbols = re.findall(stock_pattern, text)
        
        # Filter symbols against known NSE listings (placeholder)
        nse_symbols = ["SCOM", "KCB", "EQTY", "ABSA", "COOP", "EABL", "BAT", "SBIC"]
        for symbol in potential_symbols:
            if symbol in nse_symbols:
                entities["stock_symbol"].append(symbol)
        
        # Extract known financial terms
        for term, info in FINANCIAL_TERMS.items():
            if term.lower() in text.lower():
                entities["financial_term"].append(term)
        
        return entities
    
    def tokenize_for_bert(self, text: str, max_length: int = 512) -> Dict[str, Any]:
        """
        Tokenize text for BERT models.
        
        Args:
            text (str): Input text
            max_length (int): Maximum sequence length
            
        Returns:
            Dict[str, Any]: BERT-compatible tokens
        """
        if bert_tokenizer is None:
            logger.error("BERT tokenizer not available")
            return {"error": "BERT tokenizer not available"}
        
        # Use financial BERT for financial text, regular BERT otherwise
        tokenizer = financial_bert_tokenizer if financial_bert_tokenizer else bert_tokenizer
        
        encoded = tokenizer(
            text,
            add_special_tokens=True,
            max_length=max_length,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt"
        )
        
        return {
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"]
        }
    
    def process_for_sentiment_analysis(self, text: str) -> str:
        """
        Process text specifically for sentiment analysis.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Processed text optimized for sentiment analysis
        """
        # Preprocess text
        preprocessed = self.preprocess_text(text, remove_punctuation=False, lower_case=True)
        
        # For sentiment analysis, we want to keep emotionally charged stopwords
        sentiment_stopwords = {"not", "no", "never", "neither", "nor", "none", "nothing"}
        
        # Tokenize but keep certain stopwords
        tokens = word_tokenize(preprocessed)
        filtered_tokens = []
        
        for token in tokens:
            # Keep token if it's not a stopword or is a sentiment-relevant stopword
            if (token.lower() not in self.stopwords or 
                token.lower() in sentiment_stopwords or
                token.lower() in FINANCIAL_STOPWORDS_TO_EXCLUDE):
                filtered_tokens.append(token)
        
        return " ".join(filtered_tokens)
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract key financial terms from text.
        
        Args:
            text (str): Input text
            top_n (int): Number of keywords to return
            
        Returns:
            List[str]: List of extracted keywords
        """
        # Preprocess and tokenize
        preprocessed = self.preprocess_text(text)
        tokens = self.tokenize_text(preprocessed)
        
        # Count term frequency
        term_freq = {}
        for token in tokens:
            if token in term_freq:
                term_freq[token] += 1
            else:
                term_freq[token] = 1
        
        # Prioritize financial terms
        for token in tokens:
            if token.lower() in [term.lower() for term in FINANCIAL_TERMS.keys()]:
                term_freq[token] *= 2  # Double the weight of financial terms
        
        # Sort by frequency and return top N
        sorted_terms = sorted(term_freq.items(), key=lambda x: x[1], reverse=True)
        return [term for term, freq in sorted_terms[:top_n]]
    
    def normalize_financial_numbers(self, text: str) -> str:
        """
        Normalize financial numbers and currency mentions.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Text with normalized financial numbers
        """
        # Normalize Kenyan currency mentions
        # Replace KSh, Ksh, KES, etc. with a standardized form
        text = re.sub(r'(?i)\b(KSh|Ksh|KES|Kshs)\.?\s*(\d[\d,.]*)', r'KES \2', text)
        
        # Normalize large numbers
        # Replace "KES 1.2M" with "KES 1,200,000"
        def expand_number(match):
            num_str = match.group(2).replace(',', '')
            try:
                if 'M' in match.group(3):
                    num = float(num_str) * 1_000_000
                elif 'B' in match.group(3):
                    num = float(num_str) * 1_000_000_000
                elif 'K' in match.group(3):
                    num = float(num_str) * 1_000
                else:
                    return match.group(0)
                
                return f"{match.group(1)} {num:,.0f}"
            except:
                return match.group(0)
        
        return re.sub(r'(KES)\s*(\d+\.?\d*)\s*([KMB])', expand_number, text)
    
    def process_text_pipeline(self, text: str, task: str = "general") -> Union[List[str], Dict[str, Any]]:
        """
        Complete text processing pipeline for different NLP tasks.
        
        Args:
            text (str): Input text
            task (str): Processing task: "general", "sentiment", "entity", "bert", "keywords"
            
        Returns:
            Union[List[str], Dict[str, Any]]: Processed result based on task
        """
        if not text:
            return [] if task in ["general", "keywords"] else {}
        
        # Normalize financial numbers
        text = self.normalize_financial_numbers(text)
        
        # Check and potentially adjust language
        detected_lang = self.detect_language(text)
        if detected_lang != self.language:
            original_lang = self.language
            self.set_language(detected_lang)
            result = self._process_by_task(text, task)
            self.set_language(original_lang)
            return result
        else:
            return self._process_by_task(text, task)
    
    def _process_by_task(self, text: str, task: str) -> Union[List[str], Dict[str, Any]]:
        """Internal helper for processing text by task type."""
        if task == "general":
            preprocessed = self.preprocess_text(text)
            tokens = self.tokenize_text(preprocessed)
            return tokens
        
        elif task == "sentiment":
            return self.process_for_sentiment_analysis(text)
        
        elif task == "entity":
            return self.extract_financial_entities(text)
        
        elif task == "bert":
            return self.tokenize_for_bert(text)
        
        elif task == "keywords":
            return self.extract_keywords(text)
        
        else:
            logger.warning(f"Unknown task: {task}. Using general processing.")
            preprocessed = self.preprocess_text(text)
            tokens = self.tokenize_text(preprocessed)
            return tokens
    
    def handle_code_switching(self, text: str) -> Dict[str, Any]:
        """
        Process text with code-switching (mixed English and Swahili).
        
        Args:
            text (str): Input text with potential code-switching
            
        Returns:
            Dict[str, Any]: Processed tokens with language markers
        """
        # Split into sentences
        sentences = sent_tokenize(text)
        results = []
        
        for sentence in sentences:
            lang = self.detect_language(sentence)
            tokens = self.tokenize_text(sentence)
            results.append({
                "text": sentence,
                "language": lang,
                "tokens": tokens
            })
        
        return {
            "mixed_language": len(set([r["language"] for r in results])) > 1,
            "segments": results
        }
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize input text for security.
        
        Args:
            text (str): Input text
            
        Returns:
            str: Sanitized text
        """
        # Remove potentially malicious patterns
        # Remove HTML/XML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove SQL injection patterns
        text = re.sub(r'(?i)(select|insert|update|delete|drop|alter|exec|union|create|where)\s', 
                     lambda m: m.group(0).replace(' ', '_'), text)
        
        # Remove script tags
        text = re.sub(r'(?i)<script.*?>.*?</script>', '', text)
        
        return text


# Initialize a singleton instance for common use
default_tokenizer = FinancialTokenizer()

# Convenience functions using the default tokenizer
def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """
    Tokenize text using the default tokenizer.
    
    Args:
        text (str): Input text
        remove_stopwords (bool): Whether to remove stopwords
        
    Returns:
        List[str]: Tokens
    """
    return default_tokenizer.tokenize_text(text, remove_stopwords)

def preprocess(text: str) -> str:
    """
    Preprocess text using the default tokenizer.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    return default_tokenizer.preprocess_text(text)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """
    Extract financial entities using the default tokenizer.
    
    Args:
        text (str): Input text
        
    Returns:
        Dict[str, List[str]]: Extracted entities
    """
    return default_tokenizer.extract_financial_entities(text)

def detect_language(text: str) -> str:
    """
    Detect language using the default tokenizer.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Detected language
    """
    return default_tokenizer.detect_language(text)

def process_for_bert(text: str) -> Dict[str, Any]:
    """
    Process text for BERT models using the default tokenizer.
    
    Args:
        text (str): Input text
        
    Returns:
        Dict[str, Any]: BERT-compatible tokens
    """
    return default_tokenizer.tokenize_for_bert(text)

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    Extract keywords using the default tokenizer.
    
    Args:
        text (str): Input text
        top_n (int): Number of keywords to return
        
    Returns:
        List[str]: Extracted keywords
    """
    return default_tokenizer.extract_keywords(text, top_n)


if __name__ == "__main__":
    # Example usage
    sample_text = "I want to invest KES 10,000 in Safaricom stock and KES 5K in T-Bills. What do you recommend?"
    swahili_text = "Nataka kuwekeza KES 10,000 katika hisa za Safaricom na KES 5K katika T-Bills. Unapendekeza nini?"
    mixed_text = "Nataka kuwekeza KES 10,000 in Safaricom stock. What do you recommend?"
    
    # Test with English text
    print("\n=== English Text Processing ===")
    tokenizer = FinancialTokenizer()
    print(f"Detected language: {tokenizer.detect_language(sample_text)}")
    
    preprocessed = tokenizer.preprocess_text(sample_text)
    print(f"Preprocessed: {preprocessed}")
    
    tokens = tokenizer.tokenize_text(preprocessed)
    print(f"Tokens: {tokens}")
    
    entities = tokenizer.extract_financial_entities(sample_text)
    print(f"Entities: {entities}")
    
    keywords = tokenizer.extract_keywords(sample_text)
    print(f"Keywords: {keywords}")
    
    # Test with Swahili text
    print("\n=== Swahili Text Processing ===")
    print(f"Detected language: {tokenizer.detect_language(swahili_text)}")
    
    preprocessed = tokenizer.preprocess_text(swahili_text)
    print(f"Preprocessed: {preprocessed}")
    
    tokens = tokenizer.tokenize_text(preprocessed)
    print(f"Tokens: {tokens}")
    
    # Test with code-switching (mixed language)
    print("\n=== Mixed Language Processing ===")
    print(f"Detected language: {tokenizer.detect_language(mixed_text)}")
    
    mixed_results = tokenizer.handle_code_switching(mixed_text)
    print(f"Code-switching analysis: {mixed_results}")
