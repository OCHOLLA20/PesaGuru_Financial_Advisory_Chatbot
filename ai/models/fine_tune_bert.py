import os
import json
import argparse
import logging
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler
from transformers import (
    BertTokenizer, 
    BertForSequenceClassification, 
    BertForMaskedLM,
    BertConfig,
    AdamW, 
    get_linear_schedule_with_warmup,
    TrainingArguments,
    Trainer
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("../logs/fine_tune_bert.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinancialTextDataset(Dataset):
    """Dataset for financial text data from various Kenyan sources"""
    
    def __init__(self, texts, labels=None, tokenizer=None, max_length=512):
        """
        Initialize the dataset
        
        Args:
            texts (list): List of text samples
            labels (list, optional): List of labels (for classification tasks)
            tokenizer: BERT tokenizer
            max_length (int): Maximum sequence length
        """
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Convert dict of tensors to tensors and remove the extra dimension
        item = {key: val.squeeze(0) for key, val in encoding.items()}
        
        if self.labels is not None:
            item['labels'] = torch.tensor(self.labels[idx])
            
        return item

def load_financial_corpus():
    """
    Load the Kenyan financial corpus from multiple sources
    
    Returns:
        tuple: texts, labels (if applicable)
    """
    logger.info("Loading Kenyan financial corpus...")
    
    # Initialize empty lists for texts and labels
    texts = []
    labels = []
    
    # Load Kenyan financial terms dictionary
    try:
        with open('../data/kenyan_financial_corpus.json', 'r', encoding='utf-8') as f:
            financial_terms = json.load(f)
            texts.extend([term['definition'] for term in financial_terms])
            # No labels for this data
    except FileNotFoundError:
        logger.warning("Kenyan financial corpus file not found")
    
    # Load intent training data (if available)
    try:
        intent_data = pd.read_csv('../data/intent_training_data.csv')
        texts.extend(intent_data['text'].tolist())
        labels.extend(intent_data['intent_id'].tolist())
    except FileNotFoundError:
        logger.warning("Intent training data file not found")
    
    # Load news articles and financial headlines (if available)
    try:
        news_data = pd.read_csv('../data/financial_news.csv')
        texts.extend(news_data['headline'].tolist())
        # No labels for this data
    except FileNotFoundError:
        logger.warning("Financial news data file not found")
    
    # If we have a mix of labeled and unlabeled data, handle appropriately
    if labels and len(labels) < len(texts):
        # For simplicity, we'll just use the labeled portion for classification
        texts = texts[:len(labels)]
    elif not labels:
        # If no labels, we're doing MLM (Masked Language Modeling) only
        labels = None
    
    logger.info(f"Loaded {len(texts)} text samples for training")
    
    return texts, labels

def preprocess_data(texts, labels):
    """
    Preprocess the data and split into train/validation sets
    
    Args:
        texts (list): List of text samples
        labels (list, optional): List of labels
        
    Returns:
        tuple: train_texts, val_texts, train_labels, val_labels
    """
    logger.info("Preprocessing and splitting data...")
    
    # Split data into train and validation sets
    if labels is not None:
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.1, random_state=42
        )
        return train_texts, val_texts, train_labels, val_labels
    else:
        train_texts, val_texts = train_test_split(
            texts, test_size=0.1, random_state=42
        )
        return train_texts, val_texts, None, None

def compute_metrics(pred):
    """
    Compute metrics for evaluation
    
    Args:
        pred: Prediction output from trainer
        
    Returns:
        dict: Dictionary containing evaluation metrics
    """
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='weighted')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def fine_tune_bert_for_classification(train_texts, val_texts, train_labels, val_labels, model_dir):
    """
    Fine-tune BERT for sequence classification on financial data
    
    Args:
        train_texts (list): Training text samples
        val_texts (list): Validation text samples
        train_labels (list): Training labels
        val_labels (list): Validation labels
        model_dir (str): Directory to save the model
    
    Returns:
        model: Fine-tuned BERT model
    """
    logger.info("Fine-tuning BERT for financial text classification...")
    
    # Load tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    
    # Get the number of unique labels
    num_labels = len(set(train_labels))
    
    # Create model with the appropriate number of labels
    model = BertForSequenceClassification.from_pretrained(
        'bert-base-uncased',
        num_labels=num_labels,
        output_attentions=False,
        output_hidden_states=False,
    )
    
    # Create datasets
    train_dataset = FinancialTextDataset(train_texts, train_labels, tokenizer)
    val_dataset = FinancialTextDataset(val_texts, val_labels, tokenizer)
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=model_dir,
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='../logs/',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Train the model
    logger.info("Starting BERT fine-tuning...")
    trainer.train()
    
    # Evaluate the model
    eval_result = trainer.evaluate()
    logger.info(f"Evaluation results: {eval_result}")
    
    # Save the model and tokenizer
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    
    logger.info(f"Model and tokenizer saved to {model_dir}")
    
    return model

