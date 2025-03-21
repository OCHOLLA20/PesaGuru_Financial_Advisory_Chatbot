import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, mean_squared_error,
    r2_score, mean_absolute_percentage_error
)
from sklearn.model_selection import train_test_split
import joblib
import logging
from datetime import datetime

# Add parent directory to path to import from sibling directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PesaGuru modules
try:
    from nlp.text_preprocessor import TextPreprocessor
    from nlp.language_detector import LanguageDetector
    from services.sentiment_analysis import SentimentAnalyzer
    from models.intent_classifier import IntentClassifier
    from ai.nlp.entity_extractor import EntityExtractor
    from models.financial_bert import FinancialBERT
    from recommenders.investment_recommender import InvestmentRecommender
    from recommenders.market_predictor import MarketPredictor
    from recommenders.risk_analyzer import RiskAnalyzer
except ImportError as e:
    print(f"Error importing PesaGuru modules: {e}")
    print("Make sure the required modules are installed and in the PYTHONPATH")
    sys.exit(1)

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/model_evaluation_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """
    Handles evaluation of various models used in the PesaGuru chatbot.
    
    This class contains methods to evaluate different types of AI models:
    - Intent classification (for understanding user queries)
    - Named entity recognition (for extracting financial terms)
    - Sentiment analysis (for user interaction analysis)
    - Market prediction (for financial forecasting)
    - Portfolio recommendation (for investment advice)
    """
    
    def __init__(self, config_path="../config/model_evaluation_config.json"):
        """
        Initialize the model evaluator with paths and configurations.
        
        Args:
            config_path (str): Path to the evaluation configuration file
        """
        # Load configuration
        try:
            with open(config_path, 'r') as config_file:
                self.config = json.load(config_file)
            logger.info("Loaded model evaluation configuration")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found at {config_path}, using defaults")
            self.config = {
                "test_size": 0.2,
                "random_state": 42,
                "model_paths": {
                    "intent_classifier": "chatbot_model.pkl",
                    "sentiment_analyzer": "sentiment_model.pkl",
                    "entity_extractor": "entity_extractor.pkl",
                    "financial_bert": "financial_bert.pkl",
                    "market_predictor": "market_predictor.pkl",
                    "investment_recommender": "recommendation_model.pkl"
                },
                "data_paths": {
                    "intent_data": "../data/intent_training_data.csv",
                    "sentiment_data": "../data/sentiment_training_data.csv",
                    "entity_data": "../data/financial_terms_dictionary.json",
                    "market_data": "../data/market_prediction_data.csv",
                    "investment_data": "../data/investment_recommendation_data.csv",
                    "english_test": "../data/english_test_queries.csv",
                    "swahili_test": "../data/swahili_test_queries.csv",
                    "fairness_test": "../data/fairness_test_data.csv"
                },
                "output_paths": {
                    "reports": "reports/",
                    "visualizations": "visualizations/"
                }
            }
            
        # Initialize preprocessing components
        self.text_preprocessor = TextPreprocessor()
        self.language_detector = LanguageDetector()
        
        # Create output directories if they don't exist
        os.makedirs(self.config["output_paths"]["reports"], exist_ok=True)
        os.makedirs(self.config["output_paths"]["visualizations"], exist_ok=True)
        
        # Load the models
        self.load_models()
        
    def load_models(self):
        """
        Load all trained models for evaluation.
        """
        try:
            # Intent classification model
            model_path = self.config["model_paths"]["intent_classifier"]
            logger.info(f"Loading intent classification model from {model_path}")
            self.intent_classifier = joblib.load(model_path)
            
            # Sentiment analysis model
            model_path = self.config["model_paths"]["sentiment_analyzer"]
            logger.info(f"Loading sentiment analysis model from {model_path}")
            self.sentiment_analyzer = joblib.load(model_path)
            
            # Entity extraction model
            model_path = self.config["model_paths"]["entity_extractor"]
            logger.info(f"Loading entity extraction model from {model_path}")
            self.entity_extractor = joblib.load(model_path)
            
            # Financial BERT model
            model_path = self.config["model_paths"]["financial_bert"]
            logger.info(f"Loading financial BERT model from {model_path}")
            self.financial_bert = joblib.load(model_path)
            
            # Market prediction model
            model_path = self.config["model_paths"]["market_predictor"]
            logger.info(f"Loading market prediction model from {model_path}")
            self.market_predictor = joblib.load(model_path)
            
            # Investment recommendation model
            model_path = self.config["model_paths"]["investment_recommender"]
            logger.info(f"Loading investment recommendation model from {model_path}")
            self.investment_recommender = joblib.load(model_path)
            
        except FileNotFoundError as e:
            logger.error(f"Could not load a model: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
            
    def load_evaluation_data(self, data_type):
        """
        Load the appropriate evaluation dataset.
        
        Args:
            data_type (str): Type of data to load ('intent', 'sentiment', 'entity', 'market', 'investment')
            
        Returns:
            tuple: Containing features and labels for evaluation
        """
        try:
            if data_type == 'intent':
                # Load intent classification data
                data_path = self.config["data_paths"]["intent_data"]
                logger.info(f"Loading intent data from {data_path}")
                data = pd.read_csv(data_path)
                X = data['query'].values
                y = data['intent'].values
                return X, y
                
            elif data_type == 'sentiment':
                # Load sentiment analysis data
                data_path = self.config["data_paths"]["sentiment_data"]
                logger.info(f"Loading sentiment data from {data_path}")
                data = pd.read_csv(data_path)
                X = data['text'].values
                y = data['sentiment'].values
                return X, y
                
            elif data_type == 'entity':
                # Load NER data
                data_path = self.config["data_paths"]["entity_data"]
                logger.info(f"Loading entity data from {data_path}")
                with open(data_path, 'r') as f:
                    data = json.load(f)
                # Convert to the format needed for NER evaluation
                X = [item['text'] for item in data]
                y = [item['entities'] for item in data]
                return X, y
                
            elif data_type == 'market':
                # Load market prediction data
                data_path = self.config["data_paths"]["market_data"]
                logger.info(f"Loading market data from {data_path}")
                data = pd.read_csv(data_path)
                # Features include historical prices, indicators, etc.
                X = data.drop(['future_price', 'date'], axis=1, errors='ignore').values
                y = data['future_price'].values
                return X, y
                
            elif data_type == 'investment':
                # Load investment recommendation data
                data_path = self.config["data_paths"]["investment_data"]
                logger.info(f"Loading investment data from {data_path}")
                data = pd.read_csv(data_path)
                # Features include user risk profile, financial goals, etc.
                X = data.drop(['recommended_portfolio', 'user_id'], axis=1, errors='ignore').values
                y = data['recommended_portfolio'].values
                return X, y
                
            else:
                logger.error(f"Unknown data type: {data_type}")
                raise ValueError(f"Unknown data type: {data_type}")
                
        except (FileNotFoundError, KeyError) as e:
            logger.error(f"Error loading {data_type} data: {e}")
            raise
            
    def prepare_test_data(self, X, y, data_type):
        """
        Split data into train and test sets for evaluation.
        
        Args:
            X: Features
            y: Labels
            data_type (str): Type of data being processed
            
        Returns:
            tuple: X_test, y_test for model evaluation
        """
        # For most evaluations, we only need test data
        _, X_test, _, y_test = train_test_split(
            X, y, 
            test_size=self.config["test_size"], 
            random_state=self.config["random_state"],
            stratify=y if data_type in ['intent', 'sentiment', 'investment'] else None
        )
        
        return X_test, y_test
    
    def evaluate_intent_classifier(self):
        """
        Evaluate the intent classification model.
        
        Returns:
            dict: Metrics for the intent classifier
        """
        logger.info("Evaluating intent classification model...")
        
        # Load and prepare data
        X, y = self.load_evaluation_data('intent')
        X_test, y_test = self.prepare_test_data(X, y, 'intent')
        
        # Preprocess test queries
        X_test_processed = [self.text_preprocessor.preprocess(query) for query in X_test]
        
        # Get predictions
        y_pred = self.intent_classifier.predict(X_test_processed)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }
        
        # Generate confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Generate classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save confusion matrix visualization
        plt.figure(figsize=(12, 10))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Intent Classification Confusion Matrix')
        plt.ylabel('True Intent')
        plt.xlabel('Predicted Intent')
        plt.savefig(f"{self.config['output_paths']['visualizations']}intent_confusion_matrix.png")
        
        # Save classification report
        with open(f"{self.config['output_paths']['reports']}intent_classification_report.json", 'w') as f:
            json.dump(report, f, indent=4)
            
        logger.info(f"Intent classifier metrics: {metrics}")
        return metrics
    
    def evaluate_sentiment_analyzer(self):
        """
        Evaluate the sentiment analysis model.
        
        Returns:
            dict: Metrics for the sentiment analyzer
        """
        logger.info("Evaluating sentiment analysis model...")
        
        # Load and prepare data
        X, y = self.load_evaluation_data('sentiment')
        X_test, y_test = self.prepare_test_data(X, y, 'sentiment')
        
        # Preprocess test queries
        X_test_processed = [self.text_preprocessor.preprocess(text) for text in X_test]
        
        # Get predictions
        y_pred = self.sentiment_analyzer.predict(X_test_processed)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }
        
        # Generate confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Generate classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save confusion matrix visualization
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Sentiment Analysis Confusion Matrix')
        plt.ylabel('True Sentiment')
        plt.xlabel('Predicted Sentiment')
        plt.savefig(f"{self.config['output_paths']['visualizations']}sentiment_confusion_matrix.png")
        
        # Save classification report
        with open(f"{self.config['output_paths']['reports']}sentiment_analysis_report.json", 'w') as f:
            json.dump(report, f, indent=4)
            
        logger.info(f"Sentiment analyzer metrics: {metrics}")
        return metrics
    
    def evaluate_entity_extractor(self):
        """
        Evaluate the named entity recognition model.
        
        Returns:
            dict: Metrics for the entity extractor
        """
        logger.info("Evaluating named entity recognition model...")
        
        # Load and prepare data
        X, y = self.load_evaluation_data('entity')
        X_test, y_test = self.prepare_test_data(X, y, 'entity')
        
        # Metrics to calculate
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        
        # Entity type metrics for detailed analysis
        entity_metrics = {}
        
        # Evaluate each test sample
        for text, true_entities in zip(X_test, y_test):
            # Get predicted entities
            predicted_entities = self.entity_extractor.extract_entities(text)
            
            # Calculate metrics
            # For each true entity, check if it was predicted correctly
            for true_entity in true_entities:
                entity_type = true_entity['type']
                
                # Initialize entity type metrics if not already present
                if entity_type not in entity_metrics:
                    entity_metrics[entity_type] = {
                        'true_positives': 0,
                        'false_negatives': 0,
                        'false_positives': 0
                    }
                
                found = False
                for pred_entity in predicted_entities:
                    # Check if entity type and span match
                    if (true_entity['type'] == pred_entity['type'] and
                            true_entity['start'] == pred_entity['start'] and
                            true_entity['end'] == pred_entity['end']):
                        found = True
                        break
                
                if found:
                    true_positives += 1
                    entity_metrics[entity_type]['true_positives'] += 1
                else:
                    false_negatives += 1
                    entity_metrics[entity_type]['false_negatives'] += 1
            
            # For each predicted entity, check if it was a false positive
            for pred_entity in predicted_entities:
                entity_type = pred_entity['type']
                
                # Initialize entity type metrics if not already present
                if entity_type not in entity_metrics:
                    entity_metrics[entity_type] = {
                        'true_positives': 0,
                        'false_negatives': 0,
                        'false_positives': 0
                    }
                
                found = False
                for true_entity in true_entities:
                    # Check if entity type and span match
                    if (true_entity['type'] == pred_entity['type'] and
                            true_entity['start'] == pred_entity['start'] and
                            true_entity['end'] == pred_entity['end']):
                        found = True
                        break
                
                if not found:
                    false_positives += 1
                    entity_metrics[entity_type]['false_positives'] += 1
        
        # Calculate precision, recall, and F1 for each entity type
        for entity_type, metrics in entity_metrics.items():
            tp = metrics['true_positives']
            fp = metrics['false_positives']
            fn = metrics['false_negatives']
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            entity_metrics[entity_type]['precision'] = precision
            entity_metrics[entity_type]['recall'] = recall
            entity_metrics[entity_type]['f1'] = f1
        
        # Calculate overall precision, recall, and F1
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'entity_metrics': entity_metrics
        }
        
        # Save entity extraction report
        with open(f"{self.config['output_paths']['reports']}entity_extraction_report.json", 'w') as f:
            json.dump(metrics, f, indent=4)
            
        # Create a visualization of entity extraction performance by type
        plt.figure(figsize=(14, 8))
        entity_types = list(entity_metrics.keys())
        f1_scores = [entity_metrics[et]['f1'] for et in entity_types]
        
        # Sort by F1 score for better visualization
        sorted_indices = np.argsort(f1_scores)[::-1]
        sorted_entity_types = [entity_types[i] for i in sorted_indices]
        sorted_f1_scores = [f1_scores[i] for i in sorted_indices]
        
        sns.barplot(x=sorted_entity_types, y=sorted_f1_scores)
        plt.title('Entity Extraction Performance by Entity Type (F1 Score)')
        plt.ylabel('F1 Score')
        plt.xlabel('Entity Type')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f"{self.config['output_paths']['visualizations']}entity_extraction_by_type.png")
        
        logger.info(f"Entity extractor metrics: {metrics}")
        return metrics
    
    def evaluate_market_predictor(self):
        """
        Evaluate the market prediction model.
        
        Returns:
            dict: Metrics for the market predictor
        """
        logger.info("Evaluating market prediction model...")
        
        # Load and prepare data
        X, y = self.load_evaluation_data('market')
        X_test, y_test = self.prepare_test_data(X, y, 'market')
        
        # Get predictions
        y_pred = self.market_predictor.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate MAPE
        mape = mean_absolute_percentage_error(y_test, y_pred) * 100
        
        metrics = {
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'mape': mape
        }
        
        # Save market prediction report
        with open(f"{self.config['output_paths']['reports']}market_prediction_report.json", 'w') as f:
            json.dump(metrics, f, indent=4)
        
        # Create a visualization of predicted vs actual prices
        plt.figure(figsize=(12, 6))
        plt.scatter(y_test, y_pred, alpha=0.5)
        plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], 'r--')
        plt.title('Market Prediction: Actual vs Predicted')
        plt.xlabel('Actual Price')
        plt.ylabel('Predicted Price')
        plt.savefig(f"{self.config['output_paths']['visualizations']}market_prediction_scatter.png")
        
        # Create residual plot
        plt.figure(figsize=(12, 6))
        residuals = y_test - y_pred
        plt.scatter(y_test, residuals, alpha=0.5)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title('Market Prediction: Residuals')
        plt.xlabel('Actual Price')
        plt.ylabel('Residual (Actual - Predicted)')
        plt.savefig(f"{self.config['output_paths']['visualizations']}market_prediction_residuals.png")
        
        logger.info(f"Market predictor metrics: {metrics}")
        return metrics
    
    def evaluate_investment_recommender(self):
        """
        Evaluate the investment recommendation model.
        
        Returns:
            dict: Metrics for the investment recommender
        """
        logger.info("Evaluating investment recommendation model...")
        
        # Load and prepare data
        X, y = self.load_evaluation_data('investment')
        X_test, y_test = self.prepare_test_data(X, y, 'investment')
        
        # Get recommendations
        y_pred = self.investment_recommender.recommend(X_test)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1': f1_score(y_test, y_pred, average='weighted')
        }
        
        # Generate confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Generate classification report
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save confusion matrix visualization
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Investment Recommendation Confusion Matrix')
        plt.ylabel('True Portfolio')
        plt.xlabel('Recommended Portfolio')
        plt.savefig(f"{self.config['output_paths']['visualizations']}investment_confusion_matrix.png")
        
        # Save recommendation report
        with open(f"{self.config['output_paths']['reports']}investment_recommendation_report.json", 'w') as f:
            json.dump(report, f, indent=4)
            
        logger.info(f"Investment recommender metrics: {metrics}")
        return metrics
    
    def evaluate_all_models(self):
        """
        Evaluate all models and generate a comprehensive report.
        
        Returns:
            dict: Combined metrics for all models
        """
        logger.info("Starting comprehensive evaluation of all models...")
        
        # Evaluate each model
        intent_metrics = self.evaluate_intent_classifier()
        sentiment_metrics = self.evaluate_sentiment_analyzer()
        entity_metrics = self.evaluate_entity_extractor()
        market_metrics = self.evaluate_market_predictor()
        investment_metrics = self.evaluate_investment_recommender()
        
        # Combine all metrics
        all_metrics = {
            'intent_classifier': intent_metrics,
            'sentiment_analyzer': sentiment_metrics,
            'entity_extractor': entity_metrics,
            'market_predictor': market_metrics,
            'investment_recommender': investment_metrics,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Save comprehensive report
        with open(f"{self.config['output_paths']['reports']}comprehensive_evaluation_report.json", 'w') as f:
            json.dump(all_metrics, f, indent=4)
        
        # Generate a visualization comparing model performances
        self._plot_model_comparison(all_metrics)
        
        logger.info("Completed comprehensive evaluation of all models.")
        return all_metrics
    
    def _plot_model_comparison(self, all_metrics):
        """
        Generate a visualization comparing the performance of different models.
        
        Args:
            all_metrics (dict): Metrics for all models
        """
        # Extract F1 scores for classification models
        models = ['Intent Classifier', 'Sentiment Analyzer', 'Entity Extractor', 'Investment Recommender']
        f1_scores = [
            all_metrics['intent_classifier']['f1'],
            all_metrics['sentiment_analyzer']['f1'],
            all_metrics['entity_extractor']['f1'],
            all_metrics['investment_recommender']['f1']
        ]
        
        # Create bar chart
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(x=models, y=f1_scores)
        plt.title('Model Comparison: F1 Scores')
        plt.ylabel('F1 Score')
        plt.ylim(0, 1)
        
        # Add value labels
        for i, v in enumerate(f1_scores):
            ax.text(i, v + 0.02, f'{v:.2f}', ha='center')
            
        plt.savefig(f"{self.config['output_paths']['visualizations']}model_comparison_f1.png")
        
        # Create a separate chart for regression metrics (R2 for market predictor)
        plt.figure(figsize=(8, 6))
        plt.bar(['Market Predictor'], [all_metrics['market_predictor']['r2']])
        plt.title('Market Predictor: R² Score')
        plt.ylabel('R² Score')
        plt.ylim(0, 1)
        plt.text(0, all_metrics['market_predictor']['r2'] + 0.02, 
                 f"{all_metrics['market_predictor']['r2']:.2f}", ha='center')
        plt.savefig(f"{self.config['output_paths']['visualizations']}market_predictor_r2.png")
        
    def evaluate_cross_lingual_performance(self):
        """
        Evaluate how well the models perform across English and Swahili.
        
        This method is specific to the PesaGuru requirement for multilingual support.
        
        Returns:
            dict: Metrics for cross-lingual performance
        """
        logger.info("Evaluating cross-lingual model performance...")
        
        try:
            # Load English and Swahili test data
            english_data_path = self.config["data_paths"]["english_test"]
            swahili_data_path = self.config["data_paths"]["swahili_test"]
            
            logger.info(f"Loading English test data from {english_data_path}")
            english_data = pd.read_csv(english_data_path)
            
            logger.info(f"Loading Swahili test data from {swahili_data_path}")
            swahili_data = pd.read_csv(swahili_data_path)
            
            # Evaluate intent classification for both languages
            english_queries = english_data['query'].values
            english_intents = english_data['intent'].values
            english_processed = [self.text_preprocessor.preprocess(query) for query in english_queries]
            english_pred = self.intent_classifier.predict(english_processed)
            english_metrics = {
                'accuracy': accuracy_score(english_intents, english_pred),
                'f1': f1_score(english_intents, english_pred, average='weighted')
            }
            
            swahili_queries = swahili_data['query'].values
            swahili_intents = swahili_data['intent'].values
            swahili_processed = [self.text_preprocessor.preprocess(query) for query in swahili_queries]
            swahili_pred = self.intent_classifier.predict(swahili_processed)
            swahili_metrics = {
                'accuracy': accuracy_score(swahili_intents, swahili_pred),
                'f1': f1_score(swahili_intents, swahili_pred, average='weighted')
            }
            
            # Compare performance
            cross_lingual_metrics = {
                'english': english_metrics,
                'swahili': swahili_metrics,
                'performance_gap': {
                    'accuracy': english_metrics['accuracy'] - swahili_metrics['accuracy'],
                    'f1': english_metrics['f1'] - swahili_metrics['f1']
                }
            }
            
            # Save cross-lingual report
            with open(f"{self.config['output_paths']['reports']}cross_lingual_performance.json", 'w') as f:
                json.dump(cross_lingual_metrics, f, indent=4)
            
            # Create comparison visualization
            labels = ['Accuracy', 'F1 Score']
            english_scores = [english_metrics['accuracy'], english_metrics['f1']]
            swahili_scores = [swahili_metrics['accuracy'], swahili_metrics['f1']]
            
            x = np.arange(len(labels))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(10, 6))
            english_bars = ax.bar(x - width/2, english_scores, width, label='English')
            swahili_bars = ax.bar(x + width/2, swahili_scores, width, label='Swahili')
            
            ax.set_title('Cross-Lingual Performance Comparison')
            ax.set_ylabel('Score')
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
            ax.legend()
            
            # Add value labels
            for bars in [english_bars, swahili_bars]:
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.2f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),
                                textcoords="offset points",
                                ha='center', va='bottom')
            
            plt.savefig(f"{self.config['output_paths']['visualizations']}cross_lingual_comparison.png")
            
            logger.info(f"Cross-lingual performance metrics: {cross_lingual_metrics}")
            return cross_lingual_metrics
            
        except FileNotFoundError as e:
            logger.error(f"Could not load cross-lingual test data: {e}")
            logger.warning("Skipping cross-lingual evaluation")
            return {"error": "Test data not found"}
    
    def evaluate_bias_fairness(self):
        """
        Evaluate the bias and fairness of the recommendation models.
        
        This is crucial for financial services to ensure equitable treatment.
        
        Returns:
            dict: Bias and fairness metrics
        """
        logger.info("Evaluating bias and fairness in recommendation models...")
        
        # Load test data with demographic information
        try:
            fairness_data_path = self.config["data_paths"]["fairness_test"]
            logger.info(f"Loading fairness test data from {fairness_data_path}")
            fairness_data = pd.read_csv(fairness_data_path)
        except FileNotFoundError:
            logger.error("Fairness test data not found. Skipping bias evaluation.")
            return {"error": "Fairness test data not found"}
        
        # Prepare features and true labels
        X = fairness_data.drop(['recommended_portfolio', 'gender', 'age_group', 'income_level'], axis=1).values
        y_true = fairness_data['recommended_portfolio'].values
        
        # Get predictions
        y_pred = self.investment_recommender.recommend(X)
        
        # Calculate overall accuracy
        overall_accuracy = accuracy_score(y_true, y_pred)
        
        # Calculate metrics by demographic groups
        gender_metrics = {}
        for gender in fairness_data['gender'].unique():
            gender_mask = fairness_data['gender'] == gender
            gender_y_true = y_true[gender_mask]
            gender_y_pred = y_pred[gender_mask]
            gender_metrics[gender] = {
                'accuracy': accuracy_score(gender_y_true, gender_y_pred),
                'sample_size': sum(gender_mask)
            }
        
        age_metrics = {}
        for age_group in fairness_data['age_group'].unique():
            age_mask = fairness_data['age_group'] == age_group
            age_y_true = y_true[age_mask]
            age_y_pred = y_pred[age_mask]
            age_metrics[age_group] = {
                'accuracy': accuracy_score(age_y_true, age_y_pred),
                'sample_size': sum(age_mask)
            }
        
        income_metrics = {}
        for income_level in fairness_data['income_level'].unique():
            income_mask = fairness_data['income_level'] == income_level
            income_y_true = y_true[income_mask]
            income_y_pred = y_pred[income_mask]
            income_metrics[income_level] = {
                'accuracy': accuracy_score(income_y_true, income_y_pred),
                'sample_size': sum(income_mask)
            }
        
        # Calculate disparate impact
        # For simplicity, we're comparing accuracy across groups
        # A more thorough analysis would examine specific recommendation patterns
        bias_metrics = {
            'overall_accuracy': overall_accuracy,
            'gender_metrics': gender_metrics,
            'age_metrics': age_metrics,
            'income_metrics': income_metrics,
            'disparate_impact': {
                'gender': max([metrics['accuracy'] for metrics in gender_metrics.values()]) - 
                         min([metrics['accuracy'] for metrics in gender_metrics.values()]),
                'age': max([metrics['accuracy'] for metrics in age_metrics.values()]) - 
                      min([metrics['accuracy'] for metrics in age_metrics.values()]),
                'income': max([metrics['accuracy'] for metrics in income_metrics.values()]) - 
                         min([metrics['accuracy'] for metrics in income_metrics.values()])
            }
        }
        
        # Save bias evaluation report
        with open(f"{self.config['output_paths']['reports']}bias_fairness_report.json", 'w') as f:
            json.dump(bias_metrics, f, indent=4)
        
        # Create visualizations comparing performance across demographic groups
        # Gender comparison
        plt.figure(figsize=(12, 6))
        gender_labels = list(gender_metrics.keys())
        gender_accuracies = [metrics['accuracy'] for metrics in gender_metrics.values()]
        
        ax = plt.bar(gender_labels, gender_accuracies)
        plt.title('Model Accuracy by Gender')
        plt.ylabel('Accuracy')
        plt.ylim(0, 1)
        for i, acc in enumerate(gender_accuracies):
            plt.text(i, acc + 0.02, f'{acc:.2f}', ha='center')
        plt.savefig(f"{self.config['output_paths']['visualizations']}gender_fairness.png")
        
        # Age group comparison
        plt.figure(figsize=(12, 6))
        age_labels = list(age_metrics.keys())
        age_accuracies = [metrics['accuracy'] for metrics in age_metrics.values()]
        
        ax = plt.bar(age_labels, age_accuracies)
        plt.title('Model Accuracy by Age Group')
        plt.ylabel('Accuracy')
        plt.ylim(0, 1)
        for i, acc in enumerate(age_accuracies):
            plt.text(i, acc + 0.02, f'{acc:.2f}', ha='center')
        plt.savefig(f"{self.config['output_paths']['visualizations']}age_fairness.png")
        
        # Income level comparison
        plt.figure(figsize=(12, 6))
        income_labels = list(income_metrics.keys())
        income_accuracies = [metrics['accuracy'] for metrics in income_metrics.values()]
        
        ax = plt.bar(income_labels, income_accuracies)
        plt.title('Model Accuracy by Income Level')
        plt.ylabel('Accuracy')
        plt.ylim(0, 1)
        for i, acc in enumerate(income_accuracies):
            plt.text(i, acc + 0.02, f'{acc:.2f}', ha='center')
        plt.savefig(f"{self.config['output_paths']['visualizations']}income_fairness.png")
        
        logger.info(f"Bias and fairness metrics: {bias_metrics}")
        return bias_metrics


