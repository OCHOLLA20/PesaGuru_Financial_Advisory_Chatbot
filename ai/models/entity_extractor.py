import os
import re
import json
import spacy
from typing import Dict, List, Tuple, Any, Optional
import logging
from transformers import pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinancialEntityExtractor:
    """
    Financial entity extraction class for the PesaGuru chatbot.
    """
    
    def __init__(self, use_transformers: bool = True, language: str = "en"):
        """
        Initialize the entity extractor with appropriate models.
        
        Args:
            use_transformers: Whether to use transformer-based models (more accurate but slower)
            language: Language code ('en' for English, 'sw' for Swahili)
        """
        self.language = language
        self.use_transformers = use_transformers
        
        # Load spaCy models
        try:
            if language == "en":
                self.nlp = spacy.load("en_core_web_trf" if use_transformers else "en_core_web_sm")
                logger.info("Loaded English spaCy model")
            elif language == "sw":
                # Load Swahili model if available, otherwise fall back to English
                try:
                    self.nlp = spacy.load("sw_core_web_sm")
                    logger.info("Loaded Swahili spaCy model")
                except OSError:
                    logger.warning("Swahili model not found, falling back to English")
                    self.nlp = spacy.load("en_core_web_sm")
            else:
                logger.warning(f"Unsupported language: {language}, falling back to English")
                self.nlp = spacy.load("en_core_web_sm")
        except OSError as e:
            logger.error(f"Error loading spaCy model: {e}")
            logger.info("Attempting to download spaCy model...")
            if language == "en":
                model_name = "en_core_web_sm"
                os.system(f"python -m spacy download {model_name}")
                self.nlp = spacy.load(model_name)
            else:
                raise e
        
        # Load financial terms dictionary
        try:
            self.financial_terms = self._load_financial_dict()
            logger.info(f"Loaded {len(self.financial_terms)} financial terms")
        except Exception as e:
            logger.error(f"Error loading financial dictionary: {e}")
            self.financial_terms = {}
        
        # Kenya-specific financial entities
        self.kenyan_financial_entities = self._load_kenyan_entities()
        
        # Regular expressions for financial entities
        self.regex_patterns = {
            'currency_ksh': r'(KES|KSh|Ksh|ksh|kes)\s?(\d+[,\d]*(\.\d+)?)',
            'currency_with_amount': r'(\d+[,\d]*(\.\d+)?)\s?(KES|KSh|Ksh|ksh|kes|\$|USD|EUR|GBP)',
            'percentage': r'(\d+(\.\d+)?)\s?(%|percent|percentage)',
            'date': r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            'mpesa': r'(M-Pesa|M-PESA|m-pesa|mpesa)',
            'mobile_money': r'(M-Shwari|KCB M-Pesa|Fuliza|T-Kash|Airtel Money)',
            'stock_ticker': r'([A-Z]{3,4}:\s?NSE)',
            'amount': r'(\d+[,\d]*(\.\d+)?)\s?(thousand|million|billion|shillings|dollars|euros|pounds)'
        }
        
        # Initialize transformers pipeline for NER if available
        if use_transformers:
            try:
                self.ner_pipeline = pipeline(
                    "token-classification", 
                    model="flair/ner-english-ontonotes-large", 
                    aggregation_strategy="simple"
                )
                logger.info("Loaded transformers NER pipeline")
            except Exception as e:
                logger.error(f"Error loading transformers NER pipeline: {e}")
                self.ner_pipeline = None
        else:
            self.ner_pipeline = None
    
    def _load_financial_dict(self) -> Dict[str, Any]:
        """Load financial terms dictionary from JSON file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
            dict_path = os.path.join(data_dir, 'financial_terms_dictionary.json')
            
            with open(dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Financial terms dictionary not found, using empty dictionary")
            return {}
    
    def _load_kenyan_entities(self) -> Dict[str, List[str]]:
        """Load Kenya-specific financial entities."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), 'data')
            kenya_path = os.path.join(data_dir, 'kenyan_financial_corpus.json')
            
            with open(kenya_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Kenyan financial corpus not found, using default entities")
            # Default Kenya-specific entities
            return {
                "banks": ["Equity Bank", "KCB", "NCBA", "Co-operative Bank", "Absa", "Standard Chartered", 
                         "Family Bank", "DTB", "Stanbic Bank", "I&M Bank"],
                "mobile_money": ["M-Pesa", "M-Shwari", "KCB M-Pesa", "Fuliza", "T-Kash", "Airtel Money"],
                "saccos": ["Stima Sacco", "Mwalimu Sacco", "Kenya Police Sacco", "Harambee Sacco", 
                          "Unaitas", "Imarika Sacco"],
                "investment_firms": ["CIC Asset Management", "Britam Asset Managers", "Sanlam Investments", 
                                    "Old Mutual", "Cytonn Investments"],
                "nse_stocks": ["Safaricom", "EABL", "KCB Group", "Equity Group", "BAT Kenya", "Bamburi Cement"]
            }
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract financial entities from user text.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary of extracted entities by category
        """
        if not text or text.strip() == "":
            return {"entities": []}
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract entities from spaCy
        spacy_entities = self._extract_spacy_entities(doc)
        
        # Extract regex patterns
        regex_entities = self._extract_regex_entities(text)
        
        # Extract Kenya-specific entities
        kenyan_entities = self._extract_kenyan_entities(text)
        
        # Extract entities using transformers if available
        transformer_entities = []
        if self.use_transformers and self.ner_pipeline:
            transformer_entities = self._extract_transformer_entities(text)
        
        # Combine all entities and remove duplicates
        all_entities = spacy_entities + regex_entities + kenyan_entities + transformer_entities
        
        # Merge overlapping entities and resolve conflicts
        merged_entities = self._merge_entities(all_entities, text)
        
        # Group entities by type
        entity_dict = {}
        for entity in merged_entities:
            entity_type = entity["entity_type"]
            if entity_type not in entity_dict:
                entity_dict[entity_type] = []
            entity_dict[entity_type].append({
                "text": entity["text"],
                "start": entity["start"],
                "end": entity["end"],
                "confidence": entity.get("confidence", 1.0)
            })
        
        return {"entities": merged_entities, "grouped_entities": entity_dict}
    
    def _extract_spacy_entities(self, doc) -> List[Dict[str, Any]]:
        """Extract entities using spaCy."""
        entities = []
        for ent in doc.ents:
            # Map spaCy entity types to our financial entity types
            entity_type = self._map_spacy_entity(ent.label_)
            if entity_type:
                entities.append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "entity_type": entity_type,
                    "source": "spacy"
                })
        
        # Extract money and percentage entities
        for token in doc:
            if token.like_num:
                next_token = token.i + 1 < len(doc) and doc[token.i + 1]
                if next_token and next_token.text in ['%', 'percent', 'percentage']:
                    entities.append({
                        "text": token.text + next_token.text,
                        "start": token.idx,
                        "end": next_token.idx + len(next_token.text),
                        "entity_type": "PERCENTAGE",
                        "source": "spacy"
                    })
        
        return entities
    
    def _extract_regex_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using regular expressions."""
        entities = []
        
        for pattern_name, pattern in self.regex_patterns.items():
            for match in re.finditer(pattern, text):
                entity_type = self._map_regex_entity(pattern_name)
                entities.append({
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "entity_type": entity_type,
                    "source": "regex"
                })
        
        return entities
    
    def _extract_kenyan_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract Kenya-specific financial entities."""
        entities = []
        
        for category, entity_list in self.kenyan_financial_entities.items():
            for entity in entity_list:
                # Check for case-insensitive entity mentions
                for match in re.finditer(r'\b' + re.escape(entity) + r'\b', text, re.IGNORECASE):
                    entities.append({
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "entity_type": category.upper(),
                        "source": "kenyan_corpus"
                    })
        
        return entities
    
    def _extract_transformer_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using Hugging Face transformers."""
        entities = []
        
        try:
            results = self.ner_pipeline(text)
            for result in results:
                # Map transformer entity types to our financial entity types
                entity_type = self._map_transformer_entity(result["entity_group"])
                if entity_type:
                    entities.append({
                        "text": result["word"],
                        "start": result["start"],
                        "end": result["end"],
                        "entity_type": entity_type,
                        "confidence": result["score"],
                        "source": "transformer"
                    })
        except Exception as e:
            logger.error(f"Error in transformer entity extraction: {e}")
        
        return entities
    
    def _map_spacy_entity(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our financial entity types."""
        # Mapping from spaCy entity types to our financial entity types
        mapping = {
            "MONEY": "CURRENCY",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "DATE": "DATE",
            "PERCENT": "PERCENTAGE",
            "CARDINAL": "NUMBER",
            "PRODUCT": "PRODUCT",
            "PERSON": "PERSON"
        }
        return mapping.get(spacy_label)
    
    def _map_regex_entity(self, pattern_name: str) -> str:
        """Map regex pattern names to our financial entity types."""
        # Mapping from regex pattern names to our financial entity types
        mapping = {
            "currency_ksh": "CURRENCY_KSH",
            "currency_with_amount": "CURRENCY",
            "percentage": "PERCENTAGE",
            "date": "DATE",
            "mpesa": "MOBILE_MONEY",
            "mobile_money": "MOBILE_MONEY",
            "stock_ticker": "STOCK",
            "amount": "AMOUNT"
        }
        return mapping.get(pattern_name, "MISC")
    
    def _map_transformer_entity(self, transformer_label: str) -> Optional[str]:
        """Map transformer entity labels to our financial entity types."""
        # Mapping from transformer entity types to our financial entity types
        mapping = {
            "MONEY": "CURRENCY",
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "DATE": "DATE",
            "PERCENT": "PERCENTAGE",
            "CARDINAL": "NUMBER",
            "PRODUCT": "PRODUCT",
            "PERSON": "PERSON"
        }
        return mapping.get(transformer_label)
    
    def _merge_entities(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """
        Merge overlapping entities and resolve conflicts.
        
        When entities overlap, prefer:
        1. Higher confidence entities
        2. More specific entity types (e.g., CURRENCY_KSH over CURRENCY)
        3. Longer entity spans
        """
        if not entities:
            return []
        
        # Sort entities by start position, then by length (longest first)
        sorted_entities = sorted(entities, key=lambda x: (x["start"], -len(x["text"])))
        
        merged = []
        current = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            # Check if entities overlap
            if entity["start"] < current["end"]:
                # Resolve conflict based on specificity and confidence
                current_specificity = self._get_entity_specificity(current["entity_type"])
                entity_specificity = self._get_entity_specificity(entity["entity_type"])
                
                current_confidence = current.get("confidence", 0.9)
                entity_confidence = entity.get("confidence", 0.9)
                
                # If new entity is more specific or has higher confidence, replace current
                if (entity_specificity > current_specificity or 
                    (entity_specificity == current_specificity and entity_confidence > current_confidence)):
                    current = entity
            else:
                merged.append(current)
                current = entity
        
        merged.append(current)
        
        # Post-process: identify common Kenya-specific financial terms
        processed = []
        for entity in merged:
            # Add entity category information for Kenya-specific entities
            for category, items in self.kenyan_financial_entities.items():
                if entity["text"].lower() in [item.lower() for item in items]:
                    entity["entity_type"] = category.upper()
                    break
            
            # Check if entity is a financial term in our dictionary
            if entity["text"].lower() in self.financial_terms:
                entity["entity_type"] = "FINANCIAL_TERM"
                entity["metadata"] = self.financial_terms[entity["text"].lower()]
            
            processed.append(entity)
        
        return processed
    
    def _get_entity_specificity(self, entity_type: str) -> int:
        """
        Get specificity score for entity type.
        Higher score means more specific entity type.
        """
        specificity_map = {
            "CURRENCY_KSH": 10,
            "CURRENCY": 9,
            "MOBILE_MONEY": 9,
            "STOCK": 9,
            "BANKS": 8,
            "SACCOS": 8,
            "INVESTMENT_FIRMS": 8,
            "NSE_STOCKS": 8,
            "PERCENTAGE": 7,
            "AMOUNT": 7,
            "DATE": 6,
            "ORGANIZATION": 5,
            "PRODUCT": 5,
            "FINANCIAL_TERM": 8,
            "PERSON": 4,
            "LOCATION": 4,
            "NUMBER": 3,
            "MISC": 1
        }
        return specificity_map.get(entity_type, 0)
    
    def get_entity_explanations(self, entities: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Get explanations for extracted financial entities.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Dictionary mapping entity text to explanations
        """
        explanations = {}
        
        for entity in entities:
            entity_text = entity["text"]
            entity_type = entity["entity_type"]
            
            # Check if entity is in financial terms dictionary
            if entity_text.lower() in self.financial_terms:
                explanations[entity_text] = self.financial_terms[entity_text.lower()].get("definition", "")
            # Check if entity is a Kenya-specific financial entity
            elif entity_type.lower() in self.kenyan_financial_entities:
                for item in self.kenyan_financial_entities[entity_type.lower()]:
                    if item.lower() == entity_text.lower():
                        # Currently no definitions in the Kenya corpus
                        # This would be expanded with actual definitions
                        explanations[entity_text] = f"A {entity_type.lower()} in Kenya"
        
        return explanations


# Example usage
if __name__ == "__main__":
    # Test the entity extractor
    extractor = FinancialEntityExtractor(use_transformers=True)
    
    # Example queries
    test_queries = [
        "I want to invest KSh 50,000 in Safaricom shares",
        "What's the current interest rate for M-Shwari?",
        "How do I open a KCB account?",
        "I need a loan of 100,000 KES from Equity Bank",
        "What's the exchange rate for USD to KES today?",
        "How can I save 20% of my income using M-Pesa?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        entities = extractor.extract_entities(query)
        print("Extracted entities:")
        for entity in entities["entities"]:
            print(f"  - {entity['text']} ({entity['entity_type']})")
