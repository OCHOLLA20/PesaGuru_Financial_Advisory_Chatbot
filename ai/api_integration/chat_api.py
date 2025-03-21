import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import httpx
import redis
import pandas as pd
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("pesaguru.api")

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(title="PesaGuru Chat API", version="1.0.0")

# Initialize Redis for caching
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# API keys and credentials
NSE_API_KEY = os.getenv("NSE_API_KEY")
CBK_API_KEY = os.getenv("CBK_API_KEY")
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
OPEN_EXCHANGE_RATES_API_KEY = os.getenv("OPEN_EXCHANGE_RATES_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API Base URLs
NSE_API_URL = "https://nairobi-stock-exchange-nse.p.rapidapi.com"
CBK_API_URL = "https://cbk-bonds.p.rapidapi.com"
MPESA_API_URL = "https://sandbox.safaricom.co.ke"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
FOREX_API_URL = "https://exchange-rates7.p.rapidapi.com"
NEWS_API_URL = "https://news-api14.p.rapidapi.com"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# Security
api_key_header = APIKeyHeader(name="X-API-Key")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# API models
class StockInfo(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    sector: Optional[str] = None
    previous_close: Optional[float] = None
    open_price: Optional[float] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None

class ForexRate(BaseModel):
    base_currency: str
    quote_currency: str
    rate: float
    timestamp: datetime

class LoanRate(BaseModel):
    provider: str
    product: str
    interest_rate: float
    term: str
    min_amount: float
    max_amount: float
    requirements: List[str]

class CryptoPrice(BaseModel):
    coin: str
    symbol: str
    price_usd: float
    price_kes: float
    change_24h: float
    market_cap: float
    volume_24h: float

class FinancialNews(BaseModel):
    title: str
    published_at: datetime
    source: str
    url: str
    summary: str
    sentiment: Optional[str] = None

class ChatbotQuery(BaseModel):
    user_id: str
    query_text: str
    context: Optional[Dict[str, Any]] = None
    location: Optional[str] = None
    language: str = "en"  # Default to English, can be "sw" for Swahili

class ChatbotResponse(BaseModel):
    response_text: str
    data: Optional[Dict[str, Any]] = None
    intent: str
    confidence: float
    sources: Optional[List[str]] = None
    follow_up_questions: Optional[List[str]] = None

# Helper functions
def get_cache_key(prefix: str, **kwargs) -> str:
    """Generate a cache key from prefix and parameters"""
    params = "_".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
    return f"{prefix}_{params}"

async def get_from_cache_or_fetch(
    cache_key: str, 
    fetch_func, 
    expiry_seconds: int = 3600,
    **kwargs
) -> Any:
    """Get data from cache or fetch from source and cache it"""
    # Try to get from cache first
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {cache_key}")
        return json.loads(cached_data)
    
    # If not in cache, fetch it
    logger.info(f"Cache miss for {cache_key}, fetching from source")
    data = await fetch_func(**kwargs)
    
    # Cache the result
    redis_client.setex(
        cache_key,
        expiry_seconds,
        json.dumps(data, default=str)  # Handle datetime serialization
    )
    
    return data

async def validate_api_key(api_key: str = Security(api_key_header)):
    """Validate the API key"""
    valid_api_key = os.getenv("PESAGURU_API_KEY")
    if api_key != valid_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return api_key

# API integration classes
class NSEApiClient:
    """Client for interacting with the Nairobi Stock Exchange API"""
    
    def __init__(self):
        self.api_key = NSE_API_KEY
        self.base_url = NSE_API_URL
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "nairobi-stock-exchange-nse.p.rapidapi.com"
        }
    
    async def get_stock_price(self, symbol: str) -> Optional[StockInfo]:
        """
        Get current stock price for a given NSE symbol
        
        Args:
            symbol (str): NSE stock symbol (e.g., "SCOM" for Safaricom)
            
        Returns:
            StockInfo: Stock information or None if not found
        """
        cache_key = get_cache_key("nse_stock", symbol=symbol)
        
        async def fetch_stock():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/stocks/{symbol}",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching stock {symbol}: {response.text}")
                    return None
                
                data = response.json()
                
                # Process the data into our model
                return {
                    "symbol": symbol,
                    "name": data.get("name", symbol),
                    "price": float(data.get("price", 0)),
                    "change": float(data.get("change", 0)),
                    "change_percent": float(data.get("change_percentage", 0)),
                    "volume": int(data.get("volume", 0)),
                    "sector": data.get("sector"),
                    "previous_close": float(data.get("previous_close", 0)),
                    "open_price": float(data.get("open", 0)),
                    "day_high": float(data.get("high", 0)),
                    "day_low": float(data.get("low", 0))
                }
        
        result = await get_from_cache_or_fetch(
            cache_key, 
            fetch_stock,
            expiry_seconds=300  # Cache for 5 minutes
        )
        
        if result:
            return StockInfo(**result)
        return None
    
    async def get_market_index(self, index: str = "NSE20") -> Dict[str, Any]:
        """
        Get current market index value
        
        Args:
            index (str): Index name (default: "NSE20")
            
        Returns:
            Dict: Index information
        """
        cache_key = get_cache_key("nse_index", index=index)
        
        async def fetch_index():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/index/{index}",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching index {index}: {response.text}")
                    return {"error": "Failed to fetch index data"}
                
                data = response.json()
                return data
        
        return await get_from_cache_or_fetch(
            cache_key, 
            fetch_index,
            expiry_seconds=300  # Cache for 5 minutes
        )
    
    async def get_top_gainers(self, limit: int = 5) -> List[StockInfo]:
        """
        Get top gaining stocks for the day
        
        Args:
            limit (int): Number of top gainers to return
            
        Returns:
            List[StockInfo]: List of top gaining stocks
        """
        cache_key = get_cache_key("nse_top_gainers", limit=limit)
        
        async def fetch_gainers():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/top-gainers",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching top gainers: {response.text}")
                    return []
                
                data = response.json()
                stocks = []
                
                for item in data[:limit]:
                    stocks.append({
                        "symbol": item.get("symbol"),
                        "name": item.get("name", item.get("symbol")),
                        "price": float(item.get("price", 0)),
                        "change": float(item.get("change", 0)),
                        "change_percent": float(item.get("change_percentage", 0)),
                        "volume": int(item.get("volume", 0))
                    })
                
                return stocks
        
        stocks_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_gainers,
            expiry_seconds=300  # Cache for 5 minutes
        )
        
        return [StockInfo(**stock) for stock in stocks_data]
    
    async def get_top_losers(self, limit: int = 5) -> List[StockInfo]:
        """
        Get top losing stocks for the day
        
        Args:
            limit (int): Number of top losers to return
            
        Returns:
            List[StockInfo]: List of top losing stocks
        """
        cache_key = get_cache_key("nse_top_losers", limit=limit)
        
        async def fetch_losers():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/top-losers",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching top losers: {response.text}")
                    return []
                
                data = response.json()
                stocks = []
                
                for item in data[:limit]:
                    stocks.append({
                        "symbol": item.get("symbol"),
                        "name": item.get("name", item.get("symbol")),
                        "price": float(item.get("price", 0)),
                        "change": float(item.get("change", 0)),
                        "change_percent": float(item.get("change_percentage", 0)),
                        "volume": int(item.get("volume", 0))
                    })
                
                return stocks
        
        stocks_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_losers,
            expiry_seconds=300  # Cache for 5 minutes
        )
        
        return [StockInfo(**stock) for stock in stocks_data]
    
    async def search_stocks(self, query: str) -> List[StockInfo]:
        """
        Search for stocks by name or symbol
        
        Args:
            query (str): Search query
            
        Returns:
            List[StockInfo]: List of matching stocks
        """
        cache_key = get_cache_key("nse_search", query=query)
        
        async def fetch_search():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search?q={query}",
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error searching stocks for {query}: {response.text}")
                    return []
                
                data = response.json()
                stocks = []
                
                for item in data:
                    stocks.append({
                        "symbol": item.get("symbol"),
                        "name": item.get("name", item.get("symbol")),
                        "price": float(item.get("price", 0)),
                        "change": float(item.get("change", 0)),
                        "change_percent": float(item.get("change_percentage", 0)),
                        "volume": int(item.get("volume", 0)),
                        "sector": item.get("sector")
                    })
                
                return stocks
        
        stocks_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_search,
            expiry_seconds=3600  # Cache for 1 hour
        )
        
        return [StockInfo(**stock) for stock in stocks_data]


