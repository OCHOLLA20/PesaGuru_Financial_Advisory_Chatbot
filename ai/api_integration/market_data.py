import os
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Union, Optional, Any
import aiohttp
import asyncio
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/market_data.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("market_data")

# API Keys (loaded from environment variables for security)
NSE_API_KEY = os.getenv("NSE_API_KEY")
YAHOO_FINANCE_API_KEY = os.getenv("YAHOO_FINANCE_API_KEY", "64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581")
CBK_API_KEY = os.getenv("CBK_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "08HAWE6C99AGWNEZ")
COIN_GECKO_API_KEY = os.getenv("COIN_GECKO_API_KEY")
MPESA_API_KEY = os.getenv("MPESA_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Redis client for caching
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

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
    logger.info("Redis cache connection established successfully")
except Exception as e:
    logger.warning(f"Redis cache connection failed: {e}. Will operate without caching.")
    REDIS_AVAILABLE = False

# Cache TTL in seconds
CACHE_TTL = {
    "stock_price": 60 * 15,  # 15 minutes for stock prices
    "forex_rates": 60 * 60,  # 1 hour for forex rates
    "crypto_prices": 60 * 5,  # 5 minutes for crypto prices
    "market_news": 60 * 30,  # 30 minutes for news
    "cbk_rates": 60 * 60 * 12,  # 12 hours for CBK rates
    "stock_historical": 60 * 60 * 24,  # 24 hours for historical data
}


class APIError(Exception):
    """Custom exception for API errors"""
    pass


def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and parameters"""
    params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return f"{prefix}:{params}"


def cache_result(func):
    """Decorator to cache API results using Redis"""
    def wrapper(*args, **kwargs):
        if not REDIS_AVAILABLE:
            return func(*args, **kwargs)

        # Generate cache key based on function name and arguments
        func_name = func.__name__
        cache_key = get_cache_key(func_name, **kwargs)
        ttl = CACHE_TTL.get(func_name.split("_")[0], 300)  # Default 5 minutes

        # Check if result is cached
        cached_result = redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {cache_key}")
            return json.loads(cached_result)

        # Execute function and cache result
        result = func(*args, **kwargs)
        if result:
            redis_client.setex(cache_key, ttl, json.dumps(result))
            logger.info(f"Cached result for {cache_key} (TTL: {ttl}s)")

        return result
    return wrapper


async def fetch_async(url: str, headers: Dict = None, params: Dict = None) -> Dict:
    """Async function to fetch data from API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"API request failed: {response.status} - {await response.text()}")
                    return None
                return await response.json()
    except Exception as e:
        logger.error(f"Async fetch error: {e}")
        return None


def fetch_data(url: str, headers: Dict = None, params: Dict = None) -> Dict:
    """Fetch data from API with error handling"""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e}")
        raise APIError(f"API request failed: {e}")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection Error: {e}")
        raise APIError(f"Connection failed: {e}")
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout Error: {e}")
        raise APIError(f"Request timed out: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Exception: {e}")
        raise APIError(f"Request failed: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON Decode Error: {e}")
        raise APIError(f"Failed to parse response: {e}")


# NSE (Nairobi Stock Exchange) API Functions
@cache_result
def stock_price(symbol: str) -> Dict:
    """
    Fetch current stock price from NSE API
    
    Args:
        symbol: Stock symbol (e.g., 'SCOM' for Safaricom)
        
    Returns:
        Dict containing stock information
    """
    logger.info(f"Fetching stock price for {symbol}")
    
    # Try NSE API first
    if NSE_API_KEY:
        try:
            headers = {
                "x-rapidapi-key": NSE_API_KEY,
                "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com"
            }
            
            url = f"https://nairobi-stock-exchange-nse.p.rapidapi.com/stocks/{symbol}"
            data = fetch_data(url, headers=headers)
            if data:
                return {
                    "symbol": symbol,
                    "price": data.get("price", 0),
                    "change": data.get("change", 0),
                    "change_percent": data.get("change_percent", 0),
                    "volume": data.get("volume", 0),
                    "timestamp": datetime.now().isoformat(),
                    "source": "NSE API"
                }
        except Exception as e:
            logger.warning(f"NSE API failed, falling back to Yahoo Finance: {e}")
    
    # Fallback to Yahoo Finance API
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
        }
        
        # Append .NR to symbol for NSE stocks on Yahoo Finance
        yahoo_symbol = f"{symbol}.NR"
        url = f"https://yahoo-finance166.p.rapidapi.com/api/v1/quote-information"
        params = {"symbol": yahoo_symbol, "region": "KE"}
        
        data = fetch_data(url, headers=headers, params=params)
        if data and "quoteResponse" in data and "result" in data["quoteResponse"]:
            quote = data["quoteResponse"]["result"][0]
            return {
                "symbol": symbol,
                "price": quote.get("regularMarketPrice", 0),
                "change": quote.get("regularMarketChange", 0),
                "change_percent": quote.get("regularMarketChangePercent", 0),
                "volume": quote.get("regularMarketVolume", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "Yahoo Finance API"
            }
    except Exception as e:
        logger.error(f"Failed to fetch stock price for {symbol} from Yahoo Finance: {e}")
    
    # If both APIs fail, try Alpha Vantage
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": f"{symbol}.NBO",  # For NSE stocks on Alpha Vantage
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        data = fetch_data(url, params=params)
        if data and "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "symbol": symbol,
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_percent": float(quote.get("10. change percent", "0%").replace("%", "")),
                "volume": int(quote.get("06. volume", 0)),
                "timestamp": datetime.now().isoformat(),
                "source": "Alpha Vantage API"
            }
    except Exception as e:
        logger.error(f"Failed to fetch stock price for {symbol} from Alpha Vantage: {e}")
    
    return None


