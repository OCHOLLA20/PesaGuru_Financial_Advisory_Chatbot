import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Risk profile constants
RISK_PROFILES = {
    "conservative": {
        "description": "Focuses on preserving capital with minimal risk tolerance",
        "max_equity_allocation": 0.30,
        "volatility_threshold": 0.10,
        "time_horizon": "short",
        "suitable_investments": ["treasury_bills", "money_market_funds", "bonds", "fixed_deposits"]
    },
    "moderate": {
        "description": "Balanced approach with medium risk tolerance",
        "max_equity_allocation": 0.60,
        "volatility_threshold": 0.20,
        "time_horizon": "medium",
        "suitable_investments": ["bonds", "balanced_funds", "blue_chip_stocks", "real_estate"]
    },
    "aggressive": {
        "description": "Growth-focused with high risk tolerance",
        "max_equity_allocation": 0.85,
        "volatility_threshold": 0.35,
        "time_horizon": "long",
        "suitable_investments": ["stocks", "equity_funds", "real_estate", "alternative_investments"]
    },
    "very_aggressive": {
        "description": "Maximum growth with very high risk tolerance",
        "max_equity_allocation": 1.0,
        "volatility_threshold": 0.50,
        "time_horizon": "very_long",
        "suitable_investments": ["growth_stocks", "small_cap_stocks", "crypto", "high_yield_bonds"]
    }
}

# Kenya-specific investment risk parameters
KENYA_MARKET_RISK = {
    "treasury_bills": {
        "risk_score": 1.0,
        "volatility": 0.01,
        "description": "Central Bank of Kenya Treasury Bills",
        "min_investment": 50000,  # KES
        "liquidity": "high"
    },
    "treasury_bonds": {
        "risk_score": 1.5,
        "volatility": 0.03,
        "description": "Government of Kenya Treasury Bonds",
        "min_investment": 50000,  # KES
        "liquidity": "medium"
    },
    "money_market_funds": {
        "risk_score": 1.2,
        "volatility": 0.02,
        "description": "Kenyan Money Market Funds",
        "min_investment": 1000,  # KES
        "liquidity": "high"
    },
    "corporate_bonds": {
        "risk_score": 2.5,
        "volatility": 0.05,
        "description": "Kenyan Corporate Bonds",
        "min_investment": 100000,  # KES
        "liquidity": "medium"
    },
    "nse_blue_chips": {
        "risk_score": 3.0,
        "volatility": 0.15,
        "description": "Nairobi Securities Exchange Blue Chip Stocks",
        "min_investment": 10000,  # KES
        "liquidity": "high"
    },
    "nse_growth_stocks": {
        "risk_score": 4.0,
        "volatility": 0.25,
        "description": "NSE Growth Stocks",
        "min_investment": 10000,  # KES
        "liquidity": "medium"
    },
    "real_estate": {
        "risk_score": 3.5,
        "volatility": 0.10,
        "description": "Kenyan Real Estate",
        "min_investment": 1000000,  # KES
        "liquidity": "low"
    },
    "reits": {
        "risk_score": 3.2,
        "volatility": 0.12,
        "description": "Real Estate Investment Trusts",
        "min_investment": 50000,  # KES
        "liquidity": "medium"
    },
    "equity_funds": {
        "risk_score": 3.5,
        "volatility": 0.20,
        "description": "Kenyan Equity Funds",
        "min_investment": 10000,  # KES
        "liquidity": "high"
    },
    "balanced_funds": {
        "risk_score": 2.5,
        "volatility": 0.12,
        "description": "Balanced Mutual Funds",
        "min_investment": 5000,  # KES
        "liquidity": "high"
    },
    "sacco_deposits": {
        "risk_score": 2.0,
        "volatility": 0.03,
        "description": "SACCO Deposits",
        "min_investment": 1000,  # KES
        "liquidity": "medium"
    },
    "crypto": {
        "risk_score": 5.0,
        "volatility": 0.50,
        "description": "Cryptocurrency",
        "min_investment": 1000,  # KES
        "liquidity": "high"
    },
    "forex": {
        "risk_score": 4.5,
        "volatility": 0.30,
        "description": "Foreign Exchange Trading",
        "min_investment": 10000,  # KES
        "liquidity": "high"
    }
}


