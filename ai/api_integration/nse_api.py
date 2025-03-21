import os
import json
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('nse_api')

# Load environment variables for API credentials
NSE_API_KEY = os.environ.get('NSE_API_KEY')
NSE_API_HOST = "nairobi-stock-exchange-nse.p.rapidapi.com"
RAPID_API_KEY = os.environ.get('RAPID_API_KEY', "64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581")  # Default from docs

# Redis configuration for caching
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    'stock_price': 300,  # 5 minutes for stock prices
    'market_index': 600,  # 10 minutes for market indices
    'stock_details': 86400,  # 24 hours for stock details
    'sectors': 86400,  # 24 hours for sector information
}

# API rate limiting
RATE_LIMIT_REQUESTS = 10  # Maximum requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds

# Initialize Redis client for caching
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
    logger.info("Redis cache initialized successfully")
except Exception as e:
    REDIS_AVAILABLE = False
    logger.warning(f"Redis cache initialization failed: {e}. Continuing without caching.")

# Rate limiting counter
request_timestamps = []


def _check_rate_limit() -> bool:
    """
    Check if we're within API rate limits
    
    Returns:
        bool: True if request can proceed, False if rate limit is exceeded
    """
    global request_timestamps
    current_time = time.time()
    
    # Remove timestamps older than the rate limit window
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < RATE_LIMIT_WINDOW]
    
    # Check if we've exceeded the rate limit
    if len(request_timestamps) >= RATE_LIMIT_REQUESTS:
        logger.warning("Rate limit exceeded, request throttled")
        return False
    
    # Add current timestamp to the list
    request_timestamps.append(current_time)
    return True


def _get_cache_key(endpoint: str, params: Dict = None) -> str:
    """
    Generate a cache key based on the endpoint and parameters
    
    Args:
        endpoint (str): API endpoint
        params (Dict, optional): Query parameters
        
    Returns:
        str: Cache key
    """
    if params:
        param_str = json.dumps(params, sort_keys=True)
        return f"nse_api:{endpoint}:{param_str}"
    return f"nse_api:{endpoint}"


def _set_cache(key: str, data: Any, ttl: int) -> bool:
    """
    Set data in cache with TTL
    
    Args:
        key (str): Cache key
        data (Any): Data to cache
        ttl (int): Time to live in seconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not REDIS_AVAILABLE:
        return False
    
    try:
        serialized_data = json.dumps(data)
        redis_client.setex(key, ttl, serialized_data)
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {e}")
        return False


def _get_cache(key: str) -> Optional[Any]:
    """
    Get data from cache
    
    Args:
        key (str): Cache key
        
    Returns:
        Optional[Any]: Cached data or None if not found
    """
    if not REDIS_AVAILABLE:
        return None
    
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Error getting cache: {e}")
        return None


def _make_api_request(endpoint: str, params: Dict = None, cache_ttl: int = None) -> Optional[Dict]:
    """
    Make a request to the NSE API with caching and rate limiting
    
    Args:
        endpoint (str): API endpoint
        params (Dict, optional): Query parameters
        cache_ttl (int, optional): Cache TTL in seconds, if None uses default based on endpoint
        
    Returns:
        Optional[Dict]: API response data or None on error
    """
    # Generate cache key
    cache_key = _get_cache_key(endpoint, params)
    
    # Try to get from cache first
    cached_data = _get_cache(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return cached_data
    
    # Check rate limit before making request
    if not _check_rate_limit():
        # If rate limit exceeded, wait and retry
        time.sleep(5)
        return _make_api_request(endpoint, params, cache_ttl)
    
    # Construct API URL
    url = f"https://{NSE_API_HOST}/{endpoint}"
    
    # Set up headers
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": NSE_API_HOST
    }
    
    try:
        # Make API request
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse response
        data = response.json()
        
        # Determine cache TTL
        if cache_ttl is None:
            # Use default TTL based on endpoint type
            if "stocks" in endpoint:
                cache_ttl = CACHE_TTL['stock_price']
            elif "index" in endpoint:
                cache_ttl = CACHE_TTL['market_index']
            elif "sectors" in endpoint:
                cache_ttl = CACHE_TTL['sectors']
            else:
                cache_ttl = CACHE_TTL['stock_details']
        
        # Cache the result
        _set_cache(cache_key, data, cache_ttl)
        
        return data
    
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        if e.response.status_code == 429:
            logger.warning("Rate limit exceeded according to API response")
            time.sleep(10)  # Wait longer for rate limit errors
            return _make_api_request(endpoint, params, cache_ttl)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error: Failed to connect to the API")
    except requests.exceptions.Timeout:
        logger.error("Timeout: The request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
    except json.JSONDecodeError:
        logger.error("JSON decode error: Failed to parse response")
    
    return None


def get_stock_price(symbol: str) -> Optional[Dict]:
    """
    Get real-time price for a specific stock
    
    Args:
        symbol (str): Stock symbol (e.g., "Safaricom" or "SCOM")
        
    Returns:
        Optional[Dict]: Stock price data or None on error
    """
    endpoint = f"stocks/{symbol}"
    return _make_api_request(endpoint)


def get_multiple_stock_prices(symbols: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Get real-time prices for multiple stocks
    
    Args:
        symbols (List[str]): List of stock symbols
        
    Returns:
        Dict[str, Optional[Dict]]: Dictionary mapping symbols to their price data
    """
    results = {}
    for symbol in symbols:
        results[symbol] = get_stock_price(symbol)
    return results


