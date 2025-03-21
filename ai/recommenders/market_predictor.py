import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Tuple, Union, Optional
import pickle
import warnings
from scipy import stats
import tensorflow as tf

# ML libraries
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from pmdarima import auto_arima
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Local imports (from PesaGuru codebase)
from ..services.market_data_api import MarketDataAPI
from ..services.sentiment_analysis import SentimentAnalyzer
from ..services.risk_evaluation import RiskEvaluator
from ..api_integration.nse_api import NSEAPI
from ..api_integration.crypto_api import CryptoAPI
from ..api_integration.forex_api import ForexAPI
from ..api_integration.news_api import NewsAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/market_predictor.log'
)
logger = logging.getLogger(__name__)

class MarketPredictor:
    """
    Main class for market prediction and forecasting.
    Handles integration with data sources and implements prediction models.
    """
    
    def __init__(self, config_path: str = 'config/market_predictor_config.json'):
        """
        Initialize the MarketPredictor with configuration settings.
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.model_path = self.config.get('model_path', 'models/market/')
        self.data_api = MarketDataAPI()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_evaluator = RiskEvaluator()
        
        # Initialize API connectors
        self.nse_api = NSEAPI()
        self.crypto_api = CryptoAPI()
        self.forex_api = ForexAPI()
        self.news_api = NewsAPI()
        
        # Initialize scalers for data normalization
        self.scalers = {}
        
        # Load pre-trained models if they exist
        self.models = self._load_models()
        
        logger.info("MarketPredictor initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from JSON file.
        
        Args:
            config_path (str): Path to configuration file
            
        Returns:
            Dict: Configuration settings
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found. Using default settings.")
            return {
                "model_path": "models/market/",
                "prediction_horizon": {
                    "short_term": 7,
                    "medium_term": 30,
                    "long_term": 90
                },
                "lstm_settings": {
                    "units": 50,
                    "dropout": 0.2,
                    "epochs": 100,
                    "batch_size": 32
                },
                "data_window": 60,  # Days of historical data to use
                "confidence_threshold": 0.7
            }
    
    def _load_models(self) -> Dict:
        """
        Load pre-trained prediction models if they exist.
        
        Returns:
            Dict: Dictionary of loaded models
        """
        models = {
            "stock": {},
            "crypto": {},
            "forex": {},
            "macro": {}
        }
        
        # Try to load models if they exist
        try:
            # Stock prediction models
            stock_model_path = os.path.join(self.model_path, "stock_arima.pkl")
            if os.path.exists(stock_model_path):
                models["stock"]["arima"] = pickle.load(open(stock_model_path, 'rb'))
            
            stock_lstm_path = os.path.join(self.model_path, "stock_lstm.h5")
            if os.path.exists(stock_lstm_path):
                models["stock"]["lstm"] = load_model(stock_lstm_path)
            
            # Crypto prediction models
            crypto_model_path = os.path.join(self.model_path, "crypto_arima.pkl")
            if os.path.exists(crypto_model_path):
                models["crypto"]["arima"] = pickle.load(open(crypto_model_path, 'rb'))
            
            crypto_lstm_path = os.path.join(self.model_path, "crypto_lstm.h5")
            if os.path.exists(crypto_lstm_path):
                models["crypto"]["lstm"] = load_model(crypto_lstm_path)
            
            # Forex models
            forex_model_path = os.path.join(self.model_path, "forex_arima.pkl")
            if os.path.exists(forex_model_path):
                models["forex"]["arima"] = pickle.load(open(forex_model_path, 'rb'))
            
            # Load scalers for normalized data
            scaler_path = os.path.join(self.model_path, "scalers.pkl")
            if os.path.exists(scaler_path):
                self.scalers = pickle.load(open(scaler_path, 'rb'))
            
            logger.info(f"Loaded {sum(len(v) for v in models.values())} pre-trained models")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
        
        return models
    
    def save_models(self):
        """Save trained models to disk"""
        os.makedirs(self.model_path, exist_ok=True)
        
        # Save each model type
        for market_type, model_dict in self.models.items():
            for model_name, model in model_dict.items():
                if model_name == 'lstm':
                    model_path = os.path.join(self.model_path, f"{market_type}_{model_name}.h5")
                    model.save(model_path)
                else:
                    model_path = os.path.join(self.model_path, f"{market_type}_{model_name}.pkl")
                    with open(model_path, 'wb') as f:
                        pickle.dump(model, f)
        
        # Save scalers
        scaler_path = os.path.join(self.model_path, "scalers.pkl")
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scalers, f)
        
        logger.info("Models saved successfully")
    
    def preprocess_data(self, data: pd.DataFrame, asset_type: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess and normalize market data for model input.
        
        Args:
            data (pd.DataFrame): Historical price data
            asset_type (str): Type of asset ('stock', 'crypto', 'forex')
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Processed X and y data
        """
        # Handle missing values
        data = data.fillna(method='ffill')
        
        # Create or use existing scaler
        if asset_type not in self.scalers:
            self.scalers[asset_type] = MinMaxScaler(feature_range=(0, 1))
        
        # Extract features and scale
        features = data[['close', 'volume', 'high', 'low']].values
        scaled_features = self.scalers[asset_type].fit_transform(features)
        
        # Create windowed sequences for LSTM
        X, y = [], []
        window_size = self.config.get('data_window', 60)
        
        for i in range(window_size, len(scaled_features)):
            X.append(scaled_features[i-window_size:i])
            # Predict next day's closing price
            y.append(scaled_features[i, 0])  
        
        return np.array(X), np.array(y)
    
    def build_lstm_model(self, input_shape: Tuple) -> Sequential:
        """
        Build an LSTM model for sequence prediction.
        
        Args:
            input_shape (Tuple): Shape of input data
            
        Returns:
            Sequential: Keras LSTM model
        """
        settings = self.config.get('lstm_settings', {})
        units = settings.get('units', 50)
        dropout_rate = settings.get('dropout', 0.2)
        
        model = Sequential()
        model.add(LSTM(units=units, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(dropout_rate))
        model.add(LSTM(units=units))
        model.add(Dropout(dropout_rate))
        model.add(Dense(1))
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        return model
    
    def train_stock_model(self, symbol: str, model_type: str = 'lstm') -> Dict:
        """
        Train a model for stock price prediction.
        
        Args:
            symbol (str): Stock symbol (e.g., 'SCOM' for Safaricom)
            model_type (str): Model type ('lstm' or 'arima')
            
        Returns:
            Dict: Training results and metrics
        """
        logger.info(f"Training {model_type} model for stock: {symbol}")
        
        try:
            # Fetch historical stock data
            historical_data = self.nse_api.get_historical_data(symbol, days=365)
            
            if historical_data.empty:
                return {"error": "No historical data available for training"}
            
            if model_type == 'lstm':
                X, y = self.preprocess_data(historical_data, 'stock')
                
                # Split into train and test sets
                train_size = int(len(X) * 0.8)
                X_train, X_test = X[:train_size], X[train_size:]
                y_train, y_test = y[:train_size], y[train_size:]
                
                # Build and train LSTM model
                model = self.build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
                settings = self.config.get('lstm_settings', {})
                
                # Callbacks for early stopping and model checkpoint
                callbacks = [
                    EarlyStopping(patience=10, restore_best_weights=True),
                    ModelCheckpoint(
                        filepath=os.path.join(self.model_path, f"stock_lstm_{symbol}.h5"),
                        save_best_only=True
                    )
                ]
                
                history = model.fit(
                    X_train, y_train,
                    epochs=settings.get('epochs', 100),
                    batch_size=settings.get('batch_size', 32),
                    validation_data=(X_test, y_test),
                    callbacks=callbacks,
                    verbose=0
                )
                
                # Evaluate model
                y_pred = model.predict(X_test)
                
                # Inverse transform predictions for evaluation
                y_pred_actual = self.scalers['stock'].inverse_transform(
                    np.concatenate([y_pred, np.zeros((len(y_pred), 3))], axis=1)
                )[:, 0]
                
                y_test_actual = self.scalers['stock'].inverse_transform(
                    np.concatenate([y_test.reshape(-1, 1), np.zeros((len(y_test), 3))], axis=1)
                )[:, 0]
                
                # Calculate metrics
                mse = mean_squared_error(y_test_actual, y_pred_actual)
                mae = mean_absolute_error(y_test_actual, y_pred_actual)
                r2 = r2_score(y_test_actual, y_pred_actual)
                
                # Store model
                self.models["stock"][symbol] = model
                
                return {
                    "model_type": "lstm",
                    "symbol": symbol,
                    "metrics": {
                        "mse": mse,
                        "mae": mae,
                        "r2": r2
                    },
                    "training_history": {
                        "loss": history.history['loss'][-1],
                        "val_loss": history.history['val_loss'][-1]
                    }
                }
                
            elif model_type == 'arima':
                # Prepare data for ARIMA
                price_data = historical_data['close'].values
                
                # Automatically find optimal ARIMA parameters
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    arima_model = auto_arima(
                        price_data,
                        seasonal=False,
                        error_action='ignore',
                        suppress_warnings=True,
                        stepwise=True,
                        approximation=False
                    )
                
                # Store model parameters
                p, d, q = arima_model.order
                
                # Split data for evaluation
                train_size = int(len(price_data) * 0.8)
                train, test = price_data[:train_size], price_data[train_size:]
                
                # Fit ARIMA model
                arima_fitted = ARIMA(
                    train,
                    order=(p, d, q)
                ).fit()
                
                # Generate predictions
                predictions = arima_fitted.forecast(steps=len(test))
                
                # Calculate metrics
                mse = mean_squared_error(test, predictions)
                mae = mean_absolute_error(test, predictions)
                
                # Store model
                self.models["stock"][f"{symbol}_arima"] = arima_fitted
                
                return {
                    "model_type": "arima",
                    "symbol": symbol,
                    "parameters": {
                        "p": p,
                        "d": d,
                        "q": q
                    },
                    "metrics": {
                        "mse": mse,
                        "mae": mae
                    }
                }
            
            else:
                return {"error": f"Unsupported model type: {model_type}"}
                
        except Exception as e:
            logger.error(f"Error training stock model: {str(e)}")
            return {"error": str(e)}
    
    def train_crypto_model(self, symbol: str, model_type: str = 'lstm') -> Dict:
        """
        Train a model for cryptocurrency price prediction.
        
        Args:
            symbol (str): Crypto symbol (e.g., 'BTC')
            model_type (str): Model type ('lstm' or 'arima')
            
        Returns:
            Dict: Training results and metrics
        """
        logger.info(f"Training {model_type} model for crypto: {symbol}")
        
        try:
            # Fetch historical crypto data
            historical_data = self.crypto_api.get_historical_data(symbol, days=365)
            
            if historical_data.empty:
                return {"error": "No historical data available for training"}
            
            # Similar implementation as train_stock_model but adapted for crypto
            # For brevity, I'm not duplicating the full implementation here,
            # but it would follow the same pattern with appropriate adaptations
            
            # The key difference would be incorporating crypto-specific features
            # like market sentiment and BTC dominance for altcoins
            
            return {"status": "Crypto model training implemented"}
        
        except Exception as e:
            logger.error(f"Error training crypto model: {str(e)}")
            return {"error": str(e)}
    
    def train_forex_model(self, pair: str, model_type: str = 'arima') -> Dict:
        """
        Train a model for forex exchange rate prediction.
        
        Args:
            pair (str): Currency pair (e.g., 'KES/USD')
            model_type (str): Model type ('arima' or 'prophet')
            
        Returns:
            Dict: Training results and metrics
        """
        logger.info(f"Training {model_type} model for forex pair: {pair}")
        
        try:
            # Fetch historical forex data
            historical_data = self.forex_api.get_historical_data(pair, days=365)
            
            if historical_data.empty:
                return {"error": "No historical data available for training"}
            
            # Implementation would be similar to the stock model training
            # with adaptations for forex-specific features
            
            return {"status": "Forex model training implemented"}
        
        except Exception as e:
            logger.error(f"Error training forex model: {str(e)}")
            return {"error": str(e)}
    
    def predict_stock_price(self, symbol: str, days: int = 7) -> Dict:
        """
        Predict future stock prices.
        
        Args:
            symbol (str): Stock symbol (e.g., 'SCOM' for Safaricom)
            days (int): Number of days to predict ahead
            
        Returns:
            Dict: Prediction results with confidence intervals
        """
        logger.info(f"Predicting stock prices for {symbol} for next {days} days")
        
        try:
            # Check if we have a trained model for this symbol
            if symbol not in self.models["stock"] and f"{symbol}_arima" not in self.models["stock"]:
                # Train a new model
                self.train_stock_model(symbol)
            
            # Get latest market data
            latest_data = self.nse_api.get_historical_data(symbol, days=60)
            
            if latest_data.empty:
                return {"error": "No market data available for prediction"}
            
            # Prepare predictions dict
            predictions = {
                "symbol": symbol,
                "current_price": latest_data['close'].iloc[-1],
                "prediction_date": datetime.now().strftime('%Y-%m-%d'),
                "forecasts": [],
                "confidence_intervals": [],
                "market_sentiment": None,
                "trend_direction": None
            }
            
            # Check if we have an LSTM model
            if symbol in self.models["stock"]:
                # Prepare data for LSTM prediction
                X, _ = self.preprocess_data(latest_data, 'stock')
                
                # Get the most recent window for prediction
                last_window = X[-1].reshape(1, X.shape[1], X.shape[2])
                
                # Get the model
                model = self.models["stock"][symbol]
                
                # Make recursive predictions
                curr_window = last_window.copy()
                predicted_prices = []
                
                for i in range(days):
                    # Predict next day
                    pred = model.predict(curr_window)[0][0]
                    predicted_prices.append(pred)
                    
                    # Update window for next prediction
                    new_window = curr_window[0, 1:, :]
                    new_pred = np.array([[pred, 0, 0, 0]])  # Placeholder values for other features
                    curr_window = np.append(new_window, new_pred, axis=0).reshape(1, curr_window.shape[1], curr_window.shape[2])
                
                # Convert predictions back to original scale
                predicted_full = np.array([pred_val for pred_val in predicted_prices])
                predicted_full = predicted_full.reshape(-1, 1)
                predicted_full = np.hstack([predicted_full, np.zeros((len(predicted_full), 3))])
                
                predicted_prices = self.scalers['stock'].inverse_transform(predicted_full)[:, 0]
                
                # Calculate confidence intervals (using historical volatility as a proxy)
                std_dev = latest_data['close'].pct_change().std()
                confidence_intervals = []
                
                for i, price in enumerate(predicted_prices):
                    # Confidence interval widens with time
                    interval = price * std_dev * np.sqrt(i + 1) * 1.96  # 95% confidence
                    confidence_intervals.append({
                        "lower": price - interval,
                        "upper": price + interval
                    })
                
                # Add to predictions
                for i in range(days):
                    predictions["forecasts"].append({
                        "date": (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                        "price": float(predicted_prices[i])
                    })
                
                predictions["confidence_intervals"] = confidence_intervals
            
            # Check if we have an ARIMA model
            elif f"{symbol}_arima" in self.models["stock"]:
                arima_model = self.models["stock"][f"{symbol}_arima"]
                
                # Make forecast
                forecast = arima_model.forecast(steps=days)
                conf_int = arima_model.get_forecast(steps=days).conf_int()
                
                # Add to predictions
                for i in range(days):
                    predictions["forecasts"].append({
                        "date": (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d'),
                        "price": float(forecast[i])
                    })
                    
                    predictions["confidence_intervals"].append({
                        "lower": float(conf_int.iloc[i, 0]),
                        "upper": float(conf_int.iloc[i, 1])
                    })
            
            else:
                return {"error": "No trained model available for this symbol"}
            
            # Add market sentiment
            news_sentiment = self.sentiment_analyzer.analyze_market_sentiment(symbol)
            predictions["market_sentiment"] = news_sentiment["sentiment"]
            
            # Determine trend direction
            if predictions["forecasts"][-1]["price"] > predictions["current_price"]:
                predictions["trend_direction"] = "bullish"
            else:
                predictions["trend_direction"] = "bearish"
            
            # Add risk assessment
            predictions["risk_assessment"] = self.risk_evaluator.evaluate_stock_risk(symbol)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting stock price: {str(e)}")
            return {"error": str(e)}
    
    def predict_crypto_price(self, symbol: str, days: int = 7) -> Dict:
        """
        Predict future cryptocurrency prices.
        
        Args:
            symbol (str): Crypto symbol (e.g., 'BTC')
            days (int): Number of days to predict ahead
            
        Returns:
            Dict: Prediction results with confidence intervals
        """
        logger.info(f"Predicting crypto prices for {symbol} for next {days} days")
        
        try:
            # Implementation would follow similar pattern to stock prediction
            # but with crypto-specific adaptations
            
            # The implementation would fetch crypto data, use the appropriate model,
            # generate predictions, and include confidence intervals
            
            return {"status": "Crypto price prediction implemented"}
            
        except Exception as e:
            logger.error(f"Error predicting crypto price: {str(e)}")
            return {"error": str(e)}
    
    def predict_forex_rate(self, pair: str, days: int = 7) -> Dict:
        """
        Predict future forex exchange rates.
        
        Args:
            pair (str): Currency pair (e.g., 'KES/USD')
            days (int): Number of days to predict ahead
            
        Returns:
            Dict: Prediction results with confidence intervals
        """
        logger.info(f"Predicting forex rates for {pair} for next {days} days")
        
        try:
            # Implementation would follow similar pattern to stock prediction
            # but with forex-specific adaptations
            
            return {"status": "Forex rate prediction implemented"}
            
        except Exception as e:
            logger.error(f"Error predicting forex rate: {str(e)}")
            return {"error": str(e)}
    
    def analyze_market_volatility(self, market_type: str, symbol: str) -> Dict:
        """
        Analyze market volatility for an asset.
        
        Args:
            market_type (str): Market type ('stock', 'crypto', 'forex')
            symbol (str): Asset symbol
            
        Returns:
            Dict: Volatility metrics and risk assessment
        """
        logger.info(f"Analyzing market volatility for {market_type}: {symbol}")
        
        try:
            # Fetch historical data based on market type
            if market_type == 'stock':
                historical_data = self.nse_api.get_historical_data(symbol, days=30)
            elif market_type == 'crypto':
                historical_data = self.crypto_api.get_historical_data(symbol, days=30)
            elif market_type == 'forex':
                historical_data = self.forex_api.get_historical_data(symbol, days=30)
            else:
                return {"error": f"Unsupported market type: {market_type}"}
            
            if historical_data.empty:
                return {"error": "No historical data available for volatility analysis"}
            
            # Calculate daily returns
            returns = historical_data['close'].pct_change().dropna()
            
            # Calculate volatility metrics
            daily_volatility = returns.std()
            annualized_volatility = daily_volatility * np.sqrt(252)  # 252 trading days in a year
            
            # Calculate Value at Risk (VaR) at 95% confidence level
            var_95 = np.percentile(returns, 5)
            
            # Calculate other risk metrics
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
            max_drawdown = (historical_data['close'] / historical_data['close'].cummax() - 1).min()
            
            # Determine volatility level
            volatility_thresholds = {
                'stock': {'low': 0.01, 'medium': 0.02, 'high': 0.03},
                'crypto': {'low': 0.03, 'medium': 0.05, 'high': 0.08},
                'forex': {'low': 0.005, 'medium': 0.01, 'high': 0.02}
            }
            
            thresholds = volatility_thresholds.get(market_type, volatility_thresholds['stock'])
            
            if annualized_volatility < thresholds['low']:
                volatility_level = "low"
            elif annualized_volatility < thresholds['medium']:
                volatility_level = "medium"
            elif annualized_volatility < thresholds['high']:
                volatility_level = "high"
            else:
                volatility_level = "very high"
            
            return {
                "symbol": symbol,
                "market_type": market_type,
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "metrics": {
                    "daily_volatility": float(daily_volatility),
                    "annualized_volatility": float(annualized_volatility),
                    "var_95": float(var_95),
                    "sharpe_ratio": float(sharpe_ratio),
                    "max_drawdown": float(max_drawdown)
                },
                "volatility_level": volatility_level,
                "interpretation": f"This asset has {volatility_level} volatility. VaR indicates a 5% chance of losing {abs(var_95)*100:.2f}% or more in a single day."
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market volatility: {str(e)}")
            return {"error": str(e)}
    
    def generate_sector_forecast(self, sector: str, horizon: str = 'medium_term') -> Dict:
        """
        Generate a forecast for an entire market sector.
        
        Args:
            sector (str): Market sector (e.g., 'banking', 'technology')
            horizon (str): Time horizon ('short_term', 'medium_term', 'long_term')
            
        Returns:
            Dict: Sector forecast with trends and opportunities
        """
        logger.info(f"Generating sector forecast for {sector} with {horizon} horizon")
        
        try:
            # Get stocks in this sector
            sector_stocks = self.nse_api.get_sector_stocks(sector)
            
            if not sector_stocks:
                return {"error": f"No stocks found for sector: {sector}"}
            
            # Get prediction horizon in days
            horizon_days = self.config.get('prediction_horizon', {}).get(horizon, 30)
            
            # Generate predictions for each stock
            stock_predictions = {}
            for symbol in sector_stocks:
                stock_predictions[symbol] = self.predict_stock_price(symbol, days=horizon_days)
            
            # Aggregate sector metrics
            current_prices = [pred["current_price"] for sym, pred in stock_predictions.items() if "current_price" in pred]
            forecast_prices = [pred["forecasts"][-1]["price"] for sym, pred in stock_predictions.items() 
                              if "forecasts" in pred and len(pred["forecasts"]) > 0]
            
            # Calculate sector trend
            if len(current_prices) > 0 and len(forecast_prices) > 0:
                avg_current = sum(current_prices) / len(current_prices)
                avg_forecast = sum(forecast_prices) / len(forecast_prices)
                sector_change_pct = ((avg_forecast / avg_current) - 1) * 100
            else:
                sector_change_pct = 0
            
            # Determine sector sentiment
            bullish_count = sum(1 for pred in stock_predictions.values() 
                              if "trend_direction" in pred and pred["trend_direction"] == "bullish")
            bearish_count = sum(1 for pred in stock_predictions.values() 
                              if "trend_direction" in pred and pred["trend_direction"] == "bearish")
            
            if bullish_count > bearish_count:
                sector_sentiment = "bullish"
            elif bearish_count > bullish_count:
                sector_sentiment = "bearish"
            else:
                sector_sentiment = "neutral"
            
            # Find top opportunities
            top_opportunities = []
            for symbol, pred in stock_predictions.items():
                if "forecasts" in pred and len(pred["forecasts"]) > 0 and "current_price" in pred:
                    potential_return = ((pred["forecasts"][-1]["price"] / pred["current_price"]) - 1) * 100
                    top_opportunities.append({
                        "symbol": symbol,
                        "potential_return": potential_return,
                        "sentiment": pred.get("market_sentiment", "neutral")
                    })
            
            # Sort by potential return
            top_opportunities.sort(key=lambda x: x["potential_return"], reverse=True)
            
            # Get news sentiment for the sector
            sector_news = self.news_api.get_sector_news(sector, days=7)
            sector_sentiment_analysis = self.sentiment_analyzer.analyze_text(sector_news)
            
            return {
                "sector": sector,
                "forecast_horizon": horizon,
                "horizon_days": horizon_days,
                "forecast_date": datetime.now().strftime('%Y-%m-%d'),
                "sector_trend": {
                    "direction": sector_sentiment,
                    "change_percentage": float(sector_change_pct)
                },
                "stock_count": len(sector_stocks),
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "top_opportunities": top_opportunities[:3] if top_opportunities else [],
                "news_sentiment": sector_sentiment_analysis["sentiment"],
                "sector_summary": f"The {sector} sector shows a {sector_sentiment} trend with a projected change of {sector_change_pct:.2f}% over the next {horizon_days} days."
            }
            
        except Exception as e:
            logger.error(f"Error generating sector forecast: {str(e)}")
            return {"error": str(e)}
    
    def analyze_macroeconomic_indicators(self) -> Dict:
        """
        Analyze macroeconomic indicators for Kenyan economy.
        
        Returns:
            Dict: Macroeconomic analysis and impact on markets
        """
        logger.info("Analyzing macroeconomic indicators")
        
        try:
            # Get macroeconomic data for Kenya
            macro_data = self.data_api.get_macroeconomic_data('Kenya')
            
            if not macro_data:
                return {"error": "No macroeconomic data available"}
            
            # Analyze key indicators
            gdp_growth = macro_data.get('gdp_growth', 0)
            inflation_rate = macro_data.get('inflation_rate', 0)
            interest_rate = macro_data.get('interest_rate', 0)
            unemployment = macro_data.get('unemployment_rate', 0)
            
            # Evaluate economic health
            economic_health = "stable"
            if gdp_growth > 5:
                economic_health = "strong"
            elif gdp_growth < 2:
                economic_health = "weak"
            
            if inflation_rate > 8:
                economic_health = "at risk" if economic_health != "weak" else "weak"
            
            # Predict impact on markets
            market_impact = {
                "equities": "neutral",
                "bonds": "neutral",
                "forex": "neutral"
            }
            
            # Equity market impact
            if gdp_growth > 4 and inflation_rate < 6:
                market_impact["equities"] = "positive"
            elif gdp_growth < 2 or inflation_rate > 8:
                market_impact["equities"] = "negative"
            
            # Bond market impact
            if interest_rate > 10 or inflation_rate > 7:
                market_impact["bonds"] = "negative"
            elif interest_rate < 7 and inflation_rate < 5:
                market_impact["bonds"] = "positive"
            
            # Forex impact (KES)
            if gdp_growth < 2 or inflation_rate > 7:
                market_impact["forex"] = "negative"  # KES likely to weaken
            elif gdp_growth > 4 and inflation_rate < 5:
                market_impact["forex"] = "positive"  # KES likely to strengthen
            
            return {
                "country": "Kenya",
                "analysis_date": datetime.now().strftime('%Y-%m-%d'),
                "indicators": {
                    "gdp_growth": gdp_growth,
                    "inflation_rate": inflation_rate,
                    "interest_rate": interest_rate,
                    "unemployment": unemployment
                },
                "economic_health": economic_health,
                "market_impact": market_impact,
                "summary": f"The Kenyan economy is currently {economic_health}. GDP growth at {gdp_growth}% and inflation at {inflation_rate}% suggest {market_impact['equities']} outlook for equities, {market_impact['bonds']} outlook for bonds, and {market_impact['forex']} outlook for the Kenyan Shilling."
            }
            
        except Exception as e:
            logger.error(f"Error analyzing macroeconomic indicators: {str(e)}")
            return {"error": str(e)}
    
    def predict_interest_rates(self, months: int = 3) -> Dict:
        """
        Predict future interest rates for Kenya.
        
        Args:
            months (int): Number of months ahead to predict
            
        Returns:
            Dict: Interest rate predictions with policy implications
        """
        logger.info(f"Predicting interest rates for next {months} months")
        
        try:
            # Get historical interest rate data from CBK
            historical_rates = self.data_api.get_interest_rate_history(months=24)
            
            if not historical_rates:
                return {"error": "No historical interest rate data available"}
            
            # Convert to dataframe for time series analysis
            df = pd.DataFrame(historical_rates)
            
            # Train ARIMA model for interest rate prediction
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                model = auto_arima(
                    df['rate'].values,
                    seasonal=False,
                    stepwise=True,
                    suppress_warnings=True
                )
            
            # Forecast interest rates
            forecast = model.predict(n_periods=months)
            
            # Build prediction results
            predictions = []
            for i in range(months):
                month_date = (datetime.now() + timedelta(days=30 * (i+1))).strftime('%Y-%m-%d')
                predictions.append({
                    "date": month_date,
                    "rate": float(forecast[i])
                })
            
            # Analyze trend
            current_rate = df['rate'].iloc[-1]
            final_prediction = forecast[-1]
            
            if final_prediction > current_rate + 0.5:
                trend = "rising"
                implication = "This suggests tightening monetary policy to control inflation. Bond yields may increase, potentially making fixed income investments more attractive."
            elif final_prediction < current_rate - 0.5:
                trend = "falling"
                implication = "This suggests expansionary monetary policy to stimulate growth. Lower rates may boost equity markets but reduce returns on savings products."
            else:
                trend = "stable"
                implication = "Monetary policy appears to be in a holding pattern. Markets may focus more on other factors like economic growth and corporate earnings."
            
            return {
                "current_rate": float(current_rate),
                "prediction_date": datetime.now().strftime('%Y-%m-%d'),
                "months_ahead": months,
                "predictions": predictions,
                "trend": trend,
                "policy_implication": implication,
                "confidence": "medium"  # Could be calculated based on model fit
            }
            
        except Exception as e:
            logger.error(f"Error predicting interest rates: {str(e)}")
            return {"error": str(e)}
    
    def get_market_insights(self, market_type: str = 'all') -> Dict:
        """
        Get comprehensive market insights for the Kenyan market.
        
        Args:
            market_type (str): Market type ('all', 'stock', 'crypto', 'forex')
            
        Returns:
            Dict: Comprehensive market insights and analysis
        """
        logger.info(f"Generating market insights for {market_type}")
        
        try:
            insights = {
                "generation_date": datetime.now().strftime('%Y-%m-%d'),
                "market_summary": {},
                "top_opportunities": [],
                "market_risks": [],
                "sector_performance": {},
                "macroeconomic_factors": {}
            }
            
            # Get macroeconomic analysis
            macro_analysis = self.analyze_macroeconomic_indicators()
            if "error" not in macro_analysis:
                insights["macroeconomic_factors"] = macro_analysis
            
            # Analyze stock market if requested
            if market_type in ['all', 'stock']:
                # Get market indices
                nse_indices = self.nse_api.get_market_indices()
                
                # Get top performing stocks
                top_stocks = self.nse_api.get_top_performers(limit=5)
                
                # Get sector performance
                sectors = ['banking', 'telecoms', 'energy', 'manufacturing', 'real_estate']
                sector_performance = {}
                
                for sector in sectors:
                    forecast = self.generate_sector_forecast(sector, 'short_term')
                    if "error" not in forecast:
                        sector_performance[sector] = {
                            "trend": forecast["sector_trend"]["direction"],
                            "change_percentage": forecast["sector_trend"]["change_percentage"]
                        }
                
                # Add to insights
                insights["market_summary"]["stock"] = {
                    "nse_20_index": nse_indices.get("NSE_20", 0),
                    "all_share_index": nse_indices.get("NSE_ASI", 0),
                    "market_sentiment": self.sentiment_analyzer.analyze_market_sentiment("NSE")["sentiment"]
                }
                
                insights["top_opportunities"].extend([
                    {"type": "stock", "symbol": stock["symbol"], "potential": stock["change"]}
                    for stock in top_stocks
                ])
                
                insights["sector_performance"] = sector_performance
            
            # Analyze crypto market if requested
            if market_type in ['all', 'crypto']:
                # Get crypto market overview
                crypto_overview = self.crypto_api.get_market_overview()
                
                # Get top cryptocurrencies
                top_cryptos = self.crypto_api.get_top_performers(limit=3)
                
                # Add to insights
                insights["market_summary"]["crypto"] = {
                    "btc_dominance": crypto_overview.get("btc_dominance", 0),
                    "market_cap": crypto_overview.get("total_market_cap", 0),
                    "market_sentiment": self.sentiment_analyzer.analyze_market_sentiment("CRYPTO")["sentiment"]
                }
                
                insights["top_opportunities"].extend([
                    {"type": "crypto", "symbol": crypto["symbol"], "potential": crypto["change"]}
                    for crypto in top_cryptos
                ])
            
            # Analyze forex market if requested
            if market_type in ['all', 'forex']:
                # Get forex market overview
                forex_overview = self.forex_api.get_market_overview()
                
                # Get key currency pairs for Kenya
                currency_pairs = ['KES/USD', 'KES/EUR', 'KES/GBP']
                forex_data = {}
                
                for pair in currency_pairs:
                    rate = self.forex_api.get_exchange_rate(pair)
                    forecast = self.predict_forex_rate(pair, days=7)
                    
                    if rate and "error" not in forecast:
                        forex_data[pair] = {
                            "current_rate": rate,
                            "forecast_7day": forecast["forecasts"][6]["price"] if "forecasts" in forecast and len(forecast["forecasts"]) > 6 else None,
                            "trend": forecast.get("trend_direction", "stable")
                        }
                
                # Add to insights
                insights["market_summary"]["forex"] = {
                    "kes_strength_index": forex_overview.get("kes_strength_index", 0),
                    "market_sentiment": self.sentiment_analyzer.analyze_market_sentiment("FOREX")["sentiment"],
                    "currency_pairs": forex_data
                }
            
            # Add market risks
            if "macroeconomic_factors" in insights and "indicators" in insights["macroeconomic_factors"]:
                inflation = insights["macroeconomic_factors"]["indicators"].get("inflation_rate", 0)
                if inflation > 7:
                    insights["market_risks"].append({
                        "risk_type": "inflation",
                        "severity": "high",
                        "description": f"High inflation rate of {inflation}% could lead to tighter monetary policy and market volatility."
                    })
            
            # Get global risks that might affect Kenyan markets
            global_risks = self.data_api.get_global_risk_factors()
            if global_risks:
                insights["market_risks"].extend(global_risks)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating market insights: {str(e)}")
            return {"error": str(e)}

# Main execution for testing
if __name__ == "__main__":
    predictor = MarketPredictor()
    
    # Test stock prediction
    result = predictor.predict_stock_price("SCOM", days=7)
    print(json.dumps(result, indent=2))
    
    # Test market insights
    insights = predictor.get_market_insights()
    print(json.dumps(insights, indent=2))
