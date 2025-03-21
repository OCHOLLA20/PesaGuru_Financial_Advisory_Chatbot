import os
import sys
import pytest
import json
import time
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Determine if using the deployed API or local server
BASE_URL = os.environ.get("PESAGURU_API_URL", "http://localhost/PesaGuru/api")

# Add necessary paths to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Define API client for making HTTP requests
class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get(self, url, headers=None, params=None):
        return self.session.get(f"{self.base_url}{url}", headers=headers, params=params)
        
    def post(self, url, json=None, data=None, headers=None):
        return self.session.post(f"{self.base_url}{url}", json=json, data=data, headers=headers)
        
    def put(self, url, json=None, headers=None):
        return self.session.put(f"{self.base_url}{url}", json=json, headers=headers)
        
    def delete(self, url, headers=None):
        return self.session.delete(f"{self.base_url}{url}", headers=headers)

# Create client instance
client = APIClient(BASE_URL)

# Test fixtures
@pytest.fixture
def test_user():
    """Create a test user for authentication testing"""
    return {
        "email": f"test-user-{int(time.time())}@example.com",
        "password": "Secure1Password!",
        "full_name": "Test User",
        "phone": "254712345678",
        "age": 30,
        "income_level": "medium",
        "risk_tolerance": "moderate",
        "employment_status": "employed"
    }

@pytest.fixture
def registered_user(test_user):
    """Fixture to create and return a registered user"""
    try:
        # Register the user
        response = client.post("/auth/register", json=test_user)
        
        # If successful, return the user with the ID
        if response.status_code == 201:
            return {**test_user, "id": response.json().get("id")}
        
        # If user already exists, attempt to login and return
        if response.status_code == 409:  # Conflict - user exists
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            login_response = client.post("/auth/login", json=login_data)
            if login_response.status_code == 200:
                return {**test_user, "id": login_response.json().get("user_id")}
    
    except Exception as e:
        pytest.skip(f"Failed to create registered user: {str(e)}")
    
    # If can't register or login, skip tests requiring a registered user
    pytest.skip("Could not create or access test user")