class CBKApiClient:
    """Client for interacting with the Central Bank of Kenya API"""
    
    def __init__(self):
        self.api_key = CBK_API_KEY
        self.base_url = CBK_API_URL
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "cbk-bonds.p.rapidapi.com",
            "Content-Type": "application/json"
        }
    
    async def get_forex_rates(self) -> List[ForexRate]:
        """
        Get current forex exchange rates from CBK
        
        Returns:
            List[ForexRate]: List of exchange rates
        """
        cache_key = "cbk_forex_rates"
        
        async def fetch_rates():
            async with httpx.AsyncClient() as client:
                # First get the token for authentication
                response = await client.post(
                    f"{self.base_url}/service/token/",
                    headers=self.headers,
                    json={}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting CBK token: {response.text}")
                    return []
                
                token_data = response.json()
                token = token_data.get("token")
                
                if not token:
                    logger.error("No token found in CBK response")
                    return []
                
                # Update headers with the token
                headers_with_token = self.headers.copy()
                headers_with_token["Authorization"] = f"Bearer {token}"
                
                # Get forex rates
                rates_response = await client.get(
                    f"{self.base_url}/forex/latest",
                    headers=headers_with_token
                )
                
                if rates_response.status_code != 200:
                    logger.error(f"Error fetching forex rates: {rates_response.text}")
                    return []
                
                rates_data = rates_response.json()
                rates = []
                
                now = datetime.now()
                
                for rate in rates_data:
                    rates.append({
                        "base_currency": "KES",
                        "quote_currency": rate.get("currency"),
                        "rate": float(rate.get("rate", 0)),
                        "timestamp": now
                    })
                
                return rates
        
        rates_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_rates,
            expiry_seconds=86400  # Cache for 24 hours
        )
        
        return [ForexRate(**rate) for rate in rates_data]
    
    async def get_cbr_rate(self) -> Dict[str, Any]:
        """
        Get current Central Bank Rate (CBR)
        
        Returns:
            Dict: CBR information
        """
        cache_key = "cbk_cbr_rate"
        
        async def fetch_cbr():
            async with httpx.AsyncClient() as client:
                # First get the token for authentication
                response = await client.post(
                    f"{self.base_url}/service/token/",
                    headers=self.headers,
                    json={}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting CBK token: {response.text}")
                    return {"error": "Failed to fetch CBR data"}
                
                token_data = response.json()
                token = token_data.get("token")
                
                if not token:
                    logger.error("No token found in CBK response")
                    return {"error": "Failed to authenticate with CBK"}
                
                # Update headers with the token
                headers_with_token = self.headers.copy()
                headers_with_token["Authorization"] = f"Bearer {token}"
                
                # Get CBR rate
                cbr_response = await client.get(
                    f"{self.base_url}/rates/cbr",
                    headers=headers_with_token
                )
                
                if cbr_response.status_code != 200:
                    logger.error(f"Error fetching CBR rate: {cbr_response.text}")
                    return {"error": "Failed to fetch CBR data"}
                
                cbr_data = cbr_response.json()
                
                return {
                    "rate": float(cbr_data.get("rate", 0)),
                    "effective_date": cbr_data.get("effective_date"),
                    "last_updated": cbr_data.get("last_updated")
                }
        
        return await get_from_cache_or_fetch(
            cache_key, 
            fetch_cbr,
            expiry_seconds=86400  # Cache for 24 hours
        )
    
    async def get_treasury_bond_rates(self) -> Dict[str, Any]:
        """
        Get current treasury bond rates
        
        Returns:
            Dict: Bond rates information
        """
        cache_key = "cbk_bond_rates"
        
        async def fetch_bond_rates():
            async with httpx.AsyncClient() as client:
                # First get the token for authentication
                response = await client.post(
                    f"{self.base_url}/service/token/",
                    headers=self.headers,
                    json={}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting CBK token: {response.text}")
                    return {"error": "Failed to fetch bond rates"}
                
                token_data = response.json()
                token = token_data.get("token")
                
                if not token:
                    logger.error("No token found in CBK response")
                    return {"error": "Failed to authenticate with CBK"}
                
                # Update headers with the token
                headers_with_token = self.headers.copy()
                headers_with_token["Authorization"] = f"Bearer {token}"
                
                # Get bond rates
                bond_response = await client.get(
                    f"{self.base_url}/bonds/current",
                    headers=headers_with_token
                )
                
                if bond_response.status_code != 200:
                    logger.error(f"Error fetching bond rates: {bond_response.text}")
                    return {"error": "Failed to fetch bond rates"}
                
                bond_data = bond_response.json()
                
                return bond_data
        
        return await get_from_cache_or_fetch(
            cache_key, 
            fetch_bond_rates,
            expiry_seconds=86400  # Cache for 24 hours
        )


class MPesaApiClient:
    """Client for interacting with Safaricom M-Pesa API (Daraja)"""
    
    def __init__(self):
        self.consumer_key = MPESA_CONSUMER_KEY
        self.consumer_secret = MPESA_CONSUMER_SECRET
        self.base_url = MPESA_API_URL
        self.access_token = None
        self.token_expiry = datetime.now()
    
    async def _get_access_token(self):
        """Get OAuth access token for M-Pesa API"""
        if self.access_token and datetime.now() < self.token_expiry:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                auth=(self.consumer_key, self.consumer_secret)
            )
            
            if response.status_code != 200:
                logger.error(f"Error getting M-Pesa access token: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to authenticate with M-Pesa API"
                )
            
            data = response.json()
            self.access_token = data.get("access_token")
            # Token typically expires in 1 hour
            self.token_expiry = datetime.now() + timedelta(seconds=3598)
            
            return self.access_token
    
    async def get_loan_rates(self) -> List[LoanRate]:
        """
        Get current loan rates for mobile lenders (M-Shwari, KCB-M-Pesa, etc.)
        
        Note: This is a mocked implementation as there's no direct API for this.
        In production, this data would either come from a database or
        scraping from mobile lenders' official websites.
        
        Returns:
            List[LoanRate]: List of loan products and rates
        """
        cache_key = "mpesa_loan_rates"
        
        async def fetch_loan_rates():
            # This would typically make an API call, but we'll mock the data
            # since M-Pesa doesn't have a public API for loan rates
            
            # Mock data based on typical rates in Kenya
            return [
                {
                    "provider": "M-Shwari",
                    "product": "Standard Loan",
                    "interest_rate": 7.5,
                    "term": "30 days",
                    "min_amount": 100.0,
                    "max_amount": 50000.0,
                    "requirements": ["M-Pesa account", "Active for 6 months"]
                },
                {
                    "provider": "KCB-M-Pesa",
                    "product": "Standard Loan",
                    "interest_rate": 8.64,
                    "term": "30 days",
                    "min_amount": 100.0,
                    "max_amount": 100000.0,
                    "requirements": ["M-Pesa account", "Active for 3 months"]
                },
                {
                    "provider": "Fuliza",
                    "product": "Overdraft",
                    "interest_rate": 1.083,  # Daily rate
                    "term": "30 days max",
                    "min_amount": 100.0,
                    "max_amount": 70000.0,
                    "requirements": ["M-Pesa account", "Active for 6 months"]
                },
                {
                    "provider": "Tala",
                    "product": "Standard Loan",
                    "interest_rate": 15.0,  # Approximate
                    "term": "30 days",
                    "min_amount": 500.0,
                    "max_amount": 50000.0,
                    "requirements": ["Smartphone", "Active for 1 month"]
                },
                {
                    "provider": "Branch",
                    "product": "Standard Loan",
                    "interest_rate": 17.0,  # Approximate
                    "term": "30-60 days",
                    "min_amount": 250.0,
                    "max_amount": 70000.0,
                    "requirements": ["Smartphone", "Active for 1 month"]
                }
            ]
        
        loan_rates_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_loan_rates,
            expiry_seconds=86400  # Cache for 24 hours
        )
        
        return [LoanRate(**rate) for rate in loan_rates_data]
    
    async def compare_loan_offers(self, amount: float, term_days: int) -> List[Dict[str, Any]]:
        """
        Compare loan offers from different mobile lenders
        
        Args:
            amount (float): Loan amount (KES)
            term_days (int): Loan term in days
            
        Returns:
            List[Dict[str, Any]]: Comparison of loan offers
        """
        # Get all loan rates
        loan_rates = await self.get_loan_rates()
        
        # Calculate total repayment amount for each loan
        loan_comparisons = []
        
        for loan in loan_rates:
            if amount < loan.min_amount or amount > loan.max_amount:
                continue
            
            # Calculate interest amount
            if loan.provider == "Fuliza":
                # Fuliza charges daily interest
                interest_amount = amount * (loan.interest_rate / 100) * min(term_days, 30)
            else:
                # Others typically charge monthly
                months = term_days / 30
                interest_amount = amount * (loan.interest_rate / 100) * months
            
            total_repayment = amount + interest_amount
            
            loan_comparisons.append({
                "provider": loan.provider,
                "product": loan.product,
                "interest_rate": loan.interest_rate,
                "loan_amount": amount,
                "term_days": term_days,
                "interest_amount": round(interest_amount, 2),
                "total_repayment": round(total_repayment, 2),
                "effective_apr": round(loan.interest_rate * 12, 2) if loan.provider != "Fuliza" else round(loan.interest_rate * 365, 2),
                "requirements": loan.requirements
            })
        
        # Sort by total repayment (lowest first)
        loan_comparisons.sort(key=lambda x: x["total_repayment"])
        
        return loan_comparisons


