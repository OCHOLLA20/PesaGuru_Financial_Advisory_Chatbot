import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables and configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.pesaguru.co.ke")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-replace-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour in seconds

# Define Pydantic models for data validation
class UserBase(BaseModel):
    email: str
    
class UserCreate(UserBase):
    password: str
    full_name: str
    phone_number: str
    
class UserProfile(UserBase):
    user_id: str
    full_name: str
    phone_number: str
    risk_profile: Optional[str] = "MODERATE"  # Default risk profile
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
class UserFinancialData(BaseModel):
    user_id: str
    monthly_income: Optional[float] = None
    expenses: Optional[float] = None
    savings: Optional[float] = None
    investments: Optional[Dict[str, Any]] = None
    loans: Optional[List[Dict[str, Any]]] = None
    financial_goals: Optional[List[Dict[str, Any]]] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRATION


def create_jwt_token(user_id: str) -> Token:
    """
    Create a JWT token for a user
    
    Args:
        user_id: The user's ID
        
    Returns:
        A Token object with the JWT token and metadata
    """
    expiration = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    payload = {
        "sub": user_id,
        "exp": expiration,
        "iat": datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return Token(
        access_token=token,
        expires_in=JWT_EXPIRATION
    )


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify a JWT token and extract the payload
    
    Args:
        token: The JWT token to verify
        
    Returns:
        The decoded payload if valid
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token"
        )


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: The plain text password
        
    Returns:
        The hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against
        
    Returns:
        True if the password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


