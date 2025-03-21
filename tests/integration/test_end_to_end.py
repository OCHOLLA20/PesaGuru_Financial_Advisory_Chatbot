import os
import sys
import time
import unittest
import json
import random
import string
import requests
from datetime import datetime, timedelta
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("e2e_test_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("e2e_tests")

# Test configuration
TEST_CONFIG = {
    'base_url': os.getenv('PESAGURU_URL', 'http://localhost:8000'),
    'api_url': os.getenv('PESAGURU_API_URL', 'http://localhost:8000/api'),
    'headless': os.getenv('HEADLESS', 'True').lower() == 'true',
    'wait_timeout': int(os.getenv('WAIT_TIMEOUT', '10')),
    'screenshot_dir': os.getenv('SCREENSHOT_DIR', 'e2e_screenshots'),
    'test_users': {
        'new_user': {
            'email': f'test_user_{datetime.now().strftime("%Y%m%d%H%M%S")}@example.com',
            'password': 'Test@123',
            'first_name': 'Test',
            'last_name': 'User'
        },
        'existing_user': {
            'email': os.getenv('EXISTING_USER_EMAIL', 'existing_user@example.com'),
            'password': os.getenv('EXISTING_USER_PASSWORD', 'Existing@123')
        }
    },
    'test_stocks': ['SCOM', 'EQTY', 'KCB', 'SBIC', 'COOP'],
    'test_amounts': {
        'investment': 100000,  # KES
        'monthly_saving': 10000,  # KES
        'goal_amount': 1000000  # KES
    }
}


def generate_random_string(length=10):
    """Generate a random string of fixed length"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


class PesaGuruBaseTest(unittest.TestCase):
    """Base class for PesaGuru end-to-end tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create screenshot directory if it doesn't exist
        if not os.path.exists(TEST_CONFIG['screenshot_dir']):
            os.makedirs(TEST_CONFIG['screenshot_dir'])
        
        # Setup Selenium WebDriver
        cls.setup_driver()
        
        # Initialize API session for direct API calls
        cls.api_session = requests.Session()
    
    @classmethod
    def setup_driver(cls):
        """Set up the Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        if TEST_CONFIG['headless']:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, TEST_CONFIG['wait_timeout'])
        cls.driver.maximize_window()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        if hasattr(cls, 'driver') and cls.driver:
            cls.driver.quit()
    
    def take_screenshot(self, name):
        """Take a screenshot of the current browser window"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{TEST_CONFIG['screenshot_dir']}/{name}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")
        return filename
    
    def wait_for_element(self, by, value, timeout=None):
        """Wait for an element to be visible and return it"""
        wait_time = timeout if timeout is not None else TEST_CONFIG['wait_timeout']
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.visibility_of_element_located((by, value)))
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """Wait for an element to be clickable and return it"""
        wait_time = timeout if timeout is not None else TEST_CONFIG['wait_timeout']
        wait = WebDriverWait(self.driver, wait_time)
        return wait.until(EC.element_to_be_clickable((by, value)))
    
    def is_element_present(self, by, value, timeout=5):
        """Check if an element is present on the page"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except TimeoutException:
            return False
    
    def scroll_to_element(self, element):
        """Scroll to make an element visible"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(0.5)  # Allow time for scrolling
    
    def api_login(self, user_data=None):
        """Login via API and return auth token"""
        user = user_data or TEST_CONFIG['test_users']['existing_user']
        response = self.api_session.post(
            f"{TEST_CONFIG['api_url']}/auth/login",
            json={
                'email': user['email'],
                'password': user['password']
            }
        )
        
        if response.status_code == 200:
            token = response.json().get('token')
            self.api_session.headers.update({'Authorization': f'Bearer {token}'})
            return token
        else:
            logger.error(f"API login failed: {response.status_code} - {response.text}")
            return None