class CryptoApiClient:
    """Client for interacting with cryptocurrency APIs"""
    
    def __init__(self):
        self.api_key = COINGECKO_API_KEY
        self.base_url = COINGECKO_API_URL
    
    async def get_crypto_prices(self, coins: List[str] = None) -> List[CryptoPrice]:
        """
        Get current cryptocurrency prices
        
        Args:
            coins (List[str], optional): List of coin IDs to fetch
                
        Returns:
            List[CryptoPrice]: List of crypto prices
        """
        # Default coins if none specified
        if not coins:
            coins = ["bitcoin", "ethereum", "solana", "tether", "cardano"]
        
        coin_ids = ",".join(coins)
        cache_key = get_cache_key("crypto_prices", coins=coin_ids)
        
        async def fetch_crypto_prices():
            # Get KES/USD exchange rate first
            cbk_client = CBKApiClient()
            forex_rates = await cbk_client.get_forex_rates()
            
            # Find USD rate
            usd_rate = None
            for rate in forex_rates:
                if rate.quote_currency == "USD":
                    usd_rate = rate.rate
                    break
            
            if not usd_rate:
                usd_rate = 147.50  # Fallback if we can't get live rate
            
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["x-cg-api-key"] = self.api_key
                
                response = await client.get(
                    f"{self.base_url}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": coin_ids,
                        "order": "market_cap_desc",
                        "per_page": 100,
                        "page": 1,
                        "sparkline": "false"
                    },
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching crypto prices: {response.text}")
                    return []
                
                data = response.json()
                crypto_prices = []
                
                for coin in data:
                    price_usd = coin.get("current_price", 0)
                    price_kes = price_usd * usd_rate
                    
                    crypto_prices.append({
                        "coin": coin.get("id"),
                        "symbol": coin.get("symbol"),
                        "price_usd": price_usd,
                        "price_kes": price_kes,
                        "change_24h": coin.get("price_change_percentage_24h", 0),
                        "market_cap": coin.get("market_cap", 0),
                        "volume_24h": coin.get("total_volume", 0)
                    })
                
                return crypto_prices
        
        crypto_prices_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_crypto_prices,
            expiry_seconds=300  # Cache for 5 minutes
        )
        
        return [CryptoPrice(**price) for price in crypto_prices_data]


