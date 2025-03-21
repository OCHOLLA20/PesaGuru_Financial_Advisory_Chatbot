import os
import json
import datetime
import logging
import numpy as np
import pandas as pd
import requests
from typing import Dict, List, Tuple, Any, Optional, Union
from functools import lru_cache
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from dotenv import load_dotenv

# Local imports
try:
    from . import sentiment_analysis
    from . import risk_evaluation
    from . import market_data_api
    from ..api_integration import nse_api, cbk_api, forex_api, crypto_api
except ImportError:
    # For standalone testing
    import sentiment_analysis
    import risk_evaluation
    import market_data_api
    from api_integration import nse_api, cbk_api, forex_api, crypto_api

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("market_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
NSE_API_KEY = os.getenv("NSE_API_KEY")
CBK_API_KEY = os.getenv("CBK_API_KEY")
CRYPTO_API_KEY = os.getenv("CRYPTO_API_KEY")
FOREX_API_KEY = os.getenv("FOREX_API_KEY")
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)


class MarketAnalysis:
    """
    Market Analysis class for analyzing different financial markets and providing insights.
    """
    
    def __init__(self):
        """Initialize the Market Analysis module with required API clients and services."""
        self.nse_client = nse_api.NSEClient(api_key=NSE_API_KEY)
        self.cbk_client = cbk_api.CBKClient(api_key=CBK_API_KEY)
        self.crypto_client = crypto_api.CryptoClient(api_key=CRYPTO_API_KEY)
        self.forex_client = forex_api.ForexClient(api_key=FOREX_API_KEY)
        self.sentiment = sentiment_analysis.SentimentAnalysis()
        self.risk_evaluator = risk_evaluation.RiskEvaluation()
        self.market_data = market_data_api.MarketDataAPI()
        
        # Cache for storing market data and analysis results
        self.data_cache = {}
        
        logger.info("Market Analysis module initialized")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        Check if cached data is still valid based on cache duration.
        
        Args:
            cache_key: Key to check in the cache
            
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if cache_key not in self.data_cache:
            return False
        
        cache_time = self.data_cache[cache_key]['timestamp']
        current_time = datetime.datetime.now().timestamp()
        
        return (current_time - cache_time) < CACHE_DURATION
    
    def _update_cache(self, cache_key: str, data: Any) -> None:
        """
        Update the cache with new data.
        
        Args:
            cache_key: Key to store in the cache
            data: Data to cache
        """
        self.data_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.datetime.now().timestamp()
        }
    
    def _get_from_cache(self, cache_key: str) -> Any:
        """
        Get data from cache if it exists and is valid.
        
        Args:
            cache_key: Key to retrieve from cache
            
        Returns:
            Any: Cached data or None if not found
        """
        if self._is_cache_valid(cache_key):
            return self.data_cache[cache_key]['data']
        return None
    
    def analyze_stock(self, symbol: str, days: int = 90) -> Dict[str, Any]:
        """
        Analyze a specific stock by symbol with trend analysis, key metrics, and recommendation.
        
        Args:
            symbol: Stock symbol to analyze (e.g., 'SCOM' for Safaricom)
            days: Number of days of historical data to analyze
            
        Returns:
            Dict with stock analysis including price trends, metrics, and recommendations
        """
        cache_key = f"stock_analysis_{symbol}_{days}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Using cached stock analysis for {symbol}")
            return cached_data
        
        try:
            # Get historical stock data
            historical_data = self.nse_client.get_historical_data(symbol, days)
            
            if not historical_data or len(historical_data) < 10:
                logger.warning(f"Insufficient historical data for {symbol}")
                return {"error": f"Insufficient data for {symbol}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Calculate key metrics
            latest_price = df['close'].iloc[-1]
            price_change = df['close'].iloc[-1] - df['close'].iloc[0]
            price_change_pct = (price_change / df['close'].iloc[0]) * 100
            
            # Calculate moving averages
            df['SMA_20'] = df['close'].rolling(window=20).mean()
            df['SMA_50'] = df['close'].rolling(window=50).mean()
            
            # Calculate RSI (Relative Strength Index)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate Bollinger Bands
            df['20dSTD'] = df['close'].rolling(window=20).std()
            df['upper_band'] = df['SMA_20'] + (df['20dSTD'] * 2)
            df['lower_band'] = df['SMA_20'] - (df['20dSTD'] * 2)
            
            # Determine trend
            if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1]:
                trend = "Bullish"
            elif df['SMA_20'].iloc[-1] < df['SMA_50'].iloc[-1]:
                trend = "Bearish"
            else:
                trend = "Neutral"
                
            # Get company fundamentals
            company_info = self.nse_client.get_company_info(symbol)
            
            # Get sentiment score for this stock (based on news articles)
            sentiment_score = self.sentiment.analyze_stock_sentiment(symbol)
            
            # Generate investment recommendation
            if price_change_pct > 15 and trend == "Bullish" and sentiment_score > 0.6:
                recommendation = "Strong Buy"
            elif price_change_pct > 5 and trend == "Bullish" and sentiment_score > 0:
                recommendation = "Buy"
            elif price_change_pct < -15 and trend == "Bearish" and sentiment_score < -0.6:
                recommendation = "Strong Sell"
            elif price_change_pct < -5 and trend == "Bearish" and sentiment_score < 0:
                recommendation = "Sell"
            else:
                recommendation = "Hold"
            
            # Predict price trend for next 7 days
            price_prediction = self._predict_stock_price(df['close'].values, 7)
            
            # Calculate volatility (standard deviation of returns)
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Annualized volatility
            
            # Compile results
            analysis_result = {
                "symbol": symbol,
                "company_name": company_info.get('name', symbol),
                "latest_price": latest_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "current_trend": trend,
                "recommendation": recommendation,
                "sentiment_score": sentiment_score,
                "sentiment_analysis": self._interpret_sentiment(sentiment_score),
                "volatility": volatility,
                "risk_level": self._calculate_risk_level(volatility),
                "technical_indicators": {
                    "RSI": df['RSI'].iloc[-1],
                    "SMA_20": df['SMA_20'].iloc[-1],
                    "SMA_50": df['SMA_50'].iloc[-1],
                    "upper_band": df['upper_band'].iloc[-1],
                    "lower_band": df['lower_band'].iloc[-1]
                },
                "price_prediction": {
                    "next_7_days": price_prediction,
                    "prediction_trend": "Up" if price_prediction[-1] > latest_price else "Down"
                },
                "fundamentals": company_info,
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info(f"Completed stock analysis for {symbol}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing stock {symbol}: {str(e)}")
            return {"error": f"Failed to analyze stock {symbol}: {str(e)}"}
    
    def _predict_stock_price(self, historical_prices: np.ndarray, days_ahead: int = 7) -> List[float]:
        """
        Predict stock prices for a specified number of days ahead using ARIMA model.
        
        Args:
            historical_prices: Array of historical stock prices
            days_ahead: Number of days to predict ahead
            
        Returns:
            List of predicted prices
        """
        try:
            # Fit ARIMA model
            model = ARIMA(historical_prices, order=(5, 1, 0))
            model_fit = model.fit()
            
            # Make prediction
            forecast = model_fit.forecast(steps=days_ahead)
            return forecast.tolist()
            
        except Exception as e:
            logger.error(f"Error predicting stock price: {str(e)}")
            # Fallback to simple linear regression
            try:
                x = np.array(range(len(historical_prices))).reshape(-1, 1)
                y = historical_prices
                model = LinearRegression()
                model.fit(x, y)
                
                future_x = np.array(range(len(historical_prices), len(historical_prices) + days_ahead)).reshape(-1, 1)
                predictions = model.predict(future_x)
                
                return predictions.tolist()
            except Exception as nested_e:
                logger.error(f"Fallback prediction also failed: {str(nested_e)}")
                # Return the last price repeated
                return [historical_prices[-1]] * days_ahead
    
    def _interpret_sentiment(self, sentiment_score: float) -> str:
        """
        Interpret the numerical sentiment score into a human-readable description.
        
        Args:
            sentiment_score: Numerical sentiment score (-1.0 to 1.0)
            
        Returns:
            String interpretation of the sentiment
        """
        if sentiment_score > 0.7:
            return "Very Positive"
        elif sentiment_score > 0.3:
            return "Positive"
        elif sentiment_score > -0.3:
            return "Neutral"
        elif sentiment_score > -0.7:
            return "Negative"
        else:
            return "Very Negative"
    
    def _calculate_risk_level(self, volatility: float) -> str:
        """
        Calculate risk level based on volatility.
        
        Args:
            volatility: Stock volatility value
            
        Returns:
            Risk level as string
        """
        if volatility < 0.10:
            return "Very Low"
        elif volatility < 0.15:
            return "Low"
        elif volatility < 0.25:
            return "Moderate"
        elif volatility < 0.35:
            return "High"
        else:
            return "Very High"
    
    def analyze_nse_index(self, index_name: str = "NSE_20", days: int = 90) -> Dict[str, Any]:
        """
        Analyze a Nairobi Securities Exchange index performance and trends.
        
        Args:
            index_name: Name of the index (default: "NSE_20")
            days: Number of days of historical data to analyze
            
        Returns:
            Dict with index analysis including trends and sector performance
        """
        cache_key = f"index_analysis_{index_name}_{days}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Using cached index analysis for {index_name}")
            return cached_data
        
        try:
            # Get historical index data
            historical_data = self.nse_client.get_index_data(index_name, days)
            
            if not historical_data:
                logger.warning(f"No data available for index {index_name}")
                return {"error": f"No data available for index {index_name}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Calculate key metrics
            latest_value = df['value'].iloc[-1]
            change = df['value'].iloc[-1] - df['value'].iloc[0]
            change_pct = (change / df['value'].iloc[0]) * 100
            
            # Calculate moving averages
            df['SMA_20'] = df['value'].rolling(window=20).mean()
            df['SMA_50'] = df['value'].rolling(window=50).mean()
            
            # Determine trend
            if df['SMA_20'].iloc[-1] > df['SMA_50'].iloc[-1]:
                trend = "Bullish"
            elif df['SMA_20'].iloc[-1] < df['SMA_50'].iloc[-1]:
                trend = "Bearish"
            else:
                trend = "Neutral"
                
            # Get market breadth data (advancing vs declining stocks)
            try:
                market_breadth = self.nse_client.get_market_breadth()
                advancing = market_breadth.get('advancing', 0)
                declining = market_breadth.get('declining', 0)
                unchanged = market_breadth.get('unchanged', 0)
                breadth_ratio = advancing / declining if declining > 0 else float('inf')
            except:
                # Default values if API fails
                advancing = declining = unchanged = 0
                breadth_ratio = 1.0
            
            # Get sector performance
            sector_performance = self.nse_client.get_sector_performance()
            
            # Predict index trend for next 7 days
            index_prediction = self._predict_stock_price(df['value'].values, 7)
            
            # Compile results
            analysis_result = {
                "index_name": index_name,
                "latest_value": latest_value,
                "change": change,
                "change_percentage": change_pct,
                "current_trend": trend,
                "market_breadth": {
                    "advancing_stocks": advancing,
                    "declining_stocks": declining,
                    "unchanged_stocks": unchanged,
                    "advance_decline_ratio": breadth_ratio,
                    "market_strength": self._interpret_market_strength(breadth_ratio)
                },
                "sector_performance": sector_performance,
                "technical_indicators": {
                    "SMA_20": df['SMA_20'].iloc[-1],
                    "SMA_50": df['SMA_50'].iloc[-1],
                },
                "prediction": {
                    "next_7_days": index_prediction,
                    "prediction_trend": "Up" if index_prediction[-1] > latest_value else "Down"
                },
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info(f"Completed index analysis for {index_name}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing index {index_name}: {str(e)}")
            return {"error": f"Failed to analyze index {index_name}: {str(e)}"}
    
    def _interpret_market_strength(self, breadth_ratio: float) -> str:
        """
        Interpret market strength based on breadth ratio.
        
        Args:
            breadth_ratio: Ratio of advancing to declining stocks
            
        Returns:
            String interpretation of market strength
        """
        if breadth_ratio > 3.0:
            return "Very Strong"
        elif breadth_ratio > 2.0:
            return "Strong"
        elif breadth_ratio > 1.0:
            return "Positive"
        elif breadth_ratio > 0.5:
            return "Weak"
        else:
            return "Very Weak"
    
    def analyze_crypto(self, symbol: str = "BTC", vs_currency: str = "KES", days: int = 90) -> Dict[str, Any]:
        """
        Analyze cryptocurrency performance, volatility, and trends.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC' for Bitcoin)
            vs_currency: Currency to compare against (default: 'KES')
            days: Number of days of historical data to analyze
            
        Returns:
            Dict with crypto analysis including price trends and metrics
        """
        cache_key = f"crypto_analysis_{symbol}_{vs_currency}_{days}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Using cached crypto analysis for {symbol}")
            return cached_data
        
        try:
            # Get current price data
            current_data = self.crypto_client.get_current_price(symbol, vs_currency)
            
            # Get historical price data
            historical_data = self.crypto_client.get_historical_data(symbol, vs_currency, days)
            
            if not historical_data:
                logger.warning(f"No historical data available for {symbol}")
                return {"error": f"No historical data available for {symbol}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.sort_values('date')
            
            # Calculate key metrics
            latest_price = current_data.get('price', df['price'].iloc[-1])
            price_change = latest_price - df['price'].iloc[0]
            price_change_pct = (price_change / df['price'].iloc[0]) * 100
            
            # Calculate moving averages
            df['SMA_7'] = df['price'].rolling(window=7).mean()
            df['SMA_30'] = df['price'].rolling(window=30).mean()
            
            # Calculate volatility (standard deviation of daily returns)
            returns = df['price'].pct_change().dropna()
            volatility = returns.std() * (365 ** 0.5)  # Annualized volatility
            
            # Determine trend
            if df['SMA_7'].iloc[-1] > df['SMA_30'].iloc[-1]:
                trend = "Bullish"
            elif df['SMA_7'].iloc[-1] < df['SMA_30'].iloc[-1]:
                trend = "Bearish"
            else:
                trend = "Neutral"
                
            # Get sentiment analysis for this crypto
            sentiment_score = self.sentiment.analyze_crypto_sentiment(symbol)
            
            # Generate trading insight
            if price_change_pct > 20 and trend == "Bullish" and sentiment_score > 0.5:
                insight = "Strong positive momentum"
            elif price_change_pct > 10 and trend == "Bullish":
                insight = "Positive trend developing"
            elif price_change_pct < -20 and trend == "Bearish" and sentiment_score < -0.5:
                insight = "Strong downward pressure"
            elif price_change_pct < -10 and trend == "Bearish":
                insight = "Downward trend developing"
            else:
                insight = "Sideways movement with no clear direction"
            
            # Predict price trend for next 7 days
            price_prediction = self._predict_crypto_price(df['price'].values, 7)
            
            # Get additional crypto info
            crypto_info = self.crypto_client.get_coin_info(symbol)
            
            # Compile results
            analysis_result = {
                "symbol": symbol,
                "name": crypto_info.get('name', symbol),
                "vs_currency": vs_currency,
                "latest_price": latest_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "current_trend": trend,
                "market_insight": insight,
                "volatility": volatility,
                "risk_level": self._calculate_crypto_risk(volatility, symbol),
                "sentiment_score": sentiment_score,
                "sentiment_analysis": self._interpret_sentiment(sentiment_score),
                "technical_indicators": {
                    "SMA_7": df['SMA_7'].iloc[-1],
                    "SMA_30": df['SMA_30'].iloc[-1],
                },
                "price_prediction": {
                    "next_7_days": price_prediction,
                    "prediction_trend": "Up" if price_prediction[-1] > latest_price else "Down"
                },
                "market_data": {
                    "market_cap": crypto_info.get('market_cap', 'N/A'),
                    "24h_volume": crypto_info.get('volume_24h', 'N/A'),
                    "circulating_supply": crypto_info.get('circulating_supply', 'N/A')
                },
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info(f"Completed crypto analysis for {symbol}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing cryptocurrency {symbol}: {str(e)}")
            return {"error": f"Failed to analyze cryptocurrency {symbol}: {str(e)}"}
    
    def _predict_crypto_price(self, historical_prices: np.ndarray, days_ahead: int = 7) -> List[float]:
        """
        Predict cryptocurrency prices for specified days ahead.
        Similar to stock prediction but modified for crypto's higher volatility.
        
        Args:
            historical_prices: Array of historical crypto prices
            days_ahead: Number of days to predict ahead
            
        Returns:
            List of predicted prices
        """
        # Use the same ARIMA model but with different parameters for crypto
        try:
            # Fit ARIMA model with parameters suitable for volatile assets
            model = ARIMA(historical_prices, order=(2, 1, 2))
            model_fit = model.fit()
            
            # Make prediction
            forecast = model_fit.forecast(steps=days_ahead)
            return forecast.tolist()
            
        except Exception as e:
            logger.error(f"Error predicting crypto price: {str(e)}")
            # Fallback to simple linear regression
            try:
                x = np.array(range(len(historical_prices))).reshape(-1, 1)
                y = historical_prices
                model = LinearRegression()
                model.fit(x, y)
                
                future_x = np.array(range(len(historical_prices), len(historical_prices) + days_ahead)).reshape(-1, 1)
                predictions = model.predict(future_x)
                
                return predictions.tolist()
            except Exception as nested_e:
                logger.error(f"Fallback prediction also failed: {str(nested_e)}")
                # Return the last price repeated
                return [historical_prices[-1]] * days_ahead
    
    def _calculate_crypto_risk(self, volatility: float, symbol: str) -> str:
        """
        Calculate risk level for cryptocurrency based on volatility and the specific coin.
        
        Args:
            volatility: Crypto volatility value
            symbol: Cryptocurrency symbol
            
        Returns:
            Risk level as string
        """
        # Base risk levels are higher for crypto than stocks
        base_risk = "High"  # Default base risk for most cryptocurrencies
        
        # Adjust base risk based on specific cryptocurrencies
        if symbol in ["BTC", "ETH"]:
            base_risk = "Moderate"  # Lower base risk for established cryptocurrencies
        elif symbol in ["USDT", "USDC", "DAI"]:
            base_risk = "Low"  # Lower risk for stablecoins
        
        # Adjust final risk based on volatility
        if volatility < 0.30:
            risk_adjustment = -1  # Lower risk
        elif volatility < 0.60:
            risk_adjustment = 0  # No adjustment
        elif volatility < 0.90:
            risk_adjustment = 1  # Higher risk
        else:
            risk_adjustment = 2  # Much higher risk
        
        # Map base risk + adjustment to final risk level
        risk_levels = ["Very Low", "Low", "Moderate", "High", "Very High"]
        base_index = risk_levels.index(base_risk)
        final_index = max(0, min(len(risk_levels) - 1, base_index + risk_adjustment))
        
        return risk_levels[final_index]
    
    def analyze_forex(self, base_currency: str = "USD", quote_currency: str = "KES", days: int = 90) -> Dict[str, Any]:
        """
        Analyze forex exchange rates, trends, and make predictions.
        
        Args:
            base_currency: Base currency code (e.g., 'USD')
            quote_currency: Quote currency code (e.g., 'KES')
            days: Number of days of historical data to analyze
            
        Returns:
            Dict with forex analysis including rate trends and forecasts
        """
        cache_key = f"forex_analysis_{base_currency}_{quote_currency}_{days}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Using cached forex analysis for {base_currency}/{quote_currency}")
            return cached_data
        
        try:
            # Get current exchange rate
            current_rate = self.forex_client.get_exchange_rate(base_currency, quote_currency)
            
            # Get historical exchange rates
            historical_data = self.forex_client.get_historical_rates(base_currency, quote_currency, days)
            
            if not historical_data:
                logger.warning(f"No historical data available for {base_currency}/{quote_currency}")
                return {"error": f"No historical data available for {base_currency}/{quote_currency}"}
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Calculate key metrics
            latest_rate = current_rate.get('rate', df['rate'].iloc[-1])
            rate_change = latest_rate - df['rate'].iloc[0]
            rate_change_pct = (rate_change / df['rate'].iloc[0]) * 100
            
            # Calculate moving averages
            df['SMA_7'] = df['rate'].rolling(window=7).mean()
            df['SMA_30'] = df['rate'].rolling(window=30).mean()
            
            # Calculate volatility
            returns = df['rate'].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Annualized volatility
            
            # Determine trend
            if df['SMA_7'].iloc[-1] > df['SMA_30'].iloc[-1]:
                trend = f"{quote_currency} is weakening against {base_currency}"
                if quote_currency == "KES":
                    trend_impact = "Imports becoming more expensive, exports more competitive"
            elif df['SMA_7'].iloc[-1] < df['SMA_30'].iloc[-1]:
                trend = f"{quote_currency} is strengthening against {base_currency}"
                if quote_currency == "KES":
                    trend_impact = "Imports becoming cheaper, exports less competitive"
            else:
                trend = f"{base_currency}/{quote_currency} rate is stable"
                trend_impact = "No significant impact on trade balance"
            
            # Get inflation data if available for economic context
            try:
                ksh_inflation = self.cbk_client.get_inflation_rate() if quote_currency == "KES" else None
                base_inflation = None  # Would need additional APIs for other countries
            except:
                ksh_inflation = base_inflation = None
                
            # Predict forex rate for next 7 days
            rate_prediction = self._predict_forex_rate(df['rate'].values, 7)
            
            # Compile results
            analysis_result = {
                "pair": f"{base_currency}/{quote_currency}",
                "latest_rate": latest_rate,
                "rate_change": rate_change,
                "rate_change_pct": rate_change_pct,
                "current_trend": trend,
                "trend_impact": trend_impact,
                "volatility": volatility,
                "stability": self._interpret_forex_stability(volatility),
                "technical_indicators": {
                    "SMA_7": df['SMA_7'].iloc[-1],
                    "SMA_30": df['SMA_30'].iloc[-1],
                },
                "rate_prediction": {
                    "next_7_days": rate_prediction,
                    "prediction_trend": "Up" if rate_prediction[-1] > latest_rate else "Down"
                },
                "economic_context": {
                    "KES_inflation": ksh_inflation,
                    f"{base_currency}_inflation": base_inflation
                },
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info(f"Completed forex analysis for {base_currency}/{quote_currency}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing forex {base_currency}/{quote_currency}: {str(e)}")
            return {"error": f"Failed to analyze forex {base_currency}/{quote_currency}: {str(e)}"}
    
    def _predict_forex_rate(self, historical_rates: np.ndarray, days_ahead: int = 7) -> List[float]:
        """
        Predict forex exchange rates for specified days ahead.
        
        Args:
            historical_rates: Array of historical exchange rates
            days_ahead: Number of days to predict ahead
            
        Returns:
            List of predicted rates
        """
        # Using ARIMA model optimized for forex
        try:
            # Fit ARIMA model with parameters suitable for forex
            model = ARIMA(historical_rates, order=(1, 1, 1))
            model_fit = model.fit()
            
            # Make prediction
            forecast = model_fit.forecast(steps=days_ahead)
            return forecast.tolist()
            
        except Exception as e:
            logger.error(f"Error predicting forex rate: {str(e)}")
            # Fallback to simple linear regression
            try:
                x = np.array(range(len(historical_rates))).reshape(-1, 1)
                y = historical_rates
                model = LinearRegression()
                model.fit(x, y)
                
                future_x = np.array(range(len(historical_rates), len(historical_rates) + days_ahead)).reshape(-1, 1)
                predictions = model.predict(future_x)
                
                return predictions.tolist()
            except Exception as nested_e:
                logger.error(f"Fallback prediction also failed: {str(nested_e)}")
                # Return the last rate repeated
                return [historical_rates[-1]] * days_ahead
    
    def _interpret_forex_stability(self, volatility: float) -> str:
        """
        Interpret forex exchange rate stability based on volatility.
        
        Args:
            volatility: Forex volatility value
            
        Returns:
            Stability description as string
        """
        if volatility < 0.05:
            return "Very Stable"
        elif volatility < 0.10:
            return "Stable"
        elif volatility < 0.15:
            return "Moderately Stable"
        elif volatility < 0.20:
            return "Volatile"
        else:
            return "Highly Volatile"
    
    def analyze_interest_rates(self) -> Dict[str, Any]:
        """
        Analyze current interest rates, bond yields, and loan rates in Kenya.
        
        Returns:
            Dict with interest rate analysis
        """
        cache_key = "interest_rates_analysis"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info("Using cached interest rates analysis")
            return cached_data
        
        try:
            # Get CBK base rate
            cbk_rate = self.cbk_client.get_central_bank_rate()
            
            # Get T-bill rates
            tbill_rates = self.cbk_client.get_tbill_rates()
            
            # Get bond yields
            bond_yields = self.cbk_client.get_bond_yields()
            
            # Get average commercial loan rates
            loan_rates = self.cbk_client.get_commercial_loan_rates()
            
            # Get historical CBK rates
            historical_cbk_rates = self.cbk_client.get_historical_cbr(90)  # Last 90 days
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_cbk_rates)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Determine trend
            if len(df) > 1:
                rate_change = df['rate'].iloc[-1] - df['rate'].iloc[0]
                if rate_change > 0:
                    trend = "Rising interest rates"
                    impact = "Borrowing becoming more expensive, potential slowdown in credit growth"
                elif rate_change < 0:
                    trend = "Falling interest rates"
                    impact = "Borrowing becoming cheaper, potential increase in credit growth"
                else:
                    trend = "Stable interest rates"
                    impact = "No significant change in borrowing costs"
            else:
                trend = "Insufficient historical data"
                impact = "Unable to determine trend impact"
                
            # Get inflation data for context
            try:
                inflation_rate = self.cbk_client.get_inflation_rate()
                real_interest_rate = cbk_rate - inflation_rate
            except:
                inflation_rate = None
                real_interest_rate = None
            
            # Predict CBK rate for next 3 months (if enough historical data)
            if len(df) > 30:
                rate_prediction = self._predict_interest_rate(df['rate'].values, 3)
            else:
                rate_prediction = [cbk_rate] * 3  # Just repeat current rate if not enough data
            
            # Compile results
            analysis_result = {
                "cbk_rate": cbk_rate,
                "current_trend": trend,
                "trend_impact": impact,
                "tbill_rates": tbill_rates,
                "bond_yields": bond_yields,
                "loan_rates": loan_rates,
                "economic_context": {
                    "inflation_rate": inflation_rate,
                    "real_interest_rate": real_interest_rate
                },
                "rate_prediction": {
                    "next_3_months": rate_prediction,
                    "prediction_trend": "Up" if rate_prediction[-1] > cbk_rate else "Down"
                },
                "investment_implications": self._get_interest_rate_implications(cbk_rate, trend),
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info("Completed interest rates analysis")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing interest rates: {str(e)}")
            return {"error": f"Failed to analyze interest rates: {str(e)}"}
    
    def _predict_interest_rate(self, historical_rates: np.ndarray, months_ahead: int = 3) -> List[float]:
        """
        Predict interest rates for specified months ahead.
        
        Args:
            historical_rates: Array of historical interest rates
            months_ahead: Number of months to predict ahead
            
        Returns:
            List of predicted rates
        """
        # Interest rates typically change in steps, so standard time series models may not work well
        # Instead, we'll use a simple approach based on recent changes
        
        if len(historical_rates) < 3:
            return [historical_rates[-1]] * months_ahead
        
        recent_changes = []
        for i in range(1, min(6, len(historical_rates))):
            if historical_rates[-i] != historical_rates[-(i+1)]:
                recent_changes.append(historical_rates[-i] - historical_rates[-(i+1)])
        
        if not recent_changes:
            # No recent changes, likely to remain stable
            return [historical_rates[-1]] * months_ahead
        
        avg_change = sum(recent_changes) / len(recent_changes)
        predictions = []
        last_rate = historical_rates[-1]
        
        for _ in range(months_ahead):
            # Apply some dampening as we look further into the future
            dampening = 0.7  # Reduce the effect of predicted changes
            last_rate += (avg_change * dampening)
            predictions.append(last_rate)
            
        return predictions
    
    def _get_interest_rate_implications(self, current_rate: float, trend: str) -> Dict[str, str]:
        """
        Generate investment implications based on current interest rate and trend.
        
        Args:
            current_rate: Current CBK rate
            trend: Current interest rate trend
            
        Returns:
            Dict with investment implications
        """
        implications = {}
        
        if "Rising" in trend:
            implications["Fixed Income"] = "Consider short-duration bonds to reduce interest rate risk"
            implications["Savings"] = "Fixed deposit rates likely to increase, good time for savings"
            implications["Loans"] = "Consider fixing loan rates before further increases"
            implications["Stocks"] = "Banking stocks may benefit, but overall market could face pressure"
            
        elif "Falling" in trend:
            implications["Fixed Income"] = "Consider locking in current rates with longer-duration bonds"
            implications["Savings"] = "Fixed deposit rates likely to decrease, consider other investments"
            implications["Loans"] = "Good time to negotiate variable rate loans or refinance"
            implications["Stocks"] = "Lower rates typically positive for stock market valuations"
            
        else:  # Stable
            implications["Fixed Income"] = "Balanced approach to duration based on financial goals"
            implications["Savings"] = "Compare different institutions for best stable rates"
            implications["Loans"] = "Assess both fixed and variable options based on risk preference"
            implications["Stocks"] = "Focus on company fundamentals rather than rate impacts"
            
        return implications
    
    def analyze_market_sentiment(self, market: str = "general") -> Dict[str, Any]:
        """
        Analyze overall market sentiment based on news, social media, and technical indicators.
        
        Args:
            market: Market to analyze (options: 'general', 'stocks', 'crypto', 'forex')
            
        Returns:
            Dict with market sentiment analysis
        """
        cache_key = f"sentiment_analysis_{market}"
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Using cached sentiment analysis for {market} market")
            return cached_data
        
        try:
            # Get sentiment from news sources
            news_sentiment = self.sentiment.analyze_market_news(market)
            
            # Get sentiment from technical indicators
            if market == "stocks" or market == "general":
                # For stocks, check market breadth and trend
                try:
                    market_breadth = self.nse_client.get_market_breadth()
                    advancing = market_breadth.get('advancing', 0)
                    declining = market_breadth.get('declining', 0)
                    technical_sentiment = advancing / (advancing + declining) if (advancing + declining) > 0 else 0.5
                except:
                    technical_sentiment = 0.5  # Neutral if data not available
            elif market == "crypto":
                # For crypto, check Bitcoin dominance trend as a general indicator
                try:
                    btc_dominance = self.crypto_client.get_bitcoin_dominance()
                    btc_dominance_change = btc_dominance.get('change_24h', 0)
                    # Higher BTC dominance during downturns often indicates defensive positioning
                    technical_sentiment = 0.4 if btc_dominance_change > 0 else 0.6
                except:
                    technical_sentiment = 0.5
            elif market == "forex":
                # For forex, check USD index as a general indicator
                try:
                    usd_index = self.forex_client.get_usd_index()
                    usd_change = usd_index.get('change_pct', 0)
                    # Stronger USD often correlates with risk-off sentiment
                    technical_sentiment = 0.4 if usd_change > 0 else 0.6
                except:
                    technical_sentiment = 0.5
            else:
                technical_sentiment = 0.5
            
            # Convert technical sentiment to -1 to 1 scale
            technical_sentiment = (technical_sentiment * 2) - 1
            
            # Combine news and technical sentiment (weighted average)
            news_weight = 0.7
            technical_weight = 0.3
            combined_sentiment = (news_sentiment * news_weight) + (technical_sentiment * technical_weight)
            
            # Determine market phase
            market_phase = self._determine_market_phase(combined_sentiment, market)
            
            # Generate market outlook
            if combined_sentiment > 0.6:
                outlook = "Strongly Bullish"
                outlook_details = "Strong positive sentiment indicates potential for continued upward movement"
            elif combined_sentiment > 0.2:
                outlook = "Moderately Bullish"
                outlook_details = "Positive sentiment suggests favorable conditions but watch for resistance levels"
            elif combined_sentiment > -0.2:
                outlook = "Neutral"
                outlook_details = "Mixed signals indicate a sideways market with no clear direction"
            elif combined_sentiment > -0.6:
                outlook = "Moderately Bearish"
                outlook_details = "Negative sentiment suggests potential downside risk, exercise caution"
            else:
                outlook = "Strongly Bearish"
                outlook_details = "Strong negative sentiment indicates potential for continued downward pressure"
            
            # Compile results
            analysis_result = {
                "market": market,
                "news_sentiment": news_sentiment,
                "technical_sentiment": technical_sentiment,
                "combined_sentiment": combined_sentiment,
                "sentiment_interpretation": self._interpret_sentiment(combined_sentiment),
                "market_phase": market_phase,
                "market_outlook": outlook,
                "outlook_details": outlook_details,
                "investment_strategy": self._get_sentiment_based_strategy(combined_sentiment, market),
                "analysis_timestamp": datetime.datetime.now().isoformat()
            }
            
            # Cache the results
            self._update_cache(cache_key, analysis_result)
            logger.info(f"Completed sentiment analysis for {market} market")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing market sentiment for {market}: {str(e)}")
            return {"error": f"Failed to analyze market sentiment for {market}: {str(e)}"}
    
    def _determine_market_phase(self, sentiment: float, market: str) -> str:
        """
        Determine current market phase based on sentiment and market type.
        
        Args:
            sentiment: Combined sentiment score
            market: Market type
            
        Returns:
            Market phase as string
        """
        # Different markets may have different phase characteristics
        if market == "crypto":
            if sentiment > 0.7:
                return "Euphoria (Be cautious of bubble conditions)"
            elif sentiment > 0.3:
                return "Optimism (Growth phase)"
            elif sentiment > -0.3:
                return "Uncertainty (Consolidation phase)"
            elif sentiment > -0.7:
                return "Fear (Decline phase)"
            else:
                return "Capitulation (Potential bottom forming)"
        else:  # stocks, forex, general
            if sentiment > 0.7:
                return "Bull Market (Expansion phase)"
            elif sentiment > 0.3:
                return "Bull Market (Early phase)"
            elif sentiment > -0.3:
                return "Transition Market (Indecision phase)"
            elif sentiment > -0.7:
                return "Bear Market (Early phase)"
            else:
                return "Bear Market (Contraction phase)"
    
    def _get_sentiment_based_strategy(self, sentiment: float, market: str) -> Dict[str, str]:
        """
        Generate investment strategy recommendations based on sentiment.
        
        Args:
            sentiment: Combined sentiment score
            market: Market type
            
        Returns:
            Dict with investment strategy recommendations
        """
        strategy = {}
        
        if market == "stocks" or market == "general":
            if sentiment > 0.5:
                strategy["Focus"] = "Growth stocks with strong fundamentals"
                strategy["Allocation"] = "Consider increasing equity exposure"
                strategy["Sectors"] = "Focus on cyclical sectors (e.g., technology, consumer discretionary)"
            elif sentiment > 0:
                strategy["Focus"] = "Quality stocks with consistent earnings"
                strategy["Allocation"] = "Balanced equity exposure"
                strategy["Sectors"] = "Mix of defensive and growth sectors"
            elif sentiment > -0.5:
                strategy["Focus"] = "Value stocks and dividend payers"
                strategy["Allocation"] = "Reduce equity exposure, increase fixed income"
                strategy["Sectors"] = "Defensive sectors (e.g., utilities, consumer staples)"
            else:
                strategy["Focus"] = "High-quality bonds and cash equivalents"
                strategy["Allocation"] = "Significantly reduce equity exposure"
                strategy["Sectors"] = "Only select defensive stocks with strong balance sheets"
                
        elif market == "crypto":
            if sentiment > 0.5:
                strategy["Focus"] = "Consider established cryptocurrencies (Bitcoin, Ethereum)"
                strategy["Allocation"] = "Could increase crypto allocation if aligned with risk tolerance"
                strategy["Risk Management"] = "Set stop-losses to protect gains in volatile conditions"
            elif sentiment > 0:
                strategy["Focus"] = "Limited exposure to major cryptocurrencies"
                strategy["Allocation"] = "Small portion of portfolio (<5% for most investors)"
                strategy["Risk Management"] = "Dollar-cost averaging approach for reduced volatility"
            else:
                strategy["Focus"] = "Exercise extreme caution in crypto markets"
                strategy["Allocation"] = "Minimal exposure unless high risk tolerance"
                strategy["Risk Management"] = "Consider staying in stablecoins if maintaining crypto exposure"
                
        elif market == "forex":
            if sentiment > 0.5:
                strategy["Focus"] = "Consider exposure to emerging market currencies"
                strategy["Allocation"] = "Diversify currency holdings"
                strategy["Risk Management"] = "Monitor central bank policies closely"
            elif sentiment > 0:
                strategy["Focus"] = "Balanced approach to major and emerging currencies"
                strategy["Allocation"] = "Maintain diversified currency exposure"
                strategy["Risk Management"] = "Hedge significant forex exposure"
            else:
                strategy["Focus"] = "Safety in major reserve currencies (USD, EUR)"
                strategy["Allocation"] = "Reduce exposure to volatile currencies"
                strategy["Risk Management"] = "Consider forex hedging instruments"
                
        return strategy
    
    def generate_market_report(self, market_type: str = "stocks") -> Dict[str, Any]:
        """
        Generate a comprehensive market report with insights and recommendations.
        
        Args:
            market_type: Type of market ('stocks', 'crypto', 'forex', 'all')
            
        Returns:
            Dict with comprehensive market report
        """
        report = {
            "title": f"PesaGuru Market Report - {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "summary": {},
            "data": {},
            "recommendations": {},
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            # Market sentiment analysis
            sentiment = self.analyze_market_sentiment(market_type if market_type != "all" else "general")
            report["summary"]["market_sentiment"] = sentiment
            
            # Add market-specific data
            if market_type in ["stocks", "all"]:
                try:
                    report["data"]["nse_index"] = self.analyze_nse_index("NSE_20")
                    
                    # Add top gainers and losers
                    report["data"]["stock_movers"] = self.nse_client.get_top_movers()
                    
                    # Add sector performance
                    report["data"]["sector_performance"] = self.nse_client.get_sector_performance()
                    
                    # Generate stock recommendations
                    report["recommendations"]["stocks"] = self._generate_stock_recommendations(sentiment["combined_sentiment"])
                    
                except Exception as e:
                    logger.error(f"Error in stock market analysis: {str(e)}")
                    report["data"]["stocks_error"] = str(e)
            
            if market_type in ["crypto", "all"]:
                try:
                    # Analyze major cryptocurrencies
                    report["data"]["bitcoin"] = self.analyze_crypto("BTC", "KES")
                    report["data"]["ethereum"] = self.analyze_crypto("ETH", "KES")
                    
                    # Get overall crypto market cap
                    report["data"]["crypto_market_cap"] = self.crypto_client.get_global_market_cap()
                    
                    # Generate crypto recommendations
                    report["recommendations"]["crypto"] = self._generate_crypto_recommendations(sentiment["combined_sentiment"])
                    
                except Exception as e:
                    logger.error(f"Error in crypto market analysis: {str(e)}")
                    report["data"]["crypto_error"] = str(e)
            
            if market_type in ["forex", "all"]:
                try:
                    # Analyze major forex pairs relevant to KES
                    report["data"]["usd_kes"] = self.analyze_forex("USD", "KES")
                    report["data"]["eur_kes"] = self.analyze_forex("EUR", "KES")
                    report["data"]["gbp_kes"] = self.analyze_forex("GBP", "KES")
                    
                    # Generate forex recommendations
                    report["recommendations"]["forex"] = self._generate_forex_recommendations()
                    
                except Exception as e:
                    logger.error(f"Error in forex market analysis: {str(e)}")
                    report["data"]["forex_error"] = str(e)
            
            # Add interest rate data for all report types
            try:
                report["data"]["interest_rates"] = self.analyze_interest_rates()
            except Exception as e:
                logger.error(f"Error in interest rate analysis: {str(e)}")
                report["data"]["interest_rates_error"] = str(e)
            
            # Generate overall market outlook
            report["summary"]["market_outlook"] = self._generate_market_outlook(report)
            
            logger.info(f"Generated comprehensive market report for {market_type}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating market report: {str(e)}")
            return {
                "error": f"Failed to generate market report: {str(e)}",
                "partial_data": report
            }
    
    def _generate_stock_recommendations(self, sentiment: float) -> Dict[str, Any]:
        """
        Generate stock recommendations based on market sentiment.
        
        Args:
            sentiment: Market sentiment score
            
        Returns:
            Dict with stock recommendations
        """
        recommendations = {}
        
        # Risk-based recommendations
        if sentiment > 0.3:  # Positive sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["Safaricom", "EABL", "Equity Bank"],
                "medium_risk": ["KCB Group", "Co-operative Bank", "Jubilee Holdings"],
                "high_risk": ["TransCentury", "Longhorn Publishers", "Nairobi Business Ventures"]
            }
        elif sentiment > -0.3:  # Neutral sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["Safaricom", "BAT Kenya", "KCB Group"],
                "medium_risk": ["Equity Bank", "NCBA Group", "Standard Chartered"],
                "high_risk": ["Home Afrika", "Uchumi Supermarkets", "Express Kenya"]
            }
        else:  # Negative sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["BAT Kenya", "Jubilee Holdings", "Bamburi Cement"],
                "medium_risk": ["Safaricom", "EABL", "Equity Bank"],
                "high_risk": ["Avoid high-risk stocks in current market conditions"]
            }
        
        # Sector recommendations
        if sentiment > 0.3:
            recommendations["sectors"] = {
                "overweight": ["Banking", "Technology", "Manufacturing"],
                "neutral": ["Energy", "Insurance", "Real Estate"],
                "underweight": ["Retail", "Construction", "Agriculture"]
            }
        elif sentiment > -0.3:
            recommendations["sectors"] = {
                "overweight": ["Banking", "Insurance", "Energy"],
                "neutral": ["Manufacturing", "Technology", "Agriculture"],
                "underweight": ["Real Estate", "Construction", "Retail"]
            }
        else:
            recommendations["sectors"] = {
                "overweight": ["Consumer Staples", "Utilities", "Healthcare"],
                "neutral": ["Banking", "Insurance", "Energy"],
                "underweight": ["Technology", "Real Estate", "Construction"]
            }
        
        # Investment strategy
        if sentiment > 0.5:
            recommendations["strategy"] = "Growth-focused strategy targeting capital appreciation"
        elif sentiment > 0:
            recommendations["strategy"] = "Balanced approach with quality growth and dividend stocks"
        elif sentiment > -0.5:
            recommendations["strategy"] = "Defensive strategy focusing on dividend stocks and value"
        else:
            recommendations["strategy"] = "Capital preservation with focus on quality dividend stocks"
        
        return recommendations
    
    def _generate_crypto_recommendations(self, sentiment: float) -> Dict[str, Any]:
        """
        Generate cryptocurrency recommendations based on market sentiment.
        
        Args:
            sentiment: Market sentiment score
            
        Returns:
            Dict with crypto recommendations
        """
        recommendations = {}
        
        # Risk-based recommendations
        if sentiment > 0.3:  # Positive sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["Bitcoin (BTC)", "Ethereum (ETH)", "Binance Coin (BNB)"],
                "medium_risk": ["Solana (SOL)", "Polkadot (DOT)", "Cardano (ADA)"],
                "high_risk": ["Emerging altcoins with strong fundamentals"]
            }
        elif sentiment > -0.3:  # Neutral sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["Bitcoin (BTC)", "Ethereum (ETH)", "Stablecoins (USDT, USDC)"],
                "medium_risk": ["Limited exposure to major altcoins"],
                "high_risk": ["Avoid high-risk cryptocurrencies in uncertain markets"]
            }
        else:  # Negative sentiment
            recommendations["risk_profile"] = {
                "low_risk": ["Stablecoins (USDT, USDC, DAI)", "Limited Bitcoin exposure"],
                "medium_risk": ["Very limited exposure or stay out of market"],
                "high_risk": ["Avoid high-risk cryptocurrencies in bearish markets"]
            }
        
        # Investment strategy
        if sentiment > 0.5:
            recommendations["strategy"] = "Growth strategy with measured exposure to potential high-growth assets"
        elif sentiment > 0:
            recommendations["strategy"] = "Balanced approach with focus on established cryptocurrencies"
        elif sentiment > -0.5:
            recommendations["strategy"] = "Defensive strategy focusing on Bitcoin and stablecoins"
        else:
            recommendations["strategy"] = "Capital preservation with majority in stablecoins or exit positions"
        
        # Allocation recommendation
        if sentiment > 0.3:
            recommendations["allocation"] = "Consider 3-5% of investment portfolio for crypto (higher for risk-tolerant investors)"
        elif sentiment > -0.3:
            recommendations["allocation"] = "Limit to 1-3% of investment portfolio"
        else:
            recommendations["allocation"] = "Minimal exposure (<1%) or stay out of market temporarily"
        
        return recommendations
    
    def _generate_forex_recommendations(self) -> Dict[str, Any]:
        """
        Generate forex recommendations based on current exchange rates and trends.
        
        Returns:
            Dict with forex recommendations
        """
        recommendations = {}
        
        try:
            # Get current USD/KES analysis
            usd_kes = self.analyze_forex("USD", "KES")
            
            # Determine if KES is strengthening or weakening
            kes_trend = "stable"
            if "strengthening" in usd_kes.get("current_trend", ""):
                kes_trend = "strengthening"
            elif "weakening" in usd_kes.get("current_trend", ""):
                kes_trend = "weakening"
            
            # Generate recommendations based on KES trend
            if kes_trend == "strengthening":
                recommendations["foreign_currency_holdings"] = "Consider reducing USD holdings temporarily"
                recommendations["import_export"] = "Favorable for imports, challenging for exporters"
                recommendations["remittances"] = "Consider timing remittances if expecting continued KES strength"
            elif kes_trend == "weakening":
                recommendations["foreign_currency_holdings"] = "May want to increase USD holdings as a hedge"
                recommendations["import_export"] = "Challenging for imports, favorable for exporters"
                recommendations["remittances"] = "Consider expediting remittances before potential further KES weakening"
            else:
                recommendations["foreign_currency_holdings"] = "Maintain balanced currency exposure"
                recommendations["import_export"] = "Stable environment for both imports and exports"
                recommendations["remittances"] = "Normal remittance schedule recommended"
            
            # Provide currency diversification recommendation
            recommendations["currency_diversification"] = {
                "base": "Kenyan Shilling (KES)",
                "recommended_exposure": ["US Dollar (USD)", "Euro (EUR)", "British Pound (GBP)"],
                "allocation_strategy": "Consider 70% KES, 20% USD, 10% EUR/GBP for balanced approach"
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating forex recommendations: {str(e)}")
            return {"error": f"Failed to generate forex recommendations: {str(e)}"}
    
    def _generate_market_outlook(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate overall market outlook based on compiled report data.
        
        Args:
            report_data: Compiled market report data
            
        Returns:
            Dict with market outlook
        """
        outlook = {}
        
        # Extract sentiment if available
        try:
            sentiment = report_data["summary"]["market_sentiment"]["combined_sentiment"]
        except:
            sentiment = 0  # Neutral if not available
        
        # Set overall market tone
        if sentiment > 0.5:
            outlook["overall_tone"] = "Strongly Positive"
        elif sentiment > 0.2:
            outlook["overall_tone"] = "Positive"
        elif sentiment > -0.2:
            outlook["overall_tone"] = "Neutral"
        elif sentiment > -0.5:
            outlook["overall_tone"] = "Negative"
        else:
            outlook["overall_tone"] = "Strongly Negative"
        
        # Generate short-term outlook
        outlook["short_term"] = "Market showing signs of " + (
            "strength with potential for continued gains" if sentiment > 0.2 else 
            "stability with mixed indicators" if sentiment > -0.2 else
            "weakness with potential for continued pressure"
        )
        
        # Generate medium-term outlook
        if "interest_rates" in report_data.get("data", {}):
            interest_trend = report_data["data"]["interest_rates"].get("current_trend", "")
            
            if "Rising" in interest_trend:
                outlook["medium_term"] = "Rising interest rates may create headwinds for growth assets"
            elif "Falling" in interest_trend:
                outlook["medium_term"] = "Falling interest rates may provide support for growth assets"
            else:
                outlook["medium_term"] = "Stable interest rates provide a balanced environment for investment"
        else:
            outlook["medium_term"] = "Medium-term outlook dependent on central bank policy and economic growth"
        
        # Key factors to watch
        outlook["key_factors"] = [
            "Central Bank of Kenya monetary policy decisions",
            "Inflation trends and their impact on purchasing power",
            "Global market sentiment, particularly US and European markets",
            "Local political stability and policy decisions"
        ]
        
        return outlook
    
    def personalized_market_insights(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized market insights based on user's risk profile and investment goals.
        
        Args:
            user_profile: Dict containing user's risk profile, goals, and preferences
            
        Returns:
            Dict with personalized insights and recommendations
        """
        insights = {
            "user_id": user_profile.get("user_id", "unknown"),
            "risk_profile": user_profile.get("risk_profile", "moderate"),
            "investment_horizon": user_profile.get("investment_horizon", "medium"),
            "personalized_insights": {},
            "recommendations": {},
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            # Get market sentiment
            sentiment = self.analyze_market_sentiment("general")
            
            # Get user's investment preferences
            preferences = user_profile.get("investment_preferences", {})
            preferred_assets = preferences.get("asset_classes", ["stocks", "bonds"])
            preferred_sectors = preferences.get("sectors", [])
            preferred_currencies = preferences.get("currencies", ["KES", "USD"])
            
            # Match risk profile with current market sentiment
            risk_level = user_profile.get("risk_profile", "moderate").lower()
            sentiment_level = sentiment["combined_sentiment"]
            
            # Generate personalized market summary
            if risk_level == "conservative":
                if sentiment_level < -0.3:
                    insights["personalized_insights"]["market_summary"] = "Current market conditions align with your conservative approach. Focus on capital preservation."
                elif sentiment_level < 0.3:
                    insights["personalized_insights"]["market_summary"] = "Market showing mixed signals. Your conservative approach suggests maintaining quality fixed income exposure."
                else:
                    insights["personalized_insights"]["market_summary"] = "Market showing positive signals, but maintain your conservative positioning with selective equity exposure."
            
            elif risk_level == "moderate":
                if sentiment_level < -0.3:
                    insights["personalized_insights"]["market_summary"] = "Current market weakness suggests reducing risk. Consider increasing fixed income allocation."
                elif sentiment_level < 0.3:
                    insights["personalized_insights"]["market_summary"] = "Market showing mixed signals. Balanced approach aligns with your moderate risk profile."
                else:
                    insights["personalized_insights"]["market_summary"] = "Positive market sentiment aligns well with your moderate risk profile. Consider tactical opportunities."
            
            elif risk_level == "aggressive":
                if sentiment_level < -0.3:
                    insights["personalized_insights"]["market_summary"] = "Market weakness may present buying opportunities for your aggressive strategy, but exercise caution."
                elif sentiment_level < 0.3:
                    insights["personalized_insights"]["market_summary"] = "Market showing mixed signals. Selective approach to high-growth assets aligns with your risk tolerance."
                else:
                    insights["personalized_insights"]["market_summary"] = "Strong market sentiment aligns well with your aggressive approach. Growth assets favored."
            
            # Generate asset-specific insights based on preferences
            insights["personalized_insights"]["asset_specific"] = {}
            
            if "stocks" in preferred_assets:
                try:
                    # Get NSE index analysis
                    nse_analysis = self.analyze_nse_index("NSE_20")
                    
                    # Generate stock insights based on risk profile and market conditions
                    if risk_level == "conservative":
                        recommended_stocks = ["Safaricom", "EABL", "KCB Group"] if sentiment_level > -0.3 else ["BAT Kenya", "Bamburi Cement", "Jubilee Holdings"]
                        strategy = "Focus on established blue-chip companies with strong dividends and low volatility"
                    elif risk_level == "moderate":
                        recommended_stocks = ["Safaricom", "Equity Bank", "EABL", "Co-operative Bank", "NCBA Group"]
                        strategy = "Balanced approach with a mix of growth and value stocks in established sectors"
                    else:  # aggressive
                        recommended_stocks = ["Safaricom", "Equity Bank", "KCB Group", "Centum Investment", "TransCentury"]
                        strategy = "Growth-focused approach with potential for capital appreciation, including select mid-cap stocks"
                    
                    # Filter by preferred sectors if specified
                    if preferred_sectors:
                        # This would require a mapping of stocks to sectors
                        pass
                    
                    insights["personalized_insights"]["asset_specific"]["stocks"] = {
                        "market_trend": nse_analysis.get("current_trend", "Unable to determine"),
                        "recommended_strategy": strategy,
                        "recommended_stocks": recommended_stocks
                    }
                    
                except Exception as e:
                    logger.error(f"Error generating stock insights: {str(e)}")
                    insights["personalized_insights"]["asset_specific"]["stocks"] = {"error": str(e)}
            
            if "crypto" in preferred_assets:
                try:
                    # Get crypto market sentiment
                    crypto_sentiment = self.analyze_market_sentiment("crypto")
                    
                    # Generate crypto insights based on risk profile and market conditions
                    if risk_level == "conservative":
                        if sentiment_level < -0.3:
                            crypto_strategy = "Avoid cryptocurrency exposure in current market conditions"
                            crypto_allocation = "0%"
                        else:
                            crypto_strategy = "Very limited exposure to established cryptocurrencies only (Bitcoin)"
                            crypto_allocation = "1-2% maximum"
                    elif risk_level == "moderate":
                        if sentiment_level < -0.3:
                            crypto_strategy = "Minimal exposure focused on Bitcoin and stablecoins"
                            crypto_allocation = "1-3%"
                        else:
                            crypto_strategy = "Measured exposure to established cryptocurrencies (Bitcoin, Ethereum)"
                            crypto_allocation = "3-5%"
                    else:  # aggressive
                        if sentiment_level < -0.3:
                            crypto_strategy = "Limited exposure with focus on dollar-cost averaging into Bitcoin"
                            crypto_allocation = "3-5%"
                        else:
                            crypto_strategy = "Strategic allocation to major cryptocurrencies and select altcoins"
                            crypto_allocation = "5-10% maximum"
                    
                    insights["personalized_insights"]["asset_specific"]["crypto"] = {
                        "market_trend": crypto_sentiment.get("market_phase", "Unable to determine"),
                        "recommended_strategy": crypto_strategy,
                        "recommended_allocation": crypto_allocation
                    }
                    
                except Exception as e:
                    logger.error(f"Error generating crypto insights: {str(e)}")
                    insights["personalized_insights"]["asset_specific"]["crypto"] = {"error": str(e)}
            
            if "forex" in preferred_assets or any(curr != "KES" for curr in preferred_currencies):
                try:
                    # Generate forex insights based on preferred currencies
                    forex_insights = {}
                    
                    for currency in preferred_currencies:
                        if currency != "KES":
                            # Analyze currency pair
                            pair_analysis = self.analyze_forex(currency, "KES")
                            forex_insights[f"{currency}/KES"] = {
                                "current_trend": pair_analysis.get("current_trend", "Unable to determine"),
                                "stability": pair_analysis.get("stability", "Unknown")
                            }
                    
                    # Generate forex strategy
                    if risk_level == "conservative":
                        forex_strategy = "Focus on major reserve currencies (USD, EUR) for stability"
                    elif risk_level == "moderate":
                        forex_strategy = "Balanced exposure to major currencies with limited emerging market exposure"
                    else:  # aggressive
                        forex_strategy = "Diversified currency exposure including emerging market currencies for potential higher returns"
                    
                    insights["personalized_insights"]["asset_specific"]["forex"] = {
                        "currency_pairs": forex_insights,
                        "recommended_strategy": forex_strategy
                    }
                    
                except Exception as e:
                    logger.error(f"Error generating forex insights: {str(e)}")
                    insights["personalized_insights"]["asset_specific"]["forex"] = {"error": str(e)}
            
            # Generate personalized portfolio recommendations
            insights["recommendations"] = self._generate_personalized_recommendations(
                risk_level, 
                sentiment_level, 
                user_profile.get("investment_horizon", "medium"),
                preferred_assets
            )
            
            logger.info(f"Generated personalized market insights for user {user_profile.get('user_id', 'unknown')}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating personalized market insights: {str(e)}")
            return {
                "user_id": user_profile.get("user_id", "unknown"),
                "error": f"Failed to generate personalized insights: {str(e)}",
                "partial_insights": insights
            }
    
    def _generate_personalized_recommendations(self, risk_level: str, sentiment: float, 
                                               investment_horizon: str, preferred_assets: List[str]) -> Dict[str, Any]:
        """
        Generate personalized portfolio recommendations based on user profile and market conditions.
        
        Args:
            risk_level: User's risk tolerance level
            sentiment: Market sentiment score
            investment_horizon: User's investment time horizon
            preferred_assets: List of user's preferred asset classes
            
        Returns:
            Dict with personalized recommendations
        """
        recommendations = {}
        
        # Define base asset allocations by risk profile
        base_allocations = {
            "conservative": {
                "stocks": 30,
                "bonds": 50,
                "money_market": 15,
                "alternatives": 5
            },
            "moderate": {
                "stocks": 50,
                "bonds": 30,
                "money_market": 10,
                "alternatives": 10
            },
            "aggressive": {
                "stocks": 70,
                "bonds": 15,
                "money_market": 5,
                "alternatives": 10
            }
        }
        
        # Get base allocation for user's risk profile
        base_allocation = base_allocations.get(risk_level, base_allocations["moderate"])
        
        # Adjust allocation based on market sentiment
        adjusted_allocation = base_allocation.copy()
        
        # Sentiment adjustment factor (how much to adjust allocations based on sentiment)
        adjustment_factor = 10  # Percentage points to shift
        
        if sentiment > 0.3:  # Positive sentiment
            # Increase growth assets, decrease defensive assets
            adjusted_allocation["stocks"] = min(100, base_allocation["stocks"] + adjustment_factor)
            adjusted_allocation["bonds"] = max(0, base_allocation["bonds"] - adjustment_factor/2)
            adjusted_allocation["money_market"] = max(0, base_allocation["money_market"] - adjustment_factor/2)
        elif sentiment < -0.3:  # Negative sentiment
            # Decrease growth assets, increase defensive assets
            adjusted_allocation["stocks"] = max(0, base_allocation["stocks"] - adjustment_factor)
            adjusted_allocation["bonds"] = min(100, base_allocation["bonds"] + adjustment_factor/2)
            adjusted_allocation["money_market"] = min(100, base_allocation["money_market"] + adjustment_factor/2)
        
        # Normalize to ensure allocations sum to 100%
        total = sum(adjusted_allocation.values())
        for asset in adjusted_allocation:
            adjusted_allocation[asset] = round(adjusted_allocation[asset] * 100 / total)
        
        # Ensure allocations sum to exactly 100% after rounding
        adjustment_needed = 100 - sum(adjusted_allocation.values())
        if adjustment_needed != 0:
            # Add adjustment to largest allocation
            largest_asset = max(adjusted_allocation, key=adjusted_allocation.get)
            adjusted_allocation[largest_asset] += adjustment_needed
        
        # Filter allocations based on preferred assets
        if preferred_assets and len(preferred_assets) < len(adjusted_allocation):
            filtered_allocation = {asset: 0 for asset in adjusted_allocation}
            for asset in preferred_assets:
                if asset.lower() in filtered_allocation:
                    filtered_allocation[asset.lower()] = adjusted_allocation[asset.lower()]
            
            # Redistribute zeroed allocations proportionally
            zero_sum = sum([adjusted_allocation[asset] for asset in adjusted_allocation if filtered_allocation[asset] == 0])
            if zero_sum > 0:
                total_preferred = sum([filtered_allocation[asset] for asset in filtered_allocation if filtered_allocation[asset] > 0])
                for asset in filtered_allocation:
                    if filtered_allocation[asset] > 0:
                        filtered_allocation[asset] += round(zero_sum * filtered_allocation[asset] / total_preferred)
            
            adjusted_allocation = filtered_allocation
        
        # Set asset allocation recommendation
        recommendations["asset_allocation"] = adjusted_allocation
        
        # Generate specific investment recommendations based on risk and sentiment
        recommendations["specific_investments"] = {}
        
        # Stock recommendations
        if "stocks" in adjusted_allocation and adjusted_allocation["stocks"] > 0:
            if risk_level == "conservative":
                recommendations["specific_investments"]["stocks"] = {
                    "focus": "Dividend-paying blue chips with low volatility",
                    "examples": ["Safaricom", "EABL", "BAT Kenya", "Bamburi Cement"]
                }
            elif risk_level == "moderate":
                recommendations["specific_investments"]["stocks"] = {
                    "focus": "Mix of growth and income stocks across sectors",
                    "examples": ["Safaricom", "Equity Bank", "KCB Group", "Co-operative Bank", "EABL"]
                }
            else:  # aggressive
                recommendations["specific_investments"]["stocks"] = {
                    "focus": "Growth-oriented stocks with higher potential returns",
                    "examples": ["Safaricom", "Equity Bank", "Centum Investment", "Nation Media Group", "Transcentury"]
                }
        
        # Bond recommendations
        if "bonds" in adjusted_allocation and adjusted_allocation["bonds"] > 0:
            if investment_horizon == "short":
                recommendations["specific_investments"]["bonds"] = {
                    "focus": "Short-term treasury bills and corporate bonds",
                    "examples": ["91-day T-bills", "182-day T-bills", "Short-term corporate bonds"]
                }
            elif investment_horizon == "medium":
                recommendations["specific_investments"]["bonds"] = {
                    "focus": "Mix of medium-term government and corporate bonds",
                    "examples": ["2-year T-bonds", "5-year T-bonds", "Medium-term corporate bonds"]
                }
            else:  # long
                recommendations["specific_investments"]["bonds"] = {
                    "focus": "Long-term government bonds for higher yields",
                    "examples": ["10-year T-bonds", "15-year T-bonds", "Long-term infrastructure bonds"]
                }
        
        # Money market recommendations
        if "money_market" in adjusted_allocation and adjusted_allocation["money_market"] > 0:
            recommendations["specific_investments"]["money_market"] = {
                "focus": "Liquid money market instruments for cash needs and stability",
                "examples": ["Money market funds", "Fixed deposits", "Call accounts"]
            }
        
        # Alternative investment recommendations
        if "alternatives" in adjusted_allocation and adjusted_allocation["alternatives"] > 0:
            if risk_level == "conservative":
                recommendations["specific_investments"]["alternatives"] = {
                    "focus": "REITs and income-generating real estate",
                    "examples": ["Stanlib Fahari I-REIT", "Income-focused property funds"]
                }
            elif risk_level == "moderate":
                recommendations["specific_investments"]["alternatives"] = {
                    "focus": "Balanced mix of real estate and commodities",
                    "examples": ["REITs", "Gold ETFs", "Balanced property funds"]
                }
            else:  # aggressive
                recommendations["specific_investments"]["alternatives"] = {
                    "focus": "Growth-oriented alternative investments",
                    "examples": ["Private equity funds", "High-growth REITs", "Select cryptocurrencies (BTC, ETH)"]
                }
        
        # Investment strategy recommendation
        if sentiment > 0.3:
            strategy_approach = "growth-oriented"
        elif sentiment > -0.3:
            strategy_approach = "balanced"
        else:
            strategy_approach = "defensive"
            
        recommendations["investment_strategy"] = f"A {strategy_approach} approach aligned with your {risk_level} risk profile"
        
        # Rebalancing recommendation
        if investment_horizon == "short":
            recommendations["rebalancing"] = "Quarterly review of portfolio allocation"
        elif investment_horizon == "medium":
            recommendations["rebalancing"] = "Semi-annual review of portfolio allocation"
        else:  # long
            recommendations["rebalancing"] = "Annual review of portfolio allocation"
        
        return recommendations


# Example usage if run directly
if __name__ == "__main__":
    analyzer = MarketAnalysis()
    
    # Example: Analyze a stock
    stock_analysis = analyzer.analyze_stock("SCOM")  # Safaricom
    print(json.dumps(stock_analysis, indent=2))
    
    # Example: Analyze market sentiment
    sentiment_analysis = analyzer.analyze_market_sentiment()
    print(json.dumps(sentiment_analysis, indent=2))