class UserRegistrationLoginTest(PesaGuruBaseTest):
    """Test user registration and login functionality"""
    
    def test_01_user_registration(self):
        """Test a new user can register successfully"""
        logger.info("Testing user registration")
        
        # Navigate to the registration page
        self.driver.get(f"{TEST_CONFIG['base_url']}/register")
        
        # Fill out the registration form
        user = TEST_CONFIG['test_users']['new_user']
        
        self.wait_for_element(By.ID, "first_name").send_keys(user['first_name'])
        self.wait_for_element(By.ID, "last_name").send_keys(user['last_name'])
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.wait_for_element(By.ID, "confirm_password").send_keys(user['password'])
        
        # Accept terms and conditions if present
        terms_checkbox = self.driver.find_element(By.ID, "accept_terms")
        if not terms_checkbox.is_selected():
            terms_checkbox.click()
        
        # Take screenshot before submission
        self.take_screenshot("registration_form")
        
        # Submit the form
        self.driver.find_element(By.ID, "register_button").click()
        
        # Wait for registration to complete and verify success
        self.wait_for_element(By.CSS_SELECTOR, ".registration-success")
        
        # Take screenshot of success message
        self.take_screenshot("registration_success")
        
        # Verify redirection to login page or dashboard
        self.assertTrue(
            "login" in self.driver.current_url or 
            "dashboard" in self.driver.current_url
        )
        
        logger.info(f"User registration successful: {user['email']}")
    
    def test_02_user_login(self):
        """Test user can login successfully"""
        logger.info("Testing user login")
        
        # Navigate to the login page
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        
        # Fill out the login form
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        
        # Take screenshot before submission
        self.take_screenshot("login_form")
        
        # Submit the form
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for login to complete and verify success
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
        
        # Take screenshot of dashboard
        self.take_screenshot("dashboard_after_login")
        
        # Verify user is logged in and on dashboard
        self.assertTrue("dashboard" in self.driver.current_url)
        
        # Verify user name is displayed in the UI
        user_profile_element = self.wait_for_element(By.CSS_SELECTOR, ".user-profile")
        self.assertTrue(user['email'] in user_profile_element.text)
        
        logger.info(f"User login successful: {user['email']}")
    
    def test_03_password_reset(self):
        """Test password reset functionality"""
        logger.info("Testing password reset")
        
        # Navigate to the password reset page
        self.driver.get(f"{TEST_CONFIG['base_url']}/forgot-password")
        
        # Fill out the form with user email
        user = TEST_CONFIG['test_users']['existing_user']
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        
        # Take screenshot before submission
        self.take_screenshot("password_reset_request")
        
        # Submit the form
        self.driver.find_element(By.ID, "reset_password_button").click()
        
        # Verify success message
        self.wait_for_element(By.CSS_SELECTOR, ".reset-password-success")
        
        # Take screenshot of success message
        self.take_screenshot("password_reset_success")
        
        logger.info("Password reset request successful")


class UserProfileSetupTest(PesaGuruBaseTest):
    """Test user profile setup and financial preferences"""
    
    def setUp(self):
        """Login before each test"""
        # Navigate to login page and authenticate
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for dashboard to load
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
    
    def test_01_financial_profile_setup(self):
        """Test setting up financial profile"""
        logger.info("Testing financial profile setup")
        
        # Navigate to profile settings
        self.driver.get(f"{TEST_CONFIG['base_url']}/user/profile")
        
        # Complete the financial profile form
        self.wait_for_element(By.ID, "monthly_income").clear()
        self.wait_for_element(By.ID, "monthly_income").send_keys("80000")
        
        self.wait_for_element(By.ID, "monthly_expenses").clear()
        self.wait_for_element(By.ID, "monthly_expenses").send_keys("50000")
        
        # Select risk tolerance
        risk_tolerance = self.wait_for_element(By.ID, "risk_tolerance")
        risk_tolerance.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='moderate']").click()
        
        # Fill investment experience
        investment_experience = self.wait_for_element(By.ID, "investment_experience")
        investment_experience.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='intermediate']").click()
        
        # Take screenshot of completed profile form
        self.take_screenshot("financial_profile_form")
        
        # Save the profile
        self.driver.find_element(By.ID, "save_profile_button").click()
        
        # Verify success message
        self.wait_for_element(By.CSS_SELECTOR, ".profile-save-success")
        
        # Take screenshot of success message
        self.take_screenshot("profile_save_success")
        
        logger.info("Financial profile setup successful")
    
    def test_02_financial_goals_setup(self):
        """Test setting up financial goals"""
        logger.info("Testing financial goals setup")
        
        # Navigate to financial goals page
        self.driver.get(f"{TEST_CONFIG['base_url']}/user/financial-goals")
        
        # Click button to add a new goal
        self.wait_for_element_clickable(By.ID, "add_goal_button").click()
        
        # Fill out the new goal form
        self.wait_for_element(By.ID, "goal_name").send_keys("Retirement Fund")
        
        # Select goal type
        goal_type = self.wait_for_element(By.ID, "goal_type")
        goal_type.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='retirement']").click()
        
        # Fill target amount
        self.wait_for_element(By.ID, "target_amount").send_keys(str(TEST_CONFIG['test_amounts']['goal_amount']))
        
        # Set target date (10 years from now)
        target_date = (datetime.now() + timedelta(days=365*10)).strftime("%Y-%m-%d")
        self.wait_for_element(By.ID, "target_date").send_keys(target_date)
        
        # Fill monthly contribution
        self.wait_for_element(By.ID, "monthly_contribution").send_keys(str(TEST_CONFIG['test_amounts']['monthly_saving']))
        
        # Take screenshot of goal form
        self.take_screenshot("financial_goal_form")
        
        # Save the goal
        self.driver.find_element(By.ID, "save_goal_button").click()
        
        # Verify success message
        self.wait_for_element(By.CSS_SELECTOR, ".goal-save-success")
        
        # Take screenshot of success message
        self.take_screenshot("goal_save_success")
        
        # Verify goal appears in the goals list
        goals_list = self.wait_for_element(By.CSS_SELECTOR, ".goals-list")
        self.assertIn("Retirement Fund", goals_list.text)
        
        logger.info("Financial goal setup successful")


