import os
import sys
import pytest
import json
import time
import requests
import random
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
        
    def patch(self, url, json=None, headers=None):
        return self.session.patch(f"{self.base_url}{url}", json=json, headers=headers)
        
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

@pytest.fixture
def test_portfolio():
    """Create a test investment portfolio"""
    return {
        "name": f"Test Portfolio {int(time.time())}",
        "description": "A balanced investment portfolio for testing",
        "target_return": 12.5,
        "investments": [
            {"symbol": "SCOM", "name": "Safaricom PLC", "allocation": 30, "amount": 50000},
            {"symbol": "EQTY", "name": "Equity Group", "allocation": 25, "amount": 40000},
            {"symbol": "KCB", "name": "KCB Group", "allocation": 20, "amount": 30000},
            {"symbol": "SBIC", "name": "Stanbic Holdings", "allocation": 15, "amount": 25000},
            {"symbol": "COOP", "name": "Co-operative Bank", "allocation": 10, "amount": 15000}
        ]
    }

@pytest.fixture
def test_financial_goal():
    """Create a test financial goal"""
    return {
        "name": f"Test Goal {int(time.time())}",
        "goal_type": random.choice(["retirement", "education", "house", "emergency", "vacation"]),
        "target_amount": random.randint(500000, 10000000),
        "current_amount": random.randint(50000, 400000),
        "monthly_contribution": random.randint(5000, 30000),
        "target_date": (datetime.now() + timedelta(days=random.randint(365, 3650))).strftime("%Y-%m-%d"),
        "priority": random.choice(["high", "medium", "low"])
    }

@pytest.fixture
def test_loan_calculation():
    """Create test loan calculation data"""
    return {
        "principal": random.randint(100000, 5000000),
        "interest_rate": round(random.uniform(8.0, 18.0), 2),
        "loan_term_years": random.randint(1, 30),
        "loan_type": random.choice(["mortgage", "personal", "auto", "business", "education"])
    }

@pytest.fixture
def test_budget():
    """Create test budget data"""
    return {
        "name": f"Monthly Budget {int(time.time())}",
        "period": "monthly",
        "income": [
            {"source": "Salary", "amount": 150000},
            {"source": "Side Business", "amount": 50000}
        ],
        "expenses": [
            {"category": "Housing", "amount": 40000},
            {"category": "Food", "amount": 25000},
            {"category": "Transportation", "amount": 15000},
            {"category": "Utilities", "amount": 10000},
            {"category": "Entertainment", "amount": 20000},
            {"category": "Healthcare", "amount": 8000},
            {"category": "Savings", "amount": 30000},
            {"category": "Miscellaneous", "amount": 10000}
        ]
    }


