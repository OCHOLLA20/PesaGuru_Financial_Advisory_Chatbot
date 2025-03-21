"""
Tests for PesaGuru API endpoints.

This test suite covers all major API endpoints including:
- Authentication
- Chatbot interaction
- Market data
- Portfolio management
- Risk assessment
- Financial goals
- User feedback
"""

import os
import sys
import pytest
import json
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the AI directory to the Python path (where the Python API might be located)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../ai')))

# If using FastAPI for the AI component
try:
    # FastAPI testing client
    from fastapi.testclient import TestClient
    
    # Import the FastAPI application - adjust path based on actual structure
    from api import app
    
    # Create test client
    client = TestClient(app)
except ImportError:
    # Fallback for when testing against a deployed API
    # Define base URL for API
    BASE_URL = os.environ.get("PESAGURU_API_URL", "http://localhost:8000/api")
    
    # Create a wrapper class to mimic TestClient for external API
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
        
        def get(self, url, headers=None, params=None):
            return self.session.get(f"{self.base_url}{url}", headers=headers, params=params)
            
        def post(self, url, json=None, headers=None):
            return self.session.post(f"{self.base_url}{url}", json=json, headers=headers)
            
        def put(self, url, json=None, headers=None):
            return self.session.put(f"{self.base_url}{url}", json=json, headers=headers)
            
        def patch(self, url, json=None, headers=None):
            return self.session.patch(f"{self.base_url}{url}", json=json, headers=headers)
            
        def delete(self, url, headers=None):
            return self.session.delete(f"{self.base_url}{url}", headers=headers)
    
    # Create client instance
    client = APIClient(BASE_URL)

# Note: We don't need to import model classes directly since we're testing the API endpoints
# and not the internal model implementations

# Note: Client is created in the imports section above

# Test data and fixtures
@pytest.fixture
def test_user():
    """Fixture to create a test user"""
    return {
        "id": "test123",
        "email": "testuser@example.com",
        "password": "securepassword123",
        "full_name": "Test User",
        "age": 30,
        "income_level": "medium",
        "risk_tolerance": "moderate"
    }

@pytest.fixture
def auth_token(test_user):
    """Fixture to generate an authentication token"""
    # Mock token generation or use actual token logic
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0MTIzIiwiZXhwIjoxNzE3NTM1NTEwfQ.test_signature"

@pytest.fixture
def auth_headers(auth_token):
    """Fixture for authenticated request headers"""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def test_stock_data():
    """Fixture for sample NSE stock data"""
    return {
        "code": "SCOM",
        "name": "Safaricom Plc",
        "current_price": 38.25,
        "previous_close": 38.00,
        "change": 0.25,
        "change_percentage": 0.66,
        "volume": 5263100,
        "market_cap": 1530000000000
    }

@pytest.fixture
def test_portfolio():
    """Fixture for a test portfolio"""
    return {
        "user_id": "test123",
        "portfolio_id": "port123",
        "name": "Test Growth Portfolio",
        "stocks": [
            {"code": "SCOM", "shares": 100, "purchase_price": 35.50},
            {"code": "EQTY", "shares": 50, "purchase_price": 45.75},
            {"code": "KCB", "shares": 75, "purchase_price": 40.00}
        ],
        "total_value": 11337.50,
        "created_at": str(datetime.now() - timedelta(days=30)),
        "updated_at": str(datetime.now())
    }

@pytest.fixture
def test_financial_goal():
    """Fixture for a test financial goal"""
    return {
        "user_id": "test123",
        "goal_id": "goal123",
        "name": "Retirement Savings",
        "target_amount": 5000000,
        "current_amount": 1000000,
        "target_date": str(datetime.now() + timedelta(days=365*20)),
        "priority": "high",
        "created_at": str(datetime.now() - timedelta(days=60))
    }

@pytest.fixture
def test_risk_assessment():
    """Fixture for a test risk assessment"""
    return {
        "user_id": "test123",
        "risk_level": "moderate",
        "score": 65,
        "investment_horizon": "long_term",
        "income_stability": "stable",
        "created_at": str(datetime.now())
    }