class MarketDataTest(PesaGuruBaseTest):
    """Test market data access and visualization"""
    
    def setUp(self):
        """Login before each test"""
        # Login via API to get the authentication token
        self.api_login()
        
        # Navigate to login page and authenticate
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for dashboard to load
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
    
    def test_01_market_overview(self):
        """Test market overview page"""
        logger.info("Testing market overview page")
        
        # Navigate to market overview page
        self.driver.get(f"{TEST_CONFIG['base_url']}/market-data")
        
        # Verify key elements are present
        self.wait_for_element(By.CSS_SELECTOR, ".market-summary")
        
        # Check for NSE index value
        nse_index = self.wait_for_element(By.CSS_SELECTOR, ".nse-index")
        self.assertIsNotNone(nse_index.text)
        
        # Check for top gainers and losers section
        top_gainers = self.wait_for_element(By.CSS_SELECTOR, ".top-gainers")
        self.assertIsNotNone(top_gainers)
        
        top_losers = self.wait_for_element(By.CSS_SELECTOR, ".top-losers")
        self.assertIsNotNone(top_losers)
        
        # Take screenshot of market overview
        self.take_screenshot("market_overview")
        
        logger.info("Market overview page validated successfully")
    
    def test_02_stock_details(self):
        """Test stock details page for a specific stock"""
        logger.info("Testing stock details page")
        
        # Pick a test stock
        test_stock = TEST_CONFIG['test_stocks'][0]  # e.g., SCOM for Safaricom
        
        # Navigate to stock details page
        self.driver.get(f"{TEST_CONFIG['base_url']}/stock/{test_stock}")
        
        # Verify stock details are loaded
        stock_header = self.wait_for_element(By.CSS_SELECTOR, ".stock-header")
        self.assertIn(test_stock, stock_header.text)
        
        # Check for price chart
        price_chart = self.wait_for_element(By.CSS_SELECTOR, ".stock-price-chart")
        self.assertIsNotNone(price_chart)
        
        # Check for key statistics
        key_stats = self.wait_for_element(By.CSS_SELECTOR, ".key-statistics")
        self.assertIsNotNone(key_stats)
        
        # Take screenshot of stock details
        self.take_screenshot(f"stock_details_{test_stock}")
        
        logger.info(f"Stock details page for {test_stock} validated successfully")
    
    def test_03_sector_performance(self):
        """Test sector performance page"""
        logger.info("Testing sector performance page")
        
        # Navigate to sector performance page
        self.driver.get(f"{TEST_CONFIG['base_url']}/market-data/sectors")
        
        # Verify sectors are displayed
        sectors_list = self.wait_for_element(By.CSS_SELECTOR, ".sectors-list")
        self.assertIsNotNone(sectors_list)
        
        # Check for sector performance chart
        sector_chart = self.wait_for_element(By.CSS_SELECTOR, ".sector-performance-chart")
        self.assertIsNotNone(sector_chart)
        
        # Take screenshot of sector performance
        self.take_screenshot("sector_performance")
        
        # Click on a specific sector
        sectors = self.driver.find_elements(By.CSS_SELECTOR, ".sector-item")
        if sectors:
            sectors[0].click()
            
            # Verify sector detail page loads
            sector_detail = self.wait_for_element(By.CSS_SELECTOR, ".sector-detail")
            self.assertIsNotNone(sector_detail)
            
            # Check for companies in the sector
            companies_list = self.wait_for_element(By.CSS_SELECTOR, ".sector-companies")
            self.assertIsNotNone(companies_list)
            
            # Take screenshot of sector detail
            self.take_screenshot("sector_detail")
        
        logger.info("Sector performance page validated successfully")


