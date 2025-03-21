import re
import json
import os
from typing import List, Dict, Union, Optional, Tuple
import logging
from pathlib import Path

# Import standard NLP libraries
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
import spacy
import contractions
from num2words import num2words
import unicodedata

# Ensure required NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load language models
try:
    # English model
    en_nlp = spacy.load('en_core_web_sm')
    # We'll attempt to load Swahili model if available
    try:
        sw_nlp = spacy.load('sw_core_web_sm')
        SWAHILI_MODEL_AVAILABLE = True
    except OSError:
        logger.warning("Swahili spaCy model not found. Using English model for Swahili text.")
        SWAHILI_MODEL_AVAILABLE = False
except OSError:
    logger.error("Failed to load spaCy language models. Make sure they're installed.")
    raise

# Path to financial terms dictionary
CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FINANCIAL_TERMS_PATH = PROJECT_ROOT / "ai" / "data" / "financial_terms_dictionary.json"
SWAHILI_CORPUS_PATH = PROJECT_ROOT / "ai" / "data" / "swahili_corpus.json"

# Load financial terms dictionary
try:
    with open(FINANCIAL_TERMS_PATH, 'r', encoding='utf-8') as f:
        FINANCIAL_TERMS = json.load(f)
    logger.info(f"Loaded {len(FINANCIAL_TERMS)} financial terms from dictionary.")
except FileNotFoundError:
    logger.warning(f"Financial terms dictionary not found at {FINANCIAL_TERMS_PATH}. Using empty dictionary.")
    FINANCIAL_TERMS = {}

# Load Swahili corpus if available
try:
    with open(SWAHILI_CORPUS_PATH, 'r', encoding='utf-8') as f:
        SWAHILI_CORPUS = json.load(f)
    logger.info(f"Loaded Swahili corpus with {len(SWAHILI_CORPUS)} entries.")
except FileNotFoundError:
    logger.warning(f"Swahili corpus not found at {SWAHILI_CORPUS_PATH}. Swahili support may be limited.")
    SWAHILI_CORPUS = {}

# Initialize stemmer and lemmatizer
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

# Common financial symbols and their standardized forms
FINANCIAL_SYMBOLS = {
    '$': 'USD',
    '€': 'EUR',
    '£': 'GBP',
    '¥': 'JPY',
    'KSh': 'KES',
    'Ksh': 'KES',
    'KES': 'KES',
    'TSh': 'TZS',
    'Tsh': 'TZS',
    'USh': 'UGX',
    'Ush': 'UGX',
    'R': 'ZAR',
    '%': 'percent'
}

# Common English stopwords to exclude in financial context
FINANCIAL_STOPWORDS_EXCLUSIONS = {
    'interest', 'rate', 'rates', 'increase', 'decrease', 'up', 'down',
    'high', 'low', 'profit', 'loss', 'buy', 'sell', 'market', 'stock',
    'bond', 'equity', 'investment', 'risk', 'return', 'dividend',
    'yield', 'portfolio', 'asset', 'liability', 'loan', 'debt', 'credit',
    'deposit', 'withdrawal', 'payment', 'fee', 'tax', 'income', 'expense',
    'budget', 'saving', 'retirement', 'pension', 'fund', 'account'
}

# Custom stopwords for English and Swahili
ENGLISH_STOPWORDS = set(stopwords.words('english')) - FINANCIAL_STOPWORDS_EXCLUSIONS
SWAHILI_STOPWORDS = set([
    'na', 'ya', 'wa', 'kwa', 'ni', 'katika', 'za', 'la', 'kuwa', 'kama',
    'hii', 'huo', 'huu', 'hizi', 'hayo', 'yake', 'wake', 'sana', 'pia',
    'lakini', 'hata', 'hivyo', 'ambayo', 'ambao', 'yao', 'wao', 'kwamba',
    'hiyo', 'hilo', 'hili', 'kubwa', 'ndani'
]) - FINANCIAL_STOPWORDS_EXCLUSIONS

