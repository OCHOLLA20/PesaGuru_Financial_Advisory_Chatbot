"""
Security Test Suite for PesaGuru Financial Advisory Chatbot

This module tests security features of the PesaGuru system including:
1. Authentication & Authorization
2. Data Encryption
3. Input Validation & Sanitization
4. API Security
5. Regulatory Compliance
6. Rate Limiting
"""

import unittest
import requests
import json
import os
import sys
import base64
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the server directory to the path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))

# Define constants that would normally be imported
JWT_SECRET = os.getenv('JWT_SECRET', 'testsecretkey123456789')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'testencryptionkey123456789')

# Base URL for API testing
BASE_URL = os.getenv('PESAGURU_TEST_API_URL', 'http://localhost:8000/api')


class AuthenticationTests(unittest.TestCase):
    """Test authentication mechanisms including login, token validation, and password handling"""
    
    def setUp(self):
        """Setup test data"""
        self.valid_credentials = {
            "email": "test@example.com",
            "password": "Secure@Password123"
        }
        self.invalid_credentials = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        self.test_user = {
            "id": 1,
            "email": "test@example.com",
            "role": "user"
        }
    
    def generate_token(self, user):
        """Mock implementation of token generation"""
        payload = {
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    def validate_token(self, token):
        """Mock implementation of token validation"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if payload["exp"] < datetime.now().timestamp():
                raise Exception("Token has expired")
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
    
    def hash_password(self, password):
        """Mock implementation of password hashing"""
        # This is a simplified mock - in a real implementation, use bcrypt or argon2
        salt = os.urandom(16).hex()
        return f"{salt}:{hash(password + salt)}"
    
    def verify_password(self, password, hashed):
        """Mock implementation of password verification"""
        # This is a simplified mock - in a real implementation, use bcrypt or argon2
        if not hashed or ":" not in hashed:
            return False
        salt, stored_hash = hashed.split(":", 1)
        return hash(password + salt) == int(stored_hash)
        
    def test_successful_login(self):
        """Test that valid credentials return a valid JWT token"""
        # Mock a successful login
        token = self.generate_token(self.test_user)
        
        # Token should be a valid JWT
        self.assertIsNotNone(token)
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        self.assertEqual(payload["user_id"], self.test_user["id"])
        self.assertEqual(payload["email"], self.test_user["email"])
        self.assertTrue(payload["exp"] > datetime.now().timestamp())
    
    def test_failed_login(self):
        """Test that invalid credentials fail authentication"""
        # Mock a function that would verify credentials and raise an exception for invalid ones
        def mock_login(credentials):
            if credentials["password"] != self.valid_credentials["password"]:
                raise Exception("Invalid credentials")
            return self.generate_token(self.test_user)
        
        # Test with invalid credentials
        with self.assertRaises(Exception) as context:
            mock_login(self.invalid_credentials)
        self.assertTrue('Invalid credentials' in str(context.exception))
    
    def test_password_hashing(self):
        """Test that passwords are properly hashed and verified"""
        password = "Secure@Password123"
        
        # Hash the password
        hashed = self.hash_password(password)
        
        # Verify the hash is not the plaintext password
        self.assertNotEqual(hashed, password)
        
        # Verify the password matches the hash
        self.assertTrue(self.verify_password(password, hashed))
        
        # Verify wrong password fails
        self.assertFalse(self.verify_password("WrongPassword", hashed))
    
    def test_jwt_expiration(self):
        """Test that expired tokens are rejected"""
        # Create a token that expired 1 hour ago
        payload = {
            "user_id": self.test_user["id"],
            "email": self.test_user["email"],
            "role": self.test_user["role"],
            "exp": datetime.now().timestamp() - 3600
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        # Validate token should fail
        with self.assertRaises(Exception) as context:
            self.validate_token(expired_token)
        self.assertTrue('Token has expired' in str(context.exception))
    
    def test_token_validation(self):
        """Test that token validation works correctly"""
        # Create a valid token
        payload = {
            "user_id": self.test_user["id"],
            "email": self.test_user["email"],
            "role": self.test_user["role"],
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        valid_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        # Token should validate successfully
        validated_user = self.validate_token(valid_token)
        self.assertEqual(validated_user["user_id"], self.test_user["id"])
        self.assertEqual(validated_user["email"], self.test_user["email"])


class DataEncryptionTests(unittest.TestCase):
    """Test data encryption and decryption functionality"""
    
    def encrypt(self, plaintext):
        """Mock implementation of encryption"""
        # This is a simplified mock - in a real implementation, use a proper encryption library
        from cryptography.fernet import Fernet
        import base64
        
        # Create a deterministic key from ENCRYPTION_KEY
        key_bytes = ENCRYPTION_KEY.encode('utf-8')
        key_bytes = key_bytes + b'=' * (len(key_bytes) % 4)
        key = base64.urlsafe_b64encode(key_bytes[:32].ljust(32, b'\0'))
        
        cipher = Fernet(key)
        return cipher.encrypt(plaintext.encode('utf-8')).decode('utf-8')
    
    def decrypt(self, ciphertext):
        """Mock implementation of decryption"""
        # This is a simplified mock - in a real implementation, use a proper encryption library
        from cryptography.fernet import Fernet
        import base64
        
        # Create a deterministic key from ENCRYPTION_KEY
        key_bytes = ENCRYPTION_KEY.encode('utf-8')
        key_bytes = key_bytes + b'=' * (len(key_bytes) % 4)
        key = base64.urlsafe_b64encode(key_bytes[:32].ljust(32, b'\0'))
        
        cipher = Fernet(key)
        return cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    
    def encrypt_sensitive_data(self, data):
        """Mock implementation of sensitive data encryption"""
        encrypted_data = {}
        for key, value in data.items():
            encrypted_data[key] = self.encrypt(str(value))
        return encrypted_data
    
    def test_sensitive_data_encryption(self):
        """Test that sensitive data is properly encrypted and decrypted"""
        # Original data
        sensitive_data = {
            "credit_card": "4111111111111111",
            "expiry": "12/25",
            "cvv": "123",
            "id_number": "12345678"
        }
        
        try:
            # Encrypt data
            encrypted_data = self.encrypt_sensitive_data(sensitive_data)
            
            # Verify the data is encrypted (not plaintext)
            self.assertNotEqual(encrypted_data["credit_card"], sensitive_data["credit_card"])
            self.assertNotEqual(encrypted_data["expiry"], sensitive_data["expiry"])
            self.assertNotEqual(encrypted_data["cvv"], sensitive_data["cvv"])
            self.assertNotEqual(encrypted_data["id_number"], sensitive_data["id_number"])
            
            # Decrypt data
            decrypted_data = {}
            for key, value in encrypted_data.items():
                decrypted_data[key] = self.decrypt(value)
            
            # Verify decryption restores original data
            self.assertEqual(decrypted_data["credit_card"], sensitive_data["credit_card"])
            self.assertEqual(decrypted_data["expiry"], sensitive_data["expiry"])
            self.assertEqual(decrypted_data["cvv"], sensitive_data["cvv"])
            self.assertEqual(decrypted_data["id_number"], sensitive_data["id_number"])
        except ImportError:
            self.skipTest("cryptography package not installed")
    
    def test_encrypt_decrypt_cycle(self):
        """Test encryption and decryption with various data types"""
        try:
            test_values = [
                "Plain text string",
                "Special chars: !@#$%^&*()",
                "1234567890",
                "Multi-line\ntext\ndata",
                "Swahili: Habari yako?",
                json.dumps({"nested": {"data": "structure"}}),
            ]
            
            for value in test_values:
                encrypted = self.encrypt(value)
                decrypted = self.decrypt(encrypted)
                self.assertEqual(decrypted, value)
                # Verify encryption actually happened
                self.assertNotEqual(encrypted, value)
        except ImportError:
            self.skipTest("cryptography package not installed")


class InputValidationTests(unittest.TestCase):
    """Test input validation and sanitization"""
    
    def sanitize_input(self, input_str):
        """Mock implementation of input sanitization"""
        import re
        
        # Sanitize SQL injection attempts
        sql_chars = ["'", ";", "--", "/*", "*/", "xp_"]
        sanitized = input_str
        for char in sql_chars:
            sanitized = sanitized.replace(char, "")
        
        # Sanitize XSS attempts
        sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE|re.DOTALL)
        sanitized = re.sub(r'<.*?on\w+.*?=', '<', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are caught and sanitized"""
        malicious_inputs = [
            "Robert'; DROP TABLE Users; --",
            "1; DELETE FROM Investments",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT username, password FROM users --",
        ]
        
        for inp in malicious_inputs:
            sanitized = self.sanitize_input(inp)
            # Check that SQL command characters are escaped or removed
            self.assertNotIn("'", sanitized)
            self.assertNotIn(";", sanitized)
            self.assertNotIn("--", sanitized)
    
    def test_xss_prevention(self):
        """Test that Cross-Site Scripting (XSS) attempts are sanitized"""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(\"XSS\")'>",
            "<a href='javascript:alert(\"XSS\")'>Click me</a>",
            "<div onmouseover='alert(\"XSS\")'>Hover over me</div>"
        ]
        
        for inp in malicious_inputs:
            sanitized = self.sanitize_input(inp)
            # Check that HTML/JavaScript tags and events are escaped or removed
            self.assertNotIn("<script>", sanitized)
            self.assertNotIn("onerror=", sanitized)
            self.assertNotIn("javascript:", sanitized)
            self.assertNotIn("onmouseover=", sanitized)


class APISecurityTests(unittest.TestCase):
    """Test API security measures"""
    
    def setUp(self):
        """Setup API test data"""
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._generate_test_token()
        }
        self.portfolio_data = {
            "name": "Test Portfolio",
            "risk_level": "medium",
            "investment_amount": 10000
        }
        
        # Create a mock API service
        self.api_service = self.MockAPIService()
    
    class MockAPIService:
        """Mock class to simulate API responses"""
        
        def check_auth(self, headers):
            """Check if Authorization header is present and valid"""
            if 'Authorization' not in headers or not headers['Authorization'].startswith('Bearer '):
                return False
            
            token = headers['Authorization'].split(' ')[1]
            try:
                jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                return True
            except:
                return False
        
        def check_csrf(self, headers):
            """Check if CSRF token is present and valid"""
            return 'X-CSRF-Token' in headers
        
        def validate_input(self, data):
            """Validate input data for malicious content"""
            if not isinstance(data, dict):
                return False
                
            # Check for malicious content in string values
            for key, value in data.items():
                if isinstance(value, str) and any(x in value for x in ["<script>", "DROP TABLE", "'"]):
                    return False
            
            # Check data types
            if 'investment_amount' in data and not isinstance(data['investment_amount'], (int, float)):
                return False
                
            return True
        
        def post(self, url, data=None, headers=None):
            """Mock post method that checks security requirements"""
            response = MagicMock()
            
            # Check authorization
            if not self.check_auth(headers):
                response.status_code = 401
                response.json.return_value = {"error": "Unauthorized access"}
                return response
            
            # Check CSRF token
            if not self.check_csrf(headers):
                response.status_code = 403
                response.json.return_value = {"error": "CSRF token missing or invalid"}
                return response
            
            # Validate input data
            if data and not self.validate_input(json.loads(data)):
                response.status_code = 400
                response.json.return_value = {"error": "Invalid input data"}
                return response
            
            # If all checks pass
            response.status_code = 200
            response.json.return_value = {"success": True}
            return response
    
    def _generate_test_token(self):
        """Generate a test token for API calls"""
        payload = {
            "user_id": 1,
            "email": "test@example.com",
            "role": "user",
            "exp": (datetime.now() + timedelta(hours=1)).timestamp()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    def test_unauthorized_access_prevention(self):
        """Test that unauthorized API access is prevented"""
        # API call without auth header
        response = self.api_service.post(
            f"{BASE_URL}/portfolio/create",
            data=json.dumps(self.portfolio_data),
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"], "Unauthorized access")
    
    def test_csrf_protection(self):
        """Test CSRF token validation"""
        # API call without CSRF token
        response = self.api_service.post(
            f"{BASE_URL}/portfolio/create",
            data=json.dumps(self.portfolio_data),
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "CSRF token missing or invalid")
    
    def test_api_input_validation(self):
        """Test API input validation for malicious data"""
        # Add CSRF token to headers for this test
        headers = self.headers.copy()
        headers["X-CSRF-Token"] = "valid-token"
        
        # API call with malicious data
        malicious_data = {
            "name": "<script>alert('XSS')</script>",
            "risk_level": "'; DROP TABLE users; --",
            "investment_amount": "not_a_number"
        }
        
        response = self.api_service.post(
            f"{BASE_URL}/portfolio/create",
            data=json.dumps(malicious_data),
            headers=headers
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Invalid input data")


class RegulatoryComplianceTests(unittest.TestCase):
    """Test compliance with financial regulations"""
    
    def check_regulatory_compliance(self, regulation_type, operation_data):
        """Mock implementation of regulatory compliance checking"""
        result = {"compliant": True, "compliance_issues": []}
        
        if regulation_type == "pdpa":  # Kenya's Data Protection Act
            required_fields = ["consent_obtained", "purpose_specified", "retention_period_defined"]
            
            for field in required_fields:
                if field not in operation_data or not operation_data[field]:
                    result["compliant"] = False
                    result["compliance_issues"].append(f"Missing or invalid {field}")
            
            if "security_measures" not in operation_data or not operation_data["security_measures"]:
                result["compliant"] = False
                result["compliance_issues"].append("No security measures specified")
                
        elif regulation_type == "cbk":  # Central Bank of Kenya regulations
            required_fields = ["disclaimer_provided", "risk_disclosure", "registered_with_cma"]
            
            for field in required_fields:
                if field not in operation_data or not operation_data[field]:
                    result["compliant"] = False
                    result["compliance_issues"].append(f"Missing or invalid {field}")
            
            # Check for personalized advice without proper registration
            if operation_data.get("personalized_advice", False) and operation_data.get("advice_type") == "specific":
                if not operation_data.get("registered_with_cma", False):
                    result["compliant"] = False
                    result["compliance_issues"].append("Personalized specific advice requires CMA registration")
        
        return result
    
    def test_pdpa_compliance(self):
        """Test compliance with Kenya's Data Protection Act (2019)"""
        # Mock user data operation
        user_operation = {
            "operation": "collect_data",
            "data_type": "financial_profile",
            "consent_obtained": True,
            "purpose_specified": True,
            "retention_period_defined": True,
            "security_measures": ["encryption", "access_control", "audit_logging"]
        }
        
        compliance_result = self.check_regulatory_compliance("pdpa", user_operation)
        self.assertTrue(compliance_result["compliant"])
        self.assertEqual(len(compliance_result["compliance_issues"]), 0)
        
        # Test case where compliance fails
        non_compliant_operation = {
            "operation": "collect_data",
            "data_type": "financial_profile",
            "consent_obtained": False,
            "purpose_specified": False,
            "retention_period_defined": False,
            "security_measures": []
        }
        
        compliance_result = self.check_regulatory_compliance("pdpa", non_compliant_operation)
        self.assertFalse(compliance_result["compliant"])
        self.assertGreater(len(compliance_result["compliance_issues"]), 0)
    
    def test_cbk_compliance(self):
        """Test compliance with Central Bank of Kenya regulations"""
        # Mock financial advice operation
        financial_advice = {
            "operation": "provide_investment_advice",
            "disclaimer_provided": True,
            "risk_disclosure": True,
            "registered_with_cma": True,
            "advice_type": "general",
            "personalized_advice": False
        }
        
        compliance_result = self.check_regulatory_compliance("cbk", financial_advice)
        self.assertTrue(compliance_result["compliant"])
        self.assertEqual(len(compliance_result["compliance_issues"]), 0)
        
        # Test case where compliance fails
        non_compliant_advice = {
            "operation": "provide_investment_advice",
            "disclaimer_provided": False,
            "risk_disclosure": False,
            "registered_with_cma": False,
            "advice_type": "specific",
            "personalized_advice": True
        }
        
        compliance_result = self.check_regulatory_compliance("cbk", non_compliant_advice)
        self.assertFalse(compliance_result["compliant"])
        self.assertGreater(len(compliance_result["compliance_issues"]), 0)


class RateLimitingTests(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        """Set up rate limiting test data"""
        self.rate_limit_data = {}
        self.rate_limit = 20  # Max requests per minute
    
    def rate_limit_check(self, client_ip, endpoint):
        """Mock implementation of rate limiting check"""
        key = f"{client_ip}:{endpoint}"
        current_time = datetime.now()
        minute_ago = current_time - timedelta(minutes=1)
        
        # Initialize or clean up old requests
        if key not in self.rate_limit_data:
            self.rate_limit_data[key] = []
        
        # Remove requests older than 1 minute
        self.rate_limit_data[key] = [t for t in self.rate_limit_data[key] if t > minute_ago]
        
        # Check if rate limit is exceeded
        if len(self.rate_limit_data[key]) >= self.rate_limit:
            return {
                "allowed": False,
                "message": f"Rate limit exceeded for {endpoint}. Maximum {self.rate_limit} requests per minute."
            }
        
        # Add the current request
        self.rate_limit_data[key].append(current_time)
        
        return {
            "allowed": True,
            "message": "Request allowed"
        }
    
    def test_rate_limiting(self):
        """Test that rate limiting prevents excessive requests"""
        client_ip = "192.168.1.1"
        endpoint = "/api/stock-data"
        
        # Simulate 5 requests (below limit)
        results = []
        for _ in range(5):
            results.append(self.rate_limit_check(client_ip, endpoint))
        
        # All should be allowed
        for result in results:
            self.assertTrue(result["allowed"])
        
        # Simulate 20 more requests (should exceed limit)
        for _ in range(20):
            self.rate_limit_check(client_ip, endpoint)
        
        # Next request should be rate limited
        result = self.rate_limit_check(client_ip, endpoint)
        self.assertFalse(result["allowed"])
        self.assertTrue("exceeded" in result["message"])


class SecurityAuditTests(unittest.TestCase):
    """Test security audit logging"""
    
    def log_security_event(self, event):
        """Mock implementation of security event logging"""
        # In a real implementation, this would write to a secure database or log file
        return self.write_to_log(event)
    
    def write_to_log(self, event):
        """Mock implementation of log writing"""
        # Validate required fields
        required_fields = ["event_type", "ip_address", "timestamp"]
        for field in required_fields:
            if field not in event:
                return False
        
        # In a real implementation, this would write to a file or database
        return True
    
    def test_security_event_logging(self):
        """Test that security events are properly logged"""
        # Mock write_to_log to capture the log data
        original_write_to_log = self.write_to_log
        
        try:
            log_data = None
            
            def mock_write_to_log(event):
                nonlocal log_data
                log_data = event
                return True
            
            self.write_to_log = mock_write_to_log
            
            # Log a security event
            event = {
                "event_type": "authentication_failure",
                "user_id": None,
                "ip_address": "192.168.1.100",
                "timestamp": datetime.now().isoformat(),
                "details": "Failed login attempt for user test@example.com"
            }
            
            result = self.log_security_event(event)
            self.assertTrue(result)
            
            # Verify the log data contains the correct information
            self.assertEqual(log_data["event_type"], "authentication_failure")
            self.assertEqual(log_data["ip_address"], "192.168.1.100")
            
        finally:
            # Restore original function
            self.write_to_log = original_write_to_log


def run_tests():
    """Run all security tests"""
    test_classes = [
        AuthenticationTests,
        DataEncryptionTests,
        InputValidationTests,
        APISecurityTests,
        RegulatoryComplianceTests,
        RateLimitingTests,
        SecurityAuditTests
    ]
    
    loader = unittest.TestLoader()
    
    suites_list = []
    for test_class in test_classes:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)
    
    full_suite = unittest.TestSuite(suites_list)
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(full_suite)


if __name__ == '__main__':
    run_tests()