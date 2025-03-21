import os
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from scipy import stats
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("risk_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("risk_analyzer")

# Import local modules (these would exist in the PesaGuru project)
try:
    from ..services.market_data_api import MarketDataAPI
    from ..services.user_profiler import UserProfiler
    from ..services.portfolio_ai import PortfolioAnalyzer
    from ..services.sentiment_analysis import SentimentAnalyzer
except ImportError:
    logger.warning("Running in standalone mode, some functionality may be limited")
    # Mock classes for standalone testing
    class MarketDataAPI:
        def get_market_volatility(self, market_type='stock', period='1month'):
            return {'volatility': 0.15, 'trend': 'stable'}
        
        def get_asset_historical_data(self, asset_id, period='1year'):
            # Return mock historical data
            return pd.DataFrame(
                {'date': pd.date_range(start='2024-01-01', periods=365),
                 'price': np.random.normal(100, 10, 365)}
            )
            
    class UserProfiler:
        def get_user_data(self, user_id):
            return {
                'age': 30,
                'income': 80000,
                'savings': 200000,
                'debt': 30000,
                'dependents': 1,
                'financial_literacy': 7,
                'investment_experience': 5,
                'risk_preferences': {
                    'risk_score': 65,
                    'investment_horizon': 10,
                    'loss_tolerance': 0.15
                }
            }
            
    class PortfolioAnalyzer:
        def get_portfolio_composition(self, user_id):
            return {
                'stocks': 0.60,
                'bonds': 0.20,
                'cash': 0.10,
                'real_estate': 0.05,
                'crypto': 0.05,
                'assets': [
                    {'type': 'stock', 'id': 'SCOM', 'name': 'Safaricom', 'amount': 100000},
                    {'type': 'bond', 'id': 'KE-GOV-10Y', 'name': 'Kenya 10Y Bond', 'amount': 50000},
                    {'type': 'cash', 'id': 'KES', 'name': 'Kenya Shilling', 'amount': 25000},
                    {'type': 'real_estate', 'id': 'REIT-1', 'name': 'Kenyan REIT', 'amount': 12500},
                    {'type': 'crypto', 'id': 'BTC', 'name': 'Bitcoin', 'amount': 12500}
                ]
            }
            
    class SentimentAnalyzer:
        def get_market_sentiment(self, market='general'):
            return {'sentiment': 'neutral', 'confidence': 0.65}


class RiskAnalyzer:
    """
    Core class for analyzing financial risk and generating personalized recommendations.
    """
    
    # Risk category thresholds
    RISK_CATEGORIES = {
        'conservative': {'min': 0, 'max': 40},
        'moderate': {'min': 41, 'max': 70},
        'aggressive': {'min': 71, 'max': 100}
    }
    
    # Asset class risk weights (higher = riskier)
    ASSET_RISK_WEIGHTS = {
        'cash': 0.1,
        'bonds': 0.3,
        'real_estate': 0.5,
        'stocks': 0.7,
        'crypto': 0.9
    }
    
    def __init__(self):
        """Initialize the Risk Analyzer with necessary dependencies."""
        self.market_data_api = MarketDataAPI()
        self.user_profiler = UserProfiler()
        self.portfolio_analyzer = PortfolioAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Load Kenyan-specific risk factors
        self._load_kenya_risk_factors()
        
        logger.info("RiskAnalyzer initialized successfully")
    
    def _load_kenya_risk_factors(self):
        """Load Kenya-specific risk factors from configuration file."""
        try:
            # In production, this would load from a real file
            self.kenya_risk_factors = {
                'inflation_rate': 0.065,  # 6.5% annual inflation
                'currency_volatility': 0.12,  # KES volatility
                'political_risk_premium': 0.02,  # 2% additional risk premium
                'market_liquidity_factor': 0.85,  # Liquidity adjustment (lower than 1 = less liquid)
                'interest_rate': 0.095,  # Current interest rate (9.5%)
                'gdp_growth': 0.043  # 4.3% GDP growth
            }
            logger.info("Loaded Kenya risk factors successfully")
        except Exception as e:
            logger.error(f"Failed to load Kenya risk factors: {e}")
            # Fallback values
            self.kenya_risk_factors = {
                'inflation_rate': 0.07,
                'currency_volatility': 0.15,
                'political_risk_premium': 0.03,
                'market_liquidity_factor': 0.8,
                'interest_rate': 0.10,
                'gdp_growth': 0.04
            }
    
    def analyze_user_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze a user's risk profile based on personal and financial factors.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            A dictionary containing the user's risk profile and category
        """
        logger.info(f"Analyzing risk profile for user {user_id}")
        
        # Get user data
        user_data = self.user_profiler.get_user_data(user_id)
        
        # Calculate demographic risk score (age-based)
        age = user_data.get('age', 35)
        # Younger users can typically take more risk
        demographic_risk_score = max(0, min(100, 100 - age))
        
        # Financial situation risk score
        income = user_data.get('income', 0)
        savings = user_data.get('savings', 0)
        debt = user_data.get('debt', 0)
        
        # Calculate debt-to-income and savings-to-income ratios
        debt_to_income = min(1, debt / max(1, income))  # Cap at 100%
        savings_to_income = min(3, savings / max(1, income))  # Cap at 300%
        
        # Higher income and savings increase risk capacity, debt decreases it
        financial_risk_score = 50 + (50 * (1 - debt_to_income)) + (10 * savings_to_income)
        financial_risk_score = max(0, min(100, financial_risk_score))
        
        # User preferences from questionnaire
        preference_risk_score = user_data.get('risk_preferences', {}).get('risk_score', 50)
        
        # Investment experience (1-10 scale)
        experience = user_data.get('investment_experience', 5)
        experience_factor = experience / 10  # Normalize to 0-1
        
        # Financial literacy (1-10 scale)
        literacy = user_data.get('financial_literacy', 5)
        literacy_factor = literacy / 10  # Normalize to 0-1
        
        # Calculate weighted final risk score
        weights = {
            'demographic': 0.15,
            'financial': 0.25,
            'preference': 0.35,
            'experience': 0.15,
            'literacy': 0.10
        }
        
        final_risk_score = (
            weights['demographic'] * demographic_risk_score +
            weights['financial'] * financial_risk_score +
            weights['preference'] * preference_risk_score +
            weights['experience'] * (experience_factor * 100) +
            weights['literacy'] * (literacy_factor * 100)
        )
        
        # Determine risk category
        risk_category = self._determine_risk_category(final_risk_score)
        
        # Calculate risk capacity (ability to take risks)
        risk_capacity = min(100, (
            (savings / max(1, income) * 50) +  # Higher savings = higher capacity
            (50 - (debt_to_income * 50)) +     # Lower debt = higher capacity
            (experience_factor * 20) +         # More experience = higher capacity
            (literacy_factor * 20)             # More literacy = higher capacity
        ))
        
        # Investment horizon (in years)
        investment_horizon = user_data.get('risk_preferences', {}).get('investment_horizon', 10)
        
        # Loss tolerance (% of portfolio)
        loss_tolerance = user_data.get('risk_preferences', {}).get('loss_tolerance', 0.10)
        
        risk_profile = {
            'user_id': user_id,
            'risk_score': round(final_risk_score, 2),
            'risk_category': risk_category,
            'risk_capacity': round(risk_capacity, 2),
            'risk_components': {
                'demographic_risk': round(demographic_risk_score, 2),
                'financial_risk': round(financial_risk_score, 2),
                'preference_risk': preference_risk_score,
                'experience_factor': round(experience_factor, 2),
                'literacy_factor': round(literacy_factor, 2)
            },
            'investment_horizon': investment_horizon,
            'loss_tolerance': loss_tolerance,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Risk profile for user {user_id}: Category = {risk_category}, Score = {round(final_risk_score, 2)}")
        return risk_profile
    
    def _determine_risk_category(self, risk_score: float) -> str:
        """Determine risk category based on risk score."""
        for category, thresholds in self.RISK_CATEGORIES.items():
            if thresholds['min'] <= risk_score <= thresholds['max']:
                return category
        return 'moderate'  # Default fallback
    
    def analyze_portfolio_risk(self, user_id: str, risk_profile: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze the risk of a user's investment portfolio.
        
        Args:
            user_id: The unique identifier for the user
            risk_profile: Optional pre-calculated risk profile
            
        Returns:
            A dictionary containing portfolio risk metrics
        """
        logger.info(f"Analyzing portfolio risk for user {user_id}")
        
        # Get portfolio data
        portfolio = self.portfolio_analyzer.get_portfolio_composition(user_id)
        
        if not portfolio or not portfolio.get('assets'):
            logger.warning(f"No portfolio data found for user {user_id}")
            return {
                'user_id': user_id,
                'risk_level': 'unknown',
                'error': 'No portfolio data available'
            }
        
        # If risk profile not provided, get it
        if not risk_profile:
            risk_profile = self.analyze_user_risk_profile(user_id)
        
        # Calculate portfolio diversification score
        asset_types = set(asset['type'] for asset in portfolio.get('assets', []))
        diversification_score = min(100, len(asset_types) * 20)  # 20 points per asset type
        
        # Calculate asset class risk
        total_portfolio_value = sum(asset['amount'] for asset in portfolio.get('assets', []))
        weighted_risk = 0
        
        for asset_type, percentage in portfolio.items():
            if asset_type in self.ASSET_RISK_WEIGHTS:
                weighted_risk += percentage * self.ASSET_RISK_WEIGHTS[asset_type]
        
        # Adjust for Kenyan market factors
        kenya_risk_adjustment = (
            self.kenya_risk_factors['inflation_rate'] +
            self.kenya_risk_factors['currency_volatility'] +
            self.kenya_risk_factors['political_risk_premium']
        ) / self.kenya_risk_factors['market_liquidity_factor']
        
        # Calculate Value at Risk (VaR) - simplified version
        # Assuming normal distribution of returns
        confidence_level = 0.95
        time_horizon = 30  # 30 days
        
        # Get historical volatility for portfolio
        portfolio_volatility = self._calculate_portfolio_volatility(portfolio)
        
        # Calculate VaR
        z_score = stats.norm.ppf(1 - confidence_level)
        value_at_risk = total_portfolio_value * portfolio_volatility * z_score * np.sqrt(time_horizon/252)
        value_at_risk_percentage = abs(value_at_risk) / total_portfolio_value
        
        # Run simplified Monte Carlo simulation for portfolio
        mc_results = self._run_monte_carlo_simulation(portfolio, total_portfolio_value)
        
        # Calculate Sharpe Ratio (risk-adjusted return)
        # Assuming risk-free rate is equal to Kenya's interest rate
        risk_free_rate = self.kenya_risk_factors['interest_rate']
        expected_return = self._estimate_portfolio_return(portfolio)
        sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        
        # Calculate Beta (market sensitivity)
        portfolio_beta = self._calculate_portfolio_beta(portfolio)
        
        # Calculate overall portfolio risk score (0-100)
        portfolio_risk_score = (
            (weighted_risk * 100 * 0.4) +                      # Asset allocation risk (40%)
            (value_at_risk_percentage * 100 * 2 * 0.3) +       # VaR contribution (30%)
            ((1 - min(1, sharpe_ratio)) * 100 * 0.2) +         # Inverse of Sharpe Ratio (20%)
            (portfolio_beta * 50 * 0.1)                        # Beta contribution (10%)
        )
        
        # Adjust by Kenya risk factors
        portfolio_risk_score = min(100, portfolio_risk_score * (1 + kenya_risk_adjustment * 0.5))
        
        # Determine if portfolio risk matches user risk profile
        user_risk_score = risk_profile['risk_score']
        risk_alignment = abs(portfolio_risk_score - user_risk_score) <= 15  # Within 15 points
        
        # Analyze concentration risk (if any asset > 30% of portfolio)
        concentration_risks = []
        for asset in portfolio.get('assets', []):
            percentage = asset['amount'] / total_portfolio_value
            if percentage > 0.3:
                concentration_risks.append({
                    'asset_name': asset['name'],
                    'percentage': round(percentage * 100, 2),
                    'recommendation': f"Consider reducing position in {asset['name']} to decrease concentration risk"
                })
        
        portfolio_risk_analysis = {
            'user_id': user_id,
            'portfolio_risk_score': round(portfolio_risk_score, 2),
            'risk_category': self._determine_risk_category(portfolio_risk_score),
            'aligned_with_profile': risk_alignment,
            'metrics': {
                'diversification_score': diversification_score,
                'weighted_risk': round(weighted_risk * 100, 2),
                'value_at_risk': {
                    'amount': abs(round(value_at_risk, 2)),
                    'percentage': round(value_at_risk_percentage * 100, 2),
                    'confidence_level': confidence_level * 100,
                    'time_horizon': time_horizon
                },
                'sharpe_ratio': round(sharpe_ratio, 2),
                'portfolio_beta': round(portfolio_beta, 2),
                'volatility': round(portfolio_volatility * 100, 2),  # As percentage
                'expected_return': round(expected_return * 100, 2)   # As percentage
            },
            'monte_carlo': {
                'worst_case': round(mc_results['worst_case'], 2),
                'best_case': round(mc_results['best_case'], 2),
                'median_case': round(mc_results['median'], 2),
                'success_probability': round(mc_results['success_probability'] * 100, 2)
            },
            'concentration_risks': concentration_risks,
            'kenya_factors': {
                'inflation_impact': round(self.kenya_risk_factors['inflation_rate'] * 100, 2),
                'currency_risk': round(self.kenya_risk_factors['currency_volatility'] * 100, 2),
                'political_risk': round(self.kenya_risk_factors['political_risk_premium'] * 100, 2),
                'market_liquidity': round(self.kenya_risk_factors['market_liquidity_factor'] * 100, 2)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Portfolio risk analysis completed for user {user_id}")
        return portfolio_risk_analysis
    
    def _calculate_portfolio_volatility(self, portfolio: Dict) -> float:
        """Calculate portfolio volatility based on asset allocation."""
        # In a real implementation, this would use historical data for all assets
        # and calculate covariance matrix
        
        # Simplified version using asset class volatilities
        asset_volatilities = {
            'cash': 0.01,
            'bonds': 0.05,
            'real_estate': 0.12,
            'stocks': 0.18,
            'crypto': 0.50
        }
        
        weighted_volatility = 0
        for asset_type, percentage in portfolio.items():
            if asset_type in asset_volatilities:
                weighted_volatility += percentage * asset_volatilities[asset_type]
        
        # Add Kenya-specific volatility factor
        kenya_volatility_factor = 1 + self.kenya_risk_factors['currency_volatility'] * 0.5
        return weighted_volatility * kenya_volatility_factor
    
    def _calculate_portfolio_beta(self, portfolio: Dict) -> float:
        """Calculate portfolio beta (market sensitivity)."""
        # Simplified asset class betas relative to Kenyan market
        asset_betas = {
            'cash': 0.0,
            'bonds': 0.2,
            'real_estate': 0.7,
            'stocks': 1.1,  # Higher than market due to Kenyan market volatility
            'crypto': 2.5
        }
        
        weighted_beta = 0
        for asset_type, percentage in portfolio.items():
            if asset_type in asset_betas:
                weighted_beta += percentage * asset_betas[asset_type]
        
        return weighted_beta
    
    def _estimate_portfolio_return(self, portfolio: Dict) -> float:
        """Estimate expected portfolio return based on asset allocation."""
        # Simplified asset class expected returns
        asset_returns = {
            'cash': self.kenya_risk_factors['interest_rate'] * 0.7,  # Below interest rate
            'bonds': self.kenya_risk_factors['interest_rate'] * 1.2,
            'real_estate': 0.10,  # 10% annual return
            'stocks': 0.15,       # 15% annual return
            'crypto': 0.25        # 25% annual return (high risk/high return)
        }
        
        weighted_return = 0
        for asset_type, percentage in portfolio.items():
            if asset_type in asset_returns:
                weighted_return += percentage * asset_returns[asset_type]
        
        # Adjust for inflation
        real_return = weighted_return - self.kenya_risk_factors['inflation_rate']
        return real_return
    
    def _run_monte_carlo_simulation(self, portfolio: Dict, total_value: float, 
                                    num_simulations: int = 1000, 
                                    time_horizon: int = 60) -> Dict:
        """
        Run a Monte Carlo simulation for portfolio performance.
        
        Args:
            portfolio: The user's portfolio composition
            total_value: Total portfolio value
            num_simulations: Number of simulations to run
            time_horizon: Time horizon in months
            
        Returns:
            Dictionary with simulation results
        """
        # Get expected return and volatility
        expected_return = self._estimate_portfolio_return(portfolio)
        volatility = self._calculate_portfolio_volatility(portfolio)
        
        # Monthly return and volatility
        monthly_return = expected_return / 12
        monthly_volatility = volatility / np.sqrt(12)
        
        # Run simulations
        results = np.zeros((num_simulations, time_horizon+1))
        results[:, 0] = total_value
        
        for i in range(num_simulations):
            for t in range(1, time_horizon+1):
                random_return = np.random.normal(monthly_return, monthly_volatility)
                results[i, t] = results[i, t-1] * (1 + random_return)
        
        # Analyze results
        final_values = results[:, -1]
        worst_case = np.percentile(final_values, 5)  # 5th percentile
        best_case = np.percentile(final_values, 95)  # 95th percentile
        median = np.median(final_values)
        
        # Probability of beating inflation
        inflation_adjusted_target = total_value * (1 + self.kenya_risk_factors['inflation_rate']) ** (time_horizon / 12)
        success_probability = np.mean(final_values > inflation_adjusted_target)
        
        return {
            'worst_case': worst_case,
            'best_case': best_case,
            'median': median,
            'success_probability': success_probability
        }
    
    def analyze_market_risk(self) -> Dict[str, Any]:
        """
        Analyze current market risk conditions across different markets.
        
        Returns:
            Dictionary with market risk analysis
        """
        logger.info("Analyzing market risk conditions")
        
        # Get market volatility for different markets
        stock_volatility = self.market_data_api.get_market_volatility('stock')
        forex_volatility = self.market_data_api.get_market_volatility('forex')
        crypto_volatility = self.market_data_api.get_market_volatility('crypto')
        
        # Get market sentiment
        market_sentiment = self.sentiment_analyzer.get_market_sentiment()
        
        # Calculate overall market risk score (0-100)
        stock_weight = 0.5
        forex_weight = 0.3
        crypto_weight = 0.2
        
        market_risk_score = (
            stock_volatility['volatility'] * 100 * stock_weight +
            forex_volatility['volatility'] * 100 * forex_weight +
            crypto_volatility['volatility'] * 100 * crypto_weight
        )
        
        # Adjust based on sentiment (negative sentiment increases risk)
        sentiment_factor = 1.0
        if market_sentiment['sentiment'] == 'negative':
            sentiment_factor = 1.2
        elif market_sentiment['sentiment'] == 'positive':
            sentiment_factor = 0.8
        
        market_risk_score = min(100, market_risk_score * sentiment_factor)
        
        market_risk_analysis = {
            'market_risk_score': round(market_risk_score, 2),
            'risk_category': self._determine_risk_category(market_risk_score),
            'markets': {
                'stock': {
                    'volatility': round(stock_volatility['volatility'] * 100, 2),
                    'trend': stock_volatility['trend']
                },
                'forex': {
                    'volatility': round(forex_volatility['volatility'] * 100, 2),
                    'trend': forex_volatility['trend']
                },
                'crypto': {
                    'volatility': round(crypto_volatility['volatility'] * 100, 2),
                    'trend': crypto_volatility['trend']
                }
            },
            'sentiment': {
                'overall': market_sentiment['sentiment'],
                'confidence': market_sentiment['confidence']
            },
            'kenya_factors': {
                'inflation_rate': round(self.kenya_risk_factors['inflation_rate'] * 100, 2),
                'interest_rate': round(self.kenya_risk_factors['interest_rate'] * 100, 2),
                'gdp_growth': round(self.kenya_risk_factors['gdp_growth'] * 100, 2)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Market risk analysis completed. Score: {round(market_risk_score, 2)}")
        return market_risk_analysis
    
    def analyze_debt_credit_risk(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze user's debt and credit risk.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            Dictionary with debt and credit risk analysis
        """
        logger.info(f"Analyzing debt and credit risk for user {user_id}")
        
        # Get user financial data
        user_data = self.user_profiler.get_user_data(user_id)
        
        income = user_data.get('income', 0)
        debt = user_data.get('debt', 0)
        
        # Calculate key ratios
        debt_to_income_ratio = debt / max(1, income)
        
        # Simplified credit score estimation (in real implementation, would use actual credit data)
        # Scale: 300-850 (similar to FICO)
        estimated_credit_score = 300 + min(550, (
            (1 - min(1, debt_to_income_ratio)) * 300 +  # Lower DTI ratio = higher score
            (user_data.get('financial_literacy', 5) / 10) * 100 +  # Financial literacy bonus
            (min(10, max(0, (user_data.get('age', 30) - 20) / 5)) * 15)  # Age factor (credit history)
        ))
        
        # Debt sustainability analysis
        if debt_to_income_ratio < 0.30:
            sustainability_level = "sustainable"
            sustainability_score = 80 + (0.30 - debt_to_income_ratio) * 100
        elif debt_to_income_ratio < 0.45:
            sustainability_level = "manageable"
            sustainability_score = 50 + (0.45 - debt_to_income_ratio) * 200
        elif debt_to_income_ratio < 0.60:
            sustainability_level = "concerning"
            sustainability_score = 30 + (0.60 - debt_to_income_ratio) * 133
        else:
            sustainability_level = "unsustainable"
            sustainability_score = max(0, 30 - (debt_to_income_ratio - 0.60) * 50)
        
        sustainability_score = min(100, max(0, sustainability_score))
        
        # Impact of current interest rates on debt burden
        interest_rate_impact = debt * self.kenya_risk_factors['interest_rate']
        interest_burden_percentage = interest_rate_impact / max(1, income)
        
        debt_risk_analysis = {
            'user_id': user_id,
            'debt_to_income_ratio': round(debt_to_income_ratio, 2),
            'estimated_credit_score': int(estimated_credit_score),
            'debt_sustainability': {
                'level': sustainability_level,
                'score': round(sustainability_score, 2)
            },
            'interest_rate_impact': {
                'annual_interest_cost': round(interest_rate_impact, 2),
                'percentage_of_income': round(interest_burden_percentage * 100, 2)
            },
            'recommended_actions': self._generate_debt_recommendations(debt_to_income_ratio, estimated_credit_score),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Debt risk analysis completed for user {user_id}")
        return debt_risk_analysis
    
    def _generate_debt_recommendations(self, debt_to_income_ratio: float, credit_score: float) -> List[Dict]:
        """Generate personalized debt management recommendations."""
        recommendations = []
        
        if debt_to_income_ratio > 0.50:
            recommendations.append({
                'priority': 'high',
                'action': 'Reduce high-interest debt immediately',
                'impact': 'Critical for financial health',
                'suggestion': 'Consider debt consolidation or creating a debt repayment plan'
            })
        elif debt_to_income_ratio > 0.40:
            recommendations.append({
                'priority': 'medium',
                'action': 'Create a debt reduction plan',
                'impact': 'Important for long-term financial stability',
                'suggestion': 'Focus on high-interest debt first while maintaining minimum payments on other debt'
            })
        
        if credit_score < 600:
            recommendations.append({
                'priority': 'high',
                'action': 'Improve credit score',
                'impact': 'Better loan terms and financial opportunities',
                'suggestion': 'Ensure timely bill payments and reduce credit utilization'
            })
        
        # Always include general recommendations
        recommendations.append({
            'priority': 'medium',
            'action': 'Build emergency fund',
            'impact': 'Avoid taking on new debt for emergencies',
            'suggestion': 'Aim for 3-6 months of essential expenses in savings'
        })
        
        return recommendations
    
    def generate_risk_mitigation_strategies(self, user_id: str, comprehensive: bool = False) -> Dict[str, Any]:
        """
        Generate personalized risk mitigation strategies for the user.
        
        Args:
            user_id: The unique identifier for the user
            comprehensive: Whether to include detailed strategies
            
        Returns:
            Dictionary with risk mitigation strategies
        """
        logger.info(f"Generating risk mitigation strategies for user {user_id}")
        
        # Get user risk profile
        risk_profile = self.analyze_user_risk_profile(user_id)
        risk_category = risk_profile['risk_category']
        
        # Get portfolio risk analysis
        portfolio_risk = self.analyze_portfolio_risk(user_id, risk_profile)
        
        # Get market risk analysis
        market_risk = self.analyze_market_risk()
        
        # Get debt risk analysis
        debt_risk = self.analyze_debt_credit_risk(user_id)
        
        # Generate asset allocation recommendation based on risk profile
        recommended_allocation = self._generate_recommended_allocation(risk_category)
        
        # Generate investment diversification recommendations
        diversification_recommendations = self._generate_diversification_recommendations(
            portfolio_risk,
            risk_category
        )
        
        # Generate market timing recommendations based on current market conditions
        market_timing_recommendations = self._generate_market_timing_recommendations(
            market_risk,
            risk_category
        )
        
        # Generate debt management recommendations
        debt_recommendations = debt_risk['recommended_actions']
        
        # Compile all strategies
        strategies = {
            'user_id': user_id,
            'risk_profile': {
                'category': risk_category,
                'score': risk_profile['risk_score']
            },
            'recommended_asset_allocation': recommended_allocation,
            'recommended_actions': {
                'asset_allocation': {
                    'priority': 'high',
                    'action': f"Adjust portfolio to match {risk_category} allocation",
                    'current_vs_target': self._compare_allocations(
                        self.portfolio_analyzer.get_portfolio_composition(user_id),
                        recommended_allocation
                    )
                },
                'diversification': diversification_recommendations,
                'market_timing': market_timing_recommendations,
                'debt_management': debt_recommendations
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add detailed strategies if requested
        if comprehensive:
            strategies['detailed_strategies'] = self._generate_comprehensive_strategies(
                risk_profile,
                portfolio_risk,
                market_risk,
                debt_risk
            )
        
        logger.info(f"Risk mitigation strategies generated for user {user_id}")
        return strategies
    
    def _generate_recommended_allocation(self, risk_category: str) -> Dict[str, float]:
        """Generate recommended asset allocation based on risk category."""
        if risk_category == 'conservative':
            return {
                'cash': 0.15,
                'bonds': 0.50,
                'real_estate': 0.15,
                'stocks': 0.15,
                'crypto': 0.05
            }
        elif risk_category == 'moderate':
            return {
                'cash': 0.10,
                'bonds': 0.30,
                'real_estate': 0.20,
                'stocks': 0.35,
                'crypto': 0.05
            }
        elif risk_category == 'aggressive':
            return {
                'cash': 0.05,
                'bonds': 0.15,
                'real_estate': 0.20,
                'stocks': 0.50,
                'crypto': 0.10
            }
        else:
            # Default (moderate)
            return {
                'cash': 0.10,
                'bonds': 0.30,
                'real_estate': 0.20,
                'stocks': 0.35,
                'crypto': 0.05
            }
    
    def _compare_allocations(self, current: Dict, target: Dict) -> List[Dict]:
        """Compare current and target allocations to identify adjustments."""
        comparison = []
        for asset_class, target_percentage in target.items():
            if asset_class in current:
                current_percentage = current.get(asset_class, 0)
                difference = target_percentage - current_percentage
                action = "maintain"
                if difference > 0.05:
                    action = "increase"
                elif difference < -0.05:
                    action = "decrease"
                
                comparison.append({
                    'asset_class': asset_class,
                    'current_percentage': round(current_percentage * 100, 2),
                    'target_percentage': round(target_percentage * 100, 2),
                    'difference': round(difference * 100, 2),
                    'action': action
                })
        
        return comparison
    
    def _generate_diversification_recommendations(self, portfolio_risk: Dict, risk_category: str) -> List[Dict]:
        """Generate diversification recommendations based on portfolio analysis."""
        recommendations = []
        
        diversification_score = portfolio_risk.get('metrics', {}).get('diversification_score', 0)
        
        if diversification_score < 60:
            recommendations.append({
                'priority': 'high',
                'action': 'Increase portfolio diversification',
                'impact': 'Reduced risk exposure to market volatility',
                'suggestion': 'Add more asset classes or diversify within existing asset classes'
            })
        
        # Add concentration risk recommendations
        for risk in portfolio_risk.get('concentration_risks', []):
            recommendations.append({
                'priority': 'medium',
                'action': f"Reduce position in {risk['asset_name']}",
                'impact': f"Currently {risk['percentage']}% of portfolio",
                'suggestion': 'Aim to keep individual assets below 30% of portfolio'
            })
        
        # Recommend Kenya-specific investments based on risk profile
        if risk_category == 'conservative':
            recommendations.append({
                'priority': 'medium',
                'action': 'Consider Kenya government bonds',
                'impact': 'Stable returns with lower risk',
                'suggestion': 'Treasury bonds offer higher returns than cash with government backing'
            })
        elif risk_category == 'moderate':
            recommendations.append({
                'priority': 'medium',
                'action': 'Consider Kenya REITs and blue-chip stocks',
                'impact': 'Balance of growth and stability',
                'suggestion': 'NSE blue-chip stocks like Safaricom, KCB, and Equity Bank offer dividends and growth'
            })
        elif risk_category == 'aggressive':
            recommendations.append({
                'priority': 'medium',
                'action': 'Consider growth-oriented Kenyan stocks and select crypto',
                'impact': 'Higher growth potential with higher risk',
                'suggestion': 'Small-cap Kenyan stocks with growth potential alongside established cryptocurrencies'
            })
        
        return recommendations
    
    def _generate_market_timing_recommendations(self, market_risk: Dict, risk_category: str) -> List[Dict]:
        """Generate market timing recommendations based on current market conditions."""
        recommendations = []
        
        market_sentiment = market_risk.get('sentiment', {}).get('overall', 'neutral')
        stock_trend = market_risk.get('markets', {}).get('stock', {}).get('trend', 'stable')
        
        # Market entry strategy
        if market_sentiment == 'negative' and stock_trend == 'downward':
            if risk_category == 'aggressive':
                recommendations.append({
                    'priority': 'medium',
                    'action': 'Consider phased buying into stocks',
                    'impact': 'Potential to buy assets at lower valuations',
                    'suggestion': 'Implement dollar-cost averaging to enter the market gradually'
                })
            else:
                recommendations.append({
                    'priority': 'medium',
                    'action': 'Maintain cautious approach to equity markets',
                    'impact': 'Reduced exposure to potential further declines',
                    'suggestion': 'Focus on high-quality bonds and dividend-paying stocks'
                })
        elif market_sentiment == 'positive' and stock_trend == 'upward':
            if risk_category == 'conservative':
                recommendations.append({
                    'priority': 'medium',
                    'action': 'Consider locking in some gains',
                    'impact': 'Protecting profits from potential market corrections',
                    'suggestion': 'Rebalance portfolio to maintain target asset allocation'
                })
        
        # Inflation protection
        if self.kenya_risk_factors['inflation_rate'] > 0.05:  # Inflation > 5%
            recommendations.append({
                'priority': 'medium',
                'action': 'Add inflation protection to portfolio',
                'impact': 'Preserve purchasing power against inflation',
                'suggestion': 'Consider inflation-linked bonds, real estate, or dividend-growing stocks'
            })
        
        # Currency protection
        if market_risk.get('markets', {}).get('forex', {}).get('volatility', 0) > 15:  # Forex volatility > 15%
            recommendations.append({
                'priority': 'medium',
                'action': 'Consider adding currency diversification',
                'impact': 'Hedge against KES depreciation risk',
                'suggestion': 'Allocate a portion of investments to USD or EUR-denominated assets'
            })
        
        return recommendations
    
    def _generate_comprehensive_strategies(self, risk_profile: Dict, portfolio_risk: Dict, 
                                           market_risk: Dict, debt_risk: Dict) -> Dict[str, Any]:
        """Generate comprehensive risk mitigation strategies."""
        # This would contain detailed, personalized strategies
        # For now, providing a simplified version
        
        risk_category = risk_profile['risk_category']
        investment_horizon = risk_profile.get('investment_horizon', 10)
        
        strategies = {
            'short_term_strategies': [
                {
                    'strategy': 'Emergency fund establishment',
                    'action': 'Build 3-6 months of emergency funds',
                    'rationale': 'Foundation of financial security before investing',
                    'implementation': 'Use high-yield savings account or money market fund'
                },
                {
                    'strategy': 'Debt optimization',
                    'action': 'Focus on high-interest debt repayment',
                    'rationale': 'Immediate return equal to interest rate',
                    'implementation': 'Allocate extra cash to highest interest debt first'
                }
            ],
            'medium_term_strategies': [
                {
                    'strategy': 'Portfolio diversification',
                    'action': f"Build {risk_category} portfolio with proper asset allocation",
                    'rationale': 'Reduce risk through diversification',
                    'implementation': 'Use mix of Kenyan stocks, bonds, and international assets'
                }
            ],
            'long_term_strategies': [
                {
                    'strategy': 'Retirement planning',
                    'action': 'Consistent investment in retirement accounts',
                    'rationale': 'Compound growth over time',
                    'implementation': 'Maximize contributions to retirement plans'
                }
            ]
        }
        
        # Add Kenya-specific strategies
        strategies['kenya_specific_strategies'] = [
            {
                'strategy': 'M-Akiba investment',
                'action': 'Consider government retail bonds through M-Akiba',
                'rationale': 'Low minimum investment with government backing',
                'implementation': 'Invest via M-Pesa with as little as KES 3,000'
            },
            {
                'strategy': 'NSSF contribution optimization',
                'action': 'Maximize National Social Security Fund contributions',
                'rationale': 'Tax-advantaged retirement savings',
                'implementation': 'Consider voluntary contributions beyond mandatory amounts'
            }
        ]
        
        return strategies
    
    def get_risk_alerts(self, user_id: str) -> List[Dict]:
        """
        Generate risk alerts based on user's financial situation and market conditions.
        
        Args:
            user_id: The unique identifier for the user
            
        Returns:
            List of risk alerts
        """
        alerts = []
        
        # Get portfolio risk
        portfolio_risk = self.analyze_portfolio_risk(user_id)
        
        # Get market risk
        market_risk = self.analyze_market_risk()
        
        # Get debt risk
        debt_risk = self.analyze_debt_credit_risk(user_id)
        
        # Check for high portfolio concentration
        for concentration in portfolio_risk.get('concentration_risks', []):
            alerts.append({
                'alert_type': 'portfolio_concentration',
                'severity': 'medium',
                'title': f"High concentration in {concentration['asset_name']}",
                'description': f"Your portfolio has {concentration['percentage']}% allocated to {concentration['asset_name']}, which increases risk",
                'action': concentration['recommendation']
            })
        
        # Check for portfolio-profile mismatch
        if not portfolio_risk.get('aligned_with_profile', True):
            alerts.append({
                'alert_type': 'risk_mismatch',
                'severity': 'medium',
                'title': "Portfolio risk doesn't match your risk profile",
                'description': f"Your risk profile is {portfolio_risk.get('risk_category')}, but your investments have a different risk level",
                'action': "Consider adjusting your investments to better match your risk tolerance"
            })
        
        # Check for high debt-to-income ratio
        if debt_risk.get('debt_to_income_ratio', 0) > 0.45:
            alerts.append({
                'alert_type': 'high_debt',
                'severity': 'high',
                'title': "High debt-to-income ratio",
                'description': f"Your debt-to-income ratio is {debt_risk.get('debt_to_income_ratio', 0) * 100:.1f}%, which may limit financial flexibility",
                'action': "Consider focusing on debt reduction before increasing investments"
            })
        
        # Check for high market risk
        if market_risk.get('market_risk_score', 0) > 70:
            alerts.append({
                'alert_type': 'market_volatility',
                'severity': 'medium',
                'title': "High market volatility",
                'description': "Current market conditions show above-average volatility",
                'action': "Consider waiting for stability before making major investment changes"
            })
        
        # Check for negative market sentiment
        if market_risk.get('sentiment', {}).get('overall') == 'negative':
            alerts.append({
                'alert_type': 'market_sentiment',
                'severity': 'low',
                'title': "Negative market sentiment",
                'description': "Current market sentiment is cautious or negative",
                'action': "Monitor investments closely and avoid panic selling"
            })
        
        # Check for high inflation impact
        if market_risk.get('kenya_factors', {}).get('inflation_rate', 0) > 7:
            alerts.append({
                'alert_type': 'inflation_risk',
                'severity': 'medium',
                'title': "High inflation environment",
                'description': f"Current inflation rate of {market_risk.get('kenya_factors', {}).get('inflation_rate', 0)}% may erode purchasing power",
                'action': "Consider inflation-protected investments like real estate or stocks"
            })
        
        return alerts


# Example usage
if __name__ == "__main__":
    risk_analyzer = RiskAnalyzer()
    
    # Example analysis for a user
    user_id = "user123"
    
    # Get user risk profile
    risk_profile = risk_analyzer.analyze_user_risk_profile(user_id)
    print(f"User Risk Profile: {risk_profile['risk_category']}, Score: {risk_profile['risk_score']}")
    
    # Get portfolio risk analysis
    portfolio_risk = risk_analyzer.analyze_portfolio_risk(user_id)
    print(f"Portfolio Risk Score: {portfolio_risk['portfolio_risk_score']}")
    
    # Get risk mitigation strategies
    strategies = risk_analyzer.generate_risk_mitigation_strategies(user_id)
    print(f"Generated {len(strategies['recommended_actions'])} risk mitigation strategies")
    
    # Get risk alerts
    alerts = risk_analyzer.get_risk_alerts(user_id)
    print(f"Generated {len(alerts)} risk alerts")