class NewsApiClient:
    """Client for interacting with financial news APIs"""
    
    def __init__(self):
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = NEWS_API_URL
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "news-api14.p.rapidapi.com"
        }
    
    async def get_financial_news(self, country: str = "kenya", limit: int = 5) -> List[FinancialNews]:
        """
        Get latest financial news
        
        Args:
            country (str): Country focus (default: "kenya")
            limit (int): Number of news items to return
            
        Returns:
            List[FinancialNews]: List of financial news
        """
        cache_key = get_cache_key("financial_news", country=country, limit=limit)
        
        async def fetch_news():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "q": f"finance {country}",
                        "language": "en",
                        "pageSize": limit
                    },
                    headers=self.headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Error fetching financial news: {response.text}")
                    return []
                
                data = response.json()
                articles = data.get("articles", [])
                news_items = []
                
                for article in articles:
                    news_items.append({
                        "title": article.get("title"),
                        "published_at": article.get("publishedAt"),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "url": article.get("url"),
                        "summary": article.get("description") or article.get("content") or "",
                        "sentiment": "neutral"  # Default sentiment, would be calculated with NLP
                    })
                
                return news_items
        
        news_data = await get_from_cache_or_fetch(
            cache_key, 
            fetch_news,
            expiry_seconds=3600  # Cache for 1 hour
        )
        
        # Convert the date strings to datetime objects
        for item in news_data:
            if isinstance(item["published_at"], str):
                try:
                    item["published_at"] = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    item["published_at"] = datetime.now()
        
        return [FinancialNews(**item) for item in news_data]


