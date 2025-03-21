import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
import logging
import json
import os
import requests
from datetime import datetime, timedelta
import warnings

# Suppress specific deprecation warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import internal modules
try:
    from ..services import market_data_api, risk_evaluation, sentiment_analysis
except ImportError:
    logger.warning("Unable to import internal modules directly. Using alternate import path.")
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services import market_data_api, risk_evaluation, sentiment_analysis


class PortfolioAI:
    """Main class for portfolio AI functionality and optimization strategies."""
    
    def __init__(self, user_id=None, risk_profile=None):
        """
        Initialize the Portfolio AI service with user context if available.
        
        Args:
            user_id (str, optional): User ID for personalized recommendations
            risk_profile (dict, optional): User's risk profile information
        """
        self.user_id = user_id
        self.risk_profile = risk_profile
        self.market_data = market_data_api.MarketDataAPI()
        self.risk_service = risk_evaluation.RiskEvaluation()
        self.sentiment_service = sentiment_analysis.SentimentAnalysis()
        
        # Load model configurations
        self._load_configs()
        
        # Initialize ML models
        self._initialize_models()

    def _load_configs(self):
        """Load configuration settings for portfolio management."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "portfolio_config.json"
            )
            
            with open(config_path, 'r') as f:
                self.config = json.load(f)
                
            # Set default asset classes and allocations
            self.asset_classes = self.config.get('asset_classes', {
                'stocks': {'min': 0, 'max': 0.8},
                'bonds': {'min': 0.1, 'max': 0.7},
                'cash': {'min': 0.05, 'max': 0.3},
                'alternative': {'min': 0, 'max': 0.2}
            })
            
            # Define Kenyan market specifics
            self.kenyan_market = self.config.get('kenyan_market', {
                'nse_indices': ['NSE 20', 'NSE 25', 'NASI'],
                'sectors': ['Banking', 'Energy', 'Manufacturing', 'Telecom'],
                'local_bonds': ['T-Bills', 'T-Bonds', 'Corporate Bonds'],
                'alternative': ['Real Estate', 'REITS', 'Private Equity']
            })
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading configuration: {e}")
            # Set default configuration
            self.config = {}
            self.asset_classes = {
                'stocks': {'min': 0, 'max': 0.8},
                'bonds': {'min': 0.1, 'max': 0.7},
                'cash': {'min': 0.05, 'max': 0.3},
                'alternative': {'min': 0, 'max': 0.2}
            }
            self.kenyan_market = {
                'nse_indices': ['NSE 20', 'NSE 25', 'NASI'],
                'sectors': ['Banking', 'Energy', 'Manufacturing', 'Telecom'],
                'local_bonds': ['T-Bills', 'T-Bonds', 'Corporate Bonds'],
                'alternative': ['Real Estate', 'REITS', 'Private Equity'],
                'top_stocks': [
                    'Safaricom PLC', 
                    'Equity Group Holdings', 
                    'KCB Group', 
                    'EABL', 
                    'BAT Kenya',
                    'Cooperative Bank'
                ]
            }

    def _initialize_models(self):
        """Initialize machine learning models for portfolio optimization."""
        # Market prediction model (Random Forest)
        self.market_prediction_model = RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
        
        # Risk prediction model (Gradient Boosting)
        self.risk_prediction_model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.05,
            random_state=42
        )
        
        # For deep learning models, initialize the structure but don't train yet
        self.deep_learning_model = None

    def optimize_portfolio(self, assets, expected_returns, covariance_matrix, 
                          risk_tolerance, constraints=None):
        """
        Optimize portfolio using Modern Portfolio Theory (Markowitz model).
        
        Args:
            assets (list): List of asset identifiers
            expected_returns (numpy.array): Expected returns for each asset
            covariance_matrix (numpy.array): Covariance matrix of asset returns
            risk_tolerance (float): Risk tolerance factor (0-1)
            constraints (dict, optional): Additional portfolio constraints
            
        Returns:
            dict: Optimized portfolio weights and metrics
        """
        n_assets = len(assets)
        
        # Default initial weights: equal allocation
        initial_weights = np.ones(n_assets) / n_assets
        
        # Define bounds based on constraints or defaults
        if constraints and 'bounds' in constraints:
            bounds = constraints['bounds']
        else:
            # Default bounds: 0-1 for each asset
            bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Portfolio return function
        def portfolio_return(weights):
            return np.sum(weights * expected_returns)
        
        # Portfolio volatility function
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
        
        # Portfolio Sharpe ratio (negative for minimization)
        def negative_sharpe_ratio(weights):
            # Using risk-free rate from Kenya T-bills (placeholder)
            risk_free_rate = 0.07
            portfolio_ret = portfolio_return(weights)
            portfolio_vol = portfolio_volatility(weights)
            return -(portfolio_ret - risk_free_rate) / portfolio_vol
        
        # Portfolio utility function (balancing return and risk)
        def portfolio_utility(weights):
            portfolio_ret = portfolio_return(weights)
            portfolio_vol = portfolio_volatility(weights)
            # Higher risk_tolerance values place more emphasis on returns vs. risk
            return -(portfolio_ret - (1-risk_tolerance) * portfolio_vol)
        
        # Constraint: weights sum to 1
        constraints = [{'type': 'eq', 'fun': lambda weights: np.sum(weights) - 1}]
        
        # If user has a very low risk tolerance, minimize volatility
        if risk_tolerance < 0.2:
            optimization_result = minimize(
                portfolio_volatility, 
                initial_weights, 
                method='SLSQP', 
                bounds=bounds, 
                constraints=constraints
            )
        # If user has a very high risk tolerance, maximize return
        elif risk_tolerance > 0.8:
            optimization_result = minimize(
                lambda weights: -portfolio_return(weights), 
                initial_weights, 
                method='SLSQP', 
                bounds=bounds, 
                constraints=constraints
            )
        # Otherwise, maximize Sharpe ratio (risk-adjusted return)
        else:
            optimization_result = minimize(
                negative_sharpe_ratio, 
                initial_weights, 
                method='SLSQP', 
                bounds=bounds, 
                constraints=constraints
            )
        
        # Extract optimized weights
        optimized_weights = optimization_result['x']
        
        # Calculate portfolio metrics
        expected_portfolio_return = portfolio_return(optimized_weights)
        expected_portfolio_volatility = portfolio_volatility(optimized_weights)
        sharpe_ratio = (expected_portfolio_return - 0.07) / expected_portfolio_volatility
        
        # Create a dictionary mapping assets to their weights
        portfolio_allocation = {assets[i]: round(optimized_weights[i], 4) 
                              for i in range(n_assets)}
        
        # Return portfolio details
        return {
            'allocation': portfolio_allocation,
            'expected_return': round(expected_portfolio_return, 4),
            'expected_volatility': round(expected_portfolio_volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'optimization_success': optimization_result['success']
        }

    def black_litterman_optimization(self, market_capitalization, covariance_matrix, 
                                    views, uncertainty, market_return, risk_aversion=2.5):
        """
        Implement Black-Litterman model for portfolio optimization, incorporating investor views.
        
        Args:
            market_capitalization (numpy.array): Market cap weights of assets
            covariance_matrix (numpy.array): Covariance matrix of asset returns
            views (dict): Dictionary of views on specific assets or asset pairs
            uncertainty (float): Confidence level in investor views (0-1)
            market_return (float): Expected market return
            risk_aversion (float, optional): Risk aversion coefficient
            
        Returns:
            dict: Optimized portfolio based on Black-Litterman model
        """
        # Implementation of Black-Litterman model
        # This is a simplified version for the example
        
        n_assets = len(market_capitalization)
        
        # Step 1: Calculate implied equilibrium returns
        implied_returns = risk_aversion * np.dot(covariance_matrix, market_capitalization)
        
        # Step 2: Incorporate investor views
        # Convert views to matrix form
        P = np.zeros((len(views), n_assets))
        Q = np.zeros(len(views))
        
        for i, (view_assets, view_return) in enumerate(views.items()):
            # Single asset view
            if isinstance(view_assets, str):
                asset_idx = list(market_capitalization.keys()).index(view_assets)
                P[i, asset_idx] = 1
                Q[i] = view_return
            # Relative view (asset1 vs asset2)
            elif isinstance(view_assets, tuple) and len(view_assets) == 2:
                asset1_idx = list(market_capitalization.keys()).index(view_assets[0])
                asset2_idx = list(market_capitalization.keys()).index(view_assets[1])
                P[i, asset1_idx] = 1
                P[i, asset2_idx] = -1
                Q[i] = view_return
        
        # Step 3: Calculate posterior expected returns
        # Uncertainty in views
        omega = uncertainty * np.eye(len(views))
        posterior_returns = np.linalg.inv(
            np.linalg.inv(risk_aversion * covariance_matrix) + 
            np.dot(P.T, np.dot(np.linalg.inv(omega), P))
        ).dot(
            np.dot(np.linalg.inv(risk_aversion * covariance_matrix), implied_returns) + 
            np.dot(P.T, np.dot(np.linalg.inv(omega), Q))
        )
        
        # Step 4: Use the posterior returns in standard mean-variance optimization
        optimized_portfolio = self.optimize_portfolio(
            assets=list(market_capitalization.keys()),
            expected_returns=posterior_returns,
            covariance_matrix=covariance_matrix,
            risk_tolerance=0.5  # Moderate risk tolerance as default
        )
        
        return optimized_portfolio

    def reinforcement_learning_portfolio(self, market_data, initial_portfolio, 
                                        time_horizon, risk_profile):
        """
        Portfolio optimization using reinforcement learning.
        
        This is a placeholder for a more complex RL implementation.
        In a real implementation, this would use a trained RL agent
        to make sequential investment decisions.
        
        Args:
            market_data (pd.DataFrame): Historical market data
            initial_portfolio (dict): Starting portfolio allocation
            time_horizon (int): Investment horizon in days
            risk_profile (dict): User's risk profile
            
        Returns:
            dict: RL-optimized portfolio strategy
        """
        # In a real implementation, this would use a pre-trained RL model
        # For now, we'll return a simulated strategy
        
        logger.info("Reinforcement learning portfolio optimization (placeholder)")
        
        # Simulate a portfolio strategy based on risk profile
        risk_score = risk_profile.get('risk_score', 5)  # 1-10 scale
        
        # Adjust allocations based on risk tolerance
        if risk_score < 4:  # Conservative
            strategy = {
                'stocks': 0.3,
                'bonds': 0.5,
                'cash': 0.15,
                'alternative': 0.05
            }
        elif risk_score < 7:  # Moderate
            strategy = {
                'stocks': 0.5,
                'bonds': 0.3,
                'cash': 0.1,
                'alternative': 0.1
            }
        else:  # Aggressive
            strategy = {
                'stocks': 0.7,
                'bonds': 0.1,
                'cash': 0.05,
                'alternative': 0.15
            }
            
        # Add simple rebalancing strategy
        rebalancing = {
            'frequency': 'quarterly',
            'threshold': 0.05  # Rebalance when allocation deviates by 5%
        }
        
        return {
            'initial_allocation': strategy,
            'rebalancing_strategy': rebalancing,
            'expected_return': 0.08 + (risk_score - 5) * 0.01,  # Simplified return model
            'confidence_level': 0.7  # Indicating this is a simplified placeholder
        }

    def predict_asset_returns(self, assets, time_horizon=30, use_deep_learning=False):
        """
        Predict future returns for given assets using ML models.
        
        Args:
            assets (list): List of asset identifiers
            time_horizon (int): Prediction horizon in days
            use_deep_learning (bool): Whether to use deep learning models
            
        Returns:
            dict: Predicted returns for each asset
        """
        predictions = {}
        
        for asset in assets:
            try:
                # Fetch historical data
                historical_data = self.market_data.get_asset_history(
                    asset_id=asset,
                    days=180  # Use 6 months of historical data
                )
                
                if historical_data.empty:
                    logger.warning(f"No historical data available for {asset}")
                    predictions[asset] = None
                    continue
                
                # Feature engineering
                features = self._engineer_features(historical_data)
                
                # Make prediction using appropriate model
                if use_deep_learning and self.deep_learning_model:
                    # Deep learning prediction (placeholder)
                    pred_return = 0.05  # Default placeholder
                else:
                    # Use Random Forest model
                    # In a real implementation, this would use a trained model
                    # For now, we'll use a simple heuristic based on recent performance
                    recent_returns = historical_data['return'].tail(30).mean()
                    market_sentiment = self.sentiment_service.get_asset_sentiment(asset)
                    
                    # Adjust based on sentiment
                    sentiment_factor = 1 + (market_sentiment['score'] * 0.2)
                    pred_return = recent_returns * sentiment_factor
                
                predictions[asset] = round(pred_return, 4)
                
            except Exception as e:
                logger.error(f"Error predicting returns for {asset}: {e}")
                predictions[asset] = None
        
        return predictions

    def _engineer_features(self, data):
        """
        Engineer features for ML models from financial time series data.
        
        Args:
            data (pd.DataFrame): Historical financial data
            
        Returns:
            pd.DataFrame: Engineered features
        """
        features = data.copy()
        
        # Calculate technical indicators
        # Moving averages
        features['ma_5'] = data['close'].rolling(window=5).mean()
        features['ma_20'] = data['close'].rolling(window=20).mean()
        features['ma_50'] = data['close'].rolling(window=50).mean()
        
        # Relative Strength Index (RSI)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        features['bb_middle'] = data['close'].rolling(window=20).mean()
        stddev = data['close'].rolling(window=20).std()
        features['bb_upper'] = features['bb_middle'] + (stddev * 2)
        features['bb_lower'] = features['bb_middle'] - (stddev * 2)
        
        # MACD
        features['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
        features['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
        features['macd'] = features['ema_12'] - features['ema_26']
        features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
        
        # Volume indicators
        features['volume_ma_5'] = data['volume'].rolling(window=5).mean()
        features['volume_change'] = data['volume'].pct_change()
        
        # Volatility
        features['volatility'] = data['close'].rolling(window=20).std()
        
        # Drop NaN values
        features = features.dropna()
        
        return features

    def calculate_var(self, portfolio, confidence_level=0.95, time_horizon=10):
        """
        Calculate Value at Risk (VaR) for a portfolio.
        
        Args:
            portfolio (dict): Portfolio with assets and weights
            confidence_level (float): Confidence level for VaR calculation
            time_horizon (int): Time horizon in days
            
        Returns:
            dict: VaR metrics
        """
        # Get historical data for all assets
        asset_histories = {}
        for asset, weight in portfolio.items():
            try:
                history = self.market_data.get_asset_history(
                    asset_id=asset,
                    days=252  # Use 1 year of trading days
                )
                
                if not history.empty:
                    # Calculate daily returns
                    asset_histories[asset] = history['close'].pct_change().dropna()
            except Exception as e:
                logger.error(f"Error fetching history for {asset}: {e}")
        
        if not asset_histories:
            return {
                'var': None,
                'cvar': None,
                'error': 'Insufficient historical data'
            }
        
        # Combine asset returns weighted by portfolio allocation
        combined_returns = pd.DataFrame()
        for asset, returns in asset_histories.items():
            weight = portfolio.get(asset, 0)
            combined_returns[asset] = returns * weight
        
        # Sum across assets to get portfolio returns
        portfolio_returns = combined_returns.sum(axis=1)
        
        # Calculate VaR using historical method
        var_percentile = 1 - confidence_level
        var_daily = portfolio_returns.quantile(var_percentile)
        
        # Scale to the specified time horizon (assuming normal distribution)
        var_horizon = var_daily * np.sqrt(time_horizon)
        
        # Calculate Conditional VaR (CVaR/Expected Shortfall)
        cvar_daily = portfolio_returns[portfolio_returns <= var_daily].mean()
        cvar_horizon = cvar_daily * np.sqrt(time_horizon)
        
        # Calculate portfolio value for interpretation
        portfolio_value = 1000000  # Assuming 1M KES for illustration
        
        return {
            'var_percent': round(float(-var_horizon * 100), 2),
            'var_amount': round(float(-var_horizon * portfolio_value), 2),
            'cvar_percent': round(float(-cvar_horizon * 100), 2),
            'cvar_amount': round(float(-cvar_horizon * portfolio_value), 2),
            'confidence_level': confidence_level,
            'time_horizon': time_horizon,
            'interpretation': f"With {confidence_level*100}% confidence, the maximum loss over {time_horizon} days will not exceed {round(float(-var_horizon * 100), 2)}% (KES {round(float(-var_horizon * portfolio_value), 2):,})"
        }

    def stress_test_portfolio(self, portfolio, scenarios=None):
        """
        Perform stress testing on a portfolio under various scenarios.
        
        Args:
            portfolio (dict): Portfolio with assets and weights
            scenarios (list, optional): List of scenarios to test
            
        Returns:
            dict: Stress test results
        """
        # Default scenarios if none provided
        if not scenarios:
            scenarios = [
                {
                    'name': 'Market Crash',
                    'description': 'Severe market downturn similar to 2008',
                    'impacts': {
                        'stocks': -0.40,  # 40% drop
                        'bonds': -0.05,   # 5% drop
                        'cash': 0,
                        'alternative': -0.20  # 20% drop
                    }
                },
                {
                    'name': 'Economic Recession',
                    'description': 'Prolonged economic slowdown',
                    'impacts': {
                        'stocks': -0.25,
                        'bonds': -0.10,
                        'cash': 0,
                        'alternative': -0.15
                    }
                },
                {
                    'name': 'Interest Rate Hike',
                    'description': 'Significant increase in interest rates',
                    'impacts': {
                        'stocks': -0.15,
                        'bonds': -0.20,
                        'cash': 0.01,
                        'alternative': -0.05
                    }
                },
                {
                    'name': 'Currency Devaluation',
                    'description': 'Kenyan Shilling loses 20% value',
                    'impacts': {
                        'stocks': -0.05,
                        'bonds': -0.15,
                        'cash': -0.20,
                        'alternative': 0.10
                    }
                }
            ]
        
        results = {}
        portfolio_value = 1000000  # Assuming 1M KES for illustration
        
        for scenario in scenarios:
            scenario_impact = 0
            asset_impacts = {}
            
            # Calculate impact for each asset in the portfolio
            for asset, weight in portfolio.items():
                # Determine asset class (simplified)
                asset_class = self._determine_asset_class(asset)
                
                # Apply impact based on asset class
                impact_pct = scenario['impacts'].get(asset_class, 0)
                asset_impact = weight * impact_pct
                scenario_impact += asset_impact
                
                # Record individual asset impact
                asset_impacts[asset] = {
                    'percent': round(impact_pct * 100, 2),
                    'value_change': round(weight * portfolio_value * impact_pct, 2)
                }
            
            # Record scenario results
            results[scenario['name']] = {
                'description': scenario['description'],
                'total_impact_percent': round(scenario_impact * 100, 2),
                'total_impact_value': round(scenario_impact * portfolio_value, 2),
                'asset_impacts': asset_impacts,
                'new_portfolio_value': round(portfolio_value * (1 + scenario_impact), 2)
            }
        
        return results

    def _determine_asset_class(self, asset):
        """
        Determine the asset class for a given asset.
        
        Args:
            asset (str): Asset identifier
            
        Returns:
            str: Asset class category
        """
        # This is a simplified mapping - in reality would use a more robust approach
        asset_lower = asset.lower()
        
        # Check if this is a stock/equity
        if any(term in asset_lower for term in ['stock', 'share', 'equity']):
            return 'stocks'
        
        # Check if this is a bond
        elif any(term in asset_lower for term in ['bond', 'bill', 'note', 'treasury']):
            return 'bonds'
        
        # Check if this is cash or equivalent
        elif any(term in asset_lower for term in ['cash', 'money market', 'savings']):
            return 'cash'
        
        # Check if this is an alternative investment
        elif any(term in asset_lower for term in 
                ['real estate', 'reit', 'commodity', 'crypto', 'hedge', 'private equity']):
            return 'alternative'
        
        # Check for common Kenyan stocks
        elif any(stock.lower() in asset_lower for stock in 
                ['safaricom', 'equity', 'kcb', 'eabl', 'bat', 'cooperative']):
            return 'stocks'
        
        # Default to stocks if unknown
        else:
            return 'stocks'
            
    def _estimate_rebalancing_cost(self, recommendations, portfolio_value):
        """
        Estimate the cost of implementing rebalancing recommendations.
        
        Args:
            recommendations (list): List of rebalancing recommendations
            portfolio_value (float): Total portfolio value
            
        Returns:
            dict: Estimated rebalancing costs
        """
        # Calculate total transaction value
        total_transaction_value = sum(rec['adjustment_value'] for rec in recommendations)
        
        # Estimate trading costs
        # NSE typical costs: 1.5% brokerage, 0.3% other fees (simplified)
        brokerage_fee = total_transaction_value * 0.015
        regulatory_fees = total_transaction_value * 0.003
        
        # Total cost
        total_cost = brokerage_fee + regulatory_fees
        cost_percent = (total_cost / portfolio_value) * 100 if portfolio_value > 0 else 0
        
        return {
            'transaction_value': round(total_transaction_value, 2),
            'brokerage_fee': round(brokerage_fee, 2),
            'regulatory_fees': round(regulatory_fees, 2),
            'total_cost': round(total_cost, 2),
            'cost_percent': round(cost_percent, 2),
            'note': 'Estimated based on typical NSE transaction costs'
        }

    def get_portfolio_recommendation(self, user_id, risk_profile, investment_amount, 
                                    time_horizon, financial_goals=None):
        """
        Generate a personalized portfolio recommendation based on user profile.
        
        Args:
            user_id (str): User identifier
            risk_profile (dict): User's risk profile
            investment_amount (float): Amount to invest in KES
            time_horizon (int): Investment horizon in years
            financial_goals (list, optional): List of financial goals
            
        Returns:
            dict: Personalized portfolio recommendation
        """
        # Get risk score from profile
        risk_score = risk_profile.get('risk_score', 5)  # 1-10 scale
        
        # Adjust allocations based on risk tolerance and time horizon
        if risk_score < 4:  # Conservative
            if time_horizon < 2:
                allocation = {
                    'stocks': 0.15,
                    'bonds': 0.55,
                    'cash': 0.25,
                    'alternative': 0.05
                }
            elif time_horizon < 5:
                allocation = {
                    'stocks': 0.30,
                    'bonds': 0.50,
                    'cash': 0.15,
                    'alternative': 0.05
                }
            else:
                allocation = {
                    'stocks': 0.40,
                    'bonds': 0.45,
                    'cash': 0.10,
                    'alternative': 0.05
                }
        elif risk_score < 7:  # Moderate
            if time_horizon < 2:
                allocation = {
                    'stocks': 0.30,
                    'bonds': 0.45,
                    'cash': 0.20,
                    'alternative': 0.05
                }
            elif time_horizon < 5:
                allocation = {
                    'stocks': 0.50,
                    'bonds': 0.30,
                    'cash': 0.10,
                    'alternative': 0.10
                }
            else:
                allocation = {
                    'stocks': 0.60,
                    'bonds': 0.25,
                    'cash': 0.05,
                    'alternative': 0.10
                }
        else:  # Aggressive
            if time_horizon < 2:
                allocation = {
                    'stocks': 0.50,
                    'bonds': 0.30,
                    'cash': 0.15,
                    'alternative': 0.05
                }
            elif time_horizon < 5:
                allocation = {
                    'stocks': 0.65,
                    'bonds': 0.20,
                    'cash': 0.05,
                    'alternative': 0.10
                }
            else:
                allocation = {
                    'stocks': 0.75,
                    'bonds': 0.10,
                    'cash': 0.05,
                    'alternative': 0.10
                }
        
        # Convert high-level allocation to specific investment recommendations
        specific_investments = self._get_specific_investments(allocation, investment_amount)
        
        # Calculate expected returns, volatility, etc.
        expected_annual_return = 0.05 + (risk_score * 0.005)  # Simple linear model
        expected_volatility = 0.03 + (risk_score * 0.01)  # Simple linear model
        
        # Calculate projected growth
        projected_growth = self._calculate_projected_growth(
            investment_amount, 
            expected_annual_return, 
            time_horizon
        )
        
        # VaR calculation
        var_result = self.calculate_var(
            {inv['name']: inv['weight'] for inv in specific_investments},
            confidence_level=0.95,
            time_horizon=30  # 30 days
        )
        
        return {
            'user_id': user_id,
            'investment_amount': investment_amount,
            'time_horizon_years': time_horizon,
            'risk_profile': {
                'score': risk_score,
                'category': self._risk_score_to_category(risk_score)
            },
            'allocation_strategy': allocation,
            'specific_investments': specific_investments,
            'expected_metrics': {
                'annual_return': round(expected_annual_return * 100, 2),
                'volatility': round(expected_volatility * 100, 2),
                'sharpe_ratio': round((expected_annual_return - 0.07) / expected_volatility, 2)
            },
            'projected_growth': projected_growth,
            'risk_metrics': var_result,
            'recommendation_date': datetime.now().strftime('%Y-%m-%d'),
            'rebalancing_frequency': 'Quarterly',
            'local_market_context': self._get_local_market_context()
        }

    def _get_specific_investments(self, allocation, investment_amount):
        """
        Convert high-level asset allocation to specific investment recommendations.
        
        Args:
            allocation (dict): High-level asset allocation percentages
            investment_amount (float): Amount to invest
            
        Returns:
            list: Specific investment recommendations
        """
        specific_investments = []
        
        # Stocks allocation
        if 'stocks' in allocation and allocation['stocks'] > 0:
            stock_amount = investment_amount * allocation['stocks']
            
            # NSE stocks (Kenya-specific)
            specific_investments.append({
                'name': 'Safaricom PLC',
                'ticker': 'SCOM.NR',
                'type': 'stock',
                'amount': round(stock_amount * 0.3, 2),
                'weight': round(allocation['stocks'] * 0.3, 4),
                'description': 'Leading telecom provider in Kenya'
            })
            
            specific_investments.append({
                'name': 'Equity Group Holdings',
                'ticker': 'EQTY.NR',
                'type': 'stock',
                'amount': round(stock_amount * 0.2, 2),
                'weight': round(allocation['stocks'] * 0.2, 4),
                'description': 'Major East African banking group'
            })
            
            specific_investments.append({
                'name': 'NSE Index Fund',
                'ticker': 'NSE-IDX',
                'type': 'etf',
                'amount': round(stock_amount * 0.5, 2),
                'weight': round(allocation['stocks'] * 0.5, 4),
                'description': 'Tracks the Nairobi Securities Exchange indices'
            })
            
        # Bonds allocation
        if 'bonds' in allocation and allocation['bonds'] > 0:
            bond_amount = investment_amount * allocation['bonds']
            
            specific_investments.append({
                'name': 'Kenya 10-Year Treasury Bond',
                'ticker': 'KE10Y',
                'type': 'government_bond',
                'amount': round(bond_amount * 0.6, 2),
                'weight': round(allocation['bonds'] * 0.6, 4),
                'description': 'Long-term government bond with ~12% yield'
            })
            
            specific_investments.append({
                'name': 'Kenya 1-Year Treasury Bill',
                'ticker': 'KE1Y',
                'type': 'government_bill',
                'amount': round(bond_amount * 0.4, 2),
                'weight': round(allocation['bonds'] * 0.4, 4),
                'description': 'Short-term government bill with ~9% yield'
            })
        
        # Cash allocation
        if 'cash' in allocation and allocation['cash'] > 0:
            cash_amount = investment_amount * allocation['cash']
            
            specific_investments.append({
                'name': 'Money Market Fund',
                'ticker': 'MMF-KE',
                'type': 'money_market',
                'amount': round(cash_amount, 2),
                'weight': round(allocation['cash'], 4),
                'description': 'Liquid money market fund with ~8% yield'
            })
        
        # Alternative allocation
        if 'alternative' in allocation and allocation['alternative'] > 0:
            alt_amount = investment_amount * allocation['alternative']
            
            specific_investments.append({
                'name': 'Stanlib Fahari I-REIT',
                'ticker': 'FAHR.NR',
                'type': 'reit',
                'amount': round(alt_amount * 0.7, 2),
                'weight': round(allocation['alternative'] * 0.7, 4),
                'description': 'Real Estate Investment Trust on the NSE'
            })
            
            specific_investments.append({
                'name': 'Gold ETF',
                'ticker': 'GOLD-ETF',
                'type': 'commodity',
                'amount': round(alt_amount * 0.3, 2),
                'weight': round(allocation['alternative'] * 0.3, 4),
                'description': 'Gold-backed exchange-traded fund'
            })
        
        return specific_investments

    def _risk_score_to_category(self, risk_score):
        """
        Convert numerical risk score to category.
        
        Args:
            risk_score (int): Risk score on a 1-10 scale
            
        Returns:
            str: Risk category
        """
        if risk_score <= 3:
            return 'Conservative'
        elif risk_score <= 6:
            return 'Moderate'
        else:
            return 'Aggressive'
            
    def _get_local_market_context(self):
        """
        Get relevant Kenyan market context for investment recommendations.
        
        Returns:
            dict: Market context information
        """
        try:
            # Get NSE market data
            nse_data = self.market_data.get_market_index('NSE20')
            
            # Get interest rates
            interest_rates = {
                'cbr': 10.0,  # Central Bank Rate (placeholder)
                'tbill_91d': 9.5,  # 91-day T-bill rate (placeholder)
                'tbill_182d': 10.2,  # 182-day T-bill rate (placeholder)
                'tbill_364d': 10.8,  # 364-day T-bill rate (placeholder)
                'inflation': 5.0  # Current inflation rate (placeholder)
            }
            
            # Get forex data
            forex = {
                'usd_kes': 127.5,  # USD to KES exchange rate (placeholder)
                'gbp_kes': 163.2,  # GBP to KES exchange rate (placeholder)
                'eur_kes': 139.8  # EUR to KES exchange rate (placeholder)
            }
            
            # Market sentiment
            market_sentiment = self.sentiment_service.get_market_sentiment()
            
            return {
                'nse_indices': {
                    'nse_20': {
                        'value': nse_data.get('value', 1850),
                        'change_percent': nse_data.get('change_percent', 0.5)
                    }
                },
                'interest_rates': interest_rates,
                'forex_rates': forex,
                'market_sentiment': market_sentiment,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            # Return placeholder data
            return {
                'nse_indices': {
                    'nse_20': {
                        'value': 1850,
                        'change_percent': 0.5
                    }
                },
                'interest_rates': {
                    'cbr': 10.0,
                    'tbill_91d': 9.5,
                    'tbill_182d': 10.2,
                    'tbill_364d': 10.8,
                    'inflation': 5.0
                },
                'forex_rates': {
                    'usd_kes': 127.5,
                    'gbp_kes': 163.2,
                    'eur_kes': 139.8
                },
                'market_sentiment': {
                    'overall': 'Neutral',
                    'score': 0.2  # Range: -1 to 1
                },
                'note': 'Placeholder data',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            }

    def _calculate_projected_growth(self, initial_amount, annual_return, years):
        """
        Calculate projected investment growth.
        
        Args:
            initial_amount (float): Initial investment amount
            annual_return (float): Expected annual return rate
            years (int): Investment horizon in years
            
        Returns:
            dict: Projected growth details
        """
        # Year-by-year projection
        yearly_projection = []
        cumulative_amount = initial_amount
        
        for year in range(1, years + 1):
            interest = cumulative_amount * annual_return
            cumulative_amount += interest
            
            yearly_projection.append({
                'year': year,
                'start_amount': round(cumulative_amount - interest, 2),
                'interest': round(interest, 2),
                'end_amount': round(cumulative_amount, 2)
            })
        
        # Final results
        total_growth = cumulative_amount - initial_amount
        total_growth_percent = (total_growth / initial_amount) * 100
        
        return {
            'initial_investment': initial_amount,
            'final_amount': round(cumulative_amount, 2),
            'total_growth': round(total_growth, 2),
            'total_growth_percent': round(total_growth_percent, 2),
            'yearly_projection': yearly_projection,
            'cagr': round(((cumulative_amount / initial_amount) ** (1 / years) - 1) * 100, 2),
            'inflation_adjusted': {
                'assumed_inflation': 5.0,  # Kenya's typical inflation rate
                'final_amount': round(cumulative_amount / ((1 + 0.05) ** years), 2)
            }
        }

    def get_thematic_portfolios(self):
        """
        Generate thematic investment portfolios based on different themes/sectors.
        
        These are pre-defined investment strategies focused on specific sectors,
        trends, or investment philosophies that might interest Kenyan investors.
        
        Returns:
            dict: Thematic portfolio options
        """
        return {
            'tech_innovation': {
                'name': 'Technology Innovation',
                'description': 'Focus on technology leaders and innovators',
                'allocation': {
                    'Safaricom PLC': 0.40,
                    'Equity Group (Digital Banking)': 0.20,
                    'Tech-focused Mutual Fund': 0.30,
                    'Cash/Money Market': 0.10
                },
                'expected_return': 12.5,
                'risk_level': 'High',
                'min_investment': 50000
            },
            'sustainable_investing': {
                'name': 'Sustainable Investing',
                'description': 'Environmentally and socially responsible investments',
                'allocation': {
                    'KenGen (Renewable Energy)': 0.30,
                    'Green Bonds': 0.35,
                    'Sustainable Real Estate': 0.25,
                    'Cash/Money Market': 0.10
                },
                'expected_return': 9.8,
                'risk_level': 'Moderate',
                'min_investment': 50000
            },
            'infrastructure_development': {
                'name': 'Infrastructure Development',
                'description': 'Investments in Kenya\'s infrastructure growth',
                'allocation': {
                    'Infrastructure Bonds': 0.45,
                    'Cement Companies': 0.20,
                    'Construction Firms': 0.25,
                    'Cash/Money Market': 0.10
                },
                'expected_return': 11.2,
                'risk_level': 'Moderate',
                'min_investment': 75000
            },
            'financial_inclusion': {
                'name': 'Financial Inclusion',
                'description': 'Companies expanding financial access',
                'allocation': {
                    'Equity Group': 0.25,
                    'KCB Group': 0.25,
                    'Microfinance Institutions': 0.20,
                    'Fintech Funds': 0.20,
                    'Cash/Money Market': 0.10
                },
                'expected_return': 10.5,
                'risk_level': 'Moderate',
                'min_investment': 50000
            },
            'agricultural_innovation': {
                'name': 'Agricultural Innovation',
                'description': 'Modern agriculture and food production',
                'allocation': {
                    'Agri-focused Stocks': 0.35,
                    'Agricultural REITs': 0.25,
                    'Food Processing Companies': 0.30,
                    'Cash/Money Market': 0.10
                },
                'expected_return': 9.0,
                'risk_level': 'Moderate-High',
                'min_investment': 50000
            }
        }

    def rebalance_portfolio(self, current_portfolio, target_allocation, threshold=0.05):
        """
        Provide portfolio rebalancing recommendations.
        
        Args:
            current_portfolio (dict): Current portfolio holdings and weights
            target_allocation (dict): Target asset allocation
            threshold (float): Rebalancing threshold (percentage deviation)
            
        Returns:
            dict: Rebalancing recommendations
        """
        rebalancing_needed = False
        recommendations = []
        total_portfolio_value = sum(current_portfolio.values())
        
        # Check each asset for deviation from target
        for asset, target_weight in target_allocation.items():
            current_value = current_portfolio.get(asset, 0)
            current_weight = current_value / total_portfolio_value if total_portfolio_value > 0 else 0
            
            # Calculate deviation
            deviation = current_weight - target_weight
            deviation_percent = abs(deviation) * 100
            
            # Determine if rebalancing is needed
            if abs(deviation) > threshold:
                rebalancing_needed = True
                
                # Calculate adjustment
                target_value = total_portfolio_value * target_weight
                adjustment_value = target_value - current_value
                
                # Create recommendation
                action = 'Buy' if adjustment_value > 0 else 'Sell'
                recommendations.append({
                    'asset': asset,
                    'action': action,
                    'current_weight': round(current_weight * 100, 2),
                    'target_weight': round(target_weight * 100, 2),
                    'deviation': round(deviation_percent, 2),
                    'adjustment_value': round(abs(adjustment_value), 2),
                    'adjustment_percent': round(abs(adjustment_value) / total_portfolio_value * 100, 2)
                })
        
        # Check for missing assets in current portfolio
        for asset, target_weight in target_allocation.items():
            if asset not in current_portfolio and target_weight > 0:
                # This is a new asset to add
                target_value = total_portfolio_value * target_weight
                recommendations.append({
                    'asset': asset,
                    'action': 'Buy (New)',
                    'current_weight': 0,
                    'target_weight': round(target_weight * 100, 2),
                    'deviation': round(target_weight * 100, 2),
                    'adjustment_value': round(target_value, 2),
                    'adjustment_percent': round(target_weight * 100, 2)
                })
                rebalancing_needed = True
        
        # Check for assets to be fully liquidated
        for asset, current_value in current_portfolio.items():
            if asset not in target_allocation and current_value > 0:
                # This asset should be sold completely
                current_weight = current_value / total_portfolio_value
                recommendations.append({
                    'asset': asset,
                    'action': 'Sell (Liquidate)',
                    'current_weight': round(current_weight * 100, 2),
                    'target_weight': 0,
                    'deviation': round(current_weight * 100, 2),
                    'adjustment_value': round(current_value, 2),
                    'adjustment_percent': round(current_weight * 100, 2)
                })
                rebalancing_needed = True
        
        # Sort recommendations by adjustment value (largest first)
        recommendations.sort(key=lambda x: x['adjustment_value'], reverse=True)
        
        return {
            'rebalancing_needed': rebalancing_needed,
            'recommendations': recommendations,
            'total_portfolio_value': round(total_portfolio_value, 2),
            'rebalancing_date': datetime.now().strftime('%Y-%m-%d'),
            'threshold_used': threshold * 100,
            'summary': f"{'Rebalancing recommended' if rebalancing_needed else 'No rebalancing needed'} with {len(recommendations)} adjustments",
            'estimated_cost': self._estimate_rebalancing_cost(recommendations, total_portfolio_value)
        }
