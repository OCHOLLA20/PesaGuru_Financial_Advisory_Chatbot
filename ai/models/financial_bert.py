import os
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from transformers import (
    BertTokenizer, 
    BertForSequenceClassification, 
    BertForTokenClassification,
    BertConfig,
    AdamW, 
    get_linear_schedule_with_warmup
)

# Local imports - adjust paths based on your project structure
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from nlp.text_preprocessor import preprocess_text
from nlp.language_detector import detect_language
from nlp.tokenizer import KenyanFinancialTokenizer


class FinancialBERTConfig:
    """Configuration settings for the Financial BERT model."""
    
    def __init__(self):
        # Model configuration
        self.base_model = "bert-base-uncased"  # Starting point for fine-tuning
        self.financial_bert_path = os.path.join(os.path.dirname(__file__), "saved_models/financial_bert/")
        self.ner_model_path = os.path.join(os.path.dirname(__file__), "saved_models/financial_bert_ner/")
        self.sentiment_model_path = os.path.join(os.path.dirname(__file__), "saved_models/financial_bert_sentiment/")
        
        # Training parameters
        self.max_seq_length = 128
        self.batch_size = 16
        self.learning_rate = 2e-5
        self.epochs = 4
        self.warmup_steps = 0
        self.weight_decay = 0.01
        
        # Language support
        self.swahili_support = True
        
        # Financial categories for intent classification
        self.financial_classes = [
            "investment_advice",       # Investment recommendations
            "loan_information",        # Loan products and rates
            "budgeting",               # Budgeting and expense tracking
            "risk_assessment",         # Financial risk evaluation
            "market_trends",           # Market analysis and forecasts
            "retirement_planning",     # Retirement and pension plans
            "tax_planning",            # Tax advice and compliance
            "savings_goals",           # Savings strategies and goals
            "insurance",               # Insurance products and coverage
            "general_query"            # General financial questions
        ]
        
        # Sentiment categories
        self.sentiment_classes = [
            "positive",     # Bullish, optimistic
            "negative",     # Bearish, pessimistic 
            "neutral"       # Factual, no clear sentiment
        ]
        
        # Kenyan financial entity types for NER
        self.entity_types = [
            "BANK",             # Banking institutions (KCB, Equity)
            "INVESTMENT",       # Investment vehicles (stocks, bonds)
            "FINTECH",          # Financial technology (M-Pesa, Fuliza)
            "EXCHANGE",         # Financial exchanges (NSE)
            "INSTITUTION",      # Financial institutions (CBK, CMA)
            "INSURANCE",        # Insurance providers
            "PENSION",          # Pension schemes (NSSF)
            "HEALTHCARE",       # Healthcare finance (NHIF)
            "CURRENCY",         # Currency references (KES, USD)
            "AMOUNT"            # Money amounts
        ]
        
        # Kenya-specific financial entities
        self.financial_entities = {
            "BANK": ["KCB", "Equity Bank", "Co-operative Bank", "NCBA", "Absa", "Standard Chartered", "DTB", "Family Bank"],
            "FINTECH": ["M-Pesa", "Fuliza", "M-Shwari", "KCB-M-Pesa", "Tala", "Branch", "Zenka"],
            "EXCHANGE": ["NSE", "Nairobi Securities Exchange"],
            "INSTITUTION": ["CBK", "Central Bank of Kenya", "CMA", "Capital Markets Authority", "SASRA", "Sacco Societies Regulatory Authority"],
            "INVESTMENT": ["Treasury Bills", "T-Bills", "Treasury Bonds", "Sacco", "Unit Trust", "Shares", "Stocks", "REITs", "ETFs"],
            "INSURANCE": ["NHIF", "National Hospital Insurance Fund", "Britam", "Jubilee Insurance", "CIC Insurance", "Kenya Re"],
            "PENSION": ["NSSF", "National Social Security Fund", "Pension Fund", "Retirement Benefit"],
            "CURRENCY": ["KES", "Kenyan Shilling", "USD", "Dollar", "EUR", "Euro", "GBP", "Pound"]
        }


class FinancialDataset(Dataset):
    """PyTorch dataset for financial text data."""
    
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
        
    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    
    def __len__(self):
        return len(self.labels)