def get_market_index(index_name: str = "NSE20") -> Optional[Dict]:
    """
    Get the current value of an NSE market index
    
    Args:
        index_name (str): Index name (default: "NSE20")
        
    Returns:
        Optional[Dict]: Index data or None on error
    """
    endpoint = f"index/{index_name}"
    return _make_api_request(endpoint)


def get_stock_details(symbol: str) -> Optional[Dict]:
    """
    Get detailed information about a stock
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        Optional[Dict]: Stock details or None on error
    """
    endpoint = f"stocks/{symbol}/details"
    return _make_api_request(endpoint, cache_ttl=CACHE_TTL['stock_details'])


def get_sector_stocks(sector: str) -> Optional[List[Dict]]:
    """
    Get all stocks in a specific sector
    
    Args:
        sector (str): Sector name
        
    Returns:
        Optional[List[Dict]]: List of stocks in the sector or None on error
    """
    endpoint = "sectors"
    sector_data = _make_api_request(endpoint)
    
    if not sector_data or 'sectors' not in sector_data:
        return None
    
    # Find the specified sector
    for sector_info in sector_data['sectors']:
        if sector_info['name'].lower() == sector.lower():
            return sector_info.get('stocks', [])
    
    return []


def get_all_sectors() -> Optional[List[Dict]]:
    """
    Get all available sectors and their stocks
    
    Returns:
        Optional[List[Dict]]: List of sectors or None on error
    """
    endpoint = "sectors"
    sector_data = _make_api_request(endpoint)
    
    if not sector_data:
        return None
    
    return sector_data.get('sectors', [])


def get_market_movers(mover_type: str = "gainers") -> Optional[List[Dict]]:
    """
    Get market movers (gainers or losers)
    
    Args:
        mover_type (str): Type of movers ("gainers" or "losers")
        
    Returns:
        Optional[List[Dict]]: List of market movers or None on error
    """
    if mover_type not in ["gainers", "losers"]:
        logger.error(f"Invalid mover type: {mover_type}. Must be 'gainers' or 'losers'")
        return None
    
    endpoint = f"market/{mover_type}"
    return _make_api_request(endpoint)