class UserRiskProfile:
    """Class to manage user risk profiles based on questionnaire responses and financial data."""
    
    def __init__(self, user_id: str):
        """
        Initialize a user risk profile.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.risk_tolerance_score = 0
        self.risk_profile = "undefined"
        self.age_group = None
        self.income_level = None
        self.financial_goals = []
        self.investment_horizon = None
        self.emergency_fund = False
        self.dependents = 0
        self.investment_experience = None
        self.last_updated = None
        self.questionnaire_responses = {}
        
    def calculate_risk_profile(self) -> str:
        """
        Calculate risk profile based on questionnaire responses and user data.
        
        Returns:
            str: Risk profile category (conservative, moderate, aggressive, very_aggressive)
        """
        if not self.questionnaire_responses:
            logger.warning(f"No questionnaire responses for user {self.user_id}")
            return "undefined"
        
        # Calculate base risk score from questionnaire responses
        score = sum(self.questionnaire_responses.values())
        
        # Apply modifiers based on user characteristics
        
        # Age modifier: younger users can take more risk
        if self.age_group == "18-25":
            score += 5
        elif self.age_group == "26-35":
            score += 3
        elif self.age_group == "36-45":
            score += 1
        elif self.age_group == "46-55":
            score -= 1
        elif self.age_group == "56-65":
            score -= 3
        elif self.age_group == "65+":
            score -= 5
            
        # Income level modifier
        if self.income_level == "high":
            score += 2
        elif self.income_level == "low":
            score -= 2
            
        # Investment horizon modifier
        if self.investment_horizon == "short":  # 0-2 years
            score -= 3
        elif self.investment_horizon == "medium":  # 3-5 years
            score += 0
        elif self.investment_horizon == "long":  # 6-10 years
            score += 2
        elif self.investment_horizon == "very_long":  # 10+ years
            score += 4
            
        # Emergency fund modifier
        if not self.emergency_fund:
            score -= 3
            
        # Dependents modifier
        score -= self.dependents
        
        # Investment experience modifier
        if self.investment_experience == "none":
            score -= 2
        elif self.investment_experience == "novice":
            score -= 1
        elif self.investment_experience == "experienced":
            score += 1
        elif self.investment_experience == "advanced":
            score += 2
            
        # Cap the score between 0 and 100
        self.risk_tolerance_score = max(0, min(100, score))
        
        # Map score to risk profile
        if self.risk_tolerance_score < 25:
            self.risk_profile = "conservative"
        elif self.risk_tolerance_score < 50:
            self.risk_profile = "moderate"
        elif self.risk_tolerance_score < 75:
            self.risk_profile = "aggressive"
        else:
            self.risk_profile = "very_aggressive"
            
        self.last_updated = datetime.now()
        logger.info(f"Calculated risk profile for user {self.user_id}: {self.risk_profile} (score: {self.risk_tolerance_score})")
        
        return self.risk_profile
    
    def process_questionnaire(self, responses: Dict[str, int]) -> None:
        """
        Process questionnaire responses to calculate risk profile.
        
        Args:
            responses: Dictionary of question IDs to numeric response values
        """
        self.questionnaire_responses = responses
        self.calculate_risk_profile()
        
    def update_user_info(self, **kwargs) -> None:
        """
        Update user information attributes.
        
        Args:
            **kwargs: Key-value pairs of attributes to update
        """
        valid_attributes = [
            'age_group', 'income_level', 'financial_goals', 'investment_horizon', 
            'emergency_fund', 'dependents', 'investment_experience'
        ]
        
        for key, value in kwargs.items():
            if key in valid_attributes:
                setattr(self, key, value)
            else:
                logger.warning(f"Invalid attribute: {key}")
                
        # Recalculate risk profile if we have questionnaire responses
        if self.questionnaire_responses:
            self.calculate_risk_profile()
    
    def to_dict(self) -> Dict:
        """
        Convert user risk profile to dictionary.
        
        Returns:
            Dict: Dictionary representation of user risk profile
        """
        return {
            "user_id": self.user_id,
            "risk_tolerance_score": self.risk_tolerance_score,
            "risk_profile": self.risk_profile,
            "age_group": self.age_group,
            "income_level": self.income_level,
            "financial_goals": self.financial_goals,
            "investment_horizon": self.investment_horizon,
            "emergency_fund": self.emergency_fund,
            "dependents": self.dependents,
            "investment_experience": self.investment_experience,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class InvestmentRisk:
    """Class to evaluate risk of specific investment options."""
    
    def __init__(self):
        """Initialize the investment risk evaluator."""
        self.kenya_market_risk = KENYA_MARKET_RISK
        self.current_market_conditions = "normal"  # Can be "normal", "volatile", "bullish", "bearish"
        self.market_risk_adjustments = {
            "normal": 1.0,
            "volatile": 1.2,
            "bullish": 0.9,
            "bearish": 1.1
        }
        
    def get_investment_risk(self, investment_type: str) -> Dict:
        """
        Get risk metrics for a specific investment type.
        
        Args:
            investment_type: Type of investment
            
        Returns:
            Dict: Risk metrics for the investment
            
        Raises:
            ValueError: If investment_type is not recognized
        """
        if investment_type not in self.kenya_market_risk:
            raise ValueError(f"Unknown investment type: {investment_type}")
            
        # Apply market condition adjustment
        risk_data = self.kenya_market_risk[investment_type].copy()
        adjustment = self.market_risk_adjustments.get(self.current_market_conditions, 1.0)
        risk_data["risk_score"] *= adjustment
        risk_data["volatility"] *= adjustment
        
        return risk_data
    
    def compare_investments(self, investment_types: List[str]) -> pd.DataFrame:
        """
        Compare risk metrics for multiple investment types.
        
        Args:
            investment_types: List of investment types to compare
            
        Returns:
            pd.DataFrame: DataFrame with risk comparison
            
        Raises:
            ValueError: If any investment_type is not recognized
        """
        invalid_types = [inv_type for inv_type in investment_types if inv_type not in self.kenya_market_risk]
        if invalid_types:
            raise ValueError(f"Unknown investment types: {invalid_types}")
            
        comparison_data = []
        
        for inv_type in investment_types:
            risk_data = self.get_investment_risk(inv_type)
            comparison_data.append({
                "investment_type": inv_type,
                "description": risk_data["description"],
                "risk_score": risk_data["risk_score"],
                "volatility": risk_data["volatility"],
                "min_investment": risk_data["min_investment"],
                "liquidity": risk_data["liquidity"]
            })
            
        return pd.DataFrame(comparison_data)
    
    def recommend_investments(self, risk_profile: str, amount: float, 
                             preferred_attributes: Optional[List[str]] = None) -> List[Dict]:
        """
        Recommend investments based on user's risk profile and amount.
        
        Args:
            risk_profile: User's risk profile (conservative, moderate, aggressive, very_aggressive)
            amount: Amount to invest (in KES)
            preferred_attributes: Optional list of preferred investment attributes (e.g., 'high_liquidity')
            
        Returns:
            List[Dict]: List of recommended investments with risk metrics
            
        Raises:
            ValueError: If risk_profile is not recognized
        """
        if risk_profile not in RISK_PROFILES:
            raise ValueError(f"Unknown risk profile: {risk_profile}")
            
        profile_data = RISK_PROFILES[risk_profile]
        suitable_investments = profile_data["suitable_investments"]
        
        recommendations = []
        
        for inv_type in self.kenya_market_risk:
            risk_data = self.get_investment_risk(inv_type)
            
            # Filter by suitable investments for risk profile
            if inv_type not in suitable_investments:
                continue
                
            # Filter by minimum investment amount
            if risk_data["min_investment"] > amount:
                continue
                
            # Apply preferred attributes filter if specified
            if preferred_attributes:
                if "high_liquidity" in preferred_attributes and risk_data["liquidity"] != "high":
                    continue
                    
            # Calculate a match score (higher is better)
            match_score = 10
            
            # Adjust score based on how well investment matches profile
            volatility_diff = abs(risk_data["volatility"] - profile_data["volatility_threshold"])
            match_score -= volatility_diff * 10  # Reduce score for volatility differences
            
            # Add recommendation
            recommendations.append({
                "investment_type": inv_type,
                "description": risk_data["description"],
                "risk_score": risk_data["risk_score"],
                "volatility": risk_data["volatility"],
                "min_investment": risk_data["min_investment"],
                "liquidity": risk_data["liquidity"],
                "match_score": max(0, match_score)
            })
            
        # Sort by match score (descending)
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        return recommendations
    
    def update_market_conditions(self, condition: str) -> None:
        """
        Update current market conditions.
        
        Args:
            condition: Market condition (normal, volatile, bullish, bearish)
            
        Raises:
            ValueError: If condition is not recognized
        """
        if condition not in self.market_risk_adjustments:
            raise ValueError(f"Unknown market condition: {condition}")
            
        self.current_market_conditions = condition
        logger.info(f"Updated market conditions to: {condition}")


class PortfolioRisk:
    """Class to analyze risk of investment portfolios."""
    
    def __init__(self, investment_risk: InvestmentRisk):
        """
        Initialize the portfolio risk analyzer.
        
        Args:
            investment_risk: InvestmentRisk instance for investment risk data
        """
        self.investment_risk = investment_risk
        
    def calculate_portfolio_metrics(self, portfolio: Dict[str, float]) -> Dict:
        """
        Calculate risk metrics for a portfolio.
        
        Args:
            portfolio: Dictionary mapping investment types to allocation percentages
            
        Returns:
            Dict: Portfolio risk metrics
            
        Raises:
            ValueError: If investment_type is not recognized
        """
        if not portfolio:
            raise ValueError("Empty portfolio provided")
            
        total_allocation = sum(portfolio.values())
        if abs(total_allocation - 100.0) > 0.01:  # Allow small rounding errors
            raise ValueError(f"Portfolio allocations must sum to 100%, got {total_allocation}%")
        
        # Normalize allocations to decimal (0-1)
        normalized_portfolio = {k: v / 100.0 for k, v in portfolio.items()}
        
        # Calculate weighted average risk score
        weighted_risk = 0
        weighted_volatility = 0
        
        for inv_type, allocation in normalized_portfolio.items():
            risk_data = self.investment_risk.get_investment_risk(inv_type)
            weighted_risk += risk_data["risk_score"] * allocation
            weighted_volatility += risk_data["volatility"] * allocation
            
        # Determine overall risk profile
        if weighted_risk < 1.5:
            risk_profile = "conservative"
        elif weighted_risk < 2.5:
            risk_profile = "moderate"
        elif weighted_risk < 3.5:
            risk_profile = "aggressive"
        else:
            risk_profile = "very_aggressive"
            
        # Calculate diversification score (0-100, higher is better)
        diversification_score = min(100, len(portfolio) * 20)  # Simple proxy based on number of investments
        
        # Build liquidity profile
        liquidity_profile = {"high": 0, "medium": 0, "low": 0}
        for inv_type, allocation in normalized_portfolio.items():
            risk_data = self.investment_risk.get_investment_risk(inv_type)
            liquidity_profile[risk_data["liquidity"]] += allocation
            
        return {
            "weighted_risk_score": weighted_risk,
            "weighted_volatility": weighted_volatility,
            "risk_profile": risk_profile,
            "diversification_score": diversification_score,
            "liquidity_profile": liquidity_profile
        }
    
    def optimize_portfolio(self, target_risk_profile: str, 
                          constraints: Optional[Dict] = None) -> Dict[str, float]:
        """
        Optimize a portfolio allocation for a target risk profile.
        
        Args:
            target_risk_profile: Target risk profile (conservative, moderate, aggressive, very_aggressive)
            constraints: Optional dictionary of constraints (e.g., {"max_crypto": 0.1})
            
        Returns:
            Dict[str, float]: Optimized portfolio allocation
            
        Raises:
            ValueError: If target_risk_profile is not recognized
        """
        if target_risk_profile not in RISK_PROFILES:
            raise ValueError(f"Unknown risk profile: {target_risk_profile}")
            
        profile_data = RISK_PROFILES[target_risk_profile]
        suitable_investments = profile_data["suitable_investments"]
        
        # Simple optimization strategy: allocate more to less risky investments
        # This is a simplified version - a real implementation would use more sophisticated optimization
        
        # Filter suitable investments
        investments = []
        for inv_type in suitable_investments:
            if inv_type in self.investment_risk.kenya_market_risk:
                risk_data = self.investment_risk.get_investment_risk(inv_type)
                investments.append((inv_type, risk_data["risk_score"]))
                
        # Sort by risk score (ascending)
        investments.sort(key=lambda x: x[1])
        
        # Apply basic allocation strategy
        if target_risk_profile == "conservative":
            # Weight towards safer investments
            weights = [0.4, 0.3, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0]
        elif target_risk_profile == "moderate":
            # Balanced allocation
            weights = [0.25, 0.25, 0.2, 0.15, 0.1, 0.05, 0.0, 0.0]
        elif target_risk_profile == "aggressive":
            # Weight towards higher risk/reward
            weights = [0.1, 0.15, 0.2, 0.25, 0.15, 0.1, 0.05, 0.0]
        else:  # very_aggressive
            # Heavily weighted to high risk/reward
            weights = [0.05, 0.1, 0.1, 0.15, 0.2, 0.2, 0.1, 0.1]
            
        # Apply constraints
        if constraints:
            # TODO: Implement constraint handling
            pass
            
        # Create allocation dictionary
        allocation = {}
        for i, (inv_type, _) in enumerate(investments):
            if i < len(weights):
                allocation[inv_type] = weights[i] * 100
                
        # Normalize to ensure sum is 100%
        total = sum(allocation.values())
        allocation = {k: (v / total * 100) for k, v in allocation.items()}
        
        return allocation
    
    def evaluate_portfolio_suitability(self, portfolio: Dict[str, float], 
                                      user_risk_profile: str) -> Dict:
        """
        Evaluate how suitable a portfolio is for a user's risk profile.
        
        Args:
            portfolio: Dictionary mapping investment types to allocation percentages
            user_risk_profile: User's risk profile
            
        Returns:
            Dict: Portfolio suitability evaluation
            
        Raises:
            ValueError: If user_risk_profile is not recognized
        """
        if user_risk_profile not in RISK_PROFILES:
            raise ValueError(f"Unknown risk profile: {user_risk_profile}")
            
        # Calculate portfolio metrics
        metrics = self.calculate_portfolio_metrics(portfolio)
        
        # Get target profile data
        profile_data = RISK_PROFILES[user_risk_profile]
        
        # Calculate match score
        match_score = 100
        
        # Adjust score based on risk profile match
        if metrics["risk_profile"] != user_risk_profile:
            # Penalty for mismatched risk profile
            risk_profiles = ["conservative", "moderate", "aggressive", "very_aggressive"]
            user_index = risk_profiles.index(user_risk_profile)
            portfolio_index = risk_profiles.index(metrics["risk_profile"])
            profile_difference = abs(user_index - portfolio_index)
            match_score -= profile_difference * 20
            
        # Adjust score based on diversification
        if metrics["diversification_score"] < 60:
            match_score -= (60 - metrics["diversification_score"]) / 2
            
        # Adjust score based on liquidity profile
        if user_risk_profile == "conservative" and metrics["liquidity_profile"]["low"] > 0.2:
            match_score -= (metrics["liquidity_profile"]["low"] - 0.2) * 100
            
        # Generate recommendations
        recommendations = []
        
        if metrics["risk_profile"] != user_risk_profile:
            if portfolio_index > user_index:
                recommendations.append("Portfolio is more aggressive than your risk profile suggests. Consider reducing high-risk investments.")
            else:
                recommendations.append("Portfolio is more conservative than your risk profile suggests. Consider adding more growth-oriented investments.")
                
        if metrics["diversification_score"] < 60:
            recommendations.append("Portfolio could benefit from greater diversification across different asset classes.")
            
        if metrics["liquidity_profile"]["high"] < 0.3:
            recommendations.append("Consider increasing allocation to more liquid investments for emergency needs.")
            
        return {
            "match_score": max(0, match_score),
            "portfolio_metrics": metrics,
            "user_risk_profile": user_risk_profile,
            "recommendations": recommendations,
            "is_suitable": match_score >= 70
        }


class RiskEvaluator:
    """Main class for PesaGuru risk assessment functionality."""
    
    def __init__(self):
        """Initialize the risk evaluator with all component services."""
        self.investment_risk = InvestmentRisk()
        self.portfolio_risk = PortfolioRisk(self.investment_risk)
        self.user_profiles = {}  # Dictionary to store UserRiskProfile instances
        
    def get_or_create_user_profile(self, user_id: str) -> UserRiskProfile:
        """
        Get existing user profile or create a new one.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            UserRiskProfile: User's risk profile object
        """
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserRiskProfile(user_id)
            
        return self.user_profiles[user_id]
    
    def process_risk_questionnaire(self, user_id: str, responses: Dict[str, int]) -> Dict:
        """
        Process risk questionnaire responses and update user profile.
        
        Args:
            user_id: Unique identifier for the user
            responses: Dictionary of question IDs to numeric response values
            
        Returns:
            Dict: Updated user risk profile
        """
        user_profile = self.get_or_create_user_profile(user_id)
        user_profile.process_questionnaire(responses)
        
        return user_profile.to_dict()
    
    def update_user_profile(self, user_id: str, **kwargs) -> Dict:
        """
        Update user profile information.
        
        Args:
            user_id: Unique identifier for the user
            **kwargs: Key-value pairs of attributes to update
            
        Returns:
            Dict: Updated user risk profile
        """
        user_profile = self.get_or_create_user_profile(user_id)
        user_profile.update_user_info(**kwargs)
        
        return user_profile.to_dict()
    
    def get_investment_recommendations(self, user_id: str, amount: float, 
                                     preferred_attributes: Optional[List[str]] = None) -> List[Dict]:
        """
        Get investment recommendations for a user.
        
        Args:
            user_id: Unique identifier for the user
            amount: Amount to invest (in KES)
            preferred_attributes: Optional list of preferred investment attributes
            
        Returns:
            List[Dict]: List of recommended investments
            
        Raises:
            ValueError: If user profile is undefined
        """
        user_profile = self.get_or_create_user_profile(user_id)
        
        if user_profile.risk_profile == "undefined":
            raise ValueError(f"Risk profile not defined for user {user_id}")
            
        return self.investment_risk.recommend_investments(
            user_profile.risk_profile, amount, preferred_attributes
        )
    
    def evaluate_investment(self, investment_type: str) -> Dict:
        """
        Evaluate risk metrics for a specific investment.
        
        Args:
            investment_type: Type of investment
            
        Returns:
            Dict: Risk metrics for the investment
        """
        return self.investment_risk.get_investment_risk(investment_type)
    
    def compare_investments(self, investment_types: List[str]) -> Dict:
        """
        Compare risk metrics for multiple investments.
        
        Args:
            investment_types: List of investment types
            
        Returns:
            Dict: Comparison of risk metrics
        """
        df = self.investment_risk.compare_investments(investment_types)
        
        # Convert DataFrame to dictionary for API response
        comparison = {
            "investments": df.to_dict(orient="records"),
            "summary": {
                "lowest_risk": df.loc[df["risk_score"].idxmin(), "investment_type"],
                "highest_risk": df.loc[df["risk_score"].idxmax(), "investment_type"],
                "lowest_min_investment": df.loc[df["min_investment"].idxmin(), "investment_type"],
                "highest_liquidity": df.loc[df["liquidity"] == "high", "investment_type"].tolist()
            }
        }
        
        return comparison
    
    def analyze_portfolio(self, user_id: str, portfolio: Dict[str, float]) -> Dict:
        """
        Analyze a portfolio for a user.
        
        Args:
            user_id: Unique identifier for the user
            portfolio: Dictionary mapping investment types to allocation percentages
            
        Returns:
            Dict: Portfolio analysis results
            
        Raises:
            ValueError: If user profile is undefined
        """
        user_profile = self.get_or_create_user_profile(user_id)
        
        if user_profile.risk_profile == "undefined":
            raise ValueError(f"Risk profile not defined for user {user_id}")
            
        # Calculate portfolio metrics
        metrics = self.portfolio_risk.calculate_portfolio_metrics(portfolio)
        
        # Evaluate portfolio suitability
        suitability = self.portfolio_risk.evaluate_portfolio_suitability(
            portfolio, user_profile.risk_profile
        )
        
        return {
            "user_id": user_id,
            "user_risk_profile": user_profile.risk_profile,
            "portfolio_metrics": metrics,
            "suitability_evaluation": suitability
        }
    
    def optimize_portfolio(self, user_id: str, 
                         constraints: Optional[Dict] = None) -> Dict:
        """
        Optimize portfolio allocation for a user.
        
        Args:
            user_id: Unique identifier for the user
            constraints: Optional dictionary of constraints
            
        Returns:
            Dict: Optimized portfolio allocation
            
        Raises:
            ValueError: If user profile is undefined
        """
        user_profile = self.get_or_create_user_profile(user_id)
        
        if user_profile.risk_profile == "undefined":
            raise ValueError(f"Risk profile not defined for user {user_id}")
            
        # Get optimized allocation
        allocation = self.portfolio_risk.optimize_portfolio(
            user_profile.risk_profile, constraints
        )
        
        # Calculate metrics for the optimized portfolio
        metrics = self.portfolio_risk.calculate_portfolio_metrics(allocation)
        
        return {
            "user_id": user_id,
            "user_risk_profile": user_profile.risk_profile,
            "optimized_allocation": allocation,
            "portfolio_metrics": metrics
        }
    
    def update_market_conditions(self, condition: str) -> None:
        """
        Update current market conditions.
        
        Args:
            condition: Market condition (normal, volatile, bullish, bearish)
        """
        self.investment_risk.update_market_conditions(condition)


# Example usage
if __name__ == "__main__":
    # Initialize risk evaluator
    evaluator = RiskEvaluator()
    
    # Process questionnaire for a user
    user_id = "user123"
    responses = {
        "q1": 3,  # Preference for steady returns (1) vs. maximizing growth (5)
        "q2": 4,  # Comfort with short-term losses (1-5)
        "q3": 3,  # Knowledge of investments (1-5)
        "q4": 4,  # Willingness to take risk (1-5)
        "q5": 3   # Preference for stability (1) vs. growth potential (5)
    }
    
    user_profile = evaluator.process_risk_questionnaire(user_id, responses)
    print(f"User risk profile: {user_profile['risk_profile']}")
    
    # Update user information
    evaluator.update_user_profile(
        user_id,
        age_group="26-35",
        income_level="moderate",
        financial_goals=["retirement", "home_purchase"],
        investment_horizon="medium",
        emergency_fund=True,
        dependents=1,
        investment_experience="novice"
    )
    
    # Get investment recommendations
    recommendations = evaluator.get_investment_recommendations(
        user_id, 
        amount=50000,
        preferred_attributes=["high_liquidity"]
    )
    print(f"Top recommendation: {recommendations[0]['investment_type']}")
    
    # Analyze a portfolio
    portfolio = {
        "treasury_bills": 20,
        "nse_blue_chips": 40,
        "money_market_funds": 30,
        "equity_funds": 10
    }
    
    analysis = evaluator.analyze_portfolio(user_id, portfolio)
    print(f"Portfolio suitability: {analysis['suitability_evaluation']['is_suitable']}")
    
    # Optimize portfolio
    optimized = evaluator.optimize_portfolio(user_id)
    print(f"Optimized allocation: {optimized['optimized_allocation']}")
