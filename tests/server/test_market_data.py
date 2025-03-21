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
def known_stocks():
    """Fixture to provide well-known NSE stocks"""
    return [
        {"symbol": "SCOM", "name": "Safaricom PLC"},
        {"symbol": "EQTY", "name": "Equity Group Holdings"},
        {"symbol": "KCB", "name": "KCB Group"},
        {"symbol": "COOP", "name": "Co-operative Bank"},
        {"symbol": "SCBK", "name": "Standard Chartered Bank"},
        {"symbol": "BAMB", "name": "Bamburi Cement"},
        {"symbol": "EABL", "name": "East African Breweries"}
    ]

@pytest.fixture
def known_sectors():
    """Fixture to provide NSE market sectors"""
    return [
        "Banking",
        "Commercial and Services",
        "Telecommunication and Technology",
        "Manufacturing and Allied",
        "Construction and Allied",
        "Energy and Petroleum",
        "Investment",
        "Insurance"
    ]


class TestStockData:
    """Tests for stock data retrieval"""
    
    def test_get_stock_price(self, auth_headers, known_stocks):
        """Test retrieving current stock price data"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        response = client.get(f"/market-data/stocks/{stock_symbol}", headers=auth_headers)
        
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
        assert "change" in data or "day_change" in data, "Price change not in response"
        assert "change_percent" in data or "day_change_percent" in data, "Percent change not in response"
        
        # Verify symbol matches request
        assert data["symbol"] == stock_symbol, "Returned symbol doesn't match request"
    
    def test_get_multiple_stocks(self, auth_headers, known_stocks):
        """Test retrieving data for multiple stocks"""
        # Select a subset of stocks to query
        selected_stocks = random.sample(known_stocks, min(3, len(known_stocks)))
        symbols = [stock["symbol"] for stock in selected_stocks]
        
        # Query string format: ?symbols=SCOM,EQTY,KCB
        query_string = ",".join(symbols)
        
        response = client.get(f"/market-data/stocks?symbols={query_string}", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Multiple stocks endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Multiple stocks retrieval failed: {response.text}"
        
        # Verify response contains expected data
        data = response.json()
        assert isinstance(data, list), "Expected a list of stocks"
        assert len(data) == len(symbols), f"Expected {len(symbols)} stocks, got {len(data)}"
        
        # Verify each requested symbol is in the response
        returned_symbols = [stock["symbol"] for stock in data]
        for symbol in symbols:
            assert symbol in returned_symbols, f"Requested symbol {symbol} not in response"
    
    def test_stock_details(self, auth_headers, known_stocks):
        """Test retrieving detailed stock information"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        response = client.get(f"/market-data/stocks/{stock_symbol}/details", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock details endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock details retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "name" in data, "Company name not in response"
        assert "sector" in data, "Sector not in response"
        assert "market_cap" in data, "Market cap not in response"
        assert "52_week_high" in data or "year_high" in data, "52-week high not in response"
        assert "52_week_low" in data or "year_low" in data, "52-week low not in response"
        
        # Verify symbol matches request
        assert data["symbol"] == stock_symbol, "Returned symbol doesn't match request"