# Kenyan financial acronyms and their full forms
KENYAN_FINANCIAL_ACRONYMS = {
    'NSE': 'Nairobi Securities Exchange',
    'CMA': 'Capital Markets Authority',
    'CBK': 'Central Bank of Kenya',
    'NSSF': 'National Social Security Fund',
    'NHIF': 'National Hospital Insurance Fund',
    'KRA': 'Kenya Revenue Authority',
    'KCB': 'Kenya Commercial Bank',
    'SACCO': 'Savings and Credit Cooperative Organization',
    'HELB': 'Higher Education Loans Board',
    'ICDC': 'Industrial and Commercial Development Corporation',
    'EFT': 'Electronic Funds Transfer',
    'RTGS': 'Real Time Gross Settlement',
    'SASRA': 'SACCO Societies Regulatory Authority',
    'CRB': 'Credit Reference Bureau',
    'IPO': 'Initial Public Offering',
    'CDSC': 'Central Depository & Settlement Corporation',
    'KEPSS': 'Kenya Electronic Payment and Settlement System',
    'MFI': 'Microfinance Institution',
    'DTM': 'Deposit Taking Microfinance',
    'ICIFA': 'Institute of Certified Investment and Financial Analysts'
}


def detect_language(text: str) -> str:
    """
    Detect whether the text is in English or Swahili.
    
    Args:
        text (str): Input text
        
    Returns:
        str: 'en' for English, 'sw' for Swahili
    """
    # Simple language detection based on common words
    text = text.lower()
    
    # Count common English and Swahili words
    en_count = sum(1 for word in ['the', 'and', 'is', 'are', 'in', 'to', 'for', 'you', 'that', 'have'] 
                  if f' {word} ' in f' {text} ')
    
    sw_count = sum(1 for word in ['na', 'ya', 'ni', 'kwa', 'wa', 'katika', 'kuwa', 'hii', 'huo', 'lakini'] 
                  if f' {word} ' in f' {text} ')
    
    # Check for Swahili specific financial terms
    sw_financial_count = sum(1 for word in ['fedha', 'akiba', 'benki', 'mkopo', 'pesa', 'riba', 'hisa', 'malipo'] 
                            if f' {word} ' in f' {text} ')
    
    # Add Swahili financial terms to the count
    sw_count += sw_financial_count
    
    return 'sw' if sw_count > en_count else 'en'


