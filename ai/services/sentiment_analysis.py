import os
import re
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Union, Optional

# NLP and ML libraries
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import spacy
import pickle

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('vader_lexicon')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    A sentiment analysis class for financial conversations.
    
    This class analyzes text to determine sentiment (positive, negative, neutral)
    and extract emotions that may be present in financial-related conversations.
    It supports both English and Swahili languages.
    """
    
    def __init__(self, model_path: Optional[str] = None, financial_terms_path: Optional[str] = None):
        """
        Initialize the Sentiment Analyzer.
        
        Args:
            model_path (str, optional): Path to a custom sentiment model
            financial_terms_path (str, optional): Path to financial terms dictionary
        """
        # Initialize sentiment analyzers
        self.vader = SentimentIntensityAnalyzer()
        
        # Load SpaCy language models
        try:
            self.nlp_en = spacy.load('en_core_web_sm')
            logger.info("Loaded English language model")
        except OSError:
            logger.warning("English model not found. Using basic spaCy model.")
            self.nlp_en = spacy.blank('en')
        
        # Load financial terms dictionary
        self.financial_terms = {}
        self.load_financial_terms(financial_terms_path)
        
        # Load custom ML model if available
        self.custom_model = None
        if model_path and os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.custom_model = pickle.load(f)
                logger.info(f"Loaded custom sentiment model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load custom model: {str(e)}")
        
        # Financial sentiment lexicon - specific terms with custom sentiment scores
        self.financial_sentiment_lexicon = {
            # English financial terms with sentiment scores
            "profit": 1.5,
            "loss": -1.5,
            "debt": -1.2,
            "savings": 1.2,
            "investment": 0.8,
            "risk": -0.5,
            "opportunity": 1.0,
            "crisis": -1.8,
            "growth": 1.3,
            "default": -1.7,
            "dividend": 1.2,
            "bankruptcy": -2.0,
            "fraud": -2.0,
            "interest": -0.3,  # Interest can be positive or negative depending on context
            "loan": -0.2,      # Loans can be seen as both helpful and burdensome
            "tax": -0.5,
            "budget": 0.5,
            "expense": -0.5,
            "income": 1.0,
            "wealth": 1.5,
            "poor": -1.5,
            "rich": 1.0,
            # Swahili financial terms
            "faida": 1.5,      # profit
            "hasara": -1.5,    # loss
            "deni": -1.2,      # debt
            "akiba": 1.2,      # savings
            "uwekezaji": 0.8,  # investment
            "hatari": -0.5,    # risk
            "fursa": 1.0,      # opportunity
            "mgogoro": -1.8,   # crisis
            "ukuaji": 1.3,     # growth
            "kushindwa": -1.7, # default
            "gawio": 1.2,      # dividend
            "kufilisika": -2.0,# bankruptcy
            "ulaghai": -2.0,   # fraud
            "riba": -0.3,      # interest
            "mkopo": -0.2,     # loan
            "ushuru": -0.5,    # tax
            "bajeti": 0.5,     # budget
            "gharama": -0.5,   # expense
            "mapato": 1.0,     # income
            "utajiri": 1.5,    # wealth
            "maskini": -1.5,   # poor
            "tajiri": 1.0,     # rich
        }
        
        # Emotion mapping for financial contexts
        self.financial_emotion_map = {
            "anxiety": ["worried", "anxious", "nervous", "uneasy", "stressed", "fear", 
                       "afraid", "concerned", "scared", "risk", "uncertain", "debt", "loan"],
            "frustration": ["frustrated", "annoyed", "irritated", "upset", "confused", 
                           "misunderstood", "difficult", "hard", "complex", "complicated"],
            "satisfaction": ["satisfied", "pleased", "happy", "content", "glad", "grateful", 
                            "appreciate", "profit", "gain", "growth", "success", "achievement"],
            "disappointment": ["disappointed", "sad", "unhappy", "dissatisfied", "regret", 
                              "unfortunate", "loss", "decline", "fail", "failure", "missed"],
            "hope": ["hope", "optimistic", "looking forward", "future", "potential", 
                    "opportunity", "possibilities", "prospect", "chance", "growth"],
            "confusion": ["confused", "unsure", "unclear", "don't understand", "complicated", 
                         "complex", "puzzled", "perplexed", "lost", "bewildered"],
            "trust": ["trust", "believe", "confidence", "reliable", "secure", "safe", 
                     "dependable", "trustworthy", "faith", "certain", "sure"],
            "distrust": ["distrust", "skeptical", "suspicious", "doubt", "questionable", 
                        "unreliable", "risky", "scam", "fraud", "deceptive", "misleading"]
        }
        
        # Swahili emotion words
        self.swahili_emotion_map = {
            "anxiety": ["wasiwasi", "hofu", "woga", "dhiki", "mfadhaiko", "mashaka"],
            "frustration": ["kukasirika", "kuudhi", "kero", "hasira", "chuki"],
            "satisfaction": ["kuridhika", "furaha", "shangwe", "furahi", "kusherehekea"],
            "disappointment": ["kukata tamaa", "huzuni", "sikitiko", "kusononesha"],
            "hope": ["matumaini", "tumaini", "taraja", "matarajio"],
            "confusion": ["kuchanganyikiwa", "kutatanisha", "shida", "mzongo"],
            "trust": ["imani", "kuamini", "tegemea", "hakika"],
            "distrust": ["mashaka", "kutokuamini", "shuku", "tilia shaka"]
        }
        
        # Language detection dictionary - common Swahili words for detection
        self.swahili_markers = set([
            "na", "ya", "wa", "kwa", "ni", "za", "katika", "la", "kuwa", "yake", 
            "hii", "huo", "hizi", "hayo", "hiyo", "hili", "kwamba", "ndio", "sana", 
            "cha", "kama", "tu", "lakini", "pia", "hata", "kwenye", "vya", "mimi", 
            "wewe", "yeye", "sisi", "nyinyi", "wao", "huyu", "huyo", "hawa"
        ])
        
        # Historical context for tracking sentiment over time
        self.sentiment_history = []
        
    def load_financial_terms(self, financial_terms_path: Optional[str] = None) -> None:
        """
        Load financial terms dictionary from a JSON file.
        
        Args:
            financial_terms_path (str, optional): Path to financial terms JSON
        """
        if not financial_terms_path:
            # Use default path from project structure
            financial_terms_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'data',
                'financial_terms_dictionary.json'
            )
        
        try:
            if os.path.exists(financial_terms_path):
                with open(financial_terms_path, 'r', encoding='utf-8') as f:
                    self.financial_terms = json.load(f)
                logger.info(f"Loaded {len(self.financial_terms)} financial terms")
            else:
                logger.warning(f"Financial terms dictionary not found at {financial_terms_path}")
        except Exception as e:
            logger.error(f"Error loading financial terms: {str(e)}")
    
    def detect_language(self, text: str) -> str:
        """
        Detect if the text is in English or Swahili.
        
        Args:
            text (str): Input text
            
        Returns:
            str: 'en' for English, 'sw' for Swahili
        """
        if not text:
            return 'en'
        
        # Simple language detection based on common words
        words = text.lower().split()
        swahili_word_count = sum(1 for word in words if word in self.swahili_markers)
        
        # If more than 15% of words are Swahili markers, classify as Swahili
        if swahili_word_count / max(len(words), 1) > 0.15:
            return 'sw'
        return 'en'
    
    def preprocess_text(self, text: str, language: str = 'en') -> str:
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text (str): Input text
            language (str): Language code ('en' or 'sw')
            
        Returns:
            str: Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove special characters and numbers
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # For English, remove stopwords
        if language == 'en':
            tokens = word_tokenize(text)
            filtered_tokens = [word for word in tokens if word not in stopwords.words('english')]
            text = ' '.join(filtered_tokens)
        
        return text
    
    def analyze_vader_sentiment(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment using VADER (Valence Aware Dictionary and sEntiment Reasoner).
        
        Args:
            text (str): Preprocessed text
            
        Returns:
            dict: VADER sentiment scores and classification
        """
        if not text:
            return {
                'compound': 0.0,
                'pos': 0.0,
                'neu': 1.0,
                'neg': 0.0,
                'sentiment': 'neutral'
            }
        
        # Get VADER sentiment scores
        sentiment_scores = self.vader.polarity_scores(text)
        
        # Classify sentiment based on compound score
        if sentiment_scores['compound'] >= 0.05:
            sentiment = 'positive'
        elif sentiment_scores['compound'] <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Add sentiment classification to the scores
        sentiment_scores['sentiment'] = sentiment
        
        return sentiment_scores
    
    def analyze_textblob_sentiment(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment using TextBlob.
        
        Args:
            text (str): Preprocessed text
            
        Returns:
            dict: TextBlob sentiment scores and classification
        """
        if not text:
            return {
                'polarity': 0.0,
                'subjectivity': 0.0,
                'sentiment': 'neutral'
            }
        
        # Get TextBlob sentiment scores
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Classify sentiment based on polarity
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment
        }
    
    def analyze_financial_sentiment(self, text: str) -> Dict[str, Union[float, str]]:
        """
        Analyze sentiment with a focus on financial terms.
        
        Args:
            text (str): Preprocessed text
            
        Returns:
            dict: Financial sentiment scores and classification
        """
        if not text:
            return {
                'financial_score': 0.0,
                'financial_sentiment': 'neutral',
                'financial_terms': []
            }
        
        words = text.lower().split()
        financial_terms_found = []
        financial_score = 0.0
        
        # Calculate sentiment based on financial lexicon
        for word in words:
            if word in self.financial_sentiment_lexicon:
                financial_score += self.financial_sentiment_lexicon[word]
                financial_terms_found.append(word)
        
        # Normalize the score based on number of financial terms found
        if financial_terms_found:
            financial_score /= max(len(financial_terms_found), 1)
        
        # Classify sentiment based on financial score
        if financial_score > 0.2:
            financial_sentiment = 'positive'
        elif financial_score < -0.2:
            financial_sentiment = 'negative'
        else:
            financial_sentiment = 'neutral'
        
        return {
            'financial_score': financial_score,
            'financial_terms': financial_terms_found,
            'financial_sentiment': financial_sentiment
        }
    
    def detect_emotions(self, text: str, language: str = 'en') -> Dict[str, float]:
        """
        Detect emotions in the text specific to financial contexts.
        
        Args:
            text (str): Preprocessed text
            language (str): Language code ('en' or 'sw')
            
        Returns:
            dict: Emotion scores
        """
        if not text:
            return {}
        
        emotion_scores = {emotion: 0.0 for emotion in self.financial_emotion_map.keys()}
        words = text.lower().split()
        
        # Choose the appropriate emotion map based on language
        emotion_map = self.financial_emotion_map
        if language == 'sw':
            emotion_map = self.swahili_emotion_map
        
        # Count emotion words
        for emotion, emotion_words in emotion_map.items():
            for word in words:
                if word in emotion_words:
                    emotion_scores[emotion] += 1.0
        
        # Normalize scores
        total_emotion_words = sum(emotion_scores.values())
        if total_emotion_words > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= total_emotion_words
        
        # Keep only emotions with non-zero scores
        emotion_scores = {k: v for k, v in emotion_scores.items() if v > 0}
        
        return emotion_scores
    
    def analyze_sentiment(self, text: str, user_id: Optional[str] = None, 
                         context: Optional[Dict] = None) -> Dict:
        """
        Main method to analyze sentiment in text.
        
        Args:
            text (str): Input text
            user_id (str, optional): User identifier for tracking sentiment over time
            context (dict, optional): Additional context for sentiment analysis
            
        Returns:
            dict: Complete sentiment analysis results
        """
        if not text:
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0.0,
                'confidence': 0.0,
                'details': {
                    'vader': {
                        'compound': 0.0,
                        'sentiment': 'neutral'
                    },
                    'textblob': {
                        'polarity': 0.0,
                        'sentiment': 'neutral'
                    },
                    'financial': {
                        'financial_score': 0.0,
                        'financial_sentiment': 'neutral',
                        'financial_terms': []
                    }
                },
                'emotions': {},
                'language': 'en'
            }
        
        # Detect language
        language = self.detect_language(text)
        
        # Preprocess text
        preprocessed_text = self.preprocess_text(text, language)
        
        # Analyze sentiment using different methods
        vader_results = self.analyze_vader_sentiment(preprocessed_text)
        textblob_results = self.analyze_textblob_sentiment(preprocessed_text)
        financial_results = self.analyze_financial_sentiment(preprocessed_text)
        
        # Detect emotions
        emotions = self.detect_emotions(preprocessed_text, language)
        
        # Combine sentiment scores with weights
        # Give more weight to financial sentiment for financial conversations
        has_financial_terms = len(financial_results.get('financial_terms', [])) > 0
        
        if has_financial_terms:
            # If financial terms are present, give more weight to financial sentiment
            vader_weight = 0.2
            textblob_weight = 0.2
            financial_weight = 0.6
        else:
            # Otherwise, rely more on general sentiment analysis
            vader_weight = 0.5
            textblob_weight = 0.4
            financial_weight = 0.1
        
        # Calculate overall sentiment score
        vader_score = vader_results['compound']
        textblob_score = textblob_results['polarity']
        financial_score = financial_results['financial_score']
        
        overall_score = (
            vader_weight * vader_score +
            textblob_weight * textblob_score +
            financial_weight * financial_score
        )
        
        # Determine overall sentiment
        if overall_score >= 0.05:
            overall_sentiment = 'positive'
        elif overall_score <= -0.05:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Calculate confidence based on agreement between methods
        methods = [vader_results['sentiment'], 
                  textblob_results['sentiment'], 
                  financial_results['financial_sentiment']]
        
        agreement_count = methods.count(overall_sentiment)
        confidence = agreement_count / len(methods)
        
        # Compile complete results
        results = {
            'overall_sentiment': overall_sentiment,
            'overall_score': overall_score,
            'confidence': confidence,
            'details': {
                'vader': vader_results,
                'textblob': textblob_results,
                'financial': financial_results
            },
            'emotions': emotions,
            'language': language
        }
        
        # Store sentiment history if user_id is provided
        if user_id:
            self.store_sentiment_history(user_id, results)
        
        return results
    
    def store_sentiment_history(self, user_id: str, sentiment_results: Dict) -> None:
        """
        Store sentiment analysis results for historical tracking.
        
        Args:
            user_id (str): User identifier
            sentiment_results (dict): Sentiment analysis results
        """
        # Create a simplified version of the results for storage
        history_entry = {
            'user_id': user_id,
            'timestamp': np.datetime64('now'),
            'sentiment': sentiment_results['overall_sentiment'],
            'score': sentiment_results['overall_score'],
            'emotions': sentiment_results['emotions']
        }
        
        self.sentiment_history.append(history_entry)
        
        # Limit history size to prevent memory issues
        if len(self.sentiment_history) > 1000:
            self.sentiment_history = self.sentiment_history[-1000:]
    
    def get_sentiment_trend(self, user_id: str, n_entries: int = 5) -> Dict:
        """
        Get sentiment trend for a specific user.
        
        Args:
            user_id (str): User identifier
            n_entries (int): Number of recent entries to consider
            
        Returns:
            dict: Sentiment trend analysis
        """
        # Filter history for the specific user
        user_history = [entry for entry in self.sentiment_history 
                       if entry['user_id'] == user_id]
        
        # Sort by timestamp (newest first) and take the most recent n_entries
        user_history.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_history = user_history[:n_entries]
        
        if not recent_history:
            return {
                'trend': 'neutral',
                'stability': 1.0,
                'frequent_emotions': []
            }
        
        # Calculate average sentiment score
        avg_score = sum(entry['score'] for entry in recent_history) / len(recent_history)
        
        # Determine trend
        if avg_score > 0.1:
            trend = 'positive'
        elif avg_score < -0.1:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        # Calculate stability (consistency of sentiment)
        scores = [entry['score'] for entry in recent_history]
        stability = 1.0 - min(1.0, np.std(scores) if len(scores) > 1 else 0)
        
        # Get most frequent emotions
        all_emotions = []
        for entry in recent_history:
            all_emotions.extend(entry['emotions'].keys())
        
        emotion_counts = {}
        for emotion in all_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Sort emotions by frequency
        frequent_emotions = sorted(
            emotion_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        return {
            'trend': trend,
            'avg_score': avg_score,
            'stability': stability,
            'frequent_emotions': [emotion for emotion, count in frequent_emotions]
        }

    def get_response_suggestion(self, sentiment_results: Dict) -> Dict:
        """
        Generate response suggestions based on sentiment analysis.
        
        Args:
            sentiment_results (dict): Sentiment analysis results
            
        Returns:
            dict: Response suggestions
        """
        sentiment = sentiment_results['overall_sentiment']
        emotions = sentiment_results['emotions']
        
        response_type = 'neutral'
        tone_adjustment = 'balanced'
        content_suggestions = []
        
        # Determine response type based on sentiment
        if sentiment == 'positive':
            response_type = 'encouraging'
            tone_adjustment = 'upbeat'
            content_suggestions.append('Acknowledge positive sentiment')
        elif sentiment == 'negative':
            response_type = 'empathetic'
            tone_adjustment = 'calm'
            content_suggestions.append('Address concerns with empathy')
        
        # Adjust based on emotions
        if 'anxiety' in emotions and emotions['anxiety'] > 0.3:
            response_type = 'reassuring'
            tone_adjustment = 'calm'
            content_suggestions.append('Provide clear, factual information to reduce anxiety')
            
        if 'frustration' in emotions and emotions['frustration'] > 0.3:
            response_type = 'helpful'
            tone_adjustment = 'patient'
            content_suggestions.append('Offer clear steps or solutions')
            
        if 'confusion' in emotions and emotions['confusion'] > 0.3:
            response_type = 'clarifying'
            tone_adjustment = 'simple'
            content_suggestions.append('Simplify explanation and check understanding')
            
        if 'trust' in emotions and emotions['trust'] > 0.3:
            response_type = 'collaborative'
            tone_adjustment = 'confident'
            content_suggestions.append('Provide detailed recommendations')
            
        if 'distrust' in emotions and emotions['distrust'] > 0.3:
            response_type = 'transparent'
            tone_adjustment = 'factual'
            content_suggestions.append('Provide sources and explain reasoning')
        
        # Financial context-specific suggestions
        financial_terms = sentiment_results['details']['financial'].get('financial_terms', [])
        if financial_terms:
            if 'debt' in financial_terms or 'loan' in financial_terms or 'mkopo' in financial_terms:
                content_suggestions.append('Provide balanced view of debt management')
                
            if 'investment' in financial_terms or 'uwekezaji' in financial_terms:
                content_suggestions.append('Include risk disclaimer with investment advice')
                
            if 'budget' in financial_terms or 'bajeti' in financial_terms:
                content_suggestions.append('Offer practical budgeting tips')
        
        return {
            'response_type': response_type,
            'tone_adjustment': tone_adjustment,
            'content_suggestions': content_suggestions
        }


# Example usage function
def analyze_text(text, user_id=None):
    """
    Example function to demonstrate usage of the SentimentAnalyzer.
    
    Args:
        text (str): Text to analyze
        user_id (str, optional): User identifier
        
    Returns:
        dict: Sentiment analysis results
    """
    analyzer = SentimentAnalyzer()
    results = analyzer.analyze_sentiment(text, user_id)
    
    # Print a summary of the results
    print(f"Text: {text}")
    print(f"Overall Sentiment: {results['overall_sentiment']} (Score: {results['overall_score']:.2f})")
    
    if results['emotions']:
        print("Emotions detected:")
        for emotion, score in results['emotions'].items():
            print(f"- {emotion}: {score:.2f}")
    
    return results


# If run as a script, perform a test analysis
if __name__ == "__main__":
    test_texts = [
        "I'm really happy with the investment returns I got this month!",
        "I'm worried about taking on too much debt for my business loan.",
        "The stock market is so confusing, I don't understand what to invest in.",
        "Ninafurahi kupata faida kubwa kutoka kwa uwekezaji wangu.", # Swahili: I'm happy to get good profits from my investment
        "I lost all my savings in that risky investment and now I'm broke."
    ]
    
    for text in test_texts:
        analyze_text(text, "test_user")
        print("-" * 50)