def fine_tune_bert_for_mlm(train_texts, val_texts, model_dir):
    """
    Fine-tune BERT for masked language modeling on financial data
    
    Args:
        train_texts (list): Training text samples
        val_texts (list): Validation text samples
        model_dir (str): Directory to save the model
    
    Returns:
        model: Fine-tuned BERT model
    """
    logger.info("Fine-tuning BERT for masked language modeling on financial texts...")
    
    # Load tokenizer and model
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertForMaskedLM.from_pretrained('bert-base-uncased')
    
    # Create datasets
    train_dataset = FinancialTextDataset(train_texts, None, tokenizer)
    val_dataset = FinancialTextDataset(val_texts, None, tokenizer) if val_texts else None
    
    # Set up training arguments
    training_args = TrainingArguments(
        output_dir=model_dir,
        num_train_epochs=5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='../logs/',
        logging_steps=10,
        evaluation_strategy="epoch" if val_dataset else "no",
        save_strategy="epoch",
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    
    # Train the model
    logger.info("Starting BERT MLM fine-tuning...")
    trainer.train()
    
    # Evaluate the model if we have validation data
    if val_dataset:
        eval_result = trainer.evaluate()
        logger.info(f"Evaluation results: {eval_result}")
    
    # Save the model and tokenizer
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    
    logger.info(f"Model and tokenizer saved to {model_dir}")
    
    return model

def fine_tune_swahili_bert(train_texts, val_texts, train_labels, val_labels, model_dir):
    """
    Fine-tune a multilingual BERT model for Swahili financial texts
    
    Args:
        train_texts (list): Training text samples
        val_texts (list): Validation text samples
        train_labels (list): Training labels (optional)
        val_labels (list): Validation labels (optional)
        model_dir (str): Directory to save the model
    
    Returns:
        model: Fine-tuned BERT model
    """
    logger.info("Fine-tuning multilingual BERT for Swahili financial texts...")
    
    # Use multilingual BERT for Swahili support
    tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
    
    if train_labels is not None:
        # Classification task
        num_labels = len(set(train_labels))
        model = BertForSequenceClassification.from_pretrained(
            'bert-base-multilingual-cased',
            num_labels=num_labels
        )
        
        # Create datasets
        train_dataset = FinancialTextDataset(train_texts, train_labels, tokenizer)
        val_dataset = FinancialTextDataset(val_texts, val_labels, tokenizer)
        
        # Set up training arguments
        training_args = TrainingArguments(
            output_dir=model_dir,
            num_train_epochs=3,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='../logs/',
            logging_steps=10,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            compute_metrics=compute_metrics,
        )
    else:
        # MLM task
        model = BertForMaskedLM.from_pretrained('bert-base-multilingual-cased')
        
        # Create datasets
        train_dataset = FinancialTextDataset(train_texts, None, tokenizer)
        val_dataset = FinancialTextDataset(val_texts, None, tokenizer) if val_texts else None
        
        # Set up training arguments
        training_args = TrainingArguments(
            output_dir=model_dir,
            num_train_epochs=5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='../logs/',
            logging_steps=10,
            evaluation_strategy="epoch" if val_dataset else "no",
            save_strategy="epoch",
        )
        
        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
        )
    
    # Train the model
    logger.info("Starting multilingual BERT fine-tuning...")
    trainer.train()
    
    # Evaluate the model
    if val_dataset:
        eval_result = trainer.evaluate()
        logger.info(f"Evaluation results: {eval_result}")
    
    # Save the model and tokenizer
    model.save_pretrained(model_dir)
    tokenizer.save_pretrained(model_dir)
    
    logger.info(f"Model and tokenizer saved to {model_dir}")
    
    return model