def main():
    """
    Main function to run the evaluation process.
    """
    try:
        logger.info("Starting model evaluation process")
        
        # Initialize evaluator
        evaluator = ModelEvaluator()
        
        # Run comprehensive evaluation
        all_metrics = evaluator.evaluate_all_models()
        
        # Additional evaluations specific to PesaGuru requirements
        cross_lingual_metrics = evaluator.evaluate_cross_lingual_performance()
        bias_metrics = evaluator.evaluate_bias_fairness()
        
        logger.info("Model evaluation completed successfully")
        
        # Print summary of evaluation results
        print("\n=== PesaGuru Model Evaluation Summary ===")
        print(f"Evaluation completed at: {all_metrics['timestamp']}")
        
        print("\nIntent Classification:")
        print(f"Accuracy: {all_metrics['intent_classifier']['accuracy']:.4f}")
        print(f"F1 Score: {all_metrics['intent_classifier']['f1']:.4f}")
        
        print("\nSentiment Analysis:")
        print(f"Accuracy: {all_metrics['sentiment_analyzer']['accuracy']:.4f}")
        print(f"F1 Score: {all_metrics['sentiment_analyzer']['f1']:.4f}")
        
        print("\nEntity Extraction:")
        print(f"Precision: {all_metrics['entity_extractor']['precision']:.4f}")
        print(f"Recall: {all_metrics['entity_extractor']['recall']:.4f}")
        print(f"F1 Score: {all_metrics['entity_extractor']['f1']:.4f}")
        
        print("\nMarket Prediction:")
        print(f"RMSE: {all_metrics['market_predictor']['rmse']:.4f}")
        print(f"R² Score: {all_metrics['market_predictor']['r2']:.4f}")
        print(f"MAPE: {all_metrics['market_predictor']['mape']:.2f}%")
        
        print("\nInvestment Recommendation:")
        print(f"Accuracy: {all_metrics['investment_recommender']['accuracy']:.4f}")
        print(f"F1 Score: {all_metrics['investment_recommender']['f1']:.4f}")
        
        if 'error' not in cross_lingual_metrics:
            print("\nCross-Lingual Performance:")
            print(f"English F1: {cross_lingual_metrics['english']['f1']:.4f}")
            print(f"Swahili F1: {cross_lingual_metrics['swahili']['f1']:.4f}")
            print(f"Performance Gap (F1): {abs(cross_lingual_metrics['performance_gap']['f1']):.4f}")
        
        if 'error' not in bias_metrics:
            print("\nBias & Fairness Summary:")
            print(f"Overall Accuracy: {bias_metrics['overall_accuracy']:.4f}")
            print(f"Gender Disparity: {bias_metrics['disparate_impact']['gender']:.4f}")
            print(f"Age Group Disparity: {bias_metrics['disparate_impact']['age']:.4f}")
            print(f"Income Level Disparity: {bias_metrics['disparate_impact']['income']:.4f}")
        
        print("\nDetailed reports and visualizations saved to:")
        print(f"- Reports: {os.path.abspath(evaluator.config['output_paths']['reports'])}")
        print(f"- Visualizations: {os.path.abspath(evaluator.config['output_paths']['visualizations'])}")
        print("==========================================\n")
        
        return {
            'status': 'success',
            'model_metrics': all_metrics,
            'cross_lingual_metrics': cross_lingual_metrics,
            'bias_metrics': bias_metrics
        }
        
    except Exception as e:
        logger.error(f"Error during model evaluation: {e}", exc_info=True)
        print(f"Evaluation failed: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }


if __name__ == "__main__":
    main()