def get_historical_data(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Get historical price data for a stock
    
    Args:
        symbol (str): Stock symbol
        start_date (str, optional): Start date in ISO format (YYYY-MM-DD)
        end_date (str, optional): End date in ISO format (YYYY-MM-DD)
        
    Returns:
        Optional[List[Dict]]: Historical data or None on error
    """
    # If dates not provided, use last 30 days
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    endpoint = f"stocks/{symbol}/history"
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    
    return _make_api_request(endpoint, params)


def fetch_local_historical_data(symbol: str, year: str = None) -> Optional[pd.DataFrame]:
    """
    Fetch historical data from local CSV files
    
    Args:
        symbol (str): Stock symbol
        year (str, optional): Year to fetch data for
        
    Returns:
        Optional[pd.DataFrame]: Historical data or None if not found
    """
    # Define the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    try:
        # Handle specific year request
        if year:
            file_path = os.path.join(data_dir, f"NSE_data_all_stocks_{year}.csv")
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return None
            
            # Load the data
            df = pd.read_csv(file_path)
            
            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Filter for the requested symbol
            symbol_data = df[df['code'] == symbol]
            
            if symbol_data.empty:
                logger.warning(f"No data found for symbol {symbol} in year {year}")
                return None
            
            # Convert date to datetime
            symbol_data['date'] = pd.to_datetime(symbol_data['date'], errors='coerce')
            
            # Sort by date
            symbol_data = symbol_data.sort_values('date')
            
            return symbol_data
        
        # If no specific year, try to get all available data
        all_data = []
        
        # Look for all available years
        for file_name in os.listdir(data_dir):
            if file_name.startswith("NSE_data_all_stocks_") and file_name.endswith(".csv"):
                file_path = os.path.join(data_dir, file_name)
                
                # Extract year from filename
                year_match = file_name.replace("NSE_data_all_stocks_", "").replace(".csv", "")
                
                try:
                    # Load the data
                    df = pd.read_csv(file_path)
                    
                    # Standardize column names
                    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
                    
                    # Filter for the requested symbol
                    symbol_data = df[df['code'] == symbol]
                    
                    if not symbol_data.empty:
                        # Add year as a column for reference
                        symbol_data['year'] = year_match
                        all_data.append(symbol_data)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        if not all_data:
            logger.warning(f"No historical data found for symbol {symbol}")
            return None
        
        # Combine all yearly data
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # Convert date to datetime
        combined_data['date'] = pd.to_datetime(combined_data['date'], errors='coerce')
        
        # Sort by date
        combined_data = combined_data.sort_values('date')
        
        return combined_data
        
    except Exception as e:
        logger.error(f"Error fetching local historical data: {e}")
        return None


def get_stock_performance(symbol: str, period: str = "1y") -> Optional[Dict]:
    """
    Calculate performance metrics for a stock over a specific period
    
    Args:
        symbol (str): Stock symbol
        period (str): Time period ("1d", "1w", "1m", "3m", "6m", "1y", "5y", "all")
        
    Returns:
        Optional[Dict]: Performance metrics or None on error
    """
    # Map periods to days
    period_days = {
        "1d": 1,
        "1w": 7,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "5y": 1825,
        "all": None  # Use all available data
    }
    
    if period not in period_days:
        logger.error(f"Invalid period: {period}")
        return None
    
    # Try to get data from the API first
    days = period_days[period]
    if days:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        api_data = get_historical_data(symbol, start_date, end_date)
        if api_data:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(api_data)
            
            # Compute performance metrics
            performance = _calculate_performance_metrics(df)
            return performance
    
    # Fallback to local data if API request fails or if period is "all"
    year = datetime.now().year if period == "1y" else None
    local_data = fetch_local_historical_data(symbol, str(year) if year else None)
    
    if local_data is None or local_data.empty:
        logger.warning(f"No historical data found for symbol {symbol}")
        return None
    
    # Filter data based on period if not "all"
    if days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        local_data = local_data[(local_data['date'] >= start_date) & (local_data['date'] <= end_date)]
    
    # Calculate performance metrics
    performance = _calculate_performance_metrics(local_data)
    return performance


def _calculate_performance_metrics(df: pd.DataFrame) -> Dict:
    """
    Calculate performance metrics from stock data
    
    Args:
        df (pd.DataFrame): Stock data DataFrame
        
    Returns:
        Dict: Performance metrics
    """
    # Ensure price columns are numeric
    price_cols = ['day_price', 'previous', 'change', 'day_low', 'day_high', '12m_low', '12m_high']
    for col in price_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Calculate metrics
    metrics = {}
    
    # Starting and ending prices
    if 'day_price' in df.columns and not df.empty:
        metrics['start_price'] = df.iloc[0]['day_price']
        metrics['end_price'] = df.iloc[-1]['day_price']
        
        # Calculate price change and percentage change
        metrics['price_change'] = metrics['end_price'] - metrics['start_price']
        metrics['percentage_change'] = (metrics['price_change'] / metrics['start_price']) * 100
    
    # Price range
    if 'day_low' in df.columns and 'day_high' in df.columns:
        metrics['min_price'] = df['day_low'].min()
        metrics['max_price'] = df['day_high'].max()
        metrics['price_range'] = metrics['max_price'] - metrics['min_price']
    
    # Volume stats if available
    if 'volume' in df.columns:
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        metrics['total_volume'] = df['volume'].sum()
        metrics['avg_volume'] = df['volume'].mean()
        metrics['max_volume'] = df['volume'].max()
    
    # Volatility (standard deviation of daily returns)
    if 'day_price' in df.columns:
        df['daily_return'] = df['day_price'].pct_change()
        metrics['volatility'] = df['daily_return'].std() * 100  # Convert to percentage
    
    # Date range
    if 'date' in df.columns:
        metrics['start_date'] = df['date'].min().strftime('%Y-%m-%d')
        metrics['end_date'] = df['date'].max().strftime('%Y-%m-%d')
        metrics['days'] = (df['date'].max() - df['date'].min()).days
    
    return metrics


def get_top_stocks(by: str = "performance", sector: str = None, limit: int = 10) -> Optional[List[Dict]]:
    """
    Get top stocks ranked by various metrics
    
    Args:
        by (str): Ranking metric ("performance", "volume", "market_cap", "dividend_yield")
        sector (str, optional): Filter by sector
        limit (int, optional): Number of stocks to return
        
    Returns:
        Optional[List[Dict]]: List of top stocks or None on error
    """
    # Different endpoints based on ranking metric
    if by == "performance":
        data = get_market_movers("gainers")
    elif by == "volume":
        endpoint = "market/volume"
        data = _make_api_request(endpoint)
    elif by == "market_cap":
        endpoint = "market/cap"
        data = _make_api_request(endpoint)
    elif by == "dividend_yield":
        endpoint = "market/dividend"
        data = _make_api_request(endpoint)
    else:
        logger.error(f"Invalid ranking metric: {by}")
        return None
    
    if not data:
        return None
    
    # Filter by sector if specified
    if sector:
        sector_stocks = get_sector_stocks(sector)
        if not sector_stocks:
            return []
        
        sector_symbols = [stock['symbol'] for stock in sector_stocks]
        data = [stock for stock in data if stock.get('symbol') in sector_symbols]
    
    # Limit results
    return data[:limit]


def get_stock_suggestions(partial_query: str) -> Optional[List[Dict]]:
    """
    Get stock suggestions based on partial query for autocomplete
    
    Args:
        partial_query (str): Partial stock name or symbol
        
    Returns:
        Optional[List[Dict]]: List of matching stocks or None on error
    """
    if len(partial_query) < 2:
        return []
    
    # Check local data first
    results = []
    
    # Search in local sector data
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    sector_files = [f for f in os.listdir(data_dir) if f.startswith("NSE_data_stock_market_sectors")]
    
    if sector_files:
        # Use the most recent sector file
        sector_files.sort(reverse=True)
        sector_file = os.path.join(data_dir, sector_files[0])
        
        try:
            df = pd.read_csv(sector_file)
            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Find stock code column
            code_col = next((col for col in df.columns if 'code' in col.lower()), None)
            name_col = next((col for col in df.columns if 'name' in col.lower()), None)
            sector_col = next((col for col in df.columns if 'sector' in col.lower()), None)
            
            if code_col and name_col:
                # Filter stocks that match the query
                matches = df[
                    (df[code_col].str.contains(partial_query, case=False)) | 
                    (df[name_col].str.contains(partial_query, case=False))
                ]
                
                # Format results
                for _, row in matches.iterrows():
                    stock = {
                        'symbol': row[code_col],
                        'name': row[name_col],
                        'sector': row[sector_col] if sector_col else 'Unknown'
                    }
                    results.append(stock)
        except Exception as e:
            logger.error(f"Error searching local stock data: {e}")
    
    # If we found results locally, return them
    if results:
        return results[:10]  # Limit to 10 suggestions
    
    # Otherwise, try the API
    api_results = search_stocks(partial_query)
    if not api_results:
        return []
    
    # Format for autocomplete
    suggestions = [
        {
            'symbol': stock.get('symbol', ''),
            'name': stock.get('name', ''),
            'sector': stock.get('sector', '')
        }
        for stock in api_results
    ]
    
    return suggestions[:10]  # Limit to 10 suggestions


def search_stocks(query: str) -> Optional[List[Dict]]:
    """
    Search for stocks by name or symbol
    
    Args:
        query (str): Search query
        
    Returns:
        Optional[List[Dict]]: Search results or None on error
    """
    endpoint = "search"
    params = {"q": query}
    return _make_api_request(endpoint, params)


def get_market_summary() -> Optional[Dict]:
    """
    Get summary of current market status
    
    Returns:
        Optional[Dict]: Market summary or None on error
    """
    endpoint = "market/summary"
    return _make_api_request(endpoint)


def convert_to_dataframe(data: List[Dict]) -> pd.DataFrame:
    """
    Convert JSON stock data to pandas DataFrame
    
    Args:
        data (List[Dict]): Stock data
        
    Returns:
        pd.DataFrame: DataFrame containing stock data
    """
    if not data:
        return pd.DataFrame()
    
    return pd.DataFrame(data)


def init_nse_api():
    """Initialize the NSE API by pre-warming caches for common requests"""
    try:
        logger.info("Initializing NSE API and pre-warming caches...")
        
        # Get market summary
        get_market_summary()
        
        # Get main market index
        get_market_index()
        
        # Get market movers
        get_market_movers("gainers")
        get_market_movers("losers")
        
        # Get all sectors
        get_all_sectors()
        
        logger.info("NSE API initialization complete")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing NSE API: {e}")
        return False


if __name__ == "__main__":
    # Initialize the NSE API
    init_nse_api()
    
    # Example usage
    print("=== NSE Market Summary ===")
    summary = get_market_summary()
    if summary:
        print(f"Market Status: {summary.get('status')}")
        print(f"NSE20 Index: {summary.get('nse20Index')}")
        print(f"Market Cap: {summary.get('marketCap')} KES")
    
    print("\n=== Top Gainers ===")
    gainers = get_market_movers("gainers")
    if gainers:
        for stock in gainers[:5]:
            print(f"{stock['symbol']} - {stock['name']}: +{stock['change']}%")
    
    print("\n=== Sample Stock Price (Safaricom) ===")
    safcom = get_stock_price("SCOM")
    if safcom:
        print(f"Current Price: {safcom['price']} KES")
        print(f"Change: {safcom['change']}%")
        print(f"Volume: {safcom['volume']}")
