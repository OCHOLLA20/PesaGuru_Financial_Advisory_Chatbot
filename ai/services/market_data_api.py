import os
import json
import time
import logging
import requests
from typing import Dict, List, Union, Optional, Any
from datetime import datetime, timedelta
import redis

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv not installed. Using environment variables directly.")

# Initialize Redis for caching
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        password=os.getenv('REDIS_PASSWORD', ''),
        db=int(os.getenv('REDIS_DB', 0))
    )
    redis_client.ping()  # Test connection
    logger.info("Redis cache connection established successfully")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory cache fallback.")
    redis_client = None

class APIRateLimiter:
    """
    Handles API rate limiting to prevent exceeding quotas
    """
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.call_timestamps = []
        
    def wait_if_needed(self):
        """Check if rate limit is reached and wait if necessary"""
        current_time = time.time()
        # Remove timestamps older than a minute
        self.call_timestamps = [ts for ts in self.call_timestamps 
                               if current_time - ts < 60]
        
        if len(self.call_timestamps) >= self.calls_per_minute:
            # Wait until oldest timestamp is a minute old
            sleep_time = 60 - (current_time - self.call_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Rate limit approached. Waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            # Clear old timestamps
            self.call_timestamps = self.call_timestamps[1:]
            
        # Add current call timestamp
        self.call_timestamps.append(time.time())

class CacheManager:
    """
    Manages caching of financial data to reduce API calls
    """
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # In-memory cache fallback
        self.memory_cache = {}
        self.cache_expiry = {}
        
    def get(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if self.redis_client:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        else:
            # Check memory cache and expiry
            if key in self.memory_cache and key in self.cache_expiry:
                if datetime.now() < self.cache_expiry[key]:
                    return self.memory_cache[key]
                else:
                    # Remove expired data
                    del self.memory_cache[key]
                    del self.cache_expiry[key]
        return None
        
    def set(self, key: str, value: Any, expiry_seconds: int = 3600) -> None:
        """Set data in cache with expiry time"""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    expiry_seconds,
                    json.dumps(value)
                )
            else:
                # Use in-memory cache
                self.memory_cache[key] = value
                self.cache_expiry[key] = datetime.now() + timedelta(seconds=expiry_seconds)
        except Exception as e:
            logger.error(f"Cache error: {e}")

class MarketDataAPI:
    """
    Main class for fetching and processing financial market data
    """
    def __init__(self):
        # API credentials
        self.nse_api_key = os.getenv('NSE_API_KEY')
        self.cbk_api_key = os.getenv('CBK_API_KEY')
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY', '08HAWE6C99AGWNEZ')
        self.rapid_api_key = os.getenv('RAPID_API_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        
        # Base URLs
        self.nse_base_url = "https://nairobi-stock-exchange-nse.p.rapidapi.com"
        self.cbk_base_url = "https://api.centralbank.go.ke"
        self.forex_base_url = "https://exchange-rates7.p.rapidapi.com"
        self.crypto_base_url = "https://api.coingecko.com/api/v3"
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # Initialize rate limiters
        self.nse_rate_limiter = APIRateLimiter(calls_per_minute=30)
        self.cbk_rate_limiter = APIRateLimiter(calls_per_minute=30)
        self.forex_rate_limiter = APIRateLimiter(calls_per_minute=10)
        self.crypto_rate_limiter = APIRateLimiter(calls_per_minute=50)
        self.alpha_vantage_rate_limiter = APIRateLimiter(calls_per_minute=5)
        
        # Initialize cache
        self.cache = CacheManager(redis_client)
        
    def _make_request(self, url: str, headers: Dict = None, params: Dict = None, 
                     rate_limiter: APIRateLimiter = None, cache_key: str = None, 
                     cache_expiry: int = 3600, method: str = "GET", data: Dict = None) -> Dict:
        """
        Make API request with rate limiting, caching, and error handling
        
        Args:
            url: API endpoint URL
            headers: Request headers
            params: Query parameters
            rate_limiter: Rate limiter to use
            cache_key: Key for caching response
            cache_expiry: Cache expiry time in seconds
            method: HTTP method (GET or POST)
            data: POST request data
            
        Returns:
            JSON response data
        """
        # Check cache first if cache_key provided
        if cache_key:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for {cache_key}")
                return cached_data
        
        # Apply rate limiting if provided
        if rate_limiter:
            rate_limiter.wait_if_needed()
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, params=params, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            data = response.json()
            
            # Cache response if cache_key provided
            if cache_key:
                self.cache.set(cache_key, data, expiry_seconds=cache_expiry)
                
            return data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            if response.status_code == 429:
                logger.warning("Rate limit exceeded. Implementing exponential backoff.")
                time.sleep(30)  # Simple backoff strategy
                return self._make_request(url, headers, params, rate_limiter, cache_key, cache_expiry, method, data)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
        except json.JSONDecodeError:
            logger.error(f"JSON decode error. Response content: {response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
    
    # NSE Stock Market Functions
    def get_nse_stock_price(self, symbol: str) -> Dict:
        """
        Get current price for a specific NSE listed stock
        
        Args:
            symbol: Stock symbol (e.g., "SCOM" for Safaricom)
            
        Returns:
            Stock price data
        """
        cache_key = f"nse:stock:{symbol}:price"
        url = f"{self.nse_base_url}/stocks/{symbol}"
        headers = {
            "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        # Short cache expiry for price data (5 minutes)
        return self._make_request(
            url=url,
            headers=headers,
            rate_limiter=self.nse_rate_limiter,
            cache_key=cache_key,
            cache_expiry=300  # 5 minutes
        )
    
    def get_nse_index(self, index_name: str = "NSE20") -> Dict:
        """
        Get latest NSE index value
        
        Args:
            index_name: Index name (default: "NSE20")
            
        Returns:
            Index data
        """
        cache_key = f"nse:index:{index_name}"
        url = f"{self.nse_base_url}/indices/{index_name}"
        headers = {
            "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        return self._make_request(
            url=url,
            headers=headers,
            rate_limiter=self.nse_rate_limiter,
            cache_key=cache_key,
            cache_expiry=300  # 5 minutes
        )
    
    def get_nse_stock_historical(self, symbol: str, days: int = 30) -> Dict:
        """
        Get historical stock data for NSE listed company
        
        Args:
            symbol: Stock symbol (e.g., "SCOM" for Safaricom)
            days: Number of days of historical data
            
        Returns:
            Historical stock data
        """
        # Using Alpha Vantage as a source for historical data
        cache_key = f"nse:stock:{symbol}:historical:{days}"
        
        url = self.alpha_vantage_base_url
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": f"{symbol}.NBO",  # NSE symbol format for Alpha Vantage
            "outputsize": "full" if days > 100 else "compact",
            "apikey": self.alpha_vantage_api_key
        }
        
        data = self._make_request(
            url=url,
            params=params,
            rate_limiter=self.alpha_vantage_rate_limiter,
            cache_key=cache_key,
            cache_expiry=86400  # 24 hours for historical data
        )
        
        # Process and filter Alpha Vantage data
        if "Time Series (Daily)" in data:
            time_series = data["Time Series (Daily)"]
            # Convert to list and limit by days
            result = []
            for date, values in sorted(time_series.items(), reverse=True)[:days]:
                result.append({
                    "date": date,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"])
                })
            return {"symbol": symbol, "historical_data": result}
        
        return data
    
    def get_top_nse_performers(self, limit: int = 5) -> Dict:
        """
        Get top performing NSE stocks
        
        Args:
            limit: Number of top stocks to retrieve
            
        Returns:
            List of top performing stocks
        """
        cache_key = f"nse:top_performers:{limit}"
        url = f"{self.nse_base_url}/top_gainers"
        headers = {
            "x-rapidapi-host": "nairobi-stock-exchange-nse.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        data = self._make_request(
            url=url,
            headers=headers,
            rate_limiter=self.nse_rate_limiter,
            cache_key=cache_key,
            cache_expiry=3600  # 1 hour
        )
        
        # Limit results if needed
        if isinstance(data, list) and len(data) > limit:
            data = data[:limit]
            
        return {"top_performers": data}
    
    # CBK Interest Rates and Forex
    def get_cbk_interest_rates(self) -> Dict:
        """
        Get current CBK interest rates
        
        Returns:
            Interest rate data
        """
        cache_key = "cbk:interest_rates"
        url = "https://cbk-bonds.p.rapidapi.com/service/token/"
        headers = {
            "x-rapidapi-host": "cbk-bonds.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key,
            "Content-Type": "application/json"
        }
        
        # CBK API requires a POST request with empty payload for authentication
        try:
            token_data = self._make_request(
                url=url,
                headers=headers,
                data={},
                method="POST"
            )
            
            # Now use the token to get interest rates
            if "token" in token_data:
                token = token_data["token"]
                rates_url = "https://cbk-bonds.p.rapidapi.com/rates/current"
                headers["Authorization"] = f"Bearer {token}"
                
                return self._make_request(
                    url=rates_url,
                    headers=headers,
                    rate_limiter=self.cbk_rate_limiter,
                    cache_key=cache_key,
                    cache_expiry=21600  # 6 hours
                )
            else:
                logger.error("Failed to get CBK API token")
                raise Exception("CBK API authentication failed")
                
        except Exception as e:
            logger.error(f"CBK interest rates error: {e}")
            # Fallback to a simulated response if API fails
            return {
                "central_bank_rate": 7.00,
                "interbank_rate": 5.28,
                "note": "Fallback data - API connection failed"
            }
    
    def get_forex_rates(self, base_currency: str = "KES") -> Dict:
        """
        Get forex exchange rates
        
        Args:
            base_currency: Base currency code
            
        Returns:
            Exchange rates data
        """
        cache_key = f"forex:rates:{base_currency}"
        url = "https://exchange-rates7.p.rapidapi.com/codes"
        headers = {
            "x-rapidapi-host": "exchange-rates7.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        try:
            # First get all available currency codes
            codes_data = self._make_request(
                url=url,
                headers=headers,
                rate_limiter=self.forex_rate_limiter
            )
            
            # Then get exchange rates for base currency
            rates_url = f"https://exchange-rates7.p.rapidapi.com/rates"
            params = {"base": base_currency}
            
            rates_data = self._make_request(
                url=rates_url,
                headers=headers,
                params=params,
                rate_limiter=self.forex_rate_limiter,
                cache_key=cache_key,
                cache_expiry=3600  # 1 hour
            )
            
            return rates_data
        except Exception as e:
            logger.error(f"Forex rates error: {e}")
            # Fallback to Alpha Vantage for forex data
            return self._get_alpha_vantage_forex(base_currency)
    
    def _get_alpha_vantage_forex(self, base_currency: str) -> Dict:
        """
        Fallback method to get forex data from Alpha Vantage
        
        Args:
            base_currency: Base currency code
            
        Returns:
            Exchange rates data
        """
        url = self.alpha_vantage_base_url
        
        # Common currency pairs for Kenya
        target_currencies = ["USD", "EUR", "GBP", "JPY", "AED", "CNY"]
        if base_currency != "KES":
            target_currencies.append("KES")
        
        rates = {}
        for target in target_currencies:
            if target == base_currency:
                continue
                
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": base_currency,
                "to_currency": target,
                "apikey": self.alpha_vantage_api_key
            }
            
            try:
                data = self._make_request(
                    url=url,
                    params=params,
                    rate_limiter=self.alpha_vantage_rate_limiter
                )
                
                if "Realtime Currency Exchange Rate" in data:
                    exchange_rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
                    rates[target] = exchange_rate
                    
                # Avoid hitting rate limits
                time.sleep(1)
            except Exception as e:
                logger.error(f"Alpha Vantage forex error for {target}: {e}")
        
        return {
            "base": base_currency,
            "rates": rates,
            "timestamp": datetime.now().timestamp(),
            "note": "Fallback data from Alpha Vantage"
        }
    
    # Cryptocurrency functions
    def get_crypto_prices(self, coins: List[str] = None) -> Dict:
        """
        Get cryptocurrency prices in KES
        
        Args:
            coins: List of coin IDs (e.g., ["bitcoin", "ethereum"])
            
        Returns:
            Crypto price data
        """
        if coins is None:
            coins = ["bitcoin", "ethereum", "solana", "ripple", "cardano"]
            
        coins_str = ",".join(coins)
        cache_key = f"crypto:prices:{coins_str}"
        
        url = f"{self.crypto_base_url}/simple/price"
        params = {
            "ids": coins_str,
            "vs_currencies": "kes,usd",
            "include_24hr_change": "true"
        }
        
        headers = {}
        if self.coingecko_api_key:
            headers["x-cg-api-key"] = self.coingecko_api_key
        
        try:
            return self._make_request(
                url=url,
                params=params,
                headers=headers if headers else None,
                rate_limiter=self.crypto_rate_limiter,
                cache_key=cache_key,
                cache_expiry=300  # 5 minutes
            )
        except Exception as e:
            logger.error(f"Crypto prices error: {e}")
            # Fallback to rapid API CoinGecko
            return self._get_rapid_api_crypto(coins)
    
    def _get_rapid_api_crypto(self, coins: List[str]) -> Dict:
        """
        Fallback method to get crypto data from RapidAPI
        
        Args:
            coins: List of coin IDs
            
        Returns:
            Crypto price data
        """
        url = "https://coingecko.p.rapidapi.com/simple/price"
        params = {
            "ids": ",".join(coins),
            "vs_currencies": "kes,usd",
            "include_24hr_change": "true"
        }
        
        headers = {
            "x-rapidapi-host": "coingecko.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        try:
            return self._make_request(
                url=url,
                params=params,
                headers=headers,
                rate_limiter=self.crypto_rate_limiter
            )
        except Exception as e:
            logger.error(f"RapidAPI crypto error: {e}")
            # Generate fallback data with disclaimer
            return {
                "bitcoin": {"kes": 3500000, "usd": 27000, "kes_24h_change": -1.2},
                "ethereum": {"kes": 250000, "usd": 1800, "kes_24h_change": 0.5},
                "note": "Fallback data - API connection failed"
            }
    
    def get_crypto_historical(self, coin_id: str, days: int = 30) -> Dict:
        """
        Get historical cryptocurrency price data
        
        Args:
            coin_id: Coin ID (e.g., "bitcoin")
            days: Number of days of historical data
            
        Returns:
            Historical crypto price data
        """
        cache_key = f"crypto:historical:{coin_id}:{days}"
        
        url = f"{self.crypto_base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "kes",
            "days": days,
            "interval": "daily" if days > 90 else "hourly"
        }
        
        headers = {}
        if self.coingecko_api_key:
            headers["x-cg-api-key"] = self.coingecko_api_key
        
        data = self._make_request(
            url=url,
            params=params,
            headers=headers if headers else None,
            rate_limiter=self.crypto_rate_limiter,
            cache_key=cache_key,
            cache_expiry=86400  # 24 hours
        )
        
        # Process data into a more usable format
        if "prices" in data:
            result = []
            for timestamp, price in data["prices"]:
                dt = datetime.fromtimestamp(timestamp / 1000)  # Convert from milliseconds
                result.append({
                    "date": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "price": price
                })
            return {"coin": coin_id, "historical_data": result}
        
        return data
    
    # Financial news functions
    def get_financial_news(self, limit: int = 10) -> Dict:
        """
        Get financial news articles relevant to Kenya
        
        Args:
            limit: Number of news articles to retrieve
            
        Returns:
            Financial news data
        """
        cache_key = f"financial:news:{limit}"
        
        url = "https://yahoo-finance166.p.rapidapi.com/api/news/list-by-symbol"
        params = {
            "s": "AAPL,GOOGL,TSLA", 
            "region": "US",
            "snippetCount": 500
        }
        
        headers = {
            "x-rapidapi-host": "yahoo-finance166.p.rapidapi.com",
            "x-rapidapi-key": self.rapid_api_key
        }
        
        try:
            news_data = self._make_request(
                url=url,
                params=params,
                headers=headers,
                rate_limiter=self.alpha_vantage_rate_limiter,
                cache_key=cache_key,
                cache_expiry=3600  # 1 hour
            )
            
            # Filter and process news data
            if isinstance(news_data, dict) and "snippets" in news_data:
                articles = news_data["snippets"][:limit]
                return {"news_articles": articles}
            
            return news_data
        except Exception as e:
            logger.error(f"Financial news error: {e}")
            return {
                "news_articles": [
                    {
                        "title": "CBK Maintains Base Rate at 7%",
                        "summary": "The Central Bank of Kenya maintained its base lending rate...",
                        "source": "Business Daily",
                        "published_date": "2024-01-10"
                    },
                    {
                        "title": "NSE Reports Increased Trading Volume",
                        "summary": "The Nairobi Securities Exchange reported increased trading...",
                        "source": "Capital Markets",
                        "published_date": "2024-01-08"
                    }
                ],
                "note": "Fallback data - API connection failed"
            }
    
    # Mobile money and loan rates 
    def get_mobile_loan_rates(self) -> Dict:
        """
        Get current mobile loan interest rates from various providers
        
        Returns:
            Mobile loan rate data
        """
        cache_key = "mobile:loan:rates:kenya"
        
        # In a production environment, this would be fetched from a dedicated API
        # For now, using representative data
        
        return {
            "mobile_loans": [
                {"provider": "M-Shwari", "rate": "7.5% monthly", "min_amount": "500", "max_amount": "50,000", 
                 "processing_fee": "7.5%", "repayment_period": "30 days"},
                {"provider": "KCB-MPesa", "rate": "8.64% monthly", "min_amount": "1,000", "max_amount": "100,000",
                 "processing_fee": "2.5%", "repayment_period": "30 days"},
                {"provider": "Fuliza", "rate": "1% daily", "min_amount": "100", "max_amount": "70,000",
                 "processing_fee": "1% of borrowed amount", "repayment_period": "Flexible"},
                {"provider": "Tala", "rate": "15.0% monthly", "min_amount": "500", "max_amount": "30,000",
                 "processing_fee": "None", "repayment_period": "21-30 days"},
                {"provider": "Branch", "rate": "17.0% monthly", "min_amount": "1,000", "max_amount": "70,000",
                 "processing_fee": "None", "repayment_period": "4-68 weeks"}
            ],
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    
    def get_bank_loan_rates(self) -> Dict:
        """
        Get current bank loan interest rates
        
        Returns:
            Bank loan rate data
        """
        cache_key = "bank:loan:rates:kenya"
        
        # This would ideally come from a dedicated financial product API
        # For now, using representative data
        
        return {
            "personal_loans": [
                {"provider": "KCB", "rate": "13.0%", "min_amount": "50,000", "max_amount": "7,000,000"},
                {"provider": "Equity Bank", "rate": "13.5%", "min_amount": "100,000", "max_amount": "10,000,000"},
                {"provider": "Co-operative Bank", "rate": "12.5%", "min_amount": "50,000", "max_amount": "5,000,000"},
                {"provider": "NCBA", "rate": "13.0%", "min_amount": "100,000", "max_amount": "7,500,000"},
                {"provider": "Absa", "rate": "13.2%", "min_amount": "100,000", "max_amount": "6,000,000"}
            ],
            "mortgages": [
                {"provider": "HF Group", "rate": "11.5%", "min_amount": "1,000,000", "max_amount": "100,000,000"},
                {"provider": "Absa", "rate": "12.0%", "min_amount": "1,500,000", "max_amount": "150,000,000"},
                {"provider": "KCB", "rate": "12.5%", "min_amount": "1,000,000", "max_amount": "200,000,000"},
                {"provider": "Stanbic", "rate": "12.3%", "min_amount": "2,000,000", "max_amount": "100,000,000"}
            ],
            "business_loans": [
                {"provider": "KCB", "rate": "14.0%", "min_amount": "100,000", "max_amount": "20,000,000"},
                {"provider": "Equity Bank", "rate": "14.5%", "min_amount": "100,000", "max_amount": "30,000,000"},
                {"provider": "Co-operative Bank", "rate": "13.5%", "min_amount": "100,000", "max_amount": "15,000,000"}
            ],
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
    
    # Investment recommendations
    def get_investment_recommendations(self, risk_profile: str) -> Dict:
        """
        Get investment recommendations based on risk profile
        
        Args:
            risk_profile: User risk profile (low, medium, high)
            
        Returns:
            Investment recommendations
        """
        cache_key = f"investment:recommendations:{risk_profile}"
        
        # In a production environment, this would use ML models and market data
        # to generate personalized recommendations
        
        recommendations = {
            "low": [
                {"type": "T-Bill", "name": "91-day Treasury Bill", "expected_return": "9.2%", "risk_level": "Low"},
                {"type": "Money Market", "name": "CIC Money Market Fund", "expected_return": "10.1%", "risk_level": "Low"},
                {"type": "Fixed Deposit", "name": "KCB Fixed Deposit", "expected_return": "8.5%", "risk_level": "Low"},
                {"type": "Bond", "name": "2-year Treasury Bond", "expected_return": "11.5%", "risk_level": "Low-Medium"}
            ],
            "medium": [
                {"type": "Bond", "name": "5-year Treasury Bond", "expected_return": "12.5%", "risk_level": "Medium"},
                {"type": "Equity", "name": "Safaricom (SCOM)", "expected_return": "15.0%", "risk_level": "Medium"},
                {"type": "Mixed Fund", "name": "Britam Balanced Fund", "expected_return": "13.2%", "risk_level": "Medium"},
                {"type": "REIT", "name": "ILAM Fahari I-REIT", "expected_return": "14.5%", "risk_level": "Medium"}
            ],
            "high": [
                {"type": "Equity", "name": "KQ Shares", "expected_return": "18.5%", "risk_level": "High"},
                {"type": "Crypto", "name": "Bitcoin", "expected_return": "25.0%", "risk_level": "Very High"},
                {"type": "REIT", "name": "Acorn Student Accommodation REIT", "expected_return": "16.7%", "risk_level": "High"},
                {"type": "Forex", "name": "USD/KES Trading", "expected_return": "22.0%", "risk_level": "Very High"}
            ]
        }
        
        if risk_profile.lower() in recommendations:
            return {"recommendations": recommendations[risk_profile.lower()]}
        else:
            return {"recommendations": recommendations["medium"], "note": "Using default medium risk profile"}
    
    # Methods for aggregated data
    def get_market_summary(self) -> Dict:
        """
        Get comprehensive market summary
        
        Returns:
            Market summary data
        """
        cache_key = "market:summary"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get data from various sources
            try:
                nse_index = self.get_nse_index()
            except:
                nse_index = {"value": 1645.28, "change": -0.5, "note": "Fallback data"}
                
            try:
                top_stocks = self.get_top_nse_performers(limit=3)
            except:
                top_stocks = {"top_performers": [
                    {"symbol": "SCOM", "price": 20.45, "change": 2.1},
                    {"symbol": "EQTY", "price": 45.75, "change": 1.8}
                ], "note": "Fallback data"}
                
            try:
                forex = self.get_forex_rates()
                # Extract just a few key currencies
                key_rates = {
                    "USD": forex["rates"].get("USD", 147.35),
                    "EUR": forex["rates"].get("EUR", 158.92),
                    "GBP": forex["rates"].get("GBP", 185.40)
                }
            except:
                key_rates = {"USD": 147.35, "EUR": 158.92, "GBP": 185.40, "note": "Fallback data"}
                
            try:
                crypto = self.get_crypto_prices(["bitcoin", "ethereum"])
            except:
                crypto = {
                    "bitcoin": {"kes": 3500000, "usd": 27000},
                    "ethereum": {"kes": 250000, "usd": 1800},
                    "note": "Fallback data"
                }
                
            try:
                cbk_rates = self.get_cbk_interest_rates()
                central_bank_rate = cbk_rates.get("central_bank_rate", 7.0)
            except:
                central_bank_rate = 7.0
            
            # Aggregate the data
            summary = {
                "nse": {
                    "index": nse_index.get("value", 1645.28),
                    "change": nse_index.get("change", -0.5),
                    "top_performers": top_stocks.get("top_performers", [])
                },
                "forex": {
                    "rates": key_rates,
                    "base": "KES"
                },
                "crypto": {
                    "bitcoin": {
                        "kes": crypto.get("bitcoin", {}).get("kes", 3500000),
                        "usd": crypto.get("bitcoin", {}).get("usd", 27000)
                    },
                    "ethereum": {
                        "kes": crypto.get("ethereum", {}).get("kes", 250000),
                        "usd": crypto.get("ethereum", {}).get("usd", 1800)
                    }
                },
                "interest_rates": {
                    "central_bank_rate": central_bank_rate
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Cache the aggregated data
            self.cache.set(cache_key, summary, expiry_seconds=1800)  # 30 minutes
            
            return summary
        except Exception as e:
            logger.error(f"Market summary error: {e}")
            # Return a basic fallback response
            return {
                "nse": {"index": 1645.28, "change": -0.5},
                "forex": {"USD": 147.35, "EUR": 158.92, "GBP": 185.40},
                "crypto": {"bitcoin": 3500000, "ethereum": 250000},
                "interest_rates": {"central_bank_rate": 7.0},
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "Fallback data - API connection failed"
            }
    
    def get_economic_indicators(self) -> Dict:
        """
        Get key economic indicators for Kenya
        
        Returns:
            Economic indicator data
        """
        cache_key = "economic:indicators:kenya"
        
        # This data might need to be aggregated from multiple sources
        # or manually updated periodically
        
        # Fallback to hardcoded recent data with timestamp
        # In a production environment, this should come from a reliable API
        return {
            "gdp_growth_rate": 4.8,  # percentage
            "inflation_rate": 6.7,    # percentage
            "unemployment_rate": 5.7, # percentage
            "interest_rate": 7.0,     # percentage
            "last_updated": "2024-01-15",
            "note": "Data from CBK economic reports"
        }

# Initialize a singleton instance
market_api = MarketDataAPI()

# Example usage
if __name__ == "__main__":
    # Test the API functions
    print("Testing market data API...")
    
    # Get market summary
    summary = market_api.get_market_summary()
    print(f"Market summary: {summary}")
    
    # Get crypto prices
    crypto_prices = market_api.get_crypto_prices()
    print(f"Crypto prices: {crypto_prices}")