class TestLoanCalculator:
    """Tests for loan calculator functionality"""
    
    def test_loan_payment_calculation(self, auth_headers, test_loan_calculation):
        """Test loan payment calculation"""
        response = client.post("/financial/loan-calculator", json=test_loan_calculation, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Loan calculator endpoint not implemented")
        
        # Assert successful calculation
        assert response.status_code == 200, f"Loan calculation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "monthly_payment" in data, "Monthly payment not in response"
        assert "total_payment" in data, "Total payment not in response"
        assert "total_interest" in data, "Total interest not in response"
        assert "amortization_schedule" in data, "Amortization schedule not in response"
        
        # Verify mathematical accuracy
        principal = test_loan_calculation["principal"]
        rate = test_loan_calculation["interest_rate"] / 100 / 12  # Monthly rate
        term = test_loan_calculation["loan_term_years"] * 12  # Term in months
        
        # Basic check: monthly payment should be > principal / term (since interest exists)
        assert data["monthly_payment"] > principal / term, "Monthly payment seems too low"
        
        # Total payment should be > principal
        assert data["total_payment"] > principal, "Total payment should exceed principal"
        
        # Total interest should be total_payment - principal
        expected_interest = data["total_payment"] - principal
        assert abs(data["total_interest"] - expected_interest) < 1, "Interest calculation is inconsistent"
    
    def test_loan_affordability(self, auth_headers):
        """Test loan affordability calculation"""
        # Affordability calculation typically requires income and expenses
        affordability_data = {
            "monthly_income": 150000,
            "monthly_expenses": 75000,
            "debt_to_income_ratio": 0.4,  # 40% maximum
            "loan_term_years": 20,
            "interest_rate": 12.5
        }
        
        response = client.post("/financial/loan-affordability", json=affordability_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Loan affordability endpoint not implemented")
        
        # Assert successful calculation
        assert response.status_code == 200, f"Loan affordability calculation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "maximum_loan_amount" in data, "Maximum loan amount not in response"
        assert "maximum_monthly_payment" in data, "Maximum monthly payment not in response"
        
        # Verify logical constraints
        # Maximum monthly payment should be less than or equal to income * debt ratio - expenses
        expected_max_payment = affordability_data["monthly_income"] * affordability_data["debt_to_income_ratio"] - affordability_data["monthly_expenses"]
        assert data["maximum_monthly_payment"] <= expected_max_payment, "Maximum payment exceeds affordability"
    
    def test_loan_comparison(self, auth_headers):
        """Test loan comparison functionality"""
        # Compare multiple loan options
        comparison_data = {
            "loans": [
                {
                    "name": "Option A - Bank X",
                    "principal": 2000000,
                    "interest_rate": 12.5,
                    "loan_term_years": 20,
                    "fees": 50000
                },
                {
                    "name": "Option B - Bank Y",
                    "principal": 2000000,
                    "interest_rate": 13.0,
                    "loan_term_years": 20,
                    "fees": 25000
                },
                {
                    "name": "Option C - Bank Z",
                    "principal": 2000000,
                    "interest_rate": 11.5,
                    "loan_term_years": 15,
                    "fees": 75000
                }
            ]
        }
        
        response = client.post("/financial/loan-comparison", json=comparison_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Loan comparison endpoint not implemented")
        
        # Assert successful comparison
        assert response.status_code == 200, f"Loan comparison failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "comparison_results" in data, "Comparison results not in response"
        assert len(data["comparison_results"]) == len(comparison_data["loans"]), "Not all loans compared"
        
        # Each result should have monthly payment, total cost, etc.
        for result in data["comparison_results"]:
            assert "name" in result, "Loan name missing"
            assert "monthly_payment" in result, "Monthly payment missing"
            assert "total_cost" in result, "Total cost missing"
            assert "total_interest" in result, "Total interest missing"


class TestInvestmentCalculator:
    """Tests for investment calculator functionality"""
    
    def test_compound_interest_calculation(self, auth_headers):
        """Test compound interest calculation"""
        investment_data = {
            "principal": 100000,
            "annual_rate": 12.0,
            "years": 10,
            "compounds_per_year": 12,  # Monthly compounding
            "additional_contribution": 5000,
            "contribution_frequency": "monthly"
        }
        
        response = client.post("/financial/investment-calculator", json=investment_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Investment calculator endpoint not implemented")
        
        # Assert successful calculation
        assert response.status_code == 200, f"Investment calculation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "final_amount" in data, "Final amount not in response"
        assert "total_contributions" in data, "Total contributions not in response"
        assert "total_interest_earned" in data, "Total interest earned not in response"
        assert "yearly_breakdown" in data, "Yearly breakdown not in response"
        
        # Verify the final amount makes sense (should be > principal + contributions)
        total_contributions = investment_data["principal"] + (investment_data["additional_contribution"] * 12 * investment_data["years"])
        assert data["final_amount"] > total_contributions, "Final amount should exceed total contributions"
        
        # Verify interest earned = final amount - total contributions
        expected_interest = data["final_amount"] - data["total_contributions"]
        assert abs(data["total_interest_earned"] - expected_interest) < 1, "Interest calculation is inconsistent"
    
    def test_retirement_calculator(self, auth_headers):
        """Test retirement calculator"""
        retirement_data = {
            "current_age": 30,
            "retirement_age": 60,
            "life_expectancy": 85,
            "current_savings": 500000,
            "monthly_contribution": 20000,
            "expected_annual_return": 10.0,
            "expected_inflation_rate": 6.0,
            "desired_monthly_income": 200000
        }
        
        response = client.post("/financial/retirement-calculator", json=retirement_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Retirement calculator endpoint not implemented")
        
        # Assert successful calculation
        assert response.status_code == 200, f"Retirement calculation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "retirement_corpus_needed" in data, "Retirement corpus needed not in response"
        assert "projected_retirement_corpus" in data, "Projected retirement corpus not in response"
        assert "monthly_income_gap" in data or "surplus_shortfall" in data, "Income gap/surplus not in response"
        
        # Basic validation: retirement needed should be > 0
        assert data["retirement_corpus_needed"] > 0, "Retirement corpus needed should be positive"
        
        # Yearly breakdown should cover all years from current age to retirement
        if "yearly_breakdown" in data:
            expected_years = retirement_data["retirement_age"] - retirement_data["current_age"] + 1
            assert len(data["yearly_breakdown"]) == expected_years, "Yearly breakdown doesn't cover all years"
    
    def test_goal_based_investment(self, auth_headers):
        """Test goal-based investment calculator"""
        goal_data = {
            "goal_amount": 5000000,
            "time_horizon_years": 10,
            "current_investment": 500000,
            "expected_annual_return": 12.0,
            "risk_tolerance": "moderate"
        }
        
        response = client.post("/financial/goal-calculator", json=goal_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Goal-based calculator endpoint not implemented")
        
        # Assert successful calculation
        assert response.status_code == 200, f"Goal-based calculation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "required_monthly_investment" in data, "Required monthly investment not in response"
        assert "projected_final_amount" in data, "Projected final amount not in response"
        assert "recommended_asset_allocation" in data, "Recommended asset allocation not in response"
        
        # Validate that the recommended allocation percentages sum to 100%
        if "recommended_asset_allocation" in data:
            total_allocation = sum(allocation["percentage"] for allocation in data["recommended_asset_allocation"])
            assert abs(total_allocation - 100.0) < 0.01, "Asset allocation percentages should sum to 100%"


class TestPortfolioAnalysis:
    """Tests for portfolio analysis functionality"""
    
    def test_create_portfolio(self, auth_headers, test_portfolio):
        """Test creating a new portfolio"""
        response = client.post("/financial/portfolios", json=test_portfolio, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Portfolio creation endpoint not implemented")
        
        # Assert successful creation
        assert response.status_code in [200, 201], f"Portfolio creation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "portfolio_id" in data, "Portfolio ID not in response"
        assert "name" in data, "Portfolio name not in response"
        assert data["name"] == test_portfolio["name"], "Portfolio name doesn't match"
        
        # Store portfolio ID for other tests
        return data["portfolio_id"]
    
    def test_portfolio_analysis(self, auth_headers, test_portfolio):
        """Test portfolio analysis functionality"""
        # First create a portfolio
        portfolio_id = self.test_create_portfolio(auth_headers, test_portfolio)
        if not portfolio_id:
            pytest.skip("Could not create portfolio for analysis")
        
        # Now request portfolio analysis
        response = client.get(f"/financial/portfolios/{portfolio_id}/analysis", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Portfolio analysis endpoint not implemented")
        
        # Assert successful analysis
        assert response.status_code == 200, f"Portfolio analysis failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "risk_metrics" in data, "Risk metrics not in response"
        assert "performance_metrics" in data, "Performance metrics not in response"
        assert "diversification_analysis" in data, "Diversification analysis not in response"
        
        # Verify risk metrics
        risk_metrics = data["risk_metrics"]
        assert "volatility" in risk_metrics, "Volatility not in risk metrics"
        assert "sharpe_ratio" in risk_metrics, "Sharpe ratio not in risk metrics"
        
        # Verify performance metrics
        performance = data["performance_metrics"]
        assert "expected_return" in performance, "Expected return not in performance metrics"
        assert "historical_return" in performance, "Historical return not in performance metrics"
    
    def test_portfolio_optimization(self, auth_headers, test_portfolio):
        """Test portfolio optimization functionality"""
        # First create a portfolio
        portfolio_id = self.test_create_portfolio(auth_headers, test_portfolio)
        if not portfolio_id:
            pytest.skip("Could not create portfolio for optimization")
        
        # Define optimization parameters
        optimization_params = {
            "strategy": "max_return",  # or "min_risk", "efficient_frontier"
            "risk_tolerance": "moderate",
            "constraints": {
                "max_allocation_per_asset": 40,  # Maximum 40% in any single asset
                "min_allocation_per_asset": 5    # Minimum 5% in any single asset
            }
        }
        
        # Now request portfolio optimization
        response = client.post(f"/financial/portfolios/{portfolio_id}/optimize", 
                              json=optimization_params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Portfolio optimization endpoint not implemented")
        
        # Assert successful optimization
        assert response.status_code == 200, f"Portfolio optimization failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "optimized_portfolio" in data, "Optimized portfolio not in response"
        assert "expected_return" in data, "Expected return not in response"
        assert "expected_risk" in data, "Expected risk not in response"
        
        # Verify optimized allocations
        optimized = data["optimized_portfolio"]
        assert "allocations" in optimized, "Allocations not in optimized portfolio"
        
        # Validate that the optimized allocations meet constraints
        allocations = optimized["allocations"]
        total_allocation = sum(allocation["percentage"] for allocation in allocations)
        assert abs(total_allocation - 100.0) < 0.01, "Allocations should sum to 100%"
        
        # Check max/min constraints
        for allocation in allocations:
            assert allocation["percentage"] <= optimization_params["constraints"]["max_allocation_per_asset"], \
                f"Allocation for {allocation['symbol']} exceeds maximum constraint"
            assert allocation["percentage"] >= optimization_params["constraints"]["min_allocation_per_asset"], \
                f"Allocation for {allocation['symbol']} is below minimum constraint"
    
    def test_portfolio_rebalancing(self, auth_headers, test_portfolio):
        """Test portfolio rebalancing functionality"""
        # First create a portfolio
        portfolio_id = self.test_create_portfolio(auth_headers, test_portfolio)
        if not portfolio_id:
            pytest.skip("Could not create portfolio for rebalancing")
        
        # Define current holdings that have drifted from target
        current_holdings = [
            {"symbol": "SCOM", "current_value": 60000, "target_allocation": 30},  # Overweight
            {"symbol": "EQTY", "current_value": 35000, "target_allocation": 25},  # Underweight
            {"symbol": "KCB", "current_value": 15000, "target_allocation": 20},   # Underweight
            {"symbol": "SBIC", "current_value": 25000, "target_allocation": 15},  # On target
            {"symbol": "COOP", "current_value": 25000, "target_allocation": 10}   # Overweight
        ]
        
        # Request rebalancing
        response = client.post(f"/financial/portfolios/{portfolio_id}/rebalance", 
                              json={"holdings": current_holdings}, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Portfolio rebalancing endpoint not implemented")
        
        # Assert successful rebalancing
        assert response.status_code == 200, f"Portfolio rebalancing failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "rebalancing_actions" in data, "Rebalancing actions not in response"
        assert "total_portfolio_value" in data, "Total portfolio value not in response"
        
        # Verify rebalancing actions
        actions = data["rebalancing_actions"]
        for action in actions:
            assert "symbol" in action, "Symbol missing in rebalancing action"
            assert "action" in action, "Action type missing in rebalancing action"
            assert "amount" in action, "Amount missing in rebalancing action"
            assert action["action"] in ["buy", "sell", "hold"], f"Invalid action type: {action['action']}"


class TestFinancialGoals:
    """Tests for financial goals functionality"""
    
    def test_create_financial_goal(self, auth_headers, test_financial_goal):
        """Test creating a new financial goal"""
        response = client.post("/financial/goals", json=test_financial_goal, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Financial goals endpoint not implemented")
        
        # Assert successful creation
        assert response.status_code in [200, 201], f"Financial goal creation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "goal_id" in data, "Goal ID not in response"
        assert "name" in data, "Goal name not in response"
        assert data["name"] == test_financial_goal["name"], "Goal name doesn't match"
        
        # Store goal ID for other tests
        return data["goal_id"]
    
    def test_goal_progress_tracking(self, auth_headers, test_financial_goal):
        """Test financial goal progress tracking"""
        # First create a goal
        goal_id = self.test_create_financial_goal(auth_headers, test_financial_goal)
        if not goal_id:
            pytest.skip("Could not create financial goal for tracking")
        
        # Get goal progress
        response = client.get(f"/financial/goals/{goal_id}/progress", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Goal progress endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Goal progress retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "progress_percentage" in data, "Progress percentage not in response"
        assert "remaining_amount" in data, "Remaining amount not in response"
        assert "remaining_time" in data, "Remaining time not in response"
        assert "on_track" in data, "On-track status not in response"
        
        # Basic validations
        assert 0 <= data["progress_percentage"] <= 100, "Progress percentage should be between 0 and 100"
        assert data["remaining_amount"] <= test_financial_goal["target_amount"], "Remaining amount should not exceed target"
    
    def test_goal_recommendations(self, auth_headers, test_financial_goal):
        """Test financial goal recommendations"""
        # First create a goal
        goal_id = self.test_create_financial_goal(auth_headers, test_financial_goal)
        if not goal_id:
            pytest.skip("Could not create financial goal for recommendations")
        
        # Get goal recommendations
        response = client.get(f"/financial/goals/{goal_id}/recommendations", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Goal recommendations endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Goal recommendations retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "investment_recommendations" in data, "Investment recommendations not in response"
        assert "suggested_monthly_contribution" in data, "Suggested monthly contribution not in response"
        assert "expected_timeline" in data, "Expected timeline not in response"
        
        # Verify investment recommendations
        recommendations = data["investment_recommendations"]
        assert len(recommendations) > 0, "No investment recommendations provided"
        
        for recommendation in recommendations:
            assert "asset_class" in recommendation, "Asset class not in recommendation"
            assert "allocation_percentage" in recommendation, "Allocation percentage not in recommendation"
            assert "expected_return" in recommendation, "Expected return not in recommendation"


class TestBudgetPlanning:
    """Tests for budget planning functionality"""
    
    def test_create_budget(self, auth_headers, test_budget):
        """Test creating a new budget"""
        response = client.post("/financial/budgets", json=test_budget, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Budget creation endpoint not implemented")
        
        # Assert successful creation
        assert response.status_code in [200, 201], f"Budget creation failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "budget_id" in data, "Budget ID not in response"
        assert "name" in data, "Budget name not in response"
        assert data["name"] == test_budget["name"], "Budget name doesn't match"
        
        # Store budget ID for other tests
        return data["budget_id"]
    
    def test_budget_analysis(self, auth_headers, test_budget):
        """Test budget analysis functionality"""
        # First create a budget
        budget_id = self.test_create_budget(auth_headers, test_budget)
        if not budget_id:
            pytest.skip("Could not create budget for analysis")
        
        # Get budget analysis
        response = client.get(f"/financial/budgets/{budget_id}/analysis", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Budget analysis endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Budget analysis retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "total_income" in data, "Total income not in analysis"
        assert "total_expenses" in data, "Total expenses not in analysis"
        assert "savings_amount" in data, "Savings amount not in analysis"
        assert "savings_rate" in data, "Savings rate not in analysis"
        assert "expense_breakdown" in data, "Expense breakdown not in analysis"
        
        # Validate that expense breakdown categories match input budget
        expense_categories = [expense["category"] for expense in test_budget["expenses"]]
        breakdown_categories = [breakdown["category"] for breakdown in data["expense_breakdown"]]
        for category in expense_categories:
            assert category in breakdown_categories, f"Category {category} missing from breakdown"
        
        # Validate total income and expenses
        expected_income = sum(income["amount"] for income in test_budget["income"])
        expected_expenses = sum(expense["amount"] for expense in test_budget["expenses"])
        
        assert data["total_income"] == expected_income, "Total income doesn't match"
        assert data["total_expenses"] == expected_expenses, "Total expenses don't match"
        assert data["savings_amount"] == expected_income - expected_expenses, "Savings amount incorrect"
    
    def test_budget_recommendations(self, auth_headers, test_budget):
        """Test budget recommendations functionality"""
        # First create a budget
        budget_id = self.test_create_budget(auth_headers, test_budget)
        if not budget_id:
            pytest.skip("Could not create budget for recommendations")
        
        # Get budget recommendations
        response = client.get(f"/financial/budgets/{budget_id}/recommendations", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Budget recommendations endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Budget recommendations retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "saving_recommendations" in data, "Saving recommendations not in response"
        assert "expense_reduction_opportunities" in data, "Expense reduction opportunities not in response"
        assert "budget_health_score" in data, "Budget health score not in response"
        
        # Validate budget health score range
        assert 0 <= data["budget_health_score"] <= 100, "Budget health score should be between 0 and 100"


class TestRiskAssessment:
    """Tests for risk assessment functionality"""
    
    def test_risk_questionnaire(self, auth_headers):
        """Test risk assessment questionnaire"""
        # Sample questionnaire answers
        questionnaire_data = {
            "answers": [
                {"question_id": "time_horizon", "answer": "5_to_10_years"},
                {"question_id": "investment_experience", "answer": "moderate"},
                {"question_id": "income_stability", "answer": "stable"},
                {"question_id": "loss_tolerance", "answer": "moderate"},
                {"question_id": "financial_goals", "answer": "growth"},
                {"question_id": "emergency_fund", "answer": "yes"},
                {"question_id": "investment_knowledge", "answer": "knowledgeable"}
            ]
        }
        
        response = client.post("/financial/risk-assessment", json=questionnaire_data, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Risk assessment endpoint not implemented")
        
        # Assert successful assessment
        assert response.status_code == 200, f"Risk assessment failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "risk_profile" in data, "Risk profile not in response"
        assert "risk_score" in data, "Risk score not in response"
        assert "asset_allocation_recommendation" in data, "Asset allocation recommendation not in response"
        
        # Validate risk profile
        assert data["risk_profile"] in ["conservative", "moderately_conservative", "moderate", 
                                      "moderately_aggressive", "aggressive"], "Invalid risk profile"
        
        # Validate risk score range
        assert 0 <= data["risk_score"] <= 100, "Risk score should be between 0 and 100"
        
        # Validate asset allocation recommendation
        allocations = data["asset_allocation_recommendation"]
        assert "equities" in allocations, "Equities allocation missing"
        assert "fixed_income" in allocations, "Fixed income allocation missing"
        assert "cash" in allocations, "Cash allocation missing"
        
        # Allocations should sum to 100%
        total_allocation = sum(allocations.values())
        assert abs(total_allocation - 100.0) < 0.01, "Asset allocations should sum to 100%"
    
    def test_risk_profile_update(self, auth_headers):
        """Test updating user risk profile"""
        # Updated risk profile data
        risk_update = {
            "risk_profile": "moderately_aggressive",
            "risk_tolerance": "high",
            "investment_timeline": "long_term",
            "emergency_fund_status": "adequate"
        }
        
        response = client.put("/financial/risk-profile", json=risk_update, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Risk profile update endpoint not implemented")
        
        # Assert successful update
        assert response.status_code == 200, f"Risk profile update failed: {response.text}"
        
        # Verify response indicates success
        data = response.json()
        assert "success" in data, "Success indicator not in response"
        assert data["success"] is True, "Update was not successful"
        
        # Verify updated profile is returned
        assert "updated_profile" in data, "Updated profile not in response"
        assert data["updated_profile"]["risk_profile"] == risk_update["risk_profile"], "Risk profile not updated"


class TestMarketData:
    """Tests for market data functionality"""
    
    def test_stock_price_data(self, auth_headers):
        """Test retrieving stock price data"""
        # Test with well-known Kenyan stock
        stock_symbol = "SCOM"  # Safaricom
        
        response = client.get(f"/financial/market/stocks/{stock_symbol}", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock price endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock price retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "name" in data, "Company name not in response"
        assert "current_price" in data, "Current price not in response"
        assert "day_change" in data, "Day change not in response"
        assert "day_change_percent" in data, "Day change percent not in response"
        
        # Verify symbol matches request
        assert data["symbol"] == stock_symbol, "Returned symbol doesn't match request"
    
    def test_market_indices(self, auth_headers):
        """Test retrieving market indices data"""
        response = client.get("/financial/market/indices", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market indices endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market indices retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert isinstance(data, list), "Expected list of indices"
        
        # There should be at least one index (NSE 20)
        assert len(data) > 0, "No indices returned"
        
        # Verify each index has required fields
        for index in data:
            assert "name" in index, "Index name not in response"
            assert "value" in index, "Index value not in response"
            assert "change" in index, "Index change not in response"
            assert "change_percent" in index, "Index change percent not in response"
    
    def test_historical_data(self, auth_headers):
        """Test retrieving historical price data"""
        # Test parameters
        stock_symbol = "SCOM"  # Safaricom
        params = {
            "period": "1y",    # 1 year
            "interval": "1d"   # Daily data
        }
        
        response = client.get(f"/financial/market/history/{stock_symbol}", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Historical data endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Historical data retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Symbol not in response"
        assert "period" in data, "Period not in response"
        assert "interval" in data, "Interval not in response"
        assert "data" in data, "Historical data not in response"
        
        # Verify historical data is a non-empty list
        assert isinstance(data["data"], list), "Historical data should be a list"
        assert len(data["data"]) > 0, "No historical data points returned"
        
        # Verify data points have required fields
        for point in data["data"]:
            assert "date" in point, "Date not in data point"
            assert "close" in point, "Close price not in data point"
            assert "volume" in point, "Volume not in data point"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])