class ChatbotInteractionTest(PesaGuruBaseTest):
    """Test chatbot interaction for financial advice"""
    
    def setUp(self):
        """Login before each test"""
        # Login via API to get the authentication token
        self.api_login()
        
        # Navigate to login page and authenticate
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for dashboard to load
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
    
    def test_01_basic_chatbot_interaction(self):
        """Test basic chatbot interaction"""
        logger.info("Testing basic chatbot interaction")
        
        # Navigate to chatbot page
        self.driver.get(f"{TEST_CONFIG['base_url']}/chatbot")
        
        # Wait for chatbot to load
        chatbot_container = self.wait_for_element(By.CSS_SELECTOR, ".chatbot-container")
        self.assertIsNotNone(chatbot_container)
        
        # Send a greeting message
        chat_input = self.wait_for_element(By.CSS_SELECTOR, ".chat-input")
        chat_input.send_keys("Hello")
        chat_input.send_keys(Keys.RETURN)
        
        # Wait for chatbot response
        self.wait_for_element(By.CSS_SELECTOR, ".bot-message")
        
        # Take screenshot of initial interaction
        self.take_screenshot("chatbot_greeting")
        
        # Send a financial question
        chat_input = self.wait_for_element(By.CSS_SELECTOR, ".chat-input")
        chat_input.send_keys("What are some good investment options in Kenya?")
        chat_input.send_keys(Keys.RETURN)
        
        # Wait for chatbot response
        time.sleep(3)  # Allow time for response generation
        bot_messages = self.driver.find_elements(By.CSS_SELECTOR, ".bot-message")
        self.assertGreaterEqual(len(bot_messages), 2)  # At least two responses now
        
        # Take screenshot of financial advice interaction
        self.take_screenshot("chatbot_investment_advice")
        
        # Verify bot response contains investment options
        investment_terms = ['stocks', 'bonds', 'mutual funds', 'treasury bills', 'real estate']
        bot_response_text = bot_messages[-1].text.lower()
        
        found_terms = [term for term in investment_terms if term in bot_response_text]
        self.assertGreaterEqual(len(found_terms), 2, 
                              f"Chatbot response should mention at least 2 investment options. Found: {found_terms}")
        
        logger.info("Basic chatbot interaction validated successfully")
    
    def test_02_stock_specific_questions(self):
        """Test chatbot response to stock-specific questions"""
        logger.info("Testing stock-specific chatbot questions")
        
        # Navigate to chatbot page
        self.driver.get(f"{TEST_CONFIG['base_url']}/chatbot")
        
        # Wait for chatbot to load
        self.wait_for_element(By.CSS_SELECTOR, ".chatbot-container")
        
        # Send a stock-specific question
        test_stock = TEST_CONFIG['test_stocks'][0]  # e.g., SCOM for Safaricom
        chat_input = self.wait_for_element(By.CSS_SELECTOR, ".chat-input")
        chat_input.send_keys(f"How has {test_stock} stock performed recently?")
        chat_input.send_keys(Keys.RETURN)
        
        # Wait for chatbot response
        time.sleep(5)  # Allow more time for generating response with stock analysis
        bot_messages = self.driver.find_elements(By.CSS_SELECTOR, ".bot-message")
        
        # Take screenshot of stock question interaction
        self.take_screenshot(f"chatbot_stock_{test_stock}")
        
        # Verify bot response contains stock information
        bot_response_text = bot_messages[-1].text
        self.assertIn(test_stock, bot_response_text)
        
        # Look for price or performance indicators in the response
        performance_terms = ['price', 'increased', 'decreased', 'performance', 'trend']
        found_terms = [term for term in performance_terms if term.lower() in bot_response_text.lower()]
        self.assertGreaterEqual(len(found_terms), 1, 
                              f"Chatbot response should mention stock performance. Found: {found_terms}")
        
        logger.info(f"Stock-specific chatbot questions for {test_stock} validated successfully")
    
    def test_03_personalized_advice(self):
        """Test personalized financial advice from chatbot"""
        logger.info("Testing personalized financial advice")
        
        # Navigate to chatbot page
        self.driver.get(f"{TEST_CONFIG['base_url']}/chatbot")
        
        # Wait for chatbot to load
        self.wait_for_element(By.CSS_SELECTOR, ".chatbot-container")
        
        # Send a personalized advice request
        chat_input = self.wait_for_element(By.CSS_SELECTOR, ".chat-input")
        question = (
            "I earn 80,000 KES per month, have 20,000 KES in savings, "
            "and want to invest for retirement. What would you recommend?"
        )
        chat_input.send_keys(question)
        chat_input.send_keys(Keys.RETURN)
        
        # Wait for chatbot response
        time.sleep(8)  # Allow more time for generating complex advice
        bot_messages = self.driver.find_elements(By.CSS_SELECTOR, ".bot-message")
        
        # Take screenshot of personalized advice
        self.take_screenshot("chatbot_personalized_advice")
        
        # Verify bot response contains personalized advice
        bot_response_text = bot_messages[-1].text
        
        # Check for income acknowledgment
        self.assertTrue(
            "80,000" in bot_response_text or 
            "80000" in bot_response_text or
            "income" in bot_response_text.lower()
        )
        
        # Check for long-term investment terms
        investment_terms = ['retirement', 'long-term', 'portfolio', 'diversify', 'allocation']
        found_terms = [term for term in investment_terms if term.lower() in bot_response_text.lower()]
        self.assertGreaterEqual(len(found_terms), 2, 
                              f"Chatbot response should mention retirement planning terms. Found: {found_terms}")
        
        logger.info("Personalized financial advice validated successfully")


