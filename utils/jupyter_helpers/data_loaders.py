import os
import json
import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Union, Optional, Tuple
import datetime
import logging
from pathlib import Path
import sqlite3
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("pesaguru_data_loader")

# Base paths for data storage
NOTEBOOK_DIR = Path(os.path.dirname(os.path.abspath(__file__)) + '/../..')
DATA_DIR = NOTEBOOK_DIR / 'data'
EXTERNAL_DATA_DIR = DATA_DIR / 'external'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
INTERIM_DATA_DIR = DATA_DIR / 'interim'

# Create directories if they don't exist
os.makedirs(EXTERNAL_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(INTERIM_DATA_DIR, exist_ok=True)

#############################################
# CSV and Local File Loaders
#############################################

def load_csv(
    file_path: str, 
    encoding: str = 'utf-8', 
    **kwargs
) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame with proper encoding handling.
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding (default: utf-8)
        **kwargs: Additional arguments to pass to pandas.read_csv
        
    Returns:
        DataFrame containing the CSV data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        Exception: For any other errors during loading
    """
    try:
        # Check if path is absolute, if not make it relative to DATA_DIR
        if not os.path.isabs(file_path):
            if os.path.exists(file_path):
                # Use as is if it exists
                pass
            elif os.path.exists(os.path.join(str(DATA_DIR), file_path)):
                file_path = os.path.join(str(DATA_DIR), file_path)
            elif os.path.exists(os.path.join(str(EXTERNAL_DATA_DIR), file_path)):
                file_path = os.path.join(str(EXTERNAL_DATA_DIR), file_path)
                
        logger.info(f"Loading CSV file from: {file_path}")
        df = pd.read_csv(file_path, encoding=encoding, **kwargs)
        logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        return df
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except UnicodeDecodeError:
        logger.warning(f"Unicode decode error with {encoding}, trying 'latin-1'")
        return pd.read_csv(file_path, encoding='latin-1', **kwargs)
    except Exception as e:
        logger.error(f"Error loading CSV file: {str(e)}")
        raise

def load_financial_survey(
    file_path: str = 'financial_advisory_chabot_survey.csv'
) -> pd.DataFrame:
    """
    Load and preprocess the financial advisory chatbot survey data.
    
    Args:
        file_path: Path to the survey CSV file
        
    Returns:
        Preprocessed DataFrame containing the survey data
    """
    df = load_csv(file_path)
    
    # Preprocessing steps specific to survey data
    
    # Convert income ranges to numeric values (for analysis)
    if 'Monthly Income Range (KES)' in df.columns:
        # Extract lower bound of income range
        df['Income_Lower_Bound'] = df['Monthly Income Range (KES)'].apply(
            lambda x: float(re.search(r'(\d+,?\d*)', str(x)).group(1).replace(',', '')) 
            if re.search(r'(\d+,?\d*)', str(x)) else np.nan
        )
    
    # Convert categorical financial literacy to ordinal
    if 'Financial Literacy Level' in df.columns and df['Financial Literacy Level'].dtype == 'object':
        literacy_map = {
            'Very Low': 1,
            'Low': 2,
            'Medium': 3,
            'High': 4,
            'Very High': 5
        }
        df['Financial_Literacy_Ordinal'] = df['Financial Literacy Level'].map(literacy_map)
    
    return df

def load_json(file_path: str) -> dict:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary containing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file isn't valid JSON
    """
    try:
        # Check if path is absolute, if not make it relative to DATA_DIR
        if not os.path.isabs(file_path):
            if os.path.exists(file_path):
                # Use as is if it exists
                pass
            elif os.path.exists(os.path.join(str(DATA_DIR), file_path)):
                file_path = os.path.join(str(DATA_DIR), file_path)
            elif os.path.exists(os.path.join(str(EXTERNAL_DATA_DIR), file_path)):
                file_path = os.path.join(str(EXTERNAL_DATA_DIR), file_path)
        
        logger.info(f"Loading JSON file from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        raise

def load_financial_corpus(
    corpus_type: str = 'kenyan'
) -> dict:
    """
    Load the financial terminology corpus based on type.
    
    Args:
        corpus_type: Type of corpus ('kenyan', 'general', 'swahili')
        
    Returns:
        Dictionary containing the financial terms and definitions
    """
    corpus_files = {
        'kenyan': 'kenyan_financial_corpus.json',
        'general': 'financial_terms_dictionary.json',
        'swahili': 'swahili_corpus.json'
    }
    
    file_path = os.path.join(str(EXTERNAL_DATA_DIR), corpus_files.get(
        corpus_type, corpus_files['general']))
    
    try:
        return load_json(file_path)
    except FileNotFoundError:
        logger.warning(f"Corpus file not found: {file_path}. Using empty corpus.")
        return {}

def save_processed_data(
    df: pd.DataFrame, 
    filename: str,
    folder: str = 'processed'
) -> str:
    """
    Save a processed DataFrame to the appropriate folder.
    
    Args:
        df: DataFrame to save
        filename: Name for the saved file
        folder: Subfolder within data directory ('processed', 'interim', 'external')
        
    Returns:
        Path to the saved file
    """
    folder_map = {
        'processed': PROCESSED_DATA_DIR,
        'interim': INTERIM_DATA_DIR,
        'external': EXTERNAL_DATA_DIR
    }
    
    target_dir = folder_map.get(folder, PROCESSED_DATA_DIR)
    
    # Ensure the filename has the right extension
    if not filename.endswith('.csv') and not filename.endswith('.parquet'):
        filename = f"{filename}.csv"
    
    output_path = os.path.join(str(target_dir), filename)
    
    if filename.endswith('.csv'):
        df.to_csv(output_path, index=False, encoding='utf-8')
    elif filename.endswith('.parquet'):
        df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved processed data to: {output_path}")
    return output_path

#############################################
# Database Loaders
#############################################

def load_from_database(
    query: str,
    params: Optional[tuple] = None,
    db_type: str = 'postgres'
) -> pd.DataFrame:
    """
    Load data from a database using a SQL query.
    
    Args:
        query: SQL query string
        params: Parameters for the query
        db_type: Type of database ('postgres', 'sqlite')
        
    Returns:
        DataFrame containing query results
    """
    try:
        if db_type == 'postgres':
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('DB_NAME', 'pesaguru'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', '')
                )
            except (ImportError, Exception) as e:
                logger.warning(f"Postgres connection failed: {str(e)}. Using SQLite fallback.")
                db_type = 'sqlite'
        
        if db_type == 'sqlite':
            conn = sqlite3.connect(os.getenv('SQLITE_PATH', str(DATA_DIR / 'pesaguru.db')))
            
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    except Exception as e:
        logger.error(f"Error executing database query: {str(e)}")
        # Return empty DataFrame with column names from query if possible
        try:
            import re
            column_names = re.findall(r'SELECT\s+([\w\s,._]+)\s+FROM', query, re.IGNORECASE)
            if column_names:
                columns = [c.strip() for c in column_names[0].split(',')]
                return pd.DataFrame(columns=columns)
            else:
                return pd.DataFrame()
        except:
            return pd.DataFrame()

#############################################
# External API Loaders
#############################################

def fetch_api_data(
    api_name: str,
    endpoint: str,
    params: Optional[Dict] = None,
    method: str = 'GET'
) -> Dict:
    """
    Fetch data from an external API.
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint to call
        params: Query parameters for the API call
        method: HTTP method ('GET', 'POST')
        
    Returns:
        JSON response from the API as a dictionary
    """
    # Default headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # API configuration based on environment variables
    api_config = {
        'nse': {
            'base_url': os.getenv('NSE_API_URL', 'https://nairobi-stock-exchange-nse.p.rapidapi.com'),
            'api_key': os.getenv('NSE_API_KEY', ''),
            'headers': {
                'x-rapidapi-host': 'nairobi-stock-exchange-nse.p.rapidapi.com',
                'x-rapidapi-key': os.getenv('NSE_API_KEY', '')
            }
        },
        'cbk': {
            'base_url': os.getenv('CBK_API_URL', 'https://cbk-bonds.p.rapidapi.com'),
            'headers': {
                'x-rapidapi-host': 'cbk-bonds.p.rapidapi.com',
                'x-rapidapi-key': os.getenv('CBK_API_KEY', '')
            }
        },
        'forex': {
            'base_url': os.getenv('FOREX_API_URL', 'https://exchange-rates7.p.rapidapi.com'),
            'headers': {
                'x-rapidapi-host': 'exchange-rates7.p.rapidapi.com',
                'x-rapidapi-key': os.getenv('FOREX_API_KEY', '')
            }
        }
    }
    
    if api_name not in api_config:
        logger.warning(f"Unknown API: {api_name}. Using default configuration.")
        base_url = f"https://{api_name.lower()}.example.com/api"
    else:
        base_url = api_config[api_name]['base_url']
        if 'headers' in api_config[api_name]:
            headers.update(api_config[api_name]['headers'])
    
    url = f"{base_url}/{endpoint.lstrip('/')}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()
    
    except requests.RequestException as e:
        logger.error(f"API request error ({api_name}): {str(e)}")
        return {'error': str(e), 'status': 'error'}
    except Exception as e:
        logger.error(f"Error in API request: {str(e)}")
        return {'error': str(e), 'status': 'error'}

def load_loan_data(
    source: str = 'database',
    loan_types: Optional[List[str]] = None,
    providers: Optional[List[str]] = None,
    include_historical: bool = False,
    db_type: str = 'postgres',
    cache: bool = True,
    cache_ttl: int = 3600  # 1 hour cache TTL
) -> pd.DataFrame:
    """
    Load loan product data for Kenyan financial institutions.
    
    Args:
        source: Data source ('database', 'api', 'csv')
        loan_types: Filter by loan types ('personal', 'business', 'mortgage', 'asset', 'mobile')
        providers: Filter by loan providers/banks
        include_historical: Include historical interest rate data
        db_type: Database type for database source
        cache: Whether to use cached data if available
        cache_ttl: Time-to-live for cache in seconds
        
    Returns:
        DataFrame containing loan product information
        
    Example:
        >>> # Load all mobile loans
        >>> mobile_loans = load_loan_data(loan_types=['mobile'])
        >>> 
        >>> # Load mortgage products from specific banks
        >>> mortgages = load_loan_data(
        ...     loan_types=['mortgage'], 
        ...     providers=['Equity Bank', 'KCB', 'Cooperative Bank']
        ... )
    """
    loan_types = loan_types or ['personal', 'business', 'mortgage', 'asset', 'mobile']
    providers = providers or []
    cache_file = INTERIM_DATA_DIR / 'loan_products_cache.parquet'
    
    # Check cache first if enabled
    if cache and os.path.exists(cache_file):
        cache_mod_time = os.path.getmtime(cache_file)
        if (datetime.datetime.now().timestamp() - cache_mod_time) < cache_ttl:
            df = pd.read_parquet(cache_file)
            # Apply filters
            if loan_types:
                df = df[df['loan_type'].isin(loan_types)]
            if providers:
                df = df[df['provider'].isin(providers)]
            return df
    
    if source == 'database':
        try:
            # Construct SQL query
            base_query = """
            SELECT 
                l.id, l.product_name, l.loan_type, l.provider, l.min_amount, 
                l.max_amount, l.interest_rate, l.interest_type, l.term_min, 
                l.term_max, l.processing_fee, l.early_repayment_fee,
                l.late_payment_penalty, l.collateral_required, l.eligibility_criteria,
                l.application_url, l.updated_at
            FROM loan_products l
            """
            
            where_clauses = []
            params = []
            
            if loan_types:
                placeholders = ', '.join(['%s'] * len(loan_types))
                where_clauses.append(f"l.loan_type IN ({placeholders})")
                params.extend(loan_types)
            
            if providers:
                placeholders = ', '.join(['%s'] * len(providers))
                where_clauses.append(f"l.provider IN ({placeholders})")
                params.extend(providers)
            
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            # Include historical data if requested
            if include_historical:
                historical_query = f"""
                SELECT 
                    l.id, l.product_name, l.loan_type, l.provider, l.min_amount, 
                    l.max_amount, h.interest_rate, l.interest_type, l.term_min, 
                    l.term_max, l.processing_fee, l.early_repayment_fee,
                    l.late_payment_penalty, l.collateral_required, l.eligibility_criteria,
                    l.application_url, h.effective_date as updated_at
                FROM loan_products l
                JOIN loan_interest_history h ON l.id = h.loan_product_id
                """
                
                if where_clauses:
                    historical_query += " WHERE " + " AND ".join(where_clauses)
                
                historical_query += " ORDER BY h.effective_date DESC"
                
                # Get both current and historical data
                df_current = load_from_database(base_query, tuple(params) if params else None, db_type)
                df_historical = load_from_database(historical_query, tuple(params) if params else None, db_type)
                
                # Add a column to indicate current vs historical
                df_current['is_current'] = True
                df_historical['is_current'] = False
                
                # Combine the dataframes
                df = pd.concat([df_current, df_historical], ignore_index=True)
            else:
                df = load_from_database(base_query, tuple(params) if params else None, db_type)
            
            # Cache the results if enabled
            if cache:
                df.to_parquet(cache_file, index=False)
            
            return df
        
        except Exception as e:
            logger.error(f"Error loading loan data from database: {str(e)}")
            
            # If cache exists, use it as fallback
            if os.path.exists(cache_file):
                logger.warning("Using cache as fallback")
                df = pd.read_parquet(cache_file)
                # Apply filters
                if loan_types:
                    df = df[df['loan_type'].isin(loan_types)]
                if providers:
                    df = df[df['provider'].isin(providers)]
                return df
            
            # If no cache and database fails, fallback to CSV
            logger.warning("Falling back to CSV data source")
            source = 'csv'
    
    if source == 'api':
        try:
            # Attempt to fetch from API
            response_data = []
            
            # Fetch from CBK API or other APIs with loan information
            for loan_type in loan_types:
                try:
                    # Different endpoints for different loan types
                    endpoint = f"loan-products/{loan_type}" if loan_type != 'mobile' else "mobile-loans"
                    data = fetch_api_data('cbk', endpoint)
                    
                    if isinstance(data, list):
                        for item in data:
                            if not providers or item.get('provider') in providers:
                                response_data.append(item)
                    elif isinstance(data, dict) and 'products' in data:
                        for item in data['products']:
                            if not providers or item.get('provider') in providers:
                                response_data.append(item)
                except Exception as api_error:
                    logger.warning(f"Error fetching {loan_type} loans from API: {str(api_error)}")
            
            if response_data:
                df = pd.DataFrame(response_data)
                
                # Standardize column names
                column_mapping = {
                    'name': 'product_name',
                    'lender': 'provider',
                    'type': 'loan_type',
                    'min': 'min_amount',
                    'max': 'max_amount',
                    'rate': 'interest_rate',
                    'rate_type': 'interest_type',
                    'min_term': 'term_min',
                    'max_term': 'term_max',
                    'fees': 'processing_fee',
                    'early_payment_fee': 'early_repayment_fee',
                    'late_fee': 'late_payment_penalty',
                    'collateral': 'collateral_required',
                    'eligibility': 'eligibility_criteria',
                    'url': 'application_url',
                    'last_updated': 'updated_at'
                }
                
                df = df.rename(columns={old: new for old, new in column_mapping.items() if old in df.columns})
                
                # Add missing columns
                required_columns = [
                    'product_name', 'loan_type', 'provider', 'min_amount', 'max_amount', 
                    'interest_rate', 'interest_type', 'term_min', 'term_max', 'processing_fee', 
                    'early_repayment_fee', 'late_payment_penalty', 'collateral_required', 
                    'eligibility_criteria', 'application_url', 'updated_at'
                ]
                
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = None
                
                # Add timestamp
                df['timestamp'] = datetime.datetime.now().isoformat()
                
                # Cache the data if cache is enabled
                if cache:
                    df.to_parquet(cache_file, index=False)
                
                return df
            
            # If API returns empty, fall back to CSV
            logger.warning("API returned no data, falling back to CSV")
            source = 'csv'
        
        except Exception as e:
            logger.error(f"Error loading loan data from API: {str(e)}")
            
            # If cache exists, use it as fallback
            if os.path.exists(cache_file):
                logger.warning("Using cache as fallback")
                df = pd.read_parquet(cache_file)
                # Apply filters
                if loan_types:
                    df = df[df['loan_type'].isin(loan_types)]
                if providers:
                    df = df[df['provider'].isin(providers)]
                return df
            
            # If no cache and API fails, fallback to CSV
            logger.warning("Falling back to CSV data source")
            source = 'csv'
    
    if source == 'csv':
        # Fallback to local CSV data if database and API fail
        try:
            # Try to load from default locations
            csv_paths = [
                'external/kenyan_loan_products.csv',
                'loan_products.csv',
                '../data/external/kenyan_loan_products.csv',
                '../../data/external/kenyan_loan_products.csv'
            ]
            
            df = None
            for path in csv_paths:
                try:
                    df = load_csv(path)
                    break
                except FileNotFoundError:
                    continue
            
            if df is None:
                # If no predefined file found, create a basic dataset with typical Kenyan loans
                # This is a fallback to ensure the function always returns something useful
                logger.warning("No loan data CSV found, creating synthetic dataset")
                
                # Create synthetic dataset with typical Kenyan loan products
                data = [
                    # Mobile loans
                    {
                        'product_name': 'M-Shwari', 'loan_type': 'mobile', 'provider': 'Safaricom',
                        'min_amount': 100, 'max_amount': 100000, 'interest_rate': 7.5,
                        'interest_type': 'flat_monthly', 'term_min': 1, 'term_max': 1,
                        'processing_fee': 7.5, 'early_repayment_fee': 0, 'late_payment_penalty': 3.0,
                        'collateral_required': False, 'eligibility_criteria': 'M-PESA user for at least 6 months',
                        'application_url': 'https://www.safaricom.co.ke/personal/m-pesa/credit-and-savings/m-shwari'
                    },
                    {
                        'product_name': 'KCB M-PESA', 'loan_type': 'mobile', 'provider': 'KCB',
                        'min_amount': 100, 'max_amount': 150000, 'interest_rate': 8.64,
                        'interest_type': 'flat_monthly', 'term_min': 1, 'term_max': 6,
                        'processing_fee': 2.5, 'early_repayment_fee': 0, 'late_payment_penalty': 5.0,
                        'collateral_required': False, 'eligibility_criteria': 'M-PESA user for at least 6 months',
                        'application_url': 'https://www.safaricom.co.ke/personal/m-pesa/credit-and-savings/kcb-m-pesa'
                    },
                    {
                        'product_name': 'Fuliza M-PESA', 'loan_type': 'mobile', 'provider': 'Safaricom',
                        'min_amount': 1, 'max_amount': 70000, 'interest_rate': 1.083,
                        'interest_type': 'daily', 'term_min': 1, 'term_max': 30,
                        'processing_fee': 1.0, 'early_repayment_fee': 0, 'late_payment_penalty': 0,
                        'collateral_required': False, 'eligibility_criteria': 'Active M-PESA user',
                        'application_url': 'https://www.safaricom.co.ke/personal/m-pesa/credit-and-savings/fuliza-m-pesa'
                    },
                    # Personal loans
                    {
                        'product_name': 'Salary Advance', 'loan_type': 'personal', 'provider': 'Equity Bank',
                        'min_amount': 10000, 'max_amount': 3000000, 'interest_rate': 14.0,
                        'interest_type': 'reducing_balance', 'term_min': 1, 'term_max': 60,
                        'processing_fee': 2.5, 'early_repayment_fee': 5.0, 'late_payment_penalty': 3.0,
                        'collateral_required': False, 'eligibility_criteria': 'Salary account holder',
                        'application_url': 'https://equitygroupholdings.com/ke/borrow'
                    },
                    {
                        'product_name': 'Personal Unsecured Loan', 'loan_type': 'personal', 'provider': 'KCB',
                        'min_amount': 50000, 'max_amount': 3000000, 'interest_rate': 13.0,
                        'interest_type': 'reducing_balance', 'term_min': 3, 'term_max': 60,
                        'processing_fee': 3.0, 'early_repayment_fee': 3.0, 'late_payment_penalty': 3.0,
                        'collateral_required': False, 'eligibility_criteria': 'Proof of regular income',
                        'application_url': 'https://ke.kcbgroup.com/personal/get-a-loan/personal-loan'
                    },
                    # Mortgages
                    {
                        'product_name': 'Home Loan', 'loan_type': 'mortgage', 'provider': 'KCB',
                        'min_amount': 1000000, 'max_amount': 100000000, 'interest_rate': 11.5,
                        'interest_type': 'reducing_balance', 'term_min': 60, 'term_max': 240,
                        'processing_fee': 1.5, 'early_repayment_fee': 5.0, 'late_payment_penalty': 3.0,
                        'collateral_required': True, 'eligibility_criteria': 'Property collateral required',
                        'application_url': 'https://ke.kcbgroup.com/personal/get-a-loan/mortgages'
                    },
                    {
                        'product_name': 'Mortgage Loan', 'loan_type': 'mortgage', 'provider': 'Cooperative Bank',
                        'min_amount': 1000000, 'max_amount': 50000000, 'interest_rate': 12.5,
                        'interest_type': 'reducing_balance', 'term_min': 60, 'term_max': 300,
                        'processing_fee': 2.0, 'early_repayment_fee': 4.0, 'late_payment_penalty': 3.5,
                        'collateral_required': True, 'eligibility_criteria': 'Property collateral required',
                        'application_url': 'https://www.co-opbank.co.ke/personal-banking/borrowing/mortgages/'
                    },
                    # Business loans
                    {
                        'product_name': 'Business Loan', 'loan_type': 'business', 'provider': 'Equity Bank',
                        'min_amount': 100000, 'max_amount': 10000000, 'interest_rate': 13.0,
                        'interest_type': 'reducing_balance', 'term_min': 3, 'term_max': 60,
                        'processing_fee': 3.0, 'early_repayment_fee': 3.0, 'late_payment_penalty': 3.5,
                        'collateral_required': True, 'eligibility_criteria': 'Business registration required',
                        'application_url': 'https://equitygroupholdings.com/ke/borrow'
                    },
                    {
                        'product_name': 'SME Loan', 'loan_type': 'business', 'provider': 'ABSA',
                        'min_amount': 250000, 'max_amount': 15000000, 'interest_rate': 14.0,
                        'interest_type': 'reducing_balance', 'term_min': 6, 'term_max': 60,
                        'processing_fee': 2.5, 'early_repayment_fee': 4.0, 'late_payment_penalty': 3.0,
                        'collateral_required': True, 'eligibility_criteria': 'Business operational for 2+ years',
                        'application_url': 'https://www.absa.co.ke/business/borrow/'
                    },
                    # Asset financing
                    {
                        'product_name': 'Car Loan', 'loan_type': 'asset', 'provider': 'NCBA',
                        'min_amount': 500000, 'max_amount': 10000000, 'interest_rate': 12.5,
                        'interest_type': 'reducing_balance', 'term_min': 12, 'term_max': 60,
                        'processing_fee': 2.5, 'early_repayment_fee': 5.0, 'late_payment_penalty': 3.0,
                        'collateral_required': True, 'eligibility_criteria': 'Vehicle as collateral',
                        'application_url': 'https://ke.ncbagroup.com/personal-banking/loans/asset-financing/'
                    },
                    {
                        'product_name': 'Asset Finance', 'loan_type': 'asset', 'provider': 'Stanbic Bank',
                        'min_amount': 500000, 'max_amount': 20000000, 'interest_rate': 13.0,
                        'interest_type': 'reducing_balance', 'term_min': 12, 'term_max': 72,
                        'processing_fee': 2.0, 'early_repayment_fee': 4.0, 'late_payment_penalty': 3.5,
                        'collateral_required': True, 'eligibility_criteria': 'Asset as collateral',
                        'application_url': 'https://www.stanbicbank.co.ke/kenya/personal/borrow/asset-finance'
                    }
                ]
                
                df = pd.DataFrame(data)
                df['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Apply filters
            if loan_types:
                df = df[df['loan_type'].isin(loan_types)]
            
            if providers:
                df = df[df['provider'].isin(providers)]
            
            # Add timestamp
            df['timestamp'] = datetime.datetime.now().isoformat()
            
            # Cache the data
            if cache:
                df.to_parquet(cache_file, index=False)
            
            return df
        
        except Exception as e:
            logger.error(f"Error loading loan data from CSV: {str(e)}")
            
            # If all else fails, return empty DataFrame with correct structure
            logger.error("All data sources failed, returning empty DataFrame")
            columns = [
                'product_name', 'loan_type', 'provider', 'min_amount', 'max_amount', 
                'interest_rate', 'interest_type', 'term_min', 'term_max', 'processing_fee', 
                'early_repayment_fee', 'late_payment_penalty', 'collateral_required', 
                'eligibility_criteria', 'application_url', 'updated_at', 'timestamp'
            ]
            return pd.DataFrame(columns=columns)