@cache_result
def stock_historical(symbol: str, period: str = "1y") -> Dict:
    """
    Fetch historical stock prices
    
    Args:
        symbol: Stock symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max)
        
    Returns:
        Dict containing historical price data
    """
    logger.info(f"Fetching historical stock data for {symbol} over {period}")
    
    # Determine interval based on period
    interval_map = {
        "1d": "5m",
        "5d": "30m",
        "1mo": "1d",
        "3mo": "1d",
        "6mo": "1d",
        "1y": "1wk",
        "5y": "1mo",
        "max": "1mo"
    }
    interval = interval_map.get(period, "1d")
    
    # Try Yahoo Finance API
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
        }
        
        # Append .NR to symbol for NSE stocks on Yahoo Finance
        yahoo_symbol = f"{symbol}.NR"
        url = f"https://yahoo-finance166.p.rapidapi.com/api/v1/historical-data"
        params = {
            "symbol": yahoo_symbol, 
            "region": "KE",
            "period": period,
            "interval": interval
        }
        
        data = fetch_data(url, headers=headers, params=params)
        if data and "prices" in data:
            processed_data = []
            for item in data["prices"]:
                if "date" in item and "close" in item:
                    processed_data.append({
                        "date": datetime.fromtimestamp(item["date"]).isoformat(),
                        "open": item.get("open", 0),
                        "high": item.get("high", 0),
                        "low": item.get("low", 0),
                        "close": item.get("close", 0),
                        "volume": item.get("volume", 0)
                    })
                    
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": processed_data,
                "source": "Yahoo Finance API"
            }
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {symbol} from Yahoo Finance: {e}")
    
    # Fallback to Alpha Vantage
    try:
        url = "https://www.alphavantage.co/query"
        
        # Map period to Alpha Vantage function
        if period in ["1d", "5d"]:
            function = "TIME_SERIES_INTRADAY"
            outputsize = "full" if period == "5d" else "compact"
            interval_param = "60min"
        elif period in ["1mo", "3mo", "6mo", "1y"]:
            function = "TIME_SERIES_DAILY"
            outputsize = "full" if period in ["6mo", "1y"] else "compact"
            interval_param = None
        else:
            function = "TIME_SERIES_WEEKLY"
            outputsize = "full"
            interval_param = None
        
        params = {
            "function": function,
            "symbol": f"{symbol}.NBO",
            "outputsize": outputsize,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        if interval_param:
            params["interval"] = interval_param
        
        data = fetch_data(url, params=params)
        if data:
            # Determine the time series key based on function
            time_series_key = None
            if function == "TIME_SERIES_INTRADAY":
                time_series_key = f"Time Series ({interval_param})"
            elif function == "TIME_SERIES_DAILY":
                time_series_key = "Time Series (Daily)"
            elif function == "TIME_SERIES_WEEKLY":
                time_series_key = "Weekly Time Series"
            
            if time_series_key and time_series_key in data:
                processed_data = []
                time_series = data[time_series_key]
                
                for date, values in time_series.items():
                    processed_data.append({
                        "date": date,
                        "open": float(values.get("1. open", 0)),
                        "high": float(values.get("2. high", 0)),
                        "low": float(values.get("3. low", 0)),
                        "close": float(values.get("4. close", 0)),
                        "volume": int(values.get("5. volume", 0))
                    })
                
                # Sort by date
                processed_data.sort(key=lambda x: x["date"])
                
                return {
                    "symbol": symbol,
                    "period": period,
                    "interval": interval,
                    "data": processed_data,
                    "source": "Alpha Vantage API"
                }
    except Exception as e:
        logger.error(f"Failed to fetch historical data for {symbol} from Alpha Vantage: {e}")
    
    return None


@cache_result
def stock_search(query: str) -> List[Dict]:
    """
    Search for stocks by name or symbol
    
    Args:
        query: Search query
        
    Returns:
        List of matching stocks
    """
    logger.info(f"Searching for stocks with query: {query}")
    
    # Try Alpha Vantage first for search
    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        data = fetch_data(url, params=params)
        if data and "bestMatches" in data:
            results = []
            for match in data["bestMatches"]:
                # Filter for Kenyan stock exchange (NBO)
                if ".NBO" in match.get("1. symbol", ""):
                    results.append({
                        "symbol": match.get("1. symbol", "").replace(".NBO", ""),
                        "name": match.get("2. name", ""),
                        "type": match.get("3. type", ""),
                        "region": match.get("4. region", ""),
                        "market": match.get("5. marketOpen", ""),
                        "close": match.get("6. marketClose", ""),
                        "timezone": match.get("7. timezone", ""),
                        "currency": match.get("8. currency", "")
                    })
            
            return results
    except Exception as e:
        logger.error(f"Failed to search stocks with Alpha Vantage: {e}")
    
    # Fallback to Yahoo Finance
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
        }
        
        url = f"https://yahoo-finance166.p.rapidapi.com/api/v1/search"
        params = {"query": query, "region": "KE"}
        
        data = fetch_data(url, headers=headers, params=params)
        if data and "quotes" in data:
            results = []
            for quote in data["quotes"]:
                # Filter for Kenyan stock exchange
                if "NR" in quote.get("symbol", "") or "NBO" in quote.get("symbol", ""):
                    symbol = quote.get("symbol", "").replace(".NR", "").replace(".NBO", "")
                    results.append({
                        "symbol": symbol,
                        "name": quote.get("shortname", ""),
                        "type": quote.get("quoteType", ""),
                        "exchange": quote.get("exchange", ""),
                        "currency": quote.get("currency", "KES")
                    })
            
            return results
    except Exception as e:
        logger.error(f"Failed to search stocks with Yahoo Finance: {e}")
    
    return []


@cache_result
def nse_market_summary() -> Dict:
    """
    Fetch NSE market summary (indices, top gainers, top losers)
    
    Returns:
        Dict containing market summary data
    """
    logger.info("Fetching NSE market summary")
    
    # Use Alpha Vantage for top gainers and losers
    try:
        # For demo purposes, we'll use a pre-defined list of indices
        # In production, this would be fetched from an actual API
        indices = [
            {"name": "NSE 20 Share Index", "value": 1741.54, "change": 4.23, "change_percent": 0.24},
            {"name": "NSE 25 Share Index", "value": 3205.36, "change": 10.87, "change_percent": 0.34},
            {"name": "NSE All Share Index (NASI)", "value": 126.74, "change": 0.53, "change_percent": 0.42}
        ]
        
        # Get top gainers and losers by fetching and sorting individual stocks
        # This is a simplified approach; in production, use actual API endpoints for top movers
        top_stocks = []
        for symbol in ["SCOM", "EQTY", "KCB", "COOP", "ABSA", "BAT", "EABL", "SCBK", "DTK", "JUB"]:
            stock_data = stock_price(symbol)
            if stock_data:
                top_stocks.append(stock_data)
        
        # Sort by change percent for gainers and losers
        top_stocks.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
        gainers = top_stocks[:5]
        
        top_stocks.sort(key=lambda x: x.get("change_percent", 0))
        losers = top_stocks[:5]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": indices,
            "top_gainers": gainers,
            "top_losers": losers
        }
    except Exception as e:
        logger.error(f"Failed to fetch NSE market summary: {e}")
    
    return None


