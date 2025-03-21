import requests
import json
import os
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoalsAPI:
    """Class to handle financial goals API integration for PesaGuru in Kenya"""
    
    def __init__(self, base_url: str = None, token: str = None, client_id: str = None, client_secret: str = None):
        """
        Initialize the Financial Goals API client with OAuth2 authentication
        
        Args:
            base_url: Base URL for the goals API (defaults to env variable)
            token: OAuth2 token (if already authenticated)
            client_id: OAuth2 client ID for authentication
            client_secret: OAuth2 client secret for authentication
        """
        self.base_url = base_url or os.environ.get("PESAGURU_API_URL", "http://localhost:8000/api")
        self.goals_endpoint = f"{self.base_url}/financial-goals"
        
        # Authentication credentials
        self.token = token
        self.client_id = client_id or os.environ.get("PESAGURU_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("PESAGURU_CLIENT_SECRET")
        self.token_expiry = None
        
        # Rate limiting
        self.rate_limit_remaining = 100  # Default high value until we get actual limit
        self.rate_limit_reset = 0
        
        # Kenyan financial goal categories
        self.kenyan_goal_categories = [
            "Emergency Fund",
            "Home Purchase (Mortgage)",
            "Land Purchase",
            "School Fees",
            "College Education",
            "Wedding",
            "Car Purchase",
            "Business Startup",
            "Harambee Contribution",
            "Chama Investment",
            "Retirement (Pension)",
            "NHIF/NSSF Payments",
            "M-Shwari Savings",
            "Farming Investment",
            "Travel",
            "Housing Development",
            "Family Support"
        ]
    
    def _get_headers(self):
        """
        Get request headers with authentication token
        
        Returns:
            Dict with headers including auth token
        """
        # Check if token is expired and refresh if needed
        if not self.token or (self.token_expiry and datetime.now() >= self.token_expiry):
            self._refresh_token()
            
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}" if self.token else ""
        }
    
    def _refresh_token(self):
        """Refresh OAuth2 token using client credentials flow"""
        try:
            if not self.client_id or not self.client_secret:
                logger.warning("Cannot refresh token: Missing client credentials")
                return
                
            response = requests.post(
                f"{self.base_url}/auth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            self.token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            logger.info("OAuth2 token refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing OAuth2 token: {e}")
    
    def _handle_rate_limiting(self, response):
        """
        Update rate limit information based on response headers
        
        Args:
            response: Requests response object
        """
        # Extract rate limit headers
        self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 100))
        self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))
        
        # If we're close to being rate limited, log a warning
        if self.rate_limit_remaining < 10:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset)
            logger.warning(f"API rate limit almost reached. {self.rate_limit_remaining} requests remaining. Reset at {reset_time}")
            
        # If we're actually rate limited, wait until reset
        if self.rate_limit_remaining <= 0:
            current_time = time.time()
            sleep_time = max(0, self.rate_limit_reset - current_time)
            
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time} seconds before retrying.")
                time.sleep(sleep_time)
    
    def _api_request(self, method, endpoint, **kwargs):
        """
        Make an API request with error handling and rate limiting
        
        Args:
            method: HTTP method (get, post, put, delete)
            endpoint: API endpoint to call
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response data or error dict
        """
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop('headers', self._get_headers())
        
        # Retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    **kwargs
                )
                
                # Handle rate limiting
                if response.status_code == 429:  # Too Many Requests
                    retry_count += 1
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    sleep_time = max(1, reset_time - time.time())  # At least 1 second
                    logger.warning(f"Rate limited. Retrying in {sleep_time} seconds... (Attempt {retry_count}/{max_retries})")
                    time.sleep(sleep_time)
                    continue
                
                # Update rate limit info if headers present
                self._handle_rate_limiting(response)
                
                # Handle response
                if response.status_code in (200, 201, 204):
                    if method.lower() == 'delete':
                        return {"success": True, "message": "Operation completed successfully"}
                    return response.json() if response.content else {"success": True}
                
                # Handle authentication errors
                if response.status_code == 401:
                    retry_count += 1
                    logger.warning(f"Authentication failed. Refreshing token and retrying... (Attempt {retry_count}/{max_retries})")
                    self._refresh_token()
                    headers = self._get_headers()
                    continue
                    
                # Handle other errors
                error_msg = f"API error: {response.status_code}"
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict) and 'detail' in error_data:
                        error_msg = error_data['detail']
                except:
                    error_msg = response.text or error_msg
                    
                logger.error(f"API request failed: {error_msg}")
                return {"error": error_msg, "status_code": response.status_code}
                
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Request failed. Retrying in {retry_count} seconds... (Attempt {retry_count}/{max_retries})")
                    time.sleep(retry_count)  # Exponential backoff
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    return {"error": str(e)}


