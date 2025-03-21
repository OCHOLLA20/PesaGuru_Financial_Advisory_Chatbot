import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union

# Import internal services
try:
    from ai.services.risk_evaluation import RiskEvaluator
    from ai.services.sentiment_analysis import SentimentAnalyzer
    from ai.services.market_analysis import MarketAnalyzer
    from ai.nlp.language_detector import LanguageDetector
    from ai.models.recommendation_model import RecommendationModel
except ImportError:
    # For local development/testing
    logging.warning("Running in standalone mode - service imports not available")
    RiskEvaluator = SentimentAnalyzer = MarketAnalyzer = LanguageDetector = RecommendationModel = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("user_profiler")

class UserProfiler:
    """
    Manages user profiling for personalized financial advice.
    Collects, analyzes, and maintains user financial profiles.
    """
    
    # Define constants for profile segmentation
    RISK_CATEGORIES = {
        1: "Conservative",
        2: "Moderately Conservative", 
        3: "Balanced",
        4: "Moderately Aggressive",
        5: "Aggressive"
    }
    
    INCOME_CATEGORIES = {
        "low": {"min": 0, "max": 50000},         # Under 50K KES
        "medium": {"min": 50000, "max": 150000}, # 50K-150K KES
        "high": {"min": 150000, "max": 500000},  # 150K-500K KES
        "very_high": {"min": 500000, "max": float('inf')}  # Over 500K KES
    }
    
    LIFE_STAGES = [
        "student", 
        "young_professional", 
        "mid_career", 
        "pre_retirement", 
        "retirement"
    ]
    
    # Financial product categories - Kenya specific
    FINANCIAL_PRODUCTS = {
        "savings": ["M-Pesa Lock", "KCB Goal Savings", "Equity Jijenge"],
        "investments": ["NSE Stocks", "T-Bills", "T-Bonds", "Unit Trusts", "REITs"],
        "loans": ["M-Shwari", "KCB-MPesa", "Fuliza", "Branch", "Tala"],
        "insurance": ["NHIF", "Private Health Insurance", "Life Insurance"],
        "retirement": ["NSSF", "Personal Pension Plans"]
    }

    def __init__(self, risk_evaluator=None, sentiment_analyzer=None, 
                 market_analyzer=None, language_detector=None,
                 recommendation_model=None, encryption_service=None):
        """
        Initialize the user profiler with required services.
        
        Args:
            risk_evaluator: Service for evaluating financial risk
            sentiment_analyzer: Service for analyzing user sentiment
            market_analyzer: Service for market data and trends
            language_detector: Service for detecting user language
            recommendation_model: ML model for generating recommendations
            encryption_service: Service for encrypting sensitive user data
        """
        # Initialize services
        self.risk_evaluator = risk_evaluator or RiskEvaluator() if RiskEvaluator else None
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer() if SentimentAnalyzer else None
        self.market_analyzer = market_analyzer or MarketAnalyzer() if MarketAnalyzer else None
        self.language_detector = language_detector or LanguageDetector() if LanguageDetector else None
        self.recommendation_model = recommendation_model or RecommendationModel() if RecommendationModel else None
        self.encryption_service = encryption_service
        
        logger.info("UserProfiler initialized")
        
    def create_new_profile(self, user_id: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile with initial data.
        
        Args:
            user_id: Unique identifier for the user
            initial_data: Dictionary containing initial profile data
            
        Returns:
            Dictionary containing the created user profile
        """
        try:
            # Initialize basic profile structure
            profile = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "basic_info": self._extract_basic_info(initial_data),
                "financial_status": self._extract_financial_status(initial_data),
                "risk_profile": self._initialize_risk_profile(initial_data),
                "financial_goals": self._extract_financial_goals(initial_data),
                "behavior": {
                    "interaction_history": [],
                    "financial_actions": [],
                    "product_interests": []
                },
                "preferences": self._extract_preferences(initial_data),
                "recommendations": {
                    "history": [],
                    "current": [],
                    "dismissed": []
                },
                "language": self._detect_preferred_language(initial_data)
            }
            
            logger.info(f"Created new profile for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating profile for user {user_id}: {str(e)}")
            raise
    
    def update_profile(self, profile: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing user profile with new data.
        
        Args:
            profile: The current user profile
            new_data: Dictionary containing new data to update the profile
            
        Returns:
            Updated user profile
        """
        try:
            # Update timestamp
            profile["updated_at"] = datetime.now().isoformat()
            
            # Update basic information if provided
            if "basic_info" in new_data:
                profile["basic_info"].update(new_data["basic_info"])
            
            # Update financial status if provided
            if "financial_status" in new_data:
                profile["financial_status"].update(new_data["financial_status"])
                
                # Recalculate derived metrics
                profile["financial_status"]["savings_rate"] = self._calculate_savings_rate(
                    profile["financial_status"]["income"],
                    profile["financial_status"]["expenses"],
                    profile["financial_status"]["savings"]
                )
                
                profile["financial_status"]["debt_to_income"] = self._calculate_debt_to_income(
                    profile["financial_status"]["income"],
                    profile["financial_status"]["debt"]
                )
            
            # Update risk profile if needed
            if "risk_questionnaire" in new_data:
                profile["risk_profile"] = self._evaluate_risk_profile(new_data["risk_questionnaire"])
            
            # Update financial goals
            if "financial_goals" in new_data:
                self._update_financial_goals(profile, new_data["financial_goals"])
            
            # Update behavior tracking
            if "behavior" in new_data:
                self._update_behavior_tracking(profile, new_data["behavior"])
            
            # Update preferences
            if "preferences" in new_data:
                profile["preferences"].update(new_data["preferences"])
            
            # Update language preference if detected
            if "language" in new_data:
                profile["language"] = new_data["language"]
            
            # Generate new recommendations based on updated profile
            profile["recommendations"]["current"] = self.generate_recommendations(profile)
            
            logger.info(f"Updated profile for user {profile['user_id']}")
            return profile
            
        except Exception as e:
            logger.error(f"Error updating profile for user {profile['user_id']}: {str(e)}")
            raise
    
    def process_conversation(self, profile: Dict[str, Any], conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile based on conversation data.
        
        Args:
            profile: Current user profile
            conversation_data: Data extracted from conversation with the chatbot
            
        Returns:
            Updated user profile
        """
        try:
            # Extract financial sentiments from conversation
            if self.sentiment_analyzer and "message" in conversation_data:
                sentiment = self.sentiment_analyzer.analyze_financial_sentiment(conversation_data["message"])
                
                # Track detected sentiment
                financial_concerns = sentiment.get("financial_concerns", [])
                financial_interests = sentiment.get("financial_interests", [])
                financial_sentiment = sentiment.get("overall_sentiment", "neutral")
                
                # Update behavior tracking with conversation insights
                behavior_update = {
                    "behavior": {
                        "financial_concerns": financial_concerns,
                        "financial_interests": financial_interests,
                        "financial_sentiment": financial_sentiment,
                        "interaction_history": {
                            "timestamp": datetime.now().isoformat(),
                            "interaction_type": "conversation",
                            "details": {
                                "intent": conversation_data.get("intent", "unknown"),
                                "context": conversation_data.get("context", {}),
                                "entities": conversation_data.get("entities", [])
                            }
                        }
                    }
                }
                
                # Track product interests detected in conversation
                if "product_interests" in sentiment:
                    behavior_update["behavior"]["product_interests"] = sentiment["product_interests"]
                
                # Update the profile with the new behavior data
                profile = self.update_profile(profile, behavior_update)
                
                # Detect language if not already set
                if not profile.get("language") and "message" in conversation_data:
                    if self.language_detector:
                        detected_language = self.language_detector.detect(conversation_data["message"])
                        profile["language"] = detected_language
                
                logger.info(f"Processed conversation data for user {profile['user_id']}")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error processing conversation for user {profile['user_id']}: {str(e)}")
            return profile  # Return unchanged profile on error
    
    def generate_recommendations(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate personalized financial recommendations based on user profile.
        
        Args:
            profile: User profile data
            
        Returns:
            List of recommendations for the user
        """
        try:
            recommendations = []
            
            if self.recommendation_model:
                # Use ML model for sophisticated recommendations
                recommendations = self.recommendation_model.predict(profile)
            else:
                # Fallback to rule-based recommendations
                recommendations = self._rule_based_recommendations(profile)
            
            # Enrich recommendations with market data if available
            if self.market_analyzer:
                recommendations = self._enrich_with_market_data(recommendations)
            
            # Apply risk-based filtering
            recommendations = self._filter_by_risk_tolerance(recommendations, profile["risk_profile"])
            
            # Prioritize by relevance to financial goals
            recommendations = self._prioritize_by_goals(recommendations, profile["financial_goals"])
            
            # Localize recommendations (language, currency, etc.)
            recommendations = self._localize_recommendations(recommendations, profile["language"])
            
            logger.info(f"Generated {len(recommendations)} recommendations for user {profile['user_id']}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for user {profile['user_id']}: {str(e)}")
            return []  # Return empty recommendations on error
    
    def _extract_basic_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate basic user information."""
        basic_info = {
            "name": data.get("name", ""),
            "age": data.get("age", 0),
            "gender": data.get("gender", ""),
            "location": data.get("location", ""),
            "occupation": data.get("occupation", ""),
            "education": data.get("education", ""),
            "life_stage": self._determine_life_stage(data),
            "family_size": data.get("family_size", 0)
        }
        return basic_info
    
    def _extract_financial_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process financial status information."""
        income = data.get("income", 0)
        expenses = data.get("expenses", 0)
        savings = data.get("savings", 0)
        debt = data.get("debt", 0)
        
        financial_status = {
            "income": income,
            "income_category": self._categorize_income(income),
            "income_sources": data.get("income_sources", []),
            "expenses": expenses,
            "expense_categories": data.get("expense_categories", {}),
            "savings": savings,
            "savings_rate": self._calculate_savings_rate(income, expenses, savings),
            "assets": data.get("assets", {}),
            "debt": debt,
            "debt_categories": data.get("debt_categories", {}),
            "debt_to_income": self._calculate_debt_to_income(income, debt),
            "net_worth": (data.get("assets_value", 0) - debt),
            "credit_score": data.get("credit_score", None),
            "existing_financial_products": data.get("existing_financial_products", [])
        }
        return financial_status
    
    def _initialize_risk_profile(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize risk profile based on available data."""
        if "risk_questionnaire" in data:
            return self._evaluate_risk_profile(data["risk_questionnaire"])
        else:
            # Default conservative risk profile
            return {
                "risk_tolerance_score": 2,  # Default to moderately conservative
                "risk_tolerance_category": "Moderately Conservative",
                "investment_horizon": data.get("investment_horizon", "medium"),
                "loss_tolerance": data.get("loss_tolerance", "low"),
                "investment_experience": data.get("investment_experience", "beginner"),
                "last_evaluated": datetime.now().isoformat()
            }
    
    def _evaluate_risk_profile(self, questionnaire: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate risk profile based on questionnaire responses."""
        try:
            if self.risk_evaluator:
                risk_profile = self.risk_evaluator.evaluate(questionnaire)
            else:
                # Simplified risk evaluation
                score = 0
                
                # Age factor (younger = higher risk tolerance)
                age = questionnaire.get("age", 35)
                if age < 30:
                    score += 1
                elif age < 50:
                    score += 0.5
                
                # Investment horizon (longer = higher risk tolerance)
                horizon = questionnaire.get("investment_horizon", "medium")
                if horizon == "long":
                    score += 1
                elif horizon == "medium":
                    score += 0.5
                
                # Loss tolerance (higher = higher risk tolerance)
                loss_tolerance = questionnaire.get("loss_tolerance", "low")
                if loss_tolerance == "high":
                    score += 1.5
                elif loss_tolerance == "medium":
                    score += 0.75
                
                # Investment experience (more = higher risk tolerance)
                experience = questionnaire.get("investment_experience", "beginner")
                if experience == "expert":
                    score += 1
                elif experience == "intermediate":
                    score += 0.5
                
                # Financial stability (higher = higher risk tolerance)
                stability = questionnaire.get("financial_stability", "medium")
                if stability == "high":
                    score += 1
                elif stability == "medium":
                    score += 0.5
                
                # Map score to risk tolerance category (1-5)
                risk_score = min(5, max(1, round(score + 1)))
                
                risk_profile = {
                    "risk_tolerance_score": risk_score,
                    "risk_tolerance_category": self.RISK_CATEGORIES[risk_score],
                    "investment_horizon": questionnaire.get("investment_horizon", "medium"),
                    "loss_tolerance": questionnaire.get("loss_tolerance", "low"),
                    "investment_experience": questionnaire.get("investment_experience", "beginner"),
                    "last_evaluated": datetime.now().isoformat()
                }
            
            return risk_profile
            
        except Exception as e:
            logger.error(f"Error evaluating risk profile: {str(e)}")
            # Return default risk profile on error
            return {
                "risk_tolerance_score": 2,
                "risk_tolerance_category": "Moderately Conservative",
                "investment_horizon": "medium",
                "loss_tolerance": "low",
                "investment_experience": "beginner",
                "last_evaluated": datetime.now().isoformat()
            }
    
    def _extract_financial_goals(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and validate financial goals."""
        financial_goals = data.get("financial_goals", [])
        
        # If no goals provided, create default ones based on life stage
        if not financial_goals:
            life_stage = self._determine_life_stage(data)
            financial_goals = self._get_default_goals_by_life_stage(life_stage)
        
        # Validate and format each goal
        formatted_goals = []
        for goal in financial_goals:
            formatted_goal = {
                "id": goal.get("id", f"goal_{len(formatted_goals)+1}"),
                "name": goal.get("name", "Unnamed Goal"),
                "type": goal.get("type", "savings"),
                "target_amount": goal.get("target_amount", 0),
                "current_amount": goal.get("current_amount", 0),
                "target_date": goal.get("target_date", ""),
                "priority": goal.get("priority", "medium"),
                "status": goal.get("status", "active"),
                "created_at": goal.get("created_at", datetime.now().isoformat()),
                "progress": self._calculate_goal_progress(
                    goal.get("current_amount", 0), 
                    goal.get("target_amount", 0)
                )
            }
            formatted_goals.append(formatted_goal)
        
        return formatted_goals
    
    def _extract_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract user preferences."""
        return {
            "communication": {
                "preferred_language": data.get("preferred_language", "English"),
                "notification_frequency": data.get("notification_frequency", "weekly"),
                "notification_channels": data.get("notification_channels", ["app"])
            },
            "app": {
                "theme": data.get("theme", "light"),
                "dashboard_layout": data.get("dashboard_layout", "default")
            },
            "products": {
                "favorite_categories": data.get("favorite_categories", []),
                "excluded_categories": data.get("excluded_categories", [])
            }
        }
    
    def _update_financial_goals(self, profile: Dict[str, Any], new_goals: List[Dict[str, Any]]) -> None:
        """Update financial goals in the profile."""
        # Process new goals
        for new_goal in new_goals:
            goal_id = new_goal.get("id", "")
            
            # Check if this is an update to an existing goal
            existing_goal_index = next(
                (i for i, g in enumerate(profile["financial_goals"]) if g["id"] == goal_id), 
                None
            )
            
            if existing_goal_index is not None:
                # Update existing goal
                profile["financial_goals"][existing_goal_index].update(new_goal)
                # Recalculate progress
                profile["financial_goals"][existing_goal_index]["progress"] = self._calculate_goal_progress(
                    profile["financial_goals"][existing_goal_index]["current_amount"],
                    profile["financial_goals"][existing_goal_index]["target_amount"]
                )
            else:
                # Add new goal
                formatted_goal = {
                    "id": goal_id or f"goal_{len(profile['financial_goals'])+1}",
                    "name": new_goal.get("name", "Unnamed Goal"),
                    "type": new_goal.get("type", "savings"),
                    "target_amount": new_goal.get("target_amount", 0),
                    "current_amount": new_goal.get("current_amount", 0),
                    "target_date": new_goal.get("target_date", ""),
                    "priority": new_goal.get("priority", "medium"),
                    "status": new_goal.get("status", "active"),
                    "created_at": new_goal.get("created_at", datetime.now().isoformat()),
                    "progress": self._calculate_goal_progress(
                        new_goal.get("current_amount", 0), 
                        new_goal.get("target_amount", 0)
                    )
                }
                profile["financial_goals"].append(formatted_goal)
    
    def _update_behavior_tracking(self, profile: Dict[str, Any], behavior_data: Dict[str, Any]) -> None:
        """Update behavior tracking in the profile."""
        # Track interaction history
        if "interaction" in behavior_data:
            profile["behavior"]["interaction_history"].append({
                "timestamp": datetime.now().isoformat(),
                "interaction_type": behavior_data["interaction"].get("type", "other"),
                "details": behavior_data["interaction"].get("details", {})
            })
        
        # Track financial actions
        if "financial_action" in behavior_data:
            profile["behavior"]["financial_actions"].append({
                "timestamp": datetime.now().isoformat(),
                "action_type": behavior_data["financial_action"].get("type", "other"),
                "details": behavior_data["financial_action"].get("details", {})
            })
        
        # Track product interests
        if "product_interest" in behavior_data:
            product = behavior_data["product_interest"]
            profile["behavior"]["product_interests"].append({
                "timestamp": datetime.now().isoformat(),
                "product_type": product.get("type", "other"),
                "product_name": product.get("name", ""),
                "interest_level": product.get("interest_level", "medium"),
                "context": product.get("context", "")
            })
    
    def _rule_based_recommendations(self, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rule-based recommendations when ML model is unavailable."""
        recommendations = []
        
        # Extract key profile information
        risk_score = profile["risk_profile"]["risk_tolerance_score"]
        income = profile["financial_status"]["income"]
        savings_rate = profile["financial_status"]["savings_rate"]
        debt_to_income = profile["financial_status"]["debt_to_income"]
        life_stage = profile["basic_info"]["life_stage"]
        
        # 1. Emergency Fund Recommendation
        if profile["financial_status"].get("emergency_fund", 0) < (income * 3):
            recommendations.append({
                "id": "rec_emergency_fund",
                "type": "emergency_fund",
                "category": "savings",
                "title": "Build Emergency Fund",
                "description": "Build an emergency fund with 3-6 months of expenses",
                "priority": "high",
                "products": ["M-Pesa Lock", "KCB Goal Savings"],
                "risk_level": 1
            })
        
        # 2. Savings Recommendations
        if savings_rate < 0.2:  # Less than 20% savings rate
            recommendations.append({
                "id": "rec_increase_savings",
                "type": "savings_improvement",
                "category": "savings",
                "title": "Increase Savings Rate",
                "description": "Aim to save at least 20% of your income",
                "priority": "high",
                "steps": ["Track expenses", "Create a budget", "Cut unnecessary spending"],
                "risk_level": 1
            })
        
        # 3. Debt Management Recommendations
        if debt_to_income > 0.4:  # Debt-to-income ratio over 40%
            recommendations.append({
                "id": "rec_debt_reduction",
                "type": "debt_management",
                "category": "debt",
                "title": "Reduce Debt Burden",
                "description": "Create a plan to reduce your debt-to-income ratio",
                "priority": "high",
                "steps": ["List all debts", "Focus on high-interest debt", "Consider debt consolidation"],
                "risk_level": 1
            })
        
        # 4. Investment Recommendations based on risk profile
        investment_rec = {
            "id": "rec_investment_plan",
            "type": "investment",
            "category": "investment",
            "title": "Investment Portfolio Recommendation",
            "priority": "medium",
            "risk_level": risk_score
        }
        
        if risk_score == 1:  # Conservative
            investment_rec["description"] = "Conservative investment strategy for capital preservation"
            investment_rec["products"] = ["Treasury Bills", "Money Market Funds"]
            investment_rec["allocation"] = {"T-Bills": "70%", "Money Market": "30%"}
        elif risk_score == 2:  # Moderately Conservative
            investment_rec["description"] = "Moderately conservative strategy with some growth potential"
            investment_rec["products"] = ["Treasury Bonds", "Money Market Funds", "Blue-chip Stocks"]
            investment_rec["allocation"] = {"T-Bonds": "60%", "Money Market": "30%", "Stocks": "10%"}
        elif risk_score == 3:  # Balanced
            investment_rec["description"] = "Balanced investment strategy for long-term growth"
            investment_rec["products"] = ["Treasury Bonds", "REITS", "NSE Stocks", "Unit Trusts"]
            investment_rec["allocation"] = {"T-Bonds": "40%", "REITS": "15%", "Stocks": "35%", "Unit Trusts": "10%"}
        elif risk_score == 4:  # Moderately Aggressive
            investment_rec["description"] = "Growth-oriented investment strategy"
            investment_rec["products"] = ["NSE Stocks", "Unit Trusts", "REITs", "Treasury Bonds"]
            investment_rec["allocation"] = {"Stocks": "55%", "Unit Trusts": "20%", "REITs": "15%", "T-Bonds": "10%"}
        else:  # Aggressive
            investment_rec["description"] = "Aggressive growth investment strategy"
            investment_rec["products"] = ["NSE Stocks", "Growth Unit Trusts", "REITs"]
            investment_rec["allocation"] = {"Stocks": "70%", "Growth Unit Trusts": "20%", "REITs": "10%"}
        
        recommendations.append(investment_rec)
        
        # 5. Life Stage-specific Recommendations
        if life_stage == "student":
            recommendations.append({
                "id": "rec_student_finance",
                "type": "education",
                "category": "education",
                "title": "Student Financial Planning",
                "description": "Build good financial habits while in school",
                "priority": "medium",
                "steps": ["Create a student budget", "Start small savings", "Avoid unnecessary debt"],
                "risk_level": 1
            })
        elif life_stage == "young_professional":
            recommendations.append({
                "id": "rec_career_start",
                "type": "career",
                "category": "planning",
                "title": "Early Career Financial Steps",
                "description": "Set yourself up for financial success in your career",
                "priority": "medium",
                "steps": ["Maximize retirement contributions", "Build emergency fund", "Start investing early"],
                "risk_level": 2
            })
        elif life_stage == "mid_career":
            recommendations.append({
                "id": "rec_family_planning",
                "type": "family",
                "category": "planning",
                "title": "Family Financial Planning",
                "description": "Financial strategies for family needs",
                "priority": "medium",
                "steps": ["Education savings", "Life insurance review", "Estate planning basics"],
                "risk_level": 3
            })
        elif life_stage == "pre_retirement":
            recommendations.append({
                "id": "rec_retirement_prep",
                "type": "retirement",
                "category": "planning",
                "title": "Preparing for Retirement",
                "description": "Steps to prepare for upcoming retirement",
                "priority": "high",
                "steps": ["Retirement income planning", "Healthcare planning", "Shift to more conservative investments"],
                "risk_level": 2
            })
        elif life_stage == "retirement":
            recommendations.append({
                "id": "rec_retirement_income",
                "type": "retirement",
                "category": "income",
                "title": "Retirement Income Strategies",
                "description": "Maximize retirement income and minimize tax burden",
                "priority": "high",
                "steps": ["Withdrawal strategy", "Tax-efficient income", "Legacy planning"],
                "risk_level": 1
            })
        
        return recommendations
    
    def _enrich_with_market_data(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich recommendations with current market data."""
        if not self.market_analyzer:
            return recommendations
            
        try:
            # Get current market data
            market_data = self.market_analyzer.get_current_market_data()
            
            for i, rec in enumerate(recommendations):
                # For investment recommendations, add current market info
                if rec["type"] == "investment":
                    for product in rec.get("products", []):
                        if product == "NSE Stocks" and "nse_index" in market_data:
                            recommendations[i]["market_info"] = {
                                "nse_index": market_data["nse_index"],
                                "nse_trend": market_data.get("nse_trend", "stable"),
                                "top_performers": market_data.get("top_performers", [])
                            }
                        elif product == "Treasury Bills" and "t_bill_rates" in market_data:
                            recommendations[i]["market_info"] = {
                                "t_bill_rates": market_data["t_bill_rates"],
                                "t_bill_trend": market_data.get("t_bill_trend", "stable")
                            }
                        elif product == "Treasury Bonds" and "t_bond_rates" in market_data:
                            recommendations[i]["market_info"] = {
                                "t_bond_rates": market_data["t_bond_rates"],
                                "t_bond_trend": market_data.get("t_bond_trend", "stable")
                            }
                
                # For loan recommendations, add current interest rates
                if rec["type"] == "loan" and "loan_rates" in market_data:
                    recommendations[i]["market_info"] = {
                        "average_rates": market_data["loan_rates"],
                        "rate_trend": market_data.get("loan_rate_trend", "stable")
                    }
            
            return recommendations
        except Exception as e:
            logger.error(f"Error enriching recommendations with market data: {str(e)}")
            return recommendations
    
    def _filter_by_risk_tolerance(self, recommendations: List[Dict[str, Any]], 
                                 risk_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter recommendations based on user's risk tolerance."""
        user_risk_score = risk_profile["risk_tolerance_score"]
        
        filtered_recommendations = []
        for rec in recommendations:
            rec_risk_level = rec.get("risk_level", 3)
            
            # Skip recommendations that are too risky for the user
            if rec_risk_level > user_risk_score + 1:
                continue
                
            # Add warning for recommendations slightly above user's comfort zone
            if rec_risk_level > user_risk_score:
                rec["warning"] = "This recommendation is slightly above your usual risk tolerance."
                
            filtered_recommendations.append(rec)
            
        return filtered_recommendations
    
    def _prioritize_by_goals(self, recommendations: List[Dict[str, Any]], 
                            goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize recommendations based on user's financial goals."""
        # Extract goal types
        goal_types = [goal["type"] for goal in goals]
        
        # Function to calculate goal alignment score
        def goal_alignment_score(rec):
            if rec["type"] in goal_types:
                return 2
            elif rec["category"] in goal_types:
                return 1
            else:
                return 0
        
        # Sort recommendations by priority and goal alignment
        priority_values = {"high": 3, "medium": 2, "low": 1}
        
        sorted_recommendations = sorted(
            recommendations,
            key=lambda r: (
                priority_values.get(r.get("priority", "medium"), 2),
                goal_alignment_score(r)
            ),
            reverse=True
        )
        
        return sorted_recommendations
    
    def _localize_recommendations(self, recommendations: List[Dict[str, Any]], 
                                language: str) -> List[Dict[str, Any]]:
        """Localize recommendations based on user's language preference."""
        # Currently supporting English and Swahili
        if language.lower() != "swahili":
            return recommendations
            
        # Simple dictionary of English to Swahili translations for common terms
        translations = {
            "Build Emergency Fund": "Jenga Akiba ya Dharura",
            "Increase Savings Rate": "Ongeza Kiwango cha Akiba",
            "Reduce Debt Burden": "Punguza Mzigo wa Madeni",
            "Investment Portfolio Recommendation": "Mapendekezo ya Uwekezaji",
            "Student Financial Planning": "Mipango ya Kifedha ya Wanafunzi",
            "Early Career Financial Steps": "Hatua za Kifedha za Mwanzo wa Kazi",
            "Family Financial Planning": "Mipango ya Kifedha ya Familia",
            "Preparing for Retirement": "Kujiandaa kwa Kustaafu",
            "Retirement Income Strategies": "Mikakati ya Mapato ya Uzeeni"
        }
        
        # Translate recommendations
        for i, rec in enumerate(recommendations):
            if rec["title"] in translations:
                recommendations[i]["title"] = translations[rec["title"]]
                
            # Also provide original English version
            recommendations[i]["title_english"] = rec["title"]
            
            # Add notice about language
            recommendations[i]["language"] = "swahili"
            
        return recommendations
    
    def _determine_life_stage(self, data: Dict[str, Any]) -> str:
        """Determine user's life stage based on provided data."""
        age = data.get("age", 30)
        occupation = data.get("occupation", "").lower()
        has_children = data.get("has_children", False)
        is_retired = data.get("is_retired", False)
        
        if is_retired:
            return "retirement"
        elif age >= 55:
            return "pre_retirement"
        elif age >= 35:
            return "mid_career"
        elif age >= 23:
            return "young_professional"
        else:
            if "student" in occupation:
                return "student"
            else:
                return "young_professional"
    
    def _categorize_income(self, income: float) -> str:
        """Categorize income level."""
        for category, limits in self.INCOME_CATEGORIES.items():
            if limits["min"] <= income < limits["max"]:
                return category
        return "low"  # Default category
    
    def _calculate_savings_rate(self, income: float, expenses: float, savings: float) -> float:
        """Calculate savings rate as a percentage of income."""
        if income <= 0:
            return 0
            
        # If savings is provided directly
        if savings > 0:
            return min(1.0, savings / income)
            
        # Otherwise calculate from income and expenses
        if expenses < income:
            return (income - expenses) / income
        else:
            return 0
    
    def _calculate_debt_to_income(self, income: float, debt: float) -> float:
        """Calculate debt-to-income ratio."""
        if income <= 0:
            return 0
        return debt / income
    
    def _calculate_goal_progress(self, current_amount: float, target_amount: float) -> float:
        """Calculate progress percentage towards a financial goal."""
        if target_amount <= 0:
            return 0
        return min(1.0, current_amount / target_amount)
    
    def _get_default_goals_by_life_stage(self, life_stage: str) -> List[Dict[str, Any]]:
        """Get default financial goals based on life stage."""
        default_goals = []
        
        if life_stage == "student":
            default_goals = [
                {
                    "id": "goal_1",
                    "name": "Emergency Fund",
                    "type": "savings",
                    "target_amount": 30000,  # 30K KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_2",
                    "name": "Education Fund",
                    "type": "education",
                    "target_amount": 50000,  # 50K KES
                    "current_amount": 0,
                    "priority": "medium"
                }
            ]
        elif life_stage == "young_professional":
            default_goals = [
                {
                    "id": "goal_1",
                    "name": "Emergency Fund",
                    "type": "savings",
                    "target_amount": 100000,  # 100K KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_2",
                    "name": "Investment Start",
                    "type": "investment",
                    "target_amount": 50000,  # 50K KES
                    "current_amount": 0,
                    "priority": "medium"
                }
            ]
        elif life_stage == "mid_career":
            default_goals = [
                {
                    "id": "goal_1",
                    "name": "Emergency Fund",
                    "type": "savings",
                    "target_amount": 300000,  # 300K KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_2",
                    "name": "Retirement Savings",
                    "type": "retirement",
                    "target_amount": 1000000,  # 1M KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_3",
                    "name": "Children's Education",
                    "type": "education",
                    "target_amount": 500000,  # 500K KES
                    "current_amount": 0,
                    "priority": "medium"
                }
            ]
        elif life_stage == "pre_retirement":
            default_goals = [
                {
                    "id": "goal_1",
                    "name": "Retirement Fund",
                    "type": "retirement",
                    "target_amount": 3000000,  # 3M KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_2",
                    "name": "Emergency Fund",
                    "type": "savings",
                    "target_amount": 500000,  # 500K KES
                    "current_amount": 0,
                    "priority": "medium"
                }
            ]
        elif life_stage == "retirement":
            default_goals = [
                {
                    "id": "goal_1",
                    "name": "Income Preservation",
                    "type": "income",
                    "target_amount": 1000000,  # 1M KES
                    "current_amount": 0,
                    "priority": "high"
                },
                {
                    "id": "goal_2",
                    "name": "Healthcare Fund",
                    "type": "health",
                    "target_amount": 500000,  # 500K KES
                    "current_amount": 0,
                    "priority": "high"
                }
            ]
        
        return default_goals
    
    def _detect_preferred_language(self, data: Dict[str, Any]) -> str:
        """Detect user's preferred language."""
        # Check if explicitly provided
        if "preferred_language" in data:
            return data["preferred_language"]
            
        # Check location for hints
        location = data.get("location", "").lower()
        if location in ["nairobi", "mombasa", "kisumu", "nakuru", "kenya"]:
            # Default to English for Kenyan users, but note that Swahili is also common
            return "English"
            
        # Default
        return "English"

# If running as a standalone module
if __name__ == "__main__":
    profiler = UserProfiler()
    
    # Test with sample data
    sample_data = {
        "name": "John Kamau",
        "age": 32,
        "gender": "male",
        "location": "Nairobi",
        "occupation": "Software Engineer",
        "income": 120000,
        "expenses": 80000,
        "savings": 40000,
        "debt": 200000,
        "has_children": True,
        "risk_questionnaire": {
            "age": 32,
            "investment_horizon": "medium",
            "loss_tolerance": "medium",
            "investment_experience": "intermediate",
            "financial_stability": "medium"
        }
    }
    
    # Create a profile
    profile = profiler.create_new_profile("user123", sample_data)
    
    # Generate recommendations
    recommendations = profiler.generate_recommendations(profile)
    
    # Print results
    print("User Profile Created:")
    print(f"Risk Profile: {profile['risk_profile']['risk_tolerance_category']}")
    print(f"Life Stage: {profile['basic_info']['life_stage']}")
    print(f"Savings Rate: {profile['financial_status']['savings_rate']:.2%}")
    print(f"Debt-to-Income: {profile['financial_status']['debt_to_income']:.2%}")
    
    print("\nTop Recommendations:")
    for rec in recommendations[:3]:
        print(f"- {rec['title']}: {rec['description']}")