class InvestmentPortfolioTest(PesaGuruBaseTest):
    """Test investment portfolio creation and management"""
    
    def setUp(self):
        """Login before each test"""
        # Login via API to get the authentication token
        self.api_login()
        
        # Navigate to login page and authenticate
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for dashboard to load
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
    
    def test_01_create_investment_portfolio(self):
        """Test creating a new investment portfolio"""
        logger.info("Testing investment portfolio creation")
        
        # Navigate to portfolio page
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        
        # Click on create new portfolio button
        self.wait_for_element_clickable(By.ID, "create_portfolio_button").click()
        
        # Fill portfolio details
        portfolio_name = f"Test Portfolio {generate_random_string(5)}"
        self.wait_for_element(By.ID, "portfolio_name").send_keys(portfolio_name)
        
        # Select risk level
        risk_level = self.wait_for_element(By.ID, "risk_level")
        risk_level.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='moderate']").click()
        
        # Enter investment amount
        self.wait_for_element(By.ID, "investment_amount").send_keys(str(TEST_CONFIG['test_amounts']['investment']))
        
        # Select stocks
        for i, stock in enumerate(TEST_CONFIG['test_stocks'][:3]):
            # Find stock selection element - this will vary based on your UI
            stock_checkbox = self.wait_for_element(By.CSS_SELECTOR, f"input[value='{stock}']")
            if not stock_checkbox.is_selected():
                stock_checkbox.click()
                
            # Set allocation
            allocation_input = self.wait_for_element(By.ID, f"allocation_{stock}")
            allocation_input.clear()
            allocation_input.send_keys(str(30 if i < 2 else 40))  # 30%, 30%, 40% allocation
        
        # Take screenshot of portfolio creation form
        self.take_screenshot("portfolio_creation_form")
        
        # Submit the form
        self.driver.find_element(By.ID, "save_portfolio_button").click()
        
        # Verify portfolio creation success
        self.wait_for_element(By.CSS_SELECTOR, ".portfolio-save-success")
        
        # Take screenshot of success message
        self.take_screenshot("portfolio_creation_success")
        
        # Verify new portfolio appears in the portfolios list
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        portfolios_list = self.wait_for_element(By.CSS_SELECTOR, ".portfolios-list")
        self.assertIn(portfolio_name, portfolios_list.text)
        
        logger.info(f"Investment portfolio '{portfolio_name}' created successfully")
    
    def test_02_view_portfolio_details(self):
        """Test viewing portfolio details"""
        logger.info("Testing portfolio details view")
        
        # Navigate to portfolio page
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        
        # Click on the first portfolio in the list to view details
        portfolio_items = self.driver.find_elements(By.CSS_SELECTOR, ".portfolio-item")
        if not portfolio_items:
            self.skipTest("No portfolios available to test details view")
        
        portfolio_name = portfolio_items[0].find_element(By.CSS_SELECTOR, ".portfolio-name").text
        portfolio_items[0].click()
        
        # Verify portfolio details page loads
        portfolio_detail = self.wait_for_element(By.CSS_SELECTOR, ".portfolio-detail")
        self.assertIsNotNone(portfolio_detail)
        
        # Check for portfolio composition chart
        composition_chart = self.wait_for_element(By.CSS_SELECTOR, ".portfolio-composition-chart")
        self.assertIsNotNone(composition_chart)
        
        # Check for performance section
        performance_section = self.wait_for_element(By.CSS_SELECTOR, ".portfolio-performance")
        self.assertIsNotNone(performance_section)
        
        # Take screenshot of portfolio details
        self.take_screenshot("portfolio_details")
        
        logger.info(f"Portfolio details for '{portfolio_name}' validated successfully")
    
    def test_03_edit_portfolio(self):
        """Test editing an existing portfolio"""
        logger.info("Testing portfolio editing")
        
        # Navigate to portfolio page
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        
        # Click on the first portfolio's edit button
        portfolio_items = self.driver.find_elements(By.CSS_SELECTOR, ".portfolio-item")
        if not portfolio_items:
            self.skipTest("No portfolios available to test editing")
        
        portfolio_name = portfolio_items[0].find_element(By.CSS_SELECTOR, ".portfolio-name").text
        edit_button = portfolio_items[0].find_element(By.CSS_SELECTOR, ".edit-portfolio-button")
        edit_button.click()
        
        # Update portfolio name
        updated_name = f"{portfolio_name}_edited"
        name_input = self.wait_for_element(By.ID, "portfolio_name")
        name_input.clear()
        name_input.send_keys(updated_name)
        
        # Change risk level if not already set to aggressive
        risk_level = self.wait_for_element(By.ID, "risk_level")
        risk_level.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='aggressive']").click()
        
        # Take screenshot of portfolio edit form
        self.take_screenshot("portfolio_edit_form")
        
        # Submit the form
        self.driver.find_element(By.ID, "save_portfolio_button").click()
        
        # Verify portfolio update success
        self.wait_for_element(By.CSS_SELECTOR, ".portfolio-save-success")
        
        # Take screenshot of success message
        self.take_screenshot("portfolio_edit_success")
        
        # Verify updated portfolio appears in the portfolios list
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        portfolios_list = self.wait_for_element(By.CSS_SELECTOR, ".portfolios-list")
        self.assertIn(updated_name, portfolios_list.text)
        
        logger.info(f"Portfolio updated from '{portfolio_name}' to '{updated_name}' successfully")