class ChatApiService:
    """Main service for the chatbot API integration"""
    
    def __init__(self):
        self.nse_client = NSEApiClient()
        self.cbk_client = CBKApiClient()
        self.mpesa_client = MPesaApiClient()
        self.crypto_client = CryptoApiClient()
        self.news_client = NewsApiClient()
    
    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Get stock information response for the chatbot"""
        stock_info = await self.nse_client.get_stock_price(symbol)
        
        if not stock_info:
            return {
                "response_text": f"I couldn't find information for the stock symbol {symbol}. Please check if the symbol is correct.",
                "data": None,
                "intent": "stock_info",
                "confidence": 0.0,
                "sources": []
            }
        
        # Format the response
        change_direction = "up" if stock_info.change > 0 else "down" if stock_info.change < 0 else "unchanged"
        change_sign = "+" if stock_info.change > 0 else ""
        
        response_text = (
            f"{stock_info.name} ({symbol}) is currently trading at KES {stock_info.price:,.2f}, "
            f"{change_direction} {change_sign}{stock_info.change_percent:.2f}% today. "
            f"The day's trading range is KES {stock_info.day_low:,.2f} - {stock_info.day_high:,.2f} "
            f"with a volume of {stock_info.volume:,} shares."
        )
        
        if stock_info.sector:
            response_text += f" It belongs to the {stock_info.sector} sector."
        
        return {
            "response_text": response_text,
            "data": stock_info.dict(),
            "intent": "stock_info",
            "confidence": 0.95,
            "sources": ["Nairobi Stock Exchange (NSE)"],
            "follow_up_questions": [
                f"What is the 52-week range for {symbol}?",
                f"How has {symbol} performed over the past year?",
                f"What is the dividend yield for {symbol}?",
                f"Can you compare {symbol} with other stocks in its sector?"
            ]
        }
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get market summary response for the chatbot"""
        top_gainers = await self.nse_client.get_top_gainers(5)
        top_losers = await self.nse_client.get_top_losers(5)
        market_index = await self.nse_client.get_market_index()
        
        # Format the response
        response_text = "Here's today's NSE market summary:\n\n"
        
        if isinstance(market_index, dict) and "value" in market_index:
            response_text += f"NSE 20 Index: {market_index['value']:,.2f} "
            if "change_percent" in market_index:
                change_sign = "+" if market_index["change_percent"] > 0 else ""
                response_text += f"({change_sign}{market_index['change_percent']:.2f}%)\n\n"
        
        response_text += "Top Gainers:\n"
        for i, stock in enumerate(top_gainers, 1):
            response_text += f"{i}. {stock.name} ({stock.symbol}): KES {stock.price:,.2f} (+{stock.change_percent:.2f}%)\n"
        
        response_text += "\nTop Losers:\n"
        for i, stock in enumerate(top_losers, 1):
            response_text += f"{i}. {stock.name} ({stock.symbol}): KES {stock.price:,.2f} ({stock.change_percent:.2f}%)\n"
        
        return {
            "response_text": response_text,
            "data": {
                "top_gainers": [stock.dict() for stock in top_gainers],
                "top_losers": [stock.dict() for stock in top_losers],
                "market_index": market_index
            },
            "intent": "market_summary",
            "confidence": 0.95,
            "sources": ["Nairobi Stock Exchange (NSE)"],
            "follow_up_questions": [
                "What are the most traded stocks today?",
                "How is the banking sector performing today?",
                "What's the current CBK rate?",
                "Can you show me recent financial news?"
            ]
        }
    
    async def get_forex_rates(self) -> Dict[str, Any]:
        """Get forex rates response for the chatbot"""
        forex_rates = await self.cbk_client.get_forex_rates()
        
        if not forex_rates:
            return {
                "response_text": "I'm sorry, I couldn't retrieve the current forex rates. Please try again later.",
                "data": None,
                "intent": "forex_rates",
                "confidence": 0.0,
                "sources": []
            }
        
        # Format the response
        response_text = "Here are the current forex exchange rates against the Kenyan Shilling (KES):\n\n"
        
        # Sort by currency code
        forex_rates.sort(key=lambda x: x.quote_currency)
        
        for rate in forex_rates:
            response_text += f"{rate.quote_currency}: {rate.rate:,.4f}\n"
        
        response_text += f"\nRates as of {forex_rates[0].timestamp.strftime('%Y-%m-%d %H:%M')} (Central Bank of Kenya)"
        
        return {
            "response_text": response_text,
            "data": {
                "rates": [rate.dict() for rate in forex_rates],
                "timestamp": forex_rates[0].timestamp.isoformat()
            },
            "intent": "forex_rates",
            "confidence": 0.95,
            "sources": ["Central Bank of Kenya (CBK)"],
            "follow_up_questions": [
                "What is the trend for USD/KES over the past month?",
                "How do I calculate currency conversion?",
                "What factors affect exchange rates?",
                "How can I hedge against currency risk?"
            ]
        }
    
    async def compare_loans(self, amount: float = 10000, term: int = 30) -> Dict[str, Any]:
        """Get loan comparison response for the chatbot"""
        loan_comparisons = await self.mpesa_client.compare_loan_offers(amount, term)
        
        if not loan_comparisons:
            return {
                "response_text": f"I couldn't find any suitable loan offers for KES {amount:,.2f} over {term} days. Try a different amount or term.",
                "data": None,
                "intent": "loan_comparison",
                "confidence": 0.0,
                "sources": []
            }
        
        # Format the response
        response_text = f"Here's a comparison of loan options for KES {amount:,.2f} over {term} days:\n\n"
        
        for i, loan in enumerate(loan_comparisons, 1):
            response_text += (
                f"{i}. {loan['provider']} ({loan['product']}):\n"
                f"   Rate: {loan['interest_rate']}% ({loan['effective_apr']}% APR)\n"
                f"   Interest: KES {loan['interest_amount']:,.2f}\n"
                f"   Total repayment: KES {loan['total_repayment']:,.2f}\n"
            )
        
        response_text += "\nPlease note that actual rates may vary based on your credit history and eligibility."
        
        return {
            "response_text": response_text,
            "data": {
                "loan_comparisons": loan_comparisons,
                "amount": amount,
                "term_days": term
            },
            "intent": "loan_comparison",
            "confidence": 0.95,
            "sources": ["M-Pesa", "KCB-M-Pesa", "Fuliza", "Tala", "Branch"],
            "follow_up_questions": [
                "What are the requirements for these loans?",
                "How quickly can I get approved?",
                "What happens if I repay the loan early?",
                "Can you compare loans for a different amount or term?"
            ]
        }
    
    async def get_crypto_prices(self) -> Dict[str, Any]:
        """Get cryptocurrency prices response for the chatbot"""
        crypto_prices = await self.crypto_client.get_crypto_prices()
        
        if not crypto_prices:
            return {
                "response_text": "I'm sorry, I couldn't retrieve the current cryptocurrency prices. Please try again later.",
                "data": None,
                "intent": "crypto_prices",
                "confidence": 0.0,
                "sources": []
            }
        
        # Format the response
        response_text = "Here are the current cryptocurrency prices in KES and USD:\n\n"
        
        for crypto in crypto_prices:
            change_sign = "+" if crypto.change_24h > 0 else ""
            response_text += (
                f"{crypto.coin.capitalize()} ({crypto.symbol.upper()}):\n"
                f"   KES {crypto.price_kes:,.2f}\n"
                f"   USD {crypto.price_usd:,.2f}\n"
                f"   24h Change: {change_sign}{crypto.change_24h:.2f}%\n"
            )
        
        response_text += "\nPrices are updated in real-time. Cryptocurrency investments are subject to high market risk."
        
        return {
            "response_text": response_text,
            "data": {
                "crypto_prices": [crypto.dict() for crypto in crypto_prices]
            },
            "intent": "crypto_prices",
            "confidence": 0.95,
            "sources": ["CoinGecko"],
            "follow_up_questions": [
                "How do I invest in cryptocurrencies in Kenya?",
                "What are the risks of cryptocurrency investing?",
                "How has Bitcoin performed over the past year?",
                "Can you explain blockchain technology?"
            ]
        }
    
    async def get_financial_news(self) -> Dict[str, Any]:
        """Get financial news response for the chatbot"""
        news_items = await self.news_client.get_financial_news()
        
        if not news_items:
            return {
                "response_text": "I'm sorry, I couldn't retrieve the latest financial news. Please try again later.",
                "data": None,
                "intent": "financial_news",
                "confidence": 0.0,
                "sources": []
            }
        
        # Format the response
        response_text = "Here are the latest financial news headlines:\n\n"
        
        for i, news in enumerate(news_items, 1):
            response_text += (
                f"{i}. {news.title}\n"
                f"   Source: {news.source}\n"
                f"   Published: {news.published_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"   Summary: {news.summary[:100]}...\n\n"
            )
        
        return {
            "response_text": response_text,
            "data": {
                "news_items": [news.dict() for news in news_items]
            },
            "intent": "financial_news",
            "confidence": 0.95,
            "sources": ["Financial News API"],
            "follow_up_questions": [
                "How might these news affect the Kenyan market?",
                "Can you summarize the most important financial news?",
                "What's the latest news about the Kenyan economy?",
                "How should I adjust my investment strategy based on recent news?"
            ]
        }
    
    async def process_query(self, query: ChatbotQuery) -> ChatbotResponse:
        """
        Process a chatbot query and return an appropriate response
        
        Args:
            query (ChatbotQuery): User query
            
        Returns:
            ChatbotResponse: Chatbot response
        """
        # This is a simplified intent detection
        # In a real implementation, this would use a more sophisticated NLP model
        query_text = query.query_text.lower()
        
        # Get response based on intent
        response_data = None
        
        if any(term in query_text for term in ["stock", "share", "price", "nse", "safaricom", "equity", "kcb"]):
            # Extract stock symbol if present
            stock_symbols = {
                "safaricom": "SCOM",
                "equity": "EQTY",
                "kcb": "KCB",
                "coop": "COOP",
                "eabl": "EABL",
                "bamburi": "BAMB",
                "britam": "BRIT",
                "jubilee": "JUB",
                "kengen": "KEGN",
                "kenya airways": "KA"
            }
            
            symbol = None
            for name, symbol_code in stock_symbols.items():
                if name in query_text:
                    symbol = symbol_code
                    break
            
            if symbol:
                response_data = await self.get_stock_info(symbol)
            elif "market" in query_text or "summary" in query_text:
                response_data = await self.get_market_summary()
            else:
                # Default to market summary if no specific stock is mentioned
                response_data = await self.get_market_summary()
                
        elif any(term in query_text for term in ["forex", "exchange", "dollar", "euro", "pound", "currency"]):
            response_data = await self.get_forex_rates()
            
        elif any(term in query_text for term in ["loan", "borrow", "credit", "m-shwari", "fuliza", "m-pesa", "tala", "branch"]):
            # Extract loan amount if present
            amount = 10000  # Default amount
            term = 30  # Default term
            
            # Try to extract amount
            import re
            amount_match = re.search(r'(\d+,?\d*\.?\d*)', query_text)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                except ValueError:
                    pass
            
            # Try to extract term
            term_match = re.search(r'(\d+)\s*(day|days|month|months)', query_text)
            if term_match:
                term_value = int(term_match.group(1))
                term_unit = term_match.group(2)
                
                if term_unit in ["month", "months"]:
                    term = term_value * 30  # Convert months to days
                else:
                    term = term_value
            
            response_data = await self.compare_loans(amount, term)
            
        elif any(term in query_text for term in ["crypto", "bitcoin", "ethereum", "btc", "eth", "cryptocurrency"]):
            response_data = await self.get_crypto_prices()
            
        elif any(term in query_text for term in ["news", "headlines", "article", "financial news"]):
            response_data = await self.get_financial_news()
            
        else:
            # Default fallback response
            response_data = {
                "response_text": (
                    "I'm not sure what financial information you're looking for. "
                    "You can ask me about stocks, forex rates, loans, cryptocurrencies, or financial news. "
                    "For example, try asking 'What's the current price of Safaricom stock?' or 'Show me today's forex rates.'"
                ),
                "data": None,
                "intent": "unknown",
                "confidence": 0.5,
                "sources": [],
                "follow_up_questions": [
                    "What's the current price of Safaricom stock?",
                    "Show me today's market summary",
                    "What are the current forex rates?",
                    "Compare loan options for 10,000 KES",
                    "What are the current cryptocurrency prices?"
                ]
            }
        
        # Translate response if language is Swahili
        if query.language.lower() == "sw":
            # In a real implementation, this would use a proper translation service
            # For now, we just add a note indicating translation would happen
            response_data["response_text"] = "[Translated to Swahili] " + response_data["response_text"]
        
        return ChatbotResponse(**response_data)