def load_stock_market_data():
    """
    Load and preprocess NSE stock market data for training
    
    Returns:
        list: Processed text samples about Kenyan stocks
    """
    logger.info("Loading NSE stock market data...")
    
    stock_texts = []
    
    # Try to load stock market data files
    try:
        # Find all NSE data files
        data_dir = "../data"
        stock_files = [f for f in os.listdir(data_dir) if f.startswith("NSE_data_all_stocks_")]
        
        for file in stock_files:
            year = file.split("_")[-1].split(".")[0]  # Extract year from filename
            df = pd.read_csv(os.path.join(data_dir, file))
            
            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Group by stock code and create text descriptions
            stocks = df['code'].unique()
            
            for stock in stocks[:50]:  # Limit to first 50 stocks to avoid too much data
                stock_df = df[df['code'] == stock].copy()
                
                if len(stock_df) > 0:
                    # Get stock name
                    stock_name = stock_df['name'].iloc[0]
                    
                    # Calculate average price and change
                    avg_price = stock_df['day_price'].astype(float).mean()
                    avg_change = stock_df['change%'].astype(float).replace([np.inf, -np.inf], np.nan).dropna().mean()
                    
                    # Create a text description
                    text = f"The stock {stock_name} ({stock}) traded on the Nairobi Securities Exchange in {year} "
                    text += f"with an average price of {avg_price:.2f} KES. "
                    text += f"It had an average daily change of {avg_change:.2f}%."
                    
                    stock_texts.append(text)
    
    except Exception as e:
        logger.error(f"Error processing stock market data: {e}")
    
    logger.info(f"Generated {len(stock_texts)} text samples from NSE stock data")
    
    return stock_texts

def load_swahili_corpus():
    """
    Load Swahili financial corpus for multilingual training
    
    Returns:
        list: Swahili text samples related to finance
    """
    logger.info("Loading Swahili financial corpus...")
    
    swahili_texts = []
    
    try:
        # Try to load Swahili corpus
        with open('../data/swahili_corpus.json', 'r', encoding='utf-8') as f:
            swahili_data = json.load(f)
            swahili_texts = [item['text'] for item in swahili_data]
    except FileNotFoundError:
        # If file not found, create some basic Swahili financial texts
        swahili_texts = [
            "Akaunti ya benki inayotumika kwa shughuli za kila siku.",
            "Hisa ni sehemu ya umiliki katika kampuni.",
            "Riba ni malipo yanayofanywa kwa matumizi ya fedha za mkopo.",
            "Bajeti ni mpango wa matumizi ya fedha kwa kipindi maalum.",
            "Akiba ni fedha zinazohifadhiwa kwa matumizi ya baadaye.",
            "Hazina ya uwekezaji ni mkusanyiko wa fedha kutoka kwa wawekezaji wengi.",
            "Bima ni mkataba wa kulinda dhidi ya hasara ya kifedha.",
            "Mikopo ni fedha zinazokopeshwa kwa ahadi ya kulipa baadaye na riba.",
            "Soko la hisa ni mahali ambapo hisa zinauziwa na kununuliwa.",
            "Faida ni fedha zinazobaki baada ya kutoa gharama zote."
        ]
        logger.warning("Swahili corpus file not found, using default texts")
    
    logger.info(f"Loaded {len(swahili_texts)} Swahili text samples")
    
    return swahili_texts

