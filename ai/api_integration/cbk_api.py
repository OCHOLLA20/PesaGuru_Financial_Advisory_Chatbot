import os
import json
import time
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Union, cast
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

import httpx
import redis
from pydantic import BaseSettings, Field
from fastapi import HTTPException, status, Depends
from fastapi.responses import JSONResponse

# Configure logging with more structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger("pesaguru.cbk_api")


class Settings(BaseSettings):
    """Configuration settings for CBK API using pydantic for validation."""
    cbk_api_base_url: str = Field(
        default="https://sandbox.centralbank.go.ke/api/v1",
        description="CBK API base URL"
    )
    cbk_client_id: Optional[str] = Field(
        default=None,
        description="CBK API client ID"
    )
    cbk_client_secret: Optional[str] = Field(
        default=None,
        description="CBK API client secret"
    )
    cbk_token_url: str = Field(
        default="https://sandbox.centralbank.go.ke/oauth/token",
        description="CBK OAuth token URL"
    )
    redis_host: str = Field(
        default="localhost",
        description="Redis host for caching"
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port for caching"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database index"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    api_request_timeout: int = Field(
        default=30,
        description="Timeout for API requests in seconds"
    )
    use_fallback_on_error: bool = Field(
        default=True,
        description="Use fallback implementation on API errors"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()


class CacheExpiry(Enum):
    """Cache expiry times in seconds for different types of data."""
    FOREX = 3600           # 1 hour
    INTEREST_RATES = 21600 # 6 hours
    MONETARY_POLICY = 43200 # 12 hours
    TREASURY = 86400       # 24 hours
    CURRENCIES = 604800    # 1 week
    ECONOMIC = 86400       # 24 hours


# Initialize Redis client for caching with better error handling
redis_client = None
try:
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        decode_responses=True,
        socket_timeout=5,  # Short timeout for Redis operations
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info("Redis cache connected successfully")
except (redis.ConnectionError, redis.RedisError) as e:
    logger.warning(f"Redis cache connection failed: {e}. Caching will be disabled.")
    redis_client = None


class CBKApiError(Exception):
    """Custom exception for CBK API errors with status code and details."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"CBK API Error {status_code}: {detail}")


class CBKApiRateLimitError(CBKApiError):
    """Exception for rate limit errors."""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)


class CBKApiAuthError(CBKApiError):
    """Exception for authentication errors."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)


class CBKApi:
    """
    Enhanced Central Bank of Kenya API integration for PesaGuru.
    Provides access to forex rates, interest rates, and other financial data from CBK.
    """
    
    def __init__(self):
        """Initialize the CBK API client with async HTTP client."""
        self.base_url = settings.cbk_api_base_url
        self.client_id = settings.cbk_client_id
        self.client_secret = settings.cbk_client_secret
        self.token_url = settings.cbk_token_url
        self.access_token = None
        self.token_expires_at = 0
        self.request_timeout = settings.api_request_timeout
        
        # Initialize async HTTP client with connection pooling
        self.http_client = httpx.AsyncClient(
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        
        # Rate limiting parameters
        self.request_count = 0
        self.rate_limit_reset = time.time() + 3600
        self.rate_limit_max = 1000  # Assumed max requests per hour
        
        # Check if credentials are available
        if not self.client_id or not self.client_secret:
            logger.warning("CBK API credentials not found in environment variables")
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with client cleanup."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client session."""
        if self.http_client:
            await self.http_client.aclose()
    
    async def _check_rate_limit(self):
        """
        Check if we're within rate limits.
        Raises CBKApiRateLimitError if limit exceeded.
        """
        current_time = time.time()
        
        # Reset count if we're in a new period
        if current_time > self.rate_limit_reset:
            self.request_count = 0
            self.rate_limit_reset = current_time + 3600
        
        # Check if we're over the limit
        if self.request_count >= self.rate_limit_max:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset)
            reset_in = timedelta(seconds=int(self.rate_limit_reset - current_time))
            
            logger.warning(f"Rate limit exceeded. Resets at {reset_time} (in {reset_in})")
            raise CBKApiRateLimitError(f"Rate limit exceeded. Reset in {reset_in}")
        
        # Increment counter
        self.request_count += 1
    
    async def _get_auth_token(self) -> str:
        """
        Get a valid authentication token for CBK API with async implementation.
        Handles token refresh if expired.
        
        Returns:
            str: Valid access token
        
        Raises:
            CBKApiAuthError: If authentication fails
        """
        # Check if token exists and is not expired
        current_time = time.time()
        if self.access_token and current_time < self.token_expires_at:
            return self.access_token
        
        # Request new token
        try:
            logger.info("Requesting new CBK API auth token")
            response = await self.http_client.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                error_msg = f"Failed to obtain auth token: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise CBKApiAuthError(error_msg)
                
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            # Set expiry time with a buffer (5 min) before actual expiry
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = current_time + expires_in - 300
            
            return self.access_token
            
        except httpx.RequestError as e:
            error_msg = f"Auth token request error: {str(e)}"
            logger.error(error_msg)
            raise CBKApiError(status_code=503, detail=error_msg)
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """
        Generate a cache key for API requests.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            str: Cache key
        """
        param_string = json.dumps(params or {}, sort_keys=True)
        return f"pesaguru:cbk_api:{endpoint}:{param_string}"
    
    async def _make_api_request(
        self, 
        endpoint: str, 
        params: Dict = None, 
        use_cache: bool = True, 
        cache_ttl: int = 3600
    ) -> Dict:
        """
        Make an authenticated request to the CBK API with caching support.
        
        Args:
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            use_cache: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Dict: API response data
            
        Raises:
            CBKApiError: If the API request fails
        """
        await self._check_rate_limit()
        
        # Try cache first if enabled
        cache_key = None
        if use_cache and redis_client:
            cache_key = self._get_cache_key(endpoint, params)
            
            # Try to get from cache
            cached_response = redis_client.get(cache_key)
            if cached_response:
                logger.info(f"Cache hit for: {endpoint}")
                return json.loads(cached_response)
        
        # Make API request with auth token
        url = f"{self.base_url}/{endpoint}"
        token = await self._get_auth_token()
        
        try:
            logger.info(f"Making CBK API request: {endpoint}")
            response = await self.http_client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 401:
                # Token might be expired, get a new one and retry once
                logger.info("Auth token expired, refreshing and retrying")
                self.access_token = None
                token = await self._get_auth_token()
                
                response = await self.http_client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            if response.status_code == 429:
                # Handle rate limiting
                reset_after = response.headers.get("X-RateLimit-Reset", "3600")
                raise CBKApiRateLimitError(f"Rate limit exceeded. Reset after {reset_after} seconds")
            
            if response.status_code != 200:
                error_msg = f"CBK API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise CBKApiError(
                    status_code=response.status_code,
                    detail=error_msg
                )
            
            data = response.json()
            
            # Store in cache if enabled
            if use_cache and redis_client and cache_key:
                try:
                    redis_client.setex(cache_key, cache_ttl, json.dumps(data))
                except redis.RedisError as e:
                    logger.warning(f"Failed to cache response: {e}")
                
            return data
            
        except httpx.RequestError as e:
            error_msg = f"CBK API request error: {str(e)}"
            logger.error(error_msg)
            
            # Use fallback if enabled
            if settings.use_fallback_on_error:
                logger.info(f"Using fallback data for {endpoint}")
                return self._get_fallback_data(endpoint, params)
            
            raise CBKApiError(status_code=503, detail=error_msg)
    
    def _get_fallback_data(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Get fallback data when API is unavailable.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict: Fallback data
        """
        fallback = CBKApiFallback()
        
        # Map endpoint to fallback method
        if endpoint == "forex":
            return fallback.get_mock_forex_rates()
        elif endpoint == "interest-rates":
            return fallback.get_mock_interest_rates()
        elif endpoint == "treasury/t-bills":
            return fallback.get_mock_t_bill_rates()
        elif endpoint == "treasury/t-bonds":
            return fallback.get_mock_t_bond_rates()
        elif endpoint == "monetary-policy":
            return fallback.get_mock_monetary_policy()
        elif endpoint == "currencies":
            return fallback.get_mock_currencies_list()
        elif endpoint == "indicators":
            return fallback.get_mock_economic_indicators()
        elif endpoint == "converter" and params:
            return fallback.get_mock_currency_conversion(
                params.get("from", "USD"),
                params.get("to", "KES"),
                float(params.get("amount", 1))
            )
        
        # Default fallback for unknown endpoints
        return {
            "status": "fallback",
            "message": "This is mock data. Real API connection failed.",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_forex_rates(
        self, 
        currency: Optional[str] = None, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get exchange rates from the CBK.
        
        Args:
            currency: Optional currency code (USD, EUR, GBP, etc.)
            start_date: Optional start date for historical rates (YYYY-MM-DD)
            end_date: Optional end date for historical rates (YYYY-MM-DD)
            
        Returns:
            Dict: Exchange rate data
        """
        params = {}
        if currency:
            params["currency"] = currency
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
            
        # Use shorter cache time (1 hour) for forex rates
        return await self._make_api_request(
            "forex", 
            params, 
            cache_ttl=CacheExpiry.FOREX.value
        )
    
    async def get_interest_rates(self, rate_type: Optional[str] = None) -> Dict:
        """
        Get CBK interest rates.
        
        Args:
            rate_type: Optional rate type (CBR, T-Bill, etc.)
            
        Returns:
            Dict: Interest rate data
        """
        params = {}
        if rate_type:
            params["type"] = rate_type
            
        # Interest rates don't change frequently, cache longer (6 hours)
        return await self._make_api_request(
            "interest-rates", 
            params, 
            cache_ttl=CacheExpiry.INTEREST_RATES.value
        )
    
    async def get_monetary_policy(self) -> Dict:
        """
        Get latest monetary policy information from CBK.
        
        Returns:
            Dict: Monetary policy data
        """
        # Monetary policy data changes infrequently, cache for 12 hours
        return await self._make_api_request(
            "monetary-policy", 
            cache_ttl=CacheExpiry.MONETARY_POLICY.value
        )
    
    async def get_t_bill_rates(self) -> Dict:
        """
        Get latest Treasury Bill rates.
        
        Returns:
            Dict: T-Bill rate data
        """
        # T-Bill rates typically update weekly, cache for 24 hours
        return await self._make_api_request(
            "treasury/t-bills", 
            cache_ttl=CacheExpiry.TREASURY.value
        )
    
    async def get_t_bond_rates(self) -> Dict:
        """
        Get latest Treasury Bond rates.
        
        Returns:
            Dict: T-Bond rate data
        """
        # T-Bond rates update monthly, cache for 24 hours
        return await self._make_api_request(
            "treasury/t-bonds", 
            cache_ttl=CacheExpiry.TREASURY.value
        )

    async def get_currencies_list(self) -> List[Dict]:
        """
        Get list of available currencies from CBK.
        
        Returns:
            List[Dict]: List of currency data
        """
        # Currency list rarely changes, cache for a week
        result = await self._make_api_request(
            "currencies", 
            cache_ttl=CacheExpiry.CURRENCIES.value
        )
        return cast(List[Dict], result)
    
    async def get_economic_indicators(self) -> Dict:
        """
        Get current economic indicators from CBK.
        
        Returns:
            Dict: Economic indicators data
        """
        # Economic indicators typically update monthly, cache for 24 hours
        return await self._make_api_request(
            "indicators", 
            cache_ttl=CacheExpiry.ECONOMIC.value
        )
    
    async def convert_currency(
        self, 
        from_currency: str, 
        to_currency: str, 
        amount: float
    ) -> Dict:
        """
        Convert currency based on latest CBK rates.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            amount: Amount to convert
            
        Returns:
            Dict: Conversion result
        """
        params = {
            "from": from_currency,
            "to": to_currency,
            "amount": amount
        }
        
        # Use short cache time for currency conversion (1 hour)
        return await self._make_api_request(
            "converter", 
            params, 
            cache_ttl=CacheExpiry.FOREX.value
        )


class CBKApiFallback:
    """
    Enhanced fallback implementation with mock data when CBK API is not available.
    Used for testing or when real API access fails.
    """
    
    @staticmethod
    def get_mock_forex_rates() -> Dict[str, Any]:
        """Get mock forex rates data."""
        return {
            "base_currency": "KES",
            "rates": {
                "USD": 147.25,
                "EUR": 160.82,
                "GBP": 186.33,
                "JPY": 0.99,
                "ZAR": 8.12,
                "AED": 40.05,
                "CHF": 167.78,
                "CNY": 22.95,
                "INR": 1.95,
                "UGX": 0.039
            },
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_interest_rates() -> Dict[str, Any]:
        """Get mock interest rates data."""
        return {
            "central_bank_rate": 10.0,
            "interbank_rate": 9.5,
            "t_bill_91_days": 9.85,
            "t_bill_182_days": 10.25,
            "t_bill_364_days": 10.85,
            "mortgage_average_rate": 12.5,
            "lending_average_rate": 13.2,
            "deposit_average_rate": 6.8,
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_t_bill_rates() -> Dict[str, Any]:
        """Get mock T-Bill rates data."""
        return {
            "91_days": {
                "rate": 9.85,
                "previous_rate": 9.75,
                "change": 0.10
            },
            "182_days": {
                "rate": 10.25,
                "previous_rate": 10.15,
                "change": 0.10
            },
            "364_days": {
                "rate": 10.85,
                "previous_rate": 10.75,
                "change": 0.10
            },
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_t_bond_rates() -> Dict[str, Any]:
        """Get mock T-Bond rates data."""
        return {
            "2_year": {
                "rate": 11.25,
                "previous_rate": 11.15,
                "change": 0.10
            },
            "5_year": {
                "rate": 12.45,
                "previous_rate": 12.35,
                "change": 0.10
            },
            "10_year": {
                "rate": 13.75,
                "previous_rate": 13.65,
                "change": 0.10
            },
            "15_year": {
                "rate": 14.05,
                "previous_rate": 13.95,
                "change": 0.10
            },
            "20_year": {
                "rate": 14.35,
                "previous_rate": 14.25,
                "change": 0.10
            },
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_monetary_policy() -> Dict[str, Any]:
        """Get mock monetary policy data."""
        return {
            "central_bank_rate": 10.0,
            "last_mpc_meeting": (datetime.now() - timedelta(days=15)).isoformat(),
            "next_mpc_meeting": (datetime.now() + timedelta(days=45)).isoformat(),
            "policy_statement": "The Monetary Policy Committee (MPC) decided to maintain the Central Bank Rate (CBR) at 10.0 percent. The Committee noted that inflation remains within the target range and the economy is operating close to its potential.",
            "inflation_target": {
                "lower": 2.5,
                "upper": 7.5,
                "current": 5.6
            },
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_currencies_list() -> List[Dict[str, Any]]:
        """Get mock currencies list."""
        return [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "¥"},
            {"code": "ZAR", "name": "South African Rand", "symbol": "R"},
            {"code": "KES", "name": "Kenyan Shilling", "symbol": "KSh"},
            {"code": "UGX", "name": "Ugandan Shilling", "symbol": "USh"},
            {"code": "TZS", "name": "Tanzanian Shilling", "symbol": "TSh"},
            {"code": "RWF", "name": "Rwandan Franc", "symbol": "RF"},
            {"code": "AED", "name": "UAE Dirham", "symbol": "د.إ"}
        ]
    
    @staticmethod
    def get_mock_economic_indicators() -> Dict[str, Any]:
        """Get mock economic indicators data."""
        return {
            "gdp_growth": 5.4,
            "inflation_rate": 5.6,
            "unemployment_rate": 12.7,
            "forex_reserves": {
                "amount": 8.25,
                "unit": "billion USD",
                "months_of_import_cover": 4.5
            },
            "public_debt": {
                "amount": 7.5,
                "unit": "trillion KES",
                "percent_of_gdp": 66.2
            },
            "current_account": {
                "balance": -5.2,
                "unit": "billion USD",
                "percent_of_gdp": -4.8
            },
            "last_updated": datetime.now().isoformat(),
            "_is_mock": True
        }
    
    @staticmethod
    def get_mock_currency_conversion(from_currency: str, to_currency: str, amount: float) -> Dict[str, Any]:
        """
        Get mock currency conversion data.
        
        Args:
            from_currency: Source currency
            to_currency: Target currency
            amount: Amount to convert
            
        Returns:
            Dict: Conversion result
        """
        # Mock rates table (to KES)
        rates_to_kes = {
            "USD": 147.25,
            "EUR": 160.82,
            "GBP": 186.33,
            "JPY": 0.99,
            "ZAR": 8.12,
            "KES": 1.0
        }
        
        # Default rates if currency not in table
        if from_currency not in rates_to_kes:
            rates_to_kes[from_currency] = 100.0
        if to_currency not in rates_to_kes:
            rates_to_kes[to_currency] = 100.0
        
        # Calculate conversion
        kes_amount = amount * rates_to_kes[from_currency]
        target_amount = kes_amount / rates_to_kes[to_currency]
        
        return {
            "from": {
                "currency": from_currency,
                "amount": amount
            },
            "to": {
                "currency": to_currency,
                "amount": round(target_amount, 2)
            },
            "rate": round(rates_to_kes[from_currency] / rates_to_kes[to_currency], 6),
            "timestamp": datetime.now().isoformat(),
            "_is_mock": True
        }


# Create async factory for CBK API client
@lru_cache()
def get_cbk_api() -> CBKApi:
    """Factory function for CBK API client with caching."""
    return CBKApi()


# FastAPI dependency for injecting CBK API client
async def get_cbk_api_client(api: CBKApi = Depends(get_cbk_api)) -> CBKApi:
    """
    Dependency that provides a CBK API client.
    
    Args:
        api: CBK API client from factory
        
    Returns:
        CBKApi: CBK API client
        
    Yields:
        CBKApi: CBK API client for use in route handlers
    """
    try:
        yield api
    finally:
        # No need to close here as the client is cached and reused
        pass


# Exception handler for CBK API errors
def register_exception_handlers(app):
    """Register exception handlers for CBK API errors."""
    
    @app.exception_handler(CBKApiError)
    async def handle_cbk_api_error(request, exc: CBKApiError):
        """Handle CBK API errors with appropriate response."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(CBKApiRateLimitError)
    async def handle_rate_limit_error(request, exc: CBKApiRateLimitError):
        """Handle rate limit errors with appropriate headers."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers={"Retry-After": "3600"}
        )


# Example usage in FastAPI routes
'''
@router.get("/forex-rates")
async def get_forex_rates(
    currency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cbk_api: CBKApi = Depends(get_cbk_api_client)
):
    """Get exchange rates from CBK."""
    try:
        rates = await cbk_api.get_forex_rates(currency, start_date, end_date)
        return rates
    except CBKApiError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
'''

# Export both the real implementation and fallback
__all__ = ['CBKApi', 'CBKApiFallback', 'get_cbk_api', 'get_cbk_api_client', 'register_exception_handlers']
