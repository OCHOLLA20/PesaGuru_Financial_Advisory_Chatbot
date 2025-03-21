import re
import json
import os
from collections import Counter
import fasttext
import nltk
from nltk.tokenize import word_tokenize
from typing import Dict, Tuple, List, Any, Optional

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class LanguageDetector:
    """
    Class responsible for detecting the language of input text,
    primarily focusing on distinguishing between English and Swahili,
    with support for mixed language detection.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the language detector with required resources.
        
        Args:
            model_path: Path to a pre-trained fastText model for language detection.
                        If None, will use the default paths.
        """
        self.languages = ['en', 'sw']  # English and Swahili
        
        # Load common words for each language (stopwords, common terms)
        self.common_words = self._load_common_words()
        
        # Load financial terms dictionary
        self.financial_terms = self._load_financial_terms()
        
        # Initialize fastText model for language detection
        if model_path is None:
            # Default model path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, '..', 'models', 'lid.176.bin')
        
        try:
            # Load the pre-trained model
            self.model = fasttext.load_model(model_path)
        except Exception as e:
            print(f"Warning: Could not load fastText model: {e}")
            print("Falling back to rule-based detection only.")
            self.model = None
    
    def _load_common_words(self) -> Dict[str, set]:
        """
        Load common words (like stopwords) for supported languages.
        
        Returns:
            Dictionary mapping language codes to sets of common words.
        """
        # These are commonly used words in each language
        en_common = {
            'the', 'and', 'to', 'of', 'in', 'a', 'for', 'is', 'on', 'that', 'by',
            'this', 'with', 'i', 'you', 'it', 'not', 'or', 'be', 'are', 'from',
            'at', 'as', 'your', 'have', 'more', 'an', 'was', 'we', 'will', 'can',
            'do', 'if', 'would', 'like', 'how', 'what', 'when', 'my', 'should'
        }
        
        sw_common = {
            'na', 'ya', 'kwa', 'ni', 'katika', 'za', 'wa', 'kuwa', 'la', 'kama',
            'hii', 'yake', 'huo', 'wake', 'huo', 'hizi', 'hili', 'hiyo', 'huku',
            'huyu', 'mimi', 'wewe', 'yeye', 'sisi', 'nyinyi', 'wao', 'hapa',
            'ambayo', 'pia', 'lakini', 'hata', 'kila', 'kwamba', 'tu', 'bado',
            'hivyo', 'sana', 'baada', 'kabla', 'bila', 'kwenye', 'pamoja'
        }
        
        return {
            'en': en_common,
            'sw': sw_common
        }
    
    def _load_financial_terms(self) -> Dict[str, Dict[str, str]]:
        """
        Load financial terminology in both English and Swahili.
        
        Returns:
            Dictionary mapping financial terms between languages.
        """
        # In production, this would load from financial_terms_dictionary.json
        # For now, we're defining a sample dictionary of common financial terms
        
        # Map English financial terms to Swahili
        en_to_sw = {
            "investment": "uwekezaji",
            "savings": "akiba",
            "loan": "mkopo",
            "interest rate": "kiwango cha riba",
            "budget": "bajeti",
            "stock market": "soko la hisa",
            "bank": "benki",
            "money": "pesa",
            "profit": "faida",
            "loss": "hasara",
            "credit": "mikopo",
            "debit": "debit",
            "mortgage": "rehani",
            "insurance": "bima",
            "tax": "kodi",
            "dividend": "mgao",
            "portfolio": "mkoba wa uwekezaji",
            "asset": "mali",
            "liability": "dhima",
            "debt": "deni",
            "expense": "gharama",
            "income": "mapato",
            "risk": "hatari",
            "bond": "hati fungani",
            "shares": "hisa",
            "deposit": "amana",
            "withdraw": "kutoa",
            "transaction": "muamala",
            "account": "akaunti",
            "payment": "malipo",
            "balance": "salio",
            "statement": "taarifa",
            "currency": "sarafu",
            "exchange rate": "kiwango cha ubadilishaji"
        }
        
        # Create reverse mapping (Swahili to English)
        sw_to_en = {v: k for k, v in en_to_sw.items()}
        
        return {
            'en_to_sw': en_to_sw,
            'sw_to_en': sw_to_en
        }
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the input text.
        
        Uses multiple strategies:
        1. Common word frequency analysis
        2. Character n-gram patterns
        3. FastText model (if available)
        4. Financial terminology detection
        
        Args:
            text: The input text to analyze.
            
        Returns:
            Dictionary containing:
            - 'language': The detected language code ('en', 'sw', or 'mixed')
            - 'confidence': Confidence score (0-1) for the detection
            - 'language_distribution': Dictionary with percentage estimates for each language
            - 'is_financial': Boolean indicating if financial terminology was detected
            - 'financial_terms': List of detected financial terms
        """
        # Clean and normalize text
        cleaned_text = self._preprocess_text(text)
        
        # Check if the text is too short for reliable detection
        if len(cleaned_text.split()) < 2:
            # For very short texts, use character-based detection
            return self._detect_short_text(cleaned_text)
        
        # Initialize results
        result = {
            'language': 'unknown',
            'confidence': 0.0,
            'language_distribution': {lang: 0.0 for lang in self.languages},
            'is_financial': False,
            'financial_terms': []
        }
        
        # 1. Common word frequency analysis
        word_analysis = self._analyze_word_frequency(cleaned_text)
        
        # 2. Financial terminology detection
        financial_analysis = self._detect_financial_terms(cleaned_text)
        result['is_financial'] = financial_analysis['is_financial']
        result['financial_terms'] = financial_analysis['terms']
        
        # 3. Use fastText model if available
        model_prediction = self._predict_with_model(cleaned_text)
        
        # Combine the analyses to make a final decision
        final_decision = self._combine_analyses(
            word_analysis=word_analysis,
            model_prediction=model_prediction,
            financial_analysis=financial_analysis
        )
        
        # Update the result with the final decision
        result.update(final_decision)
        
        # Check for mixed language (code-switching)
        if result['language'] != 'mixed' and min(result['language_distribution'].values()) > 0.2:
            result['language'] = 'mixed'
            # Adjust confidence based on the mixing ratio
            result['confidence'] = max(0.6, result['confidence'] - 0.2)
            
        return result
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and normalize the input text.
        
        Args:
            text: The input text to process.
            
        Returns:
            Cleaned and normalized text.
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs, email addresses
        text = re.sub(r'https?://\S+|www\.\S+|\S+@\S+', '', text)
        
        # Remove numbers and punctuation, but keep spaces and word boundaries
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _detect_short_text(self, text: str) -> Dict[str, Any]:
        """
        Detect language for very short texts using character n-grams.
        
        Args:
            text: The short input text.
            
        Returns:
            Language detection result dictionary.
        """
        # Define character patterns more common in Swahili
        sw_patterns = ['ng', 'ny', 'mw', 'kw', 'ch', 'sh', 'dh', 'th', 'mb', 'nd']
        
        # Count occurrences of Swahili patterns
        sw_count = sum(text.count(pattern) for pattern in sw_patterns)
        
        # Simple threshold-based decision
        if sw_count > 0 and sw_count >= len(text) / 10:
            return {
                'language': 'sw',
                'confidence': min(0.6 + (sw_count / len(text)), 0.9),  # Cap at 0.9
                'language_distribution': {'en': 0.1, 'sw': 0.9},
                'is_financial': False,
                'financial_terms': []
            }
        else:
            return {
                'language': 'en',  # Default to English for short ambiguous text
                'confidence': 0.6,
                'language_distribution': {'en': 0.9, 'sw': 0.1},
                'is_financial': False,
                'financial_terms': []
            }
    
    def _analyze_word_frequency(self, text: str) -> Dict[str, Any]:
        """
        Analyze language based on the frequency of common words.
        
        Args:
            text: The preprocessed input text.
            
        Returns:
            Dictionary with word frequency analysis results.
        """
        # Tokenize the text
        words = word_tokenize(text)
        
        # Count words that match common words in each language
        lang_counts = {lang: 0 for lang in self.languages}
        for word in words:
            for lang, common_set in self.common_words.items():
                if word in common_set:
                    lang_counts[lang] += 1
        
        # Calculate percentages
        total_matched = sum(lang_counts.values())
        percentages = {
            lang: count / max(1, total_matched) 
            for lang, count in lang_counts.items()
        }
        
        # Determine dominant language
        if total_matched == 0:
            # No common words matched
            dominant_lang = 'unknown'
            confidence = 0.5
        else:
            dominant_lang = max(percentages, key=percentages.get)
            # Confidence based on the difference between the top two languages
            sorted_percs = sorted(percentages.values(), reverse=True)
            diff = sorted_percs[0] - (sorted_percs[1] if len(sorted_percs) > 1 else 0)
            confidence = 0.5 + (diff / 2)  # Scale to 0.5-1.0 range
        
        return {
            'language': dominant_lang,
            'confidence': confidence,
            'language_distribution': percentages
        }
    
    def _detect_financial_terms(self, text: str) -> Dict[str, Any]:
        """
        Detect financial terminology in the text.
        
        Args:
            text: The preprocessed input text.
            
        Returns:
            Dictionary with financial term analysis results.
        """
        words = word_tokenize(text)
        detected_terms = {
            'en': [],
            'sw': []
        }
        
        # Check for English financial terms (including multi-word terms)
        for term in self.financial_terms['en_to_sw'].keys():
            if term in text:
                detected_terms['en'].append(term)
        
        # Check for Swahili financial terms (including multi-word terms)
        for term in self.financial_terms['sw_to_en'].keys():
            if term in text:
                detected_terms['sw'].append(term)
        
        # Calculate the ratio of financial terms to total words
        all_terms = detected_terms['en'] + detected_terms['sw']
        financial_ratio = len(all_terms) / max(1, len(words))
        
        return {
            'is_financial': len(all_terms) > 0,
            'terms': all_terms,
            'financial_ratio': financial_ratio,
            'term_lang_distribution': {
                'en': len(detected_terms['en']) / max(1, len(all_terms)) if all_terms else 0,
                'sw': len(detected_terms['sw']) / max(1, len(all_terms)) if all_terms else 0
            }
        }
    
    def _predict_with_model(self, text: str) -> Dict[str, Any]:
        """
        Use the fastText model to predict the language.
        
        Args:
            text: The preprocessed input text.
            
        Returns:
            Dictionary with model prediction results, or empty if model isn't available.
        """
        if self.model is None:
            return {}
        
        try:
            # Get predictions from the model
            predictions = self.model.predict(text, k=len(self.languages))
            
            # Extract language labels and probabilities
            langs = [label.replace('__label__', '') for label in predictions[0]]
            probs = [float(p) for p in predictions[1]]
            
            # Create language distribution
            distribution = {lang: 0.0 for lang in self.languages}
            for lang, prob in zip(langs, probs):
                if lang in distribution:
                    distribution[lang] = prob
            
            # Determine dominant language
            dominant_lang = max(distribution, key=distribution.get)
            
            return {
                'language': dominant_lang,
                'confidence': distribution[dominant_lang],
                'language_distribution': distribution
            }
        except Exception as e:
            print(f"Error in model prediction: {e}")
            return {}
    
    def _combine_analyses(
        self, 
        word_analysis: Dict[str, Any], 
        model_prediction: Dict[str, Any],
        financial_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine different analyses to make a final language decision.
        
        Args:
            word_analysis: Results from word frequency analysis.
            model_prediction: Results from fastText model prediction.
            financial_analysis: Results from financial term detection.
            
        Returns:
            Dictionary with final language decision.
        """
        # If we have model prediction with high confidence, prioritize it
        if model_prediction and model_prediction.get('confidence', 0) > 0.8:
            final_decision = model_prediction.copy()
        else:
            # Otherwise, use word analysis as base
            final_decision = word_analysis.copy()
            
            # If we have model prediction, adjust distribution
            if model_prediction:
                # Merge language distributions with weighting
                model_weight = 0.7
                word_weight = 0.3
                
                for lang in self.languages:
                    final_decision['language_distribution'][lang] = (
                        model_weight * model_prediction['language_distribution'].get(lang, 0) +
                        word_weight * word_analysis['language_distribution'].get(lang, 0)
                    )
                
                # Update dominant language and confidence
                final_decision['language'] = max(
                    final_decision['language_distribution'], 
                    key=final_decision['language_distribution'].get
                )
                final_decision['confidence'] = final_decision['language_distribution'][final_decision['language']]
        
        # Adjust based on financial terms if present
        if financial_analysis['is_financial']:
            # If financial terms are predominantly in one language, boost its confidence
            term_dist = financial_analysis.get('term_lang_distribution', {})
            financial_lang = max(term_dist, key=term_dist.get) if term_dist else None
            
            if financial_lang and term_dist.get(financial_lang, 0) > 0.7:
                # If financial terms strongly indicate a different language
                if financial_lang != final_decision['language']:
                    # This might be mixed language text with financial terms in a different language
                    if term_dist.get(financial_lang, 0) > 0.9 and financial_analysis['financial_ratio'] > 0.3:
                        # Many financial terms in the minority language - probably mixed
                        final_decision['language'] = 'mixed'
                        final_decision['confidence'] = max(0.7, final_decision['confidence'] - 0.1)
                else:
                    # Financial terms agree with detected language - increase confidence
                    final_decision['confidence'] = min(1.0, final_decision['confidence'] + 0.1)
        
        return final_decision

    def is_english(self, text: str, threshold: float = 0.7) -> bool:
        """
        Check if the input text is in English.
        
        Args:
            text: The input text to analyze.
            threshold: Confidence threshold for language detection.
            
        Returns:
            True if the text is in English, False otherwise.
        """
        result = self.detect_language(text)
        return result['language'] == 'en' and result['confidence'] >= threshold
    
    def is_swahili(self, text: str, threshold: float = 0.7) -> bool:
        """
        Check if the input text is in Swahili.
        
        Args:
            text: The input text to analyze.
            threshold: Confidence threshold for language detection.
            
        Returns:
            True if the text is in Swahili, False otherwise.
        """
        result = self.detect_language(text)
        return result['language'] == 'sw' and result['confidence'] >= threshold
    
    def is_mixed(self, text: str) -> bool:
        """
        Check if the input text is mixed language (code-switched).
        
        Args:
            text: The input text to analyze.
            
        Returns:
            True if the text contains mixed languages, False otherwise.
        """
        result = self.detect_language(text)
        return result['language'] == 'mixed'
    
    def get_language_distribution(self, text: str) -> Dict[str, float]:
        """
        Get the distribution of languages in the text.
        
        Args:
            text: The input text to analyze.
            
        Returns:
            Dictionary mapping language codes to their percentage in the text.
        """
        result = self.detect_language(text)
        return result['language_distribution']
    
    def extract_financial_terms(self, text: str) -> Dict[str, List[str]]:
        """
        Extract financial terminology from the text, categorized by language.
        
        Args:
            text: The input text to analyze.
            
        Returns:
            Dictionary mapping language codes to lists of financial terms.
        """
        # Preprocess the text
        cleaned_text = self._preprocess_text(text)
        
        # Detect financial terms
        financial_analysis = self._detect_financial_terms(cleaned_text)
        
        # Categorize terms by language
        en_terms = []
        sw_terms = []
        
        for term in financial_analysis['terms']:
            if term in self.financial_terms['en_to_sw']:
                en_terms.append(term)
            elif term in self.financial_terms['sw_to_en']:
                sw_terms.append(term)
        
        return {
            'en': en_terms,
            'sw': sw_terms
        }

