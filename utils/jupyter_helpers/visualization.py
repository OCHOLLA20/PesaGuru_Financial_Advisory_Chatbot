import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set default plot style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

def plot_stock_price(
    df: pd.DataFrame,
    stock_code: str,
    title: Optional[str] = None,
    include_volume: bool = True,
    include_ma: bool = True,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> None:
    """
    Plot stock price history with optional volume and moving averages.
    
    Args:
        df: DataFrame containing stock data
        stock_code: Stock code to plot
        title: Custom title for the plot
        include_volume: Whether to include volume data
        include_ma: Whether to include moving averages
        start_date: Start date for filtering (format: 'YYYY-MM-DD')
        end_date: End date for filtering (format: 'YYYY-MM-DD')
        figsize: Figure size as (width, height)
        save_path: Path to save the plot image
    """
    try:
        # Filter data for the specific stock
        stock_data = df[df['code'] == stock_code].copy()
        
        if stock_data.empty:
            logger.warning(f"No data found for stock code: {stock_code}")
            return
        
        # Apply date filters if provided
        if start_date:
            stock_data = stock_data[stock_data['date'] >= pd.to_datetime(start_date)]
        
        if end_date:
            stock_data = stock_data[stock_data['date'] <= pd.to_datetime(end_date)]
        
        # Sort by date
        stock_data = stock_data.sort_values('date')
        
        # Get stock name
        stock_name = stock_data['name'].iloc[0] if 'name' in stock_data.columns else stock_code
        
        # Create figure
        plt.figure(figsize=figsize)
        
        # Create primary axis for stock price
        ax1 = plt.gca()
        
        # Plot stock price
        ax1.plot(stock_data['date'], stock_data['day_price'], label='Price', color='#1f77b4', linewidth=2)
        
        # Add moving averages if requested and available
        if include_ma:
            # Calculate moving averages if not already present
            if 'sma_20' not in stock_data.columns:
                stock_data['sma_20'] = stock_data['day_price'].rolling(window=20).mean()
            
            if 'sma_50' not in stock_data.columns:
                stock_data['sma_50'] = stock_data['day_price'].rolling(window=50).mean()
            
            # Plot moving averages
            ax1.plot(stock_data['date'], stock_data['sma_20'], label='20-day MA', color='#ff7f0e', linewidth=1.5)
            ax1.plot(stock_data['date'], stock_data['sma_50'], label='50-day MA', color='#2ca02c', linewidth=1.5)
        
        # Format primary axis
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price (KES)')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        
        # Add volume if requested
        if include_volume and 'volume' in stock_data.columns:
            # Create secondary axis for volume
            ax2 = ax1.twinx()
            
            # Plot volume as bars
            ax2.bar(stock_data['date'], stock_data['volume'], alpha=0.3, color='gray', label='Volume')
            
            # Format secondary axis
            ax2.set_ylabel('Volume', color='gray')
            ax2.tick_params(axis='y', labelcolor='gray')
            
            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        else:
            ax1.legend(loc='upper left')
        
        # Set title
        if title:
            plt.title(title)
        else:
            date_range = f"{stock_data['date'].min().strftime('%Y-%m-%d')} to {stock_data['date'].max().strftime('%Y-%m-%d')}"
            plt.title(f"{stock_name} ({stock_code}) - {date_range}")
        
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            plt.close()
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting stock price: {e}")

def plot_stock_comparison(
    df: pd.DataFrame,
    stock_codes: List[str],
    normalize: bool = True,
    title: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> None:
    """
    Plot comparison of multiple stocks.
    
    Args:
        df: DataFrame containing stock data
        stock_codes: List of stock codes to compare
        normalize: Whether to normalize prices to the same starting point
        title: Custom title for the plot
        start_date: Start date for filtering (format: 'YYYY-MM-DD')
        end_date: End date for filtering (format: 'YYYY-MM-DD')
        figsize: Figure size as (width, height)
        save_path: Path to save the plot image
    """
    try:
        # Create figure
        plt.figure(figsize=figsize)
        
        # Keep track of stock names for legend
        stock_names = []
        
        # Process each stock
        for stock_code in stock_codes:
            # Filter data for this stock
            stock_data = df[df['code'] == stock_code].copy()
            
            if stock_data.empty:
                logger.warning(f"No data found for stock code: {stock_code}")
                continue
            
            # Apply date filters if provided
            if start_date:
                stock_data = stock_data[stock_data['date'] >= pd.to_datetime(start_date)]
            
            if end_date:
                stock_data = stock_data[stock_data['date'] <= pd.to_datetime(end_date)]
            
            # Sort by date
            stock_data = stock_data.sort_values('date')
            
            # Get stock name
            stock_name = stock_data['name'].iloc[0] if 'name' in stock_data.columns else stock_code
            stock_names.append(f"{stock_name} ({stock_code})")
            
            # Normalize prices if requested
            if normalize:
                # Calculate normalized price (starting from 100)
                initial_price = stock_data['day_price'].iloc[0]
                stock_data['normalized_price'] = (stock_data['day_price'] / initial_price) * 100
                y_values = stock_data['normalized_price']
                y_label = 'Normalized Price (Starting at 100)'
            else:
                y_values = stock_data['day_price']
                y_label = 'Price (KES)'
            
            # Plot the stock
            plt.plot(stock_data['date'], y_values, label=f"{stock_name} ({stock_code})", linewidth=2)
        
        # Format the plot
        if title:
            plt.title(title)
        else:
            date_range = ""
            if start_date and end_date:
                date_range = f" ({start_date} to {end_date})"
            plt.title(f"Stock Comparison{date_range}")
        
        plt.xlabel('Date')
        plt.ylabel(y_label)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            plt.close()
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting stock comparison: {e}")

def plot_sector_performance(
    df: pd.DataFrame,
    metric: str = 'change%',
    year: Optional[str] = None,
    top_n: Optional[int] = None,
    figsize: Tuple[int, int] = (12, 8),
    save_path: Optional[str] = None
) -> None:
    """
    Plot sector performance based on a specified metric.
    
    Args:
        df: DataFrame containing sector performance data
        metric: Metric to plot ('change%', 'day_price', etc.)
        year: Year to filter for
        top_n: Number of top sectors to display
        figsize: Figure size as (width, height)
        save_path: Path to save the plot image
    """
    try:
        # Create a copy to avoid modifying the original data
        plot_df = df.copy()
        
        # Ensure we have a sector column
        if 'sector' not in plot_df.columns:
            # Look for alternative column names
            sector_cols = [col for col in plot_df.columns if 'sector' in col.lower()]
            if not sector_cols:
                logger.error("No sector column found in the data")
                return
            
            # Use the first matched column
            plot_df['sector'] = plot_df[sector_cols[0]]
        
        # Filter for the specified year if provided
        if year:
            if 'year' in plot_df.columns:
                plot_df = plot_df[plot_df['year'] == year]
            elif 'date' in plot_df.columns:
                plot_df = plot_df[plot_df['date'].dt.year == int(year)]
        
        # Ensure the metric column exists
        if metric not in plot_df.columns:
            logger.error(f"Metric '{metric}' not found in the data")
            return
        
        # Group by sector and calculate the mean of the metric
        sector_performance = plot_df.groupby('sector')[metric].mean().reset_index()
        
        # Sort by the metric
        sector_performance = sector_performance.sort_values(metric, ascending=False)
        
        # Limit to top N sectors if specified
        if top_n and top_n < len(sector_performance):
            sector_performance = sector_performance.head(top_n)
        
        # Create figure
        plt.figure(figsize=figsize)
        
        # Create horizontal bar chart
        bars = plt.barh(sector_performance['sector'], sector_performance[metric])
        
        # Add data labels
        for bar in bars:
            width = bar.get_width()
            label_x_pos = width if width >= 0 else width - 0.5
            plt.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}%' if metric == 'change%' else f'{width:.2f}',
                    va='center')
        
        # Format the plot
        year_str = f" - {year}" if year else ""
        metric_label = 'Percent Change' if metric == 'change%' else ('Price Change' if metric == 'change' else metric.replace('_', ' ').title())
        plt.title(f'NSE Sector Performance{year_str} ({metric_label})')
        plt.xlabel(metric_label)
        plt.ylabel('Sector')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            plt.close()
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting sector performance: {e}")

