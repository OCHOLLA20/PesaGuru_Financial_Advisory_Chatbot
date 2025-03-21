import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
import pickle
import joblib

# Import utilities from other PesaGuru modules
from ai.services.user_profiler import UserProfiler
from ai.services.market_analysis import MarketAnalyzer
from ai.api_integration.nse_api import NSEDataFetcher
from ai.api_integration.cbk_api import CBKDataFetcher
from ai.api_integration.crypto_api import CryptoDataFetcher
from ai.recommenders.risk_analyzer import RiskAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """User profile data structure for recommendation processing"""
    user_id: str
    age_group: str
    income_range: str
    financial_literacy: int
    financial_goals: List[str]
    risk_tolerance: str
    location: str
    investment_history: List[Dict] = None
    

@dataclass
class RecommendationResult:
    """Data structure for recommendation results"""
    investment_products: List[Dict]
    allocation_percentages: Dict[str, float]
    expected_returns: Dict[str, float]
    risk_assessment: Dict[str, Union[str, float]]
    rationale: str
    time_horizon: str


class RecommendationModel:
    """
    Machine learning model for generating personalized investment recommendations
    based on user profiles and market conditions in Kenya.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the recommendation model.
        
        Args:
            model_path: Path to the pre-trained model file
        """
        self.model_path = model_path or os.path.join(
            os.path.dirname(__file__), "trained_models/recommendation_model.pkl"
        )
        self.model = None
        self.risk_analyzer = RiskAnalyzer()
        self.market_analyzer = MarketAnalyzer()
        self.nse_data_fetcher = NSEDataFetcher()
        self.cbk_data_fetcher = CBKDataFetcher()
        self.crypto_data_fetcher = CryptoDataFetcher()
        
        # Investment product categories available in Kenya
        self.product_categories = {
            "equities": {
                "name": "Equities (NSE Stocks)",
                "min_investment": 5000,
                "liquidity": "medium",
                "volatility": "high"
            },
            "bonds": {
                "name": "Government Bonds & Treasury Bills",
                "min_investment": 50000,
                "liquidity": "low",
                "volatility": "low"
            },
            "mutual_funds": {
                "name": "Unit Trusts & Mutual Funds",
                "min_investment": 5000,
                "liquidity": "medium",
                "volatility": "medium"
            },
            "money_market": {
                "name": "Money Market Funds",
                "min_investment": 1000,
                "liquidity": "high",
                "volatility": "very_low"
            },
            "sacco": {
                "name": "SACCO Shares & Deposits",
                "min_investment": 1000,
                "liquidity": "low",
                "volatility": "low"
            },
            "real_estate": {
                "name": "Real Estate Investment Trusts (REITs)",
                "min_investment": 5000,
                "liquidity": "low",
                "volatility": "medium"
            },
            "crypto": {
                "name": "Cryptocurrency",
                "min_investment": 1000,
                "liquidity": "high",
                "volatility": "very_high"
            }
        }
        
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained recommendation model"""
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                self.model = joblib.load(self.model_path)
            else:
                logger.warning(f"Model file not found at {self.model_path}. Using rule-based fallback.")
                self.model = None  # Will use rule-based recommendations as fallback
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
    
    def preprocess_user_data(self, user_profile: UserProfile) -> np.ndarray:
        """
        Preprocess user profile data for the recommendation model.
        
        Args:
            user_profile: User profile data
            
        Returns:
            Processed feature vector for the model
        """
        # Encode categorical variables
        age_mapping = {
            "18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55-64": 4, "65+": 5
        }
        
        income_mapping = {
            "0-30k": 0, "30k-50k": 1, "50k-100k": 2, 
            "100k-200k": 3, "200k-500k": 4, "500k+": 5
        }
        
        risk_mapping = {
            "very_low": 0, "low": 1, "medium": 2, "high": 3, "very_high": 4
        }
        
        # Create feature vector for model input
        features = [
            age_mapping.get(user_profile.age_group, 2),  # Default to middle age if unknown
            income_mapping.get(user_profile.income_range, 2),  # Default to middle income
            user_profile.financial_literacy,  # Scale of 1-10
            risk_mapping.get(user_profile.risk_tolerance, 2),  # Default to medium risk
        ]
        
        # Encode financial goals (multi-hot encoding)
        goal_categories = ["retirement", "education", "home", "emergency", "business", "wealth"]
        for goal in goal_categories:
            features.append(1 if goal in user_profile.financial_goals else 0)
        
        return np.array(features).reshape(1, -1)
    
    def get_market_data(self) -> Dict:
        """
        Fetch current market data from various sources
        
        Returns:
            Dictionary containing current market data
        """
        market_data = {
            "nse_indices": {},
            "interest_rates": {},
            "forex_rates": {},
            "crypto_prices": {}
        }
        
        try:
            # Get NSE market data (top stocks and indices)
            market_data["nse_indices"] = self.nse_data_fetcher.get_market_indices()
            
            # Get interest rates from Central Bank of Kenya
            market_data["interest_rates"] = self.cbk_data_fetcher.get_interest_rates()
            
            # Get forex exchange rates
            market_data["forex_rates"] = self.cbk_data_fetcher.get_forex_rates()
            
            # Get cryptocurrency prices
            market_data["crypto_prices"] = self.crypto_data_fetcher.get_crypto_prices(
                currencies=["BTC", "ETH", "SOL", "USDT"]
            )
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
        
        return market_data
    
    def apply_market_conditions(self, base_allocations: Dict[str, float], 
                                market_data: Dict) -> Dict[str, float]:
        """
        Adjust allocation percentages based on current market conditions
        
        Args:
            base_allocations: Initial allocation percentages
            market_data: Current market data
            
        Returns:
            Adjusted allocation percentages
        """
        adjusted_allocations = base_allocations.copy()
        
        try:
            # Example adjustments based on market conditions
            # These would be more sophisticated in a real implementation
            
            # If interest rates are high, increase bond allocation
            if market_data.get("interest_rates", {}).get("t_bill_91_day", 0) > 12.0:
                # Increase bond allocation by 5% if rates are attractive
                if "bonds" in adjusted_allocations:
                    adjusted_allocations["bonds"] += 0.05
                    # Reduce equities to compensate
                    if "equities" in adjusted_allocations and adjusted_allocations["equities"] >= 0.05:
                        adjusted_allocations["equities"] -= 0.05
            
            # If NSE is in a bull market, slightly increase equity allocation
            nse_20_change = market_data.get("nse_indices", {}).get("nse_20_pct_change", 0)
            if nse_20_change > 5.0:  # If NSE 20 has increased more than 5%
                if "equities" in adjusted_allocations:
                    adjusted_allocations["equities"] += 0.03
                    # Reduce money market to compensate
                    if "money_market" in adjusted_allocations and adjusted_allocations["money_market"] >= 0.03:
                        adjusted_allocations["money_market"] -= 0.03
            
            # Normalize allocations to ensure they sum to 1.0
            total = sum(adjusted_allocations.values())
            if total > 0:
                for key in adjusted_allocations:
                    adjusted_allocations[key] /= total
                    
        except Exception as e:
            logger.error(f"Error adjusting allocations: {str(e)}")
            return base_allocations
        
        return adjusted_allocations
    
    def rule_based_recommendation(self, user_profile: UserProfile, 
                                  market_data: Dict) -> Dict[str, float]:
        """
        Generate rule-based recommendations when ML model is unavailable
        
        Args:
            user_profile: User profile data
            market_data: Current market data
            
        Returns:
            Dictionary with recommended allocation percentages
        """
        # Default allocations based on risk tolerance
        allocations = {
            "very_low": {
                "money_market": 0.60,
                "bonds": 0.25,
                "sacco": 0.10,
                "equities": 0.05,
                "mutual_funds": 0.00,
                "real_estate": 0.00,
                "crypto": 0.00
            },
            "low": {
                "money_market": 0.40,
                "bonds": 0.30,
                "sacco": 0.15,
                "equities": 0.10,
                "mutual_funds": 0.05,
                "real_estate": 0.00,
                "crypto": 0.00
            },
            "medium": {
                "money_market": 0.20,
                "bonds": 0.25,
                "sacco": 0.15,
                "equities": 0.20,
                "mutual_funds": 0.15,
                "real_estate": 0.05,
                "crypto": 0.00
            },
            "high": {
                "money_market": 0.10,
                "bonds": 0.15,
                "sacco": 0.05,
                "equities": 0.35,
                "mutual_funds": 0.20,
                "real_estate": 0.10,
                "crypto": 0.05
            },
            "very_high": {
                "money_market": 0.05,
                "bonds": 0.10,
                "sacco": 0.00,
                "equities": 0.40,
                "mutual_funds": 0.20,
                "real_estate": 0.15,
                "crypto": 0.10
            }
        }
        
        # Get base allocations for the user's risk tolerance
        risk_level = user_profile.risk_tolerance
        if risk_level not in allocations:
            risk_level = "medium"  # Default to medium risk
            
        base_allocations = allocations[risk_level]
        
        # Adjust based on financial goals
        if "retirement" in user_profile.financial_goals:
            # For retirement, increase stable investments
            if "bonds" in base_allocations:
                base_allocations["bonds"] += 0.05
                if "equities" in base_allocations and base_allocations["equities"] >= 0.05:
                    base_allocations["equities"] -= 0.05
        
        if "education" in user_profile.financial_goals:
            # For education, focus on medium-term investments
            if "mutual_funds" in base_allocations:
                base_allocations["mutual_funds"] += 0.05
                if "crypto" in base_allocations and base_allocations["crypto"] >= 0.05:
                    base_allocations["crypto"] -= 0.05
                elif "real_estate" in base_allocations and base_allocations["real_estate"] >= 0.05:
                    base_allocations["real_estate"] -= 0.05
        
        if "business" in user_profile.financial_goals:
            # For business funding, balance liquidity and growth
            if "money_market" in base_allocations:
                base_allocations["money_market"] += 0.05
                if "bonds" in base_allocations and base_allocations["bonds"] >= 0.05:
                    base_allocations["bonds"] -= 0.05
        
        # Adjust based on age group
        if user_profile.age_group in ["18-24", "25-34"]:
            # Younger investors can take more risk
            if "equities" in base_allocations:
                base_allocations["equities"] += 0.05
                if "bonds" in base_allocations and base_allocations["bonds"] >= 0.05:
                    base_allocations["bonds"] -= 0.05
        
        elif user_profile.age_group in ["55-64", "65+"]:
            # Older investors should focus on capital preservation
            if "bonds" in base_allocations:
                base_allocations["bonds"] += 0.05
                if "equities" in base_allocations and base_allocations["equities"] >= 0.05:
                    base_allocations["equities"] -= 0.05
        
        # Normalize allocations to ensure they sum to 1.0
        total = sum(base_allocations.values())
        if total > 0:
            for key in base_allocations:
                base_allocations[key] /= total
                
        # Apply market conditions to further adjust allocations
        adjusted_allocations = self.apply_market_conditions(base_allocations, market_data)
        
        return adjusted_allocations
    
    def get_specific_product_recommendations(self, 
                                             allocation: Dict[str, float], 
                                             market_data: Dict,
                                             user_profile: UserProfile) -> List[Dict]:
        """
        Convert allocation percentages to specific product recommendations
        
        Args:
            allocation: Allocation percentages by category
            market_data: Current market data
            user_profile: User profile data
            
        Returns:
            List of specific product recommendations
        """
        products = []
        
        # Determine investment amount based on income
        income_to_amount = {
            "0-30k": 10000,      # KES 10,000
            "30k-50k": 30000,    # KES 30,000
            "50k-100k": 60000,   # KES 60,000
            "100k-200k": 150000, # KES 150,000
            "200k-500k": 300000, # KES 300,000
            "500k+": 1000000     # KES 1,000,000
        }
        
        assumed_investment = income_to_amount.get(user_profile.income_range, 50000)
        
        # Equities (NSE Stocks)
        if "equities" in allocation and allocation["equities"] > 0:
            equity_amount = assumed_investment * allocation["equities"]
            
            # Get top performing stocks from NSE data
            top_stocks = []
            try:
                if "nse_top_stocks" in market_data:
                    top_stocks = market_data["nse_top_stocks"][:3]  # Top 3 performers
                else:
                    # Fallback to default recommendations
                    top_stocks = [
                        {"symbol": "SCOM", "name": "Safaricom PLC", "sector": "Telecommunications"},
                        {"symbol": "EQTY", "name": "Equity Group Holdings", "sector": "Banking"},
                        {"symbol": "KCB", "name": "KCB Group", "sector": "Banking"}
                    ]
            except Exception as e:
                logger.error(f"Error getting top stocks: {str(e)}")
                # Fallback to default recommendations
                top_stocks = [
                    {"symbol": "SCOM", "name": "Safaricom PLC", "sector": "Telecommunications"},
                    {"symbol": "EQTY", "name": "Equity Group Holdings", "sector": "Banking"},
                    {"symbol": "KCB", "name": "KCB Group", "sector": "Banking"}
                ]
            
            products.append({
                "category": "equities",
                "name": "NSE Stocks Portfolio",
                "description": "A diversified portfolio of top-performing Kenyan stocks",
                "allocation_percentage": allocation["equities"] * 100,
                "amount": equity_amount,
                "specific_products": top_stocks,
                "expected_returns": "10-15% annually",
                "risk_level": "high",
                "time_horizon": "long-term (5+ years)"
            })
        
        # Government Bonds & Treasury Bills
        if "bonds" in allocation and allocation["bonds"] > 0:
            bond_amount = assumed_investment * allocation["bonds"]
            
            # Get current treasury bond/bill rates
            t_bill_91_day = market_data.get("interest_rates", {}).get("t_bill_91_day", 10.5)
            t_bill_182_day = market_data.get("interest_rates", {}).get("t_bill_182_day", 11.0)
            t_bill_364_day = market_data.get("interest_rates", {}).get("t_bill_364_day", 12.0)
            t_bond_2_year = market_data.get("interest_rates", {}).get("t_bond_2_year", 13.0)
            
            bond_products = [
                {"name": "91-Day Treasury Bill", "rate": f"{t_bill_91_day}%", "min_investment": "KES 50,000"},
                {"name": "182-Day Treasury Bill", "rate": f"{t_bill_182_day}%", "min_investment": "KES 50,000"},
                {"name": "364-Day Treasury Bill", "rate": f"{t_bill_364_day}%", "min_investment": "KES 50,000"},
                {"name": "2-Year Treasury Bond", "rate": f"{t_bond_2_year}%", "min_investment": "KES 50,000"}
            ]
            
            products.append({
                "category": "bonds",
                "name": "Government Securities",
                "description": "Secure investment in Kenyan government treasury bills and bonds",
                "allocation_percentage": allocation["bonds"] * 100,
                "amount": bond_amount,
                "specific_products": bond_products,
                "expected_returns": f"{t_bill_364_day}% annually",
                "risk_level": "low",
                "time_horizon": "short to medium-term (3 months - 2 years)"
            })
        
        # Money Market Funds
        if "money_market" in allocation and allocation["money_market"] > 0:
            mm_amount = assumed_investment * allocation["money_market"]
            
            money_market_products = [
                {"name": "CIC Money Market Fund", "rate": "10.5%", "min_investment": "KES 5,000"},
                {"name": "Britam Money Market Fund", "rate": "10.2%", "min_investment": "KES 1,000"},
                {"name": "Sanlam Money Market Fund", "rate": "10.0%", "min_investment": "KES 2,500"}
            ]
            
            products.append({
                "category": "money_market",
                "name": "Money Market Funds",
                "description": "Low-risk liquid investment with competitive returns",
                "allocation_percentage": allocation["money_market"] * 100,
                "amount": mm_amount,
                "specific_products": money_market_products,
                "expected_returns": "9-11% annually",
                "risk_level": "very_low",
                "time_horizon": "short-term (0-1 year)"
            })
        
        # Unit Trusts & Mutual Funds
        if "mutual_funds" in allocation and allocation["mutual_funds"] > 0:
            mf_amount = assumed_investment * allocation["mutual_funds"]
            
            mutual_fund_products = [
                {"name": "Equity Investment Bank Balanced Fund", "type": "Balanced", "min_investment": "KES 5,000"},
                {"name": "NCBA Balanced Fund", "type": "Balanced", "min_investment": "KES 5,000"},
                {"name": "Old Mutual Equity Fund", "type": "Equity", "min_investment": "KES 5,000"}
            ]
            
            products.append({
                "category": "mutual_funds",
                "name": "Unit Trusts & Mutual Funds",
                "description": "Professionally managed diversified investment portfolios",
                "allocation_percentage": allocation["mutual_funds"] * 100,
                "amount": mf_amount,
                "specific_products": mutual_fund_products,
                "expected_returns": "12-15% annually",
                "risk_level": "medium",
                "time_horizon": "medium to long-term (3-7 years)"
            })
        
        # SACCO Shares & Deposits
        if "sacco" in allocation and allocation["sacco"] > 0:
            sacco_amount = assumed_investment * allocation["sacco"]
            
            sacco_products = [
                {"name": "Stima SACCO", "dividend_rate": "12-14%", "min_investment": "KES 2,000"},
                {"name": "Mwalimu SACCO", "dividend_rate": "11-13%", "min_investment": "KES 2,000"},
                {"name": "Harambee SACCO", "dividend_rate": "10-12%", "min_investment": "KES 1,000"}
            ]
            
            products.append({
                "category": "sacco",
                "name": "SACCO Shares & Deposits",
                "description": "Cooperative investment with competitive dividends and loan access",
                "allocation_percentage": allocation["sacco"] * 100,
                "amount": sacco_amount,
                "specific_products": sacco_products,
                "expected_returns": "10-14% annually",
                "risk_level": "low",
                "time_horizon": "medium-term (1-5 years)"
            })
        
        # Real Estate Investment Trusts (REITs)
        if "real_estate" in allocation and allocation["real_estate"] > 0:
            reit_amount = assumed_investment * allocation["real_estate"]
            
            reit_products = [
                {"name": "ILAM Fahari I-REIT", "type": "Income REIT", "min_investment": "KES 5,000"},
                {"name": "Acorn Student Accommodation D-REIT", "type": "Development REIT", "min_investment": "KES 5,000"}
            ]
            
            products.append({
                "category": "real_estate",
                "name": "Real Estate Investment Trusts (REITs)",
                "description": "Invest in Kenyan real estate with lower capital requirements",
                "allocation_percentage": allocation["real_estate"] * 100,
                "amount": reit_amount,
                "specific_products": reit_products,
                "expected_returns": "8-12% annually",
                "risk_level": "medium",
                "time_horizon": "long-term (5+ years)"
            })
        
        # Cryptocurrency
        if "crypto" in allocation and allocation["crypto"] > 0:
            crypto_amount = assumed_investment * allocation["crypto"]
            
            # Get current crypto prices
            crypto_products = []
            try:
                if "crypto_prices" in market_data:
                    for crypto, data in market_data["crypto_prices"].items():
                        crypto_products.append({
                            "name": data.get("name", crypto),
                            "symbol": crypto,
                            "current_price": f"{data.get('price_kes', 0):,.2f} KES"
                        })
                else:
                    # Fallback to default data
                    crypto_products = [
                        {"name": "Bitcoin", "symbol": "BTC", "current_price": "4,500,000 KES"},
                        {"name": "Ethereum", "symbol": "ETH", "current_price": "250,000 KES"},
                        {"name": "Solana", "symbol": "SOL", "current_price": "15,000 KES"}
                    ]
            except Exception as e:
                logger.error(f"Error processing crypto data: {str(e)}")
                # Fallback to default data
                crypto_products = [
                    {"name": "Bitcoin", "symbol": "BTC", "current_price": "4,500,000 KES"},
                    {"name": "Ethereum", "symbol": "ETH", "current_price": "250,000 KES"},
                    {"name": "Solana", "symbol": "SOL", "current_price": "15,000 KES"}
                ]
            
            products.append({
                "category": "crypto",
                "name": "Cryptocurrency",
                "description": "High-risk, high-reward digital assets (limit to small portion of portfolio)",
                "allocation_percentage": allocation["crypto"] * 100,
                "amount": crypto_amount,
                "specific_products": crypto_products,
                "expected_returns": "Highly variable (-30% to +100% annually)",
                "risk_level": "very_high",
                "time_horizon": "medium to long-term (3+ years)"
            })
        
        return products
    
    def calculate_expected_returns(self, allocation: Dict[str, float], assumed_investment: float = 100000) -> Dict[str, float]:
        """
        Calculate expected returns for the recommended portfolio
        
        Args:
            allocation: Asset allocation percentages
            assumed_investment: Total investment amount in KES (default: 100,000)
            
        Returns:
            Expected returns statistics
        """
        # Average historical returns for different asset classes in Kenya
        historical_returns = {
            "equities": 0.12,       # 12% average annual return
            "bonds": 0.11,          # 11% for government bonds
            "mutual_funds": 0.13,   # 13% for balanced funds
            "money_market": 0.10,   # 10% for money market funds
            "sacco": 0.12,          # 12% for SACCO dividends
            "real_estate": 0.09,    # 9% for REITs
            "crypto": 0.25          # 25% (highly variable)
        }
        
        # Average historical volatility (risk)
        historical_volatility = {
            "equities": 0.20,       # 20% standard deviation
            "bonds": 0.05,          # 5% standard deviation
            "mutual_funds": 0.12,   # 12% standard deviation
            "money_market": 0.02,   # 2% standard deviation
            "sacco": 0.04,          # 4% standard deviation
            "real_estate": 0.10,    # 10% standard deviation
            "crypto": 0.70          # 70% standard deviation (highly volatile)
        }
        
        # Calculate expected portfolio return
        portfolio_return = sum(allocation.get(asset, 0) * historical_returns.get(asset, 0) 
                              for asset in allocation)
        
        # Calculate portfolio volatility (simplified)
        portfolio_volatility = sum(allocation.get(asset, 0) * historical_volatility.get(asset, 0) 
                                  for asset in allocation)
        
        # Calculate best and worst case scenarios (simplified)
        best_case = portfolio_return + portfolio_volatility
        worst_case = portfolio_return - portfolio_volatility
        
        # One-year forecast
        one_year_projected = assumed_investment * (1 + portfolio_return)
        
        return {
            "expected_annual_return": portfolio_return,
            "expected_volatility": portfolio_volatility,
            "best_case_return": best_case,
            "worst_case_return": worst_case,
            "sharpe_ratio": (portfolio_return - 0.07) / portfolio_volatility if portfolio_volatility > 0 else 0
        }
    
    def generate_recommendation_rationale(self, 
                                         user_profile: UserProfile, 
                                         allocation: Dict[str, float],
                                         expected_returns: Dict[str, float]) -> str:
        """
        Generate a human-readable explanation for the recommendation
        
        Args:
            user_profile: User profile
            allocation: Asset allocation
            expected_returns: Expected returns data
            
        Returns:
            Explanation string
        """
        # Translate risk tolerance to human-readable form
        risk_level_desc = {
            "very_low": "very conservative",
            "low": "conservative",
            "medium": "moderate",
            "high": "aggressive",
            "very_high": "very aggressive"
        }
        
        risk_text = risk_level_desc.get(user_profile.risk_tolerance, "moderate")
        
        # Create explanation based on user profile and allocations
        top_allocations = sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]
        top_categories = [self.product_categories[cat]["name"] for cat, _ in top_allocations if cat in self.product_categories]
        
        # Format the expected return as a percentage
        exp_return = expected_returns.get("expected_annual_return", 0) * 100
        
        # Build the rationale
        rationale = f"Based on your {risk_text} risk profile and financial goals "
        
        if user_profile.financial_goals:
            goals_text = ", ".join(user_profile.financial_goals[:-1])
            if len(user_profile.financial_goals) > 1:
                goals_text += f" and {user_profile.financial_goals[-1]}"
            else:
                goals_text = user_profile.financial_goals[0]
            rationale += f"of {goals_text}, "
        
        rationale += f"we recommend a diversified portfolio focusing primarily on {', '.join(top_categories)}. "
        
        rationale += f"This investment mix aims for an expected annual return of approximately {exp_return:.1f}%, "
        
        if "age_group" in user_profile.__dict__ and user_profile.age_group:
            if user_profile.age_group in ["18-24", "25-34"]:
                rationale += "leveraging your longer investment horizon to focus on growth. "
            elif user_profile.age_group in ["35-44", "45-54"]:
                rationale += "balancing growth and stability appropriate for your life stage. "
            else:
                rationale += "with an emphasis on capital preservation suitable for your life stage. "
                
        # Add location-specific context if available
        if user_profile.location:
            if user_profile.location.lower() in ["nairobi", "mombasa", "kisumu"]:
                rationale += f"As you're based in {user_profile.location}, you have good access to a wide range of investment options through local financial institutions. "
            else:
                rationale += f"Investment options are accessible in your location ({user_profile.location}) through mobile platforms and agency banking. "
        
        return rationale
    
    def determine_time_horizon(self, user_profile: UserProfile) -> str:
        """
        Determine appropriate investment time horizon based on user profile
        
        Args:
            user_profile: User profile data
            
        Returns:
            Recommended time horizon
        """
        # Default to medium-term
        time_horizon = "medium-term (3-5 years)"
        
        # Adjust based on age
        if user_profile.age_group in ["18-24", "25-34"]:
            time_horizon = "long-term (7-10+ years)"
        elif user_profile.age_group in ["55-64", "65+"]:
            time_horizon = "short to medium-term (1-3 years)"
        
        # Adjust based on financial goals
        if "retirement" in user_profile.financial_goals:
            # For younger people, retirement is long-term
            if user_profile.age_group in ["18-24", "25-34", "35-44"]:
                time_horizon = "long-term (10+ years)"
            # For older people nearing retirement, shorter term
            elif user_profile.age_group in ["55-64", "65+"]:
                time_horizon = "short-term (1-3 years)"
        
        if "education" in user_profile.financial_goals:
            time_horizon = "medium-term (3-5 years)"
            
        if "home" in user_profile.financial_goals:
            time_horizon = "medium to long-term (5-7 years)"
            
        if "emergency" in user_profile.financial_goals:
            time_horizon = "short-term (0-1 year)"
            
        return time_horizon
    
    def generate_recommendations(self, user_profile: UserProfile) -> RecommendationResult:
        """
        Generate personalized investment recommendations based on user profile
        
        Args:
            user_profile: User profile data
            
        Returns:
            Recommendation result with portfolio allocation and rationale
        """
        try:
            # Fetch market data
            market_data = self.get_market_data()
            
            # Generate recommendations
            if self.model:
                # For ML-based recommendations when model is available
                features = self.preprocess_user_data(user_profile)
                raw_predictions = self.model.predict(features)[0]
                
                # Convert raw predictions to allocation percentages
                prediction_categories = ["equities", "bonds", "mutual_funds", 
                                        "money_market", "sacco", "real_estate", "crypto"]
                
                allocation = {category: max(0, pred) for category, pred in zip(prediction_categories, raw_predictions)}
                
                # Normalize to ensure allocations sum to 1.0
                total = sum(allocation.values())
                if total > 0:
                    for key in allocation:
                        allocation[key] /= total
                
                # Apply market conditions to adjust allocations
                allocation = self.apply_market_conditions(allocation, market_data)
            else:
                # Fallback to rule-based recommendations
                allocation = self.rule_based_recommendation(user_profile, market_data)
            
            # Get specific product recommendations
            investment_products = self.get_specific_product_recommendations(
                allocation, market_data, user_profile
            )
            
            # Get investment amount based on income profile
            income_to_investment = {
                "0-30k": 10000,      # KES 10,000
                "30k-50k": 30000,    # KES 30,000
                "50k-100k": 60000,   # KES 60,000
                "100k-200k": 150000, # KES 150,000
                "200k-500k": 300000, # KES 300,000
                "500k+": 1000000     # KES 1,000,000
            }
            assumed_investment = income_to_investment.get(user_profile.income_range, 50000)
            
            # Calculate expected returns
            expected_returns = self.calculate_expected_returns(allocation, assumed_investment)
            
            # Generate rationale for recommendations
            rationale = self.generate_recommendation_rationale(
                user_profile, allocation, expected_returns
            )
            
            # Determine appropriate time horizon
            time_horizon = self.determine_time_horizon(user_profile)
            
            # Risk assessment
            risk_assessment = {
                "overall_risk_level": user_profile.risk_tolerance,
                "volatility": expected_returns["expected_volatility"],
                "max_drawdown_potential": expected_returns["expected_volatility"] * 2,
                "sharpe_ratio": expected_returns["sharpe_ratio"]
            }
            
            # Return structured recommendation result
            return RecommendationResult(
                investment_products=investment_products,
                allocation_percentages=allocation,
                expected_returns=expected_returns,
                risk_assessment=risk_assessment,
                rationale=rationale,
                time_horizon=time_horizon
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Return a safe fallback recommendation
            fallback_allocation = {
                "money_market": 0.60,
                "bonds": 0.20,
                "equities": 0.20
            }
            
            fallback_products = [
                {
                    "category": "money_market",
                    "name": "Money Market Funds",
                    "description": "Low-risk liquid investment with competitive returns",
                    "allocation_percentage": 60,
                    "specific_products": [
                        {"name": "CIC Money Market Fund", "rate": "10.5%", "min_investment": "KES 5,000"}
                    ],
                    "expected_returns": "9-11% annually",
                    "risk_level": "very_low",
                    "time_horizon": "short-term (0-1 year)"
                }
            ]
            
            return RecommendationResult(
                investment_products=fallback_products,
                allocation_percentages=fallback_allocation,
                expected_returns={"expected_annual_return": 0.10},
                risk_assessment={"overall_risk_level": "low"},
                rationale="We've provided a conservative recommendation focused on capital preservation. Please try again or contact customer support for more detailed advice.",
                time_horizon="short to medium-term (1-3 years)"
            )


if __name__ == "__main__":
    # Example usage
    model = RecommendationModel()
    
    # Sample user profile
    user = UserProfile(
        user_id="user123",
        age_group="25-34",
        income_range="50k-100k",
        financial_literacy=7,
        financial_goals=["retirement", "home"],
        risk_tolerance="medium",
        location="Nairobi"
    )
    
    # Generate recommendations
    recommendations = model.generate_recommendations(user)
    
    # Print results
    print(f"Recommendation Rationale: {recommendations.rationale}")
    print(f"Time Horizon: {recommendations.time_horizon}")
    print("\nRecommended Portfolio Allocation:")
    for category, percentage in recommendations.allocation_percentages.items():
        print(f"  {category}: {percentage*100:.1f}%")
    
    print("\nSpecific Investment Recommendations:")
    for product in recommendations.investment_products:
        print(f"  {product['name']} ({product['allocation_percentage']:.1f}%)")
        print(f"    {product['description']}")
        print(f"    Expected Returns: {product['expected_returns']}")
        print(f"    Risk Level: {product['risk_level']}")
        print()