# Utility functions for direct use without instantiating the class
_detector = None

def detect_language(text: str) -> Dict[str, Any]:
    """
    Utility function to detect the language of the input text.
    
    Args:
        text: The input text to analyze.
        
    Returns:
        Dictionary with language detection results.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.detect_language(text)

def is_english(text: str, threshold: float = 0.7) -> bool:
    """
    Utility function to check if the input text is in English.
    
    Args:
        text: The input text to analyze.
        threshold: Confidence threshold for language detection.
        
    Returns:
        True if the text is in English, False otherwise.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.is_english(text, threshold)

def is_swahili(text: str, threshold: float = 0.7) -> bool:
    """
    Utility function to check if the input text is in Swahili.
    
    Args:
        text: The input text to analyze.
        threshold: Confidence threshold for language detection.
        
    Returns:
        True if the text is in Swahili, False otherwise.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.is_swahili(text, threshold)

def is_mixed(text: str) -> bool:
    """
    Utility function to check if the input text is mixed language.
    
    Args:
        text: The input text to analyze.
        
    Returns:
        True if the text contains mixed languages, False otherwise.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.is_mixed(text)

def get_language_distribution(text: str) -> Dict[str, float]:
    """
    Utility function to get the distribution of languages in the text.
    
    Args:
        text: The input text to analyze.
        
    Returns:
        Dictionary mapping language codes to their percentage in the text.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.get_language_distribution(text)

def extract_financial_terms(text: str) -> Dict[str, List[str]]:
    """
    Utility function to extract financial terminology from the text.
    
    Args:
        text: The input text to analyze.
        
    Returns:
        Dictionary mapping language codes to lists of financial terms.
    """
    global _detector
    if _detector is None:
        _detector = LanguageDetector()
    
    return _detector.extract_financial_terms(text)

# Example usage
if __name__ == "__main__":
    # Example texts
    examples = [
        "How can I invest in the Nairobi Stock Exchange?",
        "Nataka kuwekeza pesa zangu katika soko la hisa la Nairobi",
        "Ninahitaji loan ya biashara na interest rate nzuri",
        "I need a business loan with good interest rate",
        "Can you help me create a budget for my investments?",
        "Nisaidie kuunda bajeti ya uwekezaji wangu tafadhali"
    ]
    
    detector = LanguageDetector()
    
    for i, text in enumerate(examples):
        print(f"\nExample {i+1}: '{text}'")
        result = detector.detect_language(text)
        print(f"Language: {result['language']} (confidence: {result['confidence']:.2f})")
        print(f"Distribution: {result['language_distribution']}")
        if result['is_financial']:
            print(f"Financial terms: {result['financial_terms']}")