def plot_economic_indicators(
    indicators_df: pd.DataFrame,
    indicators: List[str],
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    normalize: bool = False,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> None:
    """
    Plot economic indicators over time.
    
    Args:
        indicators_df: DataFrame containing economic indicators
        indicators: List of indicator columns to plot
        start_year: Start year for filtering
        end_year: End year for filtering
        normalize: Whether to normalize indicators for comparison
        title: Custom title for the plot
        figsize: Figure size as (width, height)
        save_path: Path to save the plot image
    """
    try:
        # Create a copy to avoid modifying the original data
        plot_df = indicators_df.copy()
        
        # Ensure we have a year column
        if 'year' not in plot_df.columns:
            # Look for alternative column names
            year_cols = [col for col in plot_df.columns if 'year' in col.lower()]
            if not year_cols:
                logger.error("No year column found in the data")
                return
            
            # Use the first matched column
            plot_df['year'] = plot_df[year_cols[0]]
        
        # Convert year to numeric if it's not already
        plot_df['year'] = pd.to_numeric(plot_df['year'], errors='coerce')
        
        # Filter by year range if provided
        if start_year:
            plot_df = plot_df[plot_df['year'] >= start_year]
        
        if end_year:
            plot_df = plot_df[plot_df['year'] <= end_year]
        
        # Check if all requested indicators exist
        missing_indicators = [ind for ind in indicators if ind not in plot_df.columns]
        if missing_indicators:
            logger.warning(f"Indicators not found in data: {', '.join(missing_indicators)}")
            # Filter to only available indicators
            indicators = [ind for ind in indicators if ind in plot_df.columns]
            
            if not indicators:
                logger.error("No valid indicators to plot")
                return
        
        # Create figure
        plt.figure(figsize=figsize)
        
        # Normalize indicators if requested
        if normalize:
            for indicator in indicators:
                initial_value = plot_df[indicator].iloc[0]
                if initial_value != 0:  # Avoid division by zero
                    plot_df[f'{indicator}_norm'] = (plot_df[indicator] / initial_value) * 100
                else:
                    # If initial value is zero, use absolute values instead
                    plot_df[f'{indicator}_norm'] = plot_df[indicator]
                    
            # Plot normalized indicators
            for indicator in indicators:
                plt.plot(plot_df['year'], plot_df[f'{indicator}_norm'], 
                         label=indicator.replace('_', ' ').title(), linewidth=2)
            
            plt.ylabel('Normalized Value (100 = Initial)')
        else:
            # Plot raw indicator values
            for indicator in indicators:
                plt.plot(plot_df['year'], plot_df[indicator], 
                         label=indicator.replace('_', ' ').title(), linewidth=2)
            
            plt.ylabel('Value')
        
        # Format the plot
        if title:
            plt.title(title)
        else:
            year_range = f"{plot_df['year'].min()} to {plot_df['year'].max()}"
            plt.title(f"Economic Indicators - {year_range}")
        
        plt.xlabel('Year')
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add thousand separators to y-axis if values are large
        if not normalize and any(plot_df[indicators].max() > 1000):
            plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter('{x:,.0f}'))
        
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            plt.close()
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting economic indicators: {e}")

