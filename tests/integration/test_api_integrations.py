import os
import sys
import time
import json
import statistics
import requests
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import psutil
import logging
from functools import wraps
from typing import Dict, List, Tuple, Any, Callable

# Add the project root to the path to be able to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("performance_test_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("performance_tests")

# Base API URL - can be overridden with environment variable
BASE_URL = os.getenv('PESAGURU_API_URL', 'http://localhost:8000/api')

# Test configuration
DEFAULT_TEST_CONFIG = {
    'num_requests': 100,           # Number of requests to make for each test
    'concurrency': 10,             # Maximum number of concurrent requests
    'warmup_requests': 5,          # Number of warmup requests before measuring
    'test_duration': 60,           # Duration in seconds for endurance tests
    'ramp_up_time': 5,             # Time in seconds to ramp up to full load
    'acceptable_response_time': 1.0,  # Maximum acceptable response time in seconds
    'target_rps': 10,              # Target requests per second for load testing
    'test_user': {
        'email': 'performance_test@example.com',
        'password': 'Performance@123'
    }
}


def timed(func):
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        return result, duration
    return wrapper


class PerformanceTestRunner:
    """Base class for running performance tests"""
    
    def __init__(self, config=None):
        """Initialize with test configuration"""
        self.config = config or DEFAULT_TEST_CONFIG
        self.auth_token = None
        self.test_results = {}
        
    def setup(self):
        """Set up the test environment"""
        # Authenticate and get token
        self.authenticate()
        
    def authenticate(self):
        """Authenticate with the API and get JWT token"""
        try:
            auth_url = f"{BASE_URL}/auth/login"
            response = requests.post(
                auth_url,
                json=self.config['test_user'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.auth_token = response.json().get('token')
                logger.info("Authentication successful")
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
    
    def get_headers(self):
        """Get headers with authentication token"""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            
        return headers
    
    @timed
    def make_request(self, url, method='GET', data=None):
        """Make an HTTP request and measure time"""
        try:
            headers = self.get_headers()
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return None
    
    def run_single_endpoint_test(self, endpoint, method='GET', data=None, description=None):
        """Test a single API endpoint's performance"""
        url = f"{BASE_URL}/{endpoint}"
        test_name = description or f"{method} {endpoint}"
        logger.info(f"Testing endpoint: {test_name}")
        
        # Warmup
        logger.info("Performing warmup requests...")
        for _ in range(self.config['warmup_requests']):
            self.make_request(url, method, data)
        
        # Main test
        durations = []
        statuses = []
        
        logger.info(f"Running test with {self.config['num_requests']} requests...")
        for i in range(self.config['num_requests']):
            response, duration = self.make_request(url, method, data)
            durations.append(duration)
            
            if response:
                statuses.append(response.status_code)
                
            if i % max(1, self.config['num_requests'] // 10) == 0:
                logger.info(f"Completed {i} of {self.config['num_requests']} requests")
        
        # Calculate statistics
        success_rate = statuses.count(200) / len(statuses) if statuses else 0
        
        results = {
            'endpoint': endpoint,
            'method': method,
            'description': test_name,
            'total_requests': len(durations),
            'success_rate': success_rate,
            'min_response_time': min(durations) if durations else None,
            'max_response_time': max(durations) if durations else None,
            'mean_response_time': statistics.mean(durations) if durations else None,
            'median_response_time': statistics.median(durations) if durations else None,
            'p95_response_time': np.percentile(durations, 95) if durations else None,
            'status_codes': {code: statuses.count(code) for code in set(statuses)} if statuses else None
        }
        
        # Store results
        self.test_results[test_name] = results
        
        # Log results
        logger.info(f"Results for {test_name}:")
        logger.info(f"  Success rate: {success_rate:.2%}")
        logger.info(f"  Mean response time: {results['mean_response_time']:.4f} seconds")
        logger.info(f"  95th percentile: {results['p95_response_time']:.4f} seconds")
        
        # Check if performance is acceptable
        is_acceptable = results['p95_response_time'] <= self.config['acceptable_response_time']
        logger.info(f"  Performance {'ACCEPTABLE' if is_acceptable else 'POOR'}")
        
        return results
    
    def run_concurrent_test(self, endpoint, method='GET', data=None, description=None):
        """Test an endpoint with concurrent requests"""
        url = f"{BASE_URL}/{endpoint}"
        test_name = description or f"Concurrent {method} {endpoint}"
        logger.info(f"Testing endpoint with concurrency: {test_name}")
        
        # Function for concurrent execution
        def make_request_task():
            response, duration = self.make_request(url, method, data)
            status_code = response.status_code if response else None
            return {'duration': duration, 'status_code': status_code}
        
        # Warmup
        logger.info("Performing warmup requests...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda _: make_request_task(), range(self.config['warmup_requests'])))
        
        # Main test
        results = []
        logger.info(f"Running concurrent test with {self.config['num_requests']} requests...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['concurrency']) as executor:
            futures = [executor.submit(make_request_task) for _ in range(self.config['num_requests'])]
            
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                results.append(future.result())
                if i % max(1, self.config['num_requests'] // 10) == 0:
                    logger.info(f"Completed {i} of {self.config['num_requests']} requests")
        
        # Calculate statistics
        durations = [r['duration'] for r in results]
        statuses = [r['status_code'] for r in results if r['status_code'] is not None]
        success_rate = statuses.count(200) / len(statuses) if statuses else 0
        
        test_results = {
            'endpoint': endpoint,
            'method': method,
            'description': test_name,
            'concurrency': self.config['concurrency'],
            'total_requests': len(results),
            'success_rate': success_rate,
            'min_response_time': min(durations) if durations else None,
            'max_response_time': max(durations) if durations else None,
            'mean_response_time': statistics.mean(durations) if durations else None,
            'median_response_time': statistics.median(durations) if durations else None,
            'p95_response_time': np.percentile(durations, 95) if durations else None,
            'throughput': len(results) / sum(durations) if durations else None,  # requests per second
            'status_codes': {code: statuses.count(code) for code in set(statuses)} if statuses else None
        }
        
        # Store results
        self.test_results[test_name] = test_results
        
        # Log results
        logger.info(f"Concurrent test results for {test_name}:")
        logger.info(f"  Success rate: {success_rate:.2%}")
        logger.info(f"  Mean response time: {test_results['mean_response_time']:.4f} seconds")
        logger.info(f"  95th percentile: {test_results['p95_response_time']:.4f} seconds")
        logger.info(f"  Throughput: {test_results['throughput']:.2f} requests/second")
        
        return test_results
    
    def run_load_test(self, endpoint, method='GET', data=None, description=None, duration=None):
        """Run a load test for a specified duration with gradually increasing load"""
        duration = duration or self.config['test_duration']
        url = f"{BASE_URL}/{endpoint}"
        test_name = description or f"Load test {method} {endpoint}"
        logger.info(f"Running load test for {test_name} for {duration} seconds")
        
        results = []
        start_time = time.time()
        end_time = start_time + duration
        
        # Monitor system resources
        cpu_usage = []
        memory_usage = []
        
        # Execute requests until the test duration is reached
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['concurrency']) as executor:
            futures = []
            request_times = []
            
            while time.time() < end_time:
                # Calculate current target RPS based on ramp-up time
                elapsed = time.time() - start_time
                if elapsed < self.config['ramp_up_time']:
                    target_rps = self.config['target_rps'] * (elapsed / self.config['ramp_up_time'])
                else:
                    target_rps = self.config['target_rps']
                
                # Submit new requests to maintain the target RPS
                current_time = time.time()
                if not request_times or current_time - request_times[-1] >= 1.0 / target_rps:
                    futures.append(executor.submit(self.make_request, url, method, data))
                    request_times.append(current_time)
                
                # Get results from completed futures
                done, not_done = concurrent.futures.wait(
                    futures, timeout=0.1, 
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                for future in done:
                    try:
                        response, duration = future.result()
                        status_code = response.status_code if response else None
                        results.append({
                            'duration': duration, 
                            'status_code': status_code,
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        logger.error(f"Error in load test: {str(e)}")
                
                futures = list(not_done)
                
                # Monitor system resources every second
                if int(elapsed) > int(elapsed - 0.1):  # approximately every second
                    cpu_usage.append(psutil.cpu_percent())
                    memory_usage.append(psutil.virtual_memory().percent)
        
        # Wait for remaining futures to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                response, duration = future.result()
                status_code = response.status_code if response else None
                results.append({
                    'duration': duration, 
                    'status_code': status_code,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Error in load test: {str(e)}")
        
        # Calculate statistics
        durations = [r['duration'] for r in results]
        statuses = [r['status_code'] for r in results if r['status_code'] is not None]
        success_rate = statuses.count(200) / len(statuses) if statuses else 0
        
        # Calculate throughput over time (requests per second)
        if results:
            timestamps = [r['timestamp'] for r in results]
            min_timestamp = min(timestamps)
            max_timestamp = max(timestamps)
            total_time = max_timestamp - min_timestamp
            throughput = len(results) / total_time if total_time > 0 else 0
        else:
            throughput = 0
        
        test_results = {
            'endpoint': endpoint,
            'method': method,
            'description': test_name,
            'concurrency': self.config['concurrency'],
            'total_requests': len(results),
            'success_rate': success_rate,
            'min_response_time': min(durations) if durations else None,
            'max_response_time': max(durations) if durations else None,
            'mean_response_time': statistics.mean(durations) if durations else None,
            'median_response_time': statistics.median(durations) if durations else None,
            'p95_response_time': np.percentile(durations, 95) if durations else None,
            'throughput': throughput,  # requests per second
            'status_codes': {code: statuses.count(code) for code in set(statuses)} if statuses else None,
            'avg_cpu_usage': statistics.mean(cpu_usage) if cpu_usage else None,
            'avg_memory_usage': statistics.mean(memory_usage) if memory_usage else None,
            'peak_cpu_usage': max(cpu_usage) if cpu_usage else None,
            'peak_memory_usage': max(memory_usage) if memory_usage else None
        }
        
        # Store results
        self.test_results[test_name] = test_results
        
        # Log results
        logger.info(f"Load test results for {test_name}:")
        logger.info(f"  Total requests: {len(results)}")
        logger.info(f"  Success rate: {success_rate:.2%}")
        logger.info(f"  Mean response time: {test_results['mean_response_time']:.4f} seconds")
        logger.info(f"  95th percentile: {test_results['p95_response_time']:.4f} seconds")
        logger.info(f"  Throughput: {throughput:.2f} requests/second")
        logger.info(f"  Avg CPU usage: {test_results['avg_cpu_usage']:.2f}%")
        logger.info(f"  Avg memory usage: {test_results['avg_memory_usage']:.2f}%")
        
        return test_results
    
    def generate_performance_report(self, output_dir='performance_reports'):
        """Generate a performance report with charts and summary"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f'performance_report_{timestamp}.html')
        
        # Create HTML report
        with open(report_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>PesaGuru Performance Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .charts {{ display: flex; flex-wrap: wrap; }}
        .chart {{ margin: 10px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>PesaGuru Performance Test Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Summary</h2>
    <table>
        <tr>
            <th>Test</th>
            <th>Requests</th>
            <th>Success Rate</th>
            <th>Mean Response Time (s)</th>
            <th>95th Percentile (s)</th>
            <th>Throughput (req/s)</th>
            <th>Status</th>
        </tr>
""")
            
            # Add summary rows
            for test_name, results in self.test_results.items():
                status_class = 'success'
                if results.get('p95_response_time', 0) > self.config['acceptable_response_time']:
                    status_class = 'warning'
                if results.get('success_rate', 1) < 0.9:  # Less than 90% success
                    status_class = 'error'
                
                f.write(f"""
        <tr>
            <td>{test_name}</td>
            <td>{results.get('total_requests', 'N/A')}</td>
            <td>{results.get('success_rate', 0):.2%}</td>
            <td>{results.get('mean_response_time', 'N/A'):.4f}</td>
            <td>{results.get('p95_response_time', 'N/A'):.4f}</td>
            <td>{results.get('throughput', 'N/A'):.2f if results.get('throughput') else 'N/A'}</td>
            <td class="{status_class}">{
                'GOOD' if status_class == 'success' else
                'WARNING' if status_class == 'warning' else
                'POOR'
            }</td>
        </tr>""")
            
            f.write("""
    </table>
    
    <h2>Detailed Results</h2>
""")
            
            # Add detailed sections for each test
            for test_name, results in self.test_results.items():
                f.write(f"""
    <h3>{test_name}</h3>
    <table>
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Endpoint</td><td>{results.get('endpoint', 'N/A')}</td></tr>
        <tr><td>Method</td><td>{results.get('method', 'N/A')}</td></tr>
        <tr><td>Total Requests</td><td>{results.get('total_requests', 'N/A')}</td></tr>
        <tr><td>Success Rate</td><td>{results.get('success_rate', 0):.2%}</td></tr>
        <tr><td>Min Response Time</td><td>{results.get('min_response_time', 'N/A'):.4f} s</td></tr>
        <tr><td>Max Response Time</td><td>{results.get('max_response_time', 'N/A'):.4f} s</td></tr>
        <tr><td>Mean Response Time</td><td>{results.get('mean_response_time', 'N/A'):.4f} s</td></tr>
        <tr><td>Median Response Time</td><td>{results.get('median_response_time', 'N/A'):.4f} s</td></tr>
        <tr><td>95th Percentile</td><td>{results.get('p95_response_time', 'N/A'):.4f} s</td></tr>
        <tr><td>Throughput</td><td>{results.get('throughput', 'N/A'):.2f if results.get('throughput') else 'N/A'} req/s</td></tr>
""")
                
                # Add resource usage if available
                if 'avg_cpu_usage' in results:
                    f.write(f"""
        <tr><td>Average CPU Usage</td><td>{results.get('avg_cpu_usage', 'N/A'):.2f}%</td></tr>
        <tr><td>Peak CPU Usage</td><td>{results.get('peak_cpu_usage', 'N/A'):.2f}%</td></tr>
        <tr><td>Average Memory Usage</td><td>{results.get('avg_memory_usage', 'N/A'):.2f}%</td></tr>
        <tr><td>Peak Memory Usage</td><td>{results.get('peak_memory_usage', 'N/A'):.2f}%</td></tr>
""")
                
                # Add status code distribution
                if results.get('status_codes'):
                    f.write(f"""
        <tr><td>Status Codes</td><td>""")
                    for code, count in results['status_codes'].items():
                        f.write(f"{code}: {count} ({count/results['total_requests']:.2%})<br>")
                    f.write("""</td></tr>
""")
                
                f.write("""
    </table>
""")
            
            # Close the HTML
            f.write("""
    <h2>Test Configuration</h2>
    <table>
""")
            for key, value in self.config.items():
                if key != 'test_user':  # Skip sensitive information
                    f.write(f"<tr><td>{key}</td><td>{value}</td></tr>\n")
            
            f.write("""
    </table>
</body>
</html>
""")
        
        logger.info(f"Performance report generated: {report_file}")
        return report_file
    
    def plot_results(self, output_dir='performance_reports'):
        """Generate performance charts"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Response time comparison chart
        plt.figure(figsize=(12, 6))
        
        test_names = list(self.test_results.keys())
        mean_times = [results.get('mean_response_time', 0) for results in self.test_results.values()]
        p95_times = [results.get('p95_response_time', 0) for results in self.test_results.values()]
        
        x = np.arange(len(test_names))
        width = 0.35
        
        plt.bar(x - width/2, mean_times, width, label='Mean Response Time')
        plt.bar(x + width/2, p95_times, width, label='95th Percentile')
        
        plt.axhline(y=self.config['acceptable_response_time'], color='r', linestyle='-', label='Acceptable Threshold')
        
        plt.xlabel('Test')
        plt.ylabel('Response Time (s)')
        plt.title('API Response Time Comparison')
        plt.xticks(x, [name[:20] + '...' if len(name) > 20 else name for name in test_names], rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        # Save the chart
        chart_file = os.path.join(output_dir, f'response_time_comparison_{timestamp}.png')
        plt.savefig(chart_file)
        plt.close()
        
        # Throughput comparison chart (if available)
        throughputs = [results.get('throughput', 0) for results in self.test_results.values()]
        if any(throughputs):
            plt.figure(figsize=(12, 6))
            plt.bar(x, throughputs)
            plt.xlabel('Test')
            plt.ylabel('Throughput (req/s)')
            plt.title('API Throughput Comparison')
            plt.xticks(x, [name[:20] + '...' if len(name) > 20 else name for name in test_names], rotation=45, ha='right')
            plt.tight_layout()
            
            throughput_file = os.path.join(output_dir, f'throughput_comparison_{timestamp}.png')
            plt.savefig(throughput_file)
            plt.close()
        
        logger.info(f"Performance charts generated in: {output_dir}")


class PesaGuruPerformanceTests(PerformanceTestRunner):
    """Specific performance tests for PesaGuru application"""
    
    def run_api_performance_tests(self):
        """Run performance tests for key API endpoints"""
        # Test user authentication
        self.run_single_endpoint_test(
            endpoint="auth/login",
            method="POST",
            data=self.config['test_user'],
            description="User Login"
        )
        
        # Test stock data retrieval
        self.run_single_endpoint_test(
            endpoint="market-data/stocks/SCOM",
            description="Stock Data - Safaricom"
        )
        
        # Test market sector data
        self.run_single_endpoint_test(
            endpoint="market-data/sectors",
            description="Market Sectors"
        )
        
        # Test financial calculator
        self.run_single_endpoint_test(
            endpoint="calculators/investment",
            method="POST",
            data={
                "initial_investment": 10000,
                "monthly_contribution": 1000,
                "years": 10,
                "interest_rate": 8
            },
            description="Investment Calculator"
        )
        
        # Test concurrent stock data retrieval
        self.run_concurrent_test(
            endpoint="market-data/stocks/top-performers",
            description="Top Performing Stocks (Concurrent)"
        )
        
        # Test chatbot API
        self.run_concurrent_test(
            endpoint="chatbot/message",
            method="POST",
            data={
                "message": "What are the best investment options in Kenya?",
                "context": {}
            },
            description="Chatbot Financial Query (Concurrent)"
        )
        
    def run_chatbot_performance_tests(self):
        """Run performance tests specifically for the chatbot functionality"""
        # Test different types of financial queries
        simple_queries = [
            "What is the current exchange rate?",
            "Show me today's stock market updates",
            "What's the interest rate for savings accounts?",
            "How do I create a budget?",
            "What is a mutual fund?"
        ]
        
        complex_queries = [
            "I earn 80,000 KES per month, have 20,000 KES in savings, and want to invest in stocks. What would you recommend?",
            "Compare investing in NSE stocks versus treasury bonds for a 5-year investment horizon",
            "Create a retirement plan for me assuming I'm 35 years old with 500,000 KES saved and can save 15,000 KES monthly",
            "Analyze the performance of Safaricom stock over the last 3 years and give investment recommendations",
            "What's the best way to diversify a 1 million KES investment portfolio in Kenya?"
        ]
        
        # Test simple queries
        for i, query in enumerate(simple_queries):
            self.run_single_endpoint_test(
                endpoint="chatbot/message",
                method="POST",
                data={"message": query, "context": {}},
                description=f"Simple Financial Query {i+1}"
            )
        
        # Test complex queries
        for i, query in enumerate(complex_queries):
            self.run_single_endpoint_test(
                endpoint="chatbot/message",
                method="POST",
                data={"message": query, "context": {}},
                description=f"Complex Financial Query {i+1}"
            )
        
        # Load test the chatbot with mixed queries
        all_queries = simple_queries + complex_queries
        
        # Function to generate random query data
        def get_random_query():
            import random
            query = random.choice(all_queries)
            return {"message": query, "context": {}}
        
        # Run load test with randomly selected queries
        self.run_load_test(
            endpoint="chatbot/message",
            method="POST",
            data=get_random_query(),
            description="Chatbot Load Test"
        )
    
    def run_database_performance_tests(self):
        """Run performance tests for database operations"""
        # Test portfolio creation
        portfolio_data = {
            "name": "Test Performance Portfolio",
            "risk_level": "medium",
            "stocks": [
                {"symbol": "SCOM", "allocation": 30},
                {"symbol": "EQTY", "allocation": 30},
                {"symbol": "KCB", "allocation": 20},
                {"symbol": "SBIC", "allocation": 20}
            ],
            "investment_amount": 100000
        }
        
        self.run_single_endpoint_test(
            endpoint="portfolio/create",
            method="POST",
            data=portfolio_data,
            description="Portfolio Creation"
        )
        
        # Test user profile update
        profile_data = {
            "financial_goals": [
                {"type": "retirement", "target_amount": 5000000, "target_date": "2050-01-01"},
                {"type": "education", "target_amount": 1000000, "target_date": "2030-01-01"}
            ],
            "risk_tolerance": "moderate",
            "income": 100000,
            "expenses": 70000,
            "savings": 30000
        }
        
        self.run_single_endpoint_test(
            endpoint="user/profile/update",
            method="PUT",
            data=profile_data,
            description="User Profile Update"
        )
        
        # Test financial goal creation with concurrent users
        goal_data = {
            "type": "home_purchase",
            "target_amount": 5000000,
            "target_date": "2030-01-01",
            "monthly_contribution": 20000,
            "current_savings": 500000
        }
        
        self.run_concurrent_test(
            endpoint="financial-goals/create",
            method="POST",
            data=goal_data,
            description="Financial Goal Creation (Concurrent)"
        )
    
    def run_all_tests(self):
        """Run all performance tests"""
        logger.info("Starting PesaGuru comprehensive performance tests")
        
        # Setup test
        self.setup()
        
        # Run all test categories
        self.run_api_performance_tests()
        self.run_chatbot_performance_tests()
        self.run_database_performance_tests()
        
        # Generate report
        report_file = self.generate_performance_report()
        self.plot_results()
        
        logger.info(f"All performance tests completed. Report: {report_file}")
        
        return self.test_results


def main():
    """Run all performance tests and generate report"""
    # Parse command-line arguments if needed
    import argparse
    parser = argparse.ArgumentParser(description='Run PesaGuru Performance Tests')
    parser.add_argument('--api-url', type=str, help='Base API URL')
    parser.add_argument('--num-requests', type=int, help='Number of requests per test')
    parser.add_argument('--concurrency', type=int, help='Number of concurrent requests')
    parser.add_argument('--output-dir', type=str, default='performance_reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Create custom config if arguments provided
    config = DEFAULT_TEST_CONFIG.copy()
    if args.api_url:
        global BASE_URL
        BASE_URL = args.api_url
    if args.num_requests:
        config['num_requests'] = args.num_requests
    if args.concurrency:
        config['concurrency'] = args.concurrency
    
    # Run tests
    test_runner = PesaGuruPerformanceTests(config)
    results = test_runner.run_all_tests()
    
    # Generate report
    report_file = test_runner.generate_performance_report(args.output_dir)
    test_runner.plot_results(args.output_dir)
    
    # Print summary
    print("\n=== Performance Test Summary ===")
    print(f"Total Tests Run: {len(results)}")
    print(f"Report Generated: {report_file}")
    print("===============================\n")


if __name__ == "__main__":
    main()