class FinancialCalculatorTest(PesaGuruBaseTest):
    """Test financial calculators functionality"""
    
    def setUp(self):
        """Login before each test"""
        # Login via API to get the authentication token
        self.api_login()
        
        # Navigate to login page and authenticate
        self.driver.get(f"{TEST_CONFIG['base_url']}/login")
        user = TEST_CONFIG['test_users']['existing_user']
        
        self.wait_for_element(By.ID, "email").send_keys(user['email'])
        self.wait_for_element(By.ID, "password").send_keys(user['password'])
        self.driver.find_element(By.ID, "login_button").click()
        
        # Wait for dashboard to load
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
    
    def test_01_investment_calculator(self):
        """Test investment calculator"""
        logger.info("Testing investment calculator")
        
        # Navigate to investment calculator
        self.driver.get(f"{TEST_CONFIG['base_url']}/calculators/investment")
        
        # Fill calculator form
        self.wait_for_element(By.ID, "initial_investment").send_keys("100000")
        self.wait_for_element(By.ID, "monthly_contribution").send_keys("10000")
        self.wait_for_element(By.ID, "investment_period").send_keys("10")  # 10 years
        self.wait_for_element(By.ID, "expected_return").send_keys("10")  # 10% annual return
        
        # Take screenshot of calculator form
        self.take_screenshot("investment_calculator_form")
        
        # Calculate results
        self.driver.find_element(By.ID, "calculate_button").click()
        
        # Verify results are displayed
        results_section = self.wait_for_element(By.CSS_SELECTOR, ".calculator-results")
        self.assertIsNotNone(results_section)
        
        # Check for final amount
        final_amount = self.wait_for_element(By.CSS_SELECTOR, ".final-amount")
        self.assertIsNotNone(final_amount.text)
        self.assertNotEqual(final_amount.text, "")
        
        # Check for results chart
        results_chart = self.wait_for_element(By.CSS_SELECTOR, ".results-chart")
        self.assertIsNotNone(results_chart)
        
        # Take screenshot of calculator results
        self.take_screenshot("investment_calculator_results")
        
        logger.info("Investment calculator validated successfully")
    
    def test_02_loan_calculator(self):
        """Test loan calculator"""
        logger.info("Testing loan calculator")
        
        # Navigate to loan calculator
        self.driver.get(f"{TEST_CONFIG['base_url']}/calculators/loan")
        
        # Fill calculator form
        self.wait_for_element(By.ID, "loan_amount").send_keys("1000000")
        self.wait_for_element(By.ID, "loan_term").send_keys("5")  # 5 years
        self.wait_for_element(By.ID, "interest_rate").send_keys("12")  # 12% interest
        
        # Take screenshot of calculator form
        self.take_screenshot("loan_calculator_form")
        
        # Calculate results
        self.driver.find_element(By.ID, "calculate_button").click()
        
        # Verify results are displayed
        results_section = self.wait_for_element(By.CSS_SELECTOR, ".calculator-results")
        self.assertIsNotNone(results_section)
        
        # Check for monthly payment
        monthly_payment = self.wait_for_element(By.CSS_SELECTOR, ".monthly-payment")
        self.assertIsNotNone(monthly_payment.text)
        self.assertNotEqual(monthly_payment.text, "")
        
        # Check for total payment
        total_payment = self.wait_for_element(By.CSS_SELECTOR, ".total-payment")
        self.assertIsNotNone(total_payment.text)
        
        # Check for amortization schedule
        amortization_table = self.wait_for_element(By.CSS_SELECTOR, ".amortization-table")
        self.assertIsNotNone(amortization_table)
        
        # Take screenshot of calculator results
        self.take_screenshot("loan_calculator_results")
        
        logger.info("Loan calculator validated successfully")
    
    def test_03_retirement_calculator(self):
        """Test retirement calculator"""
        logger.info("Testing retirement calculator")
        
        # Navigate to retirement calculator
        self.driver.get(f"{TEST_CONFIG['base_url']}/calculators/retirement")
        
        # Fill calculator form
        self.wait_for_element(By.ID, "current_age").send_keys("30")
        self.wait_for_element(By.ID, "retirement_age").send_keys("60")
        self.wait_for_element(By.ID, "current_savings").send_keys("500000")
        self.wait_for_element(By.ID, "monthly_contribution").send_keys("20000")
        self.wait_for_element(By.ID, "expected_return").send_keys("8")  # 8% annual return
        self.wait_for_element(By.ID, "retirement_duration").send_keys("25")  # 25 years in retirement
        
        # Take screenshot of calculator form
        self.take_screenshot("retirement_calculator_form")
        
        # Calculate results
        self.driver.find_element(By.ID, "calculate_button").click()
        
        # Verify results are displayed
        results_section = self.wait_for_element(By.CSS_SELECTOR, ".calculator-results")
        self.assertIsNotNone(results_section)
        
        # Check for retirement corpus
        retirement_corpus = self.wait_for_element(By.CSS_SELECTOR, ".retirement-corpus")
        self.assertIsNotNone(retirement_corpus.text)
        self.assertNotEqual(retirement_corpus.text, "")
        
        # Check for results chart
        results_chart = self.wait_for_element(By.CSS_SELECTOR, ".results-chart")
        self.assertIsNotNone(results_chart)
        
        # Take screenshot of calculator results
        self.take_screenshot("retirement_calculator_results")
        
        logger.info("Retirement calculator validated successfully")


