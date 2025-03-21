import os
import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Union, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('inflation_api')

# API keys and endpoints - Should be moved to environment variables in production
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')
TRADINGECONOMICS_API_KEY = os.environ.get('TRADINGECONOMICS_API_KEY', '')
WORLD_BANK_ENDPOINT = "http://api.worldbank.org/v2/country/KE/indicator/FP.CPI.TOTL.ZG?format=json"
CBK_INFLATION_URL = "https://www.centralbank.go.ke/inflation-rates/"
KNBS_BASE_URL = "https://www.knbs.or.ke/api/v1/"

# Cache configuration
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
CACHE_EXPIRY = 86400  # 24 hours in seconds


class InflationAPI:
    """Class to handle inflation data API calls and processing."""
    
    def __init__(self, use_cache: bool = True, cache_expiry: int = CACHE_EXPIRY):
        """
        Initialize the Inflation API integration.
        
        Args:
            use_cache (bool): Whether to cache API responses locally
            cache_expiry (int): Cache expiry time in seconds
        """
        self.use_cache = use_cache
        self.cache_expiry = cache_expiry
        
        # Create cache directory if it doesn't exist
        if use_cache and not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
    
    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """
        Retrieve data from local cache if available and not expired.
        
        Args:
            cache_key (str): The key to identify the cached data
            
        Returns:
            Optional[Dict]: Cached data if available and not expired, None otherwise
        """
        if not self.use_cache:
            return None
            
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
            
        # Check if cache has expired
        file_modified_time = os.path.getmtime(cache_file)
        if time.time() - file_modified_time > self.cache_expiry:
            logger.info(f"Cache for {cache_key} has expired")
            return None
            
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Retrieved {cache_key} data from cache")
                return data
        except Exception as e:
            logger.error(f"Error reading cache file {cache_file}: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, data: Dict) -> bool:
        """
        Save data to local cache.
        
        Args:
            cache_key (str): The key to identify the cached data
            data (Dict): The data to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.use_cache:
            return False
            
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
                logger.info(f"Saved {cache_key} data to cache")
                return True
        except Exception as e:
            logger.error(f"Error writing to cache file {cache_file}: {e}")
            return False
    
    def get_kenya_inflation_trading_economics(self) -> Dict:
        """
        Fetch Kenya inflation data from Trading Economics API.
        
        Returns:
            Dict: Inflation data with historical rates and metadata
        """
        cache_key = "kenya_inflation_tradingeconomics"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        url = "https://trading-economics.p.rapidapi.com/historical"
        
        querystring = {
            "country": "kenya",
            "indicator": "inflation-rate",
            "start_date": (datetime.now() - timedelta(days=365*5)).strftime("%Y-%m-%d"),  # 5 years ago
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "format": "json"
        }
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "trading-economics.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and format the data
            result = {
                "source": "Trading Economics",
                "country": "Kenya",
                "indicator": "Inflation Rate",
                "unit": "% (YoY)",
                "last_updated": datetime.now().isoformat(),
                "historical_data": data
            }
            
            # Add current inflation rate
            if data and len(data) > 0:
                result["current_rate"] = data[0].get("value", None)
                
            # Calculate average rates
            if data and len(data) > 0:
                values = [item.get("value", 0) for item in data if "value" in item]
                if values:
                    result["average_rate_1yr"] = sum(values[:12]) / min(12, len(values))
                    result["average_rate_5yr"] = sum(values) / len(values)
            
            self._save_to_cache(cache_key, result)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Trading Economics inflation data: {e}")
            return {"error": str(e), "source": "Trading Economics"}
    
    def get_kenya_inflation_world_bank(self) -> Dict:
        """
        Fetch Kenya inflation data from World Bank API.
        
        Returns:
            Dict: Inflation data with historical rates and metadata
        """
        cache_key = "kenya_inflation_worldbank"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            response = requests.get(WORLD_BANK_ENDPOINT)
            response.raise_for_status()
            
            data = response.json()
            
            # World Bank returns data in a specific format, process it
            if len(data) >= 2 and isinstance(data[1], list):
                inflation_data = data[1]
                
                # Format the data
                historical_data = []
                for item in inflation_data:
                    if "value" in item and item["value"] is not None:
                        historical_data.append({
                            "year": item.get("date"),
                            "value": float(item.get("value", 0)),
                            "unit": "% (YoY)"
                        })
                
                # Sort by year
                historical_data.sort(key=lambda x: x["year"], reverse=True)
                
                result = {
                    "source": "World Bank",
                    "country": "Kenya",
                    "indicator": "Inflation, consumer prices (annual %)",
                    "unit": "% (YoY)",
                    "last_updated": datetime.now().isoformat(),
                    "historical_data": historical_data
                }
                
                # Add current inflation rate (most recent data)
                if historical_data and len(historical_data) > 0:
                    result["current_rate"] = historical_data[0].get("value", None)
                    
                # Calculate average rates
                if historical_data and len(historical_data) > 0:
                    values = [item.get("value", 0) for item in historical_data]
                    if values:
                        result["average_rate_5yr"] = sum(values[:5]) / min(5, len(values))
                        result["average_rate_10yr"] = sum(values[:10]) / min(10, len(values))
                
                self._save_to_cache(cache_key, result)
                return result
            else:
                logger.error(f"Unexpected response format from World Bank API: {data}")
                return {"error": "Unexpected response format", "source": "World Bank"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching World Bank inflation data: {e}")
            return {"error": str(e), "source": "World Bank"}
    
    def get_kenya_inflation_cbk(self) -> Dict:
        """
        Scrape Kenya inflation data from Central Bank of Kenya website.
        Note: Web scraping should be used as a fallback when APIs are not available.
        
        Returns:
            Dict: Inflation data with historical rates and metadata
        """
        cache_key = "kenya_inflation_cbk"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Note: In a real implementation, we would use a proper web scraping 
            # solution with BeautifulSoup or similar.
            # For now, we'll use the CBK API if available
            
            # This is a placeholder for when CBK provides an API
            url = "https://www.centralbank.go.ke/api/inflation"
            headers = {
                "User-Agent": "PesaGuru Financial Advisor Chatbot/1.0"
            }
            
            response = requests.get(url, headers=headers)
            
            # If CBK doesn't offer an API, this would fail and we'd need to implement scraping
            if response.status_code == 404:
                # Placeholder for scraped data
                # In production, implement proper scraping with BeautifulSoup
                return {
                    "source": "Central Bank of Kenya",
                    "country": "Kenya",
                    "indicator": "Inflation Rate",
                    "unit": "% (YoY)",
                    "last_updated": datetime.now().isoformat(),
                    "note": "Web scraping implementation required",
                    "current_rate": None,
                    "historical_data": []
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Format the data
            result = {
                "source": "Central Bank of Kenya",
                "country": "Kenya",
                "indicator": "Inflation Rate",
                "unit": "% (YoY)",
                "last_updated": datetime.now().isoformat(),
                "historical_data": data.get("historical_data", [])
            }
            
            # Add current inflation rate
            result["current_rate"] = data.get("current_rate")
            
            self._save_to_cache(cache_key, result)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching CBK inflation data: {e}")
            return {
                "error": str(e),
                "source": "Central Bank of Kenya",
                "note": "If this is a 404, CBK may not provide an API and scraping may be required"
            }
    
    def get_kenya_inflation_knbs(self) -> Dict:
        """
        Fetch Kenya inflation data from Kenya National Bureau of Statistics API.
        
        Returns:
            Dict: Inflation data with historical rates and metadata
        """
        cache_key = "kenya_inflation_knbs"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # This is a placeholder for when KNBS provides an API
        # Currently, KNBS may not offer a public API, and data might
        # need to be manually collected from their website publications
        
        try:
            # Placeholder URL - this would need to be updated with the real endpoint
            url = f"{KNBS_BASE_URL}economic-indicators/inflation"
            headers = {
                "User-Agent": "PesaGuru Financial Advisor Chatbot/1.0"
            }
            
            response = requests.get(url, headers=headers)
            
            # If KNBS doesn't offer an API, this would fail
            if response.status_code == 404:
                # Placeholder for manually collected data
                # In production, would need to be regularly updated or scraped
                return {
                    "source": "Kenya National Bureau of Statistics",
                    "country": "Kenya",
                    "indicator": "Inflation Rate",
                    "unit": "% (YoY)",
                    "last_updated": datetime.now().isoformat(),
                    "note": "API not available, manual data required",
                    "current_rate": None,
                    "historical_data": []
                }
            
            response.raise_for_status()
            data = response.json()
            
            # Format the data
            result = {
                "source": "Kenya National Bureau of Statistics",
                "country": "Kenya",
                "indicator": "Inflation Rate",
                "unit": "% (YoY)",
                "last_updated": datetime.now().isoformat(),
                "historical_data": data.get("data", [])
            }
            
            # Add current inflation rate
            if "current_rate" in data:
                result["current_rate"] = data["current_rate"]
            
            self._save_to_cache(cache_key, result)
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching KNBS inflation data: {e}")
            return {
                "error": str(e),
                "source": "Kenya National Bureau of Statistics",
                "note": "If this is a 404, KNBS may not provide an API and manual data collection may be required"
            }
    
    def get_inflation_with_fallback(self) -> Dict:
        """
        Fetch Kenya inflation data using multiple sources with fallback.
        
        The function tries different data sources in order of reliability
        and returns the first successful result.
        
        Returns:
            Dict: Inflation data from the first successful source
        """
        # Try Trading Economics API first
        data = self.get_kenya_inflation_trading_economics()
        if "error" not in data and data.get("historical_data"):
            return data
        
        # Try World Bank API as fallback
        data = self.get_kenya_inflation_world_bank()
        if "error" not in data and data.get("historical_data"):
            return data
        
        # Try Central Bank of Kenya as fallback
        data = self.get_kenya_inflation_cbk()
        if "error" not in data and data.get("historical_data"):
            return data
        
        # Try KNBS as last resort
        data = self.get_kenya_inflation_knbs()
        if "error" not in data and data.get("historical_data"):
            return data
        
        # If all sources fail, return a consolidated error
        return {
            "error": "All inflation data sources failed",
            "sources_tried": ["Trading Economics", "World Bank", "Central Bank of Kenya", "KNBS"],
            "timestamp": datetime.now().isoformat()
        }
    
    def calculate_inflation_impact(
        self, 
        amount: float, 
        years: int, 
        inflation_rate: Optional[float] = None
    ) -> Dict:
        """
        Calculate the impact of inflation on a given amount over time.
        
        Args:
            amount (float): The current amount in KES
            years (int): Number of years to forecast
            inflation_rate (Optional[float]): Custom inflation rate to use.
                                             If None, the current Kenya rate is used.
        
        Returns:
            Dict: Inflation impact calculations and forecasts
        """
        # If inflation_rate is not provided, get the current rate from our data
        if inflation_rate is None:
            data = self.get_inflation_with_fallback()
            if "error" in data or not data.get("current_rate"):
                # Use a reasonable default if we couldn't get actual data
                inflation_rate = 7.5  # Approximate historical average for Kenya
            else:
                inflation_rate = data["current_rate"]
        
        # Calculate future value with inflation
        future_values = []
        real_values = []
        
        current_amount = amount
        for year in range(1, years + 1):
            # Calculate nominal value (with inflation)
            inflation_factor = (1 + (inflation_rate / 100)) ** year
            nominal_value = amount * inflation_factor
            
            # Calculate real value (purchasing power)
            real_value = amount / inflation_factor
            
            future_values.append({
                "year": year,
                "nominal_value": round(nominal_value, 2),
                "inflation_factor": round(inflation_factor, 4)
            })
            
            real_values.append({
                "year": year,
                "real_value": round(real_value, 2),
                "purchasing_power_loss": round(100 - (real_value / amount * 100), 2)
            })
        
        return {
            "initial_amount": amount,
            "years": years,
            "inflation_rate_used": inflation_rate,
            "future_values": future_values,
            "real_values": real_values,
            "final_nominal_value": future_values[-1]["nominal_value"] if future_values else amount,
            "final_real_value": real_values[-1]["real_value"] if real_values else amount,
            "total_purchasing_power_loss_percent": round(100 - (real_values[-1]["real_value"] / amount * 100), 2) if real_values else 0
        }
    
    def get_sector_specific_inflation(self) -> Dict:
        """
        Get sector-specific inflation rates for Kenya.
        
        Returns:
            Dict: Inflation rates by economic sector
        """
        cache_key = "kenya_sector_inflation"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # In a real implementation, this would fetch data from an API
        # For now, we'll return sample data based on typical values
        # These should be updated regularly from official sources
        
        sample_data = {
            "source": "Sample Data (Replace with actual API data)",
            "country": "Kenya",
            "last_updated": datetime.now().isoformat(),
            "overall_inflation": 7.5,
            "sectors": {
                "food_and_non_alcoholic_beverages": 9.2,
                "housing_water_electricity_gas": 6.8,
                "transport": 11.3,
                "education": 4.1,
                "health": 5.6,
                "clothing_and_footwear": 4.8,
                "communication": 2.1,
                "recreation_and_culture": 3.9,
                "restaurants_and_hotels": 7.2,
                "miscellaneous_goods_and_services": 6.4
            }
        }
        
        self._save_to_cache(cache_key, sample_data)
        return sample_data
    
    def get_comparative_inflation(self, countries: List[str] = None) -> Dict:
        """
        Get comparative inflation rates across countries.
        
        Args:
            countries (List[str]): List of country codes to compare. 
                                  If None, compares Kenya with regional peers.
        
        Returns:
            Dict: Comparative inflation rates
        """
        if countries is None:
            # Default to Kenya and regional peers
            countries = ["KE", "TZ", "UG", "RW", "ET", "ZA"]
        
        cache_key = f"comparative_inflation_{'_'.join(countries)}"
        cached_data = self._get_cached_data(cache_key)
        
        if cached_data:
            return cached_data
        
        # This would normally fetch data from the World Bank API for multiple countries
        # For now, we'll return sample data
        
        sample_data = {
            "source": "Sample Data (Replace with World Bank API data)",
            "last_updated": datetime.now().isoformat(),
            "countries": {
                "KE": {"name": "Kenya", "inflation_rate": 7.5},
                "TZ": {"name": "Tanzania", "inflation_rate": 4.2},
                "UG": {"name": "Uganda", "inflation_rate": 6.8},
                "RW": {"name": "Rwanda", "inflation_rate": 3.9},
                "ET": {"name": "Ethiopia", "inflation_rate": 13.1},
                "ZA": {"name": "South Africa", "inflation_rate": 5.4}
            }
        }
        
        self._save_to_cache(cache_key, sample_data)
        return sample_data


def get_inflation_rate() -> float:
    """
    Get the current inflation rate for Kenya.
    
    Returns:
        float: Current inflation rate (percentage)
    """
    api = InflationAPI()
    data = api.get_inflation_with_fallback()
    
    if "error" in data or not data.get("current_rate"):
        # Return a reasonable default if we couldn't get actual data
        logger.warning("Could not retrieve current inflation rate, using default value")
        return 7.5  # Approximate historical average for Kenya
    
    return data["current_rate"]


def get_inflation_forecast(years: int = 5) -> Dict:
    """
    Get inflation forecast for the specified number of years.
    
    Args:
        years (int): Number of years to forecast
    
    Returns:
        Dict: Inflation forecast data
    """
    api = InflationAPI()
    data = api.get_inflation_with_fallback()
    
    if "error" in data:
        # Return a simple forecast based on historical average
        current_rate = 7.5  # Approximate historical average for Kenya
    else:
        current_rate = data.get("current_rate", 7.5)
    
    # Simple forecast model - in production, this would be more sophisticated
    forecast = []
    for year in range(1, years + 1):
        # Simplistic model that assumes reversion to long-term mean of ~6%
        forecasted_rate = current_rate * (0.8 ** year) + 6.0 * (1 - 0.8 ** year)
        forecast.append({
            "year": datetime.now().year + year,
            "forecasted_rate": round(forecasted_rate, 2)
        })
    
    return {
        "base_inflation_rate": current_rate,
        "forecast_years": years,
        "forecast": forecast,
        "average_forecasted_rate": round(sum(item["forecasted_rate"] for item in forecast) / len(forecast), 2),
        "note": "This is a simplified forecast. Actual inflation depends on many economic factors."
    }


def calculate_inflation_adjusted_returns(
    investment_amount: float,
    expected_return_rate: float,
    years: int,
    inflation_rate: Optional[float] = None
) -> Dict:
    """
    Calculate inflation-adjusted investment returns.
    
    Args:
        investment_amount (float): Initial investment amount in KES
        expected_return_rate (float): Expected annual return rate (percentage)
        years (int): Investment horizon in years
        inflation_rate (Optional[float]): Custom inflation rate to use.
                                         If None, the current Kenya rate is used.
    
    Returns:
        Dict: Investment calculations with inflation adjustment
    """
    api = InflationAPI()
    
    # If inflation_rate is not provided, get the current rate
    if inflation_rate is None:
        inflation_rate = get_inflation_rate()
    
    # Calculate nominal future value
    nominal_future_value = investment_amount * ((1 + (expected_return_rate / 100)) ** years)
    
    # Calculate real future value (inflation-adjusted)
    real_future_value = nominal_future_value / ((1 + (inflation_rate / 100)) ** years)
    
    # Calculate real rate of return
    real_return_rate = (((1 + (expected_return_rate / 100)) / (1 + (inflation_rate / 100))) - 1) * 100
    
    # Generate yearly breakdown
    yearly_breakdown = []
    for year in range(1, years + 1):
        nominal_value = investment_amount * ((1 + (expected_return_rate / 100)) ** year)
        real_value = nominal_value / ((1 + (inflation_rate / 100)) ** year)
        
        yearly_breakdown.append({
            "year": year,
            "nominal_value": round(nominal_value, 2),
            "real_value": round(real_value, 2),
            "inflation_impact": round(nominal_value - real_value, 2)
        })
    
    return {
        "investment_amount": investment_amount,
        "expected_return_rate": expected_return_rate,
        "inflation_rate_used": inflation_rate,
        "years": years,
        "nominal_future_value": round(nominal_future_value, 2),
        "real_future_value": round(real_future_value, 2),
        "real_return_rate": round(real_return_rate, 2),
        "inflation_impact": round(nominal_future_value - real_future_value, 2),
        "yearly_breakdown": yearly_breakdown
    }


if __name__ == "__main__":
    # Example usage
    api = InflationAPI()
    
    print("Getting Kenya inflation data...")
    data = api.get_inflation_with_fallback()
    print(f"Current inflation rate: {data.get('current_rate')}%")
    
    print("\nCalculating inflation impact on 100,000 KES over 10 years...")
    impact = api.calculate_inflation_impact(100000, 10)
    print(f"After 10 years, 100,000 KES will be worth approximately: {impact['final_nominal_value']} KES nominally")
    print(f"Real purchasing power will be: {impact['final_real_value']} KES")
    print(f"Total purchasing power loss: {impact['total_purchasing_power_loss_percent']}%")
    
    print("\nCalculating inflation-adjusted investment returns...")
    returns = calculate_inflation_adjusted_returns(100000, 12, 10)
    print(f"Nominal future value: {returns['nominal_future_value']} KES")
    print(f"Real future value: {returns['real_future_value']} KES")
    print(f"Real rate of return: {returns['real_return_rate']}%")