# Example usage of the GoalsAPI class
def main():
    """
    Example usage of the GoalsAPI for managing financial goals
    """
    # Initialize the API client
    api = GoalsAPI(
        base_url="http://localhost:8000/api",
        client_id="your_client_id",
        client_secret="your_client_secret"
    )
    
    # Example user ID
    user_id = "user123"
    
    # Create a new goal
    new_goal = {
        "name": "Emergency Fund",
        "target_amount": 500000,  # 500K KES
        "current_amount": 50000,  # 50K KES already saved
        "deadline": "2025-12-31",
        "category": "Emergency Fund",
        "priority": 5,  # High priority
        "description": "Save 6 months of expenses for emergencies"
    }
    
    created_goal = api.create_goal(user_id, new_goal)
    print(f"Created goal: {created_goal}\n")
    
    # Get all user goals
    user_goals = api.get_user_goals(user_id)
    print(f"User has {len(user_goals)} goals\n")
    
    # Get goal statistics
    stats = api.get_goal_statistics(user_id)
    print(f"Goal statistics: {stats}\n")
    
    # Analyze goal feasibility
    if user_goals:
        goal_id = user_goals[0].get("id")
        feasibility = api.analyze_goal_feasibility(user_id, goal_id, monthly_contribution=10000)
        print(f"Goal feasibility: {feasibility}\n")
        
        # Make a contribution
        contribution = api.record_goal_contribution(goal_id, 15000)
        print(f"Recorded contribution: {contribution}\n")
    
    # Get prioritized goals
    prioritized = api.prioritize_goals(user_id)
    print(f"Prioritized goals: {prioritized}\n")
    
    # Calculate savings plan
    savings_plan = api.calculate_savings_plan(user_id, monthly_budget=30000)
    print(f"Savings plan: {savings_plan}\n")
    
    # Get goal recommendations
    recommendations = api.generate_goal_recommendations(user_id, income=100000, age=35)
    print(f"Goal recommendations: {recommendations}\n")