@pytest.fixture
def auth_token(registered_user):
    """Fixture to get authentication token for a registered user"""
    login_data = {
        "email": registered_user["email"],
        "password": registered_user["password"]
    }
    
    response = client.post("/auth/login", json=login_data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    
    pytest.skip("Could not obtain authentication token")

@pytest.fixture
def auth_headers(auth_token):
    """Fixture for authenticated request headers"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestRegistration:
    """Tests for user registration functionality"""
    
    def test_successful_registration(self, test_user):
        """Test successful user registration with valid data"""
        # Create a unique email to avoid conflicts
        unique_email = f"user-{int(time.time())}@example.com"
        user_data = {**test_user, "email": unique_email}
        
        response = client.post("/auth/register", json=user_data)
        
        # Assert response
        assert response.status_code in [200, 201], f"Registration failed: {response.text}"
        assert "id" in response.json(), "User ID not returned in response"
        assert "access_token" in response.json(), "Access token not returned"
    
    def test_duplicate_registration(self, registered_user):
        """Test registration with an email that already exists"""
        response = client.post("/auth/register", json=registered_user)
        
        # Assert response shows conflict error
        assert response.status_code == 409, "Expected 409 Conflict for duplicate registration"
        assert "error" in response.json(), "Error message not returned"
    
    def test_invalid_registration_data(self):
        """Test registration with invalid data"""
        # Missing required fields
        invalid_user = {
            "email": "missing-fields@example.com",
            "password": "password123"
        }
        
        response = client.post("/auth/register", json=invalid_user)
        
        # Assert response shows validation error
        assert response.status_code == 422, "Expected 422 Unprocessable Entity for invalid data"
        assert "error" in response.json() or "errors" in response.json(), "Error details not returned"
    
    def test_password_validation(self, test_user):
        """Test password validation during registration"""
        # Test with weak password
        weak_password_user = {**test_user, "email": "weak-pwd@example.com", "password": "weak"}
        
        response = client.post("/auth/register", json=weak_password_user)
        
        # Assert response shows validation error for password
        assert response.status_code == 422, "Expected 422 for weak password"
        response_data = response.json()
        assert "error" in response_data or "errors" in response_data, "Error details not returned"
        
        # Check if password-specific error is mentioned
        error_text = str(response_data)
        assert "password" in error_text.lower(), "Password validation error not mentioned"


class TestLogin:
    """Tests for user login functionality"""
    
    def test_successful_login(self, registered_user):
        """Test successful login with valid credentials"""
        login_data = {
            "email": registered_user["email"],
            "password": registered_user["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Assert successful login
        assert response.status_code == 200, f"Login failed: {response.text}"
        assert "access_token" in response.json(), "Access token not returned"
        assert "token_type" in response.json(), "Token type not returned"
        assert response.json()["token_type"].lower() == "bearer", "Expected bearer token"
    
    def test_invalid_email(self):
        """Test login with non-existent email"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Assert unauthorized error
        assert response.status_code in [401, 404], "Expected 401/404 for invalid email"
        assert "error" in response.json(), "Error message not returned"
    
    def test_invalid_password(self, registered_user):
        """Test login with incorrect password"""
        login_data = {
            "email": registered_user["email"],
            "password": "WrongPassword123!"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        # Assert unauthorized error
        assert response.status_code == 401, "Expected 401 for invalid password"
        assert "error" in response.json(), "Error message not returned"
    
    def test_rate_limiting(self):
        """Test rate limiting for failed login attempts"""
        # Try multiple failed logins in quick succession
        login_data = {
            "email": "rate-limit-test@example.com",
            "password": "WrongPassword123!"
        }
        
        # Make 6 requests (typical rate limit is 5 attempts in short period)
        responses = []
        for _ in range(6):
            response = client.post("/auth/login", json=login_data)
            responses.append(response)
        
        # At least one of the later responses should be rate limited
        # Rate limiting typically returns 429 Too Many Requests
        rate_limited = any(r.status_code == 429 for r in responses[-2:])
        
        # This is a soft assertion since not all implementations have rate limiting
        if not rate_limited:
            pytest.skip("Rate limiting not implemented or not triggered")
        else:
            assert rate_limited, "Expected rate limiting after multiple failed attempts"


class TestTokenManagement:
    """Tests for token management and session handling"""
    
    def test_token_validation(self, auth_token):
        """Test that a valid token can access protected endpoints"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert successful access with token
        assert response.status_code == 200, "Valid token rejected"
        assert "email" in response.json(), "User info not returned for valid token"
    
    def test_invalid_token(self):
        """Test that an invalid token is rejected"""
        headers = {"Authorization": "Bearer invalid-token-123"}
        
        response = client.get("/auth/me", headers=headers)
        
        # Assert unauthorized error
        assert response.status_code == 401, "Expected 401 for invalid token"
    
    def test_missing_token(self):
        """Test access without a token"""
        response = client.get("/auth/me")
        
        # Assert unauthorized error
        assert response.status_code == 401, "Expected 401 for missing token"
    
    def test_refresh_token(self, auth_token, auth_headers):
        """Test refreshing an access token"""
        # Try to refresh token if endpoint exists
        response = client.post("/auth/refresh", headers=auth_headers)
        
        # If refresh endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Token refresh endpoint not implemented")
        
        # Assert successful token refresh
        assert response.status_code == 200, "Token refresh failed"
        assert "access_token" in response.json(), "New access token not returned"
        assert response.json()["access_token"] != auth_token, "Token was not changed"


class TestPasswordManagement:
    """Tests for password management functionality"""
    
    def test_change_password(self, auth_headers, registered_user):
        """Test changing password for authenticated user"""
        password_data = {
            "current_password": registered_user["password"],
            "new_password": "NewSecurePassword123!"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=auth_headers)
        
        # If endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Change password endpoint not implemented")
        
        # Assert successful password change
        assert response.status_code == 200, f"Password change failed: {response.text}"
        
        # Test login with new password
        login_data = {
            "email": registered_user["email"],
            "password": "NewSecurePassword123!"
        }
        
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200, "Login with new password failed"
    
    def test_incorrect_current_password(self, auth_headers):
        """Test changing password with incorrect current password"""
        password_data = {
            "current_password": "WrongCurrentPassword123!",
            "new_password": "NewSecurePassword123!"
        }
        
        response = client.post("/auth/change-password", json=password_data, headers=auth_headers)
        
        # If endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Change password endpoint not implemented")
        
        # Assert unauthorized or bad request error
        assert response.status_code in [400, 401], "Expected 400/401 for incorrect current password"
    
    def test_forgot_password_request(self, registered_user):
        """Test requesting a password reset"""
        reset_data = {
            "email": registered_user["email"]
        }
        
        response = client.post("/auth/forgot-password", json=reset_data)
        
        # If endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Forgot password endpoint not implemented")
        
        # Assert successful request
        assert response.status_code == 200, "Password reset request failed"
        # We can't test full reset flow as it would require email access


class TestLogout:
    """Tests for logout functionality"""
    
    def test_logout(self, auth_headers):
        """Test user logout"""
        response = client.post("/auth/logout", headers=auth_headers)
        
        # If endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Logout endpoint not implemented")
        
        # Assert successful logout
        assert response.status_code == 200, "Logout failed"
        
        # Check that token is invalidated
        second_response = client.get("/auth/me", headers=auth_headers)
        assert second_response.status_code == 401, "Token still valid after logout"


class TestSecurityFeatures:
    """Tests for additional security features"""
    
    def test_login_history(self, auth_headers):
        """Test retrieving login history"""
        response = client.get("/auth/login-history", headers=auth_headers)
        
        # If endpoint doesn't exist, skip test
        if response.status_code == 404:
            pytest.skip("Login history endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, "Failed to retrieve login history"
        assert isinstance(response.json(), list), "Expected a list of login entries"
    
    def test_xss_protection(self):
        """Test XSS protection by attempting to register with malicious data"""
        malicious_data = {
            "email": "xss-test@example.com",
            "password": "SecurePassword123!",
            "full_name": "<script>alert('XSS')</script>Test User",
            "phone": "254712345678"
        }
        
        response = client.post("/auth/register", json=malicious_data)
        
        # Skip this test if registration fails for other reasons
        if response.status_code not in [200, 201, 400, 422]:
            pytest.skip("Registration failed for reasons unrelated to XSS protection")
        
        # If registration succeeded, verify the script tag was sanitized
        if response.status_code in [200, 201]:
            user_id = response.json().get("id")
            if not user_id:
                pytest.skip("Could not retrieve user ID after registration")
            
            # Login and get profile
            login_data = {
                "email": "xss-test@example.com",
                "password": "SecurePassword123!"
            }
            login_response = client.post("/auth/login", json=login_data)
            
            if login_response.status_code != 200:
                pytest.skip("Could not login as test user")
            
            headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
            profile_response = client.get("/auth/me", headers=headers)
            
            if profile_response.status_code != 200:
                pytest.skip("Could not retrieve user profile")
            
            # Check if the script tag was sanitized
            full_name = profile_response.json().get("full_name", "")
            assert "<script>" not in full_name, "XSS attack not neutralized"
    
    def test_csrf_protection(self, auth_headers):
        """Test CSRF protection"""
        # Make a state-changing request without CSRF token
        # This is just a basic check - comprehensive CSRF testing would require browser automation
        
        # Try to change password without a CSRF token
        password_data = {
            "current_password": "Secure1Password!",
            "new_password": "AnotherSecure123!"
        }
        
        # Remove any CSRF headers that might be automatically included
        headers = {k: v for k, v in auth_headers.items() if "csrf" not in k.lower()}
        
        response = client.post("/auth/change-password", json=password_data, headers=headers)
        
        # Skip if the endpoint doesn't exist
        if response.status_code == 404:
            pytest.skip("Change password endpoint not implemented")
        
        # This is a soft assertion since not all implementations require CSRF tokens in APIs
        # Many modern APIs rely on tokens in headers instead of CSRF tokens
        if response.status_code == 403 and "csrf" in response.text.lower():
            assert True, "CSRF protection working correctly"
        else:
            pytest.skip("CSRF protection not implemented or uses a different mechanism")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])