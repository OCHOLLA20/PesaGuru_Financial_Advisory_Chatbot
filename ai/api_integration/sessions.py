import os
import time
import json
import logging
import hashlib
import requests
import redis
from redis import Redis
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Tuple, List, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from authlib.integrations.requests_client import OAuth2Session
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pesaguru.api.sessions')

# Load environment variables
load_dotenv()

# Redis configuration for caching
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_SESSION_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Encryption key for sensitive data
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    logger.warning("No encryption key found. Generating temporary key. THIS IS NOT SECURE FOR PRODUCTION!")
    ENCRYPTION_KEY = Fernet.generate_key()

# Create encryption handler
cipher_suite = Fernet(ENCRYPTION_KEY)


class APIRateLimiter:
    """Rate limiter for API calls to prevent exceeding API limits"""
    
    def __init__(self, redis_client: Redis, api_name: str, max_calls: int, time_frame: int):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client for tracking call rates
            api_name: Unique name of the API
            max_calls: Maximum number of calls allowed in the time frame
            time_frame: Time frame in seconds for the rate limit
        """
        self.redis = redis_client
        self.api_name = api_name
        self.max_calls = max_calls
        self.time_frame = time_frame
        self.key = f"rate_limit:{api_name}"
    
    def can_make_request(self) -> bool:
        """Check if a request can be made within the rate limits"""
        current_count = self.redis.get(self.key)
        if current_count is None:
            # No previous calls, initialize counter
            self.redis.setex(self.key, self.time_frame, 1)
            return True
        
        current_count = int(current_count)
        if current_count < self.max_calls:
            # Increment the counter
            self.redis.incr(self.key)
            return True
        
        return False
    
    def time_until_reset(self) -> int:
        """Get the time in seconds until the rate limit resets"""
        ttl = self.redis.ttl(self.key)
        return max(0, ttl)
    
    def wait_if_needed(self) -> bool:
        """Wait if rate limit is reached, return True if waited"""
        if not self.can_make_request():
            wait_time = self.time_until_reset()
            logger.warning(f"Rate limit reached for {self.api_name}. Waiting {wait_time} seconds.")
            time.sleep(wait_time + 1)  # Add 1 second buffer
            return True
        return False


class APISession:
    """Base class for API sessions with common functionality"""
    
    def __init__(self, api_name: str, base_url: str, cache_ttl: int = 3600):
        """
        Initialize API session
        
        Args:
            api_name: Unique name of the API
            base_url: Base URL for the API
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.api_name = api_name
        self.base_url = base_url
        self.cache_ttl = cache_ttl
        
        # Create Redis connection
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        
        # Create session with retry strategy
        self.session = self._create_session()
        
        # Create rate limiter (default: 100 calls per minute)
        self.rate_limiter = APIRateLimiter(
            self.redis,
            api_name,
            max_calls=int(os.getenv(f'{api_name.upper()}_RATE_LIMIT', 100)),
            time_frame=int(os.getenv(f'{api_name.upper()}_RATE_WINDOW', 60))
        )
    
    def _create_session(self) -> requests.Session:
        """Create a session with retry strategy"""
        session = requests.Session()
        
        # Configure retries for transient errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate a unique cache key based on the endpoint and parameters"""
        if params is None:
            params = {}
        
        # Create a string representation of parameters and hash it
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()
        
        return f"cache:{self.api_name}:{endpoint}:{param_hash}"
    
    def get_cached_response(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Get a cached response if available"""
        cache_key = self._cache_key(endpoint, params)
        cached_data = self.redis.get(cache_key)
        
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode cached data for {cache_key}")
                # Delete invalid cache entry
                self.redis.delete(cache_key)
        
        return None
    
    def cache_response(self, endpoint: str, params: Dict, response_data: Dict, ttl: int = None) -> None:
        """Cache API response data"""
        if ttl is None:
            ttl = self.cache_ttl
            
        cache_key = self._cache_key(endpoint, params)
        self.redis.setex(cache_key, ttl, json.dumps(response_data))
    
    def clear_cache(self, endpoint: str = None) -> None:
        """Clear cache for the API or specific endpoint"""
        if endpoint:
            pattern = f"cache:{self.api_name}:{endpoint}:*"
        else:
            pattern = f"cache:{self.api_name}:*"
            
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        return cipher_suite.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        return cipher_suite.decrypt(encrypted_data).decode()
    
    def close(self) -> None:
        """Close the session"""
        self.session.close()


class ApiKeySession(APISession):
    """Session for API key based authentication"""
    
    def __init__(
        self, 
        api_name: str, 
        base_url: str, 
        api_key: str, 
        api_key_header: str = "X-API-Key",
        cache_ttl: int = 3600
    ):
        """
        Initialize API key session
        
        Args:
            api_name: Unique name of the API
            base_url: Base URL for the API
            api_key: API key for authentication
            api_key_header: Header name for the API key (default: X-API-Key)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        super().__init__(api_name, base_url, cache_ttl)
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.headers = {api_key_header: api_key}
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Dict = None, 
        data: Dict = None, 
        headers: Dict = None,
        use_cache: bool = True,
        cache_ttl: int = None
    ) -> Dict:
        """
        Make an API request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Additional headers
            use_cache: Whether to use cache for GET requests
            cache_ttl: Custom cache TTL (if None, uses instance default)
            
        Returns:
            API response as dictionary
        """
        if params is None:
            params = {}
            
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Check cache for GET requests
        if method.upper() == "GET" and use_cache:
            cached_response = self.get_cached_response(endpoint, params)
            if cached_response:
                logger.debug(f"Cache hit for {url}")
                return cached_response
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Prepare headers
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Cache successful GET responses
            if method.upper() == "GET" and use_cache:
                self.cache_response(endpoint, params, response_data, cache_ttl)
                
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise


