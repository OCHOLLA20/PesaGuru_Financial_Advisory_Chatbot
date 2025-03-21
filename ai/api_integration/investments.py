import os
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from functools import lru_cache
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('investment_api')

# Load environment variables
load_dotenv()

# API Keys from environment variables
NSE_API_KEY = os.getenv('NSE_API_KEY')
YAHOO_FINANCE_API_KEY = os.getenv('YAHOO_FINANCE_API_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '08HAWE6C99AGWNEZ')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581')

# Redis configuration for caching
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        password=os.getenv('REDIS_PASSWORD', None),
        decode_responses=True
    )
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info("Redis connection established successfully")
except Exception as e:
    REDIS_AVAILABLE = False
    logger.warning(f"Redis connection failed: {e}. Will use in-memory caching.")

# Constants
NSE_SECTORS = [
    "AGRICULTURAL", "AUTOMOBILES & ACCESSORIES", "BANKING", 
    "COMMERCIAL & SERVICES", "CONSTRUCTION & ALLIED", "ENERGY & PETROLEUM",
    "INSURANCE", "INVESTMENT", "INVESTMENT SERVICES", "MANUFACTURING & ALLIED",
    "TELECOMMUNICATION & TECHNOLOGY", "REAL ESTATE INVESTMENT TRUST"
]

