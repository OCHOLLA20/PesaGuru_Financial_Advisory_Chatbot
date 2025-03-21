document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initAccountCharts();
    initOverviewCharts();
    
    // Set up event listeners
    setupAccountFilters();
    setupPeriodButtons();
    setupAccountActions();
    setupQuickActions();
});

// Function to initialize account-specific mini charts
function initAccountCharts() {
    // Savings Account Chart
    const savingsCtx = document.getElementById('savingsChart');
    if (savingsCtx) {
        new Chart(savingsCtx, {
            type: 'line',
            data: {
                labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [{
                    data: [950000, 970000, 1050000, 1100000, 1180000, 1245320],
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Current Account Chart
    const currentCtx = document.getElementById('currentChart');
    if (currentCtx) {
        new Chart(currentCtx, {
            type: 'line',
            data: {
                labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [{
                    data: [580000, 520000, 610000, 590000, 640000, 629330],
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Business Account Chart
    const businessCtx = document.getElementById('businessChart');
    if (businessCtx) {
        new Chart(businessCtx, {
            type: 'line',
            data: {
                labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [{
                    data: [400000, 550000, 680000, 780000, 900000, 1000000],
                    borderColor: '#FF9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        display: false
                    }
                }
            }
        });
    }
}

// Function to initialize overview charts
function initOverviewCharts() {
    // Income vs Expenses Chart
    const incomeExpenseCtx = document.getElementById('incomeExpenseChart');
    if (incomeExpenseCtx) {
        new Chart(incomeExpenseCtx, {
            type: 'bar',
            data: {
                labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [
                    {
                        label: 'Income',
                        data: [152000, 148000, 185000, 165000, 175000, 195000],
                        backgroundColor: '#4CAF50',
                        borderRadius: 4
                    },
                    {
                        label: 'Expenses',
                        data: [128000, 135000, 142000, 130000, 145000, 138000],
                        backgroundColor: '#f44336',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'KES ' + (value / 1000) + 'K';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Balance Trend Chart
    const balanceTrendCtx = document.getElementById('balanceTrendChart');
    if (balanceTrendCtx) {
        new Chart(balanceTrendCtx, {
            type: 'line',
            data: {
                labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
                datasets: [
                    {
                        label: 'Savings',
                        data: [950000, 970000, 1050000, 1100000, 1180000, 1245320],
                        borderColor: '#4CAF50',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 3
                    },
                    {
                        label: 'Current',
                        data: [580000, 520000, 610000, 590000, 640000, 629330],
                        borderColor: '#2196F3',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 3
                    },
                    {
                        label: 'Business',
                        data: [400000, 550000, 680000, 780000, 900000, 1000000],
                        borderColor: '#FF9800',
                        borderWidth: 2,
                        tension: 0.4,
                        pointRadius: 3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': KES ' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'KES ' + (value / 1000) + 'K';
                            }
                        }
                    }
                }
            }
        });
    }
}

// Function to set up account filter
function setupAccountFilters() {
    const accountFilter = document.getElementById('account-filter');
    if (accountFilter) {
        accountFilter.addEventListener('change', function() {
            const selectedAccount = this.value;
            // Update the chart data based on the selected account
            if (selectedAccount === 'current') {
                // Update current account chart data
                updateChartData('current');
            } else if (selectedAccount === 'business') {
                // Update business account chart data
                updateChartData('business');
            } else {
                // Update all accounts chart data
                updateChartData('all');
            }
            // Refresh the charts
            refreshCharts();
            // Update the balance
            updateBalance(selectedAccount);
            // Update the account summary
            updateAccountSummary(selectedAccount);
            // Update the transaction history
            updateTransactionHistory(selectedAccount);
            // Update the transaction trend
            updateTransactionTrend(selectedAccount);
            // Update the income expense trend
            updateIncomeExpenseTrend(selectedAccount);
            // Update the balance trend
            updateBalanceTrend(selectedAccount);
            // Update the investment strategy recommendations
            updateInvestmentStrategyRecommendations(selectedAccount);
            // Update the learning resources recommendations
            updateLearningResources(selectedAccount);
        });
    }
}

// Function to set up period buttons
function setupPeriodButtons() {
    const periodButtons = document.querySelectorAll('.period-button');
    if (periodButtons.length > 0) {
        periodButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                periodButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                this.classList.add('active');
                
                const period = this.dataset.period;
                updateDataByPeriod(period);
            });
        });
    }
}

// Function to set up account actions
function setupAccountActions() {
    const transferBtn = document.getElementById('transfer-btn');
    if (transferBtn) {
        transferBtn.addEventListener('click', function() {
            showTransferModal();
        });
    }
    
    const payBillBtn = document.getElementById('pay-bill-btn');
    if (payBillBtn) {
        payBillBtn.addEventListener('click', function() {
            showPayBillModal();
        });
    }
    
    const depositBtn = document.getElementById('deposit-btn');
    if (depositBtn) {
        depositBtn.addEventListener('click', function() {
            showDepositModal();
        });
    }
}

// Function to set up quick actions
function setupQuickActions() {
    const quickActions = document.querySelectorAll('.quick-action');
    if (quickActions.length > 0) {
        quickActions.forEach(action => {
            action.addEventListener('click', function() {
                const actionType = this.dataset.action;
                handleQuickAction(actionType);
            });
        });
    }
}

// Function to update chart data based on selected account
function updateChartData(accountType) {
    // Implementation would depend on how you're storing your data
    console.log(`Updating chart data for account: ${accountType}`);
    // This would typically involve fetching data from an API
    // and updating the chart datasets
}

// Function to refresh charts
function refreshCharts() {
    // Get all chart instances and update them
    const charts = Chart.instances;
    for (let key in charts) {
        if (charts.hasOwnProperty(key)) {
            charts[key].update();
        }
    }
}

// Function to update balance display
function updateBalance(accountType) {
    const balanceElement = document.getElementById('balance-display');
    if (!balanceElement) return;
    
    let balance = 0;
    
    switch(accountType) {
        case 'savings':
            balance = 1245320;
            break;
        case 'current':
            balance = 629330;
            break;
        case 'business':
            balance = 1000000;
            break;
        default:
            balance = 1245320 + 629330 + 1000000;
    }
    
    balanceElement.textContent = `KES ${balance.toLocaleString()}`;
}

// Function to update account summary
function updateAccountSummary(accountType) {
    console.log(`Updating account summary for: ${accountType}`);
    // This would typically involve updating UI elements with account-specific information
}

// Function to update transaction history
function updateTransactionHistory(accountType) {
    const transactionList = document.getElementById('transaction-list');
    if (!transactionList) return;
    
    // Clear existing transactions
    transactionList.innerHTML = '';
    
    // This would typically involve fetching transaction data from an API
    // and populating the transaction list
    console.log(`Updating transaction history for: ${accountType}`);
}

// Function to update transaction trend
function updateTransactionTrend(accountType) {
    console.log(`Updating transaction trend for: ${accountType}`);
    // This would typically involve updating a chart with transaction trend data
}

// Function to update income vs expense trend
function updateIncomeExpenseTrend(accountType) {
    console.log(`Updating income vs expense trend for: ${accountType}`);
    // This would typically involve updating the income vs expense chart
}

// Function to update balance trend
function updateBalanceTrend(accountType) {
    console.log(`Updating balance trend for: ${accountType}`);
    // This would typically involve updating the balance trend chart
}

// Function to update investment strategy recommendations
function updateInvestmentStrategyRecommendations(accountType) {
    console.log(`Updating investment recommendations for: ${accountType}`);
    // This would typically involve updating UI elements with investment recommendations
}

// Function to update learning resources
function updateLearningResources(accountType) {
    console.log(`Updating learning resources for: ${accountType}`);
    // This would typically involve updating UI elements with learning resources
}

// Function to update data based on selected period
function updateDataByPeriod(period) {
    console.log(`Updating data for period: ${period}`);
    // This would typically involve fetching period-specific data
    // and updating all relevant charts and displays
}

// Function to show transfer modal
function showTransferModal() {
    const modal = document.getElementById('transfer-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Function to show pay bill modal
function showPayBillModal() {
    const modal = document.getElementById('pay-bill-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Function to show deposit modal
function showDepositModal() {
    const modal = document.getElementById('deposit-modal');
    if (modal) {
        modal.classList.add('show');
    }
}

// Function to handle quick actions
function handleQuickAction(actionType) {
    console.log(`Handling quick action: ${actionType}`);
    
    switch(actionType) {
        case 'transfer':
            showTransferModal();
            break;
        case 'pay-bill':
            showPayBillModal();
            break;
        case 'deposit':
            showDepositModal();
            break;
        case 'statement':
            downloadStatement();
            break;
        default:
            console.log('Unknown action type');
    }
}

// Function to download statement
function downloadStatement() {
    console.log('Downloading statement...');
    // This would typically involve generating and downloading a PDF statement
    alert('Statement download initiated');
}