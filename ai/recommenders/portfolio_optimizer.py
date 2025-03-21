import numpy as np
import pandas as pd
import scipy.optimize as sco
import matplotlib.pyplot as plt
from sklearn.covariance import LedoitWolf
import logging
import json
import sys
import os

# Add the parent directory to sys.path to import other PesaGuru modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import PesaGuru modules
from services.market_data_api import MarketDataAPI
from services.risk_evaluation import RiskEvaluator
from services.user_profiler import UserProfiler
from api_integration.nse_api import NSEAPI
from api_integration.cbk_api import CBKAPI
from api_integration.crypto_api import CryptoAPI
from api_integration.forex_api import ForexAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("portfolio_optimizer")


class PortfolioOptimizer:
    """
    A class to optimize investment portfolios using various financial theories and models,
    adapted for the Kenyan market context.
    """

    def __init__(self, user_id=None, risk_profile=None):
        """
        Initialize the Portfolio Optimizer with user data and external APIs.

        Args:
            user_id (str, optional): User identifier for personalized optimization
            risk_profile (dict, optional): Pre-defined risk profile (if available)
        """
        self.user_id = user_id
        self.risk_profile = risk_profile
        
        # Initialize API connections
        self.market_data = MarketDataAPI()
        self.risk_evaluator = RiskEvaluator()
        self.user_profiler = UserProfiler()
        
        # Initialize Kenya-specific APIs
        self.nse_api = NSEAPI()
        self.cbk_api = CBKAPI()
        self.crypto_api = CryptoAPI()
        self.forex_api = ForexAPI()
        
        # Default optimization parameters
        self.min_return = 0.05  # 5% minimum annual return
        self.max_risk = 0.25    # 25% maximum risk (std dev)
        self.investment_horizon = 5  # 5 years default
        
        logger.info(f"Portfolio Optimizer initialized for user {user_id}")

    def load_user_preferences(self, user_id=None):
        """
        Load user financial preferences and risk profile from the database.
        
        Args:
            user_id (str, optional): User identifier to load data for
            
        Returns:
            dict: User preferences and risk profile
        """
        if user_id:
            self.user_id = user_id
            
        # Skip if no user_id is provided
        if not self.user_id:
            logger.warning("No user_id provided, using default parameters")
            return {
                "risk_tolerance": "moderate",
                "investment_horizon": 5,
                "financial_goals": ["general_investment"],
                "preferred_sectors": ["technology", "finance", "energy"],
                "excluded_sectors": [],
                "preferred_asset_classes": ["stocks", "bonds", "money_market"],
                "max_allocation_per_asset": 0.25
            }
        
        # Load user profile and risk assessment from the database
        user_profile = self.user_profiler.get_user_profile(self.user_id)
        risk_profile = self.risk_evaluator.get_risk_profile(self.user_id)
        
        # Combine and return user preferences
        preferences = {**user_profile, **risk_profile}
        
        # Set attributes from preferences
        self.investment_horizon = preferences.get("investment_horizon", 5)
        
        # Set risk parameters based on risk tolerance
        risk_tolerance = preferences.get("risk_tolerance", "moderate")
        if risk_tolerance == "conservative":
            self.min_return = 0.04
            self.max_risk = 0.12
        elif risk_tolerance == "moderate":
            self.min_return = 0.06
            self.max_risk = 0.20
        elif risk_tolerance == "aggressive":
            self.min_return = 0.08
            self.max_risk = 0.30
            
        logger.info(f"Loaded preferences for user {self.user_id}: {risk_tolerance} profile")
        return preferences

    def fetch_market_data(self, assets=None, period="5y", frequency="monthly"):
        """
        Fetch historical market data for the specified assets.
        
        Args:
            assets (list, optional): List of asset identifiers
            period (str, optional): Lookback period ('1y', '3y', '5y')
            frequency (str, optional): Data frequency ('daily', 'weekly', 'monthly')
            
        Returns:
            pandas.DataFrame: Historical returns data
        """
        if assets is None:
            # Default assets: mix of NSE stocks, bonds, and global assets
            assets = [
                # Kenyan stocks
                "NSE:SCOM",  # Safaricom
                "NSE:EQTY",  # Equity Bank
                "NSE:EABL",  # East African Breweries
                "NSE:KCB",   # KCB Bank
                "NSE:BAT",   # BAT Kenya
                # Kenyan bonds and money market
                "KEGB:91D",  # 91-day T-bill
                "KEGB:182D", # 182-day T-bill
                "KEGB:364D", # 364-day T-bill
                "KEGB:2Y",   # 2-year bond
                "KEGB:5Y",   # 5-year bond
                # Global assets
                "CRYPTO:BTC",  # Bitcoin
                "ETF:VWO",     # Emerging Markets ETF
                "ETF:GLD"      # Gold ETF
            ]
            
        # Fetch data from various APIs based on asset prefix
        all_data = {}
        
        for asset in assets:
            if asset.startswith("NSE:"):
                # Fetch NSE stock data
                symbol = asset.split(":")[1]
                data = self.nse_api.get_historical_prices(symbol, period, frequency)
                all_data[asset] = data
            elif asset.startswith("KEGB:"):
                # Fetch Kenyan government bond data
                bond_type = asset.split(":")[1]
                data = self.cbk_api.get_bond_yields(bond_type, period, frequency)
                all_data[asset] = data
            elif asset.startswith("CRYPTO:"):
                # Fetch cryptocurrency data
                crypto = asset.split(":")[1]
                data = self.crypto_api.get_historical_prices(crypto, period, frequency)
                all_data[asset] = data
            elif asset.startswith("ETF:"):
                # Fetch ETF data from global markets
                etf = asset.split(":")[1]
                data = self.market_data.get_etf_prices(etf, period, frequency)
                all_data[asset] = data
                
        # Convert to DataFrame and calculate returns
        prices_df = pd.DataFrame(all_data)
        returns_df = prices_df.pct_change().dropna()
        
        logger.info(f"Fetched market data for {len(assets)} assets over {period}")
        return returns_df

    def calculate_expected_returns(self, returns_df, method="mean_historical"):
        """
        Calculate expected returns for assets using various methods.
        
        Args:
            returns_df (pandas.DataFrame): Historical returns data
            method (str): Method to use ('mean_historical', 'capm', 'black_litterman')
            
        Returns:
            pandas.Series: Expected returns for each asset
        """
        if method == "mean_historical":
            # Simple historical mean returns (annualized)
            expected_returns = returns_df.mean() * 12  # Assuming monthly data
            
        elif method == "capm":
            # Capital Asset Pricing Model
            # Get risk-free rate from CBK
            risk_free_rate = self.cbk_api.get_tbill_rate("91D") / 100
            
            # Calculate beta for each asset against NSE index
            nse_index = self.nse_api.get_historical_index("NSE20", returns_df.index[0], returns_df.index[-1])
            nse_returns = pd.Series(nse_index).pct_change().dropna()
            
            # Calculate market risk premium (historical NSE returns - risk-free rate)
            market_return = nse_returns.mean() * 12  # Annualized
            market_risk_premium = market_return - risk_free_rate
            
            # Calculate beta and expected return for each asset
            expected_returns = pd.Series(index=returns_df.columns)
            for asset in returns_df.columns:
                asset_returns = returns_df[asset]
                # Calculate beta (covariance with market / variance of market)
                beta = np.cov(asset_returns, nse_returns)[0, 1] / np.var(nse_returns)
                # CAPM formula: rf + beta * (rm - rf)
                expected_returns[asset] = risk_free_rate + beta * market_risk_premium
                
        elif method == "black_litterman":
            # Black-Litterman model (simplified version)
            # This would normally incorporate investor views with market equilibrium
            # For now, we'll use a simple implementation
            
            # Get market capitalization weights
            market_caps = {}
            for asset in returns_df.columns:
                if asset.startswith("NSE:"):
                    symbol = asset.split(":")[1]
                    market_caps[asset] = self.nse_api.get_market_cap(symbol)
                else:
                    # For non-NSE assets, use placeholder weights
                    market_caps[asset] = 1.0
            
            # Normalize to get market weights
            total_cap = sum(market_caps.values())
            market_weights = {k: v/total_cap for k, v in market_caps.items()}
            
            # Calculate covariance matrix of returns
            cov_matrix = returns_df.cov() * 12  # Annualized
            
            # Implied market equilibrium returns (simplified)
            risk_aversion = 2.5  # Market risk aversion coefficient
            implied_returns = risk_aversion * cov_matrix.dot(pd.Series(market_weights))
            
            # For now, we'll use the implied returns as our expected returns
            # A full Black-Litterman model would incorporate investor views
            expected_returns = implied_returns
        
        else:
            raise ValueError(f"Unsupported return calculation method: {method}")
        
        logger.info(f"Calculated expected returns using {method} method")
        return expected_returns

    def calculate_risk_metrics(self, returns_df):
        """
        Calculate risk metrics including volatility and correlation matrix.
        
        Args:
            returns_df (pandas.DataFrame): Historical returns data
            
        Returns:
            tuple: (volatility Series, covariance matrix, correlation matrix)
        """
        # Calculate annualized volatility (standard deviation of returns)
        volatility = returns_df.std() * np.sqrt(12)  # Assuming monthly data
        
        # Use Ledoit-Wolf shrinkage estimator for more robust covariance estimation
        lw = LedoitWolf().fit(returns_df)
        cov_matrix = pd.DataFrame(
            lw.covariance_, 
            index=returns_df.columns, 
            columns=returns_df.columns
        ) * 12  # Annualized
        
        # Calculate correlation matrix
        corr_matrix = returns_df.corr()
        
        logger.info("Calculated risk metrics: volatility, covariance, and correlation")
        return volatility, cov_matrix, corr_matrix

    def optimize_portfolio_mpt(self, expected_returns, cov_matrix, target_return=None):
        """
        Optimize portfolio using Modern Portfolio Theory (Markowitz).
        
        Args:
            expected_returns (pandas.Series): Expected returns for each asset
            cov_matrix (pandas.DataFrame): Covariance matrix of returns
            target_return (float, optional): Target portfolio return
            
        Returns:
            dict: Optimized portfolio weights and metrics
        """
        num_assets = len(expected_returns)
        
        # Define constraints
        if target_return is None:
            target_return = self.min_return
            
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Weights sum to 1
        ]
        
        if target_return is not None:
            constraints.append(
                {'type': 'eq', 'fun': lambda x: np.sum(expected_returns * x) - target_return}
            )
            
        # Define bounds (0-25% per asset for diversification, adjustable)
        max_allocation = 0.25  # Maximum 25% in any single asset
        bounds = tuple((0, max_allocation) for _ in range(num_assets))
        
        # Define objective function (minimize portfolio variance)
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))
        
        # Initialize with equal weights
        initial_weights = np.array([1/num_assets] * num_assets)
        
        # Run optimization
        result = sco.minimize(
            portfolio_variance,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        # Extract optimized weights
        optimized_weights = result['x']
        
        # Calculate portfolio metrics
        portfolio_return = np.sum(expected_returns * optimized_weights)
        portfolio_volatility = np.sqrt(portfolio_variance(optimized_weights))
        sharpe_ratio = portfolio_return / portfolio_volatility
        
        # Prepare result dictionary
        weights_dict = {asset: weight for asset, weight in zip(expected_returns.index, optimized_weights)}
        
        optimization_result = {
            'weights': weights_dict,
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio
        }
        
        logger.info(f"MPT optimization completed. Return: {portfolio_return:.4f}, Risk: {portfolio_volatility:.4f}")
        return optimization_result

    def generate_efficient_frontier(self, expected_returns, cov_matrix, points=20):
        """
        Generate the efficient frontier for visualization.
        
        Args:
            expected_returns (pandas.Series): Expected returns for each asset
            cov_matrix (pandas.DataFrame): Covariance matrix of returns
            points (int): Number of points on the frontier
            
        Returns:
            dict: Data points for the efficient frontier
        """
        # Get min and max returns from individual assets
        min_return = min(expected_returns)
        max_return = max(expected_returns)
        
        # Generate a range of target returns
        target_returns = np.linspace(min_return, max_return, points)
        
        # Calculate optimal portfolios for each target return
        risk_values = []
        ret_values = []
        
        for target in target_returns:
            try:
                portfolio = self.optimize_portfolio_mpt(expected_returns, cov_matrix, target)
                risk_values.append(portfolio['volatility'])
                ret_values.append(portfolio['expected_return'])
            except:
                pass  # Skip infeasible targets
                
        # Create result dictionary
        frontier_data = {
            'returns': ret_values,
            'risks': risk_values
        }
        
        logger.info(f"Generated efficient frontier with {len(ret_values)} points")
        return frontier_data

    def monte_carlo_simulation(self, expected_returns, cov_matrix, num_portfolios=10000):
        """
        Perform Monte Carlo simulation for portfolio optimization.
        
        Args:
            expected_returns (pandas.Series): Expected returns for each asset
            cov_matrix (pandas.DataFrame): Covariance matrix of returns
            num_portfolios (int): Number of random portfolios to generate
            
        Returns:
            dict: Simulation results and optimal portfolios
        """
        num_assets = len(expected_returns)
        results = np.zeros((3, num_portfolios))
        weights_record = np.zeros((num_portfolios, num_assets))
        
        for i in range(num_portfolios):
            # Generate random weights
            weights = np.random.random(num_assets)
            weights /= np.sum(weights)
            
            # Calculate portfolio return and volatility
            portfolio_return = np.sum(expected_returns * weights)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Store results
            results[0, i] = portfolio_return
            results[1, i] = portfolio_volatility
            results[2, i] = portfolio_return / portfolio_volatility  # Sharpe ratio
            weights_record[i, :] = weights
            
        # Find portfolio with maximum Sharpe ratio
        max_sharpe_idx = np.argmax(results[2])
        max_sharpe_weights = weights_record[max_sharpe_idx, :]
        max_sharpe_return = results[0, max_sharpe_idx]
        max_sharpe_volatility = results[1, max_sharpe_idx]
        
        # Find portfolio with minimum volatility
        min_vol_idx = np.argmin(results[1])
        min_vol_weights = weights_record[min_vol_idx, :]
        min_vol_return = results[0, min_vol_idx]
        min_vol_volatility = results[1, min_vol_idx]
        
        # Prepare result
        simulation_results = {
            'returns': results[0, :].tolist(),
            'volatilities': results[1, :].tolist(),
            'sharpe_ratios': results[2, :].tolist(),
            'max_sharpe_portfolio': {
                'weights': {asset: weight for asset, weight in zip(expected_returns.index, max_sharpe_weights)},
                'expected_return': max_sharpe_return,
                'volatility': max_sharpe_volatility,
                'sharpe_ratio': max_sharpe_return / max_sharpe_volatility
            },
            'min_volatility_portfolio': {
                'weights': {asset: weight for asset, weight in zip(expected_returns.index, min_vol_weights)},
                'expected_return': min_vol_return,
                'volatility': min_vol_volatility,
                'sharpe_ratio': min_vol_return / min_vol_volatility
            }
        }
        
        logger.info(f"Monte Carlo simulation completed with {num_portfolios} portfolios")
        return simulation_results

    def get_optimized_portfolio(self, user_id=None, optimization_method="mpt", assets=None):
        """
        Main method to generate optimized portfolio for a user.
        
        Args:
            user_id (str, optional): User identifier
            optimization_method (str): Optimization method ('mpt', 'monte_carlo', 'black_litterman')
            assets (list, optional): List of assets to include in the portfolio
            
        Returns:
            dict: Optimized portfolio with weights and metrics
        """
        # Load user preferences and risk profile
        if user_id:
            self.user_id = user_id
        preferences = self.load_user_preferences(self.user_id)
        
        # Adjust asset list based on user preferences
        if assets is None:
            # Generate custom asset list based on user preferences
            preferred_sectors = preferences.get("preferred_sectors", [])
            excluded_sectors = preferences.get("excluded_sectors", [])
            preferred_asset_classes = preferences.get("preferred_asset_classes", ["stocks", "bonds"])
            
            assets = self._generate_asset_list(
                preferred_sectors, 
                excluded_sectors, 
                preferred_asset_classes
            )
        
        # Fetch market data
        returns_df = self.fetch_market_data(assets)
        
        # Calculate expected returns and risk metrics
        expected_returns = self.calculate_expected_returns(returns_df, method="mean_historical")
        volatility, cov_matrix, corr_matrix = self.calculate_risk_metrics(returns_df)
        
        # Run optimization based on selected method
        if optimization_method == "mpt":
            # Modern Portfolio Theory optimization
            optimal_portfolio = self.optimize_portfolio_mpt(expected_returns, cov_matrix)
            
        elif optimization_method == "monte_carlo":
            # Monte Carlo simulation
            simulation_results = self.monte_carlo_simulation(expected_returns, cov_matrix)
            
            # Use max Sharpe ratio portfolio as the optimal one
            optimal_portfolio = simulation_results['max_sharpe_portfolio']
            
            # Add simulation data to the result
            optimal_portfolio['simulation_data'] = {
                'returns': simulation_results['returns'],
                'volatilities': simulation_results['volatilities']
            }
            
        elif optimization_method == "black_litterman":
            # Use Black-Litterman model for expected returns
            bl_returns = self.calculate_expected_returns(returns_df, method="black_litterman")
            
            # Optimize using the BL expected returns
            optimal_portfolio = self.optimize_portfolio_mpt(bl_returns, cov_matrix)
            
        else:
            raise ValueError(f"Unsupported optimization method: {optimization_method}")
        
        # Add risk metrics and correlation data to the result
        optimal_portfolio['asset_volatility'] = volatility.to_dict()
        optimal_portfolio['correlation_matrix'] = corr_matrix.to_dict()
        
        # Add recommended rebalancing period
        optimal_portfolio['rebalancing_recommendation'] = self._get_rebalancing_recommendation(
            optimal_portfolio['volatility'],
            self.investment_horizon
        )
            
        # Add localized context for Kenya
        optimal_portfolio['local_context'] = self._add_kenyan_market_context(optimal_portfolio['weights'])
        
        logger.info(f"Generated optimized portfolio using {optimization_method} for user {self.user_id}")
        return optimal_portfolio

    def portfolio_stress_test(self, portfolio_weights, scenarios=None):
        """
        Perform stress tests on a portfolio under different market scenarios.
        
        Args:
            portfolio_weights (dict): Asset weights in the portfolio
            scenarios (list, optional): List of stress test scenarios
            
        Returns:
            dict: Stress test results for different scenarios
        """
        if scenarios is None:
            # Default scenarios
            scenarios = [
                {
                    "name": "market_crash",
                    "description": "Stock market crash (-30%)",
                    "impacts": {
                        "NSE:": -0.30,  # NSE stocks drop 30%
                        "KEGB:": 0.05,  # Government bonds gain 5%
                        "CRYPTO:": -0.50,  # Crypto drops 50%
                        "ETF:": -0.25  # ETFs drop 25%
                    }
                },
                {
                    "name": "interest_rate_hike",
                    "description": "CBK rate hike (3% increase)",
                    "impacts": {
                        "NSE:": -0.15,  # Stocks drop 15%
                        "KEGB:": -0.10,  # Bonds drop 10%
                        "CRYPTO:": -0.20,  # Crypto drops 20%
                        "ETF:": -0.15  # ETFs drop 15%
                    }
                },
                {
                    "name": "ksh_depreciation",
                    "description": "15% KES depreciation against USD",
                    "impacts": {
                        "NSE:": -0.05,  # Local stocks drop 5%
                        "KEGB:": -0.08,  # Bonds drop 8%
                        "CRYPTO:": 0.10,  # Crypto gains 10%
                        "ETF:": 0.05  # Foreign ETFs gain 5%
                    }
                },
                {
                    "name": "economic_recovery",
                    "description": "Strong economic recovery",
                    "impacts": {
                        "NSE:": 0.20,  # Stocks gain 20%
                        "KEGB:": -0.05,  # Bonds lose 5%
                        "CRYPTO:": 0.15,  # Crypto gains 15%
                        "ETF:": 0.15  # ETFs gain 15%
                    }
                }
            ]
        
        # Calculate portfolio value under each scenario
        results = {}
        initial_value = 100000  # Assume 100,000 KES initial investment
        
        for scenario in scenarios:
            scenario_impact = 0
            asset_impacts = {}
            
            # Calculate weighted impact on portfolio
            for asset, weight in portfolio_weights.items():
                # Find matching prefix in the impacts dictionary
                asset_prefix = None
                for prefix in scenario["impacts"]:
                    if asset.startswith(prefix):
                        asset_prefix = prefix
                        break
                
                # Apply impact if prefix found, otherwise no impact (0%)
                impact = scenario["impacts"].get(asset_prefix, 0) * weight
                scenario_impact += impact
                asset_impacts[asset] = scenario["impacts"].get(asset_prefix, 0)
            
            # Calculate new portfolio value
            new_value = initial_value * (1 + scenario_impact)
            change_amount = new_value - initial_value
            
            # Store results
            results[scenario["name"]] = {
                "description": scenario["description"],
                "original_value": initial_value,
                "new_value": new_value,
                "change_percent": scenario_impact * 100,
                "change_amount": change_amount,
                "asset_impacts": asset_impacts
            }
        
        logger.info(f"Performed stress tests on portfolio for {len(scenarios)} scenarios")
        return results

    def rebalance_portfolio(self, current_weights, target_weights, threshold=0.05):
        """
        Generate rebalancing recommendations when portfolio drifts from target allocation.
        
        Args:
            current_weights (dict): Current asset weights
            target_weights (dict): Target asset weights
            threshold (float): Rebalancing threshold (5% by default)
            
        Returns:
            dict: Rebalancing recommendations
        """
        # Calculate drift for each asset
        drifts = {}
        rebalance_actions = {}
        total_trade_amount = 0
        
        for asset in target_weights:
            current = current_weights.get(asset, 0)
            target = target_weights[asset]
            drift = current - target
            drifts[asset] = drift
            
            # Add to rebalance actions if drift exceeds threshold
            if abs(drift) > threshold:
                action = "sell" if drift > 0 else "buy"
                amount = abs(drift)
                rebalance_actions[asset] = {
                    "action": action,
                    "current_allocation": current,
                    "target_allocation": target,
                    "drift": drift,
                    "adjustment_amount": amount
                }
                total_trade_amount += amount
        
        # Prepare results
        rebalancing_result = {
            "needs_rebalancing": len(rebalance_actions) > 0,
            "actions": rebalance_actions,
            "total_trade_amount": total_trade_amount,
            "max_drift": max(abs(d) for d in drifts.values()) if drifts else 0
        }
        
        logger.info(f"Generated rebalancing recommendations with {len(rebalance_actions)} actions")
        return rebalancing_result

    def generate_investment_report(self, portfolio, user_id=None):
        """
        Generate a comprehensive investment report with recommendations and insights.
        
        Args:
            portfolio (dict): Portfolio data with weights and metrics
            user_id (str, optional): User identifier
            
        Returns:
            dict: Investment report with recommendations
        """
        if user_id:
            self.user_id = user_id
            
        # Load user preferences if not already loaded
        preferences = self.load_user_preferences(self.user_id)
        
        # Perform stress tests
        stress_test_results = self.portfolio_stress_test(portfolio["weights"])
        
        # Get market outlook
        market_outlook = self._get_market_outlook()
        
        # Generate sector-specific recommendations
        sector_recommendations = self._generate_sector_recommendations(
            portfolio["weights"],
            market_outlook
        )
        
        # Format portfolio allocation as percentages
        formatted_allocation = {
            asset: f"{weight * 100:.2f}%" 
            for asset, weight in portfolio["weights"].items()
        }
        
        # Prepare report
        report = {
            "portfolio_summary": {
                "expected_annual_return": f"{portfolio['expected_return'] * 100:.2f}%",
                "risk_level": f"{portfolio['volatility'] * 100:.2f}%",
                "sharpe_ratio": f"{portfolio['sharpe_ratio']:.2f}",
                "asset_allocation": formatted_allocation
            },
            "investment_horizon": f"{self.investment_horizon} years",
            "rebalancing_recommendation": portfolio.get("rebalancing_recommendation", "Quarterly"),
            "risk_assessment": self._assess_portfolio_risk(portfolio["volatility"]),
            "stress_test_results": stress_test_results,
            "market_outlook": market_outlook,
            "sector_recommendations": sector_recommendations,
            "educational_resources": self._get_educational_resources(preferences),
            "kenya_market_context": portfolio.get("local_context", {})
        }
        
        logger.info(f"Generated investment report for user {self.user_id}")
        return report

    def _generate_asset_list(self, preferred_sectors, excluded_sectors, preferred_asset_classes):
        """
        Generate a list of assets based on user preferences.
        
        Args:
            preferred_sectors (list): Preferred market sectors
            excluded_sectors (list): Sectors to exclude
            preferred_asset_classes (list): Preferred asset classes
            
        Returns:
            list: List of assets matching criteria
        """
        assets = []
        
        # Default sector map for Kenyan stocks
        sector_map = {
            "technology": ["NSE:SCOM"],
            "finance": ["NSE:EQTY", "NSE:KCB", "NSE:COOP", "NSE:NCBA"],
            "energy": ["NSE:KPLC", "NSE:KEGN", "NSE:TOTL"],
            "manufacturing": ["NSE:EABL", "NSE:BAT", "NSE:UNGA"],
            "agriculture": ["NSE:SASN", "NSE:KAKZ"],
            "real_estate": ["NSE:HOLD", "NSE:KURV"],
            "healthcare": ["NSE:SCAN"]
        }
        
        # Add stocks from preferred sectors
        if "stocks" in preferred_asset_classes:
            for sector in preferred_sectors:
                if sector in sector_map:
                    for stock in sector_map[sector]:
                        assets.append(stock)
        
        # Add bonds if preferred
        if "bonds" in preferred_asset_classes:
            assets.extend(["KEGB:2Y", "KEGB:5Y", "KEGB:10Y"])
        
        # Add money market if preferred
        if "money_market" in preferred_asset_classes:
            assets.extend(["KEGB:91D", "KEGB:182D", "KEGB:364D"])
        
        # Add crypto if preferred
        if "crypto" in preferred_asset_classes:
            assets.extend(["CRYPTO:BTC", "CRYPTO:ETH"])
        
        # Add global ETFs if preferred
        if "global_etfs" in preferred_asset_classes:
            assets.extend(["ETF:VWO", "ETF:GLD"])
        
        # Remove assets from excluded sectors
        for sector in excluded_sectors:
            if sector in sector_map:
                for stock in sector_map[sector]:
                    if stock in assets:
                        assets.remove(stock)
        
        return assets

    def _get_rebalancing_recommendation(self, volatility, horizon):
        """
        Determine optimal rebalancing period based on portfolio volatility and horizon.
        
        Args:
            volatility (float): Portfolio volatility
            horizon (int): Investment horizon in years
            
        Returns:
            str: Recommended rebalancing frequency
        """
        if volatility > 0.20:
            return "Monthly"
        elif volatility > 0.15:
            return "Quarterly"
        elif volatility > 0.10:
            return "Semi-annually"
        else:
            return "Annually"

    def _assess_portfolio_risk(self, volatility):
        """
        Assess portfolio risk level based on volatility.
        
        Args:
            volatility (float): Portfolio volatility
            
        Returns:
            str: Risk assessment description
        """
        if volatility < 0.10:
            return "Low Risk: This portfolio has relatively low volatility and is suitable for conservative investors."
        elif volatility < 0.18:
            return "Moderate Risk: This portfolio has moderate volatility and is suitable for balanced investors."
        else:
            return "High Risk: This portfolio has higher volatility and is suitable for aggressive investors."

    def _get_market_outlook(self):
        """
        Get current market outlook and trends for different asset classes.
        
        Returns:
            dict: Market outlook for different asset classes
        """
        # This would typically call APIs for current market trends
        # For now, we'll return placeholder data
        return {
            "kenyan_equities": {
                "outlook": "positive",
                "trend": "upward",
                "commentary": "The NSE has shown resilience with strong performance in banking and telecommunication sectors."
            },
            "kenyan_bonds": {
                "outlook": "neutral",
                "trend": "stable",
                "commentary": "Government bond yields remain relatively stable with the CBK maintaining steady monetary policy."
            },
            "global_markets": {
                "outlook": "mixed",
                "trend": "volatile",
                "commentary": "Global markets show mixed performance with concerns about inflation and monetary tightening."
            },
            "cryptocurrency": {
                "outlook": "volatile",
                "trend": "neutral",
                "commentary": "Cryptocurrencies remain highly volatile with regulatory developments affecting market sentiment."
            },
            "forex": {
                "outlook": "cautious",
                "trend": "KES depreciation",
                "commentary": "The Kenyan Shilling has faced pressure against major currencies due to global economic conditions."
            }
        }

    def _generate_sector_recommendations(self, weights, market_outlook):
        """
        Generate sector-specific investment recommendations.
        
        Args:
            weights (dict): Current portfolio weights
            market_outlook (dict): Market outlook data
            
        Returns:
            list: Sector recommendations
        """
        # Extract sectors from portfolio
        sectors = {}
        for asset, weight in weights.items():
            if asset.startswith("NSE:"):
                # Identify sector for NSE stocks
                if "SCOM" in asset:
                    sector = "technology"
                elif any(bank in asset for bank in ["EQTY", "KCB", "COOP", "NCBA"]):
                    sector = "finance"
                elif any(energy in asset for energy in ["KPLC", "KEGN", "TOTL"]):
                    sector = "energy"
                elif any(mfg in asset for mfg in ["EABL", "BAT", "UNGA"]):
                    sector = "manufacturing"
                else:
                    sector = "other"
                
                # Add to sector allocation
                sectors[sector] = sectors.get(sector, 0) + weight
        
        # Generate recommendations based on market outlook and current allocation
        recommendations = []
        
        if sectors.get("finance", 0) < 0.15 and market_outlook["kenyan_equities"]["outlook"] == "positive":
            recommendations.append({
                "sector": "finance",
                "action": "increase",
                "rationale": "Banking sector has strong growth potential due to expanding digital banking adoption in Kenya."
            })
            
        if sectors.get("technology", 0) < 0.10:
            recommendations.append({
                "sector": "technology",
                "action": "consider adding",
                "rationale": "Technology sector, particularly mobile and fintech, continues to drive innovation in Kenya."
            })
            
        # Check for overexposure to volatile sectors
        if sectors.get("energy", 0) > 0.20:
            recommendations.append({
                "sector": "energy",
                "action": "reduce",
                "rationale": "Consider reducing exposure to energy sector due to regulatory uncertainties."
            })
            
        return recommendations

    def _add_kenyan_market_context(self, weights):
        """
        Add Kenya-specific market context to portfolio recommendations.
        
        Args:
            weights (dict): Portfolio weights
            
        Returns:
            dict: Kenya-specific market insights
        """
        # Calculate exposure to Kenyan assets
        kenyan_exposure = sum(weight for asset, weight in weights.items() if asset.startswith(("NSE:", "KEGB:")))
        
        # Get current key rates
        tbill_91d_rate = self.cbk_api.get_tbill_rate("91D")
        cbr_rate = self.cbk_api.get_central_bank_rate()
        usd_kes_rate = self.forex_api.get_exchange_rate("USD", "KES")
        
        # Prepare insights
        insights = {
            "kenyan_exposure": f"{kenyan_exposure * 100:.2f}%",
            "market_indicators": {
                "cbk_rate": f"{cbr_rate:.2f}%",
                "91_day_tbill": f"{tbill_91d_rate:.2f}%",
                "usd_kes_rate": f"{usd_kes_rate:.2f}"
            },
            "local_considerations": [
                "Consider inflation impact on KES-denominated investments",
                "Be aware of Kenyan tax implications for different asset classes",
                "Monitor CBK monetary policy statements for interest rate outlook"
            ],
            "diversification_insight": self._get_diversification_insight(kenyan_exposure)
        }
        
        return insights

    def _get_diversification_insight(self, kenyan_exposure):
        """
        Generate insights about geographic diversification.
        
        Args:
            kenyan_exposure (float): Percentage of portfolio in Kenyan assets
            
        Returns:
            str: Insight about geographic diversification
        """
        if kenyan_exposure > 0.8:
            return "Your portfolio is heavily concentrated in Kenyan assets. Consider adding international exposure to reduce country-specific risk."
        elif kenyan_exposure > 0.5:
            return "Your portfolio has moderate international diversification. This provides some protection against Kenya-specific economic risks."
        else:
            return "Your portfolio is well-diversified internationally, which helps protect against Kenya-specific economic volatility."

    def _get_educational_resources(self, preferences):
        """
        Get personalized educational resources based on user preferences.
        
        Args:
            preferences (dict): User preferences
            
        Returns:
            list: Recommended educational resources
        """
        risk_tolerance = preferences.get("risk_tolerance", "moderate")
        financial_goals = preferences.get("financial_goals", ["general_investment"])
        
        resources = []
        
        # Basic resources for everyone
        resources.append({
            "title": "Understanding Investment Risk and Return",
            "type": "article",
            "link": "/learning_resources/risk_return_basics"
        })
        
        # Risk-specific resources
        if risk_tolerance == "conservative":
            resources.append({
                "title": "Guide to Kenyan Government Bonds and Treasury Bills",
                "type": "webinar",
                "link": "/webinars_forums/government_securities"
            })
        elif risk_tolerance == "aggressive":
            resources.append({
                "title": "Growth Investing in Emerging Markets",
                "type": "course",
                "link": "/learning_resources/emerging_markets"
            })
        
        # Goal-specific resources
        if "retirement" in financial_goals:
            resources.append({
                "title": "Retirement Planning in Kenya: NSSF and Beyond",
                "type": "article",
                "link": "/learning_resources/retirement_planning"
            })
        elif "education" in financial_goals:
            resources.append({
                "title": "Saving for Education in Kenya",
                "type": "calculator",
                "link": "/tools_and_calculators/education_planner"
            })
        
        return resources