# CBK (Central Bank of Kenya) API Functions
@cache_result
def cbk_rates() -> Dict:
    """
    Fetch CBK interest rates and monetary policy information
    
    Returns:
        Dict containing CBK rates
    """
    logger.info("Fetching CBK interest rates")
    
    # In production, this would use a real CBK API
    # For demo, we'll return simulated data
    
    return {
        "timestamp": datetime.now().isoformat(),
        "central_bank_rate": 10.5,  # Example value
        "interbank_rate": 10.2,
        "t_bill_91_day": 12.4,
        "t_bill_182_day": 12.7,
        "t_bill_364_day": 13.2,
        "last_updated": "2024-03-01",
        "source": "CBK"
    }


@cache_result
def forex_rates(base_currency: str = "KES") -> Dict:
    """
    Fetch foreign exchange rates
    
    Args:
        base_currency: Base currency code (default: KES)
        
    Returns:
        Dict containing forex rates against major currencies
    """
    logger.info(f"Fetching forex rates with base currency {base_currency}")
    
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "exchange-rates7.p.rapidapi.com"
        }
        
        url = "https://exchange-rates7.p.rapidapi.com/convert"
        
        # Define the currencies we want to fetch
        target_currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "ZAR", "UGX", "TZS", "RWF"]
        
        # Fetch rates for each currency pair
        rates = {}
        for currency in target_currencies:
            if currency == base_currency:
                rates[currency] = 1.0
                continue
                
            params = {
                "from": base_currency,
                "to": currency,
                "amount": "1"
            }
            
            try:
                data = fetch_data(url, headers=headers, params=params)
                if data and "result" in data:
                    rates[currency] = float(data["result"]["convertedAmount"])
            except Exception as e:
                logger.warning(f"Failed to fetch {base_currency}/{currency} rate: {e}")
        
        # If KES is not the base currency but we need KES rates
        if base_currency != "KES" and "KES" not in rates:
            params = {
                "from": base_currency,
                "to": "KES",
                "amount": "1"
            }
            
            try:
                data = fetch_data(url, headers=headers, params=params)
                if data and "result" in data:
                    rates["KES"] = float(data["result"]["convertedAmount"])
            except Exception as e:
                logger.warning(f"Failed to fetch {base_currency}/KES rate: {e}")
        
        return {
            "base_currency": base_currency,
            "rates": rates,
            "timestamp": datetime.now().isoformat(),
            "source": "Exchange Rates API"
        }
    except Exception as e:
        logger.error(f"Failed to fetch forex rates: {e}")
    
    # Fallback to Alpha Vantage
    try:
        url = "https://www.alphavantage.co/query"
        
        # For Alpha Vantage, we need to fetch each currency pair separately
        rates = {}
        
        for currency in ["USD", "EUR", "GBP", "JPY", "CNY", "ZAR"]:
            if currency == base_currency:
                rates[currency] = 1.0
                continue
                
            from_currency = base_currency
            to_currency = currency
            
            # Alpha Vantage doesn't support all currency pairs directly
            # For KES, we might need to convert through USD
            direct_conversion = True
            
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            try:
                data = fetch_data(url, params=params)
                if data and "Realtime Currency Exchange Rate" in data:
                    exchange_data = data["Realtime Currency Exchange Rate"]
                    rate = float(exchange_data.get("5. Exchange Rate", 0))
                    rates[currency] = rate
                else:
                    # If direct conversion failed, try through USD
                    direct_conversion = False
            except:
                direct_conversion = False
            
            # If direct conversion failed, try through USD
            if not direct_conversion:
                try:
                    # Get base currency to USD rate
                    params1 = {
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": from_currency,
                        "to_currency": "USD",
                        "apikey": ALPHA_VANTAGE_API_KEY
                    }
                    
                    data1 = fetch_data(url, params=params1)
                    if data1 and "Realtime Currency Exchange Rate" in data1:
                        exchange_data1 = data1["Realtime Currency Exchange Rate"]
                        rate1 = float(exchange_data1.get("5. Exchange Rate", 0))
                        
                        # Get USD to target currency rate
                        params2 = {
                            "function": "CURRENCY_EXCHANGE_RATE",
                            "from_currency": "USD",
                            "to_currency": to_currency,
                            "apikey": ALPHA_VANTAGE_API_KEY
                        }
                        
                        data2 = fetch_data(url, params=params2)
                        if data2 and "Realtime Currency Exchange Rate" in data2:
                            exchange_data2 = data2["Realtime Currency Exchange Rate"]
                            rate2 = float(exchange_data2.get("5. Exchange Rate", 0))
                            
                            # Calculate cross rate
                            rates[currency] = rate1 * rate2
                except Exception as e:
                    logger.warning(f"Failed to fetch {from_currency}/{to_currency} rate via USD: {e}")
        
        return {
            "base_currency": base_currency,
            "rates": rates,
            "timestamp": datetime.now().isoformat(),
            "source": "Alpha Vantage API"
        }
    except Exception as e:
        logger.error(f"Failed to fetch forex rates from Alpha Vantage: {e}")
    
    return None