# Authentication API Tests
class TestAuthAPI:
    def test_register_user(self, test_user):
        """Test user registration endpoint"""
        response = client.post("/api/auth/register", json=test_user)
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["email"] == test_user["email"]

    def test_login_user(self, test_user):
        """Test user login endpoint"""
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert "token_type" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_refresh_token(self, auth_token):
        """Test token refresh endpoint"""
        response = client.post("/api/auth/refresh", headers={"Authorization": f"Bearer {auth_token}"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_get_current_user(self, auth_headers):
        """Test current user endpoint"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert "email" in response.json()
        assert "id" in response.json()

    def test_change_password(self, auth_headers):
        """Test change password endpoint"""
        password_data = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456"
        }
        response = client.post("/api/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

# Chatbot API Tests
class TestChatbotAPI:
    def test_chatbot_query(self, auth_headers):
        """Test chatbot query endpoint"""
        query_data = {
            "message": "What stocks should I invest in?",
            "context": {
                "previous_messages": [],
                "user_profile": {
                    "risk_tolerance": "moderate",
                    "investment_horizon": "long_term"
                }
            }
        }
        response = client.post("/api/chatbot/query", json=query_data, headers=auth_headers)
        assert response.status_code == 200
        assert "message" in response.json()
        assert "confidence" in response.json()

    def test_chatbot_conversation_history(self, auth_headers):
        """Test getting conversation history endpoint"""
        response = client.get("/api/chatbot/history", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_chatbot_feedback(self, auth_headers):
        """Test submitting feedback for a chatbot response"""
        feedback_data = {
            "message_id": "msg123",
            "rating": 4,
            "feedback_text": "Very helpful financial advice!"
        }
        response = client.post("/api/chatbot/feedback", json=feedback_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Feedback submitted successfully"

# Market Data API Tests
class TestMarketDataAPI:
    def test_get_stock_price(self, auth_headers):
        """Test getting stock price data"""
        response = client.get("/api/market-data/stock/SCOM", headers=auth_headers)
        assert response.status_code == 200
        assert "code" in response.json()
        assert "current_price" in response.json()

    def test_get_market_index(self, auth_headers):
        """Test getting market index data"""
        response = client.get("/api/market-data/index/NSE20", headers=auth_headers)
        assert response.status_code == 200
        assert "name" in response.json()
        assert "current_value" in response.json()

    def test_get_sector_performance(self, auth_headers):
        """Test getting sector performance data"""
        response = client.get("/api/market-data/sectors", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        assert "sector" in response.json()[0]
        assert "performance" in response.json()[0]

    def test_get_forex_rates(self, auth_headers):
        """Test getting forex exchange rates"""
        response = client.get("/api/market-data/forex", headers=auth_headers)
        assert response.status_code == 200
        assert "USD" in response.json()
        assert "EUR" in response.json()

    def test_get_historical_data(self, auth_headers):
        """Test getting historical market data"""
        response = client.get(
            "/api/market-data/history/SCOM?start_date=2023-01-01&end_date=2023-12-31", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        assert "date" in response.json()[0]
        assert "price" in response.json()[0]

# Portfolio API Tests
class TestPortfolioAPI:
    def test_get_portfolios(self, auth_headers):
        """Test getting user portfolios"""
        response = client.get("/api/portfolios", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_portfolio(self, auth_headers, test_portfolio):
        """Test creating a new portfolio"""
        portfolio_data = {
            "name": test_portfolio["name"],
            "stocks": test_portfolio["stocks"]
        }
        response = client.post("/api/portfolios", json=portfolio_data, headers=auth_headers)
        assert response.status_code == 201
        assert "portfolio_id" in response.json()
        assert response.json()["name"] == portfolio_data["name"]

    def test_get_portfolio_details(self, auth_headers, test_portfolio):
        """Test getting specific portfolio details"""
        portfolio_id = test_portfolio["portfolio_id"]
        response = client.get(f"/api/portfolios/{portfolio_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["portfolio_id"] == portfolio_id
        assert "stocks" in response.json()
        assert "total_value" in response.json()

    def test_update_portfolio(self, auth_headers, test_portfolio):
        """Test updating a portfolio"""
        portfolio_id = test_portfolio["portfolio_id"]
        update_data = {
            "name": "Updated Test Portfolio",
            "stocks": [
                {"code": "SCOM", "shares": 150, "purchase_price": 35.50},
                {"code": "EQTY", "shares": 50, "purchase_price": 45.75}
            ]
        }
        response = client.put(f"/api/portfolios/{portfolio_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]
        assert len(response.json()["stocks"]) == len(update_data["stocks"])

    def test_delete_portfolio(self, auth_headers, test_portfolio):
        """Test deleting a portfolio"""
        portfolio_id = test_portfolio["portfolio_id"]
        response = client.delete(f"/api/portfolios/{portfolio_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_get_portfolio_performance(self, auth_headers, test_portfolio):
        """Test getting portfolio performance metrics"""
        portfolio_id = test_portfolio["portfolio_id"]
        response = client.get(f"/api/portfolios/{portfolio_id}/performance", headers=auth_headers)
        assert response.status_code == 200
        assert "overall_return" in response.json()
        assert "annualized_return" in response.json()
        assert "sector_allocation" in response.json()

# Risk Assessment API Tests
class TestRiskAssessmentAPI:
    def test_get_risk_profile(self, auth_headers):
        """Test getting user risk profile"""
        response = client.get("/api/risk-assessment/profile", headers=auth_headers)
        assert response.status_code == 200
        assert "risk_level" in response.json()
        assert "score" in response.json()

    def test_submit_risk_questionnaire(self, auth_headers):
        """Test submitting risk assessment questionnaire"""
        questionnaire_data = {
            "answers": [
                {"question_id": "q1", "answer": "b"},
                {"question_id": "q2", "answer": "c"},
                {"question_id": "q3", "answer": "a"},
                {"question_id": "q4", "answer": "b"},
                {"question_id": "q5", "answer": "b"}
            ]
        }
        response = client.post("/api/risk-assessment/questionnaire", json=questionnaire_data, headers=auth_headers)
        assert response.status_code == 200
        assert "risk_level" in response.json()
        assert "score" in response.json()
        assert "investment_recommendations" in response.json()

    def test_get_recommended_allocation(self, auth_headers, test_risk_assessment):
        """Test getting recommended asset allocation based on risk profile"""
        response = client.get("/api/risk-assessment/allocation", headers=auth_headers)
        assert response.status_code == 200
        assert "equity" in response.json()
        assert "bonds" in response.json()
        assert "cash" in response.json()
        assert "alternative_investments" in response.json()

# Financial Goals API Tests
class TestFinancialGoalsAPI:
    def test_get_financial_goals(self, auth_headers):
        """Test getting user financial goals"""
        response = client.get("/api/financial-goals", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_financial_goal(self, auth_headers, test_financial_goal):
        """Test creating a new financial goal"""
        goal_data = {
            "name": test_financial_goal["name"],
            "target_amount": test_financial_goal["target_amount"],
            "target_date": test_financial_goal["target_date"],
            "priority": test_financial_goal["priority"]
        }
        response = client.post("/api/financial-goals", json=goal_data, headers=auth_headers)
        assert response.status_code == 201
        assert "goal_id" in response.json()
        assert response.json()["name"] == goal_data["name"]

    def test_get_financial_goal_details(self, auth_headers, test_financial_goal):
        """Test getting specific financial goal details"""
        goal_id = test_financial_goal["goal_id"]
        response = client.get(f"/api/financial-goals/{goal_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["goal_id"] == goal_id
        assert "progress" in response.json()
        assert "recommendations" in response.json()

    def test_update_financial_goal(self, auth_headers, test_financial_goal):
        """Test updating a financial goal"""
        goal_id = test_financial_goal["goal_id"]
        update_data = {
            "name": "Updated Retirement Goal",
            "current_amount": 1200000,
            "priority": "medium"
        }
        response = client.patch(f"/api/financial-goals/{goal_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == update_data["name"]
        assert response.json()["current_amount"] == update_data["current_amount"]

    def test_delete_financial_goal(self, auth_headers, test_financial_goal):
        """Test deleting a financial goal"""
        goal_id = test_financial_goal["goal_id"]
        response = client.delete(f"/api/financial-goals/{goal_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_get_goal_progress(self, auth_headers, test_financial_goal):
        """Test getting financial goal progress"""
        goal_id = test_financial_goal["goal_id"]
        response = client.get(f"/api/financial-goals/{goal_id}/progress", headers=auth_headers)
        assert response.status_code == 200
        assert "percentage_complete" in response.json()
        assert "monthly_contribution_needed" in response.json()
        assert "projected_completion_date" in response.json()

# Error Handling Tests
class TestErrorHandling:
    def test_not_found_error(self):
        """Test 404 Not Found error handling"""
        response = client.get("/api/non-existent-endpoint")
        assert response.status_code == 404
        assert "error" in response.json()
        assert "message" in response.json()

    def test_unauthorized_error(self):
        """Test 401 Unauthorized error handling"""
        response = client.get("/api/portfolios")  # No auth token provided
        assert response.status_code == 401
        assert "error" in response.json()
        assert "message" in response.json()

    def test_validation_error(self, auth_headers):
        """Test validation error handling"""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "target_amount": "not-a-number"  # Invalid number format
        }
        response = client.post("/api/financial-goals", json=invalid_data, headers=auth_headers)
        assert response.status_code == 422
        assert "error" in response.json()
        assert "details" in response.json()

# Mock external API tests
class TestExternalAPIIntegration:
    @patch('services.integrations.nseApiService.get_stock_price')
    def test_nse_api_integration(self, mock_get_stock_price, auth_headers, test_stock_data):
        """Test NSE API integration with mocking"""
        mock_get_stock_price.return_value = test_stock_data
        
        response = client.get("/api/market-data/stock/SCOM", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == test_stock_data
        mock_get_stock_price.assert_called_once_with("SCOM")

    @patch('services.integrations.mpesaApiService.initiate_payment')
    def test_mpesa_api_integration(self, mock_initiate_payment, auth_headers):
        """Test M-Pesa API integration with mocking"""
        mock_response = {
            "ResponseCode": "0",
            "ResponseDescription": "Success",
            "MerchantRequestID": "123456",
            "CheckoutRequestID": "abcdef",
            "CustomerMessage": "Payment processing"
        }
        mock_initiate_payment.return_value = mock_response
        
        payment_data = {
            "phone_number": "254712345678",
            "amount": 1000,
            "reference": "PesaGuru Subscription",
            "description": "Monthly premium plan"
        }
        
        response = client.post("/api/payments/mpesa", json=payment_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["ResponseCode"] == "0"
        mock_initiate_payment.assert_called_once_with(payment_data)

# Main execution for standalone testing
if __name__ == "__main__":
    # This allows the test to be run directly with pytest
    pytest.main(["-xvs", __file__])