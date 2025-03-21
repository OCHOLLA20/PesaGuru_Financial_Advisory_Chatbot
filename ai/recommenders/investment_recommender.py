
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime
import json
import os

# Import internal modules
from ..services.market_data_api import MarketDataAPI
from ..services.risk_evaluation import RiskEvaluator
from ..services.sentiment_analysis import SentimentAnalyzer
from ..services.user_profiler import UserProfiler
from ..api_integration.nse_api import NSEAPI
from ..api_integration.cbk_api import CBKAPI
from ..api_integration.crypto_api import CryptoAPI
from ..api_integration.forex_api import ForexAPI

# Set up logging
logger = logging.getLogger(__name__)

class InvestmentRecommender:
    """
    Main class for generating personalized investment recommendations
    """
    
    def __init__(self):
        """
        Initialize the InvestmentRecommender with necessary dependencies
        """
        self.market_data = MarketDataAPI()
        self.risk_evaluator = RiskEvaluator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.user_profiler = UserProfiler()
        
        # API integrations for Kenyan market
        self.nse_api = NSEAPI()
        self.cbk_api = CBKAPI()
        self.crypto_api = CryptoAPI()
        self.forex_api = ForexAPI()
        
        # Load Kenya-specific investment options
        self._load_investment_options()
        
        # Initialize recommendation models
        self._initialize_models()
        
        logger.info("InvestmentRecommender initialized successfully")
    
    def _load_investment_options(self):
        """
        Load available investment options specific to Kenya
        """
        try:
            # Path is relative to the project root
            with open('ai/data/kenya_investment_options.json', 'r') as file:
                self.investment_options = json.load(file)
                
            # Structure contains categories like stocks, bonds, funds, etc.
            self.stocks = self.investment_options.get('stocks', [])
            self.bonds = self.investment_options.get('bonds', [])
            self.money_market = self.investment_options.get('money_market', [])
            self.mutual_funds = self.investment_options.get('mutual_funds', [])
            self.etfs = self.investment_options.get('etfs', [])
            self.real_estate = self.investment_options.get('real_estate', [])
            self.crypto = self.investment_options.get('crypto', [])
            self.forex = self.investment_options.get('forex', [])
            self.saccos = self.investment_options.get('saccos', [])  # Kenya-specific
            
            logger.info(f"Loaded {sum(len(v) for v in self.investment_options.values())} Kenyan investment options")
        except Exception as e:
            logger.error(f"Error loading investment options: {str(e)}")
            # Initialize with empty lists if file loading fails
            self.investment_options = {}
            self.stocks = []
            self.bonds = []
            self.money_market = []
            self.mutual_funds = []
            self.etfs = []
            self.real_estate = []
            self.crypto = []
            self.forex = []
            self.saccos = []
    
    def _initialize_models(self):
        """
        Initialize recommendation models and algorithms
        """
        # Define risk-based asset allocation matrices
        # Format: [stocks, bonds, money_market, real_estate, crypto, others]
        self.asset_allocation = {
            'conservative': [0.15, 0.40, 0.30, 0.10, 0.00, 0.05],
            'moderate': [0.35, 0.30, 0.15, 0.10, 0.05, 0.05],
            'aggressive': [0.60, 0.10, 0.05, 0.10, 0.10, 0.05]
        }
        
        # Load any ML models if available
        try:
            # This would load a recommendation model if it exists
            # model_path = 'ai/models/recommendation_model.pkl'
            # self.ml_model = load_model(model_path)
            pass
        except Exception as e:
            logger.warning(f"ML models not loaded: {str(e)}")
    
    def get_recommendations(self, user_id: str, amount: float = None, 
                           time_horizon: str = None, specific_goal: str = None) -> Dict[str, Any]:
        """
        Generate personalized investment recommendations for a user
        
        Args:
            user_id (str): Unique identifier for the user
            amount (float, optional): Amount in KES to invest
            time_horizon (str, optional): Investment time horizon (short, medium, long)
            specific_goal (str, optional): Specific financial goal for this investment
            
        Returns:
            Dict[str, Any]: Structured recommendation response
        """
        try:
            # 1. Get user profile and risk tolerance
            user_profile = self.user_profiler.get_user_profile(user_id)
            risk_profile = self.risk_evaluator.get_risk_profile(user_id)
            
            # Use provided parameters or fallback to profile defaults
            amount = amount or user_profile.get('available_investment', 10000)
            time_horizon = time_horizon or user_profile.get('investment_horizon', 'medium')
            
            # 2. Determine risk category
            risk_category = risk_profile.get('risk_category', 'moderate')
            
            # 3. Get current market sentiment and trends
            market_sentiment = self.sentiment_analyzer.get_market_sentiment()
            
            # 4. Get asset allocation based on risk profile
            allocation = self._get_asset_allocation(risk_category, time_horizon, market_sentiment)
            
            # 5. Generate specific investment recommendations
            recommendations = self._generate_specific_recommendations(
                allocation, amount, user_profile, time_horizon, specific_goal
            )
            
            # 6. Add explanations and educational content
            recommendations = self._enhance_recommendations(recommendations, user_profile)
            
            # 7. Log the recommendation for feedback learning
            self._log_recommendation(user_id, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                'status': 'error',
                'message': 'Unable to generate recommendations at this time',
                'error': str(e)
            }
    
    def _get_asset_allocation(self, risk_category: str, time_horizon: str, 
                             market_sentiment: Dict[str, float]) -> Dict[str, float]:
        """
        Determine optimal asset allocation based on risk and market conditions
        
        Args:
            risk_category (str): User's risk tolerance category
            time_horizon (str): Investment time horizon
            market_sentiment (Dict[str, float]): Current market sentiment scores
            
        Returns:
            Dict[str, float]: Asset allocation percentages
        """
        # Get base allocation from risk profile
        base_allocation = self.asset_allocation.get(risk_category, self.asset_allocation['moderate'])
        
        # Adjust based on time horizon
        time_adjustments = {
            'short': {'stocks': -0.05, 'money_market': 0.05},
            'long': {'stocks': 0.05, 'money_market': -0.05}
        }
        
        # Adjust based on market sentiment
        sentiment_adjustments = {}
        if market_sentiment.get('stocks', 0) > 0.6:  # Positive stock sentiment
            sentiment_adjustments = {'stocks': 0.03, 'bonds': -0.03}
        elif market_sentiment.get('stocks', 0) < 0.4:  # Negative stock sentiment
            sentiment_adjustments = {'stocks': -0.03, 'bonds': 0.03}
            
        # Create allocation dictionary from base percentages
        allocation = {
            'stocks': base_allocation[0],
            'bonds': base_allocation[1],
            'money_market': base_allocation[2],
            'real_estate': base_allocation[3],
            'crypto': base_allocation[4],
            'others': base_allocation[5]
        }
        
        # Apply time horizon adjustments
        if time_horizon in time_adjustments:
            for asset, adj in time_adjustments[time_horizon].items():
                if asset in allocation:
                    allocation[asset] += adj
        
        # Apply sentiment adjustments
        for asset, adj in sentiment_adjustments.items():
            if asset in allocation:
                allocation[asset] += adj
        
        # Ensure allocations are non-negative and sum to 1.0
        for asset in allocation:
            allocation[asset] = max(0, allocation[asset])
        
        total = sum(allocation.values())
        for asset in allocation:
            allocation[asset] /= total
            
        return allocation
    
    def _generate_specific_recommendations(self, allocation: Dict[str, float], 
                                         amount: float, user_profile: Dict[str, Any],
                                         time_horizon: str, specific_goal: str) -> Dict[str, Any]:
        """
        Generate specific investment recommendations based on the asset allocation
        
        Args:
            allocation (Dict[str, float]): Target asset allocation
            amount (float): Amount in KES to invest
            user_profile (Dict[str, Any]): User profile information
            time_horizon (str): Investment time horizon
            specific_goal (str): Specific financial goal
            
        Returns:
            Dict[str, Any]: Structured recommendations
        """
        # Calculate amount per asset class
        amounts = {asset: amount * percentage for asset, percentage in allocation.items()}
        
        recommendations = {
            'summary': {
                'total_amount': amount,
                'risk_profile': user_profile.get('risk_category', 'moderate'),
                'time_horizon': time_horizon,
                'goal': specific_goal,
                'recommendation_date': datetime.now().strftime('%Y-%m-%d')
            },
            'allocation': allocation,
            'specific_recommendations': {}
        }
        
        # Get stock recommendations
        if amounts['stocks'] > 0:
            recommendations['specific_recommendations']['stocks'] = self._recommend_stocks(
                amounts['stocks'], user_profile, time_horizon
            )
            
        # Get bond recommendations
        if amounts['bonds'] > 0:
            recommendations['specific_recommendations']['bonds'] = self._recommend_bonds(
                amounts['bonds'], user_profile, time_horizon
            )
            
        # Get money market recommendations
        if amounts['money_market'] > 0:
            recommendations['specific_recommendations']['money_market'] = self._recommend_money_market(
                amounts['money_market'], user_profile
            )
            
        # Get real estate recommendations
        if amounts['real_estate'] > 0:
            recommendations['specific_recommendations']['real_estate'] = self._recommend_real_estate(
                amounts['real_estate'], user_profile
            )
            
        # Get crypto recommendations
        if amounts['crypto'] > 0:
            recommendations['specific_recommendations']['crypto'] = self._recommend_crypto(
                amounts['crypto'], user_profile
            )
            
        # Get other recommendations (SACCOs, etc.)
        if amounts['others'] > 0:
            recommendations['specific_recommendations']['others'] = self._recommend_others(
                amounts['others'], user_profile
            )
            
        return recommendations
    
    def _recommend_stocks(self, amount: float, user_profile: Dict[str, Any], 
                         time_horizon: str) -> List[Dict[str, Any]]:
        """
        Generate stock recommendations specific to Kenyan market
        
        Args:
            amount (float): Amount in KES to invest in stocks
            user_profile (Dict[str, Any]): User profile information
            time_horizon (str): Investment time horizon
            
        Returns:
            List[Dict[str, Any]]: List of stock recommendations
        """
        recommendations = []
        
        try:
            # Get current NSE stock data
            nse_stocks = self.nse_api.get_top_stocks()
            
            # Prioritize stocks based on criteria matching user profile
            if time_horizon == 'short':
                # For short-term, focus on liquid stocks with momentum
                focus_stocks = [s for s in nse_stocks if s.get('liquidity_score', 0) > 0.7]
                focus_stocks = sorted(focus_stocks, key=lambda x: x.get('momentum_score', 0), reverse=True)
            elif time_horizon == 'long':
                # For long-term, focus on dividend stocks and growth potential
                focus_stocks = [s for s in nse_stocks if s.get('dividend_yield', 0) > 0.03]
                focus_stocks = sorted(focus_stocks, key=lambda x: x.get('growth_score', 0), reverse=True)
            else:
                # For medium-term, balance between growth and stability
                focus_stocks = sorted(nse_stocks, key=lambda x: x.get('composite_score', 0), reverse=True)
                
            # Select top stocks
            selected_stocks = focus_stocks[:5]
            
            # Calculate allocation weights
            if selected_stocks:
                weights = self._calculate_weights(selected_stocks, key='composite_score')
                
                for i, stock in enumerate(selected_stocks):
                    stock_amount = amount * weights[i]
                    
                    recommendations.append({
                        'name': stock.get('name'),
                        'symbol': stock.get('symbol'),
                        'exchange': 'NSE',
                        'amount': stock_amount,
                        'percentage': weights[i] * 100,
                        'current_price': stock.get('current_price'),
                        'estimated_shares': stock_amount / stock.get('current_price', 1),
                        'reason': stock.get('recommendation_reason', 'Strong financial performance'),
                        'risk_level': stock.get('risk_level', 'Moderate'),
                        'dividend_yield': stock.get('dividend_yield', 0),
                        'sector': stock.get('sector', '')
                    })
        except Exception as e:
            logger.error(f"Error recommending stocks: {str(e)}")
            # Fallback to basic recommendations if API fails
            recommendations.append({
                'name': 'Safaricom PLC',
                'symbol': 'SCOM',
                'exchange': 'NSE',
                'amount': amount * 0.3,
                'percentage': 30,
                'current_price': 30.0,  # Placeholder value
                'estimated_shares': (amount * 0.3) / 30.0,
                'reason': 'Market leader with strong financials',
                'risk_level': 'Moderate',
                'dividend_yield': 0.05,
                'sector': 'Telecommunications'
            })
            recommendations.append({
                'name': 'Equity Group Holdings',
                'symbol': 'EQTY',
                'exchange': 'NSE',
                'amount': amount * 0.3,
                'percentage': 30,
                'current_price': 50.0,  # Placeholder value
                'estimated_shares': (amount * 0.3) / 50.0,
                'reason': 'Strong banking sector performance',
                'risk_level': 'Moderate',
                'dividend_yield': 0.04,
                'sector': 'Banking'
            })
            recommendations.append({
                'name': 'East African Breweries Ltd',
                'symbol': 'EABL',
                'exchange': 'NSE',
                'amount': amount * 0.2,
                'percentage': 20,
                'current_price': 170.0,  # Placeholder value
                'estimated_shares': (amount * 0.2) / 170.0,
                'reason': 'Stable consumer goods company',
                'risk_level': 'Moderate',
                'dividend_yield': 0.03,
                'sector': 'Consumer Goods'
            })
            recommendations.append({
                'name': 'Kenya Commercial Bank',
                'symbol': 'KCB',
                'exchange': 'NSE',
                'amount': amount * 0.2,
                'percentage': 20,
                'current_price': 45.0,  # Placeholder value
                'estimated_shares': (amount * 0.2) / 45.0,
                'reason': 'Solid banking foundation',
                'risk_level': 'Moderate',
                'dividend_yield': 0.06,
                'sector': 'Banking'
            })
        
        return recommendations
    
    def _recommend_bonds(self, amount: float, user_profile: Dict[str, Any], 
                        time_horizon: str) -> List[Dict[str, Any]]:
        """
        Generate bond recommendations specific to Kenyan market
        
        Args:
            amount (float): Amount in KES to invest in bonds
            user_profile (Dict[str, Any]): User profile information
            time_horizon (str): Investment time horizon
            
        Returns:
            List[Dict[str, Any]]: List of bond recommendations
        """
        recommendations = []
        
        try:
            # Get current Kenyan bond data
            cbk_bonds = self.cbk_api.get_active_bonds()
            
            # Filter bonds by time horizon
            if time_horizon == 'short':
                # T-Bills and short-term bonds (< 3 years)
                focus_bonds = [b for b in cbk_bonds if b.get('duration_years', 0) <= 3]
            elif time_horizon == 'long':
                # Long-term bonds (> 10 years)
                focus_bonds = [b for b in cbk_bonds if b.get('duration_years', 0) >= 10]
            else:
                # Medium-term bonds (3-10 years)
                focus_bonds = [b for b in cbk_bonds if 3 < b.get('duration_years', 0) < 10]
                
            # Sort by yield
            focus_bonds = sorted(focus_bonds, key=lambda x: x.get('yield', 0), reverse=True)
            
            # Select top bonds
            selected_bonds = focus_bonds[:3]
            
            # Calculate allocation weights
            if selected_bonds:
                weights = self._calculate_weights(selected_bonds, key='yield')
                
                for i, bond in enumerate(selected_bonds):
                    bond_amount = amount * weights[i]
                    
                    recommendations.append({
                        'name': bond.get('name'),
                        'symbol': bond.get('symbol'),
                        'issuer': bond.get('issuer', 'Government of Kenya'),
                        'amount': bond_amount,
                        'percentage': weights[i] * 100,
                        'yield': bond.get('yield'),
                        'duration_years': bond.get('duration_years'),
                        'maturity_date': bond.get('maturity_date'),
                        'reason': 'Stable government-backed investment',
                        'risk_level': 'Low'
                    })
        except Exception as e:
            logger.error(f"Error recommending bonds: {str(e)}")
            # Fallback recommendations
            recommendations.append({
                'name': 'Treasury Bond 15-Year',
                'symbol': 'FXD1/2021/15',
                'issuer': 'Government of Kenya',
                'amount': amount * 0.5,
                'percentage': 50,
                'yield': 0.13,  # 13%
                'duration_years': 15,
                'maturity_date': '2036-01-15',
                'reason': 'Long-term stable government investment with good returns',
                'risk_level': 'Low'
            })
            recommendations.append({
                'name': 'Treasury Bond 5-Year',
                'symbol': 'FXD1/2022/5',
                'issuer': 'Government of Kenya',
                'amount': amount * 0.3,
                'percentage': 30,
                'yield': 0.115,  # 11.5%
                'duration_years': 5,
                'maturity_date': '2027-03-15',
                'reason': 'Medium-term government bond with competitive yield',
                'risk_level': 'Low'
            })
            recommendations.append({
                'name': 'Treasury Bill 91-Day',
                'symbol': 'T91',
                'issuer': 'Government of Kenya',
                'amount': amount * 0.2,
                'percentage': 20,
                'yield': 0.095,  # 9.5%
                'duration_years': 0.25,
                'maturity_date': '90 days from purchase',
                'reason': 'Short-term liquid investment for emergency funds',
                'risk_level': 'Very Low'
            })
        
        return recommendations
    
    def _recommend_money_market(self, amount: float, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate money market recommendations specific to Kenyan market
        
        Args:
            amount (float): Amount in KES to invest in money market
            user_profile (Dict[str, Any]): User profile information
            
        Returns:
            List[Dict[str, Any]]: List of money market recommendations
        """
        recommendations = []
        
        try:
            # Get money market funds
            money_market_funds = self.market_data.get_money_market_funds()
            
            # Sort by returns
            money_market_funds = sorted(money_market_funds, key=lambda x: x.get('current_yield', 0), reverse=True)
            
            # Select top money market funds
            selected_funds = money_market_funds[:3]
            
            # Calculate allocation weights
            if selected_funds:
                weights = self._calculate_weights(selected_funds, key='current_yield')
                
                for i, fund in enumerate(selected_funds):
                    fund_amount = amount * weights[i]
                    
                    recommendations.append({
                        'name': fund.get('name'),
                        'provider': fund.get('provider'),
                        'amount': fund_amount,
                        'percentage': weights[i] * 100,
                        'current_yield': fund.get('current_yield'),
                        'min_investment': fund.get('min_investment'),
                        'liquidity': fund.get('liquidity', 'High'),
                        'reason': 'Stable returns with high liquidity',
                        'risk_level': 'Low'
                    })
        except Exception as e:
            logger.error(f"Error recommending money market funds: {str(e)}")
            # Fallback recommendations
            recommendations.append({
                'name': 'CIC Money Market Fund',
                'provider': 'CIC Asset Management',
                'amount': amount * 0.4,
                'percentage': 40,
                'current_yield': 0.10,  # 10%
                'min_investment': 5000,
                'liquidity': 'High',
                'reason': 'Top performing money market fund with strong management',
                'risk_level': 'Low'
            })
            recommendations.append({
                'name': 'Sanlam Money Market Fund',
                'provider': 'Sanlam Investments',
                'amount': amount * 0.3,
                'percentage': 30,
                'current_yield': 0.095,  # 9.5%
                'min_investment': 2500,
                'liquidity': 'High',
                'reason': 'Well-established fund with consistent performance',
                'risk_level': 'Low'
            })
            recommendations.append({
                'name': 'NCBA Money Market Fund',
                'provider': 'NCBA Investment Bank',
                'amount': amount * 0.3,
                'percentage': 30,
                'current_yield': 0.093,  # 9.3%
                'min_investment': 1000,
                'liquidity': 'High',
                'reason': 'Low minimum investment with competitive returns',
                'risk_level': 'Low'
            })
        
        return recommendations
    
    def _recommend_real_estate(self, amount: float, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate real estate recommendations specific to Kenyan market
        
        Args:
            amount (float): Amount in KES to invest in real estate
            user_profile (Dict[str, Any]): User profile information
            
        Returns:
            List[Dict[str, Any]]: List of real estate recommendations
        """
        recommendations = []
        
        try:
            # Get REIT options
            reits = self.market_data.get_reit_funds()
            
            # Sort by performance
            reits = sorted(reits, key=lambda x: x.get('historical_return', 0), reverse=True)
            
            # Select top REITs
            selected_reits = reits[:2]
            
            if selected_reits:
                # Calculate allocation weights
                weights = self._calculate_weights(selected_reits, key='historical_return')
                
                for i, reit in enumerate(selected_reits):
                    reit_amount = amount * weights[i]
                    
                    recommendations.append({
                        'name': reit.get('name'),
                        'type': 'REIT',
                        'amount': reit_amount,
                        'percentage': weights[i] * 100,
                        'historical_return': reit.get('historical_return'),
                        'min_investment': reit.get('min_investment'),
                        'reason': 'Real estate exposure without direct property ownership',
                        'risk_level': 'Moderate'
                    })
        except Exception as e:
            logger.error(f"Error recommending real estate options: {str(e)}")
            # Fallback recommendations
            recommendations.append({
                'name': 'ILAM Fahari I-REIT',
                'type': 'Income REIT',
                'amount': amount * 0.6,
                'percentage': 60,
                'historical_return': 0.08,  # 8%
                'min_investment': 'Price of 1 share on NSE',
                'reason': 'Kenya\'s first listed REIT with stable income from commercial properties',
                'risk_level': 'Moderate'
            })
            recommendations.append({
                'name': 'Acorn Student Accommodation D-REIT',
                'type': 'Development REIT',
                'amount': amount * 0.4,
                'percentage': 40,
                'historical_return': 0.095,  # 9.5%
                'min_investment': 20000,
                'reason': 'Growing student housing market with strong growth potential',
                'risk_level': 'Moderate-High'
            })
        
        return recommendations
    
    def _recommend_crypto(self, amount: float, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate cryptocurrency recommendations with Kenyan market considerations
        
        Args:
            amount (float): Amount in KES to invest in cryptocurrencies
            user_profile (Dict[str, Any]): User profile information
            
        Returns:
            List[Dict[str, Any]]: List of cryptocurrency recommendations
        """
        recommendations = []
        
        try:
            # Get crypto price data
            crypto_data = self.crypto_api.get_top_cryptocurrencies()
            
            # Calculate a stability score based on volatility
            for crypto in crypto_data:
                if 'volatility' in crypto:
                    crypto['stability_score'] = 1 / (1 + crypto['volatility'])
            
            # For crypto, we'll consider user experience
            crypto_experience = user_profile.get('crypto_experience', 'beginner')
            
            if crypto_experience == 'beginner':
                # For beginners, focus on established cryptocurrencies
                selected_cryptos = [c for c in crypto_data if c.get('market_cap_rank', 99) <= 5]
            elif crypto_experience == 'advanced':
                # For advanced users, include some alts with higher returns
                selected_cryptos = [c for c in crypto_data if c.get('market_cap_rank', 99) <= 20]
            else:
                # For intermediate, balance between established and growing
                selected_cryptos = [c for c in crypto_data if c.get('market_cap_rank', 99) <= 10]
            
            # Sort by a weighted score of market cap and stability
            selected_cryptos = sorted(selected_cryptos, 
                                     key=lambda x: (0.7 * (1 / x.get('market_cap_rank', 99)) + 
                                                   0.3 * x.get('stability_score', 0)), 
                                     reverse=True)
            
            # Limit to top 3
            selected_cryptos = selected_cryptos[:3]
            
            if selected_cryptos:
                # Bitcoin should always have the majority weight for most users
                weights = [0.6, 0.25, 0.15] if len(selected_cryptos) == 3 else [0.7, 0.3]
                
                for i, crypto in enumerate(selected_cryptos):
                    crypto_amount = amount * weights[i]
                    
                    recommendations.append({
                        'name': crypto.get('name'),
                        'symbol': crypto.get('symbol'),
                        'amount': crypto_amount,
                        'percentage': weights[i] * 100,
                        'current_price_kes': crypto.get('price_kes'),
                        'market_cap_rank': crypto.get('market_cap_rank'),
                        'reason': crypto.get('recommendation_reason', 'Based on market stability and adoption'),
                        'risk_level': 'High'
                    })
        except Exception as e:
            logger.error(f"Error recommending cryptocurrencies: {str(e)}")
            # Fallback recommendations
            recommendations.append({
                'name': 'Bitcoin',
                'symbol': 'BTC',
                'amount': amount * 0.6,
                'percentage': 60,
                'current_price_kes': 5000000,  # Placeholder
                'market_cap_rank': 1,
                'reason': 'Most established cryptocurrency with strongest network effect',
                'risk_level': 'High'
            })
            recommendations.append({
                'name': 'Ethereum',
                'symbol': 'ETH',
                'amount': amount * 0.3,
                'percentage': 30,
                'current_price_kes': 300000,  # Placeholder
                'market_cap_rank': 2,
                'reason': 'Smart contract platform with extensive developer ecosystem',
                'risk_level': 'High'
            })
            recommendations.append({
                'name': 'Solana',
                'symbol': 'SOL',
                'amount': amount * 0.1,
                'percentage': 10,
                'current_price_kes': 15000,  # Placeholder
                'market_cap_rank': 5,
                'reason': 'High-performance blockchain with growing adoption',
                'risk_level': 'Very High'
            })
        
        return recommendations
    
    def _recommend_others(self, amount: float, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for other investment types (SACCOs, etc.)
        
        Args:
            amount (float): Amount in KES to invest
            user_profile (Dict[str, Any]): User profile information
            
        Returns:
            List[Dict[str, Any]]: List of other investment recommendations
        """
        recommendations = []
        
        # For Kenya, SACCOs are an important investment vehicle
        recommendations.append({
            'name': 'Stima SACCO',
            'type': 'SACCO',
            'amount': amount * 0.5,
            'percentage': 50,
            'annual_dividend': 0.14,  # 14%
            'min_investment': 3000,
            'reason': 'One of the largest and most stable SACCOs in Kenya',
            'risk_level': 'Low-Moderate'
        })
        
        recommendations.append({
            'name': 'Mwalimu National SACCO',
            'type': 'SACCO',
            'amount': amount * 0.5,
            'percentage': 50,
            'annual_dividend': 0.13,  # 13%
            'min_investment': 2000,
            'reason': 'Teacher-focused SACCO with consistent returns',
            'risk_level': 'Low-Moderate'
        })
        
        return recommendations
    
    def _calculate_weights(self, items: List[Dict[str, Any]], key: str) -> List[float]:
        """
        Calculate allocation weights based on a specific attribute
        
        Args:
            items (List[Dict[str, Any]]): List of investment items
            key (str): Key to use for weight calculation
            
        Returns:
            List[float]: List of weights summing to 1.0
        """
        values = [item.get(key, 0) for item in items]
        
        # Handle case where all values are 0
        if sum(values) == 0:
            return [1/len(values)] * len(values)
        
        # Convert to numpy for calculations
        values = np.array(values)
        
        # Normalize to sum to 1
        weights = values / np.sum(values)
        
        return weights.tolist()
    
    def _enhance_recommendations(self, recommendations: Dict[str, Any], 
                               user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance recommendations with explanations and educational content
        
        Args:
            recommendations (Dict[str, Any]): Generated recommendations
            user_profile (Dict[str, Any]): User profile information
            
        Returns:
            Dict[str, Any]: Enhanced recommendations
        """
        financial_literacy = user_profile.get('financial_literacy_level', 'beginner')
        
        # Add overall explanation
        recommendations['explanation'] = self._generate_explanation(
            recommendations, financial_literacy
        )
        
        # Add educational content based on literacy level
        recommendations['educational_content'] = self._generate_educational_content(
            recommendations, financial_literacy
        )
        
        # Add risk warnings
        recommendations['risk_warning'] = (
            "All investments carry risk. The value of your investments can go down as well as up, "
            "and you may get back less than you invest. Past performance is not a reliable indicator "
            "of future performance. Please consider your personal circumstances, financial resources, "
            "and risk tolerance before making investment decisions."
        )
        
        return recommendations
    
    def _generate_explanation(self, recommendations: Dict[str, Any], 
                            literacy_level: str) -> str:
        """
        Generate an explanation for the investment recommendations
        
        Args:
            recommendations (Dict[str, Any]): Generated recommendations
            literacy_level (str): User's financial literacy level
            
        Returns:
            str: Explanation text
        """
        allocation = recommendations['allocation']
        summary = recommendations['summary']
        
        risk_profile = summary['risk_profile']
        time_horizon = summary['time_horizon']
        goal = summary.get('goal', 'general investing')
        
        if literacy_level == 'beginner':
            explanation = (
                f"Based on your {risk_profile} risk profile and {time_horizon}-term investment horizon, "
                f"we recommend spreading your KSh {summary['total_amount']:,.2f} across different types of investments. "
                f"This gives you a balance of safety and growth potential. "
                f"The largest portion ({allocation['stocks']*100:.1f}%) would go to stocks for growth, "
                f"with {allocation['bonds']*100:.1f}% in bonds and {allocation['money_market']*100:.1f}% in money market funds for stability."
            )
        else:
            explanation = (
                f"For your {risk_profile} risk profile with a {time_horizon}-term horizon focusing on {goal}, "
                f"we've optimized an asset allocation comprising {allocation['stocks']*100:.1f}% equities, "
                f"{allocation['bonds']*100:.1f}% fixed income, {allocation['money_market']*100:.1f}% money market instruments, "
                f"{allocation['real_estate']*100:.1f}% real estate exposure, and {allocation['crypto']*100:.1f}% alternative investments. "
                f"This allocation aims to balance capital preservation, income generation, and growth potential "
                f"aligned with current market conditions and your financial objectives."
            )
            
        return explanation
    
    def _generate_educational_content(self, recommendations: Dict[str, Any], 
                                   literacy_level: str) -> Dict[str, str]:
        """
        Generate educational content based on recommendations and literacy level
        
        Args:
            recommendations (Dict[str, Any]): Generated recommendations
            literacy_level (str): User's financial literacy level
            
        Returns:
            Dict[str, str]: Educational content by category
        """
        educational_content = {}
        
        # Add educational content for each asset class
        if 'stocks' in recommendations['specific_recommendations']:
            if literacy_level == 'beginner':
                educational_content['stocks'] = (
                    "Stocks represent ownership in companies listed on the Nairobi Securities Exchange (NSE). "
                    "When you buy shares, you become a part-owner of the company. Stocks can grow in value over time "
                    "and may pay dividends, but they can also fall in value."
                )
            else:
                educational_content['stocks'] = (
                    "Equity investments on the NSE offer exposure to Kenya's economic growth through capital "
                    "appreciation and dividend income. Diversification across sectors helps mitigate company-specific "
                    "risk, while our recommendations factor in valuation metrics, earnings growth projections, "
                    "and macroeconomic influences on specific sectors."
                )
                
        if 'bonds' in recommendations['specific_recommendations']:
            if literacy_level == 'beginner':
                educational_content['bonds'] = (
                    "Government bonds are loans to the Kenyan government that pay fixed interest rates. "
                    "They're generally safer than stocks, though they typically offer lower returns over time. "
                    "Treasury bonds are long-term (over 1 year) while Treasury bills are short-term (under 1 year)."
                )
            else:
                educational_content['bonds'] = (
                    "Fixed income securities provide steady income streams with lower volatility than equities. "
                    "Kenyan government bonds offer sovereign backing with yields that reflect inflation expectations "
                    "and monetary policy directions. Duration management is key to navigating interest rate risks, "
                    "with longer-term bonds providing higher yields but greater sensitivity to rate changes."
                )
        
        # Add general investment principles
        if literacy_level == 'beginner':
            educational_content['investment_principles'] = (
                "Investment Basics: 1) Diversification spreads risk across different investments, "
                "2) Start early to benefit from compound growth, "
                "3) Invest regularly rather than trying to time the market, "
                "4) Keep some money easily accessible for emergencies."
            )
        else:
            educational_content['investment_principles'] = (
                "Portfolio Construction Principles: Optimal diversification extends beyond simple asset allocation to "
                "correlation management between holdings. Modern Portfolio Theory suggests maximizing the Sharpe ratio "
                "by optimizing return per unit of risk. Consider both systematic (market) and idiosyncratic (security-specific) "
                "risks when constructing your portfolio."
            )
            
        return educational_content
    
    def _log_recommendation(self, user_id: str, recommendations: Dict[str, Any]) -> None:
        """
        Log recommendations for feedback learning and auditing
        
        Args:
            user_id (str): User identifier
            recommendations (Dict[str, Any]): Generated recommendations
        """
        try:
            # In a real implementation, this would log to a database
            # For now, we just log to the logger
            logger.info(f"Generated recommendations for user {user_id}")
            
            # This would typically be stored in a database for:
            # 1. Auditing purposes
            # 2. Feedback learning
            # 3. Performance tracking
            pass
        except Exception as e:
            logger.error(f"Error logging recommendation: {str(e)}")
            
    def get_investment_product_details(self, product_id: str, product_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific investment product
        
        Args:
            product_id (str): Identifier for the product
            product_type (str): Type of investment product
            
        Returns:
            Dict[str, Any]: Detailed product information
        """
        try:
            if product_type == 'stock':
                return self.nse_api.get_stock_details(product_id)
            elif product_type == 'bond':
                return self.cbk_api.get_bond_details(product_id)
            elif product_type == 'crypto':
                return self.crypto_api.get_crypto_details(product_id)
            else:
                # For other product types, fetch from general market data
                return self.market_data.get_product_details(product_id, product_type)
        except Exception as e:
            logger.error(f"Error fetching product details: {str(e)}")
            return {
                'status': 'error',
                'message': f'Unable to fetch details for {product_type} {product_id}',
                'error': str(e)
            }
    
    def update_recommendation_based_on_feedback(self, user_id: str, recommendation_id: str, 
                                             feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update recommendations based on user feedback for continuous improvement
        
        Args:
            user_id (str): User identifier
            recommendation_id (str): Recommendation identifier
            feedback (Dict[str, Any]): User feedback
            
        Returns:
            Dict[str, Any]: Updated recommendations
        """
        try:
            # Get original recommendation
            # In a real implementation, this would fetch from a database
            original_recommendation = {}  # Placeholder
            
            # Apply feedback adjustments
            if 'risk_adjustment' in feedback:
                risk_adjustment = feedback['risk_adjustment']  # -1 = lower risk, +1 = higher risk
                # Adjust risk profile based on feedback
                pass
                
            if 'excluded_categories' in feedback:
                # Remove excluded categories
                pass
                
            if 'preferred_categories' in feedback:
                # Increase allocation to preferred categories
                pass
                
            # Generate new recommendation with adjustments
            new_recommendation = self.get_recommendations(
                user_id,
                amount=original_recommendation.get('summary', {}).get('total_amount'),
                time_horizon=original_recommendation.get('summary', {}).get('time_horizon'),
                specific_goal=original_recommendation.get('summary', {}).get('goal')
            )
            
            return new_recommendation
            
        except Exception as e:
            logger.error(f"Error updating recommendation: {str(e)}")
            return {
                'status': 'error',
                'message': 'Unable to update recommendations based on feedback',
                'error': str(e)
            }