# Cryptocurrency API Functions
@cache_result
def crypto_prices(symbols: List[str] = None) -> Dict:
    """
    Fetch cryptocurrency prices
    
    Args:
        symbols: List of cryptocurrency symbols (default: BTC, ETH, BNB, SOL, ADA, XRP)
        
    Returns:
        Dict containing crypto prices
    """
    logger.info(f"Fetching cryptocurrency prices for {symbols}")
    
    if symbols is None:
        symbols = ["BTC", "ETH", "BNB", "SOL", "ADA", "XRP"]
    
    try:
        # First try CoinGecko API
        url = "https://api.coingecko.com/api/v3/simple/price"
        
        # Convert symbols to CoinGecko IDs
        coin_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "SHIB": "shiba-inu",
            "AVAX": "avalanche-2"
        }
        
        coin_ids = [coin_map.get(symbol.upper(), symbol.lower()) for symbol in symbols if symbol.upper() in coin_map]
        
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd,kes",
            "include_24hr_change": "true"
        }
        
        data = fetch_data(url, params=params)
        if data:
            results = {}
            
            for coin_id, values in data.items():
                # Find the original symbol
                original_symbol = next((sym for sym, mapped in coin_map.items() if mapped == coin_id), coin_id.upper())
                
                results[original_symbol] = {
                    "usd_price": values.get("usd", 0),
                    "kes_price": values.get("kes", 0),
                    "change_24h": values.get("usd_24h_change", 0),
                    "timestamp": datetime.now().isoformat(),
                    "source": "CoinGecko API"
                }
            
            return results
    except Exception as e:
        logger.error(f"Failed to fetch crypto prices from CoinGecko: {e}")
    
    # Fallback to Alpha Vantage
    try:
        url = "https://www.alphavantage.co/query"
        
        results = {}
        for symbol in symbols:
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": symbol,
                "to_currency": "USD",
                "apikey": ALPHA_VANTAGE_API_KEY
            }
            
            try:
                data = fetch_data(url, params=params)
                if data and "Realtime Currency Exchange Rate" in data:
                    exchange_data = data["Realtime Currency Exchange Rate"]
                    usd_price = float(exchange_data.get("5. Exchange Rate", 0))
                    
                    # Get KES price via USD/KES rate
                    params_kes = {
                        "function": "CURRENCY_EXCHANGE_RATE",
                        "from_currency": "USD",
                        "to_currency": "KES",
                        "apikey": ALPHA_VANTAGE_API_KEY
                    }
                    
                    data_kes = fetch_data(url, params=params_kes)
                    kes_rate = 1.0
                    if data_kes and "Realtime Currency Exchange Rate" in data_kes:
                        exchange_data_kes = data_kes["Realtime Currency Exchange Rate"]
                        kes_rate = float(exchange_data_kes.get("5. Exchange Rate", 0))
                    
                    results[symbol] = {
                        "usd_price": usd_price,
                        "kes_price": usd_price * kes_rate,
                        "change_24h": 0,  # Alpha Vantage doesn't provide 24h change directly
                        "timestamp": datetime.now().isoformat(),
                        "source": "Alpha Vantage API"
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} crypto price: {e}")
        
        return results
    except Exception as e:
        logger.error(f"Failed to fetch crypto prices from Alpha Vantage: {e}")
    
    return None


@cache_result
def crypto_historical(symbol: str, vs_currency: str = "usd", days: int = 30) -> Dict:
    """
    Fetch historical cryptocurrency prices
    
    Args:
        symbol: Cryptocurrency symbol
        vs_currency: Quote currency (default: usd)
        days: Number of days of data to fetch (default: 30)
        
    Returns:
        Dict containing historical price data
    """
    logger.info(f"Fetching historical crypto data for {symbol} vs {vs_currency} for {days} days")
    
    try:
        # Convert symbol to CoinGecko ID
        coin_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "DOT": "polkadot",
            "SHIB": "shiba-inu",
            "AVAX": "avalanche-2"
        }
        
        coin_id = coin_map.get(symbol.upper(), symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        
        data = fetch_data(url, params=params)
        if data and "prices" in data:
            price_data = []
            for timestamp, price in data["prices"]:
                # Convert timestamp (milliseconds) to datetime
                date = datetime.fromtimestamp(timestamp / 1000).isoformat()
                price_data.append({"date": date, "price": price})
            
            # Get volume and market cap data if available
            volume_data = []
            if "total_volumes" in data:
                for timestamp, volume in data["total_volumes"]:
                    date = datetime.fromtimestamp(timestamp / 1000).isoformat()
                    volume_data.append({"date": date, "volume": volume})
            
            market_cap_data = []
            if "market_caps" in data:
                for timestamp, market_cap in data["market_caps"]:
                    date = datetime.fromtimestamp(timestamp / 1000).isoformat()
                    market_cap_data.append({"date": date, "market_cap": market_cap})
            
            return {
                "symbol": symbol,
                "vs_currency": vs_currency,
                "days": days,
                "prices": price_data,
                "volumes": volume_data,
                "market_caps": market_cap_data,
                "source": "CoinGecko API"
            }
    except Exception as e:
        logger.error(f"Failed to fetch historical crypto data: {e}")
    
    return None


# News and Market Analysis Functions
@cache_result
def market_news(category: str = "business", keywords: str = None, limit: int = 10) -> List[Dict]:
    """
    Fetch financial and market news
    
    Args:
        category: News category (business, finance, markets)
        keywords: Specific keywords to search for
        limit: Maximum number of news items to return
        
    Returns:
        List of news items
    """
    logger.info(f"Fetching {category} news with keywords: {keywords}")
    
    try:
        headers = {
            "x-rapidapi-key": NEWS_API_KEY or YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "news-api14.p.rapidapi.com"
        }
        
        url = "https://news-api14.p.rapidapi.com/v2/top-headlines"
        
        params = {
            "country": "ke",
            "category": category,
            "language": "en",
            "pageSize": limit
        }
        
        if keywords:
            params["q"] = keywords
        
        data = fetch_data(url, headers=headers, params=params)
        if data and "articles" in data:
            news_items = []
            for article in data["articles"][:limit]:
                news_items.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "url": article.get("url", ""),
                    "published_at": article.get("publishedAt", ""),
                    "content": article.get("content", "")
                })
            
            return news_items
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
    
    # Fallback to Yahoo Finance news
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com"
        }
        
        query = keywords or category
        url = f"https://yahoo-finance166.p.rapidapi.com/api/news/search"
        params = {"query": query, "region": "global", "snippetCount": limit}
        
        data = fetch_data(url, headers=headers, params=params)
        if data and "news" in data:
            news_items = []
            for article in data["news"][:limit]:
                news_items.append({
                    "title": article.get("title", ""),
                    "description": article.get("snippet", ""),
                    "source": article.get("publisher", "Yahoo Finance"),
                    "url": article.get("link", ""),
                    "published_at": article.get("pubDate", ""),
                    "content": article.get("snippet", "")
                })
            
            return news_items
    except Exception as e:
        logger.error(f"Failed to fetch news from Yahoo Finance: {e}")
    
    return []