def load_financial_survey_data():
    """
    Load financial advisory survey data for training
    
    Returns:
        tuple: texts, labels (if applicable)
    """
    logger.info("Loading financial survey data...")
    
    texts = []
    
    try:
        # Load from CSV
        survey_df = pd.read_csv('../data/financial_advisory_chabot_survey.csv')
        
        # Extract relevant columns for generating training data
        for _, row in survey_df.iterrows():
            # Generate financial goal texts
            if pd.notna(row['Primary Financial Goals']):
                text = f"My financial goal is {row['Primary Financial Goals'].lower()}."
                texts.append(text)
            
            # Generate financial challenge texts
            if pd.notna(row['Financial Challenges']):
                text = f"I'm facing challenges with {row['Financial Challenges'].lower()}."
                texts.append(text)
                
            # Generate chatbot feature requests
            if pd.notna(row['Preferred Chatbot Features']):
                text = f"I want a chatbot that can {row['Preferred Chatbot Features'].lower()}."
                texts.append(text)
                
            # Generate trust factor texts
            if pd.notna(row['Trust Factors for Chatbots']):
                text = f"For me to trust a financial chatbot, it needs to {row['Trust Factors for Chatbots'].lower()}."
                texts.append(text)
                
            # Generate financial concerns
            if pd.notna(row['Concerns About Using Financial Chatbot']):
                text = f"I'm concerned about {row['Concerns About Using Financial Chatbot'].lower()} when using a financial chatbot."
                texts.append(text)
        
        logger.info(f"Generated {len(texts)} training texts from survey data")
        
    except Exception as e:
        logger.error(f"Error loading survey data: {e}")
    
    return texts, None  # No labels for this data

def main():
    """Main function to run the fine-tuning process"""
    parser = argparse.ArgumentParser(description="Fine-tune BERT for financial text understanding")
    
    parser.add_argument(
        "--task", 
        type=str, 
        default="mlm",
        choices=["mlm", "classification", "swahili"],
        help="Type of task to fine-tune for (mlm, classification, swahili)"
    )
    
    parser.add_argument(
        "--model_dir", 
        type=str, 
        default="../models/financial-bert",
        help="Directory to save the fine-tuned model"
    )
    
    parser.add_argument(
        "--data_source", 
        type=str, 
        default="corpus",
        choices=["corpus", "stocks", "survey", "all"],
        help="Source of training data (corpus, stocks, survey, all)"
    )
    
    args = parser.parse_args()
    
    # Create model directory if it doesn't exist
    os.makedirs(args.model_dir, exist_ok=True)
    
    # Load data based on source
    if args.data_source == "corpus":
        texts, labels = load_financial_corpus()
    elif args.data_source == "stocks":
        texts = load_stock_market_data()
        labels = None
    elif args.data_source == "survey":
        texts, labels = load_financial_survey_data()
    elif args.data_source == "all":
        # Combine all data sources
        corpus_texts, corpus_labels = load_financial_corpus()
        stock_texts = load_stock_market_data()
        survey_texts, _ = load_financial_survey_data()
        
        texts = corpus_texts + stock_texts + survey_texts
        labels = corpus_labels if corpus_labels else None
    else:
        logger.error("Invalid data source")
        return
    
    # For Swahili task, load Swahili corpus
    if args.task == "swahili":
        swahili_texts = load_swahili_corpus()
        texts = swahili_texts + texts  # Combine with English texts
    
    # If no texts were loaded, exit
    if not texts:
        logger.error("No text samples loaded for training")
        return
    
    # Preprocess and split the data
    if labels:
        train_texts, val_texts, train_labels, val_labels = preprocess_data(texts, labels)
    else:
        train_texts, val_texts, train_labels, val_labels = preprocess_data(texts, None)
    
    # Fine-tune based on the task
    if args.task == "classification" and labels:
        fine_tune_bert_for_classification(
            train_texts, val_texts, train_labels, val_labels, args.model_dir
        )
    elif args.task == "swahili":
        fine_tune_swahili_bert(
            train_texts, val_texts, train_labels, val_labels, args.model_dir
        )
    else:  # Default to MLM
        fine_tune_bert_for_mlm(train_texts, val_texts, args.model_dir)
    
    logger.info("Fine-tuning completed successfully!")

if __name__ == "__main__":
    main()
