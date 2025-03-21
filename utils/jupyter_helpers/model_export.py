import os
import json
import pickle
import datetime
import logging
import hashlib
from typing import Dict, List, Tuple, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants
MODEL_REGISTRY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "ai", "models", "model_registry.json")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "ai", "models")

def save_trained_model(
    model: Any,
    model_name: str,
    model_type: str,
    version: Optional[str] = None,
    metadata: Optional[Dict] = None,
    export_dir: Optional[str] = None
) -> str:
    """
    Save a trained model to disk.
    
    Args:
        model: Trained model object
        model_name: Name of the model
        model_type: Type of model (e.g., 'classifier', 'recommender', 'sentiment', 'bert')
        version: Version string (if None, current timestamp will be used)
        metadata: Dictionary of additional metadata
        export_dir: Directory to save the model (if None, use default models directory)
        
    Returns:
        Path to the saved model
    """
    try:
        # Create version if not provided
        if version is None:
            version = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize model name
        safe_name = model_name.replace(" ", "_").lower()
        
        # Determine export directory
        if export_dir is None:
            export_dir = os.path.join(MODELS_DIR, model_type)
        
        # Create directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        # Determine file path
        file_path = os.path.join(export_dir, f"{safe_name}_{version}.pkl")
        
        # Save the model
        with open(file_path, 'wb') as f:
            pickle.dump(model, f)
        
        logger.info(f"Model saved to {file_path}")
        
        # Create metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            "saved_at": datetime.datetime.now().isoformat(),
            "model_type": model_type,
            "version": version,
            "file_path": file_path
        })
        
        # Add to model registry
        _update_model_registry(safe_name, model_type, version, file_path, metadata)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving model {model_name}: {e}")
        raise