@cache_result
def stock_sentiment(symbol: str) -> Dict:
    """
    Analyze sentiment for a stock based on news and social media
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dict containing sentiment analysis
    """
    logger.info(f"Analyzing sentiment for {symbol}")
    
    try:
        headers = {
            "x-rapidapi-key": YAHOO_FINANCE_API_KEY,
            "x-rapidapi-host": "stock-sentiment-analysis.p.rapidapi.com"
        }
        
        url = f"https://stock-sentiment-analysis.p.rapidapi.com/stock/{symbol}/news"
        
        data = fetch_data(url, headers=headers)
        if data and "sentiment" in data:
            sentiment_data = data["sentiment"]
            return {
                "symbol": symbol,
                "sentiment_score": sentiment_data.get("score", 0),
                "sentiment_label": sentiment_data.get("label", "neutral"),
                "positive_articles": sentiment_data.get("positive", 0),
                "negative_articles": sentiment_data.get("negative", 0),
                "neutral_articles": sentiment_data.get("neutral", 0),
                "total_articles": sentiment_data.get("total", 0),
                "timestamp": datetime.now().isoformat(),
                "source": "Stock Sentiment API"
            }
    except Exception as e:
        logger.error(f"Failed to fetch stock sentiment: {e}")
    
    # Simple fallback: analyze sentiment from news headlines
    try:
        news = market_news(keywords=symbol, limit=10)
        if news:
            # Count sentiment based on simple keyword matching (demo only)
            positive_keywords = ["up", "rise", "gain", "profit", "growth", "positive", "bullish", "outperform"]
            negative_keywords = ["down", "fall", "loss", "decline", "drop", "negative", "bearish", "underperform"]
            
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for item in news:
                title = item.get("title", "").lower()
                description = item.get("description", "").lower()
                
                positive_matches = sum(1 for keyword in positive_keywords if keyword in title or keyword in description)
                negative_matches = sum(1 for keyword in negative_keywords if keyword in title or keyword in description)
                
                if positive_matches > negative_matches:
                    positive_count += 1
                elif negative_matches > positive_matches:
                    negative_count += 1
                else:
                    neutral_count += 1
            
            total = len(news)
            sentiment_score = (positive_count - negative_count) / total if total > 0 else 0
            
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "symbol": symbol,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "positive_articles": positive_count,
                "negative_articles": negative_count,
                "neutral_articles": neutral_count,
                "total_articles": total,
                "timestamp": datetime.now().isoformat(),
                "source": "News Analysis"
            }
    except Exception as e:
        logger.error(f"Failed to analyze sentiment from news: {e}")
    
    return None


