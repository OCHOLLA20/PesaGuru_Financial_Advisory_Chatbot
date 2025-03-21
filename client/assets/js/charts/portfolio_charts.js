let portfolioAllocationChart;
let portfolioGrowthChart;
let riskReturnChart;
let assetPerformanceChart;
let monthlyContributionsChart;
let portfolioProjectionChart;

// Default color scheme for charts
const chartColors = [
  'rgba(255, 99, 132, 0.8)',  // Red
  'rgba(54, 162, 235, 0.8)',  // Blue
  'rgba(255, 206, 86, 0.8)',  // Yellow
  'rgba(75, 192, 192, 0.8)',  // Green
  'rgba(153, 102, 255, 0.8)', // Purple
  'rgba(255, 159, 64, 0.8)',  // Orange
  'rgba(199, 199, 199, 0.8)'  // Gray
];

// Common chart options
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'right',
      labels: {
        font: {
          family: "'Open Sans', sans-serif",
          size: 12
        }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      titleFont: {
        family: "'Open Sans', sans-serif",
        size: 14
      },
      bodyFont: {
        family: "'Open Sans', sans-serif",
        size: 13
      },
      displayColors: true
    }
  }
};

/**
 * Initialize all portfolio charts on the page
 */
function initializePortfolioCharts() {
  initializeAllocationChart();
  initializeGrowthChart();
  initializeRiskReturnChart();
  initializeAssetPerformanceChart();
  initializeMonthlyContributionsChart();
  initializePortfolioProjectionChart();
}

/**
 * 1. Portfolio Allocation Pie Chart
 * Displays the distribution of assets in the user's portfolio
 */
function initializeAllocationChart() {
  const ctx = document.getElementById('allocationChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (portfolioAllocationChart) {
    portfolioAllocationChart.destroy();
  }
  
  // Fetch allocation data
  fetchPortfolioAllocation()
    .then(data => {
      portfolioAllocationChart = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: data.labels,
          datasets: [{
            data: data.values,
            backgroundColor: chartColors,
            borderWidth: 1
          }]
        },
        options: {
          ...commonOptions,
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'Portfolio Allocation',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.raw || 0;
                  return `${label}: ${value}%`;
                }
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing allocation chart:', error);
      displayChartError(ctx, 'Unable to load allocation data');
    });
}

/**
 * 2. Portfolio Growth Over Time (Line Chart)
 * Tracks historical portfolio performance
 */
function initializeGrowthChart(timeFrame = 'monthly') {
  const ctx = document.getElementById('growthChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (portfolioGrowthChart) {
    portfolioGrowthChart.destroy();
  }
  
  // Fetch growth data
  fetchPortfolioGrowth(timeFrame)
    .then(data => {
      portfolioGrowthChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Portfolio Value',
              data: data.portfolioValues,
              borderColor: chartColors[0],
              backgroundColor: 'rgba(255, 99, 132, 0.1)',
              tension: 0.4,
              fill: true
            },
            {
              label: 'NSE Index',
              data: data.nseValues,
              borderColor: chartColors[1],
              borderDash: [5, 5],
              tension: 0.4,
              fill: false
            }
          ]
        },
        options: {
          ...commonOptions,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Time Period'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Value (KES)'
              },
              ticks: {
                callback: function(value) {
                  return formatCurrency(value);
                }
              }
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'Portfolio Growth Over Time',
              font: {
                size: 16,
                weight: 'bold'
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing growth chart:', error);
      displayChartError(ctx, 'Unable to load growth data');
    });
}

/**
 * 3. Risk vs. Return Scatter Plot
 * Shows how different asset classes balance risk and return
 */