class OAuth2ApiSession(APISession):
    """Session for OAuth2 based authentication"""
    
    def __init__(
        self, 
        api_name: str, 
        base_url: str, 
        client_id: str, 
        client_secret: str, 
        token_url: str,
        authorize_url: Optional[str] = None,
        scope: Optional[str] = None,
        cache_ttl: int = 3600,
        token_refresh_margin: int = 300  # 5 minutes
    ):
        """
        Initialize OAuth2 API session
        
        Args:
            api_name: Unique name of the API
            base_url: Base URL for the API
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: URL for obtaining tokens
            authorize_url: URL for authorization (optional for client credentials)
            scope: OAuth scopes (optional)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
            token_refresh_margin: Margin in seconds before token expiry to refresh (default: 5 minutes)
        """
        super().__init__(api_name, base_url, cache_ttl)
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.authorize_url = authorize_url
        self.scope = scope
        self.token_refresh_margin = token_refresh_margin
        
        # Store token info in Redis
        self.token_key = f"oauth_token:{api_name}"
        
        # Create OAuth session
        self.oauth = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope
        )
        
        # Initialize token
        self._ensure_token()
    
    def _ensure_token(self) -> None:
        """Ensure a valid token is available, fetching a new one if needed"""
        token_data = self.redis.get(self.token_key)
        
        if not token_data:
            self._fetch_new_token()
            return
            
        try:
            token = json.loads(token_data)
            # Check if token needs refresh
            expires_at = token.get('expires_at', 0)
            if time.time() + self.token_refresh_margin >= expires_at:
                self._refresh_token(token)
            
            # Update OAuth session with the token
            self.oauth.token = token
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing token data: {e}")
            self._fetch_new_token()
    
    def _fetch_new_token(self) -> None:
        """Fetch a new token using client credentials flow"""
        logger.info(f"Fetching new token for {self.api_name}")
        
        try:
            token = self.oauth.fetch_token(
                url=self.token_url,
                grant_type="client_credentials",
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            # Store token in Redis
            self._save_token(token)
            
        except Exception as e:
            logger.error(f"Failed to fetch token: {e}")
            raise
    
    def _refresh_token(self, token: Dict) -> None:
        """Refresh an existing token"""
        logger.info(f"Refreshing token for {self.api_name}")
        
        try:
            if 'refresh_token' in token:
                new_token = self.oauth.refresh_token(
                    url=self.token_url,
                    refresh_token=token['refresh_token']
                )
                self._save_token(new_token)
            else:
                # No refresh token, get a new token
                self._fetch_new_token()
                
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            # Try to get a new token instead
            self._fetch_new_token()
    
    def _save_token(self, token: Dict) -> None:
        """Save token data to Redis with expiration"""
        # Add expiration time if not present
        if 'expires_at' not in token and 'expires_in' in token:
            token['expires_at'] = time.time() + token['expires_in']
            
        # Calculate TTL for Redis
        ttl = int(token.get('expires_at', time.time() + 3600) - time.time())
        
        # Store in Redis
        self.redis.setex(
            self.token_key,
            ttl,
            json.dumps(token)
        )
    
    def request(
        self, 
        method: str, 
        endpoint: str, 
        params: Dict = None, 
        data: Dict = None, 
        headers: Dict = None,
        use_cache: bool = True,
        cache_ttl: int = None
    ) -> Dict:
        """
        Make an API request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Additional headers
            use_cache: Whether to use cache for GET requests
            cache_ttl: Custom cache TTL (if None, uses instance default)
            
        Returns:
            API response as dictionary
        """
        if params is None:
            params = {}
            
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Check cache for GET requests
        if method.upper() == "GET" and use_cache:
            cached_response = self.get_cached_response(endpoint, params)
            if cached_response:
                logger.debug(f"Cache hit for {url}")
                return cached_response
        
        # Ensure we have a valid token
        self._ensure_token()
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            # Make OAuth request
            response = self.oauth.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Cache successful GET responses
            if method.upper() == "GET" and use_cache:
                self.cache_response(endpoint, params, response_data, cache_ttl)
                
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            # Handle token expiration
            if hasattr(e, 'response') and e.response.status_code == 401:
                logger.info("Token may have expired. Fetching new token.")
                self._fetch_new_token()
                # Retry the request once
                return self.request(method, endpoint, params, data, headers, use_cache, cache_ttl)
            raise


class SessionManager:
    """Manager for API sessions across the application"""
    
    def __init__(self):
        """Initialize session manager"""
        self.sessions = {}
    
    def get_or_create_api_key_session(
        self, 
        api_name: str, 
        base_url: str, 
        api_key: str = None, 
        api_key_header: str = "X-API-Key",
        cache_ttl: int = 3600
    ) -> ApiKeySession:
        """
        Get or create an API key session
        
        Args:
            api_name: Unique name of the API
            base_url: Base URL for the API
            api_key: API key for authentication (if None, fetched from env var)
            api_key_header: Header name for the API key
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            ApiKeySession instance
        """
        session_key = f"apikey:{api_name}"
        
        if session_key in self.sessions:
            return self.sessions[session_key]
        
        # Get API key from environment if not provided
        if api_key is None:
            env_var = f"{api_name.upper()}_API_KEY"
            api_key = os.getenv(env_var)
            if not api_key:
                raise ValueError(f"No API key provided and {env_var} not found in environment")
        
        # Create new session
        session = ApiKeySession(
            api_name=api_name,
            base_url=base_url,
            api_key=api_key,
            api_key_header=api_key_header,
            cache_ttl=cache_ttl
        )
        
        self.sessions[session_key] = session
        return session
    
    def get_or_create_oauth2_session(
        self, 
        api_name: str, 
        base_url: str, 
        client_id: str = None, 
        client_secret: str = None, 
        token_url: str = None,
        authorize_url: str = None,
        scope: str = None,
        cache_ttl: int = 3600
    ) -> OAuth2ApiSession:
        """
        Get or create an OAuth2 session
        
        Args:
            api_name: Unique name of the API
            base_url: Base URL for the API
            client_id: OAuth2 client ID (if None, fetched from env var)
            client_secret: OAuth2 client secret (if None, fetched from env var)
            token_url: URL for obtaining tokens (if None, fetched from env var)
            authorize_url: URL for authorization (optional)
            scope: OAuth scopes (optional)
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            OAuth2ApiSession instance
        """
        session_key = f"oauth2:{api_name}"
        
        if session_key in self.sessions:
            return self.sessions[session_key]
        
        # Get credentials from environment if not provided
        if client_id is None:
            client_id = os.getenv(f"{api_name.upper()}_CLIENT_ID")
            if not client_id:
                raise ValueError(f"{api_name.upper()}_CLIENT_ID not found in environment")
                
        if client_secret is None:
            client_secret = os.getenv(f"{api_name.upper()}_CLIENT_SECRET")
            if not client_secret:
                raise ValueError(f"{api_name.upper()}_CLIENT_SECRET not found in environment")
                
        if token_url is None:
            token_url = os.getenv(f"{api_name.upper()}_TOKEN_URL")
            if not token_url:
                raise ValueError(f"{api_name.upper()}_TOKEN_URL not found in environment")
        
        if authorize_url is None:
            authorize_url = os.getenv(f"{api_name.upper()}_AUTHORIZE_URL")
            
        if scope is None:
            scope = os.getenv(f"{api_name.upper()}_SCOPE")
        
        # Create new session
        session = OAuth2ApiSession(
            api_name=api_name,
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            token_url=token_url,
            authorize_url=authorize_url,
            scope=scope,
            cache_ttl=cache_ttl
        )
        
        self.sessions[session_key] = session
        return session
    
    def get_session(self, api_name: str, auth_type: str = "apikey") -> Union[ApiKeySession, OAuth2ApiSession]:
        """
        Get an existing session by name and auth type
        
        Args:
            api_name: Unique name of the API
            auth_type: Authentication type ('apikey' or 'oauth2')
            
        Returns:
            API session instance
        """
        session_key = f"{auth_type}:{api_name}"
        
        if session_key not in self.sessions:
            raise KeyError(f"No session found for {api_name} with auth type {auth_type}")
            
        return self.sessions[session_key]
    
    def clear_cache(self, api_name: str = None) -> None:
        """
        Clear cache for all sessions or a specific API
        
        Args:
            api_name: If provided, clear cache only for this API
        """
        if api_name:
            for session_key, session in self.sessions.items():
                if session_key.endswith(f":{api_name}"):
                    session.clear_cache()
        else:
            for session in self.sessions.values():
                session.clear_cache()
    
    def close_all(self) -> None:
        """Close all sessions"""
        for session in self.sessions.values():
            session.close()
        self.sessions = {}


# Create a global instance of SessionManager
session_manager = SessionManager()


# Helper functions to quickly get sessions for specific APIs
def get_nse_api_session() -> ApiKeySession:
    """Get NSE (Nairobi Stock Exchange) API session"""
    return session_manager.get_or_create_api_key_session(
        api_name="nse",
        base_url=os.getenv("NSE_API_URL", "https://nairobi-stock-exchange-nse.p.rapidapi.com"),
        api_key_header="X-RapidAPI-Key"
    )

def get_cbk_api_session() -> OAuth2ApiSession:
    """Get CBK (Central Bank of Kenya) API session"""
    return session_manager.get_or_create_oauth2_session(
        api_name="cbk",
        base_url=os.getenv("CBK_API_URL", "https://sandbox.safaricom.co.ke"),
    )

def get_mpesa_api_session() -> OAuth2ApiSession:
    """Get M-Pesa API session"""
    return session_manager.get_or_create_oauth2_session(
        api_name="mpesa",
        base_url=os.getenv("MPESA_API_URL", "https://sandbox.safaricom.co.ke"),
        token_url=os.getenv("MPESA_TOKEN_URL", "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials")
    )

def get_crypto_api_session() -> ApiKeySession:
    """Get cryptocurrency API session"""
    return session_manager.get_or_create_api_key_session(
        api_name="crypto",
        base_url=os.getenv("CRYPTO_API_URL", "https://coingecko.p.rapidapi.com"),
        api_key_header="X-RapidAPI-Key"
    )

def get_forex_api_session() -> ApiKeySession:
    """Get forex exchange rate API session"""
    return session_manager.get_or_create_api_key_session(
        api_name="forex",
        base_url=os.getenv("FOREX_API_URL", "https://exchange-rates7.p.rapidapi.com"),
        api_key_header="X-RapidAPI-Key"
    )

def get_news_api_session() -> ApiKeySession:
    """Get financial news API session"""
    return session_manager.get_or_create_api_key_session(
        api_name="news",
        base_url=os.getenv("NEWS_API_URL", "https://news-api14.p.rapidapi.com"),
        api_key_header="X-RapidAPI-Key"
    )


# Example usage
if __name__ == "__main__":
    # Example of using NSE API
    try:
        nse_session = get_nse_api_session()
        stock_data = nse_session.request(
            method="GET",
            endpoint="/stocks/Safaricom"
        )
        print(f"Safaricom stock data: {json.dumps(stock_data, indent=2)}")
    except Exception as e:
        print(f"Error fetching NSE data: {e}")
        
    # Clean up
    session_manager.close_all()
