import os
import json
import time
import logging
from datetime import datetime, timedelta
import requests
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis for caching (if available)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD', None)
    )
    REDIS_AVAILABLE = True
except Exception:
    logger.warning("Redis not available. Running without cache.")
    REDIS_AVAILABLE = False

class MacroeconomicAPI:
    """
    Class for handling macroeconomic API integrations.
    Provides methods to fetch various economic indicators.
    """
    
    def __init__(self):
        """Initialize the MacroeconomicAPI with API keys and base URLs."""
        # API Keys
        self.rapidapi_key = os.getenv('RAPIDAPI_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')
        self.cbk_api_key = os.getenv('CBK_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_KEY', '08HAWE6C99AGWNEZ')
        
        # Base URLs
        self.cbk_base_url = "https://sandbox.centralbank.go.ke/api/v1"  # Example URL, may need adjustment
        self.exchange_rate_url = "https://exchange-rates7.p.rapidapi.com"
        
        # Cache settings
        self.cache_enabled = os.getenv('ENABLE_CACHE', 'True').lower() == 'true'
        self.cache_ttl = int(os.getenv('CACHE_TTL', 3600))  # Default: 1 hour
        
        # Rate limiting
        self.request_intervals = {}
        self.last_request_time = {}
    
    def _rate_limit(self, api_name, min_interval=1):
        """
        Implement rate limiting to prevent API abuse.
        
        Args:
            api_name (str): Name of the API being called
            min_interval (float): Minimum interval between requests in seconds
            
        Returns:
            None
        """
        current_time = time.time()
        if api_name in self.last_request_time:
            elapsed = current_time - self.last_request_time[api_name]
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                logger.debug(f"Rate limiting {api_name} API. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def _get_from_cache(self, cache_key):
        """
        Retrieve data from cache if available.
        
        Args:
            cache_key (str): Cache key to retrieve data
            
        Returns:
            dict or None: Cached data if available, None otherwise
        """
        if not self.cache_enabled or not REDIS_AVAILABLE:
            return None
        
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Error retrieving from cache: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key, data, ttl=None):
        """
        Save data to cache.
        
        Args:
            cache_key (str): Cache key to store data
            data (dict): Data to cache
            ttl (int, optional): Time-to-live in seconds. If None, use default.
            
        Returns:
            bool: True if successfully cached, False otherwise
        """
        if not self.cache_enabled or not REDIS_AVAILABLE:
            return False
        
        ttl = ttl if ttl is not None else self.cache_ttl
        
        try:
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            logger.warning(f"Error saving to cache: {e}")
            return False
    
    def get_cbk_interest_rates(self, force_refresh=False):
        """
        Fetch Central Bank of Kenya interest rates (Central Bank Rate, etc.).
        
        Args:
            force_refresh (bool): Whether to force refresh cache
            
        Returns:
            dict: Dictionary containing interest rate data
        """
        cache_key = "pesaguru:cbk:interest_rates"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved CBK interest rates from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("cbk_api", 2)
        
        try:
            # For CBK API integration, we would use the actual endpoint
            # headers = {
            #     "Authorization": f"Bearer {self.cbk_api_key}"
            # }
            # response = requests.get(f"{self.cbk_base_url}/interest-rates", headers=headers)
            # response.raise_for_status()
            # data = response.json()
            
            # For now, using simulated data based on current CBK rates
            data = {
                "timestamp": datetime.now().isoformat(),
                "central_bank_rate": 12.75,  # Example CBR as of 2024
                "interbank_rate": 11.85,
                "t_bill_91_day": 15.02,
                "t_bill_182_day": 16.45,
                "t_bill_364_day": 16.89,
                "last_updated": "2024-03-15"
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching CBK interest rates: {e}")
            # Return error response
            return {
                "error": "Failed to fetch CBK interest rates",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_exchange_rates(self, base_currency="KES", target_currencies=None, force_refresh=False):
        """
        Fetch exchange rates for Kenyan Shilling against other currencies.
        
        Args:
            base_currency (str): Base currency, default is KES
            target_currencies (list, optional): List of target currencies to fetch.
                If None, fetch major currencies.
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing exchange rate data
        """
        if target_currencies is None:
            target_currencies = ["USD", "EUR", "GBP", "ZAR", "UGX", "TZS", "RWF"]
        
        # Create a cache key that includes the base and target currencies
        target_key = "-".join(sorted(target_currencies))
        cache_key = f"pesaguru:exchange_rates:{base_currency}:{target_key}"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved exchange rates from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("exchange_rate_api", 1)
        
        try:
            headers = {
                "x-rapidapi-key": self.rapidapi_key,
                "x-rapidapi-host": "exchange-rates7.p.rapidapi.com"
            }
            
            # First, check if we're fetching KES rates
            if base_currency == "KES":
                # If base is KES, we'll need to fetch USD/KES and then calculate others
                response = requests.get(
                    f"{self.exchange_rate_url}/latest",
                    headers=headers,
                    params={"base": "USD"}
                )
                response.raise_for_status()
                usd_data = response.json()
                
                # Check if KES is in the rates
                if "KES" not in usd_data.get("rates", {}):
                    raise ValueError("KES rate not found in response")
                
                # Calculate KES as base
                usd_to_kes = usd_data["rates"]["KES"]
                
                rates = {}
                for currency, rate in usd_data["rates"].items():
                    if currency in target_currencies or currency == "USD":
                        # Convert to KES base
                        rates[currency] = rate / usd_to_kes
            else:
                # For other base currencies, fetch directly
                response = requests.get(
                    f"{self.exchange_rate_url}/latest",
                    headers=headers,
                    params={"base": base_currency}
                )
                response.raise_for_status()
                data = response.json()
                rates = {curr: rate for curr, rate in data["rates"].items() 
                         if curr in target_currencies}
            
            result = {
                "base": base_currency,
                "timestamp": datetime.now().isoformat(),
                "rates": rates
            }
            
            # Cache the data
            self._save_to_cache(cache_key, result)
            
            return result
            
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Error fetching exchange rates: {e}")
            # Return error response
            return {
                "error": "Failed to fetch exchange rates",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_kenya_gdp_data(self, force_refresh=False):
        """
        Fetch Kenya's GDP data and related economic indicators.
        
        Args:
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing GDP data
        """
        cache_key = "pesaguru:kenya:gdp_data"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved Kenya GDP data from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("economic_data_api", 2)
        
        try:
            # For actual implementation, replace with real API call
            # This is a simulated response based on Kenya's economic data
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "country": "Kenya",
                "gdp": {
                    "nominal_gdp_usd_billions": 110.35,  # Example data
                    "real_gdp_growth_percent": 5.6,
                    "gdp_per_capita_usd": 2050.43,
                    "year": 2023,
                },
                "sectors": {
                    "agriculture_percent": 34.1,
                    "industry_percent": 16.3,
                    "services_percent": 49.6
                },
                "last_updated": "2023-12-31",
                "source": "National Bureau of Statistics, Kenya"
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data, ttl=86400)  # 24 hours cache
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Kenya GDP data: {e}")
            # Return error response
            return {
                "error": "Failed to fetch Kenya GDP data",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_kenya_inflation_data(self, months=12, force_refresh=False):
        """
        Fetch Kenya's inflation data for the specified number of months.
        
        Args:
            months (int): Number of months of data to fetch
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing inflation data
        """
        cache_key = f"pesaguru:kenya:inflation_data:{months}"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved Kenya inflation data from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("economic_data_api", 2)
        
        try:
            # For actual implementation, replace with real API call
            # This is a simulated response based on recent Kenya inflation data
            
            # Generate sample monthly data
            current_date = datetime.now()
            monthly_data = []
            
            # Sample inflation rates (would be replaced with actual API data)
            sample_rates = [6.8, 7.1, 6.9, 6.5, 6.2, 5.9, 6.1, 6.3, 6.7, 7.0, 6.6, 6.4]
            
            for i in range(min(months, len(sample_rates))):
                month_date = current_date - timedelta(days=30 * i)
                monthly_data.append({
                    "year": month_date.year,
                    "month": month_date.month,
                    "date": month_date.strftime("%Y-%m"),
                    "inflation_rate_percent": sample_rates[i],
                    "food_inflation_percent": sample_rates[i] + 1.2,  # Food inflation usually higher
                    "energy_inflation_percent": sample_rates[i] + 0.8
                })
            
            # Reverse to get chronological order
            monthly_data.reverse()
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "country": "Kenya",
                "current_inflation_rate_percent": sample_rates[0],
                "current_core_inflation_percent": sample_rates[0] - 0.5,  # Core inflation usually lower
                "monthly_data": monthly_data,
                "last_updated": current_date.strftime("%Y-%m-%d"),
                "source": "Kenya National Bureau of Statistics"
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data, ttl=43200)  # 12 hours cache
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Kenya inflation data: {e}")
            # Return error response
            return {
                "error": "Failed to fetch Kenya inflation data",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_kenya_balance_of_trade(self, years=5, force_refresh=False):
        """
        Fetch Kenya's balance of trade data for specified number of years.
        
        Args:
            years (int): Number of years of data to fetch
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing balance of trade data
        """
        cache_key = f"pesaguru:kenya:balance_of_trade:{years}"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved Kenya balance of trade data from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("economic_data_api", 2)
        
        try:
            # Using information from Table_17__Balance_of_Merchandise_Trade__20192023_.csv
            # This simulates the data we would get from an API
            
            # Sample data based on provided files
            sample_data = [
                {"year": 2019, "exports": 650, "imports": 1700, "trade_balance": -1050},
                {"year": 2020, "exports": 600, "imports": 1500, "trade_balance": -900},
                {"year": 2021, "exports": 740, "imports": 1800, "trade_balance": -1060},
                {"year": 2022, "exports": 830, "imports": 2100, "trade_balance": -1270},
                {"year": 2023, "exports": 880, "imports": 2300, "trade_balance": -1420}
            ]
            
            yearly_data = []
            for i in range(min(years, len(sample_data))):
                yearly_data.append(sample_data[len(sample_data) - 1 - i])
            
            # Reverse to get chronological order
            yearly_data.reverse()
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "country": "Kenya",
                "current_exports_billion_kes": yearly_data[-1]["exports"],
                "current_imports_billion_kes": yearly_data[-1]["imports"],
                "current_trade_balance_billion_kes": yearly_data[-1]["trade_balance"],
                "yearly_data": yearly_data,
                "last_updated": "2023-12-31",
                "source": "Kenya National Bureau of Statistics"
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data, ttl=86400)  # 24 hours cache
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Kenya balance of trade data: {e}")
            # Return error response
            return {
                "error": "Failed to fetch Kenya balance of trade data",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_financial_sector_indicators(self, force_refresh=False):
        """
        Fetch financial sector indicators for Kenya.
        
        Args:
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing financial sector indicators
        """
        cache_key = "pesaguru:kenya:financial_indicators"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved Kenya financial indicators from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("financial_indicators_api", 2)
        
        try:
            # Using information from Table_2__Trends_in_the_Real_Values_of_Selected_Financial_Aggregates
            # This simulates the data we would get from an API
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "country": "Kenya",
                "indicators": {
                    "m3_money_supply_billion_kes": 4500,  # Current value
                    "total_deposits_billion_kes": 4200,
                    "credit_to_private_sector_billion_kes": 3100,
                    "banking_sector_assets_billion_kes": 5500,
                    "non_performing_loans_percent": 13.8,
                    "loan_to_deposit_ratio_percent": 73.8
                },
                "historical_data": [
                    {
                        "year": 2019,
                        "m3_money_supply_billion_kes": 3300,
                        "total_deposits_billion_kes": 3100,
                        "credit_to_private_sector_billion_kes": 2200
                    },
                    {
                        "year": 2020,
                        "m3_money_supply_billion_kes": 3600,
                        "total_deposits_billion_kes": 3400,
                        "credit_to_private_sector_billion_kes": 2400
                    },
                    {
                        "year": 2021,
                        "m3_money_supply_billion_kes": 3900,
                        "total_deposits_billion_kes": 3700,
                        "credit_to_private_sector_billion_kes": 2700
                    },
                    {
                        "year": 2022,
                        "m3_money_supply_billion_kes": 4200,
                        "total_deposits_billion_kes": 3900,
                        "credit_to_private_sector_billion_kes": 2900
                    },
                    {
                        "year": 2023,
                        "m3_money_supply_billion_kes": 4500,
                        "total_deposits_billion_kes": 4200,
                        "credit_to_private_sector_billion_kes": 3100
                    }
                ],
                "last_updated": "2023-12-31",
                "source": "Central Bank of Kenya"
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data, ttl=86400)  # 24 hours cache
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Kenya financial indicators: {e}")
            # Return error response
            return {
                "error": "Failed to fetch Kenya financial indicators",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_economic_forecast(self, country="Kenya", force_refresh=False):
        """
        Fetch economic forecast for Kenya (or another country).
        
        Args:
            country (str): Country to fetch forecast for, default is Kenya
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing economic forecast data
        """
        if country.lower() != "kenya":
            logger.warning("Only Kenya is supported for economic forecasts at this time")
            country = "Kenya"
        
        cache_key = f"pesaguru:economic_forecast:{country.lower()}"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Retrieved {country} economic forecast from cache")
                return cached_data
        
        # Rate limit
        self._rate_limit("economic_forecast_api", 2)
        
        try:
            # For actual implementation, replace with real API call
            # This is a simulated response based on Kenya economic forecasts
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "country": country,
                "forecast_period": "2024-2026",
                "gdp_growth": {
                    "2024": 5.2,  # Projected data
                    "2025": 5.5,
                    "2026": 5.8
                },
                "inflation_forecast": {
                    "2024": 6.1,
                    "2025": 5.5,
                    "2026": 5.0
                },
                "exchange_rate_forecast": {
                    "currency_pair": "USD/KES",
                    "2024": 145.0,
                    "2025": 148.0,
                    "2026": 150.0
                },
                "interest_rate_forecast": {
                    "2024": 12.0,
                    "2025": 11.5,
                    "2026": 10.5
                },
                "downside_risks": [
                    "Global economic slowdown",
                    "Climate change impacts on agriculture",
                    "Political instability in the region"
                ],
                "upside_potentials": [
                    "Growth in technology sector",
                    "Improved regional trade integration",
                    "Infrastructure development"
                ],
                "source": "Economic Research Institutes, IMF, World Bank",
                "last_updated": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Cache the data
            self._save_to_cache(cache_key, data, ttl=86400)  # 24 hours cache
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching {country} economic forecast: {e}")
            # Return error response
            return {
                "error": f"Failed to fetch {country} economic forecast",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_macroeconomic_summary(self, force_refresh=False):
        """
        Provide a comprehensive summary of Kenya's macroeconomic situation.
        Combines multiple data points for a holistic view.
        
        Args:
            force_refresh (bool): Whether to force refresh the cache
            
        Returns:
            dict: Dictionary containing macroeconomic summary
        """
        cache_key = "pesaguru:kenya:macroeconomic_summary"
        
        # Try to get from cache
        if not force_refresh:
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Retrieved Kenya macroeconomic summary from cache")
                return cached_data
        
        try:
            # Fetch individual data points
            gdp_data = self.get_kenya_gdp_data()
            inflation_data = self.get_kenya_inflation_data(months=1)
            interest_rates = self.get_cbk_interest_rates()
            exchange_rates = self.get_exchange_rates(base_currency="KES", target_currencies=["USD", "EUR", "GBP"])
            
            # Create a comprehensive summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "country": "Kenya",
                "gdp": {
                    "nominal_gdp_usd_billions": gdp_data.get("gdp", {}).get("nominal_gdp_usd_billions"),
                    "growth_rate_percent": gdp_data.get("gdp", {}).get("real_gdp_growth_percent")
                },
                "inflation": {
                    "current_rate_percent": inflation_data.get("current_inflation_rate_percent"),
                    "trend": "increasing" if inflation_data.get("monthly_data", []) and 
                             inflation_data["monthly_data"][-1].get("inflation_rate_percent", 0) > 
                             inflation_data["monthly_data"][0].get("inflation_rate_percent", 0) else "decreasing"
                },
                "interest_rates": {
                    "central_bank_rate": interest_rates.get("central_bank_rate"),
                    "t_bill_91_day": interest_rates.get("t_bill_91_day")
                },
                "exchange_rates": {
                    "kes_to_usd": exchange_rates.get("rates", {}).get("USD"),
                    "kes_to_eur": exchange_rates.get("rates", {}).get("EUR"),
                    "kes_to_gbp": exchange_rates.get("rates", {}).get("GBP")
                },
                "economic_outlook": {
                    "short_term": "The Kenyan economy shows resilience with positive GDP growth, but challenges remain including inflation pressures and currency fluctuations.",
                    "medium_term": "Infrastructure development and digital transformation are expected to drive growth in the medium term, but fiscal consolidation and debt management will be key challenges.",
                    "key_sectors_to_watch": ["Agriculture", "Technology", "Manufacturing", "Financial Services"]
                },
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "sources": ["Central Bank of Kenya", "Kenya National Bureau of Statistics", "IMF", "World Bank"]
            }
            
            # Cache the data
            self._save_to_cache(cache_key, summary, ttl=43200)  # 12 hours cache
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating Kenya macroeconomic summary: {e}")
            # Return error response
            return {
                "error": "Failed to generate Kenya macroeconomic summary",
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Main function to test the MacroeconomicAPI."""
    api = MacroeconomicAPI()
    
    # Test CBK interest rates
    print("\nTesting CBK interest rates...")
    interest_rates = api.get_cbk_interest_rates()
    print(json.dumps(interest_rates, indent=2))
    
    # Test exchange rates
    print("\nTesting exchange rates...")
    exchange_rates = api.get_exchange_rates()
    print(json.dumps(exchange_rates, indent=2))
    
    # Test GDP data
    print("\nTesting GDP data...")
    gdp_data = api.get_kenya_gdp_data()
    print(json.dumps(gdp_data, indent=2))
    
    # Test balance of trade
    print("\nTesting balance of trade...")
    trade_data = api.get_kenya_balance_of_trade()
    print(json.dumps(trade_data, indent=2))
    
    # Test macroeconomic summary
    print("\nTesting macroeconomic summary...")
    summary = api.get_macroeconomic_summary()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
