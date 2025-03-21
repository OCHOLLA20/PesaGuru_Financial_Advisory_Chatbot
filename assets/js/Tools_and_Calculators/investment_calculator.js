// C:\xampp\htdocs\PesaGuru\client\assets\js\Tools_and_Calculators\investment_calculator.js
import apiClient from '../apiClient.js';
import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7/+esm';

document.addEventListener('DOMContentLoaded', () => {
  // ====================================
  // DOM References and State
  // ====================================
  const calculatorForm = document.getElementById('investmentCalculatorForm');
  const resultsContainer = document.getElementById('resultsContainer');
  const chartContainer = document.getElementById('chartContainer');
  const saveResultsButton = document.getElementById('saveResultsButton');
  
  // Theme and UI state
  let state = {
    theme: localStorage.getItem('theme') || 'light',
    activeTab: 'projections',
    calculationResults: null
  };
  
  // Initialize chart dimensions
  const margin = { top: 20, right: 30, bottom: 40, left: 60 };
  const width = 600 - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;
  
  // ====================================
  // Initialization
  // ====================================
  function initialize() {
    // Initialize theme
    applyTheme();
    
    // Initialize tabs
    initTabs();
    
    // Initialize theme toggle
    initThemeToggle();
    
    // Initialize navigation
    initNavigation();
    
    // Set up input validation
    setupInputValidation();
    
    // Set up event listeners
    setupEventListeners();
  }
  
  // ====================================
  // Event Listeners and Handlers
  // ====================================
  function setupEventListeners() {
    // Form submission handler
    if (calculatorForm) {
      calculatorForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Save results handler
    if (saveResultsButton) {
      saveResultsButton.addEventListener('click', handleSaveResults);
    }
    
    // Export buttons
    const pdfExportBtn = document.querySelector('.btn-accent');
    const excelExportBtn = document.querySelector('.btn-secondary[title="Export as Excel"]');
    
    if (pdfExportBtn) {
      pdfExportBtn.addEventListener('click', () => {
        alert('PDF export functionality will be implemented soon.');
      });
    }
    
    if (excelExportBtn) {
      excelExportBtn.addEventListener('click', () => {
        alert('Excel export functionality will be implemented soon.');
      });
    }
    
    // Reset button
    const resetBtn = document.querySelector('.btn-secondary:not([title])');
    if (resetBtn) {
      resetBtn.addEventListener('click', resetCalculator);
    }
    
    // Scenario update button
    const updateScenarioBtn = document.querySelector('.update-button');
    if (updateScenarioBtn) {
      updateScenarioBtn.addEventListener('click', () => {
        if (state.calculationResults) {
          updateScenarioComparison(state.calculationResults);
        }
      });
    }
  }
  
  async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Get form values
    const initialInvestment = parseFloat(document.getElementById('initialInvestment').value);
    const monthlyContribution = parseFloat(document.getElementById('monthlyContribution').value);
    const yearsToInvest = parseInt(document.getElementById('yearsToInvest').value);
    const expectedReturnRate = parseFloat(document.getElementById('expectedReturnRate').value);
    const riskTolerance = document.getElementById('riskTolerance').value;
    const inflationRate = parseFloat(document.getElementById('inflationRate')?.value || 2.5);
    const taxRate = parseFloat(document.getElementById('taxRate')?.value || 15);
    
    // Additional parameters if they exist
    const contributionFrequency = document.querySelector('.contribution-frequency')?.value || 'Monthly';
    const compoundingFrequency = document.getElementById('compoundingFrequency')?.value || 'Monthly';
    
    try {
      // Call API for calculation
      let response;
      try {
        response = await apiClient.post('/calculators/investment', {
          initialInvestment,
          monthlyContribution,
          yearsToInvest,
          expectedReturnRate,
          riskTolerance,
          inflationRate,
          taxRate,
          contributionFrequency,
          compoundingFrequency
        });
      } catch (apiError) {
        console.warn('API call failed, using local calculation instead:', apiError);
        
        // Fallback to local calculation
        response = calculateInvestmentGrowth({
          initialInvestment,
          contributionAmount: monthlyContribution,
          contributionFrequency,
          returnRate: expectedReturnRate,
          investmentDuration: yearsToInvest,
          durationUnit: 'Years',
          compoundingFrequency,
          inflationRate,
          taxRate
        });
      }
      
      // Store results in state
      state.calculationResults = response;
      
      // Display results
      displayResults(response);
      
      // Render chart
      renderChart(response.growthData || response.yearlyBreakdown);
      
      // Show results container
      if (resultsContainer) {
        resultsContainer.style.display = 'block';
      }
      
      // Enable save button
      if (saveResultsButton) {
        saveResultsButton.disabled = false;
      }
      
      // Update scenario comparison
      updateScenarioComparison(response);
      
      // Update portfolio allocation tab if it exists
      updatePortfolioAllocation(response, riskTolerance);
      
      // Save parameters to localStorage
      saveCalculationParams({
        initialInvestment,
        monthlyContribution,
        yearsToInvest,
        expectedReturnRate,
        riskTolerance,
        inflationRate,
        taxRate,
        contributionFrequency,
        compoundingFrequency
      });
      
      // Switch to results tab
      switchTab('projections');
      
    } catch (error) {
      console.error('Error calculating investment:', error);
      alert('Failed to calculate investment results. Please try again.');
    }
  }
  
  async function handleSaveResults() {
    // Check if user is authenticated
    const token = localStorage.getItem('auth_token');
    if (!token) {
      const saveAnyway = confirm('You need to be logged in to save results to your account. Would you like to download a PDF instead?');
      if (saveAnyway) {
        // Generate PDF (could be implemented with a PDF library)
        alert('PDF download feature will be implemented soon.');
      }
      return;
    }
    
    try {
      // Get form values
      const calculatorData = {
        initialInvestment: parseFloat(document.getElementById('initialInvestment').value),
        monthlyContribution: parseFloat(document.getElementById('monthlyContribution').value),
        yearsToInvest: parseInt(document.getElementById('yearsToInvest').value),
        expectedReturnRate: parseFloat(document.getElementById('expectedReturnRate').value),
        riskTolerance: document.getElementById('riskTolerance').value,
        inflationRate: parseFloat(document.getElementById('inflationRate')?.value || 2.5),
        taxRate: parseFloat(document.getElementById('taxRate')?.value || 15)
      };
      
      // Save to user account
      await apiClient.post('/user/saved-calculations', {
        type: 'investment',
        data: calculatorData
      });
      
      alert('Calculation saved to your account!');
      
      // Save to localStorage as well
      saveCalculationHistory(state.calculationResults, calculatorData);
      
    } catch (error) {
      console.error('Error saving calculation:', error);
      alert('Failed to save calculation. Please try again.');
    }
  }
  
  // ====================================
  // Calculation Logic
  // ====================================
  function calculateInvestmentGrowth(params) {
    const {
      initialInvestment,
      contributionAmount,
      contributionFrequency,
      returnRate,
      investmentDuration,
      durationUnit,
      compoundingFrequency,
      inflationRate,
      taxRate
    } = params;
    
    // Convert all time periods to months for consistent calculation
    let durationInMonths = durationUnit === 'Years' 
        ? investmentDuration * 12 
        : investmentDuration;
    
    // Convert returnRate and inflationRate to monthly rates
    const monthlyReturnRate = returnRate / 100 / 12;
    const monthlyInflationRate = inflationRate / 100 / 12;
    
    // Determine contribution interval in months
    let contributionIntervalMonths = 1; // Default to monthly
    if (contributionFrequency === 'Quarterly') {
        contributionIntervalMonths = 3;
    } else if (contributionFrequency === 'Annually') {
        contributionIntervalMonths = 12;
    }
    
    // Determine compounding intervals per year
    let compoundingsPerYear = 12; // Default to monthly
    if (compoundingFrequency === 'Daily') {
        compoundingsPerYear = 365;
    } else if (compoundingFrequency === 'Quarterly') {
        compoundingsPerYear = 4;
    } else if (compoundingFrequency === 'Semi-Annually') {
        compoundingsPerYear = 2;
    } else if (compoundingFrequency === 'Annually') {
        compoundingsPerYear = 1;
    }
    
    const compoundingInterval = 12 / compoundingsPerYear; // In months
    
    // Initialize results
    let currentBalance = initialInvestment;
    const growthData = [];
    const yearlyData = [];
    let totalContributions = initialInvestment;
    
    // Calculate month-by-month growth
    for (let month = 0; month <= durationInMonths; month++) {
      if (month === 0) {
        // Initial month
        growthData.push({
          month,
          totalInvestment: initialInvestment,
          portfolioValue: initialInvestment
        });
        continue;
      }
      
      // Apply compounding if it's a compounding month
      if (month % compoundingInterval === 0) {
        const compoundingMonths = compoundingInterval;
        // Use compound interest formula: A = P(1 + r)^t
        currentBalance *= Math.pow(1 + (returnRate / 100 / compoundingsPerYear), 1);
      }
      
      // Add contribution if it's a contribution month
      if (month % contributionIntervalMonths === 0) {
        currentBalance += contributionAmount;
        totalContributions += contributionAmount;
      }
      
      // Store monthly data
      growthData.push({
        month,
        totalInvestment: totalContributions,
        portfolioValue: currentBalance
      });
      
      // Store yearly data at the end of each year
      if (month % 12 === 0 && month > 0) {
        const year = month / 12;
        
        yearlyData.push({
          year,
          startingBalance: yearlyData.length > 0 ? yearlyData[yearlyData.length - 1].endingBalance : initialInvestment,
          contribution: totalContributions - (yearlyData.length > 0 ? yearlyData[yearlyData.length - 1].totalContributions : initialInvestment),
          interestEarned: currentBalance - totalContributions,
          endingBalance: currentBalance,
          totalContributions: totalContributions,
          inflationAdjustedBalance: currentBalance / Math.pow(1 + (inflationRate / 100), year)
        });
      }
    }
    
    // Calculate final values
    const futureValue = currentBalance;
    const totalInterestEarned = futureValue - totalContributions;
    const taxOnGains = totalInterestEarned * (taxRate / 100);
    const afterTaxValue = futureValue - taxOnGains;
    const realFutureValue = futureValue / Math.pow(1 + (inflationRate / 100), durationInMonths / 12);
    
    // Generate recommendations based on risk tolerance
    const recommendations = generateRecommendations(params.riskTolerance || riskTolerance);
    
    return {
      futureValue,
      totalInvestment: totalContributions,
      totalInterestEarned,
      realFutureValue,
      taxAmount: taxOnGains,
      afterTaxValue,
      yearlyBreakdown: yearlyData,
      growthData,
      durationInYears: durationInMonths / 12,
      roi: (totalInterestEarned / totalContributions) * 100,
      recommendations
    };
  }
  
  function generateRecommendations(riskTolerance) {
    // Generate recommendations based on risk profile
    const recommendations = [];
    
    switch(riskTolerance) {
      case 'Conservative':
        recommendations.push(
          'Consider allocating 60-70% to government bonds and fixed income securities.',
          'Maintain 20-30% in blue-chip stocks for modest growth.',
          'Keep 10-20% in cash and money market instruments for liquidity.',
          'Review your portfolio annually to ensure it aligns with your conservative goals.'
        );
        break;
        
      case 'Moderate':
        recommendations.push(
          'Balance your portfolio with 40-50% in quality stocks across diverse sectors.',
          'Allocate 30-40% to government and corporate bonds.',
          'Consider 10-20% in real estate or REIT investments for diversification.',
          'Maintain 5-10% in cash for opportunities and emergencies.'
        );
        break;
        
      case 'Aggressive':
        recommendations.push(
          'Allocate 60-70% to growth stocks across various market caps and sectors.',
          'Consider 15-20% in emerging markets for higher growth potential.',
          'Limit bond allocation to 10-15% for minimal income stabilization.',
          'Explore 5-10% in alternative investments like venture capital or private equity.'
        );
        break;
        
      default:
        recommendations.push(
          'Diversify your investments across multiple asset classes to manage risk.',
          'Consider consulting with a financial advisor for personalized advice.',
          'Regularly review and rebalance your portfolio as your goals evolve.',
          'Maintain an emergency fund separate from your investment portfolio.'
        );
    }
    
    return recommendations;
  }
  
  // ====================================
  // Results Display Functions
  // ====================================
  function displayResults(data) {
    const resultsDiv = document.getElementById('calculationResults');
    if (!resultsDiv) return;
    
    // Format data for display
    const futureValue = data.futureValue || data.finalBalance;
    const totalInvestment = data.totalInvestment || data.totalContributions;
    const interestEarned = data.totalInterestEarned || data.interestEarned;
    const roi = data.roi || ((interestEarned / totalInvestment) * 100).toFixed(2);
    
    resultsDiv.innerHTML = `
      <div class="results-card">
        <div class="result-item">
          <h3>Total Investment</h3>
          <p class="result-value">${formatCurrency(totalInvestment)}</p>
        </div>
        <div class="result-item">
          <h3>Future Value</h3>
          <p class="result-value">${formatCurrency(futureValue)}</p>
        </div>
        <div class="result-item">
          <h3>Total Interest Earned</h3>
          <p class="result-value">${formatCurrency(interestEarned)}</p>
        </div>
        <div class="result-item">
          <h3>Return on Investment</h3>
          <p class="result-value">${parseFloat(roi).toFixed(2)}%</p>
        </div>
      </div>
      
      <div class="recommendations">
        <h3>Recommendations Based on Your Profile</h3>
        <ul>
          ${data.recommendations?.map(rec => `<li>${rec}</li>`).join('') || ''}
        </ul>
      </div>
    `;
    
    // Update year-by-year breakdown table
    updateYearByYearTable(data);
    
    // Update inflation & tax impact section
    updateInflationTaxSection(data);
  }
  
  function updateYearByYearTable(data) {
    const tableBody = document.querySelector('.results-table tbody');
    if (!tableBody) return;
    
    tableBody.innerHTML = ''; // Clear existing rows
    
    // Get yearly data (different structure depending on data source)
    const yearlyData = data.yearlyBreakdown || data.growthData?.filter(d => d.month % 12 === 0);
    
    if (!yearlyData || yearlyData.length === 0) return;
    
    // Add rows to the table
    yearlyData.forEach(yearData => {
      const year = yearData.year || (yearData.month / 12);
      if (year === 0) return; // Skip initial year
      
      const row = document.createElement('tr');
      
      // Format data based on structure
      const startBalance = yearData.startingBalance || 
                          (yearlyData[yearData.month/12 - 1]?.portfolioValue || 0);
      const endBalance = yearData.endingBalance || yearData.portfolioValue;
      const contribution = (yearData.contribution !== undefined) ? 
                          yearData.contribution : 
                          (yearData.totalInvestment - (yearlyData[yearData.month/12 - 1]?.totalInvestment || 0));
      const interest = (yearData.interestEarned !== undefined) ?
                      yearData.interestEarned :
                      (endBalance - startBalance - contribution);
      
      row.innerHTML = `
        <td>${Math.floor(year)}</td>
        <td>${formatCurrency(startBalance)}</td>
        <td>${formatCurrency(contribution)}</td>
        <td>${formatCurrency(interest)}</td>
        <td>${formatCurrency(endBalance)}</td>
      `;
      
      tableBody.appendChild(row);
    });
  }
  
  function updateInflationTaxSection(data) {
    // Update inflation impact
    const inflationCards = document.querySelectorAll('.flex-item:nth-child(1) .summary-card .summary-value');
    if (inflationCards.length >= 2) {
      const futureValue = data.futureValue || data.finalBalance;
      const realValue = data.realFutureValue || data.inflationAdjustedBalance;
      
      inflationCards[0].textContent = formatCurrency(futureValue);
      inflationCards[1].textContent = formatCurrency(realValue);
    }
    
    // Update tax impact
    const taxCards = document.querySelectorAll('.flex-item:nth-child(2) .summary-card .summary-value');
    if (taxCards.length >= 2) {
      const interestEarned = data.totalInterestEarned || data.interestEarned;
      const taxAmount = data.taxAmount || data.taxOnGains;
      
      taxCards[0].textContent = formatCurrency(interestEarned);
      taxCards[1].textContent = formatCurrency(taxAmount);
    }
  }
  
  function updateScenarioComparison(results) {
    // This compares the current scenario with a different scenario
    const scenarioSelect = document.querySelector('#scenarios select');
    const scenarioType = scenarioSelect ? scenarioSelect.value : 'Increase Monthly Contribution';
    
    // Get the scenario table
    const scenarioTable = document.querySelector('#scenarios .results-table tbody');
    if (!scenarioTable) return;
    
    if (scenarioType === 'Increase Monthly Contribution') {
      // Calculate a comparison scenario with double contribution
      const contribution = parseFloat(document.getElementById('monthlyContribution').value) || 0;
      const scenarioAValue = formatCurrency(contribution) + '/month';
      const scenarioBValue = formatCurrency(contribution * 2) + '/month';
      
      // Update scenario inputs
      const scenarioAInput = document.getElementById('scenario-a');
      const scenarioBInput = document.getElementById('scenario-b');
      
      if (scenarioAInput && scenarioBInput) {
        scenarioAInput.value = scenarioAValue;
        scenarioBInput.value = scenarioBValue;
      }
      
      // Get other calculation parameters
      const initialInvestment = parseFloat(document.getElementById('initialInvestment').value) || 0;
      const contributionFrequency = document.querySelector('.contribution-frequency')?.value || 'Monthly';
      const returnRate = parseFloat(document.getElementById('expectedReturnRate').value) || 0;
      const investmentDuration = parseInt(document.getElementById('yearsToInvest').value) || 0;
      const compoundingFrequency = document.getElementById('compoundingFrequency')?.value || 'Monthly';
      const inflationRate = parseFloat(document.getElementById('inflationRate')?.value || 2.5);
      const taxRate = parseFloat(document.getElementById('taxRate')?.value || 15);
      
      // Calculate scenario B with double contribution
      const scenarioBResults = calculateInvestmentGrowth({
        initialInvestment,
        contributionAmount: contribution * 2,
        contributionFrequency,
        returnRate,
        investmentDuration,
        durationUnit: 'Years',
        compoundingFrequency,
        inflationRate,
        taxRate
      });
      
      // Update scenario comparison table
      scenarioTable.innerHTML = '';
      
      // Add row for final balance
      const finalBalanceRow = document.createElement('tr');
      const difference = scenarioBResults.futureValue - results.futureValue;
      const percentDifference = (difference / results.futureValue * 100).toFixed(1);
      
      finalBalanceRow.innerHTML = `
        <td>Final Balance (${investmentDuration} years)</td>
        <td>${formatCurrency(results.futureValue)}</td>
        <td>${formatCurrency(scenarioBResults.futureValue)}</td>
        <td>+${formatCurrency(difference)} (${percentDifference}%)</td>
      `;
      scenarioTable.appendChild(finalBalanceRow);
      
      // Add row for total contributions
      const contributionsRow = document.createElement('tr');
      const contribDifference = scenarioBResults.totalInvestment - results.totalInvestment;
      
      contributionsRow.innerHTML = `
        <td>Total Contributions</td>
        <td>${formatCurrency(results.totalInvestment)}</td>
        <td>${formatCurrency(scenarioBResults.totalInvestment)}</td>
        <td>+${formatCurrency(contribDifference)}</td>
      `;
      scenarioTable.appendChild(contributionsRow);
      
      // Add row for total interest earned
      const interestRow = document.createElement('tr');
      const interestDifference = scenarioBResults.totalInterestEarned - results.totalInterestEarned;
      
      interestRow.innerHTML = `
        <td>Total Interest Earned</td>
        <td>${formatCurrency(results.totalInterestEarned)}</td>
        <td>${formatCurrency(scenarioBResults.totalInterestEarned)}</td>
        <td>+${formatCurrency(interestDifference)}</td>
      `;
      scenarioTable.appendChild(interestRow);
    }
  }
  
  function updatePortfolioAllocation(results, riskTolerance) {
    // Only update if portfolio tab exists
    const portfolioTab = document.getElementById('portfolio');
    if (!portfolioTab) return;
    
    // Generate asset allocation based on risk tolerance
    let allocation;
    
    switch(riskTolerance) {
      case 'Conservative':
        allocation = [
          { asset: 'Government Bonds', percentage: 40 },
          { asset: 'Corporate Bonds', percentage: 25 },
          { asset: 'Large Cap Stocks', percentage: 20 },
          { asset: 'Cash/Money Market', percentage: 15 }
        ];
        break;
        
      case 'Moderate':
        allocation = [
          { asset: 'Large Cap Stocks', percentage: 35 },
          { asset: 'Mid/Small Cap Stocks', percentage: 15 },
          { asset: 'Government Bonds', percentage: 20 },
          { asset: 'Corporate Bonds', percentage: 20 },
          { asset: 'Cash/Money Market', percentage: 10 }
        ];
        break;
        
      case 'Aggressive':
        allocation = [
          { asset: 'Large Cap Stocks', percentage: 30 },
          { asset: 'Mid/Small Cap Stocks', percentage: 30 },
          { asset: 'International Stocks', percentage: 20 },
          { asset: 'Corporate Bonds', percentage: 15 },
          { asset: 'Cash/Money Market', percentage: 5 }
        ];
        break;
        
      default:
        allocation = [
          { asset: 'Large Cap Stocks', percentage: 30 },
          { asset: 'Government Bonds', percentage: 30 },
          { asset: 'Corporate Bonds', percentage: 20 },
          { asset: 'Cash/Money Market', percentage: 10 },
          { asset: 'International Stocks', percentage: 10 }
        ];
    }
    
    // Update allocation table
    const allocationTable = portfolioTab.querySelector('.results-table tbody');
    if (allocationTable) {
      allocationTable.innerHTML = '';
      
      allocation.forEach(item => {
        const row = document.createElement('tr');
        const value = results.futureValue * (item.percentage / 100);
        
        row.innerHTML = `
          <td>${item.asset}</td>
          <td>${item.percentage}%</td>
          <td>${formatCurrency(value)}</td>
        `;
        
        allocationTable.appendChild(row);
      });
    }
  }
  
  // ====================================
  // Chart Rendering Functions
  // ====================================
  function renderChart(growthData) {
    if (!chartContainer) return;
    
    // Clear previous chart
    chartContainer.innerHTML = '';
    
    // Handle different data structures
    let formattedData = [];
    if (Array.isArray(growthData)) {
      if (growthData[0].hasOwnProperty('month')) {
        // Monthly data format
        formattedData = growthData;
      } else if (growthData[0].hasOwnProperty('year')) {
        // Convert yearly data to a format compatible with the chart
        formattedData = growthData.map((yearData, i) => ({
          month: yearData.year * 12,
          totalInvestment: yearData.totalContributions,
          portfolioValue: yearData.endingBalance
        }));
      }
    }
    
    // Create SVG
    const svg = d3.select('#chartContainer')
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Define scales
    const x = d3.scaleLinear()
      .domain([0, d3.max(formattedData, d => d.month)])
      .range([0, width]);
    
    const y = d3.scaleLinear()
      .domain([0, d3.max(formattedData, d => Math.max(d.totalInvestment, d.portfolioValue))])
      .range([height, 0]);
    
    // Add X axis
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickFormat(d => `Year ${Math.floor(d/12)}`).ticks(5));
    
    // Add Y axis
    svg.append('g')
      .call(d3.axisLeft(y).tickFormat(d => formatCurrency(d, true)));
    
    // Add lines
    const investmentLine = d3.line()
      .x(d => x(d.month))
      .y(d => y(d.totalInvestment));
    
    const valueLine = d3.line()
      .x(d => x(d.month))
      .y(d => y(d.portfolioValue));
    
    // Add investment line
    svg.append('path')
      .datum(formattedData)
      .attr('fill', 'none')
      .attr('stroke', '#4682B4')
      .attr('stroke-width', 2)
      .attr('d', investmentLine);
    
    // Add portfolio value line
    svg.append('path')
      .datum(formattedData)
      .attr('fill', 'none')
      .attr('stroke', '#228B22')
      .attr('stroke-width', 2)
      .attr('d', valueLine);
    
    // Add legend
    const legend = svg.append('g')
      .attr('font-family', 'sans-serif')
      .attr('font-size', 10)
      .attr('text-anchor', 'end')
      .selectAll('g')
      .data([{ color: '#4682B4', text: 'Total Investment' }, { color: '#228B22', text: 'Portfolio Value' }])
      .enter().append('g')
      .attr('transform', (d, i) => `translate(0,${i * 20})`);
    
    legend.append('rect')
      .attr('x', width - 19)
      .attr('width', 19)
      .attr('height', 19)
      .attr('fill', d => d.color);
    
    legend.append('text')
      .attr('x', width - 24)
      .attr('y', 9.5)
      .attr('dy', '0.32em')
      .text(d => d.text);
  }
  
  // ====================================
  // UI Helper Functions
  // ====================================
  function initTabs() {
    // Tab switching functionality
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const tabId = tab.getAttribute('data-tab');
        switchTab(tabId);
      });
    });
  }
  
  function switchTab(tabId) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(t => {
      t.classList.remove('active');
    });
    
    // Add active class to selected tab
    document.querySelector(`.tab[data-tab="${tabId}"]`)?.classList.add('active');
    
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(content => {
      content.classList.remove('active');
    });
    
    // Show corresponding tab content
    document.getElementById(tabId)?.classList.add('active');
    
    // Update state
    state.activeTab = tabId;
  }
  
  function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }
  }
  
  function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    applyTheme();
    localStorage.setItem('theme', state.theme);
  }
  
  function applyTheme() {
    if (state.theme === 'dark') {
      document.body.setAttribute('data-theme', 'dark');
    } else {
      document.body.removeAttribute('data-theme');
    }
    
    // Update theme toggle icons if they exist
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      const icon = themeToggle.querySelector('i');
      if (icon) {
        if (state.theme === 'dark') {
          icon.className = 'fas fa-sun';
        } else {
          icon.className = 'fas fa-moon';
        }
      }
    }
  }
  
  function initNavigation() {
    // Collapsible navigation sections
    document.querySelectorAll('.section-header').forEach(header => {
      header.addEventListener('click', () => {
        const section = header.parentElement;
        const items = section.querySelector('.section-items');
        const icon = header.querySelector('.fa-chevron-down, .fa-chevron-up');
        
        if (items) {
          const isActive = items.style.display === 'block' || (getComputedStyle(items).display !== 'none' && !items.style.display);
          
          items.style.display = isActive ? 'none' : 'block';
          
          if (icon) {
            icon.className = isActive ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
          }
        }
      });
    });

    // Mobile navigation toggle
    const collapseNavBtn = document.getElementById('collapseNav');
    if (collapseNavBtn) {
      collapseNavBtn.addEventListener('click', () => {
        const nav = document.querySelector('.left-navigation');
        if (nav) {
          nav.classList.toggle('collapsed');
        }
      });
    }
  }
  
  function setupInputValidation() {
    // Add validation to all numeric inputs
    const numericInputs = [
      document.getElementById('initialInvestment'),
      document.getElementById('monthlyContribution'),
      document.getElementById('yearsToInvest'),
      document.getElementById('expectedReturnRate'),
      document.getElementById('inflationRate'),
      document.getElementById('taxRate')
    ];
    
    numericInputs.forEach(input => {
      if (input) {
        input.addEventListener('input', () => {
          // Remove non-numeric characters except decimal point
          input.value = input.value.replace(/[^0-9.]/g, '');
          
          // Allow only one decimal point
          const parts = input.value.split('.');
          if (parts.length > 2) {
            input.value = parts[0] + '.' + parts.slice(1).join('');
          }
        });
      }
    });
  }
  
  function resetCalculator() {
    // Reset form to default values
    calculatorForm.reset();
    
    // Hide results container
    if (resultsContainer) {
      resultsContainer.style.display = 'none';
    }
    
    // Disable save button
    if (saveResultsButton) {
      saveResultsButton.disabled = true;
    }
    
    // Clear chart
    if (chartContainer) {
      chartContainer.innerHTML = '';
    }
    
    // Reset state
    state.calculationResults = null;
  }
  
  // ====================================
  // Utility Functions
  // ====================================
  function formatCurrency(value, abbreviated = false) {
    if (abbreviated && value >= 1000000) {
      return `KSh ${(value / 1000000).toFixed(1)}M`;
    } else if (abbreviated && value >= 1000) {
      return `KSh ${(value / 1000).toFixed(1)}K`;
    }
    
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }
  
  function saveCalculationParams(params) {
    localStorage.setItem('investmentCalculatorParams', JSON.stringify(params));
  }
  
  function loadCalculationParams() {
    const savedParams = localStorage.getItem('investmentCalculatorParams');
    return savedParams ? JSON.parse(savedParams) : null;
  }
  
  function saveCalculationHistory(results, params, name = '') {
    const history = loadCalculationHistory();
    const timestamp = new Date().toISOString();
    
    // Create a new history entry
    const newEntry = {
      id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
      name: name || `Calculation on ${new Date().toLocaleString()}`,
      timestamp,
      params,
      results: {
        futureValue: results.futureValue,
        totalContributions: results.totalInvestment,
        totalInterestEarned: results.totalInterestEarned,
        inflationAdjustedBalance: results.realFutureValue,
        taxAmount: results.taxAmount
      }
    };
    
    // Add to history
    history.unshift(newEntry);
    
    // Keep only the last 10 entries
    if (history.length > 10) {
      history.pop();
    }
    
    // Save updated history
    localStorage.setItem('calculationHistory', JSON.stringify(history));
    
    return newEntry.id;
  }
  
  function loadCalculationHistory() {
    const savedHistory = localStorage.getItem('calculationHistory');
    return savedHistory ? JSON.parse(savedHistory) : [];
  }
  
  // Initialize the calculator
  initialize();
});