# Mobile Money and Payment Integration
def mpesa_loan_rates() -> Dict:
    """
    Fetch M-Pesa loan rates (M-Shwari, KCB M-Pesa, Fuliza)
    
    Returns:
        Dict containing M-Pesa loan products and rates
    """
    logger.info("Fetching M-Pesa loan rates")
    
    # In a production environment, this would integrate with Safaricom's API
    # For now, we'll use simulated data
    
    return {
        "loan_products": [
            {
                "name": "M-Shwari",
                "provider": "NCBA",
                "interest_rate": 7.5,  # 7.5% per month
                "processing_fee": 0.0,
                "min_amount": 500,
                "max_amount": 50000,
                "term_days": 30,
                "requirements": [
                    "Active M-Pesa for at least 6 months",
                    "Active M-Shwari account",
                    "Good repayment history"
                ]
            },
            {
                "name": "KCB M-Pesa",
                "provider": "KCB",
                "interest_rate": 8.64,  # 8.64% per month
                "processing_fee": 0.0,
                "min_amount": 500,
                "max_amount": 100000,
                "term_days": 30,
                "requirements": [
                    "Active M-Pesa for at least 6 months",
                    "KCB account not required"
                ]
            },
            {
                "name": "Fuliza",
                "provider": "Safaricom",
                "interest_rate": 0.98,  # 0.98% per day
                "processing_fee": 1.0,  # % of overdraft amount
                "min_amount": 1,
                "max_amount": 70000,
                "term_days": "Until next M-Pesa deposit",
                "requirements": [
                    "Active M-Pesa for at least 6 months",
                    "Good M-Pesa transaction history"
                ]
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "PesaGuru Database"
    }


def bank_loan_rates() -> Dict:
    """
    Fetch bank loan rates from major Kenyan banks
    
    Returns:
        Dict containing bank loan products and rates
    """
    logger.info("Fetching bank loan rates")
    
    # Simulated data for development
    return {
        "personal_loans": [
            {
                "bank": "Equity Bank",
                "product": "Personal Loan",
                "interest_rate": 13.0,  # 13% per annum
                "processing_fee": 1.5,  # % of loan amount
                "min_amount": 10000,
                "max_amount": 10000000,
                "min_term_months": 3,
                "max_term_months": 60
            },
            {
                "bank": "KCB",
                "product": "Personal Loan",
                "interest_rate": 13.5,  # 13.5% per annum
                "processing_fee": 2.0,  # % of loan amount
                "min_amount": 10000,
                "max_amount": 7000000,
                "min_term_months": 3,
                "max_term_months": 72
            },
            {
                "bank": "Co-operative Bank",
                "product": "Personal Loan",
                "interest_rate": 13.2,  # 13.2% per annum
                "processing_fee": 2.0,  # % of loan amount
                "min_amount": 50000,
                "max_amount": 5000000,
                "min_term_months": 12,
                "max_term_months": 60
            }
        ],
        "mortgages": [
            {
                "bank": "HF Group",
                "product": "Home Loan",
                "interest_rate": 13.0,  # 13% per annum
                "processing_fee": 1.5,  # % of loan amount
                "min_amount": 1000000,
                "max_amount": 100000000,
                "max_term_years": 25
            },
            {
                "bank": "Stanbic Bank",
                "product": "Home Loan",
                "interest_rate": 12.8,  # 12.8% per annum
                "processing_fee": 1.0,  # % of loan amount
                "min_amount": 1000000,
                "max_amount": 150000000,
                "max_term_years": 20
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "PesaGuru Database"
    }


# Investment Products and Recommendations
def unit_trust_rates() -> Dict:
    """
    Fetch unit trust rates from Kenyan fund managers
    
    Returns:
        Dict containing unit trust products and rates
    """
    logger.info("Fetching unit trust rates")
    
    # Simulated data for development
    return {
        "money_market_funds": [
            {
                "fund_manager": "CIC Asset Management",
                "fund_name": "CIC Money Market Fund",
                "annual_yield": 10.25,  # %
                "minimum_investment": 5000,
                "management_fee": 2.0,  # %
                "risk_level": "Low"
            },
            {
                "fund_manager": "Britam Asset Managers",
                "fund_name": "Britam Money Market Fund",
                "annual_yield": 10.10,  # %
                "minimum_investment": 1000,
                "management_fee": 2.0,  # %
                "risk_level": "Low"
            },
            {
                "fund_manager": "NCBA Investment Bank",
                "fund_name": "NCBA Money Market Fund",
                "annual_yield": 9.95,  # %
                "minimum_investment": 1000,
                "management_fee": 2.0,  # %
                "risk_level": "Low"
            }
        ],
        "equity_funds": [
            {
                "fund_manager": "Old Mutual",
                "fund_name": "Old Mutual Equity Fund",
                "annual_yield": 12.5,  # %
                "minimum_investment": 5000,
                "management_fee": 3.0,  # %
                "risk_level": "High"
            },
            {
                "fund_manager": "Sanlam Investments",
                "fund_name": "Sanlam Equity Fund",
                "annual_yield": 11.8,  # %
                "minimum_investment": 2500,
                "management_fee": 3.0,  # %
                "risk_level": "High"
            }
        ],
        "balanced_funds": [
            {
                "fund_manager": "ICEA Lion Asset Management",
                "fund_name": "ICEA Lion Growth Fund",
                "annual_yield": 11.2,  # %
                "minimum_investment": 5000,
                "management_fee": 2.5,  # %
                "risk_level": "Medium"
            },
            {
                "fund_manager": "CIC Asset Management",
                "fund_name": "CIC Balanced Fund",
                "annual_yield": 10.8,  # %
                "minimum_investment": 5000,
                "management_fee": 2.5,  # %
                "risk_level": "Medium"
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "PesaGuru Database"
    }


def treasury_bonds_rates() -> Dict:
    """
    Fetch treasury bonds and bills rates from CBK
    
    Returns:
        Dict containing treasury bonds and bills rates
    """
    logger.info("Fetching treasury bonds and bills rates")
    
    # Simulated data for development
    return {
        "t_bills": [
            {
                "tenor": "91 days",
                "rate": 12.4,  # %
                "next_auction_date": "2025-03-24",
                "minimum_investment": 50000
            },
            {
                "tenor": "182 days",
                "rate": 12.7,  # %
                "next_auction_date": "2025-03-24",
                "minimum_investment": 50000
            },
            {
                "tenor": "364 days",
                "rate": 13.2,  # %
                "next_auction_date": "2025-03-24",
                "minimum_investment": 50000
            }
        ],
        "t_bonds": [
            {
                "tenor": "2 years",
                "rate": 13.5,  # %
                "next_auction_date": "2025-03-31",
                "minimum_investment": 50000
            },
            {
                "tenor": "5 years",
                "rate": 14.2,  # %
                "next_auction_date": "2025-04-15",
                "minimum_investment": 50000
            },
            {
                "tenor": "10 years",
                "rate": 14.5,  # %
                "next_auction_date": "2025-04-22",
                "minimum_investment": 50000
            },
            {
                "tenor": "15 years",
                "rate": 14.8,  # %
                "next_auction_date": "2025-05-05",
                "minimum_investment": 50000
            },
            {
                "tenor": "20 years",
                "rate": 15.0,  # %
                "next_auction_date": "2025-05-12",
                "minimum_investment": 50000
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "PesaGuru Database (CBK)"
    }


# Economic Indicators and Market Data
def economic_indicators() -> Dict:
    """
    Fetch key economic indicators for Kenya
    
    Returns:
        Dict containing economic indicators
    """
    logger.info("Fetching economic indicators")
    
    # Simulated data for development
    return {
        "gdp_growth": 5.6,  # % annual
        "inflation_rate": 6.2,  # % annual
        "unemployment_rate": 5.7,  # %
        "interest_rate": 10.5,  # % (CBR)
        "exchange_rate_usd": 147.25,  # KES per USD
        "public_debt_to_gdp": 69.8,  # %
        "fiscal_deficit": -8.1,  # % of GDP
        "current_account_balance": -5.2,  # % of GDP
        "foreign_reserves": 7.5,  # USD billions
        "last_updated": "2024-03-01",
        "source": "CBK, KNBS"
    }


def sector_performance() -> Dict:
    """
    Fetch sector performance data for the NSE
    
    Returns:
        Dict containing sector performance
    """
    logger.info("Fetching sector performance")
    
    # Simulated data for development
    return {
        "sectors": [
            {
                "name": "Banking",
                "change_percent": 3.8,
                "ytd_return": 12.5,
                "stocks": ["KCB", "EQTY", "COOP", "ABSA", "SCBK", "NCBA", "DTK", "SBIC"]
            },
            {
                "name": "Telecommunication",
                "change_percent": 2.4,
                "ytd_return": 7.8,
                "stocks": ["SCOM"]
            },
            {
                "name": "Manufacturing & Allied",
                "change_percent": 1.2,
                "ytd_return": 4.5,
                "stocks": ["EABL", "BAT", "UNGA", "BOC", "CARB"]
            },
            {
                "name": "Commercial & Services",
                "change_percent": -0.8,
                "ytd_return": -3.2,
                "stocks": ["SCAN", "LKL", "NMG", "SGL", "EGAD", "XPRS"]
            },
            {
                "name": "Energy & Petroleum",
                "change_percent": 0.5,
                "ytd_return": 2.1,
                "stocks": ["KPLC", "KEGN", "TOTL", "KENO"]
            },
            {
                "name": "Insurance",
                "change_percent": -1.2,
                "ytd_return": -5.6,
                "stocks": ["JUB", "CTUM", "PAFR", "KNRE", "BRIT", "CIC"]
            },
            {
                "name": "Investment",
                "change_percent": 1.7,
                "ytd_return": 6.4,
                "stocks": ["KAPC", "NSE", "OCH", "HOME", "CFCI"]
            },
            {
                "name": "Construction & Allied",
                "change_percent": 0.9,
                "ytd_return": 3.8,
                "stocks": ["BAMB", "PORT", "ARM"]
            },
            {
                "name": "Agricultural",
                "change_percent": -0.4,
                "ytd_return": -1.8,
                "stocks": ["SASN", "WTK", "KUKZ", "KAPC"]
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "source": "PesaGuru Analysis"
    }


# API Utility Functions
async def fetch_multiple_apis(query_list: List[Dict]) -> Dict:
    """
    Fetch data from multiple APIs concurrently
    
    Args:
        query_list: List of dictionaries with 'function', 'args', and 'kwargs' keys
        
    Returns:
        Dict with API responses
    """
    logger.info(f"Fetching data from {len(query_list)} APIs concurrently")
    
    try:
        # Map function names to actual functions
        function_map = {
            "stock_price": stock_price,
            "stock_historical": stock_historical,
            "stock_search": stock_search,
            "nse_market_summary": nse_market_summary,
            "cbk_rates": cbk_rates,
            "forex_rates": forex_rates,
            "crypto_prices": crypto_prices,
            "crypto_historical": crypto_historical,
            "market_news": market_news,
            "stock_sentiment": stock_sentiment,
            "mpesa_loan_rates": mpesa_loan_rates,
            "bank_loan_rates": bank_loan_rates,
            "unit_trust_rates": unit_trust_rates,
            "treasury_bonds_rates": treasury_bonds_rates,
            "economic_indicators": economic_indicators,
            "sector_performance": sector_performance
        }
        
        # Create tasks for each API request
        results = {}
        tasks = []
        
        for i, query in enumerate(query_list):
            func_name = query.get("function")
            args = query.get("args", [])
            kwargs = query.get("kwargs", {})
            
            if func_name in function_map:
                func = function_map[func_name]
                
                # Handle the function call
                key = query.get("key", f"{func_name}_{i}")
                
                # Use asyncio.to_thread to run synchronous functions asynchronously
                task = asyncio.to_thread(func, *args, **kwargs)
                tasks.append((key, task))
            else:
                logger.warning(f"Unknown function: {func_name}")
        
        # Run tasks concurrently
        for key, task in tasks:
            try:
                result = await task
                results[key] = result
            except Exception as e:
                logger.error(f"Error fetching data for {key}: {e}")
                results[key] = None
        
        return results
    except Exception as e:
        logger.error(f"Error running concurrent API requests: {e}")
        return {}


def get_market_snapshot() -> Dict:
    """
    Get a comprehensive market snapshot with key data
    
    Returns:
        Dict containing market snapshot data
    """
    logger.info("Generating market snapshot")
    
    try:
        # Define the APIs to call
        query_list = [
            {"function": "nse_market_summary", "key": "nse_summary"},
            {"function": "forex_rates", "key": "forex_rates"},
            {"function": "crypto_prices", "key": "crypto_prices"},
            {"function": "market_news", "kwargs": {"limit": 5}, "key": "latest_news"},
            {"function": "cbk_rates", "key": "cbk_rates"},
            {"function": "economic_indicators", "key": "economic_indicators"}
        ]
        
        # Use asyncio to run the requests
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(fetch_multiple_apis(query_list))
        
        # Add timestamp
        results["timestamp"] = datetime.now().isoformat()
        
        return results
    except Exception as e:
        logger.error(f"Error generating market snapshot: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def analyze_investment_options(risk_profile: str = "moderate") -> Dict:
    """
    Analyze investment options based on risk profile
    
    Args:
        risk_profile: Risk profile (conservative, moderate, aggressive)
        
    Returns:
        Dict containing recommended investment options
    """
    logger.info(f"Analyzing investment options for {risk_profile} risk profile")
    
    try:
        # Define the APIs to call
        query_list = [
            {"function": "unit_trust_rates", "key": "unit_trusts"},
            {"function": "treasury_bonds_rates", "key": "treasury_bonds"},
            {"function": "sector_performance", "key": "sectors"}
        ]
        
        # Use asyncio to run the requests
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(fetch_multiple_apis(query_list))
        
        # Process the data based on risk profile
        recommendations = {
            "risk_profile": risk_profile,
            "timestamp": datetime.now().isoformat(),
            "recommended_allocation": {},
            "specific_recommendations": []
        }
        
        # Set allocation percentages based on risk profile
        if risk_profile.lower() == "conservative":
            recommendations["recommended_allocation"] = {
                "money_market_funds": 50,
                "treasury_bonds": 30,
                "balanced_funds": 15,
                "equity_funds": 5
            }
        elif risk_profile.lower() == "moderate":
            recommendations["recommended_allocation"] = {
                "money_market_funds": 30,
                "treasury_bonds": 25,
                "balanced_funds": 25,
                "equity_funds": 20
            }
        elif risk_profile.lower() == "aggressive":
            recommendations["recommended_allocation"] = {
                "money_market_funds": 10,
                "treasury_bonds": 15,
                "balanced_funds": 30,
                "equity_funds": 45
            }
        else:
            recommendations["recommended_allocation"] = {
                "money_market_funds": 30,
                "treasury_bonds": 25,
                "balanced_funds": 25,
                "equity_funds": 20
            }
        
        # Add specific recommendations based on the data
        # Money Market Funds
        if "unit_trusts" in results and results["unit_trusts"]:
            money_market_funds = results["unit_trusts"].get("money_market_funds", [])
            # Sort by yield
            money_market_funds.sort(key=lambda x: x.get("annual_yield", 0), reverse=True)
            
            if money_market_funds:
                for fund in money_market_funds[:2]:  # Top 2 funds
                    recommendations["specific_recommendations"].append({
                        "type": "Money Market Fund",
                        "name": fund.get("fund_name"),
                        "provider": fund.get("fund_manager"),
                        "expected_return": fund.get("annual_yield"),
                        "risk_level": "Low",
                        "min_investment": fund.get("minimum_investment"),
                        "allocation_percentage": recommendations["recommended_allocation"].get("money_market_funds") / 2
                    })
        
        # Treasury Bonds/Bills
        if "treasury_bonds" in results and results["treasury_bonds"]:
            t_bonds = results["treasury_bonds"].get("t_bonds", [])
            t_bills = results["treasury_bonds"].get("t_bills", [])
            
            # For conservative profile, recommend shorter-term bonds
            if risk_profile.lower() == "conservative":
                # Add T-bills recommendation
                if t_bills:
                    t_bills.sort(key=lambda x: x.get("tenor", ""), reverse=False)  # Shorter tenors first
                    recommendations["specific_recommendations"].append({
                        "type": "Treasury Bill",
                        "name": f"{t_bills[0].get('tenor')} T-Bill",
                        "provider": "Central Bank of Kenya",
                        "expected_return": t_bills[0].get("rate"),
                        "risk_level": "Very Low",
                        "min_investment": t_bills[0].get("minimum_investment"),
                        "allocation_percentage": recommendations["recommended_allocation"].get("treasury_bonds") / 2
                    })
                
                # Add short-term bond recommendation
                if t_bonds:
                    # Filter for shorter-term bonds (2-5 years)
                    short_bonds = [bond for bond in t_bonds if "2 years" in bond.get("tenor", "") or "5 years" in bond.get("tenor", "")]
                    if short_bonds:
                        recommendations["specific_recommendations"].append({
                            "type": "Treasury Bond",
                            "name": f"{short_bonds[0].get('tenor')} T-Bond",
                            "provider": "Central Bank of Kenya",
                            "expected_return": short_bonds[0].get("rate"),
                            "risk_level": "Low",
                            "min_investment": short_bonds[0].get("minimum_investment"),
                            "allocation_percentage": recommendations["recommended_allocation"].get("treasury_bonds") / 2
                        })
            
            # For moderate profile, mix of medium-term bonds
            elif risk_profile.lower() == "moderate":
                if t_bonds:
                    # Filter for medium-term bonds (5-10 years)
                    medium_bonds = [bond for bond in t_bonds if "5 years" in bond.get("tenor", "") or "10 years" in bond.get("tenor", "")]
                    if medium_bonds:
                        recommendations["specific_recommendations"].append({
                            "type": "Treasury Bond",
                            "name": f"{medium_bonds[0].get('tenor')} T-Bond",
                            "provider": "Central Bank of Kenya",
                            "expected_return": medium_bonds[0].get("rate"),
                            "risk_level": "Medium-Low",
                            "min_investment": medium_bonds[0].get("minimum_investment"),
                            "allocation_percentage": recommendations["recommended_allocation"].get("treasury_bonds")
                        })
            
            # For aggressive profile, longer-term bonds
            elif risk_profile.lower() == "aggressive":
                if t_bonds:
                    # Filter for longer-term bonds (15-20 years)
                    long_bonds = [bond for bond in t_bonds if "15 years" in bond.get("tenor", "") or "20 years" in bond.get("tenor", "")]
                    if long_bonds:
                        recommendations["specific_recommendations"].append({
                            "type": "Treasury Bond",
                            "name": f"{long_bonds[0].get('tenor')} T-Bond",
                            "provider": "Central Bank of Kenya",
                            "expected_return": long_bonds[0].get("rate"),
                            "risk_level": "Medium",
                            "min_investment": long_bonds[0].get("minimum_investment"),
                            "allocation_percentage": recommendations["recommended_allocation"].get("treasury_bonds")
                        })
        
        # Balanced Funds
        if "unit_trusts" in results and results["unit_trusts"]:
            balanced_funds = results["unit_trusts"].get("balanced_funds", [])
            
            if balanced_funds and (risk_profile.lower() in ["moderate", "aggressive"]):
                # Sort by yield
                balanced_funds.sort(key=lambda x: x.get("annual_yield", 0), reverse=True)
                
                if balanced_funds:
                    recommendations["specific_recommendations"].append({
                        "type": "Balanced Fund",
                        "name": balanced_funds[0].get("fund_name"),
                        "provider": balanced_funds[0].get("fund_manager"),
                        "expected_return": balanced_funds[0].get("annual_yield"),
                        "risk_level": "Medium",
                        "min_investment": balanced_funds[0].get("minimum_investment"),
                        "allocation_percentage": recommendations["recommended_allocation"].get("balanced_funds")
                    })
        
        # Equity Funds and Stocks
        if "unit_trusts" in results and results["unit_trusts"] and "sectors" in results and results["sectors"]:
            equity_funds = results["unit_trusts"].get("equity_funds", [])
            sectors = results["sectors"].get("sectors", [])
            
            # For moderate and aggressive profiles, add equity funds
            if risk_profile.lower() in ["moderate", "aggressive"] and equity_funds:
                # Sort by yield
                equity_funds.sort(key=lambda x: x.get("annual_yield", 0), reverse=True)
                
                if equity_funds:
                    recommendations["specific_recommendations"].append({
                        "type": "Equity Fund",
                        "name": equity_funds[0].get("fund_name"),
                        "provider": equity_funds[0].get("fund_manager"),
                        "expected_return": equity_funds[0].get("annual_yield"),
                        "risk_level": "High",
                        "min_investment": equity_funds[0].get("minimum_investment"),
                        "allocation_percentage": recommendations["recommended_allocation"].get("equity_funds") / 2
                    })
            
            # For aggressive profile, add direct stock recommendations from top performing sectors
            if risk_profile.lower() == "aggressive" and sectors:
                # Sort sectors by performance
                sectors.sort(key=lambda x: x.get("change_percent", 0), reverse=True)
                
                if sectors:
                    top_sector = sectors[0]
                    recommendations["specific_recommendations"].append({
                        "type": "Direct Stocks",
                        "name": f"Top stocks in {top_sector.get('name')} sector",
                        "provider": "Nairobi Securities Exchange",
                        "expected_return": "Variable",
                        "risk_level": "High",
                        "recommended_stocks": top_sector.get("stocks", [])[:3],  # Top 3 stocks
                        "allocation_percentage": recommendations["recommended_allocation"].get("equity_funds") / 2
                    })
        
        return recommendations
    except Exception as e:
        logger.error(f"Error analyzing investment options: {e}")
        return {
            "error": str(e),
            "risk_profile": risk_profile,
            "timestamp": datetime.now().isoformat()
        }


# Main function for testing
async def main():
    """Test the market data functions"""
    print("Testing PesaGuru Market Data API...")
    
    # Test stock price function
    print("\nTesting stock_price function...")
    safcom = stock_price("SCOM")
    print(json.dumps(safcom, indent=2))
    
    # Test forex rates function
    print("\nTesting forex_rates function...")
    forex = forex_rates()
    print(json.dumps(forex, indent=2))
    
    # Test market news function
    print("\nTesting market_news function...")
    news = market_news(limit=3)
    print(json.dumps(news, indent=2))
    
    # Test comprehensive market snapshot
    print("\nTesting market snapshot...")
    snapshot = get_market_snapshot()
    print(json.dumps(snapshot, indent=2))
    
    # Test investment recommendations
    print("\nTesting investment recommendations...")
    recommendations = analyze_investment_options("moderate")
    print(json.dumps(recommendations, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
