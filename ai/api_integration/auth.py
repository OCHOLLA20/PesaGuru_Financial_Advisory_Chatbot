import os
import json
import time
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIAuthManager:
    """Manages authentication for various financial APIs."""
    
    def __init__(self, credentials_file: Optional[str] = None):
        """
        Initialize the API Authentication Manager.
        
        Args:
            credentials_file: Path to JSON file containing API credentials.
                             If None, credentials are loaded from environment variables.
        """
        self.tokens = {}  # Store active tokens
        self.credentials = {}  # Store API credentials
        
        # Load credentials from file or environment variables
        if credentials_file and os.path.exists(credentials_file):
            self._load_credentials_from_file(credentials_file)
        else:
            self._load_credentials_from_env()
    
    def _load_credentials_from_file(self, file_path: str) -> None:
        """
        Load API credentials from a JSON file.
        
        Args:
            file_path: Path to the JSON credentials file
        """
        try:
            with open(file_path, 'r') as f:
                self.credentials = json.load(f)
            logger.info(f"Loaded API credentials from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load credentials from file: {e}")
            # Fall back to environment variables
            self._load_credentials_from_env()
    
    def _load_credentials_from_env(self) -> None:
        """Load API credentials from environment variables."""
        # NSE API credentials
        self.credentials['nse'] = {
            'api_key': os.environ.get('NSE_API_KEY', ''),
            'api_secret': os.environ.get('NSE_API_SECRET', ''),
            'base_url': os.environ.get('NSE_API_URL', 'https://nairobi-stock-exchange-nse.p.rapidapi.com')
        }
        
        # CBK API credentials
        self.credentials['cbk'] = {
            'api_key': os.environ.get('CBK_API_KEY', ''),
            'api_secret': os.environ.get('CBK_API_SECRET', ''),
            'base_url': os.environ.get('CBK_API_URL', 'https://cbk-bonds.p.rapidapi.com')
        }
        
        # M-Pesa API credentials
        self.credentials['mpesa'] = {
            'consumer_key': os.environ.get('MPESA_CONSUMER_KEY', ''),
            'consumer_secret': os.environ.get('MPESA_CONSUMER_SECRET', ''),
            'base_url': os.environ.get('MPESA_API_URL', 'https://sandbox.safaricom.co.ke'),
            'pass_key': os.environ.get('MPESA_PASS_KEY', ''),
            'business_short_code': os.environ.get('MPESA_BUSINESS_SHORT_CODE', '')
        }
        
        # CoinGecko API credentials
        self.credentials['coingecko'] = {
            'api_key': os.environ.get('COINGECKO_API_KEY', ''),
            'base_url': os.environ.get('COINGECKO_API_URL', 'https://coingecko.p.rapidapi.com')
        }
        
        # Alpha Vantage API credentials
        self.credentials['alphavantage'] = {
            'api_key': os.environ.get('ALPHAVANTAGE_API_KEY', '08HAWE6C99AGWNEZ'),
            'base_url': os.environ.get('ALPHAVANTAGE_API_URL', 'https://www.alphavantage.co/query')
        }
        
        # RapidAPI credentials (used by multiple services)
        self.credentials['rapidapi'] = {
            'api_key': os.environ.get('RAPIDAPI_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581'),
            'host': os.environ.get('RAPIDAPI_HOST', '')
        }
        
        # News API credentials
        self.credentials['newsapi'] = {
            'api_key': os.environ.get('NEWS_API_KEY', ''),
            'base_url': os.environ.get('NEWS_API_URL', 'https://news-api14.p.rapidapi.com')
        }
        
        # Open Exchange Rates API credentials
        self.credentials['exchangerates'] = {
            'api_key': os.environ.get('EXCHANGE_RATES_API_KEY', ''),
            'base_url': os.environ.get('EXCHANGE_RATES_API_URL', 'https://exchange-rates7.p.rapidapi.com')
        }
        
        # Yahoo Finance API credentials
        self.credentials['yahoofinance'] = {
            'api_key': os.environ.get('YAHOO_FINANCE_API_KEY', ''),
            'base_url': os.environ.get('YAHOO_FINANCE_API_URL', 'https://yahoo-finance166.p.rapidapi.com')
        }
        
        logger.info("Loaded API credentials from environment variables")
    
    def get_auth_headers(self, api_name: str) -> Dict[str, str]:
        """
        Get authentication headers for the specified API.
        
        Args:
            api_name: Name of the API (e.g., 'nse', 'cbk', 'mpesa')
            
        Returns:
            Dictionary containing authentication headers
        """
        # For APIs that use OAuth tokens, check if we have a valid token
        if api_name in ['mpesa', 'cbk'] and api_name in self.tokens:
            token_data = self.tokens[api_name]
            # Check if token is still valid
            if datetime.now() < token_data['expiry']:
                return {'Authorization': f"Bearer {token_data['access_token']}"}
            
            # Token expired, need to refresh
            logger.info(f"Token for {api_name} expired, refreshing...")
        
        # Get fresh authentication headers
        if api_name == 'nse':
            return self._get_nse_headers()
        elif api_name == 'cbk':
            return self._get_cbk_headers()
        elif api_name == 'mpesa':
            return self._get_mpesa_headers()
        elif api_name == 'coingecko':
            return self._get_coingecko_headers()
        elif api_name == 'alphavantage':
            return self._get_alphavantage_headers()
        elif api_name == 'newsapi':
            return self._get_newsapi_headers()
        elif api_name == 'exchangerates':
            return self._get_exchangerates_headers()
        elif api_name == 'yahoofinance':
            return self._get_yahoofinance_headers()
        else:
            logger.warning(f"Unknown API: {api_name}, returning empty headers")
            return {}
    
    def _get_nse_headers(self) -> Dict[str, str]:
        """Get authentication headers for NSE API."""
        return {
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'nairobi-stock-exchange-nse.p.rapidapi.com'
        }
    
    def _get_cbk_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for CBK API.
        
        This method obtains a new OAuth token if needed.
        """
        # If we don't have a valid token, get a new one
        if 'cbk' not in self.tokens or datetime.now() >= self.tokens['cbk']['expiry']:
            token_response = self._fetch_cbk_token()
            if token_response:
                self.tokens['cbk'] = token_response
            else:
                logger.error("Failed to obtain CBK token")
                return {}
        
        return {
            'Authorization': f"Bearer {self.tokens['cbk']['access_token']}",
            'Content-Type': 'application/json',
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'cbk-bonds.p.rapidapi.com'
        }
    
    def _fetch_cbk_token(self) -> Optional[Dict[str, Any]]:
        """
        Fetch a new OAuth token for CBK API.
        
        Returns:
            Dictionary containing token information or None if failed
        """
        try:
            url = f"{self.credentials['cbk']['base_url']}/service/token/"
            headers = {
                'Content-Type': 'application/json',
                'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
                'x-rapidapi-host': 'cbk-bonds.p.rapidapi.com'
            }
            
            response = requests.post(url, headers=headers, json={})
            if response.status_code == 200:
                token_data = response.json()
                # Set token expiry (typically 1 hour, but we'll use the provided expiry if available)
                expiry_seconds = token_data.get('expires_in', 3600)
                expiry = datetime.now() + timedelta(seconds=expiry_seconds)
                return {
                    'access_token': token_data.get('access_token', ''),
                    'expiry': expiry
                }
            else:
                logger.error(f"CBK token request failed: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching CBK token: {e}")
            return None
    
    def _get_mpesa_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for M-Pesa API.
        
        This method obtains a new OAuth token if needed.
        """
        # If we don't have a valid token, get a new one
        if 'mpesa' not in self.tokens or datetime.now() >= self.tokens['mpesa']['expiry']:
            token_response = self._fetch_mpesa_token()
            if token_response:
                self.tokens['mpesa'] = token_response
            else:
                logger.error("Failed to obtain M-Pesa token")
                return {}
        
        return {
            'Authorization': f"Bearer {self.tokens['mpesa']['access_token']}",
            'Content-Type': 'application/json'
        }
    
    def _fetch_mpesa_token(self) -> Optional[Dict[str, Any]]:
        """
        Fetch a new OAuth token for M-Pesa API.
        
        Returns:
            Dictionary containing token information or None if failed
        """
        try:
            consumer_key = self.credentials['mpesa']['consumer_key']
            consumer_secret = self.credentials['mpesa']['consumer_secret']
            url = f"{self.credentials['mpesa']['base_url']}/oauth/v1/generate?grant_type=client_credentials"
            
            import base64
            auth_string = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
            headers = {
                'Authorization': f"Basic {auth_string}",
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                token_data = response.json()
                # Set token expiry (typically 1 hour)
                expiry = datetime.now() + timedelta(seconds=3599)
                return {
                    'access_token': token_data.get('access_token', ''),
                    'expiry': expiry
                }
            else:
                logger.error(f"M-Pesa token request failed: {response.status_code} {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error fetching M-Pesa token: {e}")
            return None
    
    def _get_coingecko_headers(self) -> Dict[str, str]:
        """Get authentication headers for CoinGecko API."""
        return {
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'coingecko.p.rapidapi.com'
        }
    
    def _get_alphavantage_headers(self) -> Dict[str, str]:
        """Get authentication headers for Alpha Vantage API."""
        # Alpha Vantage uses API key as a query parameter, not in headers
        return {}
    
    def get_alphavantage_params(self) -> Dict[str, str]:
        """Get request parameters for Alpha Vantage API."""
        return {
            'apikey': self.credentials.get('alphavantage', {}).get('api_key', '')
        }
    
    def _get_newsapi_headers(self) -> Dict[str, str]:
        """Get authentication headers for News API."""
        return {
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'news-api14.p.rapidapi.com'
        }
    
    def _get_exchangerates_headers(self) -> Dict[str, str]:
        """Get authentication headers for Exchange Rates API."""
        return {
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'exchange-rates7.p.rapidapi.com'
        }
    
    def _get_yahoofinance_headers(self) -> Dict[str, str]:
        """Get authentication headers for Yahoo Finance API."""
        return {
            'x-rapidapi-key': self.credentials.get('rapidapi', {}).get('api_key', ''),
            'x-rapidapi-host': 'yahoo-finance166.p.rapidapi.com'
        }
    
    def generate_mpesa_password(self, timestamp: str) -> str:
        """
        Generate M-Pesa API password for transaction authorization.
        
        Args:
            timestamp: Current timestamp in the format YYYYMMDDHHmmss
            
        Returns:
            Base64 encoded password string
        """
        import base64
        business_short_code = self.credentials['mpesa']['business_short_code']
        pass_key = self.credentials['mpesa']['pass_key']
        
        password_str = f"{business_short_code}{pass_key}{timestamp}"
        return base64.b64encode(password_str.encode()).decode()


class TokenManager:
    """Manages API tokens with automatic refresh."""
    
    def __init__(self, auth_manager: APIAuthManager):
        """
        Initialize the Token Manager.
        
        Args:
            auth_manager: The API Authentication Manager instance
        """
        self.auth_manager = auth_manager
        self.token_refresh_callbacks = {
            'mpesa': self.auth_manager._fetch_mpesa_token,
            'cbk': self.auth_manager._fetch_cbk_token,
            # Add more APIs as needed
        }
    
    def get_token(self, api_name: str) -> Tuple[bool, Optional[str]]:
        """
        Get a valid token for the specified API.
        
        Args:
            api_name: Name of the API (e.g., 'mpesa', 'cbk')
            
        Returns:
            Tuple of (success, token_string)
        """
        # Check if token exists and is valid
        if api_name in self.auth_manager.tokens:
            token_data = self.auth_manager.tokens[api_name]
            # Check if token is still valid
            if datetime.now() < token_data['expiry']:
                return True, token_data['access_token']
        
        # Token doesn't exist or is expired, try to refresh
        if api_name in self.token_refresh_callbacks:
            token_data = self.token_refresh_callbacks[api_name]()
            if token_data:
                self.auth_manager.tokens[api_name] = token_data
                return True, token_data['access_token']
        
        # Failed to get or refresh token
        return False, None


# Example usage
if __name__ == "__main__":
    # Initialize the auth manager
    auth_manager = APIAuthManager()
    
    # Get headers for NSE API
    nse_headers = auth_manager.get_auth_headers('nse')
    print("NSE Headers:", nse_headers)
    
    # Initialize the token manager
    token_manager = TokenManager(auth_manager)
    
    # Get M-Pesa token
    success, mpesa_token = token_manager.get_token('mpesa')
    if success:
        print("M-Pesa token obtained successfully!")
    else:
        print("Failed to obtain M-Pesa token.")