def export_model_to_production(
    model_name: str,
    model_type: str,
    version: Optional[str] = None,
    production_path: Optional[str] = None
) -> bool:
    """
    Export a saved model to the production environment.
    
    Args:
        model_name: Name of the model
        model_type: Type of model
        version: Specific version to export (if None, use latest version)
        production_path: Path to production models directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Sanitize model name
        safe_name = model_name.replace(" ", "_").lower()
        
        # Get model info from registry
        model_info = _get_model_info(safe_name, model_type, version)
        
        if model_info is None:
            logger.error(f"Model {safe_name} of type {model_type} not found in registry")
            return False
        
        # Get source path
        source_path = model_info.get("file_path")
        if not source_path or not os.path.exists(source_path):
            logger.error(f"Model file not found at {source_path}")
            return False
        
        # Determine production path
        if production_path is None:
            production_path = os.path.join(MODELS_DIR, "production", model_type)
        
        # Create production directory if it doesn't exist
        os.makedirs(production_path, exist_ok=True)
        
        # Determine destination path
        dest_name = f"{safe_name}.pkl"
        dest_path = os.path.join(production_path, dest_name)
        
        # Copy the model file
        import shutil
        shutil.copy2(source_path, dest_path)
        
        # Update model registry with production info
        _update_model_registry(
            safe_name, 
            model_type, 
            model_info["version"], 
            source_path, 
            {"production_path": dest_path, "deployed_at": datetime.datetime.now().isoformat()}
        )
        
        logger.info(f"Model {safe_name} exported to production at {dest_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error exporting model {model_name} to production: {e}")
        return False

def export_bert_model(
    model,
    tokenizer,
    model_name: str,
    version: Optional[str] = None,
    metadata: Optional[Dict] = None,
    export_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    Export a fine-tuned BERT model and tokenizer.
    
    Args:
        model: Trained BERT model object
        tokenizer: BERT tokenizer object
        model_name: Name of the model
        version: Version string (if None, current timestamp will be used)
        metadata: Dictionary of additional metadata
        export_dir: Directory to save the model
        
    Returns:
        Dictionary with paths to saved model and tokenizer
    """
    try:
        # Check if transformers library is available
        try:
            from transformers import PreTrainedModel, PreTrainedTokenizer
        except ImportError:
            logger.error("Transformers library not found. Please install it with: pip install transformers")
            raise ImportError("Transformers library required")
        
        # Validate inputs
        if not hasattr(model, 'save_pretrained') or not hasattr(tokenizer, 'save_pretrained'):
            logger.error("Model or tokenizer does not have save_pretrained method")
            raise ValueError("Model and tokenizer must be from the transformers library")
        
        # Create version if not provided
        if version is None:
            version = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize model name
        safe_name = model_name.replace(" ", "_").lower()
        
        # Determine export directory
        if export_dir is None:
            export_dir = os.path.join(MODELS_DIR, "bert", f"{safe_name}_{version}")
        
        # Create directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        # Save model and tokenizer
        model_path = os.path.join(export_dir, "model")
        tokenizer_path = os.path.join(export_dir, "tokenizer")
        
        model.save_pretrained(model_path)
        tokenizer.save_pretrained(tokenizer_path)
        
        logger.info(f"BERT model saved to {model_path}")
        logger.info(f"Tokenizer saved to {tokenizer_path}")
        
        # Create metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            "saved_at": datetime.datetime.now().isoformat(),
            "model_type": "bert",
            "version": version,
            "model_path": model_path,
            "tokenizer_path": tokenizer_path
        })
        
        # Save metadata file
        metadata_path = os.path.join(export_dir, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Add to model registry
        _update_model_registry(safe_name, "bert", version, export_dir, metadata)
        
        return {
            "model_path": model_path,
            "tokenizer_path": tokenizer_path,
            "metadata_path": metadata_path
        }
        
    except Exception as e:
        logger.error(f"Error exporting BERT model {model_name}: {e}")
        raise

def export_embeddings(
    embeddings: Dict[str, List[float]],
    embedding_name: str,
    version: Optional[str] = None,
    metadata: Optional[Dict] = None,
    export_dir: Optional[str] = None
) -> str:
    """
    Export word or document embeddings.
    
    Args:
        embeddings: Dictionary mapping tokens/documents to embedding vectors
        embedding_name: Name for the embeddings
        version: Version string (if None, current timestamp will be used)
        metadata: Dictionary of additional metadata
        export_dir: Directory to save the embeddings
        
    Returns:
        Path to the saved embeddings
    """
    try:
        # Create version if not provided
        if version is None:
            version = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize embedding name
        safe_name = embedding_name.replace(" ", "_").lower()
        
        # Determine export directory
        if export_dir is None:
            export_dir = os.path.join(MODELS_DIR, "embeddings")
        
        # Create directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        
        # Determine file path
        file_path = os.path.join(export_dir, f"{safe_name}_{version}.json")
        
        # Save the embeddings
        with open(file_path, 'w') as f:
            json.dump(embeddings, f)
        
        logger.info(f"Embeddings saved to {file_path}")
        
        # Create metadata if not provided
        if metadata is None:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            "saved_at": datetime.datetime.now().isoformat(),
            "model_type": "embeddings",
            "version": version,
            "file_path": file_path,
            "embedding_shape": f"{len(next(iter(embeddings.values())))}",
            "vocab_size": len(embeddings)
        })
        
        # Add to model registry
        _update_model_registry(safe_name, "embeddings", version, file_path, metadata)
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error exporting embeddings {embedding_name}: {e}")
        raise