if __name__ == "__main__":
    main()
    
    def track_goal_progress_history(self, goal_id: str, period: str = 'monthly') -> List[Dict]:
        """
        Get historical progress for a specific goal
        
        Args:
            goal_id: Unique identifier for the goal
            period: Tracking period ('weekly', 'monthly', 'quarterly')
                
        Returns:
            List of progress snapshots with dates and amounts
        """
        params = {"period": period}
        response = self._api_request("get", f"financial-goals/{goal_id}/history", params=params)
        return response if isinstance(response, list) else []
    
    def prioritize_goals(self, user_id: str) -> List[Dict]:
        """
        Get prioritized list of user goals based on deadline, importance, and feasibility
        
        Args:
            user_id: Unique identifier for the user
                
        Returns:
            List of goals sorted by priority with recommendation notes
        """
        try:
            # Get user goals
            goals = self.get_user_goals(user_id)
            if not goals:
                return []
            
            # Calculate priority scores for each goal
            prioritized_goals = []
            now = datetime.now()
            
            for goal in goals:
                # Skip completed goals
                if goal.get("current_amount", 0) >= goal.get("target_amount", 0):
                    continue
                
                # Calculate urgency based on deadline
                deadline_score = 0
                if "deadline" in goal and goal["deadline"]:
                    deadline = datetime.fromisoformat(goal["deadline"].replace("Z", "+00:00") if "Z" in goal["deadline"] else goal["deadline"])
                    days_remaining = (deadline - now).days
                    if days_remaining <= 0:
                        deadline_score = 100  # Overdue
                    elif days_remaining <= 30:
                        deadline_score = 90  # Urgent (1 month)
                    elif days_remaining <= 90:
                        deadline_score = 80  # Very soon (3 months)
                    elif days_remaining <= 180:
                        deadline_score = 70  # Soon (6 months)
                    elif days_remaining <= 365:
                        deadline_score = 60  # This year
                    else:
                        deadline_score = 50  # Long-term
                
                # Get explicit priority if available
                explicit_priority = goal.get("priority", 3)  # Default to medium priority
                priority_score = explicit_priority * 20  # Scale 1-5 to 20-100
                
                # Calculate progress score (inverse - less progress means higher priority)
                progress = goal.get("current_amount", 0) / goal.get("target_amount", 1)
                progress_score = 100 - (progress * 100)
                
                # Calculate overall priority score
                overall_score = (deadline_score * 0.4) + (priority_score * 0.4) + (progress_score * 0.2)
                
                # Add recommendation notes
                if deadline_score >= 90:
                    recommendation = "Urgent! Focus on this goal immediately."
                elif deadline_score >= 70:
                    recommendation = "High priority. Allocate significant resources to this goal."
                elif priority_score >= 80:
                    recommendation = "Important goal based on your priorities."
                elif progress_score >= 80:
                    recommendation = "This goal needs attention as it has limited progress."
                else:
                    recommendation = "Continue regular contributions to meet this goal."
                
                # Add to list
                prioritized_goals.append({
                    **goal,
                    "priority_score": round(overall_score, 2),
                    "recommendation": recommendation
                })
            
            # Sort by priority score (highest first)
            return sorted(prioritized_goals, key=lambda x: x["priority_score"], reverse=True)
                
        except Exception as e:
            logger.error(f"Error prioritizing goals for user {user_id}: {e}")
            return []
    
    def calculate_savings_plan(self, user_id: str, monthly_budget: float = None) -> Dict:
        """
        Calculate optimal savings distribution across all user goals
        
        Args:
            user_id: Unique identifier for the user
            monthly_budget: Total monthly amount available for savings (optional)
                
        Returns:
            Savings plan with allocation per goal
        """
        try:
            # Get prioritized goals
            prioritized_goals = self.prioritize_goals(user_id)
            if not prioritized_goals:
                return {"message": "No active goals found", "allocations": []}
            
            # If no monthly budget specified, estimate from goals
            if not monthly_budget:
                # Calculate total required monthly contribution across all goals
                total_remaining = sum(goal.get("target_amount", 0) - goal.get("current_amount", 0) for goal in prioritized_goals)
                avg_months = 24  # Default to 2 years average timeline
                monthly_budget = total_remaining / avg_months
            
            # Distribute budget based on priority scores
            total_priority = sum(goal.get("priority_score", 0) for goal in prioritized_goals)
            allocations = []
            
            for goal in prioritized_goals:
                # Calculate weight based on priority score
                weight = goal.get("priority_score", 0) / total_priority if total_priority > 0 else 0
                
                # Calculate allocation
                allocation = monthly_budget * weight
                
                # Calculate months to completion with this allocation
                remaining = goal.get("target_amount", 0) - goal.get("current_amount", 0)
                months_to_completion = remaining / allocation if allocation > 0 else float('inf')
                
                allocations.append({
                    "goal_id": goal.get("id"),
                    "goal_name": goal.get("name"),
                    "monthly_allocation": round(allocation, 2),
                    "monthly_allocation_display": f"KSh {allocation:,.2f}",
                    "weight_percentage": round(weight * 100, 2),
                    "months_to_completion": round(months_to_completion, 1),
                    "completion_date": (datetime.now() + timedelta(days=30 * months_to_completion)).strftime("%Y-%m-%d")
                })
            
            return {
                "monthly_budget": monthly_budget,
                "monthly_budget_display": f"KSh {monthly_budget:,.2f}",
                "allocations": allocations
            }
                
        except Exception as e:
            logger.error(f"Error calculating savings plan for user {user_id}: {e}")
            return {"error": str(e)}
    
    def generate_goal_recommendations(self, user_id: str, income: float = None, age: int = None) -> List[Dict]:
        """
        Generate recommended financial goals based on user profile
        
        Args:
            user_id: Unique identifier for the user
            income: Monthly income in KES (optional)
            age: User's age (optional)
                
        Returns:
            List of recommended goals with parameters
        """
        try:
            # Try to get recommendations from API if income and age are provided
            if income and age:
                params = {"income": income, "age": age}
                api_recommendations = self._api_request("get", f"financial-goals/recommendations/{user_id}", params=params)
                if isinstance(api_recommendations, list) and api_recommendations:
                    return api_recommendations
            
            # Fallback: Generate basic recommendations based on Kenyan financial needs
            recommendations = []
            
            # Always recommend emergency fund
            recommendations.append({
                "name": "Emergency Fund",
                "description": "Save 3-6 months of expenses for emergencies",
                "category": "Emergency Fund",
                "target_amount": income * 6 if income else 100000,  # 6 months income or default 100K KES
                "priority": 5,  # Highest priority
                "timeline_months": 24,
                "target_amount_display": f"KSh {(income * 6 if income else 100000):,.2f}",
                "monthly_contribution": (income * 6 if income else 100000) / 24,
                "monthly_contribution_display": f"KSh {((income * 6 if income else 100000) / 24):,.2f}"
            })
            
            # Age-based recommendations
            if age is not None:
                if age < 30:
                    # Young adults: Education, land/home deposit, wedding
                    recommendations.append({
                        "name": "Land Purchase Fund",
                        "description": "Save for a land purchase in Kenya",
                        "category": "Land Purchase",
                        "target_amount": 1000000,  # 1M KES
                        "priority": 4,
                        "timeline_months": 60,
                        "target_amount_display": "KSh 1,000,000.00",
                        "monthly_contribution": 1000000 / 60,
                        "monthly_contribution_display": f"KSh {(1000000 / 60):,.2f}"
                    })
                    
                    recommendations.append({
                        "name": "Further Education",
                        "description": "Save for further education or skill development",
                        "category": "College Education",
                        "target_amount": 300000,  # 300K KES
                        "priority": 3,
                        "timeline_months": 36,
                        "target_amount_display": "KSh 300,000.00",
                        "monthly_contribution": 300000 / 36,
                        "monthly_contribution_display": f"KSh {(300000 / 36):,.2f}"
                    })
                    
                elif age < 45:
                    # Middle-aged: Children's education, home purchase, business
                    recommendations.append({
                        "name": "Children's Education Fund",
                        "description": "Save for your children's education",
                        "category": "School Fees",
                        "target_amount": 1500000,  # 1.5M KES
                        "priority": 4,
                        "timeline_months": 120,
                        "target_amount_display": "KSh 1,500,000.00",
                        "monthly_contribution": 1500000 / 120,
                        "monthly_contribution_display": f"KSh {(1500000 / 120):,.2f}"
                    })
                    
                    recommendations.append({
                        "name": "Business Investment",
                        "description": "Save to start or expand a business",
                        "category": "Business Startup",
                        "target_amount": 500000,  # 500K KES
                        "priority": 3,
                        "timeline_months": 36,
                        "target_amount_display": "KSh 500,000.00",
                        "monthly_contribution": 500000 / 36,
                        "monthly_contribution_display": f"KSh {(500000 / 36):,.2f}"
                    })
                    
                else:
                    # Older: Retirement, health fund, family support
                    recommendations.append({
                        "name": "Retirement Fund",
                        "description": "Additional savings for retirement beyond NSSF",
                        "category": "Retirement (Pension)",
                        "target_amount": 3000000,  # 3M KES
                        "priority": 5,
                        "timeline_months": 120,
                        "target_amount_display": "KSh 3,000,000.00",
                        "monthly_contribution": 3000000 / 120,
                        "monthly_contribution_display": f"KSh {(3000000 / 120):,.2f}"
                    })
                    
                    recommendations.append({
                        "name": "Healthcare Fund",
                        "description": "Additional healthcare coverage beyond NHIF",
                        "category": "NHIF/NSSF Payments",
                        "target_amount": 300000,  # 300K KES
                        "priority": 4,
                        "timeline_months": 36,
                        "target_amount_display": "KSh 300,000.00",
                        "monthly_contribution": 300000 / 36,
                        "monthly_contribution_display": f"KSh {(300000 / 36):,.2f}"
                    })
            
            # Income-based recommendations
            if income is not None:
                # Vacation/travel fund
                recommendations.append({
                    "name": "Travel/Vacation Fund",
                    "description": "Save for domestic or international travel",
                    "category": "Travel",
                    "target_amount": income * 3,  # 3 months income
                    "priority": 2,
                    "timeline_months": 24,
                    "target_amount_display": f"KSh {(income * 3):,.2f}",
                    "monthly_contribution": (income * 3) / 24,
                    "monthly_contribution_display": f"KSh {((income * 3) / 24):,.2f}"
                })
                
                # Investment group (Chama)
                recommendations.append({
                    "name": "Investment Group (Chama) Contribution",
                    "description": "Regular contributions to a Kenyan investment group",
                    "category": "Chama Investment",
                    "target_amount": income * 12,  # 1 year of income
                    "priority": 3,
                    "timeline_months": 36,
                    "target_amount_display": f"KSh {(income * 12):,.2f}",
                    "monthly_contribution": (income * 12) / 36,
                    "monthly_contribution_display": f"KSh {((income * 12) / 36):,.2f}"
                })
            
            return recommendations
                
        except Exception as e:
            logger.error(f"Error generating goal recommendations for user {user_id}: {e}")
            return []
    
    def record_goal_contribution(self, goal_id: str, amount: float, transaction_date: str = None) -> Dict:
        """
        Record a contribution to a specific goal
        
        Args:
            goal_id: Unique identifier for the goal
            amount: Contribution amount in KES
            transaction_date: Date of contribution (YYYY-MM-DD, defaults to today)
                
        Returns:
            Updated goal object with new progress
        """
        try:
            # Set transaction date to today if not provided
            if not transaction_date:
                transaction_date = datetime.now().strftime("%Y-%m-%d")
            
            # Get current goal details
            goal = self.get_goal_details(goal_id)
            if "error" in goal:
                return goal
            
            # Calculate new current amount
            current_amount = goal.get("current_amount", 0)
            new_amount = current_amount + amount
            
            # Create transaction record
            transaction_data = {
                "goal_id": goal_id,
                "amount": amount,
                "amount_display": f"KSh {amount:,.2f}",
                "transaction_date": transaction_date,
                "transaction_type": "contribution",
                "description": "Goal contribution"
            }
            
            # Record transaction in API
            transaction_response = self._api_request("post", "financial-goals/transactions", json=transaction_data)
            
            # Update goal progress
            return self.update_goal_progress(goal_id, new_amount)
                
        except Exception as e:
            logger.error(f"Error recording goal contribution for {goal_id}: {e}")
            return {"error": str(e)}
    
    def get_contribution_suggestions(self, user_id: str, available_amount: float) -> Dict:
        """
        Suggest how to distribute an available amount across goals
        
        Args:
            user_id: Unique identifier for the user
            available_amount: Available amount to distribute in KES
                
        Returns:
            Suggested allocation across goals
        """
        try:
            # Get prioritized goals
            prioritized_goals = self.prioritize_goals(user_id)
            if not prioritized_goals:
                return {"message": "No active goals found", "allocations": []}
            
            # Distribute amount based on priority scores
            total_priority = sum(goal.get("priority_score", 0) for goal in prioritized_goals)
            allocations = []
            
            for goal in prioritized_goals:
                # Calculate weight based on priority score
                weight = goal.get("priority_score", 0) / total_priority if total_priority > 0 else 0
                
                # Calculate allocation
                allocation = available_amount * weight
                
                # Calculate progress impact
                current_progress = (goal.get("current_amount", 0) / goal.get("target_amount", 1)) * 100
                new_progress = ((goal.get("current_amount", 0) + allocation) / goal.get("target_amount", 1)) * 100
                progress_impact = new_progress - current_progress
                
                allocations.append({
                    "goal_id": goal.get("id"),
                    "goal_name": goal.get("name"),
                    "allocation": round(allocation, 2),
                    "allocation_display": f"KSh {allocation:,.2f}",
                    "weight_percentage": round(weight * 100, 2),
                    "current_progress": round(current_progress, 2),
                    "new_progress": round(new_progress, 2),
                    "progress_impact": round(progress_impact, 2)
                })
            
            return {
                "available_amount": available_amount,
                "available_amount_display": f"KSh {available_amount:,.2f}",
                "allocations": allocations
            }
                
        except Exception as e:
            logger.error(f"Error calculating contribution suggestions for user {user_id}: {e}")
            return {"error": str(e)}
        
        return {"error": "Maximum retries reached"}
    
    def get_user_goals(self, user_id: str) -> List[Dict]:
        """
        Retrieve all financial goals for a specific user
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            List of goal objects
        """
        response = self._api_request("get", f"financial-goals/user/{user_id}")
        return response if isinstance(response, list) else []
    
    def create_goal(self, user_id: str, goal_data: Dict) -> Dict:
        """
        Create a new financial goal for a user
        
        Args:
            user_id: Unique identifier for the user
            goal_data: Dictionary containing goal details
                - name: Goal name
                - target_amount: Target amount in KES
                - current_amount: Current saved amount in KES
                - deadline: Target date (YYYY-MM-DD)
                - category: Goal category (e.g., Education, Housing, Retirement)
                - priority: Goal priority (1-5, with 5 being highest)
                - description: Additional details (optional)
                
        Returns:
            Created goal object or error details
        """
        # Add user_id to goal data
        goal_data["user_id"] = user_id
        
        # Add creation timestamp
        goal_data["created_at"] = datetime.now().isoformat()
        
        # Convert KES amounts to use "KSh" prefix if not already present
        if "target_amount" in goal_data and isinstance(goal_data["target_amount"], (int, float)):
            if not str(goal_data["target_amount"]).startswith("KSh"):
                goal_data["target_amount_display"] = f"KSh {goal_data['target_amount']:,.2f}"
        
        if "current_amount" in goal_data and isinstance(goal_data["current_amount"], (int, float)):
            if not str(goal_data["current_amount"]).startswith("KSh"):
                goal_data["current_amount_display"] = f"KSh {goal_data['current_amount']:,.2f}"
        
        # If category not in Kenyan categories, set to "Other"
        if "category" in goal_data and goal_data["category"] not in self.kenyan_goal_categories:
            goal_data["category"] = "Other"
        
        return self._api_request("post", "financial-goals", json=goal_data)
    
    def update_goal(self, goal_id: str, update_data: Dict) -> Dict:
        """
        Update an existing financial goal
        
        Args:
            goal_id: Unique identifier for the goal
            update_data: Dictionary containing fields to update
                
        Returns:
            Updated goal object or error details
        """
        # Add update timestamp
        update_data["updated_at"] = datetime.now().isoformat()
        
        # Format KES amounts with KSh prefix for display
        if "target_amount" in update_data and isinstance(update_data["target_amount"], (int, float)):
            update_data["target_amount_display"] = f"KSh {update_data['target_amount']:,.2f}"
        
        if "current_amount" in update_data and isinstance(update_data["current_amount"], (int, float)):
            update_data["current_amount_display"] = f"KSh {update_data['current_amount']:,.2f}"
        
        return self._api_request("put", f"financial-goals/{goal_id}", json=update_data)
    
    def delete_goal(self, goal_id: str) -> Dict:
        """
        Delete a financial goal
        
        Args:
            goal_id: Unique identifier for the goal
                
        Returns:
            Success message or error details
        """
        return self._api_request("delete", f"financial-goals/{goal_id}")
    
    def get_goal_details(self, goal_id: str) -> Dict:
        """
        Get details for a specific goal
        
        Args:
            goal_id: Unique identifier for the goal
                
        Returns:
            Goal details or error information
        """
        return self._api_request("get", f"financial-goals/{goal_id}")
    
    def update_goal_progress(self, goal_id: str, new_amount: float) -> Dict:
        """
        Update the current amount saved for a goal
        
        Args:
            goal_id: Unique identifier for the goal
            new_amount: New current amount saved (in KES)
                
        Returns:
            Updated goal details including progress percentage
        """
        try:
            # Get current goal details
            goal = self.get_goal_details(goal_id)
            if "error" in goal:
                return goal
            
            # Calculate new progress
            target_amount = goal.get("target_amount", 0)
            progress_percent = (new_amount / target_amount * 100) if target_amount > 0 else 0
            
            # Update goal
            update_data = {
                "current_amount": new_amount,
                "current_amount_display": f"KSh {new_amount:,.2f}",
                "progress_percent": round(progress_percent, 2),
                "updated_at": datetime.now().isoformat()
            }
            
            return self.update_goal(goal_id, update_data)
        except Exception as e:
            logger.error(f"Error updating goal progress for {goal_id}: {e}")
            return {"error": str(e)}
    
    def analyze_goal_feasibility(self, user_id: str, goal_id: str, monthly_contribution: float = None) -> Dict:
        """
        Analyze if a goal is feasible based on timeline and savings rate
        
        Args:
            user_id: Unique identifier for the user
            goal_id: Unique identifier for the goal
            monthly_contribution: Monthly amount to save (optional)
                
        Returns:
            Feasibility analysis including:
            - is_feasible: Whether the goal is feasible
            - months_needed: Months needed to reach the goal
            - target_monthly_contribution: Suggested monthly contribution
            - completion_date: Estimated completion date
        """
        try:
            # Get goal details
            goal = self.get_goal_details(goal_id)
            if "error" in goal:
                return goal
            
            # Extract necessary values
            target_amount = goal.get("target_amount", 0)
            current_amount = goal.get("current_amount", 0)
            deadline_str = goal.get("deadline")
            
            # Calculate remaining amount
            remaining_amount = target_amount - current_amount
            
            if remaining_amount <= 0:
                return {
                    "is_feasible": True,
                    "months_needed": 0,
                    "target_monthly_contribution": 0,
                    "target_monthly_contribution_display": "KSh 0.00",
                    "completion_date": datetime.now().strftime("%Y-%m-%d"),
                    "message": "Goal has already been reached!",
                    "remaining_amount": 0,
                    "remaining_amount_display": "KSh 0.00"
                }
            
            # Calculate time to deadline if it exists
            months_to_deadline = None
            if deadline_str:
                deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00") if "Z" in deadline_str else deadline_str)
                today = datetime.now()
                days_to_deadline = (deadline - today).days
                months_to_deadline = max(days_to_deadline / 30, 0)
            
            # Calculate feasibility
            if monthly_contribution:
                months_needed = remaining_amount / monthly_contribution
                completion_date = datetime.now() + timedelta(days=months_needed * 30)
                is_feasible = months_to_deadline is None or months_needed <= months_to_deadline
                target_monthly_contribution = monthly_contribution
            elif months_to_deadline:
                # Calculate required monthly contribution to meet deadline
                target_monthly_contribution = remaining_amount / months_to_deadline
                months_needed = months_to_deadline
                completion_date = datetime.now() + timedelta(days=months_needed * 30)
                is_feasible = True
            else:
                # No deadline and no monthly contribution specified
                # Assume 10% of target amount as monthly contribution
                target_monthly_contribution = target_amount * 0.1
                months_needed = remaining_amount / target_monthly_contribution
                completion_date = datetime.now() + timedelta(days=months_needed * 30)
                is_feasible = True
                
            return {
                "is_feasible": is_feasible,
                "months_needed": round(months_needed, 1),
                "target_monthly_contribution": round(target_monthly_contribution, 2),
                "target_monthly_contribution_display": f"KSh {target_monthly_contribution:,.2f}",
                "completion_date": completion_date.strftime("%Y-%m-%d"),
                "remaining_amount": remaining_amount,
                "remaining_amount_display": f"KSh {remaining_amount:,.2f}",
                "message": self._generate_feasibility_message(is_feasible, months_needed, target_monthly_contribution)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing goal feasibility for {goal_id}: {e}")
            return {"error": str(e)}
    
    def _generate_feasibility_message(self, is_feasible: bool, months_needed: float, monthly_contribution: float) -> str:
        """Generate a user-friendly message about goal feasibility"""
        if is_feasible:
            if months_needed <= 3:
                return f"This goal is easily achievable! With a monthly contribution of KSh {monthly_contribution:,.2f}, you can reach it in just {months_needed:.1f} months."
            elif months_needed <= 12:
                return f"This goal is achievable within a year. Save KSh {monthly_contribution:,.2f} monthly to reach it in {months_needed:.1f} months."
            elif months_needed <= 36:
                years = months_needed / 12
                return f"This is a medium-term goal requiring KSh {monthly_contribution:,.2f} monthly for {years:.1f} years ({months_needed:.1f} months)."
            else:
                years = months_needed / 12
                return f"This is a long-term goal requiring KSh {monthly_contribution:,.2f} monthly for {years:.1f} years. Consider increasing your contributions to reach it faster."
        else:
            return f"This goal may not be achievable by your deadline. Consider increasing your monthly contribution beyond KSh {monthly_contribution:,.2f} or extending your deadline."
    
    def get_goal_suggestions(self, user_id: str, category: str = None) -> List[Dict]:
        """
        Get suggested goals based on user profile and category
        
        Args:
            user_id: Unique identifier for the user
            category: Optional category for goal suggestions
                
        Returns:
            List of suggested goals with recommended parameters
        """
        params = {"category": category} if category else {}
        response = self._api_request("get", f"financial-goals/suggestions/{user_id}", params=params)
        return response if isinstance(response, list) else []
    
    def get_goal_categories(self) -> List[str]:
        """
        Get all available goal categories for Kenyan users
        
        Returns:
            List of goal categories
        """
        # Try to get from API first
        response = self._api_request("get", "financial-goals/categories")
        
        # If successful and it's a list, return it
        if isinstance(response, list) and response:
            return response
        
        # Otherwise return our Kenyan categories
        return self.kenyan_goal_categories
    
    def get_goal_statistics(self, user_id: str) -> Dict:
        """
        Get statistics about user's financial goals
        
        Args:
            user_id: Unique identifier for the user
                
        Returns:
            Statistics about goals including:
            - total_goals: Total number of goals
            - total_target_amount: Sum of all goal target amounts
            - total_current_amount: Sum of current saved amounts
            - overall_progress: Overall progress across all goals
            - completed_goals: Number of completed goals
        """
        # Try to get from API first
        response = self._api_request("get", f"financial-goals/statistics/{user_id}")
        
        # Check if it's a valid response with no error
        if isinstance(response, dict) and "error" not in response:
            return response
        
        # Calculate statistics manually as fallback
        try:
            goals = self.get_user_goals(user_id)
            if not goals:
                return {
                    "total_goals": 0,
                    "total_target_amount": 0,
                    "total_current_amount": 0,
                    "overall_progress": 0,
                    "completed_goals": 0,
                    "in_progress_goals": 0,
                    "total_target_amount_display": "KSh 0.00",
                    "total_current_amount_display": "KSh 0.00"
                }
            
            total_target_amount = sum(goal.get("target_amount", 0) for goal in goals)
            total_current_amount = sum(goal.get("current_amount", 0) for goal in goals)
            overall_progress = (total_current_amount / total_target_amount * 100) if total_target_amount > 0 else 0
            completed_goals = sum(1 for goal in goals if goal.get("current_amount", 0) >= goal.get("target_amount", 0))
            
            return {
                "total_goals": len(goals),
                "total_target_amount": total_target_amount,
                "total_current_amount": total_current_amount,
                "overall_progress": round(overall_progress, 2),
                "completed_goals": completed_goals,
                "in_progress_goals": len(goals) - completed_goals,
                "total_target_amount_display": f"KSh {total_target_amount:,.2f}",
                "total_current_amount_display": f"KSh {total_current_amount:,.2f}"
            }
        except Exception as e:
            logger.error(f"Error calculating goal statistics for user {user_id}: {e}")
            return {"error": str(e)}
