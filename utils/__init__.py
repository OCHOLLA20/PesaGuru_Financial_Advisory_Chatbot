# Import subpackages
try:
    import jupyter_helpers
except ImportError:
    # Provide information if jupyter_helpers is not available
    class JupyterHelpersPlaceholder:
        """Placeholder for jupyter_helpers package if it's not available."""
        def __getattr__(self, name):
            raise ImportError(
                "jupyter_helpers module is not available. "
                "Make sure the module is installed and accessible."
            )
    
    jupyter_helpers = JupyterHelpersPlaceholder()

# Common file utility functions
def get_project_root():
    """
    Get the absolute path to the project root directory.
    
    Returns:
        str: Path to the project root directory
    """
    import os
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_data_directory():
    """
    Get the absolute path to the data directory.
    
    Returns:
        str: Path to the data directory
    """
    import os
    return os.path.join(get_project_root(), 'data')

def get_config_directory():
    """
    Get the absolute path to the configuration directory.
    
    Returns:
        str: Path to the config directory
    """
    import os
    return os.path.join(get_project_root(), 'config')

def get_logs_directory():
    """
    Get the absolute path to the logs directory.
    
    Returns:
        str: Path to the logs directory
    """
    import os
    logs_dir = os.path.join(get_project_root(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

# Configuration utility functions
def load_config(config_name='default'):
    """
    Load configuration from the config directory.
    
    Args:
        config_name (str): Name of the configuration file (without extension)
        
    Returns:
        dict: Configuration settings
    """
    import os
    import json
    
    config_dir = get_config_directory()
    config_path = os.path.join(config_dir, f"{config_name}.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return empty config if file doesn't exist
        return {}
    except json.JSONDecodeError:
        # Return empty config if file is invalid
        return {}

def get_env_variable(var_name, default=None):
    """
    Get environment variable with fallback to default.
    
    Args:
        var_name (str): Name of the environment variable
        default: Default value if environment variable is not set
        
    Returns:
        Value of the environment variable or default
    """
    import os
    from dotenv import load_dotenv
    
    # Load .env file if it exists
    load_dotenv()
    
    return os.getenv(var_name, default)

# Logging utility
def get_logger(name):
    """
    Get a configured logger.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    import logging
    import os
    from datetime import datetime
    
    logger = logging.getLogger(name)
    
    # Check if logger already has handlers to avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set logging level from environment variable or default to INFO
    log_level = get_env_variable('LOG_LEVEL', 'INFO').upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create file handler
    log_file = os.path.join(
        get_logs_directory(),
        f"{name.replace('.', '_')}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Error handling utilities
def safe_execute(func, *args, default_return=None, log_errors=True, **kwargs):
    """
    Execute a function safely, catching exceptions.
    
    Args:
        func: Function to execute
        *args: Positional arguments to pass to the function
        default_return: Value to return if an exception occurs
        log_errors: Whether to log exceptions
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Return value of the function or default_return if an exception occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger = get_logger('utils.safe_execute')
            logger.error(f"Error executing {func.__name__}: {str(e)}")
        return default_return

# String utilities
def clean_identifier(text):
    """
    Clean text to be used as an identifier (file name, variable name, etc.).
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text suitable for use as an identifier
    """
    import re
    
    # Replace spaces and special characters with underscores
    cleaned = re.sub(r'[^\w\s]', '', text)
    cleaned = re.sub(r'\s+', '_', cleaned)
    
    # Make lowercase
    cleaned = cleaned.lower()
    
    return cleaned

# Initialize package
logger = get_logger('utils')
logger.debug(f"PesaGuru utils package v{__version__} initialized")