class UserAPI:
    """
    Class to handle user-related API operations
    """
    
    def __init__(self, api_base_url: str = API_BASE_URL):
        """
        Initialize the UserAPI with the base URL
        
        Args:
            api_base_url: The base URL for the API
        """
        self.api_base_url = api_base_url
        
    def register_user(self, user_data: UserCreate) -> Union[UserProfile, None]:
        """
        Register a new user
        
        Args:
            user_data: The user data to register
            
        Returns:
            The created user profile or None if failed
        """
        try:
            # Hash the password before sending to API
            user_data_dict = user_data.dict()
            user_data_dict["password"] = hash_password(user_data_dict["password"])
            
            # In a real implementation, this would call the backend API
            # For now, simulate a successful registration
            user_id = f"usr_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            user_profile = UserProfile(
                user_id=user_id,
                email=user_data.email,
                full_name=user_data.full_name,
                phone_number=user_data.phone_number,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"User registered successfully: {user_id}")
            return user_profile
            
        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            return None
            
    def authenticate_user(self, email: str, password: str) -> Union[Token, None]:
        """
        Authenticate a user and return a JWT token
        
        Args:
            email: The user's email
            password: The user's password
            
        Returns:
            A Token object if authentication is successful, None otherwise
        """
        try:
            # In a real implementation, this would validate credentials against the database
            # For now, simulate a successful authentication for testing
            user_id = f"usr_{email.split('@')[0]}"
            
            # Create and return a JWT token
            token = create_jwt_token(user_id)
            logger.info(f"User authenticated successfully: {user_id}")
            
            return token
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None
            
    def get_user_profile(self, user_id: str, token: str) -> Union[UserProfile, None]:
        """
        Get a user's profile
        
        Args:
            user_id: The user's ID
            token: The JWT token for authentication
            
        Returns:
            The user profile or None if failed
        """
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            
            # Check if the user_id in the token matches the requested user_id
            # This prevents users from accessing other users' profiles
            if payload["sub"] != user_id:
                logger.warning(f"Token user_id does not match requested user_id: {payload['sub']} != {user_id}")
                return None
                
            # In a real implementation, this would fetch the profile from the database
            # For now, return a sample profile
            profile = UserProfile(
                user_id=user_id,
                email=f"{user_id.split('_')[1]}@example.com",
                full_name="Sample User",
                phone_number="+254712345678",
                risk_profile="MODERATE",
                created_at=datetime.now() - timedelta(days=30),
                updated_at=datetime.now()
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
            
    def update_user_profile(self, user_id: str, token: str, profile_data: Dict[str, Any]) -> Union[UserProfile, None]:
        """
        Update a user's profile
        
        Args:
            user_id: The user's ID
            token: The JWT token for authentication
            profile_data: The profile data to update
            
        Returns:
            The updated user profile or None if failed
        """
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            
            # Check if the user_id in the token matches the requested user_id
            if payload["sub"] != user_id:
                logger.warning(f"Token user_id does not match requested user_id: {payload['sub']} != {user_id}")
                return None
                
            # In a real implementation, this would update the profile in the database
            # For now, return a sample updated profile
            profile = UserProfile(
                user_id=user_id,
                email=profile_data.get("email", f"{user_id.split('_')[1]}@example.com"),
                full_name=profile_data.get("full_name", "Updated User"),
                phone_number=profile_data.get("phone_number", "+254712345678"),
                risk_profile=profile_data.get("risk_profile", "MODERATE"),
                created_at=datetime.now() - timedelta(days=30),
                updated_at=datetime.now()
            )
            
            logger.info(f"User profile updated successfully: {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return None
            
    def get_user_financial_data(self, user_id: str, token: str) -> Union[UserFinancialData, None]:
        """
        Get a user's financial data
        
        Args:
            user_id: The user's ID
            token: The JWT token for authentication
            
        Returns:
            The user's financial data or None if failed
        """
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            
            # Check if the user_id in the token matches the requested user_id
            if payload["sub"] != user_id:
                logger.warning(f"Token user_id does not match requested user_id: {payload['sub']} != {user_id}")
                return None
                
            # In a real implementation, this would fetch the financial data from the database
            # For now, return sample financial data
            financial_data = UserFinancialData(
                user_id=user_id,
                monthly_income=50000.0,
                expenses=30000.0,
                savings=20000.0,
                investments={
                    "stocks": [
                        {"symbol": "SCOM", "name": "Safaricom", "value": 10000.0},
                        {"symbol": "EQTY", "name": "Equity Bank", "value": 5000.0}
                    ],
                    "mutual_funds": [
                        {"name": "Money Market Fund", "value": 15000.0}
                    ]
                },
                loans=[
                    {"type": "Personal", "amount": 50000.0, "interest_rate": 14.0, "remaining_term": 12}
                ],
                financial_goals=[
                    {"name": "Buy a House", "target_amount": 5000000.0, "target_date": "2030-01-01", "current_amount": 200000.0},
                    {"name": "Education Fund", "target_amount": 1000000.0, "target_date": "2028-01-01", "current_amount": 100000.0}
                ]
            )
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Failed to get user financial data: {e}")
            return None
            
    def update_user_financial_data(self, user_id: str, token: str, 
                                  financial_data: Dict[str, Any]) -> Union[UserFinancialData, None]:
        """
        Update a user's financial data
        
        Args:
            user_id: The user's ID
            token: The JWT token for authentication
            financial_data: The financial data to update
            
        Returns:
            The updated financial data or None if failed
        """
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            
            # Check if the user_id in the token matches the requested user_id
            if payload["sub"] != user_id:
                logger.warning(f"Token user_id does not match requested user_id: {payload['sub']} != {user_id}")
                return None
                
            # In a real implementation, this would update the financial data in the database
            # For now, simulate a successful update
            updated_data = UserFinancialData(
                user_id=user_id,
                monthly_income=financial_data.get("monthly_income", 50000.0),
                expenses=financial_data.get("expenses", 30000.0),
                savings=financial_data.get("savings", 20000.0),
                investments=financial_data.get("investments", {}),
                loans=financial_data.get("loans", []),
                financial_goals=financial_data.get("financial_goals", [])
            )
            
            logger.info(f"User financial data updated successfully: {user_id}")
            return updated_data
            
        except Exception as e:
            logger.error(f"Failed to update user financial data: {e}")
            return None
            
    def analyze_risk_profile(self, user_id: str, token: str, 
                            survey_responses: Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """
        Analyze a user's risk profile based on survey responses
        
        Args:
            user_id: The user's ID
            token: The JWT token for authentication
            survey_responses: The user's responses to the risk assessment survey
            
        Returns:
            A dictionary with the risk profile analysis or None if failed
        """
        try:
            # Verify the token
            payload = verify_jwt_token(token)
            
            # Check if the user_id in the token matches the requested user_id
            if payload["sub"] != user_id:
                logger.warning(f"Token user_id does not match requested user_id: {payload['sub']} != {user_id}")
                return None
                
            # In a real implementation, this would perform a complex risk assessment
            # For now, use a simple scoring system based on the survey responses
            
            # Sample risk assessment logic (would be much more complex in production)
            score = 0
            
            # Example questions and scoring
            if "investment_horizon" in survey_responses:
                horizon = survey_responses["investment_horizon"]
                if horizon == "short_term":
                    score += 1
                elif horizon == "medium_term":
                    score += 3
                elif horizon == "long_term":
                    score += 5
                    
            if "risk_tolerance" in survey_responses:
                tolerance = survey_responses["risk_tolerance"]
                if tolerance == "low":
                    score += 1
                elif tolerance == "medium":
                    score += 3
                elif tolerance == "high":
                    score += 5
                    
            if "income_stability" in survey_responses:
                stability = survey_responses["income_stability"]
                if stability == "unstable":
                    score += 1
                elif stability == "somewhat_stable":
                    score += 3
                elif stability == "very_stable":
                    score += 5
            
            # Determine risk profile based on score
            risk_profile = "CONSERVATIVE"
            if score >= 10:
                risk_profile = "AGGRESSIVE"
            elif score >= 6:
                risk_profile = "MODERATE"
                
            # Update the user's risk profile
            self.update_user_profile(user_id, token, {"risk_profile": risk_profile})
            
            return {
                "user_id": user_id,
                "risk_profile": risk_profile,
                "score": score,
                "analysis": {
                    "investment_horizon": survey_responses.get("investment_horizon", ""),
                    "risk_tolerance": survey_responses.get("risk_tolerance", ""),
                    "income_stability": survey_responses.get("income_stability", "")
                },
                "recommendations": self._get_recommendations_for_risk_profile(risk_profile)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze risk profile: {e}")
            return None
            
    def _get_recommendations_for_risk_profile(self, risk_profile: str) -> List[Dict[str, Any]]:
        """
        Get investment recommendations based on risk profile
        
        Args:
            risk_profile: The user's risk profile (CONSERVATIVE, MODERATE, AGGRESSIVE)
            
        Returns:
            A list of investment recommendations
        """
        recommendations = []
        
        if risk_profile == "CONSERVATIVE":
            recommendations = [
                {
                    "type": "Money Market Fund",
                    "allocation": 60,
                    "description": "Low-risk, short-term securities focused on preservation of capital"
                },
                {
                    "type": "Government Bonds",
                    "allocation": 30,
                    "description": "Fixed income securities with government backing"
                },
                {
                    "type": "Blue Chip Stocks",
                    "allocation": 10,
                    "description": "Stable, established companies like Safaricom and Equity Bank"
                }
            ]
        elif risk_profile == "MODERATE":
            recommendations = [
                {
                    "type": "Money Market Fund",
                    "allocation": 40,
                    "description": "Low-risk, short-term securities for stability"
                },
                {
                    "type": "Government Bonds",
                    "allocation": 20,
                    "description": "Fixed income securities for regular interest"
                },
                {
                    "type": "Blue Chip Stocks",
                    "allocation": 25,
                    "description": "Stable stocks from established companies"
                },
                {
                    "type": "Growth Stocks",
                    "allocation": 15,
                    "description": "Companies with high growth potential"
                }
            ]
        elif risk_profile == "AGGRESSIVE":
            recommendations = [
                {
                    "type": "Money Market Fund",
                    "allocation": 20,
                    "description": "Some liquidity and stability"
                },
                {
                    "type": "Government Bonds",
                    "allocation": 10,
                    "description": "Some fixed income for regular cash flow"
                },
                {
                    "type": "Blue Chip Stocks",
                    "allocation": 30,
                    "description": "Stable base of established companies"
                },
                {
                    "type": "Growth Stocks",
                    "allocation": 30,
                    "description": "Companies with high growth potential"
                },
                {
                    "type": "International Stocks",
                    "allocation": 10,
                    "description": "Global diversification for higher returns"
                }
            ]
            
        return recommendations


# Create a singleton instance of the UserAPI
user_api = UserAPI()

# Example usage
if __name__ == "__main__":
    # This code will only run if the file is executed directly (not imported)
    try:
        # Example: Register a user
        user_data = UserCreate(
            email="test@example.com",
            password="SecureP@ss123",
            full_name="Test User",
            phone_number="+254712345678"
        )
        user = user_api.register_user(user_data)
        print(f"Registered user: {user.user_id}")
        
        # Example: Authenticate the user
        token = user_api.authenticate_user("test@example.com", "SecureP@ss123")
        print(f"Authentication token: {token.access_token}")
        
        # Example: Get user profile
        profile = user_api.get_user_profile(user.user_id, token.access_token)
        print(f"User profile: {profile}")
        
        # Example: Analyze risk profile
        risk_analysis = user_api.analyze_risk_profile(user.user_id, token.access_token, {
            "investment_horizon": "long_term",
            "risk_tolerance": "medium",
            "income_stability": "very_stable"
        })
        print(f"Risk profile: {risk_analysis}")
        
    except Exception as e:
        print(f"Error in example: {e}")