function initializeRiskReturnChart() {
  const ctx = document.getElementById('riskReturnChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (riskReturnChart) {
    riskReturnChart.destroy();
  }
  
  // Fetch risk-return data
  fetchRiskReturnData()
    .then(data => {
      riskReturnChart = new Chart(ctx, {
        type: 'scatter',
        data: {
          datasets: data.map((assetClass, index) => ({
            label: assetClass.name,
            data: [{
              x: assetClass.risk,
              y: assetClass.return
            }],
            backgroundColor: chartColors[index % chartColors.length],
            pointRadius: 8 + (assetClass.allocation * 0.2), // Size based on allocation
            pointHoverRadius: 12 + (assetClass.allocation * 0.2)
          }))
        },
        options: {
          ...commonOptions,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Risk (Volatility)'
              },
              min: 0,
              max: 10
            },
            y: {
              title: {
                display: true,
                text: 'Return (%)'
              },
              min: 0
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'Risk vs. Return Analysis',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.dataset.label || '';
                  const risk = context.parsed.x.toFixed(1);
                  const returns = context.parsed.y.toFixed(1);
                  const allocation = data[context.datasetIndex].allocation;
                  return [
                    `${label}`,
                    `Risk: ${risk}/10`,
                    `Return: ${returns}%`,
                    `Allocation: ${allocation}%`
                  ];
                }
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing risk-return chart:', error);
      displayChartError(ctx, 'Unable to load risk-return data');
    });
}

/**
 * 4. Asset Class Performance (Bar Chart)
 * Compares the performance of different assets in the portfolio
 */
function initializeAssetPerformanceChart() {
  const ctx = document.getElementById('assetPerformanceChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (assetPerformanceChart) {
    assetPerformanceChart.destroy();
  }
  
  // Fetch asset performance data
  fetchAssetPerformance()
    .then(data => {
      // Sort data by performance (optional)
      // data.sort((a, b) => b.performance - a.performance);
      
      // Separate positive and negative values for better visualization
      const positivePerformance = data.map(item => item.performance > 0 ? item.performance : 0);
      const negativePerformance = data.map(item => item.performance < 0 ? item.performance : 0);
      
      // Generate colors based on performance (green for positive, red for negative)
      const backgroundColors = data.map(item => 
        item.performance >= 0 ? 'rgba(75, 192, 92, 0.7)' : 'rgba(255, 99, 132, 0.7)'
      );
      
      assetPerformanceChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.map(item => item.name),
          datasets: [{
            label: 'Performance (%)',
            data: data.map(item => item.performance),
            backgroundColor: backgroundColors,
            borderWidth: 1
          }]
        },
        options: {
          ...commonOptions,
          indexAxis: 'y',
          scales: {
            x: {
              title: {
                display: true,
                text: 'Performance (%)'
              }
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'Asset Performance',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const value = context.raw || 0;
                  return `Performance: ${value.toFixed(2)}%`;
                }
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing asset performance chart:', error);
      displayChartError(ctx, 'Unable to load asset performance data');
    });
}

/**
 * 5. Monthly Investment Contributions (Stacked Bar Chart)
 * Tracks user's monthly contributions to various asset classes
 */
function initializeMonthlyContributionsChart() {
  const ctx = document.getElementById('monthlyContributionsChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (monthlyContributionsChart) {
    monthlyContributionsChart.destroy();
  }
  
  // Fetch monthly contribution data
  fetchMonthlyContributions()
    .then(data => {
      // Create datasets for each asset class
      const datasets = data.assetClasses.map((assetClass, index) => ({
        label: assetClass,
        data: data.contributions.map(month => month.values[index]),
        backgroundColor: chartColors[index % chartColors.length]
      }));
      
      monthlyContributionsChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: data.contributions.map(month => month.month),
          datasets: datasets
        },
        options: {
          ...commonOptions,
          scales: {
            x: {
              stacked: true,
              title: {
                display: true,
                text: 'Month'
              }
            },
            y: {
              stacked: true,
              title: {
                display: true,
                text: 'Amount (KES)'
              },
              ticks: {
                callback: function(value) {
                  return formatCurrency(value);
                }
              }
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'Monthly Investment Contributions',
              font: {
                size: 16,
                weight: 'bold'
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing monthly contributions chart:', error);
      displayChartError(ctx, 'Unable to load monthly contribution data');
    });
}

/**
 * 6. AI-Powered Portfolio Projection (Forecast Chart)
 * Predicts future portfolio value based on current trends and AI analysis
 */
function initializePortfolioProjectionChart() {
  const ctx = document.getElementById('portfolioProjectionChart');
  
  if (!ctx) return;
  
  // If chart already exists, destroy it before creating a new one
  if (portfolioProjectionChart) {
    portfolioProjectionChart.destroy();
  }
  
  // Fetch projection data
  fetchPortfolioProjection()
    .then(data => {
      const currentDate = new Date();
      
      portfolioProjectionChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Conservative Projection',
              data: data.conservativeValues,
              borderColor: chartColors[3], // Green
              backgroundColor: 'rgba(75, 192, 192, 0.1)',
              tension: 0.4,
              fill: false
            },
            {
              label: 'Expected Projection',
              data: data.expectedValues,
              borderColor: chartColors[0], // Red
              backgroundColor: 'rgba(255, 99, 132, 0.1)',
              tension: 0.4,
              fill: false
            },
            {
              label: 'Optimistic Projection',
              data: data.optimisticValues,
              borderColor: chartColors[2], // Yellow
              backgroundColor: 'rgba(255, 206, 86, 0.1)',
              borderDash: [5, 5],
              tension: 0.4,
              fill: false
            }
          ]
        },
        options: {
          ...commonOptions,
          scales: {
            x: {
              title: {
                display: true,
                text: 'Year'
              }
            },
            y: {
              title: {
                display: true,
                text: 'Projected Value (KES)'
              },
              ticks: {
                callback: function(value) {
                  return formatCurrency(value);
                }
              }
            }
          },
          plugins: {
            ...commonOptions.plugins,
            title: {
              display: true,
              text: 'AI-Powered Portfolio Projection',
              font: {
                size: 16,
                weight: 'bold'
              }
            },
            annotation: {
              annotations: {
                line1: {
                  type: 'line',
                  xMin: data.currentDateIndex,
                  xMax: data.currentDateIndex,
                  borderColor: 'rgb(0, 0, 0)',
                  borderWidth: 2,
                  label: {
                    display: true,
                    content: 'Current Date',
                    position: 'start'
                  }
                }
              }
            }
          }
        }
      });
    })
    .catch(error => {
      console.error('Error initializing portfolio projection chart:', error);
      displayChartError(ctx, 'Unable to load projection data');
    });
}

