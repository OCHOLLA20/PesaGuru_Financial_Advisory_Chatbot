import os
import json
import time
import requests
import logging
import redis
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Union, Optional, Tuple

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '08HAWE6C99AGWNEZ')  # Default from project docs
COINMARKETCAP_API_KEY = os.getenv('COINMARKETCAP_API_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')  # Default from project docs
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

# Redis configuration for caching
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Cache expiration times (in seconds)
CACHE_EXPIRE_TIME = {
    'price': 60,              # 1 minute for current price
    'price_history': 3600,    # 1 hour for historical prices
    'market_data': 300,       # 5 minutes for market data
    'sentiment': 1800         # 30 minutes for sentiment analysis
}

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()  # Test connection
    logger.info("Redis connection established successfully")
except redis.ConnectionError:
    logger.warning("Redis connection failed - Caching disabled")
    redis_client = None

class CryptoAPI:
    """
    Main class for cryptocurrency data integration in PesaGuru.
    
    This class provides methods to fetch, process, and analyze cryptocurrency
    market data from various sources, with built-in caching and error handling.
    """
    
    def __init__(self):
        """Initialize the CryptoAPI class with default configurations."""
        self.base_urls = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1',
            'binance': 'https://api.binance.com/api/v3'
        }
        
        # Default API source priority (failover order)
        self.api_priority = ['coingecko', 'coinmarketcap', 'binance']
        
        # Common cryptocurrency symbols and their IDs in various APIs
        self.crypto_mapping = {
            'BTC': {
                'coingecko': 'bitcoin',
                'coinmarketcap': '1',
                'binance': 'BTCUSDT'
            },
            'ETH': {
                'coingecko': 'ethereum',
                'coinmarketcap': '1027',
                'binance': 'ETHUSDT'
            },
            'SOL': {
                'coingecko': 'solana',
                'coinmarketcap': '5426',
                'binance': 'SOLUSDT'
            },
            'XRP': {
                'coingecko': 'ripple',
                'coinmarketcap': '52',
                'binance': 'XRPUSDT'
            },
            'USDT': {
                'coingecko': 'tether',
                'coinmarketcap': '825',
                'binance': 'USDTUSDC'
            }
        }
        
    def get_current_price(self, symbol: str, currency: str = 'usd') -> Dict:
        """
        Get current price and basic market data for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            currency: Currency to convert to (default: 'usd')
            
        Returns:
            Dictionary containing current price and market data
        """
        symbol = symbol.upper()
        cache_key = f"crypto:price:{symbol}:{currency}"
        
        # Try to get from cache first
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Retrieved {symbol} price from cache")
                return json.loads(cached_data)
        
        # Try APIs in priority order
        for api in self.api_priority:
            try:
                if api == 'coingecko':
                    data = self._get_price_coingecko(symbol, currency)
                elif api == 'coinmarketcap':
                    data = self._get_price_coinmarketcap(symbol, currency)
                elif api == 'binance':
                    data = self._get_price_binance(symbol, currency)
                
                # Cache the result
                if redis_client and data:
                    redis_client.setex(
                        cache_key,
                        CACHE_EXPIRE_TIME['price'],
                        json.dumps(data)
                    )
                return data
            
            except Exception as e:
                logger.warning(f"Error getting {symbol} price from {api}: {str(e)}")
                continue
        
        # If all APIs fail
        logger.error(f"Failed to get price for {symbol} from all APIs")
        return {
            'symbol': symbol,
            'price': None,
            'error': 'Data unavailable',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_price_coingecko(self, symbol: str, currency: str) -> Dict:
        """Get cryptocurrency price from CoinGecko API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        coin_id = self.crypto_mapping[symbol]['coingecko']
        url = f"{self.base_urls['coingecko']}/coins/{coin_id}"
        
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-pro-api-key'] = COINGECKO_API_KEY
            
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant data
        price = data['market_data']['current_price'][currency]
        market_cap = data['market_data']['market_cap'][currency]
        price_change_24h = data['market_data']['price_change_percentage_24h']
        volume_24h = data['market_data']['total_volume'][currency]
        
        return {
            'symbol': symbol,
            'name': data['name'],
            'price': price,
            'price_change_24h': price_change_24h,
            'market_cap': market_cap,
            'volume_24h': volume_24h,
            'currency': currency,
            'source': 'coingecko',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_price_coinmarketcap(self, symbol: str, currency: str) -> Dict:
        """Get cryptocurrency price from CoinMarketCap API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        coin_id = self.crypto_mapping[symbol]['coinmarketcap']
        url = f"{self.base_urls['coinmarketcap']}/cryptocurrency/quotes/latest"
        
        headers = {
            'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY
        }
        
        params = {
            'id': coin_id,
            'convert': currency.upper()
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant data
        crypto_data = data['data'][coin_id]
        currency_upper = currency.upper()
        
        return {
            'symbol': symbol,
            'name': crypto_data['name'],
            'price': crypto_data['quote'][currency_upper]['price'],
            'price_change_24h': crypto_data['quote'][currency_upper]['percent_change_24h'],
            'market_cap': crypto_data['quote'][currency_upper]['market_cap'],
            'volume_24h': crypto_data['quote'][currency_upper]['volume_24h'],
            'currency': currency,
            'source': 'coinmarketcap',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_price_binance(self, symbol: str, currency: str) -> Dict:
        """Get cryptocurrency price from Binance API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        symbol_pair = self.crypto_mapping[symbol]['binance']
        url = f"{self.base_urls['binance']}/ticker/24hr"
        
        params = {
            'symbol': symbol_pair
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Binance doesn't provide all the data that other APIs do
        # So we'll calculate what we can
        price = float(data['lastPrice'])
        volume_24h = float(data['volume']) * price
        price_change_24h = float(data['priceChangePercent'])
        
        return {
            'symbol': symbol,
            'name': symbol,  # Binance doesn't provide full names
            'price': price,
            'price_change_24h': price_change_24h,
            'volume_24h': volume_24h,
            'currency': currency,
            'source': 'binance',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_price_history(self, symbol: str, days: int = 7, currency: str = 'usd') -> List[Dict]:
        """
        Get historical price data for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            days: Number of days of historical data (default: 7)
            currency: Currency to convert to (default: 'usd')
            
        Returns:
            List of dictionaries containing historical price data
        """
        symbol = symbol.upper()
        cache_key = f"crypto:history:{symbol}:{currency}:{days}"
        
        # Try to get from cache first
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Retrieved {symbol} price history from cache")
                return json.loads(cached_data)
        
        # Try APIs in priority order
        for api in self.api_priority:
            try:
                if api == 'coingecko':
                    data = self._get_history_coingecko(symbol, days, currency)
                elif api == 'coinmarketcap':
                    data = self._get_history_coinmarketcap(symbol, days, currency)
                elif api == 'binance':
                    data = self._get_history_binance(symbol, days, currency)
                
                # Cache the result
                if redis_client and data:
                    redis_client.setex(
                        cache_key,
                        CACHE_EXPIRE_TIME['price_history'],
                        json.dumps(data)
                    )
                return data
            
            except Exception as e:
                logger.warning(f"Error getting {symbol} history from {api}: {str(e)}")
                continue
        
        # If all APIs fail
        logger.error(f"Failed to get price history for {symbol} from all APIs")
        return []
    
    def _get_history_coingecko(self, symbol: str, days: int, currency: str) -> List[Dict]:
        """Get cryptocurrency price history from CoinGecko API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        coin_id = self.crypto_mapping[symbol]['coingecko']
        url = f"{self.base_urls['coingecko']}/coins/{coin_id}/market_chart"
        
        params = {
            'vs_currency': currency,
            'days': days
        }
        
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-pro-api-key'] = COINGECKO_API_KEY
            
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format the data
        prices = data['prices']
        history = []
        
        for timestamp_ms, price in prices:
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
            history.append({
                'symbol': symbol,
                'price': price,
                'currency': currency,
                'timestamp': timestamp
            })
        
        return history
    
    def _get_history_coinmarketcap(self, symbol: str, days: int, currency: str) -> List[Dict]:
        """Get cryptocurrency price history from CoinMarketCap API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        coin_id = self.crypto_mapping[symbol]['coinmarketcap']
        # Calculate start and end dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Format dates as required by CoinMarketCap
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        url = f"{self.base_urls['coinmarketcap']}/cryptocurrency/quotes/historical"
        
        headers = {
            'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY
        }
        
        params = {
            'id': coin_id,
            'time_start': start_str,
            'time_end': end_str,
            'convert': currency.upper(),
            'interval': '1d'  # Daily intervals
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format the data
        history = []
        currency_upper = currency.upper()
        
        for quote in data['data']['quotes']:
            history.append({
                'symbol': symbol,
                'price': quote['quote'][currency_upper]['price'],
                'currency': currency,
                'timestamp': quote['timestamp']
            })
        
        return history
    
    def _get_history_binance(self, symbol: str, days: int, currency: str) -> List[Dict]:
        """Get cryptocurrency price history from Binance API."""
        if symbol not in self.crypto_mapping:
            raise ValueError(f"Unsupported cryptocurrency: {symbol}")
        
        symbol_pair = self.crypto_mapping[symbol]['binance']
        url = f"{self.base_urls['binance']}/klines"
        
        # Calculate start and end times in milliseconds
        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        params = {
            'symbol': symbol_pair,
            'interval': '1d',  # Daily intervals
            'startTime': start_time,
            'endTime': end_time
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format the data
        history = []
        
        for item in data:
            timestamp = datetime.fromtimestamp(item[0] / 1000).isoformat()
            close_price = float(item[4])  # Close price
            
            history.append({
                'symbol': symbol,
                'price': close_price,
                'currency': currency,
                'timestamp': timestamp
            })
        
        return history
    
    def get_market_overview(self, currency: str = 'usd', limit: int = 10) -> Dict:
        """
        Get an overview of the cryptocurrency market.
        
        Args:
            currency: Currency to convert to (default: 'usd')
            limit: Number of top cryptocurrencies to include (default: 10)
            
        Returns:
            Dictionary containing market overview data
        """
        cache_key = f"crypto:market:overview:{currency}:{limit}"
        
        # Try to get from cache first
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Retrieved market overview from cache")
                return json.loads(cached_data)
        
        # Try APIs in priority order
        for api in self.api_priority:
            try:
                if api == 'coingecko':
                    data = self._get_market_overview_coingecko(currency, limit)
                elif api == 'coinmarketcap':
                    data = self._get_market_overview_coinmarketcap(currency, limit)
                else:
                    continue  # Binance doesn't provide this kind of overview
                
                # Cache the result
                if redis_client and data:
                    redis_client.setex(
                        cache_key,
                        CACHE_EXPIRE_TIME['market_data'],
                        json.dumps(data)
                    )
                return data
            
            except Exception as e:
                logger.warning(f"Error getting market overview from {api}: {str(e)}")
                continue
        
        # If all APIs fail
        logger.error("Failed to get market overview from all APIs")
        return {
            'error': 'Data unavailable',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_market_overview_coingecko(self, currency: str, limit: int) -> Dict:
        """Get cryptocurrency market overview from CoinGecko API."""
        url = f"{self.base_urls['coingecko']}/coins/markets"
        
        params = {
            'vs_currency': currency,
            'order': 'market_cap_desc',
            'per_page': limit,
            'page': 1,
            'sparkline': False,
            'price_change_percentage': '24h,7d'
        }
        
        headers = {}
        if COINGECKO_API_KEY:
            headers['x-cg-pro-api-key'] = COINGECKO_API_KEY
            
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Calculate total market cap and 24h volume
        total_market_cap = sum(coin['market_cap'] for coin in data if coin['market_cap'])
        total_volume_24h = sum(coin['total_volume'] for coin in data if coin['total_volume'])
        
        # Format the data
        coins = []
        for coin in data:
            coins.append({
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'price': coin['current_price'],
                'market_cap': coin['market_cap'],
                'volume_24h': coin['total_volume'],
                'price_change_24h': coin['price_change_percentage_24h'],
                'price_change_7d': coin.get('price_change_percentage_7d_in_currency'),
                'image': coin['image']
            })
        
        return {
            'total_market_cap': total_market_cap,
            'total_volume_24h': total_volume_24h,
            'coins': coins,
            'currency': currency,
            'source': 'coingecko',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_market_overview_coinmarketcap(self, currency: str, limit: int) -> Dict:
        """Get cryptocurrency market overview from CoinMarketCap API."""
        url = f"{self.base_urls['coinmarketcap']}/cryptocurrency/listings/latest"
        
        headers = {
            'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY
        }
        
        params = {
            'start': 1,
            'limit': limit,
            'convert': currency.upper(),
            'sort': 'market_cap',
            'sort_dir': 'desc'
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Format the data
        coins = []
        currency_upper = currency.upper()
        total_market_cap = 0
        total_volume_24h = 0
        
        for coin in data['data']:
            quote = coin['quote'][currency_upper]
            market_cap = quote['market_cap'] or 0
            volume_24h = quote['volume_24h'] or 0
            
            total_market_cap += market_cap
            total_volume_24h += volume_24h
            
            coins.append({
                'symbol': coin['symbol'].upper(),
                'name': coin['name'],
                'price': quote['price'],
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'price_change_24h': quote['percent_change_24h'],
                'price_change_7d': quote['percent_change_7d']
            })
        
        return {
            'total_market_cap': total_market_cap,
            'total_volume_24h': total_volume_24h,
            'coins': coins,
            'currency': currency,
            'source': 'coinmarketcap',
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_crypto_sentiment(self, symbol: str) -> Dict:
        """
        Analyze market sentiment for a cryptocurrency.
        
        This function combines price data, trading volume, and other metrics
        to estimate market sentiment (bullish, bearish, or neutral).
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        symbol = symbol.upper()
        cache_key = f"crypto:sentiment:{symbol}"
        
        # Try to get from cache first
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Retrieved {symbol} sentiment from cache")
                return json.loads(cached_data)
        
        try:
            # Get current price and 7-day history
            current_data = self.get_current_price(symbol)
            history_data = self.get_price_history(symbol, days=7)
            
            if not current_data or not history_data:
                raise ValueError("Insufficient data for sentiment analysis")
            
            # Calculate key sentiment indicators
            
            # 1. Price momentum (24-hour change)
            price_change_24h = current_data.get('price_change_24h', 0)
            
            # 2. Price volatility (standard deviation over 7 days)
            prices = [point['price'] for point in history_data]
            volatility = np.std(prices) / np.mean(prices) if prices else 0
            
            # 3. Volume trend (comparing latest volume to 7-day average)
            current_volume = current_data.get('volume_24h', 0)
            
            # 4. Determine sentiment based on indicators
            sentiment = 'neutral'
            confidence = 0.5
            
            # Simple sentiment logic - can be expanded with more sophisticated analysis
            if price_change_24h > 5:  # More than 5% growth
                sentiment = 'bullish'
                confidence = min(0.5 + price_change_24h / 20, 0.95)
            elif price_change_24h < -5:  # More than 5% decline
                sentiment = 'bearish'
                confidence = min(0.5 + abs(price_change_24h) / 20, 0.95)
            
            # Adjust confidence based on volatility
            if volatility > 0.05:  # High volatility
                confidence = max(confidence - 0.1, 0.1)
            
            result = {
                'symbol': symbol,
                'sentiment': sentiment,
                'confidence': confidence,
                'price_change_24h': price_change_24h,
                'volatility': volatility,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache the result
            if redis_client:
                redis_client.setex(
                    cache_key,
                    CACHE_EXPIRE_TIME['sentiment'],
                    json.dumps(result)
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'sentiment': 'unknown',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def calculate_volatility(self, symbol: str, days: int = 30) -> Dict:
        """
        Calculate volatility metrics for a cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dictionary containing volatility metrics
        """
        symbol = symbol.upper()
        
        try:
            # Get historical data
            history = self.get_price_history(symbol, days=days)
            
            if not history:
                raise ValueError("Insufficient historical data")
            
            # Extract prices and calculate daily returns
            prices = [point['price'] for point in history]
            returns = []
            
            for i in range(1, len(prices)):
                daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(daily_return)
            
            # Calculate metrics
            daily_volatility = np.std(returns)
            annualized_volatility = daily_volatility * np.sqrt(365)
            
            # Additional metrics
            max_drawdown = 0
            highest_price = prices[0]
            
            for price in prices:
                if price > highest_price:
                    highest_price = price
                drawdown = (highest_price - price) / highest_price
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'symbol': symbol,
                'daily_volatility': daily_volatility,
                'annualized_volatility': annualized_volatility,
                'max_drawdown': max_drawdown,
                'days_analyzed': days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_crypto_conversion_rate(self, from_symbol: str, to_symbol: str) -> Dict:
        """
        Get conversion rate between two cryptocurrencies.
        
        Args:
            from_symbol: Source cryptocurrency symbol (e.g., 'BTC')
            to_symbol: Target cryptocurrency symbol (e.g., 'ETH')
            
        Returns:
            Dictionary containing conversion rate data
        """
        from_symbol = from_symbol.upper()
        to_symbol = to_symbol.upper()
        
        try:
            # Get current prices in USD
            from_data = self.get_current_price(from_symbol, 'usd')
            to_data = self.get_current_price(to_symbol, 'usd')
            
            if not from_data or not to_data:
                raise ValueError("Couldn't fetch prices for conversion")
            
            from_price = from_data.get('price')
            to_price = to_data.get('price')
            
            if not from_price or not to_price:
                raise ValueError("Missing price data for conversion")
            
            # Calculate conversion rate
            conversion_rate = from_price / to_price
            
            return {
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'conversion_rate': conversion_rate,
                'from_price_usd': from_price,
                'to_price_usd': to_price,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion rate {from_symbol} to {to_symbol}: {str(e)}")
            return {
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def convert_crypto_amount(self, amount: float, from_symbol: str, to_symbol: str) -> Dict:
        """
        Convert an amount from one cryptocurrency to another.
        
        Args:
            amount: Amount to convert
            from_symbol: Source cryptocurrency symbol (e.g., 'BTC')
            to_symbol: Target cryptocurrency symbol (e.g., 'ETH')
            
        Returns:
            Dictionary containing conversion result
        """
        try:
            # Get conversion rate
            conversion_data = self.get_crypto_conversion_rate(from_symbol, to_symbol)
            
            if 'error' in conversion_data:
                raise ValueError(conversion_data['error'])
            
            conversion_rate = conversion_data.get('conversion_rate')
            converted_amount = amount * conversion_rate
            
            return {
                'original_amount': amount,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'converted_amount': converted_amount,
                'conversion_rate': conversion_rate,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error converting {amount} {from_symbol} to {to_symbol}: {str(e)}")
            return {
                'original_amount': amount,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_crypto_market_news(self, symbol: str = None, limit: int = 5) -> List[Dict]:
        """
        Get latest crypto market news, optionally filtered by cryptocurrency.
        
        Args:
            symbol: Cryptocurrency symbol to filter news (optional)
            limit: Maximum number of news items to return (default: 5)
            
        Returns:
            List of dictionaries containing news items
        """
        cache_key = f"crypto:news:{symbol or 'general'}:{limit}"
        
        # Try to get from cache first
        if redis_client:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Retrieved crypto news from cache")
                return json.loads(cached_data)
        
        try:
            # CoinGecko API for news (free tier)
            symbol_param = ""
            if symbol:
                symbol = symbol.upper()
                if symbol not in self.crypto_mapping:
                    raise ValueError(f"Unsupported cryptocurrency: {symbol}")
                symbol_param = f"&ids={self.crypto_mapping[symbol]['coingecko']}"
            
            # Using alternative crypto news APIs (some may require API keys)
            # For now, we'll simulate news with placeholder data
            # In a production environment, integrate with a real news API
            
            # This is a placeholder - replace with actual API call
            news_items = [
                {
                    "title": f"Bitcoin Surpasses $60,000 Amid Regulatory Approval Speculation",
                    "description": "Bitcoin has reached a new milestone as market sentiment improves.",
                    "source": "CryptoNewsWire",
                    "url": "https://example.com/news/1",
                    "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "related_symbols": ["BTC"]
                },
                {
                    "title": "Ethereum Upgrade Expected to Reduce Gas Fees by 30%",
                    "description": "The upcoming Ethereum network upgrade aims to address scalability concerns.",
                    "source": "BlockchainReporter",
                    "url": "https://example.com/news/2",
                    "published_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "related_symbols": ["ETH"]
                },
                {
                    "title": "Kenya Considers Crypto Regulation Framework",
                    "description": "Kenyan regulators are exploring a comprehensive framework for cryptocurrencies.",
                    "source": "AfricanFintech",
                    "url": "https://example.com/news/3",
                    "published_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                    "related_symbols": ["BTC", "ETH", "XRP"]
                },
                {
                    "title": "Solana Network Activity Reaches All-Time High",
                    "description": "Solana blockchain records unprecedented transaction volume amid growing adoption.",
                    "source": "CryptoAnalytics",
                    "url": "https://example.com/news/4",
                    "published_at": (datetime.now() - timedelta(hours=12)).isoformat(),
                    "related_symbols": ["SOL"]
                },
                {
                    "title": "Central Banks Worldwide Explore CBDC Integration with Existing Crypto",
                    "description": "Several central banks are researching potential interoperability between CBDCs and cryptocurrencies.",
                    "source": "GlobalFinanceToday",
                    "url": "https://example.com/news/5",
                    "published_at": (datetime.now() - timedelta(hours=24)).isoformat(),
                    "related_symbols": ["BTC", "ETH", "USDT", "XRP"]
                }
            ]
            
            # Filter by symbol if provided
            if symbol:
                news_items = [
                    item for item in news_items 
                    if symbol in item.get('related_symbols', [])
                ]
            
            # Apply limit
            news_items = news_items[:limit]
            
            # Cache the result
            if redis_client:
                redis_client.setex(
                    cache_key,
                    CACHE_EXPIRE_TIME['market_data'],
                    json.dumps(news_items)
                )
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error getting crypto news: {str(e)}")
            return []
    
    def get_crypto_risk_assessment(self, symbol: str) -> Dict:
        """
        Assess risk level for a cryptocurrency investment.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            
        Returns:
            Dictionary containing risk assessment metrics
        """
        symbol = symbol.upper()
        
        try:
            # Get volatility metrics
            volatility_data = self.calculate_volatility(symbol)
            
            if 'error' in volatility_data:
                raise ValueError(volatility_data['error'])
            
            # Get market data
            market_data = self.get_current_price(symbol)
            
            if 'error' in market_data:
                raise ValueError(market_data['error'])
            
            # Calculate risk score (0-100, higher is riskier)
            annualized_volatility = volatility_data.get('annualized_volatility', 0)
            max_drawdown = volatility_data.get('max_drawdown', 0)
            
            # Simple risk scoring formula - can be expanded with more factors
            volatility_score = min(annualized_volatility * 100, 50)
            drawdown_score = min(max_drawdown * 100, 30)
            
            # Market maturity factor (lower for established cryptos)
            if symbol in ['BTC', 'ETH']:
                maturity_factor = 0.8
            elif symbol in ['XRP', 'SOL', 'USDT']:
                maturity_factor = 0.9
            else:
                maturity_factor = 1.0
            
            risk_score = (volatility_score + drawdown_score) * maturity_factor
            
            # Determine risk category
            risk_category = 'unknown'
            if 0 <= risk_score < 20:
                risk_category = 'very low'
            elif 20 <= risk_score < 40:
                risk_category = 'low'
            elif 40 <= risk_score < 60:
                risk_category = 'medium'
            elif 60 <= risk_score < 80:
                risk_category = 'high'
            elif 80 <= risk_score <= 100:
                risk_category = 'very high'
            
            return {
                'symbol': symbol,
                'risk_score': risk_score,
                'risk_category': risk_category,
                'volatility_contribution': volatility_score,
                'drawdown_contribution': drawdown_score,
                'maturity_factor': maturity_factor,
                'supporting_data': {
                    'annualized_volatility': annualized_volatility,
                    'max_drawdown': max_drawdown,
                    'price_change_24h': market_data.get('price_change_24h')
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error assessing risk for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'risk_category': 'unknown',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Create an instance that can be imported by other modules
crypto_api = CryptoAPI()

# Command-line testing
if __name__ == "__main__":
    api = CryptoAPI()
    
    # Example usage
    print("Testing Crypto API functionality...")
    
    # Get current price
    btc_price = api.get_current_price('BTC')
    print(f"\nBitcoin current price:\n{json.dumps(btc_price, indent=2)}")
    
    # Get market overview
    market_overview = api.get_market_overview(limit=5)
    print(f"\nMarket overview:\n{json.dumps(market_overview, indent=2)}")
    
    # Get sentiment analysis
    btc_sentiment = api.analyze_crypto_sentiment('BTC')
    print(f"\nBitcoin sentiment analysis:\n{json.dumps(btc_sentiment, indent=2)}")
    
    # Get risk assessment
    btc_risk = api.get_crypto_risk_assessment('BTC')
    print(f"\nBitcoin risk assessment:\n{json.dumps(btc_risk, indent=2)}")

