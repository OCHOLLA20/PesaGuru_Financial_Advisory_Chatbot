import os
import sys
import json
import pickle
import argparse
import logging
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from typing import Dict, List, Tuple, Union, Any

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from nlp.text_preprocessor import TextPreProcessor
from nlp.tokenizer import Tokenizer
from nlp.language_detector import LanguageDetector
from nlp.swahili_processor import SwahiliProcessor
from services.sentiment_analysis import SentimentAnalyzer
from services.user_profiler import UserProfiler
from recommenders.risk_analyzer import RiskAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/train_chatbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PesaGuru-Training")

# Suppress tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

class ChatbotTrainer:
    """
    Main class for training the PesaGuru chatbot models.
    Handles data preparation, model training, and evaluation.
    """
    
    def __init__(self, 
                 data_path: str = "../data", 
                 model_type: str = "bert", 
                 language: str = "all",
                 model_save_path: str = "./",
                 use_gpu: bool = True) -> None:
        """
        Initialize the ChatbotTrainer with configuration parameters.
        
        Args:
            data_path: Path to the training data directory
            model_type: Type of model to train (bert, gpt, lstm)
            language: Language to train for (en, sw, all)
            model_save_path: Path to save trained models
            use_gpu: Whether to use GPU for training
        """
        self.data_path = data_path
        self.model_type = model_type.lower()
        self.language = language.lower()
        self.model_save_path = model_save_path
        
        # Set up device configuration
        if use_gpu and tf.config.list_physical_devices('GPU'):
            self.device = '/GPU:0'
            logger.info("Using GPU for training")
        else:
            self.device = '/CPU:0'
            logger.info("Using CPU for training")
            
        # Initialize NLP components
        self.text_processor = TextPreProcessor()
        self.tokenizer = Tokenizer()
        self.language_detector = LanguageDetector()
        self.swahili_processor = SwahiliProcessor() if language in ['sw', 'all'] else None
        
        # Initialize datasets
        self.intent_data = None
        self.entity_data = None
        self.response_templates = None
        self.financial_terms = None
        self.sentiment_data = None
        
        # Initialize models
        self.intent_model = None
        self.entity_model = None
        self.response_model = None
        
        # Training metrics
        self.metrics = {
            'intent_accuracy': 0.0,
            'entity_f1': 0.0,
            'response_perplexity': 0.0
        }
        
        logger.info(f"ChatbotTrainer initialized with model_type={model_type}, language={language}")

    def load_data(self) -> None:
        """
        Load and preprocess all necessary training data.
        """
        logger.info("Loading training data...")
        
        # Load intent training data
        intent_path = os.path.join(self.data_path, "intent_training_data.csv")
        self.intent_data = pd.read_csv(intent_path)
        logger.info(f"Loaded {len(self.intent_data)} intent training samples")
        
        # Load financial terms dictionary
        terms_path = os.path.join(self.data_path, "financial_terms_dictionary.json")
        with open(terms_path, 'r', encoding='utf-8') as f:
            self.financial_terms = json.load(f)
        logger.info(f"Loaded {len(self.financial_terms)} financial terms")
        
        # Load Kenya-specific financial corpus if available
        kenyan_corpus_path = os.path.join(self.data_path, "kenyan_financial_corpus.json")
        if os.path.exists(kenyan_corpus_path):
            with open(kenyan_corpus_path, 'r', encoding='utf-8') as f:
                kenyan_corpus = json.load(f)
                # Merge with financial terms
                self.financial_terms.update(kenyan_corpus)
            logger.info(f"Enhanced with {len(kenyan_corpus)} Kenya-specific financial terms")
        
        # Load Swahili corpus if required
        if self.language in ['sw', 'all']:
            swahili_path = os.path.join(self.data_path, "swahili_corpus.json")
            if os.path.exists(swahili_path):
                with open(swahili_path, 'r', encoding='utf-8') as f:
                    self.swahili_corpus = json.load(f)
                logger.info(f"Loaded {len(self.swahili_corpus)} Swahili language entries")
            else:
                logger.warning("Swahili corpus not found. Defaulting to English-only training.")
                self.language = 'en'
        
        # Load sentiment training data if available
        sentiment_path = os.path.join(self.data_path, "sentiment_training_data.csv")
        if os.path.exists(sentiment_path):
            self.sentiment_data = pd.read_csv(sentiment_path)
            logger.info(f"Loaded {len(self.sentiment_data)} sentiment training samples")
        
        # Load response templates
        templates_path = os.path.join(self.data_path, "response_templates.json")
        if os.path.exists(templates_path):
            with open(templates_path, 'r', encoding='utf-8') as f:
                self.response_templates = json.load(f)
            logger.info(f"Loaded {len(self.response_templates)} response templates")
        else:
            logger.warning("Response templates not found. Response generation will be limited.")
            self.response_templates = {}

    def preprocess_data(self) -> Dict[str, Any]:
        """
        Preprocess loaded data for training.
        
        Returns:
            Dict containing preprocessed data for each model type
        """
        logger.info("Preprocessing training data...")
        
        processed_data = {}
        
        # Process intent classification data
        if self.intent_data is not None:
            # Clean and tokenize text
            logger.info("Preprocessing intent classification data...")
            
            # Extract features and labels
            X_text = self.intent_data['query'].tolist()
            y_intent = self.intent_data['intent'].tolist()
            
            # Get unique intent labels
            unique_intents = sorted(list(set(y_intent)))
            intent_to_idx = {intent: idx for idx, intent in enumerate(unique_intents)}
            idx_to_intent = {idx: intent for intent, idx in intent_to_idx.items()}
            
            # Convert text to features based on model type
            if self.model_type == 'bert':
                # For BERT, we'll just clean the text but actual preprocessing 
                # will happen during model creation using BERT tokenizer
                X_processed = [self.text_processor.clean_text(text) for text in X_text]
                
                # Encode intents as integers
                y_processed = [intent_to_idx[intent] for intent in y_intent]
                
                processed_data['intent'] = {
                    'X': X_processed,
                    'y': y_processed,
                    'intent_to_idx': intent_to_idx,
                    'idx_to_intent': idx_to_intent,
                    'num_classes': len(unique_intents)
                }
                
            elif self.model_type in ['lstm', 'gpt']:
                # For LSTM and GPT, we'll tokenize the text
                X_processed = []
                for text in X_text:
                    clean_text = self.text_processor.clean_text(text)
                    tokens = self.tokenizer.tokenize(clean_text)
                    X_processed.append(tokens)
                
                # Create vocabulary
                all_tokens = [token for tokens in X_processed for token in tokens]
                unique_tokens = sorted(list(set(all_tokens)))
                vocab = {token: idx + 1 for idx, token in enumerate(unique_tokens)}  # 0 reserved for padding
                
                # Encode sequences
                X_encoded = [
                    [vocab.get(token, 0) for token in tokens] 
                    for tokens in X_processed
                ]
                
                # Pad sequences to the same length
                max_length = max(len(seq) for seq in X_encoded)
                X_padded = [
                    seq + [0] * (max_length - len(seq)) 
                    for seq in X_encoded
                ]
                
                # Encode intents as integers
                y_processed = [intent_to_idx[intent] for intent in y_intent]
                
                processed_data['intent'] = {
                    'X': X_padded,
                    'y': y_processed,
                    'vocab': vocab,
                    'intent_to_idx': intent_to_idx,
                    'idx_to_intent': idx_to_intent,
                    'num_classes': len(unique_intents),
                    'max_length': max_length
                }
        
        # Process Swahili data if needed
        if self.language in ['sw', 'all'] and hasattr(self, 'swahili_corpus'):
            logger.info("Processing Swahili data...")
            # Process Swahili data similar to English but with the Swahili processor
            # This is a simplified version; would be expanded in the actual implementation
            sw_queries = [item['query'] for item in self.swahili_corpus]
            sw_intents = [item['intent'] for item in self.swahili_corpus]
            
            # Process similar to above but using Swahili-specific methods if needed
            sw_processed = [self.swahili_processor.clean_text(text) for text in sw_queries]
            
            processed_data['swahili'] = {
                'X': sw_processed,
                'y': sw_intents
            }
        
        # Process sentiment data if available
        if self.sentiment_data is not None:
            logger.info("Processing sentiment analysis data...")
            # This would follow a similar pattern as intent classification
            # but with sentiment labels instead
            
        return processed_data

    def create_intent_model(self, processed_data: Dict[str, Any]) -> Any:
        """
        Create and initialize the intent classification model.
        
        Args:
            processed_data: Preprocessed training data
            
        Returns:
            Initialized but untrained model
        """
        logger.info(f"Creating intent classification model using {self.model_type}...")
        
        intent_data = processed_data.get('intent', {})
        if not intent_data:
            logger.error("No intent classification data available")
            return None
            
        if self.model_type == 'bert':
            # Import BERT-specific modules here to avoid dependencies if not used
            from transformers import TFBertForSequenceClassification, BertTokenizer
            
            # Initialize tokenizer
            tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
            
            # Prepare BERT inputs
            texts = intent_data['X']
            labels = np.array(intent_data['y'])
            
            # Tokenize all texts
            bert_inputs = tokenizer(
                texts,
                padding=True,
                truncation=True,
                return_tensors="tf",
                max_length=128
            )
            
            # Create the model
            with tf.device(self.device):
                model = TFBertForSequenceClassification.from_pretrained(
                    'bert-base-uncased',
                    num_labels=intent_data['num_classes']
                )
                
                # Compile the model
                optimizer = tf.keras.optimizers.Adam(learning_rate=3e-5)
                loss = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
                model.compile(optimizer=optimizer, loss=loss, metrics=['accuracy'])
                
            return {
                'model': model,
                'tokenizer': tokenizer,
                'inputs': bert_inputs,
                'labels': labels
            }
            
        elif self.model_type == 'lstm':
            # Create LSTM model for intent classification
            vocab_size = len(intent_data['vocab']) + 1  # +1 for padding token
            embedding_dim = 128
            lstm_units = 64
            
            X = np.array(intent_data['X'])
            y = np.array(intent_data['y'])
            
            with tf.device(self.device):
                model = tf.keras.Sequential([
                    tf.keras.layers.Embedding(vocab_size, embedding_dim, mask_zero=True),
                    tf.keras.layers.Bidirectional(tf.keras.layers.LSTM(lstm_units)),
                    tf.keras.layers.Dense(64, activation='relu'),
                    tf.keras.layers.Dropout(0.5),
                    tf.keras.layers.Dense(intent_data['num_classes'], activation='softmax')
                ])
                
                # Compile the model
                model.compile(
                    optimizer='adam',
                    loss='sparse_categorical_crossentropy',
                    metrics=['accuracy']
                )
                
            return {
                'model': model,
                'X': X,
                'y': y
            }
            
        elif self.model_type == 'gpt':
            # In a real implementation, this would use GPT or other transformer models
            # from Hugging Face or OpenAI. This is a simplified placeholder.
            logger.info("GPT model implementation would go here")
            # Actual implementation would be similar to BERT but using GPT models
            
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            return None

    def train_intent_model(self, model_data: Dict[str, Any], 
                           epochs: int = 10, 
                           batch_size: int = 16) -> Tuple[Any, Dict[str, float]]:
        """
        Train the intent classification model.
        
        Args:
            model_data: Model and associated training data
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Tuple of (trained model, metrics dictionary)
        """
        logger.info(f"Training intent classification model for {epochs} epochs with batch size {batch_size}...")
        
        if not model_data:
            logger.error("No model data provided for training")
            return None, {}
        
        model = model_data.get('model')
        if not model:
            logger.error("No model found in model_data")
            return None, {}
            
        if self.model_type == 'bert':
            # Train BERT model
            tokenizer = model_data['tokenizer']
            bert_inputs = model_data['inputs']
            labels = model_data['labels']
            
            # Split data into train and validation sets
            split_idx = int(len(labels) * 0.8)
            
            train_inputs = {k: v[:split_idx] for k, v in bert_inputs.items()}
            train_labels = labels[:split_idx]
            
            val_inputs = {k: v[split_idx:] for k, v in bert_inputs.items()}
            val_labels = labels[split_idx:]
            
            # Train the model
            with tf.device(self.device):
                history = model.fit(
                    train_inputs,
                    train_labels,
                    validation_data=(val_inputs, val_labels),
                    epochs=epochs,
                    batch_size=batch_size
                )
                
            # Extract metrics
            metrics = {
                'intent_accuracy': float(history.history['accuracy'][-1]),
                'val_intent_accuracy': float(history.history['val_accuracy'][-1]),
                'intent_loss': float(history.history['loss'][-1]),
                'val_intent_loss': float(history.history['val_loss'][-1])
            }
            
            return model, metrics
            
        elif self.model_type == 'lstm':
            # Train LSTM model
            X = model_data['X']
            y = model_data['y']
            
            # Split data into train and validation sets
            split_idx = int(len(y) * 0.8)
            
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train the model
            with tf.device(self.device):
                history = model.fit(
                    X_train, y_train,
                    validation_data=(X_val, y_val),
                    epochs=epochs,
                    batch_size=batch_size
                )
                
            # Extract metrics
            metrics = {
                'intent_accuracy': float(history.history['accuracy'][-1]),
                'val_intent_accuracy': float(history.history['val_accuracy'][-1]),
                'intent_loss': float(history.history['loss'][-1]),
                'val_intent_loss': float(history.history['val_loss'][-1])
            }
            
            return model, metrics
            
        elif self.model_type == 'gpt':
            # Placeholder for GPT model training
            logger.info("GPT model training would go here")
            return model, {'intent_accuracy': 0.0}
            
        else:
            logger.error(f"Unsupported model type: {self.model_type}")
            return None, {}

    def create_and_train_entity_model(self, processed_data: Dict[str, Any],
                                      epochs: int = 10, 
                                      batch_size: int = 16) -> Tuple[Any, Dict[str, float]]:
        """
        Create and train named entity recognition model for financial entities.
        
        Args:
            processed_data: Preprocessed training data
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Tuple of (trained model, metrics dictionary)
        """
        logger.info("Creating and training entity recognition model...")
        
        # In a real implementation, this would create and train a NER model
        # using transformers, spaCy, or custom models
        
        # Placeholder implementation
        logger.info("Entity recognition model would be trained here")
        
        # Return placeholder model and metrics
        return None, {'entity_f1': 0.0}

    def save_models(self, intent_model: Any, entity_model: Any) -> None:
        """
        Save trained models to disk.
        
        Args:
            intent_model: Trained intent classification model
            entity_model: Trained entity recognition model
        """
        logger.info("Saving trained models...")
        
        # Create timestamp for versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save intent model
        if intent_model is not None:
            if self.model_type == 'bert':
                # Save BERT model using transformers save_pretrained
                intent_save_path = os.path.join(self.model_save_path, f"intent_model_{self.model_type}_{timestamp}")
                os.makedirs(intent_save_path, exist_ok=True)
                intent_model.save_pretrained(intent_save_path)
                logger.info(f"Intent model saved to {intent_save_path}")
            else:
                # Save regular TensorFlow model
                intent_save_path = os.path.join(self.model_save_path, f"intent_model_{self.model_type}_{timestamp}.h5")
                intent_model.save(intent_save_path)
                logger.info(f"Intent model saved to {intent_save_path}")
        
        # Save entity model (placeholder)
        if entity_model is not None:
            entity_save_path = os.path.join(self.model_save_path, f"entity_model_{timestamp}.pkl")
            with open(entity_save_path, 'wb') as f:
                pickle.dump(entity_model, f)
            logger.info(f"Entity model saved to {entity_save_path}")
            
        # Save combined chatbot model with metadata
        chatbot_model = {
            'model_type': self.model_type,
            'language': self.language,
            'metrics': self.metrics,
            'intent_model_path': intent_save_path if intent_model is not None else None,
            'entity_model_path': entity_save_path if entity_model is not None else None,
            'timestamp': timestamp
        }
        
        chatbot_model_path = os.path.join(self.model_save_path, "chatbot_model.pkl")
        with open(chatbot_model_path, 'wb') as f:
            pickle.dump(chatbot_model, f)
        logger.info(f"Combined chatbot model metadata saved to {chatbot_model_path}")

    def train(self, epochs: int = 10, batch_size: int = 16) -> Dict[str, float]:
        """
        Full training pipeline: load data, preprocess, train models, save models.
        
        Args:
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Dictionary of training metrics
        """
        logger.info("Starting full training pipeline...")
        
        # Load and preprocess data
        self.load_data()
        processed_data = self.preprocess_data()
        
        # Create and train intent classification model
        intent_model_data = self.create_intent_model(processed_data)
        intent_model, intent_metrics = self.train_intent_model(
            intent_model_data, 
            epochs=epochs, 
            batch_size=batch_size
        )
        
        # Create and train entity recognition model
        entity_model, entity_metrics = self.create_and_train_entity_model(
            processed_data,
            epochs=epochs,
            batch_size=batch_size
        )
        
        # Update metrics
        self.metrics.update(intent_metrics)
        self.metrics.update(entity_metrics)
        
        # Save models
        self.save_models(intent_model, entity_model)
        
        logger.info("Training completed successfully")
        logger.info(f"Final metrics: {self.metrics}")
        
        return self.metrics


def main():
    """Main function to run the training script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train PesaGuru chatbot models')
    parser.add_argument('--data_path', type=str, default='../data',
                        help='Path to training data directory')
    parser.add_argument('--model_type', type=str, default='bert',
                        choices=['bert', 'lstm', 'gpt'],
                        help='Type of model to train')
    parser.add_argument('--language', type=str, default='all',
                        choices=['en', 'sw', 'all'],
                        help='Language(s) to train for')
    parser.add_argument('--epochs', type=int, default=10,
                        help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=16,
                        help='Batch size for training')
    parser.add_argument('--model_save_path', type=str, default='./',
                        help='Path to save trained models')
    parser.add_argument('--use_gpu', action='store_true',
                        help='Use GPU for training if available')
    
    args = parser.parse_args()
    
    # Initialize and run trainer
    trainer = ChatbotTrainer(
        data_path=args.data_path,
        model_type=args.model_type,
        language=args.language,
        model_save_path=args.model_save_path,
        use_gpu=args.use_gpu
    )
    
    metrics = trainer.train(epochs=args.epochs, batch_size=args.batch_size)
    
    # Print final metrics
    print("\n==== Training Results ====")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")


if __name__ == "__main__":
    main()