# Create API endpoints
chat_api_service = ChatApiService()

@app.post("/api/chat", response_model=ChatbotResponse, dependencies=[Depends(validate_api_key)])
async def chat(query: ChatbotQuery):
    """
    Process a chatbot query and return a response
    """
    return await chat_api_service.process_query(query)

@app.get("/api/stocks/{symbol}", dependencies=[Depends(validate_api_key)])
async def get_stock(symbol: str):
    """
    Get current stock price for a given NSE symbol
    """
    nse_client = NSEApiClient()
    stock_info = await nse_client.get_stock_price(symbol)
    
    if not stock_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock {symbol} not found"
        )
    
    return stock_info

@app.get("/api/market/summary", dependencies=[Depends(validate_api_key)])
async def get_market_summary():
    """
    Get current NSE market summary
    """
    nse_client = NSEApiClient()
    top_gainers = await nse_client.get_top_gainers(5)
    top_losers = await nse_client.get_top_losers(5)
    market_index = await nse_client.get_market_index()
    
    return {
        "top_gainers": [stock.dict() for stock in top_gainers],
        "top_losers": [stock.dict() for stock in top_losers],
        "market_index": market_index
    }

@app.get("/api/forex", dependencies=[Depends(validate_api_key)])
async def get_forex_rates():
    """
    Get current forex exchange rates from CBK
    """
    cbk_client = CBKApiClient()
    forex_rates = await cbk_client.get_forex_rates()
    
    return {
        "rates": [rate.dict() for rate in forex_rates],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/loans/compare", dependencies=[Depends(validate_api_key)])
async def compare_loans(amount: float = 10000, term_days: int = 30):
    """
    Compare loan offers from different mobile lenders
    """
    mpesa_client = MPesaApiClient()
    loan_comparisons = await mpesa_client.compare_loan_offers(amount, term_days)
    
    return {
        "loan_comparisons": loan_comparisons,
        "amount": amount,
        "term_days": term_days
    }

@app.get("/api/crypto", dependencies=[Depends(validate_api_key)])
async def get_crypto_prices(coins: str = None):
    """
    Get current cryptocurrency prices
    """
    coin_list = coins.split(",") if coins else None
    crypto_client = CryptoApiClient()
    crypto_prices = await crypto_client.get_crypto_prices(coin_list)
    
    return {
        "crypto_prices": [crypto.dict() for crypto in crypto_prices],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/news", dependencies=[Depends(validate_api_key)])
async def get_financial_news(country: str = "kenya", limit: int = 5):
    """
    Get latest financial news
    """
    news_client = NewsApiClient()
    news_items = await news_client.get_financial_news(country, limit)
    
    return {
        "news_items": [news.dict() for news in news_items],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