class CompleteUserJourneyTest(PesaGuruBaseTest):
    """Test a complete user journey through the system"""
    
    def test_end_to_end_investment_journey(self):
        """Test a complete investment decision journey"""
        logger.info("Testing end-to-end investment journey")
        
        # Step 1: Register a new user
        new_user = {
            'email': f'journey_test_{datetime.now().strftime("%Y%m%d%H%M%S")}@example.com',
            'password': 'Journey@123',
            'first_name': 'Journey',
            'last_name': 'Test'
        }
        
        self.driver.get(f"{TEST_CONFIG['base_url']}/register")
        
        self.wait_for_element(By.ID, "first_name").send_keys(new_user['first_name'])
        self.wait_for_element(By.ID, "last_name").send_keys(new_user['last_name'])
        self.wait_for_element(By.ID, "email").send_keys(new_user['email'])
        self.wait_for_element(By.ID, "password").send_keys(new_user['password'])
        self.wait_for_element(By.ID, "confirm_password").send_keys(new_user['password'])
        
        # Accept terms if present
        terms_checkbox = self.driver.find_element(By.ID, "accept_terms")
        if not terms_checkbox.is_selected():
            terms_checkbox.click()
        
        # Register
        self.driver.find_element(By.ID, "register_button").click()
        
        # Wait for registration to complete
        self.wait_for_element(By.CSS_SELECTOR, ".registration-success")
        self.take_screenshot("journey_registration")
        
        # Step 2: Complete onboarding and financial profile
        if "onboarding" in self.driver.current_url:
            # Complete onboarding process
            self.wait_for_element(By.ID, "monthly_income").send_keys("100000")
            self.wait_for_element(By.ID, "monthly_expenses").send_keys("60000")
            
            # Select risk tolerance
            risk_tolerance = self.wait_for_element(By.ID, "risk_tolerance")
            risk_tolerance.click()
            self.wait_for_element(By.CSS_SELECTOR, "option[value='moderate']").click()
            
            # Submit onboarding
            self.driver.find_element(By.ID, "complete_onboarding_button").click()
            self.wait_for_element(By.CSS_SELECTOR, ".onboarding-complete")
            self.take_screenshot("journey_onboarding")
        
        # Step 3: Explore market data
        self.driver.get(f"{TEST_CONFIG['base_url']}/market-data")
        self.wait_for_element(By.CSS_SELECTOR, ".market-summary")
        self.take_screenshot("journey_market_data")
        
        # Check specific stock
        test_stock = TEST_CONFIG['test_stocks'][0]
        self.driver.get(f"{TEST_CONFIG['base_url']}/stock/{test_stock}")
        self.wait_for_element(By.CSS_SELECTOR, ".stock-price-chart")
        self.take_screenshot(f"journey_stock_{test_stock}")
        
        # Step 4: Use investment calculator
        self.driver.get(f"{TEST_CONFIG['base_url']}/calculators/investment")
        
        self.wait_for_element(By.ID, "initial_investment").send_keys("250000")
        self.wait_for_element(By.ID, "monthly_contribution").send_keys("15000")
        self.wait_for_element(By.ID, "investment_period").send_keys("15")  # 15 years
        self.wait_for_element(By.ID, "expected_return").send_keys("12")  # 12% annual return
        
        # Calculate results
        self.driver.find_element(By.ID, "calculate_button").click()
        self.wait_for_element(By.CSS_SELECTOR, ".calculator-results")
        self.take_screenshot("journey_calculator")
        
        # Step 5: Chat with the financial advisor bot
        self.driver.get(f"{TEST_CONFIG['base_url']}/chatbot")
        self.wait_for_element(By.CSS_SELECTOR, ".chatbot-container")
        
        # Ask for investment advice
        chat_input = self.wait_for_element(By.CSS_SELECTOR, ".chat-input")
        chat_input.send_keys("I want to invest 250,000 KES with 15,000 KES monthly for 15 years. What options do I have in Kenya?")
        chat_input.send_keys(Keys.RETURN)
        
        # Wait for response
        time.sleep(8)  # Allow time for comprehensive response
        self.take_screenshot("journey_chatbot_advice")
        
        # Step 6: Create an investment portfolio
        self.driver.get(f"{TEST_CONFIG['base_url']}/portfolio")
        self.wait_for_element_clickable(By.ID, "create_portfolio_button").click()
        
        # Fill portfolio details
        self.wait_for_element(By.ID, "portfolio_name").send_keys("My Long Term Portfolio")
        
        # Select risk level
        risk_level = self.wait_for_element(By.ID, "risk_level")
        risk_level.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='moderate']").click()
        
        # Enter investment amount
        self.wait_for_element(By.ID, "investment_amount").send_keys("250000")
        
        # Select stocks
        for i, stock in enumerate(TEST_CONFIG['test_stocks'][:4]):
            # Find stock selection element
            stock_checkbox = self.wait_for_element(By.CSS_SELECTOR, f"input[value='{stock}']")
            if not stock_checkbox.is_selected():
                stock_checkbox.click()
                
            # Set allocation
            allocation_input = self.wait_for_element(By.ID, f"allocation_{stock}")
            allocation_input.clear()
            allocation_input.send_keys(str(25))  # Equal 25% allocation each
        
        # Submit the form
        self.driver.find_element(By.ID, "save_portfolio_button").click()
        self.wait_for_element(By.CSS_SELECTOR, ".portfolio-save-success")
        self.take_screenshot("journey_portfolio_creation")
        
        # Step 7: Create a financial goal
        self.driver.get(f"{TEST_CONFIG['base_url']}/user/financial-goals")
        self.wait_for_element_clickable(By.ID, "add_goal_button").click()
        
        # Fill goal details
        self.wait_for_element(By.ID, "goal_name").send_keys("Retirement Nest Egg")
        
        # Select goal type
        goal_type = self.wait_for_element(By.ID, "goal_type")
        goal_type.click()
        self.wait_for_element(By.CSS_SELECTOR, "option[value='retirement']").click()
        
        # Fill target amount
        self.wait_for_element(By.ID, "target_amount").send_keys("10000000")  # 10M KES
        
        # Set target date (15 years from now)
        target_date = (datetime.now() + timedelta(days=365*15)).strftime("%Y-%m-%d")
        self.wait_for_element(By.ID, "target_date").send_keys(target_date)
        
        # Fill monthly contribution
        self.wait_for_element(By.ID, "monthly_contribution").send_keys("15000")
        
        # Save the goal
        self.driver.find_element(By.ID, "save_goal_button").click()
        self.wait_for_element(By.CSS_SELECTOR, ".goal-save-success")
        self.take_screenshot("journey_goal_creation")
        
        # Step 8: View dashboard with complete profile
        self.driver.get(f"{TEST_CONFIG['base_url']}/dashboard")
        self.wait_for_element(By.CSS_SELECTOR, ".dashboard-container")
        self.take_screenshot("journey_complete_dashboard")
        
        logger.info("End-to-end investment journey completed successfully")


def run_tests():
    """Run all end-to-end tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes to suite
    test_suite.addTest(unittest.makeSuite(UserRegistrationLoginTest))
    test_suite.addTest(unittest.makeSuite(UserProfileSetupTest))
    test_suite.addTest(unittest.makeSuite(MarketDataTest))
    test_suite.addTest(unittest.makeSuite(ChatbotInteractionTest))
    test_suite.addTest(unittest.makeSuite(InvestmentPortfolioTest))
    test_suite.addTest(unittest.makeSuite(FinancialCalculatorTest))
    test_suite.addTest(unittest.makeSuite(CompleteUserJourneyTest))
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # Print summary
    logger.info(f"\n=== End-to-End Test Summary ===")
    logger.info(f"Tests Run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    logger.info(f"===============================\n")
    
    return result


if __name__ == "__main__":
    run_tests()