class InvestmentAPI:
    """
    Class for handling investment-related API calls
    """
    def __init__(self):
        """Initialize the Investment API handler"""
        self.nse_api_host = "nairobi-stock-exchange-nse.p.rapidapi.com"
        self.yahoo_finance_api_host = "yahoo-finance166.p.rapidapi.com"
        self.cache_expiry = {
            'stock_price': 300,  # 5 minutes for stock prices
            'market_summary': 1800,  # 30 minutes for market summary
            'stock_news': 3600,  # 1 hour for news
            'sector_performance': 7200,  # 2 hours for sector performance
            'historical_data': 86400,  # 24 hours for historical data
        }

    def _cache_get(self, key):
        """
        Get data from cache
        
        Args:
            key (str): Cache key
            
        Returns:
            dict or None: Cached data or None if not found
        """
        if not REDIS_AVAILABLE:
            return None
            
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting data from cache: {e}")
            return None

    def _cache_set(self, key, data, expiry=300):
        """
        Store data in cache
        
        Args:
            key (str): Cache key
            data (dict): Data to cache
            expiry (int): Cache expiry in seconds (default: 5 minutes)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not REDIS_AVAILABLE:
            return False
            
        try:
            redis_client.setex(key, expiry, json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Error setting data in cache: {e}")
            return False

    def get_stock_price(self, symbol):
        """
        Get current stock price for a given symbol
        
        Args:
            symbol (str): Stock symbol (e.g., "SCOM" for Safaricom)
            
        Returns:
            dict: Stock price data
        """
        cache_key = f"stock_price:{symbol}"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol} stock price")
            return cached_data
            
        logger.info(f"Fetching stock price for {symbol}")
        
        try:
            url = f"https://{self.nse_api_host}/stocks/{symbol}"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": self.nse_api_host
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Cache the data
                self._cache_set(cache_key, data, self.cache_expiry['stock_price'])
                return data
            else:
                logger.error(f"Failed to fetch stock price for {symbol}: {response.status_code} - {response.text}")
                # Try alternative source if primary source fails
                return self._get_stock_price_alternative(symbol)
                
        except Exception as e:
            logger.error(f"Error fetching stock price for {symbol}: {e}")
            return self._get_stock_price_alternative(symbol)

    def _get_stock_price_alternative(self, symbol):
        """
        Alternative method to get stock price using Yahoo Finance API
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            dict: Stock price data
        """
        try:
            # For NSE stocks, we need to append .NR to the symbol for Yahoo Finance
            yahoo_symbol = f"{symbol}.NR"
            url = f"https://{self.yahoo_finance_api_host}/api/quotes/{yahoo_symbol}"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": self.yahoo_finance_api_host
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Transform Yahoo Finance data to match our format
                transformed_data = {
                    "symbol": symbol,
                    "name": data.get("longName", ""),
                    "price": data.get("regularMarketPrice", 0),
                    "change": data.get("regularMarketChange", 0),
                    "changePercent": data.get("regularMarketChangePercent", 0),
                    "dayHigh": data.get("regularMarketDayHigh", 0),
                    "dayLow": data.get("regularMarketDayLow", 0),
                    "volume": data.get("regularMarketVolume", 0),
                    "source": "Yahoo Finance (alternative source)"
                }
                return transformed_data
            else:
                logger.error(f"Failed to fetch stock price from alternative source for {symbol}: {response.status_code} - {response.text}")
                return {"error": "Failed to fetch stock price from all sources", "symbol": symbol}
                
        except Exception as e:
            logger.error(f"Error fetching stock price from alternative source for {symbol}: {e}")
            return {"error": "Failed to fetch stock price due to exception", "symbol": symbol}

    def get_market_summary(self):
        """
        Get Nairobi Stock Exchange market summary
        
        Returns:
            dict: Market summary data
        """
        cache_key = "market_summary"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info("Cache hit for market summary")
            return cached_data
            
        logger.info("Fetching market summary")
        
        try:
            url = f"https://{self.nse_api_host}/market-summary"
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": self.nse_api_host
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                # Cache the data
                self._cache_set(cache_key, data, self.cache_expiry['market_summary'])
                return data
            else:
                logger.error(f"Failed to fetch market summary: {response.status_code} - {response.text}")
                return {"error": "Failed to fetch market summary"}
                
        except Exception as e:
            logger.error(f"Error fetching market summary: {e}")
            return {"error": "Failed to fetch market summary due to exception"}

    def get_historical_data(self, symbol, period="1mo"):
        """
        Get historical stock data for a given symbol
        
        Args:
            symbol (str): Stock symbol
            period (str): Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            dict: Historical stock data
        """
        cache_key = f"historical_data:{symbol}:{period}"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {symbol} historical data")
            return cached_data
            
        logger.info(f"Fetching historical data for {symbol}")
        
        try:
            # For NSE stocks, we need to append .NR to the symbol for Yahoo Finance
            yahoo_symbol = f"{symbol}.NR"
            url = f"https://{self.yahoo_finance_api_host}/api/quotes/{yahoo_symbol}/history"
            params = {
                "period": period,
                "interval": "1d"  # Daily data
            }
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": self.yahoo_finance_api_host
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Transform data to a more usable format
                historical_data = []
                for timestamp, quote in data.get("items", {}).items():
                    historical_data.append({
                        "date": datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d'),
                        "open": quote.get("open", 0),
                        "high": quote.get("high", 0),
                        "low": quote.get("low", 0),
                        "close": quote.get("close", 0),
                        "volume": quote.get("volume", 0),
                        "adjclose": quote.get("adjclose", 0)
                    })
                
                # Sort by date
                historical_data = sorted(historical_data, key=lambda x: x["date"])
                
                result = {
                    "symbol": symbol,
                    "period": period,
                    "data": historical_data
                }
                
                # Cache the data
                self._cache_set(cache_key, result, self.cache_expiry['historical_data'])
                
                return result
            else:
                logger.error(f"Failed to fetch historical data for {symbol}: {response.status_code} - {response.text}")
                return {"error": "Failed to fetch historical data"}
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return {"error": "Failed to fetch historical data due to exception"}

    def get_stock_news(self, symbol=None, max_results=10):
        """
        Get financial news related to stocks
        
        Args:
            symbol (str, optional): Stock symbol to filter news. If None, get general market news.
            max_results (int): Maximum number of news items to return
            
        Returns:
            dict: Stock news data
        """
        cache_key = f"stock_news:{symbol or 'market'}:{max_results}"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for {'market' if not symbol else symbol} news")
            return cached_data
            
        logger.info(f"Fetching stock news for {'market' if not symbol else symbol}")
        
        try:
            url = f"https://{self.yahoo_finance_api_host}/api/news/list"
            params = {
                "snippetCount": max_results,
                "region": "KE"  # Kenya region
            }
            
            if symbol:
                # For NSE stocks, we need to append .NR to the symbol for Yahoo Finance
                yahoo_symbol = f"{symbol}.NR"
                params["s"] = yahoo_symbol
                
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": self.yahoo_finance_api_host
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Transform data for easier consumption
                news_items = []
                for item in data.get("items", []):
                    news_items.append({
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "publisher": item.get("publisher", ""),
                        "published_at": item.get("published_at", ""),
                        "url": item.get("url", ""),
                        "thumbnail": item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url", "")
                    })
                
                result = {
                    "symbol": symbol,
                    "count": len(news_items),
                    "news": news_items
                }
                
                # Cache the data
                self._cache_set(cache_key, result, self.cache_expiry['stock_news'])
                
                return result
            else:
                logger.error(f"Failed to fetch news for {'market' if not symbol else symbol}: {response.status_code} - {response.text}")
                return {"error": "Failed to fetch stock news"}
                
        except Exception as e:
            logger.error(f"Error fetching news for {'market' if not symbol else symbol}: {e}")
            return {"error": "Failed to fetch stock news due to exception"}

    def get_sector_performance(self):
        """
        Get performance by sector
        
        Returns:
            dict: Sector performance data
        """
        cache_key = "sector_performance"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info("Cache hit for sector performance")
            return cached_data
            
        logger.info("Fetching sector performance")
        
        # Since NSE API doesn't have a dedicated sector performance endpoint,
        # we'll calculate it based on individual stock performances
        
        try:
            # Get market summary to get list of stocks
            market_data = self.get_market_summary()
            
            if "error" in market_data:
                return {"error": "Failed to fetch sector performance due to market data unavailability"}
            
            # Get sector mapping for NSE stocks
            sector_mapping = self._get_nse_sector_mapping()
            
            # Group stocks by sector and calculate performance
            sectors = {}
            
            for stock in market_data.get("stocks", []):
                symbol = stock.get("symbol", "")
                sector = sector_mapping.get(symbol, "Other")
                
                if sector not in sectors:
                    sectors[sector] = {
                        "stocks": [],
                        "averageChange": 0,
                        "averageVolume": 0,
                        "marketCap": 0,
                        "count": 0
                    }
                
                # Add stock to sector
                sectors[sector]["stocks"].append({
                    "symbol": symbol,
                    "name": stock.get("name", ""),
                    "price": stock.get("price", 0),
                    "change": stock.get("change", 0),
                    "changePercent": stock.get("changePercent", 0),
                    "volume": stock.get("volume", 0)
                })
                
                # Update sector aggregates
                sectors[sector]["count"] += 1
                sectors[sector]["averageChange"] += stock.get("changePercent", 0)
                sectors[sector]["averageVolume"] += stock.get("volume", 0)
                
            # Calculate averages
            for sector, data in sectors.items():
                if data["count"] > 0:
                    data["averageChange"] = round(data["averageChange"] / data["count"], 2)
                    data["averageVolume"] = round(data["averageVolume"] / data["count"], 0)
            
            # Sort sectors by average change
            sector_performance = []
            for sector, data in sectors.items():
                sector_performance.append({
                    "sector": sector,
                    "averageChange": data["averageChange"],
                    "averageVolume": data["averageVolume"],
                    "stockCount": data["count"],
                    "stocks": data["stocks"]
                })
            
            # Sort by average change (descending)
            sector_performance = sorted(sector_performance, key=lambda x: x["averageChange"], reverse=True)
            
            result = {
                "count": len(sector_performance),
                "sectors": sector_performance
            }
            
            # Cache the data
            self._cache_set(cache_key, result, self.cache_expiry['sector_performance'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating sector performance: {e}")
            return {"error": "Failed to calculate sector performance due to exception"}

    def _get_nse_sector_mapping(self):
        """
        Get mapping of NSE stock symbols to sectors
        
        Returns:
            dict: Mapping of stock symbols to sectors
        """
        # This is simplified - in a real implementation, this would be fetched from a database
        # or another API. For now, we'll use a small sample of known mappings.
        return {
            "SCOM": "TELECOMMUNICATION & TECHNOLOGY",
            "EQTY": "BANKING",
            "KCB": "BANKING",
            "COOP": "BANKING",
            "SBIC": "BANKING",
            "BRIT": "INSURANCE",
            "CTUM": "COMMERCIAL & SERVICES",
            "EABL": "MANUFACTURING & ALLIED",
            "BAT": "MANUFACTURING & ALLIED",
            "SASN": "INVESTMENT SERVICES",
            "ARM": "CONSTRUCTION & ALLIED",
            "PORT": "ENERGY & PETROLEUM",
            "KUKZ": "AGRICULTURAL",
            "WTK": "AGRICULTURAL",
            "SLAM": "REAL ESTATE INVESTMENT TRUST",
            "NSE": "INVESTMENT SERVICES"
        }

    def get_top_stocks(self, metric="changePercent", sector=None, limit=10):
        """
        Get top performing stocks based on a metric
        
        Args:
            metric (str): Metric to sort by (changePercent, volume, price)
            sector (str, optional): Filter by sector
            limit (int): Maximum number of stocks to return
            
        Returns:
            dict: Top stocks data
        """
        cache_key = f"top_stocks:{metric}:{sector or 'all'}:{limit}"
        cached_data = self._cache_get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for top stocks by {metric}")
            return cached_data
            
        logger.info(f"Finding top stocks by {metric}")
        
        try:
            # Get market summary to get list of stocks
            market_data = self.get_market_summary()
            
            if "error" in market_data:
                return {"error": "Failed to fetch top stocks due to market data unavailability"}
            
            stocks = market_data.get("stocks", [])
            
            # Filter by sector if specified
            if sector:
                sector_mapping = self._get_nse_sector_mapping()
                stocks = [stock for stock in stocks if sector_mapping.get(stock.get("symbol", ""), "") == sector]
            
            # Sort by the specified metric (descending)
            if metric in ["changePercent", "volume", "price"]:
                stocks = sorted(stocks, key=lambda x: x.get(metric, 0), reverse=True)
            else:
                # Default to changePercent if invalid metric specified
                stocks = sorted(stocks, key=lambda x: x.get("changePercent", 0), reverse=True)
            
            # Limit the results
            top_stocks = stocks[:limit]
            
            result = {
                "metric": metric,
                "sector": sector,
                "count": len(top_stocks),
                "stocks": top_stocks
            }
            
            # Cache the data
            self._cache_set(cache_key, result, self.cache_expiry['market_summary'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error finding top stocks by {metric}: {e}")
            return {"error": f"Failed to find top stocks due to exception: {str(e)}"}

    def calculate_risk_profile(self, age, investment_horizon, income_stability, existing_investments):
        """
        Calculate risk profile based on user information
        
        Args:
            age (int): User's age
            investment_horizon (int): Investment horizon in years
            income_stability (int): Income stability score (1-10)
            existing_investments (dict): Existing investments by category
            
        Returns:
            dict: Risk profile assessment
        """
        try:
            # Age factor: Younger investors can take more risk
            age_factor = max(10 - (age / 10), 1)  # Scale from 1 to 10
            
            # Investment horizon factor: Longer horizons allow more risk
            horizon_factor = min(investment_horizon / 2, 10)  # Scale from 0 to 10
            
            # Income stability factor: More stable income allows more risk
            stability_factor = income_stability  # Already on scale 1-10
            
            # Existing investments factor: Less diversified portfolios suggest lower risk tolerance
            diversification = len(existing_investments.keys())
            investment_factor = min(diversification * 2, 10)  # Scale from 0 to 10
            
            # Calculate overall risk score
            risk_score = (age_factor * 0.3) + (horizon_factor * 0.3) + (stability_factor * 0.2) + (investment_factor * 0.2)
            
            # Determine risk profile based on score
            if risk_score < 3:
                risk_profile = "Conservative"
                stock_allocation = 20
                bond_allocation = 60
                cash_allocation = 15
                alternative_allocation = 5
            elif risk_score < 5:
                risk_profile = "Moderate Conservative"
                stock_allocation = 40
                bond_allocation = 40
                cash_allocation = 10
                alternative_allocation = 10
            elif risk_score < 7:
                risk_profile = "Moderate"
                stock_allocation = 60
                bond_allocation = 25
                cash_allocation = 5
                alternative_allocation = 10
            elif risk_score < 8.5:
                risk_profile = "Moderate Aggressive"
                stock_allocation = 75
                bond_allocation = 15
                cash_allocation = 0
                alternative_allocation = 10
            else:
                risk_profile = "Aggressive"
                stock_allocation = 85
                bond_allocation = 5
                cash_allocation = 0
                alternative_allocation = 10
            
            return {
                "riskScore": round(risk_score, 1),
                "riskProfile": risk_profile,
                "allocation": {
                    "stocks": stock_allocation,
                    "bonds": bond_allocation,
                    "cash": cash_allocation,
                    "alternatives": alternative_allocation
                },
                "factors": {
                    "age": round(age_factor, 1),
                    "investmentHorizon": round(horizon_factor, 1),
                    "incomeStability": round(stability_factor, 1),
                    "existingInvestments": round(investment_factor, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk profile: {e}")
            return {"error": "Failed to calculate risk profile due to exception"}

    def get_investment_recommendations(self, risk_profile, investment_amount, sectors=None):
        """
        Get investment recommendations based on risk profile
        
        Args:
            risk_profile (str): User's risk profile (Conservative, Moderate Conservative, Moderate, Moderate Aggressive, Aggressive)
            investment_amount (float): Total investment amount in KES
            sectors (list, optional): Preferred sectors to invest in
            
        Returns:
            dict: Investment recommendations
        """
        try:
            # Get sector performance to identify top sectors
            sector_data = self.get_sector_performance()
            if "error" in sector_data:
                return {"error": "Failed to generate recommendations due to sector data unavailability"}
            
            # Get top stocks
            top_stocks_data = self.get_top_stocks(metric="changePercent", limit=20)
            if "error" in top_stocks_data:
                return {"error": "Failed to generate recommendations due to stock data unavailability"}
            
            # Default allocations based on risk profile
            allocations = {
                "Conservative": {
                    "bluechip": 0.15,
                    "growth": 0.05,
                    "bonds": 0.60,
                    "tbills": 0.15,
                    "alternative": 0.05
                },
                "Moderate Conservative": {
                    "bluechip": 0.30,
                    "growth": 0.10,
                    "bonds": 0.40,
                    "tbills": 0.10,
                    "alternative": 0.10
                },
                "Moderate": {
                    "bluechip": 0.40,
                    "growth": 0.20,
                    "bonds": 0.25,
                    "tbills": 0.05,
                    "alternative": 0.10
                },
                "Moderate Aggressive": {
                    "bluechip": 0.45,
                    "growth": 0.30,
                    "bonds": 0.15,
                    "tbills": 0.0,
                    "alternative": 0.10
                },
                "Aggressive": {
                    "bluechip": 0.50,
                    "growth": 0.35,
                    "bonds": 0.05,
                    "tbills": 0.0,
                    "alternative": 0.10
                }
            }
            
            # Use default allocation if risk profile not found
            allocation = allocations.get(risk_profile, allocations["Moderate"])
            
            # Define blue chip stocks for NSE
            bluechip_stocks = ["SCOM", "EQTY", "KCB", "EABL", "BAT", "COOP", "SBIC"]
            
            # Filter top stocks by growth and blue chip categories
            growth_stocks = []
            blue_chip_stocks = []
            
            for stock in top_stocks_data.get("stocks", []):
                symbol = stock.get("symbol", "")
                if symbol in bluechip_stocks:
                    blue_chip_stocks.append(stock)
                else:
                    growth_stocks.append(stock)
            
            # Sort by performance
            blue_chip_stocks = sorted(blue_chip_stocks, key=lambda x: x.get("changePercent", 0), reverse=True)
            growth_stocks = sorted(growth_stocks, key=lambda x: x.get("changePercent", 0), reverse=True)
            
            # Calculate investment amounts
            bluechip_amount = allocation["bluechip"] * investment_amount
            growth_amount = allocation["growth"] * investment_amount
            bonds_amount = allocation["bonds"] * investment_amount
            tbills_amount = allocation["tbills"] * investment_amount
            alternative_amount = allocation["alternative"] * investment_amount
            
            # Prepare stock recommendations
            stock_recommendations = []
            
            # Add blue chip stocks to recommendations
            total_bluechip = len(blue_chip_stocks)
            if total_bluechip > 0:
                amount_per_bluechip = bluechip_amount / total_bluechip
                for stock in blue_chip_stocks[:5]:  # Maximum 5 blue chip stocks
                    stock_recommendations.append({
                        "symbol": stock.get("symbol", ""),
                        "name": stock.get("name", ""),
                        "type": "Blue Chip",
                        "amount": round(amount_per_bluechip, 2),
                        "price": stock.get("price", 0),
                        "shares": round(amount_per_bluechip / stock.get("price", 1), 0),
                        "changePercent": stock.get("changePercent", 0)
                    })
            
            # Add growth stocks to recommendations
            total_growth = len(growth_stocks)
            if total_growth > 0:
                amount_per_growth = growth_amount / total_growth
                for stock in growth_stocks[:3]:  # Maximum 3 growth stocks
                    stock_recommendations.append({
                        "symbol": stock.get("symbol", ""),
                        "name": stock.get("name", ""),
                        "type": "Growth",
                        "amount": round(amount_per_growth, 2),
                        "price": stock.get("price", 0),
                        "shares": round(amount_per_growth / stock.get("price", 1), 0),
                        "changePercent": stock.get("changePercent", 0)
                    })
            
            # Prepare bond recommendations (simplified for now)
            bond_recommendations = [
                {
                    "type": "Government Bond",
                    "name": "Kenya 10-Year Treasury Bond",
                    "yield": 13.5,
                    "amount": round(bonds_amount * 0.6, 2),
                    "maturity": "10 years"
                },
                {
                    "type": "Government Bond",
                    "name": "Kenya 5-Year Treasury Bond",
                    "yield": 12.3,
                    "amount": round(bonds_amount * 0.4, 2),
                    "maturity": "5 years"
                }
            ]
            
            # Prepare T-Bill recommendations (simplified for now)
            tbill_recommendations = []
            if tbills_amount > 0:
                tbill_recommendations = [
                    {
                        "type": "Treasury Bill",
                        "name": "Kenya 91-Day Treasury Bill",
                        "yield": 9.5,
                        "amount": round(tbills_amount * 0.5, 2),
                        "maturity": "91 days"
                    },
                    {
                        "type": "Treasury Bill",
                        "name": "Kenya 364-Day Treasury Bill",
                        "yield": 10.8,
                        "amount": round(tbills_amount * 0.5, 2),
                        "maturity": "364 days"
                    }
                ]
            
            # Prepare alternative investment recommendations (simplified for now)
            alternative_recommendations = []
            if alternative_amount > 0:
                alternative_recommendations = [
                    {
                        "type": "REIT",
                        "name": "ILAM Fahari I-REIT",
                        "symbol": "FAHR",
                        "amount": round(alternative_amount * 0.7, 2),
                        "yield": 8.0
                    },
                    {
                        "type": "ETF",
                        "name": "NewGold ETF",
                        "symbol": "GLD",
                        "amount": round(alternative_amount * 0.3, 2),
                        "yield": 5.0
                    }
                ]
            
            result = {
                "riskProfile": risk_profile,
                "totalInvestment": investment_amount,
                "allocation": {
                    "stocks": {
                        "bluechip": round(bluechip_amount, 2),
                        "growth": round(growth_amount, 2),
                        "total": round(bluechip_amount + growth_amount, 2),
                        "percentage": round((bluechip_amount + growth_amount) / investment_amount * 100, 1)
                    },
                    "bonds": {
                        "total": round(bonds_amount, 2),
                        "percentage": round(bonds_amount / investment_amount * 100, 1)
                    },
                    "tbills": {
                        "total": round(tbills_amount, 2),
                        "percentage": round(tbills_amount / investment_amount * 100, 1)
                    },
                    "alternatives": {
                        "total": round(alternative_amount, 2),
                        "percentage": round(alternative_amount / investment_amount * 100, 1)
                    }
                },
                "recommendations": {
                    "stocks": stock_recommendations,
                    "bonds": bond_recommendations,
                    "tbills": tbill_recommendations,
                    "alternatives": alternative_recommendations
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating investment recommendations: {e}")
            return {"error": f"Failed to generate investment recommendations due to exception: {str(e)}"}

    def analyze_portfolio(self, portfolio):
        """
        Analyze portfolio performance and risk
        
        Args:
            portfolio (list): List of stocks in portfolio with quantities
            
        Returns:
            dict: Portfolio analysis
        """
        try:
            # Get market data for all stocks in portfolio
            portfolio_data = []
            portfolio_value = 0
            portfolio_daily_change = 0
            
            for item in portfolio:
                symbol = item.get("symbol", "")
                quantity = item.get("quantity", 0)
                
                # Get current stock data
                stock_data = self.get_stock_price(symbol)
                
                if "error" not in stock_data:
                    current_price = stock_data.get("price", 0)
                    day_change = stock_data.get("changePercent", 0)
                    current_value = current_price * quantity
                    
                    portfolio_data.append({
                        "symbol": symbol,
                        "name": stock_data.get("name", ""),
                        "quantity": quantity,
                        "price": current_price,
                        "value": current_value,
                        "dayChange": day_change,
                        "dayChangeValue": (day_change / 100) * current_value
                    })
                    
                    portfolio_value += current_value
                    portfolio_daily_change += (day_change / 100) * current_value
            
            # Calculate portfolio metrics
            if portfolio_value > 0:
                portfolio_daily_change_percent = (portfolio_daily_change / portfolio_value) * 100
            else:
                portfolio_daily_change_percent = 0
            
            # Calculate portfolio allocation by stock
            for item in portfolio_data:
                item["allocation"] = (item["value"] / portfolio_value) * 100 if portfolio_value > 0 else 0
            
            # Get sector mapping
            sector_mapping = self._get_nse_sector_mapping()
            
            # Calculate sector allocation
            sector_allocation = {}
            for item in portfolio_data:
                sector = sector_mapping.get(item["symbol"], "Other")
                if sector not in sector_allocation:
                    sector_allocation[sector] = 0
                sector_allocation[sector] += item["value"]
            
            # Convert sector allocation to percentage
            sector_allocation = {sector: (value / portfolio_value) * 100 if portfolio_value > 0 else 0 
                               for sector, value in sector_allocation.items()}
            
            # Sort portfolio data by value (descending)
            portfolio_data = sorted(portfolio_data, key=lambda x: x["value"], reverse=True)
            
            result = {
                "totalValue": portfolio_value,
                "dailyChange": portfolio_daily_change,
                "dailyChangePercent": portfolio_daily_change_percent,
                "holdings": portfolio_data,
                "sectorAllocation": sector_allocation
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio: {e}")
            return {"error": f"Failed to analyze portfolio due to exception: {str(e)}"}

    def get_stock_prediction(self, symbol, days=30):
        """
        Get stock price prediction based on historical data
        
        Args:
            symbol (str): Stock symbol
            days (int): Number of days to predict
            
        Returns:
            dict: Stock prediction data
        """
        try:
            # Get historical data for the past year
            historical_data = self.get_historical_data(symbol, period="1y")
            
            if "error" in historical_data:
                return {"error": "Failed to predict stock prices due to historical data unavailability"}
            
            # Extract prices
            prices = [item["close"] for item in historical_data.get("data", [])]
            
            if len(prices) < 30:
                return {"error": "Insufficient historical data for prediction"}
            
            # Calculate simple moving averages
            sma20 = np.mean(prices[-20:])
            sma50 = np.mean(prices[-50:]) if len(prices) >= 50 else np.mean(prices)
            sma100 = np.mean(prices[-100:]) if len(prices) >= 100 else np.mean(prices)
            
            # Simple linear trend based on recent data
            recent_prices = prices[-30:]
            
            # Calculate linear regression
            days_array = np.arange(len(recent_prices))
            coefficients = np.polyfit(days_array, recent_prices, 1)
            slope = coefficients[0]
            intercept = coefficients[1]
            
            # Predict future prices
            future_days = np.arange(len(recent_prices), len(recent_prices) + days)
            predicted_prices = [slope * x + intercept for x in future_days]
            
            # Calculate confidence intervals (simplified)
            std_dev = np.std(recent_prices)
            confidence_interval = 1.96 * std_dev  # 95% confidence interval
            
            upper_bound = [price + confidence_interval for price in predicted_prices]
            lower_bound = [price - confidence_interval for price in predicted_prices]
            
            # Prepare future dates
            last_date = datetime.strptime(historical_data["data"][-1]["date"], "%Y-%m-%d")
            future_dates = [(last_date + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(days)]
            
            # Prepare prediction data
            prediction_data = []
            for i in range(days):
                prediction_data.append({
                    "date": future_dates[i],
                    "predicted": round(predicted_prices[i], 2),
                    "upperBound": round(upper_bound[i], 2),
                    "lowerBound": round(lower_bound[i], 2)
                })
            
            # Calculate trend indicators
            current_price = prices[-1]
            short_term_trend = "Bullish" if current_price > sma20 else "Bearish"
            medium_term_trend = "Bullish" if current_price > sma50 else "Bearish"
            long_term_trend = "Bullish" if current_price > sma100 else "Bearish"
            
            # Calculate potential return
            end_price = predicted_prices[-1]
            potential_return = ((end_price - current_price) / current_price) * 100
            
            result = {
                "symbol": symbol,
                "currentPrice": current_price,
                "predictions": prediction_data,
                "technicalIndicators": {
                    "sma20": round(sma20, 2),
                    "sma50": round(sma50, 2),
                    "sma100": round(sma100, 2),
                    "shortTermTrend": short_term_trend,
                    "mediumTermTrend": medium_term_trend,
                    "longTermTrend": long_term_trend
                },
                "potentialReturn": round(potential_return, 2),
                "confidence": round(100 - (std_dev / current_price) * 100, 2) if current_price > 0 else 0,
                "disclaimer": "This prediction is based on historical data and technical analysis only. It should not be considered as financial advice."
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting stock prices for {symbol}: {e}")
            return {"error": f"Failed to predict stock prices due to exception: {str(e)}"}


# Example usage
if __name__ == "__main__":
    investment_api = InvestmentAPI()
    
    # Example 1: Get stock price
    print("Testing get_stock_price...")
    stock_price = investment_api.get_stock_price("SCOM")
    print(json.dumps(stock_price, indent=2))
    
    # Example 2: Get market summary
    print("\nTesting get_market_summary...")
    market_summary = investment_api.get_market_summary()
    if "error" not in market_summary:
        print(f"Number of stocks: {len(market_summary.get('stocks', []))}")
    else:
        print(market_summary["error"])
    
    # Example 3: Get historical data
    print("\nTesting get_historical_data...")
    historical_data = investment_api.get_historical_data("SCOM", period="1mo")
    if "error" not in historical_data:
        print(f"Number of data points: {len(historical_data.get('data', []))}")
    else:
        print(historical_data["error"])
    
    # Example 4: Get stock news
    print("\nTesting get_stock_news...")
    stock_news = investment_api.get_stock_news("SCOM", max_results=5)
    if "error" not in stock_news:
        print(f"Number of news items: {stock_news.get('count', 0)}")
    else:
        print(stock_news["error"])
    
    # Example 5: Calculate risk profile
    print("\nTesting calculate_risk_profile...")
    risk_profile = investment_api.calculate_risk_profile(
        age=30,
        investment_horizon=10,
        income_stability=7,
        existing_investments={"stocks": 3, "bonds": 1}
    )
    print(json.dumps(risk_profile, indent=2))
    
    # Example 6: Get investment recommendations
    print("\nTesting get_investment_recommendations...")
    recommendations = investment_api.get_investment_recommendations(
        risk_profile="Moderate",
        investment_amount=1000000
    )
    if "error" not in recommendations:
        print(f"Number of stock recommendations: {len(recommendations.get('recommendations', {}).get('stocks', []))}")
    else:
        print(recommendations["error"])