class TestMarketIndices:
    """Tests for market indices data"""
    
    def test_get_all_indices(self, auth_headers):
        """Test retrieving all market indices"""
        response = client.get("/market-data/indices", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market indices endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market indices retrieval failed: {response.text}"
        
        # Verify response contains expected data
        data = response.json()
        assert isinstance(data, list), "Expected a list of indices"
        assert len(data) > 0, "No indices returned"
        
        # Verify each index has required fields
        for index in data:
            assert "name" in index, "Index name not in response"
            assert "value" in index, "Index value not in response"
            assert "change" in index, "Index change not in response"
            assert "change_percent" in index, "Index change percent not in response"
        
        # NSE 20 should be among the indices
        assert any(index["name"] in ["NSE 20", "NSE20", "NSE-20"] for index in data), "NSE 20 index not found"
    
    def test_get_specific_index(self, auth_headers):
        """Test retrieving a specific market index"""
        # NSE 20 is the main index
        index_name = "NSE20"
        
        response = client.get(f"/market-data/indices/{index_name}", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Specific index endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Specific index retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "name" in data, "Index name not in response"
        assert "value" in data, "Index value not in response"
        assert "change" in data, "Index change not in response"
        assert "change_percent" in data, "Index change percent not in response"
        assert "last_updated" in data, "Last updated timestamp not in response"
        
        # Verify name matches request (allowing for variations in format)
        assert data["name"].replace(" ", "").replace("-", "").upper() == index_name.replace(" ", "").replace("-", "").upper(), \
            "Returned index name doesn't match request"
    
    def test_index_historical_data(self, auth_headers):
        """Test retrieving historical data for an index"""
        # NSE 20 is the main index
        index_name = "NSE20"
        
        # Set parameters for historical data request
        params = {
            "period": "1m",  # 1 month
            "interval": "1d"  # Daily data
        }
        
        response = client.get(f"/market-data/indices/{index_name}/history", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Index historical data endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Index historical data retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "name" in data, "Index name not in response"
        assert "period" in data, "Period not in response"
        assert "interval" in data, "Interval not in response"
        assert "data" in data, "Historical data not in response"
        
        # Verify historical data is a non-empty list
        assert isinstance(data["data"], list), "Historical data should be a list"
        assert len(data["data"]) > 0, "No historical data points returned"
        
        # Verify data points have required fields
        for point in data["data"]:
            assert "date" in point, "Date not in data point"
            assert "value" in point, "Index value not in data point"


class TestSectorData:
    """Tests for sector data and analysis"""
    
    def test_get_all_sectors(self, auth_headers, known_sectors):
        """Test retrieving all market sectors"""
        response = client.get("/market-data/sectors", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market sectors endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market sectors retrieval failed: {response.text}"
        
        # Verify response contains expected data
        data = response.json()
        assert isinstance(data, list), "Expected a list of sectors"
        assert len(data) > 0, "No sectors returned"
        
        # Verify some known sectors are in the response
        returned_sectors = [sector["name"] for sector in data]
        for sector in known_sectors[:3]:  # Check at least a few known sectors
            assert any(known in returned_sector for returned_sector in returned_sectors for known in [sector, sector.upper(), sector.lower()]), \
                f"Known sector '{sector}' not found in response"
    
    def test_sector_performance(self, auth_headers, known_sectors):
        """Test retrieving sector performance data"""
        # Test with a well-known sector
        sector = random.choice(known_sectors)
        
        # Clean sector name for URL (remove spaces, etc.)
        sector_param = sector.replace(" ", "_").lower()
        
        response = client.get(f"/market-data/sectors/{sector_param}/performance", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Sector performance endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Sector performance retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "sector" in data, "Sector name not in response"
        assert "performance" in data, "Performance data not in response"
        assert "stocks" in data, "Sector stocks not in response"
        
        # Verify performance metrics
        performance = data["performance"]
        assert "daily_change" in performance, "Daily change not in performance data"
        assert "weekly_change" in performance, "Weekly change not in performance data"
        assert "monthly_change" in performance, "Monthly change not in performance data"
        assert "ytd_change" in performance, "YTD change not in performance data"
        
        # Verify stocks is a non-empty list
        assert isinstance(data["stocks"], list), "Sector stocks should be a list"
        assert len(data["stocks"]) > 0, "No stocks in sector"
        
        # Verify each stock has required fields
        for stock in data["stocks"]:
            assert "symbol" in stock, "Stock symbol not in response"
            assert "name" in stock, "Company name not in response"
            assert "current_price" in stock, "Current price not in response"
            assert "change_percent" in stock, "Percent change not in response"
    
    def test_sector_comparison(self, auth_headers):
        """Test sector performance comparison"""
        # Request parameters to compare sector performances
        params = {
            "period": "1m"  # 1 month
        }
        
        response = client.get("/market-data/sectors/comparison", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Sector comparison endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Sector comparison retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "period" in data, "Period not in response"
        assert "sectors" in data, "Sectors not in response"
        
        # Verify sectors is a non-empty list
        assert isinstance(data["sectors"], list), "Sectors should be a list"
        assert len(data["sectors"]) > 0, "No sectors in comparison"
        
        # Verify each sector has required fields
        for sector in data["sectors"]:
            assert "name" in sector, "Sector name not in response"
            assert "performance" in sector, "Performance not in response"
            assert "market_cap" in sector, "Market cap not in response"
            assert "top_stock" in sector, "Top stock not in response"


class TestHistoricalData:
    """Tests for historical data analysis"""
    
    def test_stock_historical_prices(self, auth_headers, known_stocks):
        """Test retrieving historical price data for a stock"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        # Set parameters for historical data request
        params = {
            "period": "3m",  # 3 months
            "interval": "1d"  # Daily data
        }
        
        response = client.get(f"/market-data/stocks/{stock_symbol}/history", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock historical data endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock historical data retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "name" in data, "Company name not in response"
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
            # Some of these might be optional depending on the data source
            # assert "open" in point, "Open price not in data point"
            # assert "high" in point, "High price not in data point"
            # assert "low" in point, "Low price not in data point"
            # assert "volume" in point, "Volume not in data point"
    
    def test_stock_technical_indicators(self, auth_headers, known_stocks):
        """Test retrieving technical indicators for a stock"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        # Set parameters for technical indicators request
        params = {
            "period": "6m",  # 6 months
            "indicators": "sma,ema,rsi"  # Moving averages and RSI
        }
        
        response = client.get(f"/market-data/stocks/{stock_symbol}/indicators", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Technical indicators endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Technical indicators retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "period" in data, "Period not in response"
        assert "indicators" in data, "Indicators not in response"
        
        # Verify indicators object has the requested indicators
        indicators = data["indicators"]
        assert "sma" in indicators, "SMA not in indicators"
        assert "ema" in indicators, "EMA not in indicators"
        assert "rsi" in indicators, "RSI not in indicators"
        
        # Verify at least SMA contains data points
        assert isinstance(indicators["sma"], list), "SMA should be a list of data points"
        assert len(indicators["sma"]) > 0, "No SMA data points returned"
        
        # Verify SMA data points have required fields
        for point in indicators["sma"]:
            assert "date" in point, "Date not in SMA data point"
            assert "value" in point, "Value not in SMA data point"
    
    def test_stock_performance_analysis(self, auth_headers, known_stocks):
        """Test retrieving performance analysis for a stock"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        response = client.get(f"/market-data/stocks/{stock_symbol}/performance", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock performance analysis endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock performance analysis failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "name" in data, "Company name not in response"
        assert "performance" in data, "Performance data not in response"
        
        # Verify performance metrics
        performance = data["performance"]
        assert "daily" in performance, "Daily performance not in response"
        assert "weekly" in performance, "Weekly performance not in response"
        assert "monthly" in performance, "Monthly performance not in response"
        assert "quarterly" in performance, "Quarterly performance not in response"
        assert "yearly" in performance, "Yearly performance not in response"
        assert "ytd" in performance, "YTD performance not in response"
        
        # Verify each performance period has change and change percent
        for period in ["daily", "weekly", "monthly", "quarterly", "yearly", "ytd"]:
            period_data = performance[period]
            assert "change" in period_data, f"Change not in {period} performance"
            assert "change_percent" in period_data, f"Change percent not in {period} performance"


class TestStockScreener:
    """Tests for stock screening functionality"""
    
    def test_stock_screener(self, auth_headers):
        """Test stock screening with various filters"""
        # Set screening criteria
        screening_params = {
            "min_price": 10,
            "max_price": 1000,
            "min_market_cap": 1000000000,  # 1 billion
            "sector": "Banking",
            "sort_by": "price",
            "order": "desc"
        }
        
        response = client.get("/market-data/screener", params=screening_params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock screener endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock screener failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "results" in data, "Results not in response"
        assert "count" in data, "Count not in response"
        assert "filters" in data, "Applied filters not in response"
        
        # Verify results is a list
        assert isinstance(data["results"], list), "Results should be a list"
        
        # If results are returned, verify they match the filtering criteria
        if len(data["results"]) > 0:
            for stock in data["results"]:
                assert "symbol" in stock, "Stock symbol not in response"
                assert "name" in stock, "Company name not in response"
                assert "price" in stock, "Price not in response"
                assert "market_cap" in stock, "Market cap not in response"
                assert "sector" in stock, "Sector not in response"
                
                # Verify the stock meets the filtering criteria
                assert stock["price"] >= screening_params["min_price"], "Stock price below min_price filter"
                assert stock["price"] <= screening_params["max_price"], "Stock price above max_price filter"
                assert stock["market_cap"] >= screening_params["min_market_cap"], "Stock market cap below min_market_cap filter"
                
                # Sector check - allowing for variations in format and partial matching
                assert screening_params["sector"].lower() in stock["sector"].lower(), "Stock sector doesn't match sector filter"
    
    def test_top_gainers_losers(self, auth_headers):
        """Test retrieving top gainers and losers"""
        # Request top 5 gainers and losers
        params = {
            "limit": 5
        }
        
        # Test gainers endpoint
        gainers_response = client.get("/market-data/gainers", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if gainers_response.status_code == 404:
            pytest.skip("Gainers endpoint not implemented")
        
        # Assert successful retrieval
        assert gainers_response.status_code == 200, f"Top gainers retrieval failed: {gainers_response.text}"
        
        # Verify gainers response contains expected fields
        gainers_data = gainers_response.json()
        assert isinstance(gainers_data, list), "Gainers should be a list"
        assert len(gainers_data) <= params["limit"], f"Expected at most {params['limit']} gainers, got {len(gainers_data)}"
        
        # Test losers endpoint
        losers_response = client.get("/market-data/losers", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if losers_response.status_code == 404:
            pytest.skip("Losers endpoint not implemented")
        
        # Assert successful retrieval
        assert losers_response.status_code == 200, f"Top losers retrieval failed: {losers_response.text}"
        
        # Verify losers response contains expected fields
        losers_data = losers_response.json()
        assert isinstance(losers_data, list), "Losers should be a list"
        assert len(losers_data) <= params["limit"], f"Expected at most {params['limit']} losers, got {len(losers_data)}"
        
        # Verify each gainer and loser has required fields
        for stock in gainers_data + losers_data:
            assert "symbol" in stock, "Stock symbol not in response"
            assert "name" in stock, "Company name not in response"
            assert "price" in stock, "Price not in response"
            assert "change" in stock or "day_change" in stock, "Change not in response"
            assert "change_percent" in stock or "day_change_percent" in stock, "Change percent not in response"
        
        # If both endpoints return data, verify gainers have positive change and losers have negative change
        if gainers_data and losers_data:
            for gainer in gainers_data:
                change_percent = gainer.get("change_percent", gainer.get("day_change_percent", 0))
                assert change_percent > 0, "Gainer has non-positive change percent"
            
            for loser in losers_data:
                change_percent = loser.get("change_percent", loser.get("day_change_percent", 0))
                assert change_percent < 0, "Loser has non-negative change percent"


class TestMarketNews:
    """Tests for market news and announcements"""
    
    def test_market_news(self, auth_headers):
        """Test retrieving market news"""
        # Set parameters for news request
        params = {
            "limit": 10,
            "category": "all"
        }
        
        response = client.get("/market-data/news", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market news endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market news retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "news" in data, "News articles not in response"
        assert "count" in data, "Count not in response"
        
        # Verify news is a non-empty list
        assert isinstance(data["news"], list), "News should be a list"
        assert len(data["news"]) > 0, "No news articles returned"
        
        # Verify each news article has required fields
        for article in data["news"]:
            assert "title" in article, "Title not in news article"
            assert "date" in article or "published_at" in article, "Date not in news article"
            assert "source" in article, "Source not in news article"
            assert "summary" in article or "description" in article, "Summary not in news article"
            assert "url" in article, "URL not in news article"
    
    def test_stock_specific_news(self, auth_headers, known_stocks):
        """Test retrieving news for a specific stock"""
        # Test with a well-known stock
        stock = random.choice(known_stocks)
        stock_symbol = stock["symbol"]
        
        # Set parameters for news request
        params = {
            "limit": 5
        }
        
        response = client.get(f"/market-data/stocks/{stock_symbol}/news", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Stock-specific news endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Stock-specific news retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "symbol" in data, "Stock symbol not in response"
        assert "name" in data, "Company name not in response"
        assert "news" in data, "News articles not in response"
        
        # Verify news is a list
        assert isinstance(data["news"], list), "News should be a list"
        
        # If news articles are returned, verify they have required fields
        if len(data["news"]) > 0:
            for article in data["news"]:
                assert "title" in article, "Title not in news article"
                assert "date" in article or "published_at" in article, "Date not in news article"
                assert "source" in article, "Source not in news article"
                assert "summary" in article or "description" in article, "Summary not in news article"
                assert "url" in article, "URL not in news article"
    
    def test_market_calendar(self, auth_headers):
        """Test retrieving market calendar events"""
        # Set parameters for calendar request
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "type": "all"  # All event types (earnings, dividends, etc.)
        }
        
        response = client.get("/market-data/calendar", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market calendar endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market calendar retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "events" in data, "Calendar events not in response"
        assert "period" in data, "Period not in response"
        
        # Verify events is a list
        assert isinstance(data["events"], list), "Events should be a list"
        
        # If events are returned, verify they have required fields
        if len(data["events"]) > 0:
            for event in data["events"]:
                assert "date" in event, "Date not in event"
                assert "type" in event, "Event type not in event"
                assert "title" in event or "description" in event, "Title/description not in event"
                
                # If it's a company event, it should have a symbol
                if event["type"] in ["earnings", "dividend", "split"]:
                    assert "symbol" in event, "Symbol not in company event"


class TestMarketStats:
    """Tests for market statistics and analytics"""
    
    def test_market_overview(self, auth_headers):
        """Test retrieving market overview statistics"""
        response = client.get("/market-data/overview", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market overview endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market overview retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "indices" in data, "Indices not in overview"
        assert "sector_performance" in data, "Sector performance not in overview"
        assert "market_breadth" in data, "Market breadth not in overview"
        assert "last_updated" in data, "Last updated timestamp not in overview"
        
        # Verify market breadth has required fields
        breadth = data["market_breadth"]
        assert "advancing" in breadth, "Advancing stocks count not in market breadth"
        assert "declining" in breadth, "Declining stocks count not in market breadth"
        assert "unchanged" in breadth, "Unchanged stocks count not in market breadth"
        assert "total_volume" in breadth, "Total volume not in market breadth"
    
    def test_market_heatmap(self, auth_headers):
        """Test retrieving market heatmap data"""
        response = client.get("/market-data/heatmap", headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market heatmap endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market heatmap retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "stocks" in data, "Stocks not in heatmap"
        assert "last_updated" in data, "Last updated timestamp not in heatmap"
        
        # Verify stocks is a non-empty list
        assert isinstance(data["stocks"], list), "Stocks should be a list"
        assert len(data["stocks"]) > 0, "No stocks in heatmap"
        
        # Verify each stock has required fields
        for stock in data["stocks"]:
            assert "symbol" in stock, "Symbol not in stock"
            assert "name" in stock, "Name not in stock"
            assert "price" in stock, "Price not in stock"
            assert "change_percent" in stock, "Change percent not in stock"
            assert "market_cap" in stock, "Market cap not in stock"
            assert "sector" in stock, "Sector not in stock"
    
    def test_market_correlation(self, auth_headers, known_stocks):
        """Test retrieving market correlation data"""
        # Select a few stocks for correlation analysis
        selected_stocks = random.sample(known_stocks, min(5, len(known_stocks)))
        symbols = [stock["symbol"] for stock in selected_stocks]
        
        # Query string format: ?symbols=SCOM,EQTY,KCB&period=1y
        symbols_param = ",".join(symbols)
        params = {
            "symbols": symbols_param,
            "period": "1y"  # 1 year
        }
        
        response = client.get("/market-data/correlation", params=params, headers=auth_headers)
        
        # Check if endpoint exists
        if response.status_code == 404:
            pytest.skip("Market correlation endpoint not implemented")
        
        # Assert successful retrieval
        assert response.status_code == 200, f"Market correlation retrieval failed: {response.text}"
        
        # Verify response contains expected fields
        data = response.json()
        assert "correlation_matrix" in data, "Correlation matrix not in response"
        assert "period" in data, "Period not in response"
        assert "symbols" in data, "Symbols not in response"
        
        # Verify returned symbols match requested symbols
        assert set(data["symbols"]) == set(symbols), "Returned symbols don't match requested symbols"
        
        # Verify correlation matrix dimensions match number of symbols
        matrix = data["correlation_matrix"]
        assert len(matrix) == len(symbols), "Correlation matrix rows don't match number of symbols"
        assert all(len(row) == len(symbols) for row in matrix), "Correlation matrix columns don't match number of symbols"
        
        # Verify diagonal elements are 1.0 (correlation of a stock with itself)
        for i in range(len(symbols)):
            assert abs(matrix[i][i] - 1.0) < 0.001, "Diagonal element not 1.0 in correlation matrix"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])