def create_model_registry_entry(
    model_name: str,
    model_type: str,
    version: str,
    file_path: str,
    additional_metadata: Optional[Dict] = None
) -> bool:
    """
    Manually create an entry in the model registry.
    
    Args:
        model_name: Name of the model
        model_type: Type of model
        version: Version string
        file_path: Path to the model file
        additional_metadata: Dictionary of additional metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Sanitize model name
        safe_name = model_name.replace(" ", "_").lower()
        
        # Create metadata
        metadata = additional_metadata or {}
        metadata.update({
            "registered_at": datetime.datetime.now().isoformat(),
            "model_type": model_type,
            "version": version,
            "file_path": file_path
        })
        
        # Update registry
        return _update_model_registry(safe_name, model_type, version, file_path, metadata)
        
    except Exception as e:
        logger.error(f"Error creating registry entry for {model_name}: {e}")
        return False

def _get_model_registry() -> Dict:
    """
    Get the model registry data.
    
    Returns:
        Dictionary containing model registry data
    """
    try:
        # Create registry file if it doesn't exist
        if not os.path.exists(MODEL_REGISTRY_PATH):
            os.makedirs(os.path.dirname(MODEL_REGISTRY_PATH), exist_ok=True)
            with open(MODEL_REGISTRY_PATH, 'w') as f:
                json.dump({}, f)
            return {}
        
        # Load registry data
        with open(MODEL_REGISTRY_PATH, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error loading model registry: {e}")
        return {}

def _update_model_registry(
    model_name: str,
    model_type: str,
    version: str,
    file_path: str,
    metadata: Dict
) -> bool:
    """
    Update the model registry with a new model entry.
    
    Args:
        model_name: Name of the model
        model_type: Type of model
        version: Version string
        file_path: Path to the model file
        metadata: Dictionary of metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current registry
        registry = _get_model_registry()
        
        # Create model entry if it doesn't exist
        if model_name not in registry:
            registry[model_name] = {
                "model_type": model_type,
                "versions": {}
            }
        
        # Add version entry
        registry[model_name]["versions"][version] = metadata
        
        # Update latest version
        registry[model_name]["latest_version"] = version
        
        # Save updated registry
        os.makedirs(os.path.dirname(MODEL_REGISTRY_PATH), exist_ok=True)
        with open(MODEL_REGISTRY_PATH, 'w') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"Model registry updated for {model_name} version {version}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating model registry: {e}")
        return False

def _get_model_info(
    model_name: str,
    model_type: Optional[str] = None,
    version: Optional[str] = None
) -> Optional[Dict]:
    """
    Get information about a specific model from the registry.
    
    Args:
        model_name: Name of the model
        model_type: Type of model (for validation)
        version: Specific version to get (if None, use latest version)
        
    Returns:
        Dictionary with model information or None if not found
    """
    try:
        # Get registry
        registry = _get_model_registry()
        
        # Check if model exists
        if model_name not in registry:
            logger.warning(f"Model {model_name} not found in registry")
            return None
        
        # Validate model type if provided
        if model_type is not None and registry[model_name]["model_type"] != model_type:
            logger.warning(f"Model {model_name} has type {registry[model_name]['model_type']}, not {model_type}")
            return None
        
        # Determine version to use
        if version is None:
            if "latest_version" in registry[model_name]:
                version = registry[model_name]["latest_version"]
            else:
                # If no latest version is specified, use the most recent by timestamp
                versions = registry[model_name]["versions"]
                if not versions:
                    logger.warning(f"No versions found for model {model_name}")
                    return None
                
                # Find the most recent version by saved_at timestamp
                latest_version = max(
                    versions.keys(),
                    key=lambda v: versions[v].get("saved_at", "")
                )
                version = latest_version
        
        # Check if version exists
        if version not in registry[model_name]["versions"]:
            logger.warning(f"Version {version} not found for model {model_name}")
            return None
        
        # Return model info
        return registry[model_name]["versions"][version]
        
    except Exception as e:
        logger.error(f"Error getting model info for {model_name}: {e}")
        return None

def calculate_model_hash(model_path: str) -> str:
    """
    Calculate MD5 hash of a model file.
    
    Args:
        model_path: Path to the model file
        
    Returns:
        MD5 hash of the model file
    """
    try:
        hash_md5 = hashlib.md5()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating model hash: {e}")
        return ""