def normalize_text(text: str, language: Optional[str] = None) -> str:
    """
    Normalize text by converting to lowercase, removing special characters,
    and standardizing whitespace.
    
    Args:
        text (str): Input text
        language (str, optional): Language code ('en' or 'sw'). If None, it will be auto-detected.
        
    Returns:
        str: Normalized text
    """
    if not text:
        return ""
    
    # Auto-detect language if not provided
    if language is None:
        language = detect_language(text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Expand contractions (English only)
    if language == 'en':
        text = contractions.fix(text)
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Replace currency symbols
    for symbol, replacement in FINANCIAL_SYMBOLS.items():
        text = text.replace(symbol, f' {replacement} ')
    
    # Expand Kenyan financial acronyms
    for acronym, full_form in KENYAN_FINANCIAL_ACRONYMS.items():
        # Use regex to match the acronym as a whole word
        text = re.sub(r'\b' + acronym + r'\b', f'{acronym} ({full_form})', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def remove_punctuation(text: str) -> str:
    """
    Remove punctuation from text.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text without punctuation
    """
    # Remove punctuation except for % and currency symbols
    text = re.sub(r'[^\w\s%$€£¥]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def remove_stopwords(text: str, language: str = 'en') -> str:
    """
    Remove stopwords from text.
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        str: Text without stopwords
    """
    if not text:
        return ""
    
    # Tokenize
    words = text.split()
    
    # Select appropriate stopwords list
    if language == 'sw':
        stops = SWAHILI_STOPWORDS
    else:  # Default to English
        stops = ENGLISH_STOPWORDS
    
    # Remove stopwords while preserving financial terms
    filtered_words = []
    for word in words:
        # Keep word if it's not a stopword or it's a financial term
        if word not in stops or word.lower() in FINANCIAL_TERMS:
            filtered_words.append(word)
    
    return ' '.join(filtered_words)


def stem_words(text: str, language: str = 'en') -> str:
    """
    Stem words in text.
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        str: Text with stemmed words
    """
    if not text or language != 'en':
        # Only support English stemming for now
        return text
    
    # Tokenize
    words = text.split()
    
    # Stem words
    stemmed_words = [stemmer.stem(word) for word in words]
    
    return ' '.join(stemmed_words)


def lemmatize_words(text: str, language: str = 'en') -> str:
    """
    Lemmatize words in text.
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        str: Text with lemmatized words
    """
    if not text:
        return ""
    
    # Only use spaCy lemmatization for supported languages
    if language == 'en':
        doc = en_nlp(text)
        lemmatized_words = [token.lemma_ for token in doc]
        return ' '.join(lemmatized_words)
    elif language == 'sw' and SWAHILI_MODEL_AVAILABLE:
        doc = sw_nlp(text)
        lemmatized_words = [token.lemma_ for token in doc]
        return ' '.join(lemmatized_words)
    else:
        # Fallback to basic tokenization without lemmatization
        return text


def normalize_numbers(text: str, language: str = 'en') -> str:
    """
    Normalize numbers in text (e.g., convert to words, standardize format).
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        str: Text with normalized numbers
    """
    if not text:
        return ""
    
    # Replace numbers with words (for certain contexts)
    def replace_num(match):
        num = float(match.group(0).replace(',', ''))
        if num.is_integer():
            num = int(num)
        
        # Convert large financial values to K/M/B notation
        if num >= 1000000000:
            return f"{num/1000000000:.2f}B"
        elif num >= 1000000:
            return f"{num/1000000:.2f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    
    # Handle numbers with commas
    text = re.sub(r'\b\d{1,3}(,\d{3})+(\.\d+)?\b', replace_num, text)
    
    # Handle plain numbers
    text = re.sub(r'\b\d+(\.\d+)?\b', replace_num, text)
    
    # Handle percentage format
    text = re.sub(r'(\d+(\.\d+)?)%', r'\1 percent', text)
    
    # Handle money format (e.g., KES 1,000)
    text = re.sub(r'(KES|USD|EUR|GBP)\s*\d{1,3}(,\d{3})*(\.\d+)?', 
                 lambda m: m.group(0).replace(',', ''), text)
    
    return text


def tokenize_text(text: str, language: str = 'en') -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        List[str]: List of tokens
    """
    if not text:
        return []
    
    # Use appropriate NLP pipeline based on language
    if language == 'en':
        doc = en_nlp(text)
        return [token.text for token in doc]
    elif language == 'sw' and SWAHILI_MODEL_AVAILABLE:
        doc = sw_nlp(text)
        return [token.text for token in doc]
    else:
        # Fallback to basic NLTK tokenization
        return word_tokenize(text)


def extract_financial_entities(text: str, language: str = 'en') -> Dict[str, List[str]]:
    """
    Extract financial entities from text (e.g., monetary values, percentages, company names).
    
    Args:
        text (str): Input text
        language (str): Language code ('en' or 'sw')
        
    Returns:
        Dict[str, List[str]]: Dictionary of entity types and their values
    """
    entities = {
        'monetary_values': [],
        'percentages': [],
        'companies': [],
        'financial_terms': []
    }
    
    # Extract monetary values
    money_pattern = r'(KES|USD|EUR|GBP|KSh|Ksh|\$|€|£)\s*\d+(,\d{3})*(\.\d+)?'
    entities['monetary_values'] = re.findall(money_pattern, text)
    
    # Extract percentages
    percent_pattern = r'\d+(\.\d+)?\s*%'
    entities['percentages'] = re.findall(percent_pattern, text)
    
    # Use spaCy for entity recognition
    if language == 'en':
        doc = en_nlp(text)
        
        # Extract companies (ORG entities)
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['companies'].append(ent.text)
    
    # Extract financial terms using the dictionary
    for term in FINANCIAL_TERMS:
        if re.search(r'\b' + re.escape(term) + r'\b', text, re.IGNORECASE):
            entities['financial_terms'].append(term)
    
    return entities


def preprocess_for_intent_classification(text: str) -> str:
    """
    Preprocess text specifically for intent classification.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    # Detect language
    language = detect_language(text)
    
    # Apply preprocessing steps
    text = normalize_text(text, language)
    text = remove_punctuation(text)
    text = remove_stopwords(text, language)
    
    # Lemmatize for better intent matching
    text = lemmatize_words(text, language)
    
    return text


def preprocess_for_sentiment_analysis(text: str) -> str:
    """
    Preprocess text specifically for sentiment analysis.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    # Detect language
    language = detect_language(text)
    
    # Apply preprocessing steps
    text = normalize_text(text, language)
    
    # For sentiment analysis, we want to keep most of the original text structure
    # but normalize it for consistency
    
    # Handle negations (important for sentiment)
    if language == 'en':
        text = re.sub(r'\b(not|no|never|neither|nor|none)\b', r' NOT ', text)
    elif language == 'sw':
        text = re.sub(r'\b(si|sio|siyo|hata|wala)\b', r' NOT ', text)
    
    return text


def preprocess_for_bert(text: str, max_length: int = 512) -> str:
    """
    Preprocess text specifically for BERT and transformer models.
    
    Args:
        text (str): Input text
        max_length (int): Maximum sequence length for BERT
        
    Returns:
        str: Preprocessed text
    """
    # Detect language
    language = detect_language(text)
    
    # Apply minimal preprocessing for BERT
    # BERT handles tokenization internally, so we just need to clean the text
    text = normalize_text(text, language)
    
    # Truncate if necessary (simple truncation; BERT tokenizers will handle this more intelligently)
    words = text.split()
    if len(words) > max_length:
        text = ' '.join(words[:max_length])
    
    return text


def preprocess_conversational_query(text: str) -> Tuple[str, str, Dict]:
    """
    Preprocess a conversational query from the chatbot.
    
    Args:
        text (str): Input text
        
    Returns:
        Tuple[str, str, Dict]: Processed text, detected language, and extracted entities
    """
    # Detect language
    language = detect_language(text)
    
    # Apply basic normalization
    processed_text = normalize_text(text, language)
    
    # Extract financial entities
    entities = extract_financial_entities(processed_text, language)
    
    return processed_text, language, entities


def prepare_text_for_embedding(text: str) -> str:
    """
    Prepare text for word embeddings or TF-IDF vectorization.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    # Detect language
    language = detect_language(text)
    
    # Apply preprocessing steps
    text = normalize_text(text, language)
    text = remove_punctuation(text)
    text = remove_stopwords(text, language)
    
    # Lemmatize for better semantic representation
    text = lemmatize_words(text, language)
    
    return text


def process_kenyan_financial_context(text: str) -> str:
    """
    Apply Kenya-specific financial context preprocessing.
    
    Args:
        text (str): Input text
        
    Returns:
        str: Processed text with Kenya-specific financial context
    """
    # Handle M-Pesa related terms
    m_pesa_pattern = r'\b(m-pesa|mpesa)\b'
    text = re.sub(m_pesa_pattern, 'M-PESA mobile money service', text, flags=re.IGNORECASE)
    
    # Handle Kenyan banking terms
    text = re.sub(r'\bsacco\b', 'Savings and Credit Cooperative (SACCO)', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchama\b', 'informal cooperative savings group', text, flags=re.IGNORECASE)
    
    # Handle Kenyan stock market references
    text = re.sub(r'\bnse\b', 'Nairobi Securities Exchange (NSE)', text, flags=re.IGNORECASE)
    
    # Standardize Kenyan currency formats
    text = re.sub(r'(Kshs?|KShs?|Kenya\s+Shillings?)', 'KES', text, flags=re.IGNORECASE)
    
    return text


def preprocess_market_data_query(text: str) -> Tuple[str, Dict]:
    """
    Preprocess a query related to market data.
    
    Args:
        text (str): Input text
        
    Returns:
        Tuple[str, Dict]: Processed text and extracted parameters
    """
    # Detect language
    language = detect_language(text)
    
    # Extract parameters
    params = {}
    
    # Extract time periods
    time_periods = {
        'today': r'\b(today|leo|current|current day)\b',
        'yesterday': r'\b(yesterday|jana|previous day)\b',
        'this week': r'\b(this week|wiki hii|current week)\b',
        'last week': r'\b(last week|wiki iliyopita|previous week)\b',
        'this month': r'\b(this month|mwezi huu|current month)\b',
        'last month': r'\b(last month|mwezi uliopita|previous month)\b',
        'this year': r'\b(this year|mwaka huu|current year)\b',
        'last year': r'\b(last year|mwaka uliopita|previous year)\b'
    }
    
    for period, pattern in time_periods.items():
        if re.search(pattern, text, re.IGNORECASE):
            params['time_period'] = period
            break
    
    # Extract stock references
    stock_pattern = r'\b([A-Z]{3,5})\b'  # Simple pattern for stock symbols
    stock_matches = re.findall(stock_pattern, text.upper())
    if stock_matches:
        params['stocks'] = stock_matches
    
    # Extract forex currency pairs
    forex_pattern = r'\b(KES|USD|EUR|GBP|JPY)\s*/\s*(KES|USD|EUR|GBP|JPY)\b'
    forex_matches = re.findall(forex_pattern, text.upper())
    if forex_matches:
        params['forex_pairs'] = forex_matches
    
    # Apply preprocessing
    processed_text = normalize_text(text, language)
    
    return processed_text, params


def clean_and_standardize(text: str, context: str = 'general') -> str:
    """
    Clean and standardize text based on the intended context.
    
    Args:
        text (str): Input text
        context (str): Context of text processing ('general', 'intent', 'sentiment', 
                       'bert', 'market_data', 'embedding')
        
    Returns:
        str: Processed text
    """
    if not text:
        return ""
    
    # Apply different preprocessing based on context
    if context == 'intent':
        return preprocess_for_intent_classification(text)
    elif context == 'sentiment':
        return preprocess_for_sentiment_analysis(text)
    elif context == 'bert':
        return preprocess_for_bert(text)
    elif context == 'market_data':
        processed, _ = preprocess_market_data_query(text)
        return processed
    elif context == 'embedding':
        return prepare_text_for_embedding(text)
    else:  # general preprocessing
        language = detect_language(text)
        text = normalize_text(text, language)
        text = remove_punctuation(text)
        text = normalize_numbers(text, language)
        
        # Apply Kenya-specific context
        text = process_kenyan_financial_context(text)
        
        return text


def preprocess_pipeline(text: str, pipeline: List[str]) -> str:
    """
    Apply a custom pipeline of preprocessing steps.
    
    Args:
        text (str): Input text
        pipeline (List[str]): List of preprocessing steps to apply
        
    Returns:
        str: Processed text
    """
    if not text:
        return ""
    
    # Detect language first
    language = detect_language(text)
    processed_text = text
    
    # Apply requested preprocessing steps in order
    for step in pipeline:
        if step == 'normalize':
            processed_text = normalize_text(processed_text, language)
        elif step == 'remove_punctuation':
            processed_text = remove_punctuation(processed_text)
        elif step == 'remove_stopwords':
            processed_text = remove_stopwords(processed_text, language)
        elif step == 'stem':
            processed_text = stem_words(processed_text, language)
        elif step == 'lemmatize':
            processed_text = lemmatize_words(processed_text, language)
        elif step == 'normalize_numbers':
            processed_text = normalize_numbers(processed_text, language)
        elif step == 'kenyan_context':
            processed_text = process_kenyan_financial_context(processed_text)
    
    return processed_text


# Main preprocessing function that other modules will typically call
def preprocess_text(text: str, purpose: str = 'general', custom_pipeline: Optional[List[str]] = None) -> Union[str, Tuple]:
    """
    Main preprocessing function for PesaGuru NLP pipeline.
    
    Args:
        text (str): Input text
        purpose (str): Purpose of preprocessing ('general', 'intent', 'sentiment', 
                      'bert', 'market_data', 'embedding', 'conversation')
        custom_pipeline (List[str], optional): Custom preprocessing pipeline
        
    Returns:
        Union[str, Tuple]: Processed text or tuple of text and metadata
    """
    if not text:
        return "" if purpose != 'conversation' else ("", "en", {})
    
    # If custom pipeline is provided, use it
    if custom_pipeline:
        return preprocess_pipeline(text, custom_pipeline)
    
    # Otherwise, use predefined processing for different purposes
    if purpose == 'conversation':
        return preprocess_conversational_query(text)
    elif purpose == 'market_data':
        return preprocess_market_data_query(text)
    else:
        return clean_and_standardize(text, purpose)


# For testing purposes
if __name__ == "__main__":
    # Example texts
    english_text = "I want to invest KSh 50,000 in the NSE. What stocks do you recommend for a 20% annual return?"
    swahili_text = "Nataka kuwekeza KSh 50,000 katika NSE. Unapendekeza hisa zipi kwa faida ya asilimia 20 kwa mwaka?"
    
    # Test preprocessing
    print("Original English text:", english_text)
    print("Preprocessed for intent:", preprocess_text(english_text, 'intent'))
    print("Preprocessed for BERT:", preprocess_text(english_text, 'bert'))