def create_interactive_chart(
    df: pd.DataFrame,
    stock_code: str,
    title: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Optional[Any]:
    """
    Create an interactive stock chart using Plotly.
    Requires Plotly to be installed.
    
    Args:
        df: DataFrame containing stock data
        stock_code: Stock code to plot
        title: Custom title for the plot
        start_date: Start date for filtering (format: 'YYYY-MM-DD')
        end_date: End date for filtering (format: 'YYYY-MM-DD')
        
    Returns:
        Plotly figure object
    """
    try:
        # Import plotly
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            logger.error("Plotly is not installed. Please install it with: pip install plotly")
            return None
        
        # Filter data for the specific stock
        stock_data = df[df['code'] == stock_code].copy()
        
        if stock_data.empty:
            logger.warning(f"No data found for stock code: {stock_code}")
            return None
        
        # Apply date filters if provided
        if start_date:
            stock_data = stock_data[stock_data['date'] >= pd.to_datetime(start_date)]
        
        if end_date:
            stock_data = stock_data[stock_data['date'] <= pd.to_datetime(end_date)]
        
        # Sort by date
        stock_data = stock_data.sort_values('date')
        
        # Get stock name
        stock_name = stock_data['name'].iloc[0] if 'name' in stock_data.columns else stock_code
        
        # Create subplots with 2 rows
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.1, 
                            row_heights=[0.7, 0.3],
                            subplot_titles=[f"{stock_name} ({stock_code})", "Volume"])
        
        # Add price trace
        fig.add_trace(
            go.Scatter(
                x=stock_data['date'],
                y=stock_data['day_price'],
                name="Price",
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )
        
        # Add moving averages if available
        if 'sma_20' in stock_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=stock_data['date'],
                    y=stock_data['sma_20'],
                    name="20-day MA",
                    line=dict(color='#ff7f0e', width=1.5)
                ),
                row=1, col=1
            )
        
        if 'sma_50' in stock_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=stock_data['date'],
                    y=stock_data['sma_50'],
                    name="50-day MA",
                    line=dict(color='#2ca02c', width=1.5)
                ),
                row=1, col=1
            )
        
        # Add volume trace if available
        if 'volume' in stock_data.columns:
            fig.add_trace(
                go.Bar(
                    x=stock_data['date'],
                    y=stock_data['volume'],
                    name="Volume",
                    marker=dict(color='rgba(100, 100, 100, 0.5)')
                ),
                row=2, col=1
            )
        
        # Update layout
        date_range = f"{stock_data['date'].min().strftime('%Y-%m-%d')} to {stock_data['date'].max().strftime('%Y-%m-%d')}"
        plot_title = title if title else f"{stock_name} ({stock_code}) - {date_range}"
        
        fig.update_layout(
            title=plot_title,
            height=600,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis2_rangeslider_visible=False,
            template="plotly_white"
        )
        
        # Add range slider
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1y", step="year", stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                type="date"
            )
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price (KES)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating interactive chart: {e}")
        return None