/**
 * Display error message when chart loading fails
 * @param {HTMLElement} ctx - The canvas element
 * @param {string} message - Error message to display
 */
function displayChartError(ctx, message) {
  if (!ctx) return;
  
  const container = ctx.parentElement;
  const errorDiv = document.createElement('div');
  errorDiv.className = 'chart-error';
  errorDiv.innerHTML = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="red" stroke-width="2"/>
      <line x1="8" y1="8" x2="16" y2="16" stroke="red" stroke-width="2"/>
      <line x1="16" y1="8" x2="8" y2="16" stroke="red" stroke-width="2"/>
    </svg>
    <p>${message}</p>
  `;
  
  // Clear any previous errors
  const existingError = container.querySelector('.chart-error');
  if (existingError) {
    container.removeChild(existingError);
  }
  
  container.appendChild(errorDiv);
}

/**
 * Format currency values (KES)
 * @param {number} value - The value to format
 * @return {string} Formatted currency string
 */
function formatCurrency(value) {
  return new Intl.NumberFormat('en-KE', {
    style: 'currency',
    currency: 'KES',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
}

// ==================== DATA FETCHING FUNCTIONS ====================

/**
 * Fetch portfolio allocation data from API
 * @return {Promise} Portfolio allocation data
 */
async function fetchPortfolioAllocation() {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        labels: ['Stocks', 'Bonds', 'Crypto', 'Real Estate', 'Cash'],
        values: [50, 20, 15, 10, 5]
      });
    }, 500);
  });
}

/**
 * Fetch portfolio growth data from API
 * @param {string} timeFrame - Time frame for data (daily, weekly, monthly, yearly)
 * @return {Promise} Portfolio growth data
 */
async function fetchPortfolioGrowth(timeFrame = 'monthly') {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      let labels, portfolioValues, nseValues;
      
      if (timeFrame === 'monthly') {
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        portfolioValues = [1000000, 1050000, 1075000, 1100000, 1150000, 1250000, 1300000, 1280000, 1320000, 1350000, 1380000, 1410000];
        nseValues = [1000000, 1030000, 1060000, 1080000, 1100000, 1120000, 1150000, 1170000, 1190000, 1210000, 1230000, 1250000];
      } else if (timeFrame === 'quarterly') {
        labels = ['Q1', 'Q2', 'Q3', 'Q4'];
        portfolioValues = [1075000, 1250000, 1320000, 1410000];
        nseValues = [1060000, 1120000, 1190000, 1250000];
      } else {
        labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'];
        portfolioValues = [1320000, 1330000, 1350000, 1360000, 1370000, 1380000, 1390000, 1410000];
        nseValues = [1190000, 1200000, 1210000, 1220000, 1230000, 1240000, 1245000, 1250000];
      }
      
      resolve({
        labels,
        portfolioValues,
        nseValues
      });
    }, 500);
  });
}

/**
 * Fetch risk-return data for each asset class
 * @return {Promise} Risk-return data for scatter plot
 */
async function fetchRiskReturnData() {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { name: 'Bonds', risk: 2.5, return: 4.2, allocation: 20 },
        { name: 'Stocks', risk: 6.3, return: 10.1, allocation: 50 },
        { name: 'Crypto', risk: 9.1, return: 25.3, allocation: 15 },
        { name: 'Real Estate', risk: 5.7, return: 8.5, allocation: 10 },
        { name: 'Cash', risk: 0.8, return: 1.5, allocation: 5 }
      ]);
    }, 500);
  });
}

/**
 * Fetch asset performance data
 * @return {Promise} Asset performance data for bar chart
 */
async function fetchAssetPerformance() {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        { name: 'Safaricom (SCOM)', performance: 12.5 },
        { name: 'KCB Bank', performance: 8.2 },
        { name: 'Equity Bank', performance: 6.7 },
        { name: 'Ethereum (ETH)', performance: 20.3 },
        { name: 'Bitcoin (BTC)', performance: 15.8 },
        { name: 'Kenya T-Bonds', performance: 3.5 },
        { name: 'Gold ETF', performance: -2.1 },
        { name: 'Britam', performance: -3.5 }
      ]);
    }, 500);
  });
}

/**
 * Fetch monthly contribution data
 * @return {Promise} Monthly contribution data for stacked bar chart
 */
async function fetchMonthlyContributions() {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        assetClasses: ['Stocks', 'Bonds', 'Crypto', 'Savings'],
        contributions: [
          { month: 'Jan', values: [50000, 30000, 20000, 10000] },
          { month: 'Feb', values: [55000, 28000, 22000, 10000] },
          { month: 'Mar', values: [52000, 30000, 18000, 10000] },
          { month: 'Apr', values: [60000, 25000, 20000, 10000] },
          { month: 'May', values: [55000, 30000, 25000, 10000] },
          { month: 'Jun', values: [58000, 32000, 20000, 10000] }
        ]
      });
    }, 500);
  });
}

/**
 * Fetch portfolio projection data
 * @return {Promise} Projection data for forecast chart
 */
async function fetchPortfolioProjection() {
  // In a real application, this would fetch from an API
  // For this example, we'll use mock data
  return new Promise((resolve) => {
    setTimeout(() => {
      const currentYear = new Date().getFullYear();
      const years = [];
      const conservativeValues = [];
      const expectedValues = [];
      const optimisticValues = [];
      
      let currentValue = 1400000; // Current portfolio value
      
      // Generate 10-year projection
      for (let i = 0; i <= 10; i++) {
        years.push(currentYear + i);
        
        // Conservative growth (7% annual)
        conservativeValues.push(currentValue * Math.pow(1.07, i));
        
        // Expected growth (12% annual)
        expectedValues.push(currentValue * Math.pow(1.12, i));
        
        // Optimistic growth (18% annual)
        optimisticValues.push(currentValue * Math.pow(1.18, i));
      }
      
      resolve({
        labels: years,
        conservativeValues,
        expectedValues,
        optimisticValues,
        currentDateIndex: 0 // Index of current date in the labels array
      });
    }, 500);
  });
}

// ==================== EVENT LISTENERS ====================

/**
 * Set up event listeners for chart interactions
 */
function setupEventListeners() {
  // Time frame selector for growth chart
  const timeFrameSelector = document.getElementById('growthTimeFrame');
  if (timeFrameSelector) {
    timeFrameSelector.addEventListener('change', (e) => {
      initializeGrowthChart(e.target.value);
    });
  }
  
  // Chart type toggle for allocation chart
  const allocationChartTypeToggle = document.getElementById('allocationChartType');
  if (allocationChartTypeToggle) {
    allocationChartTypeToggle.addEventListener('change', (e) => {
      const chartType = e.target.value; // 'pie', 'doughnut', or 'bar'
      if (portfolioAllocationChart) {
        portfolioAllocationChart.config.type = chartType;
        portfolioAllocationChart.update();
      }
    });
  }
  
  // Refresh button for all charts
  const refreshButton = document.getElementById('refreshChartsButton');
  if (refreshButton) {
    refreshButton.addEventListener('click', () => {
      initializePortfolioCharts();
    });
  }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  initializePortfolioCharts();
  setupEventListeners();
});

// Export functions for use in other modules
// export {
//   initializePortfolioCharts,
//   initializeAllocationChart,
//   initializeGrowthChart,
//   initializeRiskReturnChart,
//   initializeAssetPerformanceChart,
//   initializeMonthlyContributionsChart,
//   initializePortfolioProjectionChart
// };