class FinancialNERDataset(Dataset):
    """PyTorch dataset for Named Entity Recognition tasks."""
    
    def __init__(self, texts, tags, tokenizer, label_map, max_len=128):
        self.texts = texts
        self.tags = tags
        self.tokenizer = tokenizer
        self.label_map = label_map
        self.max_len = max_len
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        tags = self.tags[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_len,
            return_offsets_mapping=True,
            return_tensors='pt'
        )
        
        # Align labels with tokenized text
        word_ids = encoding.word_ids()
        label_ids = []
        
        # Special tokens get -100 label ID
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            else:
                label_ids.append(self.label_map[tags[word_idx]])
                
        encoding['labels'] = torch.tensor(label_ids)
        
        # Remove offset mapping
        encoding.pop('offset_mapping')
        
        # Convert to regular tensors (not batched)
        return {key: val.squeeze(0) for key, val in encoding.items()}


class FinancialBERT:
    """
    Domain-specific BERT model for financial text understanding
    Fine-tuned on Kenyan financial terminology and contexts.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Financial BERT model.
        
        Args:
            config: Configuration object. If None, default config is used.
        """
        self.config = config or FinancialBERTConfig()
        self.logger = logging.getLogger(__name__)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        
        # Main classification model
        self.model = None
        self.tokenizer = None
        
        # NER model
        self.ner_model = None
        self.ner_tokenizer = None
        self.id_to_label = None
        self.label_to_id = None
        
        # Sentiment analysis model
        self.sentiment_model = None
        
    def load_model(self, model_path=None, model_type="classification"):
        """
        Load a pre-trained or fine-tuned model.
        
        Args:
            model_path: Path to load model from. If None, use config path.
            model_type: Type of model to load - "classification", "ner", or "sentiment"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if model_type == "classification":
                model_path = model_path or self.config.financial_bert_path
                
                if os.path.exists(model_path):
                    self.logger.info(f"Loading fine-tuned classification model from {model_path}")
                    self.model = BertForSequenceClassification.from_pretrained(model_path)
                    self.tokenizer = BertTokenizer.from_pretrained(model_path)
                else:
                    self.logger.info(f"Loading base model: {self.config.base_model}")
                    self.model = BertForSequenceClassification.from_pretrained(
                        self.config.base_model,
                        num_labels=len(self.config.financial_classes)
                    )
                    self.tokenizer = BertTokenizer.from_pretrained(self.config.base_model)
                    
                    # Add financial terms to tokenizer vocabulary
                    financial_dict = load_financial_dictionary()
                    self.tokenizer = enrich_financial_bert_vocabulary(self.tokenizer, financial_dict)
                    
                self.model.to(self.device)
                
            elif model_type == "ner":
                model_path = model_path or self.config.ner_model_path
                
                # Set up label mappings for NER
                self.id_to_label = {i: label for i, label in enumerate(["O"] + [f"B-{etype}" for etype in self.config.entity_types] + [f"I-{etype}" for etype in self.config.entity_types])}
                self.label_to_id = {v: k for k, v in self.id_to_label.items()}
                
                if os.path.exists(model_path):
                    self.logger.info(f"Loading fine-tuned NER model from {model_path}")
                    self.ner_model = BertForTokenClassification.from_pretrained(model_path)
                    self.ner_tokenizer = BertTokenizer.from_pretrained(model_path)
                else:
                    self.logger.info(f"Loading base NER model: {self.config.base_model}")
                    self.ner_model = BertForTokenClassification.from_pretrained(
                        self.config.base_model,
                        num_labels=len(self.id_to_label)
                    )
                    self.ner_tokenizer = BertTokenizer.from_pretrained(self.config.base_model)
                
                self.ner_model.to(self.device)
                
            elif model_type == "sentiment":
                model_path = model_path or self.config.sentiment_model_path
                
                if os.path.exists(model_path):
                    self.logger.info(f"Loading fine-tuned sentiment model from {model_path}")
                    self.sentiment_model = BertForSequenceClassification.from_pretrained(model_path)
                else:
                    self.logger.info(f"Loading base sentiment model: {self.config.base_model}")
                    self.sentiment_model = BertForSequenceClassification.from_pretrained(
                        self.config.base_model,
                        num_labels=len(self.config.sentiment_classes)
                    )
                
                if not self.tokenizer:
                    self.tokenizer = BertTokenizer.from_pretrained(self.config.base_model)
                    
                self.sentiment_model.to(self.device)
            
            else:
                self.logger.error(f"Unknown model type: {model_type}")
                return False
                
            return True
        except Exception as e:
            self.logger.error(f"Error loading {model_type} model: {str(e)}")
            return False
    
    def prepare_financial_dataset(self, data_path):
        """
        Prepare financial dataset for fine-tuning.
        
        Args:
            data_path: Path to financial corpus CSV file with 'text' and 'label' columns
        
        Returns:
            Tuple of (train_dataset, val_dataset)
        """
        try:
            # Load dataset
            df = pd.read_csv(data_path)
            self.logger.info(f"Loaded dataset with {len(df)} examples")
            
            # Verify expected columns
            if 'text' not in df.columns or 'label' not in df.columns:
                self.logger.error("Dataset must contain 'text' and 'label' columns")
                return None, None
            
            # Preprocess text
            df['processed_text'] = df['text'].apply(preprocess_text)
            
            # Convert label strings to indices if needed
            if df['label'].dtype == 'object':
                label_map = {label: i for i, label in enumerate(self.config.financial_classes)}
                df['label_id'] = df['label'].map(label_map)
            else:
                df['label_id'] = df['label']
            
            # Split dataset
            train_texts, val_texts, train_labels, val_labels = train_test_split(
                df['processed_text'].values, 
                df['label_id'].values,
                test_size=0.1,
                stratify=df['label_id'].values,
                random_state=42
            )
            
            # Tokenize texts
            train_encodings = self.tokenizer(
                train_texts.tolist(),
                truncation=True,
                padding='max_length',
                max_length=self.config.max_seq_length,
                return_tensors='pt'
            )
            
            val_encodings = self.tokenizer(
                val_texts.tolist(),
                truncation=True,
                padding='max_length',
                max_length=self.config.max_seq_length,
                return_tensors='pt'
            )
            
            # Create torch datasets
            train_dataset = FinancialDataset(train_encodings, train_labels)
            val_dataset = FinancialDataset(val_encodings, val_labels)
            
            return train_dataset, val_dataset
            
        except Exception as e:
            self.logger.error(f"Error preparing dataset: {str(e)}")
            return None, None
    
    def prepare_ner_dataset(self, data_path):
        """
        Prepare NER dataset for fine-tuning.
        
        Args:
            data_path: Path to NER dataset (JSON format with text and entity annotations)
            
        Returns:
            Tuple of (train_dataset, val_dataset)
        """
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                ner_data = json.load(f)
            
            texts = []
            tags_list = []
            
            for item in ner_data:
                text = item['text']
                entities = item['entities']
                
                # Create tag sequence (BIO tagging)
                tags = ['O'] * len(text.split())
                
                for entity in entities:
                    start_token = entity['start_token']
                    end_token = entity['end_token']
                    entity_type = entity['type']
                    
                    tags[start_token] = f"B-{entity_type}"
                    for i in range(start_token + 1, end_token + 1):
                        tags[i] = f"I-{entity_type}"
                
                texts.append(text)
                tags_list.append(tags)
            
            # Split into train and validation
            train_texts, val_texts, train_tags, val_tags = train_test_split(
                texts, tags_list, test_size=0.1, random_state=42
            )
            
            # Create datasets
            train_dataset = FinancialNERDataset(
                train_texts, train_tags, self.ner_tokenizer, self.label_to_id
            )
            
            val_dataset = FinancialNERDataset(
                val_texts, val_tags, self.ner_tokenizer, self.label_to_id
            )
            
            return train_dataset, val_dataset
            
        except Exception as e:
            self.logger.error(f"Error preparing NER dataset: {str(e)}")
            return None, None
    
    def fine_tune(self, train_dataset, val_dataset, model_type="classification"):
        """
        Fine-tune the BERT model on financial data.
        
        Args:
            train_dataset: Training dataset
            val_dataset: Validation dataset
            model_type: Type of model to fine-tune - "classification", "ner", or "sentiment"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if model_type == "classification":
                target_model = self.model
                model_save_path = self.config.financial_bert_path
                label_names = self.config.financial_classes
            elif model_type == "ner":
                target_model = self.ner_model
                model_save_path = self.config.ner_model_path
                label_names = list(self.id_to_label.values())
            elif model_type == "sentiment":
                target_model = self.sentiment_model
                model_save_path = self.config.sentiment_model_path
                label_names = self.config.sentiment_classes
            else:
                self.logger.error(f"Unknown model type: {model_type}")
                return False
            
            # Check if model is loaded
            if target_model is None:
                self.logger.error(f"{model_type} model not loaded. Call load_model first.")
                return False
            
            # Prepare training arguments
            train_loader = DataLoader(
                train_dataset, 
                batch_size=self.config.batch_size, 
                shuffle=True
            )
            
            val_loader = DataLoader(
                val_dataset, 
                batch_size=self.config.batch_size
            )
            
            # Prepare optimizer and scheduler
            optimizer = AdamW(
                target_model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
            
            total_steps = len(train_loader) * self.config.epochs
            
            scheduler = get_linear_schedule_with_warmup(
                optimizer,
                num_warmup_steps=self.config.warmup_steps,
                num_training_steps=total_steps
            )
            
            # Training loop
            best_val_loss = float('inf')
            
            for epoch in range(self.config.epochs):
                target_model.train()
                train_loss = 0
                
                for batch in train_loader:
                    target_model.zero_grad()
                    
                    input_ids = batch['input_ids'].to(self.device)
                    attention_mask = batch['attention_mask'].to(self.device)
                    labels = batch['labels'].to(self.device)
                    
                    outputs = target_model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels
                    )
                    
                    loss = outputs.loss
                    train_loss += loss.item()
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(target_model.parameters(), 1.0)
                    
                    optimizer.step()
                    scheduler.step()
                
                # Validation
                target_model.eval()
                val_loss = 0
                val_preds = []
                val_true = []
                
                with torch.no_grad():
                    for batch in val_loader:
                        input_ids = batch['input_ids'].to(self.device)
                        attention_mask = batch['attention_mask'].to(self.device)
                        labels = batch['labels'].to(self.device)
                        
                        outputs = target_model(
                            input_ids=input_ids,
                            attention_mask=attention_mask,
                            labels=labels
                        )
                        
                        loss = outputs.loss
                        val_loss += loss.item()
                        
                        logits = outputs.logits
                        
                        if model_type == "ner":
                            # For NER, we need to handle the special tokens (-100)
                            active_loss = labels.view(-1) != -100
                            active_logits = logits.view(-1, len(self.id_to_label))[active_loss]
                            active_labels = labels.view(-1)[active_loss]
                            
                            preds = torch.argmax(active_logits, dim=1).cpu().numpy()
                            val_preds.extend(preds)
                            val_true.extend(active_labels.cpu().numpy())
                        else:
                            # For classification and sentiment
                            preds = torch.argmax(logits, dim=1).cpu().numpy()
                            val_preds.extend(preds)
                            val_true.extend(labels.cpu().numpy())
                
                # Print epoch results
                avg_train_loss = train_loss / len(train_loader)
                avg_val_loss = val_loss / len(val_loader)
                
                self.logger.info(f"Epoch {epoch+1}/{self.config.epochs}")
                self.logger.info(f"Train Loss: {avg_train_loss:.4f}")
                self.logger.info(f"Val Loss: {avg_val_loss:.4f}")
                
                # Save if best model
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    
                    # Make sure directory exists
                    Path(model_save_path).mkdir(parents=True, exist_ok=True)
                    
                    # Save model
                    target_model.save_pretrained(model_save_path)
                    if model_type == "classification" or model_type == "sentiment":
                        self.tokenizer.save_pretrained(model_save_path)
                    elif model_type == "ner":
                        self.ner_tokenizer.save_pretrained(model_save_path)
                        
                    self.logger.info(f"Saved best model to {model_save_path} (val_loss: {avg_val_loss:.4f})")
                
                # Classification report
                try:
                    report = classification_report(
                        val_true, 
                        val_preds,
                        target_names=label_names,
                        digits=4
                    )
                    self.logger.info(f"Classification Report:\n{report}")
                except Exception as e:
                    self.logger.warning(f"Could not generate classification report: {str(e)}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error during fine-tuning: {str(e)}")
            return False
    
    def predict(self, text):
        """
        Classify financial text using the fine-tuned model.
        
        Args:
            text: Input text to classify
            
        Returns:
            dict: Prediction results with class and confidence
        """
        try:
            # Check if model is loaded
            if self.model is None:
                self.logger.error("Model not loaded. Call load_model first.")
                return None
            
            # Preprocess text
            processed_text = preprocess_text(text)
            
            # Check language and handle Swahili if needed
            language = detect_language(text)
            if language == 'sw' and self.config.swahili_support:
                # Additional Swahili processing would go here
                self.logger.info("Detected Swahili text")
            
            # Tokenize
            inputs = self.tokenizer(
                processed_text,
                return_tensors="pt",
                truncation=True,
                padding='max_length',
                max_length=self.config.max_seq_length
            ).to(self.device)
            
            # Make prediction
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=1)
            
            confidence, predicted_class = torch.max(probabilities, dim=1)
            
            result = {
                'class': self.config.financial_classes[predicted_class.item()],
                'confidence': confidence.item(),
                'probabilities': {
                    self.config.financial_classes[i]: prob.item() 
                    for i, prob in enumerate(probabilities[0])
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during prediction: {str(e)}")
            return None
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment in financial text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            dict: Sentiment analysis results
        """
        try:
            # Check if sentiment model is loaded
            if self.sentiment_model is None:
                self.logger.error("Sentiment model not loaded. Call load_model with 'sentiment' type.")
                return None
            
            # Preprocess text
            processed_text = preprocess_text(text)
            
            # Tokenize
            inputs = self.tokenizer(
                processed_text,
                return_tensors="pt",
                truncation=True,
                padding='max_length',
                max_length=self.config.max_seq_length
            ).to(self.device)
            
            # Make prediction
            self.sentiment_model.eval()
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=1)
            
            confidence, predicted_sentiment = torch.max(probabilities, dim=1)
            
            result = {
                'sentiment': self.config.sentiment_classes[predicted_sentiment.item()],
                'confidence': confidence.item(),
                'probabilities': {
                    self.config.sentiment_classes[i]: prob.item() 
                    for i, prob in enumerate(probabilities[0])
                }
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during sentiment analysis: {str(e)}")
            return None
    
    def extract_financial_entities(self, text):
        """
        Extract financial entities from text using NER capabilities.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            list: Extracted financial entities with type, text, and position
        """
        try:
            # Check if NER model is loaded
            if self.ner_model is None:
                self.logger.error("NER model not loaded. Call load_model with 'ner' type.")
                return None
            
            # Preprocess text
            processed_text = preprocess_text(text)
            
            # Tokenize with offset mapping to align with original text
            inputs = self.ner_tokenizer(
                processed_text,
                return_tensors="pt",
                truncation=True,
                padding='max_length',
                max_length=self.config.max_seq_length,
                return_offsets_mapping=True
            )
            
            # Extract offset mapping and remove it from inputs
            offset_mapping = inputs.pop("offset_mapping")
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Make prediction
            self.ner_model.eval()
            with torch.no_grad():
                outputs = self.ner_model(**inputs)
                
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=2)
            
            # Convert predictions to labels
            predicted_labels = [self.id_to_label[p.item()] for p in predictions[0]]
            
            # Extract entities
            entities = []
            current_entity = None
            
            for idx, (label, offset) in enumerate(zip(predicted_labels, offset_mapping[0])):
                # Skip special tokens
                if offset[0] == 0 and offset[1] == 0:
                    continue
                
                if label.startswith("B-"):
                    # End any current entity
                    if current_entity:
                        entities.append(current_entity)
                        current_entity = None
                    
                    # Start new entity
                    entity_type = label[2:]  # Remove "B-" prefix
                    current_entity = {
                        "type": entity_type,
                        "start": offset[0].item(),
                        "end": offset[1].item(),
                        "text": text[offset[0]:offset[1]]
                    }
                
                elif label.startswith("I-") and current_entity:
                    # Continue current entity if type matches
                    entity_type = label[2:]  # Remove "I-" prefix
                    if entity_type == current_entity["type"]:
                        current_entity["end"] = offset[1].item()
                        current_entity["text"] = text[current_entity["start"]:current_entity["end"]]
                
                elif label == "O" and current_entity:
                    # End current entity
                    entities.append(current_entity)
                    current_entity = None
            
            # Add the last entity if there is one
            if current_entity:
                entities.append(current_entity)
                
            return entities
            
        except Exception as e:
            self.logger.error(f"Error during entity extraction: {str(e)}")
            return None
    
    def rule_based_entity_extraction(self, text):
        """
        Fallback rule-based entity extraction when NER model is not available.
        
        Args:
            text: Input text to extract entities from
            
        Returns:
            list: Extracted financial entities
        """
        entities = []
        words = text.split()
        
        # Check each entity type
        for entity_type, entity_list in self.config.financial_entities.items():
            for entity in entity_list:
                entity_lower = entity.lower()
                text_lower = text.lower()
                
                # Check if entity exists in text
                if entity_lower in text_lower:
                    # Find all occurrences
                    start = 0
                    while True:
                        start = text_lower.find(entity_lower, start)
                        if start == -1:
                            break
                            
                        entities.append({
                            "type": entity_type,
                            "text": text[start:start+len(entity)],
                            "start": start,
                            "end": start+len(entity)
                        })
                        
                        start += len(entity)
        
        return entities


def load_financial_dictionary(dict_path=None):
    """
    Load financial terminology dictionary.
    
    Args:
        dict_path: Path to the dictionary file
        
    Returns:
        dict: Financial terminology dictionary
    """
    if dict_path is None:
        # Default path relative to this file
        dict_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # ai folder
            "data",
            "financial_terms_dictionary.json"
        )
    
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading financial dictionary: {str(e)}")
        return {}


def enrich_financial_bert_vocabulary(tokenizer, financial_dict):
    """
    Add financial terms to tokenizer vocabulary.
    
    Args:
        tokenizer: BERT tokenizer
        financial_dict: Dictionary of financial terms
        
    Returns:
        Enriched tokenizer
    """
    try:
        new_tokens = []
        for term_category in financial_dict.values():
            if isinstance(term_category, list):
                new_tokens.extend(term_category)
            elif isinstance(term_category, dict):
                for terms in term_category.values():
                    new_tokens.extend(terms)
        
        # Add Kenyan-specific financial terms
        kenyan_terms = [
            "M-Pesa", "M-Shwari", "Fuliza", "KCB-M-Pesa", "Tala", "Branch",
            "Nairobi Securities Exchange", "NSE", "Equity Bank", "KCB Group",
            "Safaricom", "Treasury Bills", "T-Bills", "Sacco", "NHIF", "NSSF",
            "matatu", "jua kali", "harambee", "chama", "CBK", "CMA"
        ]
        new_tokens.extend(kenyan_terms)
        
        # Remove duplicates
        new_tokens = list(set(new_tokens))
        
        # Add tokens to tokenizer
        num_added = tokenizer.add_tokens(new_tokens)
        logging.info(f"Added {num_added} financial terms to tokenizer vocabulary")
        
        return tokenizer
    except Exception as e:
        logging.error(f"Error enriching vocabulary: {str(e)}")
        return tokenizer


def evaluate_model(model_path, test_data_path, model_type="classification"):
    """
    Evaluate model performance on test dataset.
    
    Args:
        model_path: Path to the model
        test_data_path: Path to test dataset
        model_type: Type of model to evaluate
        
    Returns:
        dict: Evaluation metrics
    """
    try:
        # Initialize model
        finbert = FinancialBERT()
        finbert.load_model(model_path, model_type)
        
        # Load test dataset
        if model_type == "classification" or model_type == "sentiment":
            test_df = pd.read_csv(test_data_path)
            
            # Make predictions
            predictions = []
            true_labels = test_df['label'].values
            
            for text in test_df['text'].values:
                if model_type == "classification":
                    result = finbert.predict(text)
                    if result:
                        predictions.append(finbert.config.financial_classes.index(result['class']))
                    else:
                        predictions.append(-1)  # Error case
                else:  # sentiment
                    result = finbert.analyze_sentiment(text)
                    if result:
                        predictions.append(finbert.config.sentiment_classes.index(result['sentiment']))
                    else:
                        predictions.append(-1)  # Error case
            
            # Filter out error cases
            valid_indices = [i for i, p in enumerate(predictions) if p != -1]
            valid_predictions = [predictions[i] for i in valid_indices]
            valid_true_labels = [true_labels[i] for i in valid_indices]
            
            # Generate evaluation report
            report = classification_report(
                valid_true_labels,
                valid_predictions,
                target_names=(finbert.config.financial_classes if model_type == "classification" 
                              else finbert.config.sentiment_classes),
                output_dict=True
            )
            
            # Calculate confusion matrix
            cm = confusion_matrix(valid_true_labels, valid_predictions)
            
            return {
                "classification_report": report,
                "confusion_matrix": cm,
                "accuracy": accuracy_score(valid_true_labels, valid_predictions)
            }
            
        elif model_type == "ner":
            # NER evaluation is more complex and would be implemented separately
            logging.info("NER evaluation not implemented in this function")
            return None
            
    except Exception as e:
        logging.error(f"Error evaluating model: {str(e)}")
        return None


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"financial_bert_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial BERT Model Operations")
    parser.add_argument('--mode', type=str, choices=['train', 'predict', 'evaluate'], 
                         default='predict', help='Operation mode')
    parser.add_argument('--model_type', type=str, choices=['classification', 'ner', 'sentiment'],
                         default='classification', help='Model type')
    parser.add_argument('--data_path', type=str, help='Path to training/test data')
    parser.add_argument('--model_path', type=str, help='Path to save/load model')
    parser.add_argument('--input_text', type=str, help='Text for prediction (predict mode)')
    
    args = parser.parse_args()
    
    # Initialize FinancialBERT
    finbert = FinancialBERT()
    
    if args.mode == 'train':
        # Training mode
        if not args.data_path:
            logging.error("Data path required for training")
            exit(1)
            
        # Load model
        finbert.load_model(args.model_path, args.model_type)
        
        # Prepare dataset
        if args.model_type == 'classification' or args.model_type == 'sentiment':
            train_dataset, val_dataset = finbert.prepare_financial_dataset(args.data_path)
        elif args.model_type == 'ner':
            train_dataset, val_dataset = finbert.prepare_ner_dataset(args.data_path)
        
        if train_dataset and val_dataset:
            # Fine-tune model
            finbert.fine_tune(train_dataset, val_dataset, args.model_type)
        else:
            logging.error("Failed to prepare dataset")
            
    elif args.mode == 'predict':
        # Prediction mode
        if not args.input_text:
            logging.error("Input text required for prediction")
            exit(1)
            
        # Load model
        finbert.load_model(args.model_path, args.model_type)
        
        # Make prediction
        if args.model_type == 'classification':
            result = finbert.predict(args.input_text)
            if result:
                logging.info(f"Prediction: {result['class']} (Confidence: {result['confidence']:.4f})")
                
        elif args.model_type == 'sentiment':
            result = finbert.analyze_sentiment(args.input_text)
            if result:
                logging.info(f"Sentiment: {result['sentiment']} (Confidence: {result['confidence']:.4f})")
                
        elif args.model_type == 'ner':
            entities = finbert.extract_financial_entities(args.input_text)
            if entities:
                logging.info(f"Entities found: {len(entities)}")
                for entity in entities:
                    logging.info(f"  {entity['type']}: {entity['text']}")
            else:
                # Fallback to rule-based extraction
                entities = finbert.rule_based_entity_extraction(args.input_text)
                logging.info(f"Rule-based entities found: {len(entities)}")
                for entity in entities:
                    logging.info(f"  {entity['type']}: {entity['text']}")
                    
    elif args.mode == 'evaluate':
        # Evaluation mode
        if not args.data_path:
            logging.error("Test data path required for evaluation")
            exit(1)
            
        results = evaluate_model(args.model_path, args.data_path, args.model_type)
        if results:
            logging.info(f"Evaluation results:")
            logging.info(f"Accuracy: {results['accuracy']:.4f}")
            logging.info(f"Classification Report:\n{results['classification_report']}")
        else:
            logging.error("Evaluation failed")
    
    # Example usage
    if args.mode == 'example':
        # Load model
        finbert.load_model()
        
        # Example prediction
        sample_text = "I want to invest in Safaricom shares on the NSE. What should I know about their dividend policy?"
        result = finbert.predict(sample_text)
        logging.info(f"Prediction: {result['class']} (Confidence: {result['confidence']:.4f})")
        
        # Example NER
        finbert.load_model(model_type="ner")
        entities = finbert.extract_financial_entities(sample_text)
        logging.info(f"Entities found: {len(entities)}")
        for entity in entities:
            logging.info(f"  {entity['type']}: {entity['text']}")