def plot_risk_profile_distribution(
    survey_df: pd.DataFrame,
    category_col: str,
    risk_col: str,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> None:
    """
    Plot risk profile distribution across different categories.
    
    Args:
        survey_df: DataFrame containing survey data
        category_col: Column containing categories (e.g., 'Age Group', 'Location')
        risk_col: Column containing risk profile data
        title: Custom title for the plot
        figsize: Figure size as (width, height)
        save_path: Path to save the plot image
    """
    try:
        # Ensure the required columns exist
        if category_col not in survey_df.columns:
            logger.error(f"Category column '{category_col}' not found in the data")
            return
        
        if risk_col not in survey_df.columns:
            logger.error(f"Risk column '{risk_col}' not found in the data")
            return
        
        # Create a cross-tabulation of category vs risk profile
        crosstab = pd.crosstab(
            survey_df[category_col], 
            survey_df[risk_col], 
            normalize='index'
        ) * 100  # Convert to percentages
        
        # Create the plot
        plt.figure(figsize=figsize)
        crosstab.plot(kind='bar', stacked=True, ax=plt.gca(), colormap='viridis')
        
        # Format the plot
        if title:
            plt.title(title)
        else:
            plt.title(f'Risk Profile Distribution by {category_col}')
        
        plt.xlabel(category_col)
        plt.ylabel('Percentage (%)')
        plt.legend(title=risk_col, bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3, axis='y')
        
        # Add percentage labels
        for i, (idx, row) in enumerate(crosstab.iterrows()):
            cum_sum = 0
            for val in row:
                if val > 5:  # Only show labels for segments > 5%
                    plt.text(i, cum_sum + val/2, f'{val:.1f}%', 
                             ha='center', va='center', color='white', fontweight='bold')
                cum_sum += val
        
        plt.tight_layout()
        
        # Save or show the plot
        if save_path:
            plt.savefig(save_path)
            plt.close()
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()
            
    except Exception as e:
        logger.error(f"Error plotting risk profile distribution: {e}")