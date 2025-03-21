import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional, Union
from sklearn.metrics.pairwise import cosine_similarity
import tensorflow as tf

# Internal PesaGuru modules
from ..models.recommendation_model import RecommendationModel
from ..services.user_profiler import UserProfiler
from ..services.market_analysis import MarketAnalysis
from ..services.risk_evaluation import RiskEvaluator
from ..services.sentiment_analysis import SentimentAnalyzer
from ..api_integration.nse_api import NSEDataAPI
from ..api_integration.cbk_api import CBKDataAPI
from ..api_integration.mpesa_api import MPesaAPI
from ..api_integration.crypto_api import CryptoAPI
from ..api_integration.forex_api import ForexAPI
from ..nlp.context_manager import ContextManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("recommendation_engine")


class RecommendationEngine:
    """
    Generates personalized financial recommendations for users based on 
    their profiles, market conditions, and financial goals.
    """
    
    def __init__(self, model_path: str = "../models/recommendation_model.pkl"):
        """
        Initialize the recommendation engine.
        
        Args:
            model_path: Path to the trained recommendation model
        """
        self.model = RecommendationModel.load(model_path)
        self.user_profiler = UserProfiler()
        self.market_analysis = MarketAnalysis()
        self.risk_evaluator = RiskEvaluator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.context_manager = ContextManager()
        
        # API integrations
        self.nse_api = NSEDataAPI()
        self.cbk_api = CBKDataAPI()
        self.mpesa_api = MPesaAPI()
        self.crypto_api = CryptoAPI()
        self.forex_api = ForexAPI()
        
        # Load recommendation categories and products
        self.investment_products = self._load_investment_products()
        self.loan_products = self._load_loan_products()
        self.savings_products = self._load_savings_products()
        self.tax_optimization_strategies = self._load_tax_strategies()
        
        logger.info("Recommendation Engine initialized successfully")
    
    def _load_investment_products(self) -> Dict:
        """Load available investment products from database/config"""
        try:
            with open('../data/investment_products.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Investment products file not found. Using default values.")
            return {
                "nse_stocks": {
                    "safaricom": {"risk": 3, "min_investment": 1000, "sector": "telecom"},
                    "equity_bank": {"risk": 4, "min_investment": 1000, "sector": "banking"},
                    "kcb": {"risk": 4, "min_investment": 1000, "sector": "banking"},
                    "eabl": {"risk": 3, "min_investment": 1500, "sector": "manufacturing"}
                },
                "treasury_bonds": {
                    "t_bill_91": {"risk": 1, "min_investment": 50000, "duration": 91},
                    "t_bill_182": {"risk": 1, "min_investment": 50000, "duration": 182},
                    "t_bill_364": {"risk": 1, "min_investment": 50000, "duration": 364},
                    "t_bond_2yr": {"risk": 2, "min_investment": 50000, "duration": 730}
                },
                "mutual_funds": {
                    "cic_equity": {"risk": 4, "min_investment": 5000, "category": "equity"},
                    "britam_money_market": {"risk": 1, "min_investment": 1000, "category": "money_market"},
                    "sanlam_balanced": {"risk": 3, "min_investment": 2500, "category": "balanced"}
                },
                "real_estate": {
                    "stanlib_reit": {"risk": 3, "min_investment": 10000, "category": "reit"},
                    "acorn_reit": {"risk": 3, "min_investment": 20000, "category": "reit"}
                },
                "crypto": {
                    "bitcoin": {"risk": 5, "volatile": True, "category": "crypto"},
                    "ethereum": {"risk": 5, "volatile": True, "category": "crypto"}
                }
            }

    def _load_loan_products(self) -> Dict:
        """Load available loan products from database/config"""
        try:
            with open('../data/loan_products.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Loan products file not found. Using default values.")
            return {
                "personal_loans": {
                    "equity_personal": {"interest_rate": 13.0, "max_term": 60, "min_amount": 10000},
                    "kcb_personal": {"interest_rate": 12.5, "max_term": 72, "min_amount": 50000},
                    "co-op_personal": {"interest_rate": 13.2, "max_term": 60, "min_amount": 30000}
                },
                "mobile_loans": {
                    "m_shwari": {"interest_rate": 7.5, "max_term": 1, "min_amount": 500},
                    "kcb_mpesa": {"interest_rate": 7.8, "max_term": 1, "min_amount": 1000},
                    "tala": {"interest_rate": 15.0, "max_term": 1, "min_amount": 500},
                    "branch": {"interest_rate": 14.0, "max_term": 2, "min_amount": 500},
                    "fuliza": {"daily_rate": 1.083, "max_amount": "varies", "min_amount": 100}
                },
                "mortgages": {
                    "equity_mortgage": {"interest_rate": 13.0, "max_term": 240, "min_amount": 1000000},
                    "kcb_mortgage": {"interest_rate": 12.5, "max_term": 300, "min_amount": 1000000},
                    "hf_mortgage": {"interest_rate": 13.0, "max_term": 300, "min_amount": 500000}
                },
                "business_loans": {
                    "equity_business": {"interest_rate": 14.0, "max_term": 84, "min_amount": 100000},
                    "kcb_business": {"interest_rate": 13.5, "max_term": 84, "min_amount": 100000}
                },
                "sacco_loans": {
                    "mwalimu_sacco": {"interest_rate": 12.0, "max_term": 72, "min_amount": 50000},
                    "stima_sacco": {"interest_rate": 12.5, "max_term": 72, "min_amount": 20000}
                }
            }
    
    def _load_savings_products(self) -> Dict:
        """Load available savings products from database/config"""
        try:
            with open('../data/savings_products.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Savings products file not found. Using default values.")
            return {
                "savings_accounts": {
                    "equity_save": {"interest_rate": 5.0, "min_balance": 1000, "fees": "low"},
                    "co-op_save": {"interest_rate": 4.5, "min_balance": 1000, "fees": "low"},
                    "kcb_save": {"interest_rate": 4.8, "min_balance": 1000, "fees": "low"}
                },
                "fixed_deposits": {
                    "equity_fixed": {"interest_rate": 7.0, "min_amount": 50000, "duration": [3, 6, 12]},
                    "kcb_fixed": {"interest_rate": 7.5, "min_amount": 50000, "duration": [3, 6, 12]},
                    "co-op_fixed": {"interest_rate": 7.2, "min_amount": 50000, "duration": [3, 6, 12]}
                },
                "mobile_savings": {
                    "m-shwari_lock": {"interest_rate": 5.0, "min_amount": 500, "duration": [1, 3, 6, 9, 12]},
                    "kcb_goal": {"interest_rate": 5.5, "min_amount": 500, "duration": "flexible"}
                },
                "sacco_savings": {
                    "mwalimu_sacco": {"interest_rate": 8.0, "min_amount": 1000, "dividend_rate": "11-12%"},
                    "stima_sacco": {"interest_rate": 7.5, "min_amount": 1000, "dividend_rate": "10-11%"}
                }
            }
    
    def _load_tax_strategies(self) -> Dict:
        """Load available tax optimization strategies from database/config"""
        try:
            with open('../data/tax_strategies.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Tax strategies file not found. Using default values.")
            return {
                "retirement_plans": {
                    "personal_pension": {"tax_benefit": "Deductible up to KES 20,000 monthly"},
                    "nssf": {"tax_benefit": "Mandatory contribution, tax deductible"}
                },
                "insurance_plans": {
                    "education_policy": {"tax_benefit": "Some premium payments may be tax deductible"},
                    "health_insurance": {"tax_benefit": "NHIF payments are tax deductible"}
                },
                "mortgage_interest": {
                    "home_ownership": {"tax_benefit": "Up to KES 300,000 annually on mortgage interest"}
                },
                "investment_deductions": {
                    "infrastructure_bonds": {"tax_benefit": "Tax-free interest income"}
                }
            }
    
    async def get_user_recommendations(self, user_id: str, recommendation_type: str = "all") -> Dict:
        """
        Generate personalized recommendations for a user.
        
        Args:
            user_id: The unique identifier for the user
            recommendation_type: Type of recommendation to generate 
                (all, investment, saving, loan, tax)
                
        Returns:
            Dictionary containing personalized recommendations
        """
        try:
            # Get user profile and financial data
            user_profile = await self.user_profiler.get_user_profile(user_id)
            
            # Verify we have sufficient data for recommendations
            if not user_profile:
                logger.warning(f"Insufficient profile data for user {user_id}")
                return {
                    "status": "limited",
                    "message": "We need more information about your financial situation to provide personalized recommendations.",
                    "recommendations": self._get_general_recommendations(recommendation_type)
                }
            
            # Get real-time market data
            market_data = await self.market_analysis.get_current_market_data()
            
            # Generate recommendations based on type
            recommendations = {}
            
            if recommendation_type == "all" or recommendation_type == "investment":
                recommendations["investment"] = await self._generate_investment_recommendations(
                    user_profile, market_data
                )
                
            if recommendation_type == "all" or recommendation_type == "saving":
                recommendations["saving"] = await self._generate_savings_recommendations(
                    user_profile
                )
                
            if recommendation_type == "all" or recommendation_type == "loan":
                recommendations["loan"] = await self._generate_loan_recommendations(
                    user_profile, market_data
                )
                
            if recommendation_type == "all" or recommendation_type == "tax":
                recommendations["tax"] = await self._generate_tax_recommendations(
                    user_profile
                )
            
            # Track recommendation event for future improvement
            self._track_recommendation_event(user_id, recommendation_type, recommendations)
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "An error occurred while generating your recommendations. Please try again later.",
                "recommendations": self._get_general_recommendations(recommendation_type)
            }
    
    async def _generate_investment_recommendations(self, user_profile: Dict, market_data: Dict) -> List[Dict]:
        """
        Generate personalized investment recommendations based on user profile and market data.
        
        Args:
            user_profile: User's financial profile data
            market_data: Current market data and trends
            
        Returns:
            List of investment recommendations
        """
        recommendations = []
        
        # Extract key user attributes
        risk_tolerance = user_profile.get("risk_tolerance", 3)  # Default to moderate risk
        investment_horizon = user_profile.get("investment_horizon", 5)  # Default to 5 years
        available_funds = user_profile.get("available_funds", 10000)  # Default to 10000 KES
        investment_goals = user_profile.get("investment_goals", ["growth"])
        
        # Get user age
        try:
            birth_year = int(user_profile.get("birth_year", 1990))
            current_year = datetime.now().year
            age = current_year - birth_year
        except (ValueError, TypeError):
            age = 30  # Default age if not available
        
        # Filter investment products based on user's risk tolerance and available funds
        suitable_investments = []
        
        # Stocks
        for stock_name, stock_data in self.investment_products["nse_stocks"].items():
            if stock_data["risk"] <= risk_tolerance + 1 and stock_data["min_investment"] <= available_funds:
                # Get latest stock price
                try:
                    stock_info = await self.nse_api.get_stock_info(stock_name)
                    current_price = stock_info.get("current_price")
                    price_change = stock_info.get("price_change_percent")
                    
                    suitable_investments.append({
                        "type": "stock",
                        "name": stock_name.replace("_", " ").title(),
                        "current_price": current_price,
                        "price_change": price_change,
                        "risk_level": stock_data["risk"],
                        "sector": stock_data["sector"],
                        "min_investment": stock_data["min_investment"],
                        "recommendation_strength": self._calculate_recommendation_strength(
                            stock_data, user_profile, market_data
                        )
                    })
                except Exception as e:
                    logger.warning(f"Error getting stock info for {stock_name}: {str(e)}")
        
        # Treasury bonds/bills based on investment horizon
        for bond_name, bond_data in self.investment_products["treasury_bonds"].items():
            if bond_data["min_investment"] <= available_funds:
                # Recommend shorter-term bonds for older investors or shorter horizons
                if (bond_data["duration"] <= 182 and (age > 55 or investment_horizon <= 2)) or \
                   (bond_data["duration"] <= 364 and age <= 55 and investment_horizon > 2):
                    
                    try:
                        bond_info = await self.cbk_api.get_treasury_rates()
                        rate = bond_info.get(bond_name, {"rate": 10.0})["rate"]
                        
                        suitable_investments.append({
                            "type": "government_security",
                            "name": bond_name.replace("_", " ").upper(),
                            "current_rate": rate,
                            "duration_days": bond_data["duration"],
                            "risk_level": bond_data["risk"],
                            "min_investment": bond_data["min_investment"],
                            "recommendation_strength": self._calculate_recommendation_strength(
                                bond_data, user_profile, market_data
                            )
                        })
                    except Exception as e:
                        logger.warning(f"Error getting bond info for {bond_name}: {str(e)}")
        
        # Mutual funds based on risk profile
        for fund_name, fund_data in self.investment_products["mutual_funds"].items():
            if fund_data["risk"] <= risk_tolerance + 1 and fund_data["min_investment"] <= available_funds:
                try:
                    fund_info = {"current_nav": 100, "annual_return": 8.5}  # Default values
                    
                    suitable_investments.append({
                        "type": "mutual_fund",
                        "name": fund_name.replace("_", " ").title(),
                        "current_nav": fund_info["current_nav"],
                        "annual_return": fund_info["annual_return"],
                        "category": fund_data["category"],
                        "risk_level": fund_data["risk"],
                        "min_investment": fund_data["min_investment"],
                        "recommendation_strength": self._calculate_recommendation_strength(
                            fund_data, user_profile, market_data
                        )
                    })
                except Exception as e:
                    logger.warning(f"Error getting fund info for {fund_name}: {str(e)}")
        
        # Only recommend crypto for high risk tolerance users
        if risk_tolerance >= 4 and available_funds >= 5000:
            for crypto_name, crypto_data in self.investment_products["crypto"].items():
                try:
                    crypto_info = await self.crypto_api.get_crypto_price(crypto_name)
                    
                    suitable_investments.append({
                        "type": "cryptocurrency",
                        "name": crypto_name.title(),
                        "current_price": crypto_info["price"],
                        "price_change": crypto_info["price_change_24h"],
                        "risk_level": crypto_data["risk"],
                        "warning": "Cryptocurrencies are highly volatile and not regulated by CBK. Only invest what you can afford to lose.",
                        "recommendation_strength": self._calculate_recommendation_strength(
                            crypto_data, user_profile, market_data
                        ) * 0.8  # Reduce recommendation strength for crypto
                    })
                except Exception as e:
                    logger.warning(f"Error getting crypto info for {crypto_name}: {str(e)}")
        
        # Get real estate investment options for long-term investors
        if investment_horizon >= 5 and available_funds >= 10000:
            for reit_name, reit_data in self.investment_products["real_estate"].items():
                try:
                    reit_info = await self.nse_api.get_stock_info(reit_name)
                    
                    suitable_investments.append({
                        "type": "real_estate",
                        "name": reit_name.replace("_", " ").upper(),
                        "current_price": reit_info.get("current_price", 0),
                        "annual_yield": reit_info.get("dividend_yield", 7.0),
                        "risk_level": reit_data["risk"],
                        "min_investment": reit_data["min_investment"],
                        "recommendation_strength": self._calculate_recommendation_strength(
                            reit_data, user_profile, market_data
                        )
                    })
                except Exception as e:
                    logger.warning(f"Error getting REIT info for {reit_name}: {str(e)}")
        
        # Sort suitable investments by recommendation strength
        suitable_investments.sort(key=lambda x: x["recommendation_strength"], reverse=True)
        
        # Take top 5 recommendations
        recommendations = suitable_investments[:5]
        
        # Add portfolio allocation suggestion
        if recommendations:
            recommendations.append(self._generate_portfolio_allocation(
                user_profile, recommendations
            ))
        
        return recommendations
    
    async def _generate_savings_recommendations(self, user_profile: Dict) -> List[Dict]:
        """
        Generate personalized savings recommendations based on user profile.
        
        Args:
            user_profile: User's financial profile data
            
        Returns:
            List of savings recommendations
        """
        recommendations = []
        
        # Extract key user attributes
        monthly_income = user_profile.get("monthly_income", 50000)  # Default to 50000 KES
        monthly_expenses = user_profile.get("monthly_expenses", 40000)  # Default to 40000 KES
        savings_goal = user_profile.get("savings_goal", "emergency_fund")
        current_savings = user_profile.get("current_savings", 10000)
        has_emergency_fund = user_profile.get("has_emergency_fund", False)
        
        # Calculate savings capacity
        savings_capacity = monthly_income - monthly_expenses
        if savings_capacity <= 0:
            # User needs budgeting advice
            recommendations.append({
                "type": "budgeting_advice",
                "title": "Improve Your Budget",
                "description": "Your expenses currently exceed your income. Consider reviewing your budget to find areas where you can reduce spending.",
                "action_steps": [
                    "Track all expenses for 30 days",
                    "Identify non-essential spending",
                    "Create a realistic budget plan",
                    "Consider additional income sources"
                ],
                "recommendation_strength": 10  # Highest priority recommendation
            })
        
        # Recommend emergency fund if user doesn't have one
        if not has_emergency_fund:
            recommendations.append({
                "type": "emergency_fund",
                "title": "Start an Emergency Fund",
                "description": "An emergency fund can provide financial security. Aim to save 3-6 months of living expenses.",
                "target_amount": monthly_expenses * 3,
                "suggested_monthly_contribution": min(savings_capacity * 0.5, monthly_expenses * 0.2),
                "recommended_products": [
                    {
                        "name": "M-Shwari Lock Savings",
                        "interest_rate": self.savings_products["mobile_savings"]["m-shwari_lock"]["interest_rate"],
                        "min_amount": self.savings_products["mobile_savings"]["m-shwari_lock"]["min_amount"],
                        "features": ["Easy access via M-Pesa", "No withdrawal fees after maturity"]
                    },
                    {
                        "name": "Equity Bank Save Direct",
                        "interest_rate": self.savings_products["savings_accounts"]["equity_save"]["interest_rate"],
                        "min_balance": self.savings_products["savings_accounts"]["equity_save"]["min_balance"],
                        "features": ["Easy access", "Low maintenance fees"]
                    }
                ],
                "recommendation_strength": 9
            })
        
        # Recommend specific savings products based on user goals
        if savings_goal == "education":
            recommendations.append({
                "type": "education_savings",
                "title": "Education Savings Plan",
                "description": "Save for education expenses with these dedicated options",
                "suggested_monthly_contribution": savings_capacity * 0.4,
                "recommended_products": [
                    {
                        "name": "Co-op Bank Education Savings Plan",
                        "interest_rate": self.savings_products["fixed_deposits"]["co-op_fixed"]["interest_rate"],
                        "min_amount": self.savings_products["fixed_deposits"]["co-op_fixed"]["min_amount"],
                        "features": ["Higher interest rates", "Structured saving"]
                    }
                ],
                "recommendation_strength": 8
            })
        elif savings_goal == "home_purchase":
            recommendations.append({
                "type": "home_purchase_savings",
                "title": "Home Purchase Savings Plan",
                "description": "Save for a home down payment with these options",
                "suggested_monthly_contribution": savings_capacity * 0.5,
                "recommended_products": [
                    {
                        "name": "SACCO Savings Account",
                        "interest_rate": self.savings_products["sacco_savings"]["stima_sacco"]["interest_rate"],
                        "dividend_rate": self.savings_products["sacco_savings"]["stima_sacco"]["dividend_rate"],
                        "features": ["Higher returns through dividends", "Access to home loans"]
                    }
                ],
                "recommendation_strength": 8
            })
        elif savings_goal == "retirement":
            recommendations.append({
                "type": "retirement_savings",
                "title": "Retirement Savings Plan",
                "description": "Prepare for retirement with these long-term savings options",
                "suggested_monthly_contribution": savings_capacity * 0.3,
                "recommended_products": [
                    {
                        "name": "Personal Pension Plan",
                        "features": ["Tax benefits", "Long-term growth", "Retirement security"],
                        "tax_advantage": "Up to KES 20,000 monthly can be deducted from taxable income"
                    }
                ],
                "recommendation_strength": 8
            })
        
        # General savings recommendations
        recommendations.append({
            "type": "general_savings",
            "title": "Regular Savings Plan",
            "description": "Establish a habit of regular saving with these options",
            "suggested_monthly_contribution": savings_capacity * 0.2,
            "recommended_products": [
                {
                    "name": "Automatic M-Pesa to M-Shwari Transfers",
                    "features": ["Automated savings", "Easy setup", "Flexible access"]
                },
                {
                    "name": "KCB Goal Savings Account",
                    "interest_rate": self.savings_products["mobile_savings"]["kcb_goal"]["interest_rate"],
                    "features": ["Goal-based saving", "Automated savings plans"]
                }
            ],
            "recommendation_strength": 7
        })
        
        # General budgeting tips for everyone
        recommendations.append({
            "type": "budgeting_tips",
            "title": "Budgeting Tips",
            "description": "Simple strategies to help manage your finances better",
            "tips": [
                "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings",
                "Track your expenses with apps like M-Ledger",
                "Set up automatic transfers to savings on payday",
                "Review and cancel unused subscriptions"
            ],
            "recommendation_strength": 6
        })
        
        # Sort by recommendation strength
        recommendations.sort(key=lambda x: x["recommendation_strength"], reverse=True)
        
        return recommendations
    
    async def _generate_loan_recommendations(self, user_profile: Dict, market_data: Dict) -> List[Dict]:
        """
        Generate personalized loan recommendations based on user profile and market data.
        
        Args:
            user_profile: User's financial profile data
            market_data: Current market data and trends
            
        Returns:
            List of loan recommendations
        """
        recommendations = []
        
        # Extract key user attributes
        monthly_income = user_profile.get("monthly_income", 50000)  # Default to 50000 KES
        credit_score = user_profile.get("credit_score", "unknown")
        loan_purpose = user_profile.get("loan_purpose", "general")
        existing_debt = user_profile.get("existing_debt", 0)
        employment_status = user_profile.get("employment_status", "unknown")
        
        # Calculate debt-to-income ratio (DTI)
        existing_monthly_payment = user_profile.get("existing_monthly_payment", 0)
        dti_ratio = (existing_monthly_payment / monthly_income) if monthly_income > 0 else 1
        
        # Define max affordable monthly payment (40% of income including existing debt)
        max_affordable_payment = monthly_income * 0.4 - existing_monthly_payment
        
        # Check if user should be taking a loan
        if dti_ratio > 0.5:
            recommendations.append({
                "type": "debt_warning",
                "title": "Caution: High Debt Level",
                "description": "Your current debt level is already high compared to your income. Consider reducing existing debt before taking on new loans.",
                "debt_to_income_ratio": f"{dti_ratio:.0%}",
                "recommendation": "Focus on debt reduction",
                "recommendation_strength": 10
            })
            
            # Add debt consolidation if user has high debt
            recommendations.append({
                "type": "debt_consolidation",
                "title": "Debt Consolidation Options",
                "description": "Consider these options to consolidate and manage your existing debt",
                "options": [
                    {
                        "name": "KCB Debt Consolidation Loan",
                        "interest_rate": self.loan_products["personal_loans"]["kcb_personal"]["interest_rate"],
                        "features": ["Lower interest rate", "Single monthly payment", "Extended repayment term"]
                    }
                ],
                "recommendation_strength": 9
            })
            
            # Return recommendations focused on debt management
            return recommendations
        
        # Determine suitable loan types based on purpose
        if loan_purpose == "business":
            suitable_loan_category = "business_loans"
        elif loan_purpose == "home_purchase":
            suitable_loan_category = "mortgages"
        elif loan_purpose == "emergency" or loan_purpose == "short_term":
            suitable_loan_category = "mobile_loans"
        else:
            suitable_loan_category = "personal_loans"
        
        # Get current interest rates from CBK API
        try:
            interest_rates = await self.cbk_api.get_lending_rates()
            average_rate = interest_rates.get("average_lending_rate", 13.0)
        except Exception as e:
            logger.warning(f"Error getting current interest rates: {str(e)}")
            average_rate = 13.0  # Default value
        
        # Add recommendation based on loan category
        if suitable_loan_category == "personal_loans":
            for loan_name, loan_data in self.loan_products["personal_loans"].items():
                # Calculate maximum loan amount based on income
                max_term = loan_data["max_term"]
                interest_rate = loan_data["interest_rate"]
                monthly_rate = interest_rate / 100 / 12
                max_amount = max_affordable_payment * ((1 - (1 + monthly_rate) ** (-max_term)) / monthly_rate)
                
                # Only recommend if max amount is above minimum loan amount
                if max_amount >= loan_data["min_amount"]:
                    recommendations.append({
                        "type": "personal_loan",
                        "name": loan_name.replace("_", " ").title(),
                        "description": "Personal loan for general expenses",
                        "interest_rate": interest_rate,
                        "max_term_months": max_term,
                        "max_amount": max_amount,
                        "monthly_payment": max_affordable_payment,
                        "comparison_to_market": f"{interest_rate - average_rate:.1f}% compared to average market rate",
                        "recommendation_strength": self._calculate_loan_recommendation_strength(
                            loan_data, user_profile, interest_rate, average_rate
                        )
                    })
        
        elif suitable_loan_category == "business_loans":
            for loan_name, loan_data in self.loan_products["business_loans"].items():
                # Calculate maximum loan amount based on income
                max_term = loan_data["max_term"]
                interest_rate = loan_data["interest_rate"]
                monthly_rate = interest_rate / 100 / 12
                max_amount = max_affordable_payment * ((1 - (1 + monthly_rate) ** (-max_term)) / monthly_rate)
                
                # Only recommend if max amount is above minimum loan amount
                if max_amount >= loan_data["min_amount"]:
                    recommendations.append({
                        "type": "business_loan",
                        "name": loan_name.replace("_", " ").title(),
                        "description": "Financing for business needs",
                        "interest_rate": interest_rate,
                        "max_term_months": max_term,
                        "max_amount": max_amount,
                        "monthly_payment": max_affordable_payment,
                        "requirements": ["Business registration", "6 months bank statements", "Business plan"],
                        "recommendation_strength": self._calculate_loan_recommendation_strength(
                            loan_data, user_profile, interest_rate, average_rate
                        )
                    })
        
        elif suitable_loan_category == "mortgages":
            for loan_name, loan_data in self.loan_products["mortgages"].items():
                # Mortgage calculations
                max_term = loan_data["max_term"]
                interest_rate = loan_data["interest_rate"]
                monthly_rate = interest_rate / 100 / 12
                max_amount = max_affordable_payment * ((1 - (1 + monthly_rate) ** (-max_term)) / monthly_rate)
                
                # Only recommend if max amount is above minimum loan amount
                if max_amount >= loan_data["min_amount"]:
                    recommendations.append({
                        "type": "mortgage",
                        "name": loan_name.replace("_", " ").title(),
                        "description": "Home purchase financing",
                        "interest_rate": interest_rate,
                        "max_term_months": max_term,
                        "max_amount": max_amount,
                        "monthly_payment": max_affordable_payment,
                        "requirements": ["Down payment of 10-20%", "Property valuation", "Legal documentation"],
                        "tax_benefit": "Mortgage interest relief up to KES 300,000 annually",
                        "recommendation_strength": self._calculate_loan_recommendation_strength(
                            loan_data, user_profile, interest_rate, average_rate
                        )
                    })
        
        elif suitable_loan_category == "mobile_loans":
            for loan_name, loan_data in self.loan_products["mobile_loans"].items():
                # Mobile loans typically have shorter terms and different calculation methods
                if loan_name == "fuliza":
                    # Fuliza has a daily rate rather than monthly
                    recommendations.append({
                        "type": "mobile_loan",
                        "name": "Fuliza M-Pesa",
                        "description": "Overdraft facility through M-Pesa",
                        "daily_rate": loan_data["daily_rate"],
                        "limit": "Based on M-Pesa transaction history",
                        "term": "Until next M-Pesa deposit",
                        "convenience": "Automatic access when M-Pesa balance is insufficient",
                        "recommendation_strength": 7 if existing_debt < 5000 else 4
                    })
                else:
                    recommendations.append({
                        "type": "mobile_loan",
                        "name": loan_name.replace("_", " ").title(),
                        "description": "Quick access to short-term credit",
                        "interest_rate": loan_data["interest_rate"],
                        "term_months": loan_data["max_term"],
                        "min_amount": loan_data["min_amount"],
                        "max_amount": "Based on credit history and usage patterns",
                        "convenience": "Application and disbursement via mobile phone",
                        "recommendation_strength": self._calculate_loan_recommendation_strength(
                            loan_data, user_profile, loan_data["interest_rate"], average_rate, is_mobile=True
                        )
                    })
        
        # If user is employed, add SACCO loan options
        if employment_status in ["employed", "self_employed"]:
            for loan_name, loan_data in self.loan_products["sacco_loans"].items():
                # Calculate maximum loan amount based on income
                max_term = loan_data["max_term"]
                interest_rate = loan_data["interest_rate"]
                monthly_rate = interest_rate / 100 / 12
                max_amount = max_affordable_payment * ((1 - (1 + monthly_rate) ** (-max_term)) / monthly_rate)
                
                # Only recommend if max amount is above minimum loan amount
                if max_amount >= loan_data["min_amount"]:
                    recommendations.append({
                        "type": "sacco_loan",
                        "name": loan_name.replace("_", " ").title(),
                        "description": "Lower interest loans through SACCO membership",
                        "interest_rate": interest_rate,
                        "max_term_months": max_term,
                        "max_amount": max_amount,
                        "monthly_payment": max_affordable_payment,
                        "requirements": ["SACCO membership", "Minimum savings", "Guarantors"],
                        "recommendation_strength": self._calculate_loan_recommendation_strength(
                            loan_data, user_profile, interest_rate, average_rate
                        ) + 1  # Boost SACCO loans slightly
                    })
        
        # Add general loan advice
        recommendations.append({
            "type": "loan_advice",
            "title": "General Loan Advice",
            "tips": [
                "Compare total loan costs, not just interest rates",
                "Check for hidden fees and early repayment penalties",
                "Avoid borrowing more than you need",
                "Consider loan insurance for large loans"
            ],
            "recommendation_strength": 5
        })
        
        # Sort by recommendation strength
        recommendations.sort(key=lambda x: x["recommendation_strength"], reverse=True)
        
        # Take top 5 recommendations
        return recommendations[:5]
    
    async def _generate_tax_recommendations(self, user_profile: Dict) -> List[Dict]:
        """
        Generate personalized tax optimization recommendations based on user profile.
        
        Args:
            user_profile: User's financial profile data
            
        Returns:
            List of tax optimization recommendations
        """
        recommendations = []
        
        # Extract key user attributes
        annual_income = user_profile.get("monthly_income", 50000) * 12
        employment_status = user_profile.get("employment_status", "employed")
        has_mortgage = user_profile.get("has_mortgage", False)
        has_children = user_profile.get("has_children", False)
        has_business = user_profile.get("has_business", False)
        
        # Kenya Tax Brackets (simplified for example)
        tax_brackets = [
            {"bracket": "Up to KES 288,000", "rate": 10},
            {"bracket": "KES 288,001 - KES 388,000", "rate": 25},
            {"bracket": "KES 388,001 and above", "rate": 30}
        ]
        
        # Add general tax information
        recommendations.append({
            "type": "tax_information",
            "title": "Your Tax Bracket",
            "estimated_annual_income": annual_income,
            "tax_brackets": tax_brackets,
            "estimated_tax_bracket": self._determine_tax_bracket(annual_income),
            "recommendation_strength": 7
        })
        
        # Recommend retirement contributions for tax benefits
        recommendations.append({
            "type": "retirement_tax_benefit",
            "title": "Retirement Planning Tax Benefits",
            "description": "Contributions to registered pension schemes are tax-deductible",
            "tax_benefit": "Up to KES 20,000 per month can be deducted from taxable income",
            "potential_annual_savings": min(20000 * 12, annual_income * 0.3) * 0.3,  # Rough estimate of tax savings
            "recommended_actions": [
                "Contribute to an employer pension scheme",
                "Open a personal pension plan if not available through employer",
                "Consider additional voluntary contributions"
            ],
            "recommendation_strength": 8
        })
        
        # Mortgage interest for homeowners
        if has_mortgage:
            recommendations.append({
                "type": "mortgage_tax_benefit",
                "title": "Mortgage Interest Relief",
                "description": "Interest paid on mortgages for owner-occupied properties can be tax-deductible",
                "tax_benefit": "Up to KES 300,000 annually in mortgage interest can be claimed",
                "required_documentation": "Annual mortgage statement showing interest paid",
                "recommendation_strength": 9
            })
        
        # Home ownership savings plan for non-homeowners
        if not has_mortgage:
            recommendations.append({
                "type": "hosp_tax_benefit",
                "title": "Home Ownership Savings Plan (HOSP)",
                "description": "Savings in an approved HOSP account receive tax benefits",
                "tax_benefit": "Interest income is tax-exempt up to KES 3 million",
                "recommended_providers": ["KCB HOSP", "Co-op Bank HOSP"],
                "recommendation_strength": 7
            })
        
        # Insurance premium tax benefits
        recommendations.append({
            "type": "insurance_tax_benefit",
            "title": "Insurance Premium Tax Relief",
            "description": "Premiums paid for life insurance may qualify for tax relief",
            "tax_benefit": "15% of premiums paid, up to a maximum of KES 60,000 annually",
            "qualifying_policies": "Life insurance policies with a term of 10 years or more",
            "recommendation_strength": 6
        })
        
        # NHIF benefits
        recommendations.append({
            "type": "nhif_tax_benefit",
            "title": "NHIF Contributions",
            "description": "National Hospital Insurance Fund contributions are tax-deductible",
            "current_contribution": self._calculate_nhif_contribution(annual_income / 12),
            "benefit": "Reduces taxable income while providing health coverage",
            "recommendation_strength": 8
        })
        
        # Business owners specific recommendations
        if has_business:
            recommendations.append({
                "type": "business_tax_strategies",
                "title": "Business Tax Optimization Strategies",
                "description": "Legal ways to optimize taxes for business owners",
                "strategies": [
                    "Maintain proper business expense records",
                    "Consider business structure (sole proprietorship vs. limited company)",
                    "Timing of income and expenses",
                    "Capital allowances for business assets"
                ],
                "recommended_action": "Consult with a tax professional for personalized business tax planning",
                "recommendation_strength": 9
            })
        
        # Education insurance for parents
        if has_children:
            recommendations.append({
                "type": "education_insurance_tax_benefit",
                "title": "Education Insurance Tax Benefits",
                "description": "Education insurance policies may qualify for tax benefits",
                "tax_benefit": "Premiums may be tax-deductible under certain conditions",
                "recommended_providers": ["Jubilee Insurance", "Britam"],
                "recommendation_strength": 7
            })
        
        # Infrastructure bonds for higher income individuals
        if annual_income > 1000000:  # Over 1M KES annually
            recommendations.append({
                "type": "tax_free_investments",
                "title": "Tax-Free Investment Options",
                "description": "Government infrastructure bonds offer tax-free interest income",
                "benefit": "Interest earned is completely exempt from tax",
                "minimum_investment": "Typically KES 50,000",
                "how_to_invest": "Through Central Bank of Kenya during bond issuances",
                "recommendation_strength": 8
            })
        
        # Sort by recommendation strength
        recommendations.sort(key=lambda x: x["recommendation_strength"], reverse=True)
        
        return recommendations[:5]
    
    def _calculate_recommendation_strength(self, product_data: Dict, user_profile: Dict, market_data: Dict) -> float:
        """
        Calculate the strength of a recommendation based on user profile and market data.
        
        Args:
            product_data: Data about the investment product
            user_profile: User's financial profile
            market_data: Current market data
            
        Returns:
            Recommendation strength score (0-10)
        """
        strength = 5.0  # Default neutral score
        
        # Match risk profile
        user_risk = user_profile.get("risk_tolerance", 3)
        product_risk = product_data.get("risk", 3)
        
        # Risk matching (closer risk levels get higher scores)
        risk_diff = abs(user_risk - product_risk)
        if risk_diff == 0:
            strength += 2.5
        elif risk_diff == 1:
            strength += 1.5
        elif risk_diff >= 3:
            strength -= 2.0
        
        # Check investment goals
        user_goals = user_profile.get("investment_goals", ["growth"])
        if "growth" in user_goals and product_risk >= 3:
            strength += 1.0
        if "income" in user_goals and "dividend" in product_data.get("category", ""):
            strength += 1.5
        if "preservation" in user_goals and product_risk <= 2:
            strength += 1.5
        
        # Check investment horizon
        horizon = user_profile.get("investment_horizon", 5)
        if "duration" in product_data:
            product_duration_years = product_data["duration"] / 365  # Convert days to years
            if abs(horizon - product_duration_years) <= 1:
                strength += 1.0
            elif abs(horizon - product_duration_years) >= 3:
                strength -= 1.0
        
        # Adjust based on market trends from market data
        if "market_trend" in market_data:
            sector = product_data.get("sector", "")
            if sector in market_data["market_trend"]:
                trend = market_data["market_trend"][sector]
                if trend == "bullish" and product_risk >= 3:
                    strength += 1.0
                elif trend == "bearish" and product_risk <= 2:
                    strength += 1.0
        
        # Cap the strength between 0 and 10
        return max(0, min(10, strength))
    
    def _calculate_loan_recommendation_strength(self, loan_data: Dict, user_profile: Dict, 
                                             interest_rate: float, average_rate: float, is_mobile: bool = False) -> float:
        """
        Calculate the strength of a loan recommendation.
        
        Args:
            loan_data: Data about the loan product
            user_profile: User's financial profile
            interest_rate: The loan's interest rate
            average_rate: Average market interest rate
            is_mobile: Whether this is a mobile loan
            
        Returns:
            Recommendation strength score (0-10)
        """
        strength = 5.0  # Default neutral score
        
        # Adjust based on interest rate comparison to market average
        rate_diff = average_rate - interest_rate
        if rate_diff > 2:
            strength += 2.0  # Much better than market
        elif rate_diff > 0:
            strength += 1.0  # Better than market
        elif rate_diff < -2:
            strength -= 2.0  # Much worse than market
        elif rate_diff < 0:
            strength -= 1.0  # Worse than market
        
        # Consider loan purpose
        loan_purpose = user_profile.get("loan_purpose", "general")
        loan_type = loan_data.get("type", "personal")
        
        if (loan_purpose == "business" and loan_type == "business") or \
           (loan_purpose == "home_purchase" and loan_type == "mortgage") or \
           (loan_purpose == "emergency" and is_mobile):
            strength += 1.5  # Good match for purpose
        
        # Consider credit score for traditional loans
        if not is_mobile:
            credit_score = user_profile.get("credit_score", "unknown")
            if credit_score == "excellent":
                strength += 1.0  # Better terms likely
            elif credit_score == "poor":
                strength -= 1.0  # May face approval challenges
        
        # Mobile loans get lower recommendation for long-term needs
        if is_mobile and loan_purpose in ["home_purchase", "education", "business"]:
            strength -= 2.0  # Not suitable for long-term financing
        
        # For emergency needs, convenience matters
        if loan_purpose == "emergency" and is_mobile:
            strength += 1.5  # Quick access is valuable in emergencies
        
        # Cap the strength between 0 and 10
        return max(0, min(10, strength))
    
    def _generate_portfolio_allocation(self, user_profile: Dict, recommendations: List[Dict]) -> Dict:
        """
        Generate portfolio allocation recommendation based on user profile and top investment recommendations.
        
        Args:
            user_profile: User's financial profile
            recommendations: List of recommended investments
            
        Returns:
            Portfolio allocation recommendation
        """
        risk_tolerance = user_profile.get("risk_tolerance", 3)
        age = datetime.now().year - int(user_profile.get("birth_year", 1990))
        
        # Basic allocation based on risk tolerance and age
        if risk_tolerance <= 2:  # Conservative
            stocks_allocation = 30
            bonds_allocation = 50
            cash_allocation = 20
            alternative_allocation = 0
        elif risk_tolerance <= 4:  # Moderate
            stocks_allocation = 50
            bonds_allocation = 30
            cash_allocation = 15
            alternative_allocation = 5
        else:  # Aggressive
            stocks_allocation = 70
            bonds_allocation = 15
            cash_allocation = 5
            alternative_allocation = 10
        
        # Age-based adjustments
        if age > 55:
            # Reduce risk for near-retirement
            stocks_allocation = max(20, stocks_allocation - 20)
            bonds_allocation += 15
            cash_allocation += 5
        elif age < 35:
            # Younger investors can take more risk
            stocks_allocation = min(80, stocks_allocation + 10)
            bonds_allocation = max(10, bonds_allocation - 10)
        
        return {
            "type": "portfolio_allocation",
            "title": "Recommended Portfolio Allocation",
            "description": "How to distribute your investment across asset classes",
            "allocation": {
                "stocks": f"{stocks_allocation}%",
                "bonds": f"{bonds_allocation}%",
                "cash": f"{cash_allocation}%",
                "alternatives": f"{alternative_allocation}%"
            },
            "notes": "This allocation is a general guideline. Consider rebalancing your portfolio every 6-12 months.",
            "recommendation_strength": 8
        }
    
    def _get_general_recommendations(self, recommendation_type: str) -> Dict:
        """
        Provide general recommendations when personalized ones cannot be generated.
        
        Args:
            recommendation_type: Type of recommendation requested
            
        Returns:
            General recommendations
        """
        general_recs = {}
        
        if recommendation_type == "all" or recommendation_type == "investment":
            general_recs["investment"] = [
                {
                    "type": "general_investment_advice",
                    "title": "Investment Principles",
                    "principles": [
                        "Diversify your investments across different asset classes",
                        "Start investing early to benefit from compound growth",
                        "Invest regularly, even in small amounts",
                        "Consider your risk tolerance and investment horizon"
                    ]
                },
                {
                    "type": "common_investments",
                    "title": "Common Investment Options in Kenya",
                    "options": [
                        "Government Treasury Bills and Bonds",
                        "Nairobi Securities Exchange (NSE) Stocks",
                        "Money Market Funds",
                        "Real Estate Investment Trusts (REITs)"
                    ]
                }
            ]
        
        if recommendation_type == "all" or recommendation_type == "saving":
            general_recs["saving"] = [
                {
                    "type": "saving_principles",
                    "title": "Saving Strategies",
                    "strategies": [
                        "Build an emergency fund covering 3-6 months of expenses",
                        "Automate your savings with scheduled transfers",
                        "Save at least 20% of your income",
                        "Set specific savings goals"
                    ]
                },
                {
                    "type": "saving_options",
                    "title": "Savings Options in Kenya",
                    "options": [
                        "Fixed Deposit Accounts",
                        "Money Market Funds",
                        "SACCO Savings Accounts",
                        "M-Shwari Lock Savings"
                    ]
                }
            ]
        
        if recommendation_type == "all" or recommendation_type == "loan":
            general_recs["loan"] = [
                {
                    "type": "borrowing_principles",
                    "title": "Responsible Borrowing Principles",
                    "principles": [
                        "Borrow only what you need and can repay",
                        "Compare interest rates and total cost of loans",
                        "Understand all terms and conditions",
                        "Maintain a good credit history"
                    ]
                },
                {
                    "type": "loan_options",
                    "title": "Common Loan Options in Kenya",
                    "options": [
                        "Bank Personal Loans",
                        "SACCO Loans",
                        "Mobile Loans (M-Shwari, KCB M-Pesa, Tala, Branch)",
                        "Secured Loans (Home Equity, Asset Financing)"
                    ]
                }
            ]
        
        if recommendation_type == "all" or recommendation_type == "tax":
            general_recs["tax"] = [
                {
                    "type": "tax_principles",
                    "title": "Tax Optimization Strategies",
                    "strategies": [
                        "Contribute to registered pension schemes",
                        "Consider mortgage interest relief",
                        "Explore insurance premium relief",
                        "Understand PAYE and filing obligations"
                    ]
                },
                {
                    "type": "tax_free_investments",
                    "title": "Tax-Free or Tax-Advantaged Investment Options",
                    "options": [
                        "Infrastructure Bonds",
                        "Home Ownership Savings Plan (HOSP)",
                        "Pension Schemes",
                        "Life Insurance with Investment Component"
                    ]
                }
            ]
        
        return general_recs
    
    def _determine_tax_bracket(self, annual_income: float) -> Dict:
        """
        Determine the user's tax bracket based on annual income.
        
        Args:
            annual_income: User's annual income
            
        Returns:
            Tax bracket information
        """
        if annual_income <= 288000:
            return {"bracket": "Up to KES 288,000", "rate": 10}
        elif annual_income <= 388000:
            return {"bracket": "KES 288,001 - KES 388,000", "rate": 25}
        else:
            return {"bracket": "KES 388,001 and above", "rate": 30}
    
    def _calculate_nhif_contribution(self, monthly_income: float) -> float:
        """
        Calculate NHIF contribution based on monthly income.
        
        Args:
            monthly_income: User's monthly income
            
        Returns:
            Monthly NHIF contribution
        """
        if monthly_income <= 5999:
            return 150
        elif monthly_income <= 7999:
            return 300
        elif monthly_income <= 11999:
            return 400
        elif monthly_income <= 14999:
            return 500
        elif monthly_income <= 19999:
            return 600
        elif monthly_income <= 24999:
            return 750
        elif monthly_income <= 29999:
            return 850
        elif monthly_income <= 34999:
            return 900
        elif monthly_income <= 39999:
            return 950
        elif monthly_income <= 44999:
            return 1000
        elif monthly_income <= 49999:
            return 1100
        elif monthly_income <= 59999:
            return 1200
        elif monthly_income <= 69999:
            return 1300
        elif monthly_income <= 79999:
            return 1400
        elif monthly_income <= 89999:
            return 1500
        else:
            return 1700
    
    def _track_recommendation_event(self, user_id: str, recommendation_type: str, recommendations: Dict) -> None:
        """
        Track recommendation events for analytics and improvement.
        
        Args:
            user_id: The user's ID
            recommendation_type: Type of recommendation generated
            recommendations: The recommendations generated
        """
        try:
            # In a real implementation, this would store recommendation data
            # in a database or analytics system for later analysis
            logger.info(f"Generated {recommendation_type} recommendations for user {user_id}")
        except Exception as e:
            logger.error(f"Error tracking recommendation event: {str(e)}")
    
    async def update_recommendations_based_on_feedback(self, user_id: str, recommendation_id: str, 
                                                   feedback: Dict) -> Dict:
        """
        Update recommendation models based on user feedback.
        
        Args:
            user_id: The user's ID
            recommendation_id: ID of the recommendation receiving feedback
            feedback: Feedback data including rating and comments
            
        Returns:
            Status of the feedback processing
        """
        try:
            # Record feedback
            logger.info(f"Received feedback from user {user_id} on recommendation {recommendation_id}")
            
            # Analyze feedback sentiment
            if "comment" in feedback:
                sentiment = await self.sentiment_analyzer.analyze_text(feedback["comment"])
                logger.info(f"Feedback sentiment: {sentiment}")
            
            # In a real implementation, this would update the recommendation models
            # based on user feedback to improve future recommendations
            
            return {
                "status": "success",
                "message": "Thank you for your feedback. We'll use it to improve our recommendations."
            }
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "An error occurred while processing your feedback."
            }
    
    async def get_recommendation_explanation(self, recommendation_id: str) -> Dict:
        """
        Provide a detailed explanation for a specific recommendation.
        
        Args:
            recommendation_id: ID of the recommendation to explain
            
        Returns:
            Detailed explanation of the recommendation
        """
        try:
            # In a real implementation, this would retrieve the specific recommendation
            # and generate a detailed explanation of the factors that led to it
            return {
                "status": "success",
                "explanation": {
                    "factors_considered": [
                        "Your financial goals and risk tolerance",
                        "Current market conditions",
                        "Your income and expenses",
                        "Your investment horizon"
                    ],
                    "data_sources": [
                        "Your provided financial information",
                        "Real-time market data",
                        "Historical performance of similar investments"
                    ],
                    "regulatory_compliance": "This recommendation adheres to Central Bank of Kenya and Capital Markets Authority guidelines."
                }
            }
        except Exception as e:
            logger.error(f"Error generating recommendation explanation: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "An error occurred while generating the explanation."
            }
