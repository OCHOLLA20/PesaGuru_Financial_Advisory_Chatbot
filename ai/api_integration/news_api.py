import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("news_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API Configuration
API_KEYS = {
    "rapid_api": os.getenv("RAPIDAPI_KEY", "64be62d004msh5d2c420664b91e8p114762jsn5d31ba70e581"),
    "news_api": os.getenv("NEWS_API_KEY"),
    "reuters_api": os.getenv("REUTERS_API_KEY"),
}

ENDPOINTS = {
    "reuters_business": {
        "host": "reuters-business-and-financial-news.p.rapidapi.com",
        "base_url": "https://reuters-business-and-financial-news.p.rapidapi.com",
        "list_rics": "/market-rics/list-rics-by-asset-and-category/1/1",
    },
    "reuters": {
        "host": "reuters-api.p.rapidapi.com",
        "base_url": "https://reuters-api.p.rapidapi.com",
        "category": "/category",
    },
    "news_api": {
        "host": "news-api14.p.rapidapi.com",
        "base_url": "https://news-api14.p.rapidapi.com",
        "search": "/v2/search/publishers",
    },
    "stock_sentiment": {
        "host": "stock-sentiment-analysis.p.rapidapi.com", 
        "base_url": "https://stock-sentiment-analysis.p.rapidapi.com",
        "news": "/stock/{symbol}/news",
    },
}

class NewsAPIClient:
    """Client for fetching financial news from multiple API sources"""
    
    def __init__(self, api_key: str = None, cache_dir: str = "cache"):
        """Initialize the News API client
        
        Args:
            api_key: RapidAPI key (defaults to value from environment)
            cache_dir: Directory to store cached responses
        """
        self.api_key = api_key or API_KEYS.get("rapid_api")
        self.cache_dir = cache_dir
        self.cache_duration = 1800  # 30 minutes in seconds
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        logger.info("NewsAPIClient initialized")
    
    def _get_cache_path(self, endpoint: str, params: Dict) -> str:
        """Get the cache file path for a specific request
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            
        Returns:
            Path to the cache file
        """
        # Create a unique cache key based on endpoint and params
        param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
        endpoint_key = endpoint.replace("/", "_")
        cache_key = f"{endpoint_key}_{param_str}"
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if the cache is still valid
        
        Args:
            cache_path: Path to the cache file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not os.path.exists(cache_path):
            return False
        
        # Check if the cache file is not expired
        file_mtime = os.path.getmtime(cache_path)
        age = time.time() - file_mtime
        return age < self.cache_duration
    
    def _request(self, 
                 endpoint_key: str, 
                 path: str, 
                 params: Dict = None, 
                 use_cache: bool = True) -> Dict:
        """Make an API request
        
        Args:
            endpoint_key: Key for the endpoint configuration
            path: API path to request
            params: Query parameters
            use_cache: Whether to use cached responses
            
        Returns:
            API response as a dictionary
        """
        endpoint_config = ENDPOINTS.get(endpoint_key)
        if not endpoint_config:
            raise ValueError(f"Unknown endpoint key: {endpoint_key}")
        
        # Merge path with any provided path parameters
        if params and any(key in path for key in params):
            for key, value in params.items():
                if '{' + key + '}' in path:
                    path = path.replace('{' + key + '}', str(value))
            
            # Remove used params from the query parameters
            params = {k: v for k, v in params.items() if '{' + k + '}' not in path}
        
        url = f"{endpoint_config['base_url']}{path}"
        
        # Check cache if enabled
        if use_cache:
            cache_path = self._get_cache_path(path, params or {})
            if self._is_cache_valid(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        logger.debug(f"Using cached response for {url}")
                        return json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Error reading cache: {e}")
        
        # Prepare headers
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": endpoint_config['host']
        }
        
        # Make the request
        try:
            logger.debug(f"Making request to {url}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            try:
                data = response.json()
                
                # Save to cache if enabled
                if use_cache:
                    cache_path = self._get_cache_path(path, params or {})
                    with open(cache_path, 'w') as f:
                        json.dump(data, f)
                
                return data
            except ValueError:
                logger.error("Failed to parse JSON response")
                return {"error": "Invalid JSON response"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}
    
    def get_reuters_business_news(self) -> List[Dict]:
        """Fetch the latest Reuters business news
        
        Returns:
            List of news articles
        """
        path = ENDPOINTS["reuters_business"]["list_rics"]
        data = self._request("reuters_business", path)
        
        if "error" in data:
            logger.error(f"Failed to fetch Reuters business news: {data['error']}")
            return []
        
        # Process and return the articles
        try:
            # Adjust this based on actual API response structure
            if isinstance(data, dict) and "rics" in data:
                return data["rics"]
            elif isinstance(data, list):
                return data
            else:
                logger.warning("Unexpected Reuters business news format")
                return []
        except Exception as e:
            logger.error(f"Error processing Reuters business news: {e}")
            return []
    
    def get_reuters_africa_news(self) -> List[Dict]:
        """Fetch the latest Reuters Africa news
        
        Returns:
            List of news articles from Africa
        """
        path = ENDPOINTS["reuters"]["category"]
        params = {"url": "https://www.reuters.com/world/africa/"}
        data = self._request("reuters", path, params)
        
        if "error" in data:
            logger.error(f"Failed to fetch Reuters Africa news: {data['error']}")
            return []
        
        # Process and return the articles
        try:
            # Adjust based on actual API response structure
            if isinstance(data, dict) and "articles" in data:
                return data["articles"]
            elif isinstance(data, list):
                return data
            else:
                logger.warning("Unexpected Reuters Africa news format")
                return []
        except Exception as e:
            logger.error(f"Error processing Reuters Africa news: {e}")
            return []
    
    def get_financial_news(self, 
                          query: str = "finance", 
                          days: int = 7,
                          sources: List[str] = None,
                          count: int = 10) -> List[Dict]:
        """Get financial news from multiple sources
        
        Args:
            query: Search query
            days: Number of days to look back
            sources: List of news sources to search (defaults to financial sources)
            count: Number of articles to return
            
        Returns:
            List of news articles matching the criteria
        """
        # Default financial sources
        if sources is None:
            sources = [
                "bloomberg", "cnbc", "financial-times", "wall-street-journal",
                "business-insider", "reuters", "the-economist", "bbc-news"
            ]
        
        params = {
            "q": query,
            "sources": ",".join(sources),
            "count": count
        }
        
        # Add date restriction if needed
        if days > 0:
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            params["from"] = from_date
        
        path = ENDPOINTS["news_api"]["search"]
        data = self._request("news_api", path, params)
        
        if "error" in data:
            logger.error(f"Failed to fetch financial news: {data['error']}")
            return []
        
        # Process and return the articles
        try:
            # Adjust based on actual API response structure
            if isinstance(data, dict) and "articles" in data:
                return data["articles"]
            elif isinstance(data, list):
                return data
            else:
                logger.warning("Unexpected news API format")
                return []
        except Exception as e:
            logger.error(f"Error processing news API response: {e}")
            return []
    
    def get_stock_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for a specific stock
        
        Args:
            symbol: Stock symbol (e.g., "SCOM" for Safaricom)
            
        Returns:
            Dictionary with sentiment analysis results
        """
        path = ENDPOINTS["stock_sentiment"]["news"]
        params = {"symbol": symbol}
        data = self._request("stock_sentiment", path, params)
        
        if "error" in data:
            logger.error(f"Failed to fetch stock sentiment for {symbol}: {data['error']}")
            return {"symbol": symbol, "sentiment": "neutral", "articles": []}
        
        # Process and return the sentiment data
        try:
            # This should be adjusted based on the actual API response
            if isinstance(data, dict):
                return data
            else:
                logger.warning(f"Unexpected stock sentiment format for {symbol}")
                return {"symbol": symbol, "sentiment": "neutral", "articles": []}
        except Exception as e:
            logger.error(f"Error processing stock sentiment for {symbol}: {e}")
            return {"symbol": symbol, "sentiment": "neutral", "articles": []}
    
    def get_kenyan_financial_news(self, days: int = 7, count: int = 10) -> List[Dict]:
        """Get financial news specific to Kenya
        
        Args:
            days: Number of days to look back
            count: Number of articles to return
            
        Returns:
            List of news articles about Kenyan finance and business
        """
        queries = [
            "Kenya finance", 
            "Nairobi Stock Exchange", 
            "NSE Kenya", 
            "Kenya economy",
            "Kenya business",
            "Safaricom",
            "Kenya Central Bank",
            "Kenya banking",
            "Kenya investment"
        ]
        
        all_articles = []
        for query in queries:
            articles = self.get_financial_news(
                query=query,
                days=days,
                count=count // len(queries) + 1  # Distribute the count
            )
            all_articles.extend(articles)
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Sort by date (newest first) and limit to requested count
        sorted_articles = sorted(
            unique_articles, 
            key=lambda x: x.get("publishedAt", ""), 
            reverse=True
        )
        return sorted_articles[:count]
    
    def get_nse_stock_news(self, stock_code: str) -> List[Dict]:
        """Get news related to a specific NSE stock
        
        Args:
            stock_code: NSE stock code (e.g., "SCOM" for Safaricom)
            
        Returns:
            List of news articles about the stock
        """
        # Map of NSE stock codes to company names
        nse_stocks = {
            "SCOM": "Safaricom",
            "KCB": "KCB Group",
            "EQTY": "Equity Group",
            "COOP": "Co-operative Bank",
            "SBIC": "Stanbic Holdings",
            "ABSA": "Absa Bank Kenya",
            "BAT": "British American Tobacco Kenya",
            "EABL": "East African Breweries",
            "KNRE": "Kenya Re",
            "JUB": "Jubilee Holdings",
            "NSE": "Nairobi Securities Exchange",
            "CARB": "Carbacid Investments",
            "SASN": "Sasini",
            "UNGA": "Unga Group",
            "CFCI": "Car & General",
        }
        
        # Get the company name if it exists, otherwise use the stock code
        company_name = nse_stocks.get(stock_code, stock_code)
        
        # Build queries to cover different ways the company might be mentioned
        queries = [
            f"{company_name} Kenya",
            f"{stock_code} stock",
            f"{company_name} financial results",
            f"{company_name} NSE",
        ]
        
        all_articles = []
        for query in queries:
            articles = self.get_financial_news(
                query=query,
                days=30,  # Look back further for specific stocks
                count=5  # Few articles per query
            )
            all_articles.extend(articles)
        
        # Remove duplicates
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        # Sort by date and relevance (articles explicitly mentioning stock code first)
        def relevance_key(article):
            title = article.get("title", "").upper()
            content = article.get("content", "").upper()
            
            # Check if stock code is mentioned
            stock_mentioned = stock_code.upper() in title or stock_code.upper() in content
            
            # Check if company name is mentioned
            company_mentioned = company_name.upper() in title or company_name.upper() in content
            
            # Calculate relevance score
            score = 0
            if stock_mentioned:
                score += 3
            if company_mentioned:
                score += 2
            if stock_mentioned and company_mentioned:
                score += 1
                
            # Return tuple for sorting (relevance, date)
            return (score, article.get("publishedAt", ""))
        
        sorted_articles = sorted(unique_articles, key=relevance_key, reverse=True)
        return sorted_articles[:10]  # Return top 10 most relevant articles
    
    def process_news_for_chatbot(self, news_items: List[Dict]) -> List[Dict]:
        """Process news items for use by the chatbot
        
        Args:
            news_items: Raw news items
        
        Returns:
            Processed news items suitable for chatbot responses
        """
        processed_news = []
        
        for item in news_items:
            if not item:
                continue
                
            # Extract relevant fields
            processed_item = {
                "title": item.get("title", ""),
                "description": item.get("description", "").strip(),
                "source": item.get("source", {}).get("name", "Unknown"),
                "url": item.get("url", ""),
                "date": item.get("publishedAt", "")
            }
            
            # Clean up and truncate description if needed
            if processed_item["description"] and len(processed_item["description"]) > 150:
                processed_item["description"] = processed_item["description"][:147] + "..."
            
            # Format date
            if processed_item["date"]:
                try:
                    date_obj = datetime.fromisoformat(processed_item["date"].replace("Z", "+00:00"))
                    processed_item["date"] = date_obj.strftime("%d %b %Y")
                except (ValueError, TypeError):
                    pass
            
            processed_news.append(processed_item)
        
        return processed_news
    
    def format_news_markdown(self, news_items: List[Dict], title: str = "Financial News") -> str:
        """Format news items as markdown for chatbot responses
        
        Args:
            news_items: Processed news items
            title: Title for the news section
            
        Returns:
            Markdown-formatted news content
        """
        if not news_items:
            return f"# {title}\nNo news items available at this time."
        
        markdown = f"# {title}\n\n"
        
        for i, item in enumerate(news_items[:5], 1):  # Limit to 5 items
            markdown += f"### {i}. {item.get('title')}\n"
            
            if item.get("description"):
                markdown += f"{item.get('description')}\n"
                
            source_date = []
            if item.get("source"):
                source_date.append(f"Source: {item.get('source')}")
            if item.get("date"):
                source_date.append(f"Date: {item.get('date')}")
                
            if source_date:
                markdown += f"*{' | '.join(source_date)}*\n"
                
            if item.get("url"):
                markdown += f"[Read more]({item.get('url')})\n"
                
            markdown += "\n---\n\n"
        
        return markdown


def main():
    """Test function to demonstrate the NewsAPIClient"""
    client = NewsAPIClient()
    
    # Get general financial news
    print("Fetching general financial news...")
    financial_news = client.get_financial_news(query="kenya finance", count=5)
    processed_news = client.process_news_for_chatbot(financial_news)
    markdown = client.format_news_markdown(processed_news, "Latest Financial News")
    print(markdown)
    
    # Get news about a specific stock
    print("\nFetching news about Safaricom...")
    stock_news = client.get_nse_stock_news("SCOM")
    processed_stock_news = client.process_news_for_chatbot(stock_news)
    stock_markdown = client.format_news_markdown(processed_stock_news, "Safaricom (SCOM) News")
    print(stock_markdown)


if __name__ == "__main__":
    main()
