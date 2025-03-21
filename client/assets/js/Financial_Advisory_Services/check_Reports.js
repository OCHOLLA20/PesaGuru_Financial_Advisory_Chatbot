document.addEventListener('DOMContentLoaded', function() {
    // ==========================================
    // Initialize Charts
    // ==========================================
    initializeCharts();
    
    // ==========================================
    // Setup Event Listeners
    // ==========================================
    setupEventListeners();
    
    // ==========================================
    // Initialize Data Table Functionality
    // ==========================================
    initializeDataTable();
});

/**
 * Initializes the expense breakdown and trend charts
 */
function initializeCharts() {
    // Sample data for charts - this would typically come from an API
    const chartData = {
        expenses: {
            categories: ['Food & Groceries', 'Transportation', 'Utilities', 'Education', 'Entertainment', 'Others'],
            values: [5650, 1300, 6350, 1200, 900, 4200],
            colors: ['#0099ff', '#ff9933', '#33cc33', '#9966ff', '#ff3399', '#999999']
        },
        trends: {
            months: ['Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May'],
            expenses: [32500, 29800, 31200, 34500, 32000, 35842],
            income: [45000, 48000, 47500, 49000, 48500, 52600]
        }
    };
    
    // Initialize Expense Breakdown Chart
    initializeExpenseChart(chartData.expenses);
    
    // Initialize Monthly Trend Chart
    initializeTrendChart(chartData.trends);
}

/**
 * Initializes the expense breakdown pie chart
 * @param {Object} data - Object containing expense categories, values and colors
 */
function initializeExpenseChart(data) {
    const expenseCtx = document.getElementById('expenseChart').getContext('2d');
    window.expenseChart = new Chart(expenseCtx, {
        type: 'pie',
        data: {
            labels: data.categories,
            datasets: [{
                data: data.values,
                backgroundColor: data.colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${label}: KES ${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initializes the monthly trend line chart
 * @param {Object} data - Object containing trend months and values
 */
function initializeTrendChart(data) {
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    window.trendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: data.months,
            datasets: [{
                label: 'Expenses',
                data: data.expenses,
                borderColor: '#4361ee',
                backgroundColor: 'rgba(67, 97, 238, 0.1)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Income',
                data: data.income,
                borderColor: '#32CD32',
                backgroundColor: 'rgba(50, 205, 50, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.raw || 0;
                            return `${label}: KES ${value.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Sets up event listeners for user interactions
 */
function setupEventListeners() {
    // Chart tab switching
    setupChartTabSwitching();
    
    // Filter changes
    setupFilterListeners();
    
    // Export button
    setupExportButton();
    
    // Transaction search
    setupTransactionSearch();
    
    // Toggle theme
    setupThemeToggle();
    
    // Sidebar toggle for mobile
    setupSidebarToggle();
    
    // Chatbot toggle
    setupChatbotToggle();
    
    // Currency toggle
    setupCurrencyToggle();
}

/**
 * Setup event listeners for switching between chart types
 */
function setupChartTabSwitching() {
    const chartTabs = document.querySelectorAll('.chart-tab');
    
    chartTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Get all siblings
            const siblings = Array.from(this.parentElement.children);
            
            // Remove active class from all tabs
            siblings.forEach(sib => sib.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Get the chart container and determine which chart we're updating
            const chartContainer = this.closest('.chart-container');
            const chartCanvas = chartContainer.querySelector('canvas');
            const chartType = this.textContent.trim();
            
            // Get the chart instance
            const chartInstance = Chart.getChart(chartCanvas);
            
            // Update chart configuration based on the selected tab
            updateChartType(chartInstance, chartType, chartCanvas.id);
        });
    });
}

/**
 * Updates the chart type based on user selection
 * @param {Chart} chartInstance - The Chart.js instance
 * @param {string} chartType - The new chart type
 * @param {string} chartId - The ID of the chart canvas element
 */
function updateChartType(chartInstance, chartType, chartId) {
    // Store the original data
    const originalData = chartInstance.data;
    
    // Different chart types need different data structures
    if (chartType === 'Pie Chart') {
        chartInstance.config.type = 'pie';
        
        // Adjust legend position for pie chart
        chartInstance.options.plugins.legend.position = 'right';
        
        // Remove scales for pie chart
        chartInstance.options.scales = {};
    } 
    else if (chartType === 'Bar Chart') {
        chartInstance.config.type = 'bar';
        
        // Adjust legend position for bar chart
        chartInstance.options.plugins.legend.position = 'top';
        
        // Set scales for bar/line charts
        chartInstance.options.scales = {
            y: {
                beginAtZero: false,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    } 
    else if (chartType === 'Line Chart') {
        chartInstance.config.type = 'line';
        
        // Set tension for line chart
        if (chartInstance.data.datasets) {
            chartInstance.data.datasets.forEach(dataset => {
                dataset.tension = 0.4;
            });
        }
        
        // Adjust legend position for line chart
        chartInstance.options.plugins.legend.position = 'top';
        
        // Set scales for bar/line charts
        chartInstance.options.scales = {
            y: {
                beginAtZero: false,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                }
            },
            x: {
                grid: {
                    display: false
                }
            }
        };
    }
    
    // Update the chart
    chartInstance.update();
}

/**
 * Setup listeners for the filter dropdowns
 */
function setupFilterListeners() {
    // Time period dropdown to show/hide date range inputs
    const timePeriod = document.getElementById('time-period');
    const dateRange = document.querySelector('.date-range');
    
    if (timePeriod && dateRange) {
        timePeriod.addEventListener('change', function() {
            if (this.value === 'custom') {
                dateRange.style.display = 'flex';
            } else {
                dateRange.style.display = 'none';
                
                // Refresh reports based on the selected time period
                refreshReports(this.value);
            }
        });
    }
    
    // Date range inputs
    const dateFrom = document.getElementById('date-from');
    const dateTo = document.getElementById('date-to');
    
    if (dateFrom && dateTo) {
        // Set default dates (last 30 days)
        const today = new Date();
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(today.getDate() - 30);
        
        dateFrom.valueAsDate = thirtyDaysAgo;
        dateTo.valueAsDate = today;
        
        // Add event listeners to update report when dates change
        [dateFrom, dateTo].forEach(dateInput => {
            dateInput.addEventListener('change', function() {
                if (dateFrom.value && dateTo.value) {
                    refreshReports('custom', {
                        from: dateFrom.value,
                        to: dateTo.value
                    });
                }
            });
        });
    }
    
    // Report type dropdown
    const reportType = document.getElementById('report-type');
    if (reportType) {
        reportType.addEventListener('change', function() {
            refreshReports(timePeriod.value, null, this.value);
        });
    }
    
    // Category filter dropdown
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', function() {
            filterTransactionsByCategory(this.value);
        });
    }
}

/**
 * Setup the export button functionality
 */
function setupExportButton() {
    const exportBtn = document.querySelector('.export-btn');
    
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Simulate export loading
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            
            // Simulate export process (would be replaced with actual API call)
            setTimeout(() => {
                // Reset button
                this.innerHTML = '<i class="fas fa-download"></i> Export Reports';
                
                // Show success notification
                showNotification('Report exported successfully!', 'success');
            }, 1500);
        });
    }
}

/**
 * Setup transaction search functionality
 */
function setupTransactionSearch() {
    const transactionSearch = document.getElementById('transaction-search');
    
    if (transactionSearch) {
        transactionSearch.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            filterTransactionsBySearch(searchTerm);
        });
    }
}

/**
 * Setup theme toggle functionality
 */
function setupThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    
    if (themeToggle) {
        // Check if dark mode is enabled in localStorage
        const isDarkMode = localStorage.getItem('pesaguru-dark-mode') === 'true';
        
        // Apply dark mode if it was previously enabled
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            themeToggle.innerHTML = '<i class="fas fa-sun"></i><span class="sr-only">Toggle light mode</span>';
        }
        
        themeToggle.addEventListener('click', function() {
            // Toggle dark mode class on body
            document.body.classList.toggle('dark-mode');
            
            // Update button icon
            const isDarkModeNow = document.body.classList.contains('dark-mode');
            
            if (isDarkModeNow) {
                this.innerHTML = '<i class="fas fa-sun"></i><span class="sr-only">Toggle light mode</span>';
            } else {
                this.innerHTML = '<i class="fas fa-moon"></i><span class="sr-only">Toggle dark mode</span>';
            }
            
            // Save preference to localStorage
            localStorage.setItem('pesaguru-dark-mode', isDarkModeNow);
        });
    }
}

/**
 * Setup sidebar toggle for mobile devices
 */
function setupSidebarToggle() {
    // Add mobile menu toggle button if not already present
    const header = document.querySelector('.header');
    
    if (header && !document.querySelector('.mobile-menu-toggle')) {
        const mobileToggle = document.createElement('button');
        mobileToggle.className = 'mobile-menu-toggle';
        mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
        mobileToggle.setAttribute('aria-label', 'Toggle navigation menu');
        
        header.querySelector('.header-left').prepend(mobileToggle);
        
        // Add event listener
        mobileToggle.addEventListener('click', function() {
            document.querySelector('.sidebar').classList.toggle('active');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(event) {
            const sidebar = document.querySelector('.sidebar');
            const toggle = document.querySelector('.mobile-menu-toggle');
            
            if (sidebar.classList.contains('active') && 
                !sidebar.contains(event.target) && 
                event.target !== toggle && 
                !toggle.contains(event.target)) {
                sidebar.classList.remove('active');
            }
        });
    }
}

/**
 * Setup chatbot toggle functionality
 */
function setupChatbotToggle() {
    const chatbotToggle = document.querySelector('.chatbot-toggle');
    
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', function() {
            // Create chatbot modal if it doesn't exist
            if (!document.querySelector('.chatbot-modal')) {
                createChatbotModal();
            } else {
                // Toggle existing modal
                document.querySelector('.chatbot-modal').classList.toggle('active');
            }
        });
    }
}

/**
 * Creates the chatbot modal
 */
function createChatbotModal() {
    const modal = document.createElement('div');
    modal.className = 'chatbot-modal active';
    
    modal.innerHTML = `
        <div class="chatbot-header">
            <h3><i class="fas fa-robot"></i> PesaGuru Assistant</h3>
            <button class="close-chatbot"><i class="fas fa-times"></i></button>
        </div>
        <div class="chatbot-messages">
            <div class="message bot">
                <div class="message-content">
                    Hello! I'm your PesaGuru assistant. How can I help you with your finances today?
                </div>
                <div class="message-time">Just now</div>
            </div>
        </div>
        <div class="chatbot-input">
            <input type="text" placeholder="Type your question here..." />
            <button class="send-message"><i class="fas fa-paper-plane"></i></button>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.querySelector('.close-chatbot').addEventListener('click', function() {
        modal.classList.remove('active');
    });
    
    const inputField = modal.querySelector('input');
    const sendButton = modal.querySelector('.send-message');
    
    // Function to send message
    const sendMessage = () => {
        const message = inputField.value.trim();
        if (message) {
            // Add user message
            addChatMessage(message, 'user');
            inputField.value = '';
            
            // Simulate bot response after a delay
            setTimeout(() => {
                // This would typically be replaced with an actual API call
                const responses = [
                    "I see you've spent KES 35,842 this month. That's 12% more than last month.",
                    "Based on your spending patterns, I suggest reducing your entertainment budget by 10%.",
                    "You're on track to reach your savings goal of KES 100,000 by December!",
                    "I notice your utility bills are higher than usual. Would you like some tips to reduce them?"
                ];
                
                const randomResponse = responses[Math.floor(Math.random() * responses.length)];
                addChatMessage(randomResponse, 'bot');
            }, 1000);
        }
    };
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    inputField.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Focus the input field
    inputField.focus();
}

/**
 * Adds a message to the chatbot
 * @param {string} message - The message text
 * @param {string} sender - Either 'user' or 'bot'
 */
function addChatMessage(message, sender) {
    const chatMessages = document.querySelector('.chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${timeString}</div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Initialize data table functionality including pagination
 */
function initializeDataTable() {
    setupPagination();
    
    // Add click handlers for transaction action buttons
    const actionButtons = document.querySelectorAll('.report-table .btn-icon');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Get the transaction details from the row
            const row = this.closest('tr');
            const date = row.cells[0].textContent;
            const description = row.cells[1].textContent;
            const amount = row.cells[3].textContent;
            
            // Create and show action menu
            showTransactionActionMenu(this, { date, description, amount });
        });
    });
    
    // Add click handlers for transaction rows
    const tableRows = document.querySelectorAll('.report-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            // Show transaction details modal
            const date = this.cells[0].textContent;
            const description = this.cells[1].textContent;
            const category = this.cells[2].querySelector('.category-badge').textContent;
            const amount = this.cells[3].textContent;
            const paymentMethod = this.cells[4].textContent;
            
            showTransactionDetailsModal({ date, description, category, amount, paymentMethod });
        });
    });
}

/**
 * Setup pagination functionality
 */
function setupPagination() {
    const paginationButtons = document.querySelectorAll('.pagination-buttons button');
    
    paginationButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Ignore disabled buttons
            if (this.hasAttribute('disabled')) {
                return;
            }
            
            // Remove active class from all buttons
            paginationButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button if it's a page number
            if (!this.querySelector('i')) {
                this.classList.add('active');
            }
            
            // Handle pagination actions
            if (this.querySelector('.fa-chevron-left')) {
                // Previous page
                const activePage = document.querySelector('.pagination-buttons button.active');
                if (activePage && activePage.previousElementSibling && !activePage.previousElementSibling.querySelector('i')) {
                    activePage.previousElementSibling.click();
                }
            } 
            else if (this.querySelector('.fa-chevron-right')) {
                // Next page
                const activePage = document.querySelector('.pagination-buttons button.active');
                if (activePage && activePage.nextElementSibling && !activePage.nextElementSibling.querySelector('i')) {
                    activePage.nextElementSibling.click();
                }
            }
            else {
                // Page number clicked - fetch data for that page
                const pageNumber = parseInt(this.textContent);
                fetchPageData(pageNumber);
            }
        });
    });
}

/**
 * Fetches data for the specified page
 * @param {number} pageNumber - The page number to fetch
 */
function fetchPageData(pageNumber) {
    // This would typically be an API call to get data for the specific page
    console.log(`Fetching data for page ${pageNumber}`);
    
    // Simulate loading state
    const tableBody = document.querySelector('.report-table tbody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <i class="fas fa-spinner fa-spin"></i> Loading transactions...
            </td>
        </tr>
    `;
    
    // For demo purposes, we'll just show different data based on page number
    setTimeout(() => {
        // This would be replaced with actual API response data
        if (pageNumber === 1) {
            resetTableToOriginalData();
        } else {
            // Show some different dummy data for other pages
            const dummyData = generateDummyDataForPage(pageNumber);
            updateTableWithNewData(dummyData);
        }
        
        // Update navigation buttons state
        updatePaginationState(pageNumber);
    }, 800);
}

/**
 * Reset the table to its original data (for page 1)
 */
function resetTableToOriginalData() {
    // The original data is already in the HTML, so we don't need to do anything
    // This function would be more useful in a real application where we're
    // dynamically loading data
}

/**
 * Generates dummy data for pagination demonstration
 * @param {number} pageNumber - The page number
 * @returns {Array} - Array of transaction data
 */
function generateDummyDataForPage(pageNumber) {
    // Sample categories with their badge classes
    const categories = [
        { name: 'Food', class: 'category-food' },
        { name: 'Transport', class: 'category-transport' },
        { name: 'Utilities', class: 'category-utilities' },
        { name: 'Education', class: 'category-education' },
        { name: 'Entertainment', class: 'category-entertainment' }
    ];
    
    // Sample payment methods
    const paymentMethods = ['Credit Card', 'Mobile Payment', 'Bank Transfer', 'Cash'];
    
    // Generate dummy data based on page number
    const data = [];
    const baseDate = new Date(2024, 3, 25); // April 25, 2024
    
    // Calculate date offset based on page number
    const daysOffset = (pageNumber - 1) * 10;
    
    for (let i = 0; i < 8; i++) {
        const date = new Date(baseDate);
        date.setDate(date.getDate() - (i + daysOffset));
        
        const category = categories[Math.floor(Math.random() * categories.length)];
        const amount = Math.floor(Math.random() * 5000) + 500;
        
        data.push({
            date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
            description: getSampleDescription(category.name),
            category: {
                name: category.name,
                class: category.class
            },
            amount: `KES ${amount}`,
            paymentMethod: paymentMethods[Math.floor(Math.random() * paymentMethods.length)]
        });
    }
    
    return data;
}

/**
 * Gets a sample description based on the category
 * @param {string} category - The transaction category
 * @returns {string} - A relevant description
 */
function getSampleDescription(category) {
    const descriptions = {
        'Food': ['Grocery Shopping', 'Restaurant Dinner', 'Coffee Shop', 'Food Delivery', 'Bakery Items'],
        'Transport': ['Uber Ride', 'Taxi Fare', 'Bus Ticket', 'Fuel Purchase', 'Car Maintenance'],
        'Utilities': ['Electricity Bill', 'Water Bill', 'Internet Bill', 'Mobile Phone Bill', 'Gas Bill'],
        'Education': ['Online Course', 'Textbook Purchase', 'School Fees', 'Tuition Payment', 'Stationery Items'],
        'Entertainment': ['Movie Tickets', 'Concert Tickets', 'Streaming Subscription', 'Gaming Purchase', 'Museum Entry']
    };
    
    const options = descriptions[category] || ['Miscellaneous Purchase'];
    return options[Math.floor(Math.random() * options.length)];
}

/**
 * Updates the table with new data
 * @param {Array} data - Array of transaction objects
 */
/**
 * Shows a transaction details modal
 * @param {Object} transaction - The transaction details
 */
function showTransactionDetailsModal(transaction) {
    // Create modal if it doesn't exist
    if (!document.querySelector('.transaction-details-modal')) {
        const modal = document.createElement('div');
        modal.className = 'transaction-details-modal';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Transaction Details</h3>
                    <button class="close-modal"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <div class="transaction-detail">
                        <span class="label">Date:</span>
                        <span class="value">${transaction.date}</span>
                    </div>
                    <div class="transaction-detail">
                        <span class="label">Description:</span>
                        <span class="value">${transaction.description}</span>
                    </div>
                    <div class="transaction-detail">
                        <span class="label">Category:</span>
                        <span class="value">${transaction.category}</span>
                    </div>
                    <div class="transaction-detail">
                        <span class="label">Amount:</span>
                        <span class="value">${transaction.amount}</span>
                    </div>
                    <div class="transaction-detail">
                        <span class="label">Payment Method:</span>
                        <span class="value">${transaction.paymentMethod}</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-outline modal-close">Close</button>
                    <button class="btn-primary">Edit Transaction</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.querySelector('.btn-primary').addEventListener('click', () => {
            modal.remove();
            showNotification('Edit transaction functionality would open here', 'info');
        });
        
        // Close when clicking outside
        modal.addEventListener('click', function(event) {
            if (event.target === modal) {
                modal.remove();
            }
        });
    } else {
        // Update existing modal
        const modal = document.querySelector('.transaction-details-modal');
        const fields = modal.querySelectorAll('.transaction-detail .value');
        fields[0].textContent = transaction.date;
        fields[1].textContent = transaction.description;
        fields[2].textContent = transaction.category;
        fields[3].textContent = transaction.amount;
        fields[4].textContent = transaction.paymentMethod;
    }
}

/**
 * Shows a delete confirmation dialog
 * @param {Object} transaction - The transaction to delete
 */
function showDeleteConfirmation(transaction) {
    const modal = document.createElement('div');
    modal.className = 'confirmation-modal';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Confirm Deletion</h3>
                <button class="close-modal"><i class="fas fa-times"></i></button>
            </div>
            <div class="modal-body">
                <p>Are you sure you want to delete the following transaction?</p>
                <div class="transaction-detail">
                    <span class="label">Date:</span>
                    <span class="value">${transaction.date}</span>
                </div>
                <div class="transaction-detail">
                    <span class="label">Description:</span>
                    <span class="value">${transaction.description}</span>
                </div>
                <div class="transaction-detail">
                    <span class="label">Amount:</span>
                    <span class="value">${transaction.amount}</span>
                </div>
                <p class="text-danger">This action cannot be undone!</p>
            </div>
            <div class="modal-footer">
                <button class="btn-outline modal-close">Cancel</button>
                <button class="btn-danger">Delete Transaction</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.querySelector('.close-modal').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.querySelector('.modal-close').addEventListener('click', () => {
        modal.remove();
    });
    
    modal.querySelector('.btn-danger').addEventListener('click', () => {
        // This would typically make an API call to delete the transaction
        modal.remove();
        showNotification('Transaction deleted successfully', 'success');
        
        // Remove the row from the table (in a real app, you'd confirm deletion from the server first)
        const rows = document.querySelectorAll('.report-table tbody tr');
        rows.forEach(row => {
            if (row.cells[0].textContent === transaction.date && 
                row.cells[1].textContent === transaction.description) {
                row.remove();
            }
        });
    });
    
    // Close when clicking outside
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.remove();
        }
    });
}

/**
 * Shows a notification message
 * @param {string} message - The message to display
 * @param {string} type - The notification type (success, error, info, warning)
 */
function showNotification(message, type = 'info') {
    // Remove any existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Add icon based on type
    let icon;
    switch (type) {
        case 'success':
            icon = 'fa-check-circle';
            break;
        case 'error':
            icon = 'fa-exclamation-circle';
            break;
        case 'warning':
            icon = 'fa-exclamation-triangle';
            break;
        default:
            icon = 'fa-info-circle';
    }
    
    notification.innerHTML = `
        <i class="fas ${icon}"></i>
        <span>${message}</span>
        <button class="close-notification"><i class="fas fa-times"></i></button>
    `;
    
    document.body.appendChild(notification);
    
    // Add event listener to close button
    notification.querySelector('.close-notification').addEventListener('click', () => {
        notification.remove();
    });
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.classList.add('notification-hiding');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

/**
 * Refreshes the reports based on filters
 * @param {string} timePeriod - The selected time period
 * @param {Object} dateRange - Custom date range (if applicable)
 * @param {string} reportType - The type of report
 */
function refreshReports(timePeriod, dateRange, reportType) {
    // Show loading state for charts
    showLoadingState();
    
    // This would typically be an API call to get filtered data
    // For demo purposes, we'll just show different data after a delay
    setTimeout(() => {
        // Update summary cards
        updateSummaryCards(timePeriod, reportType);
        
        // Update charts
        updateChartsWithFilteredData(timePeriod, dateRange, reportType);
        
        // Show notification
        showNotification(`Reports updated for ${getTimePeriodText(timePeriod, dateRange)}`, 'success');
    }, 1000);
}

/**
 * Shows loading state for charts and summary cards
 */
function showLoadingState() {
    // Add loading overlay to charts
    const chartContainers = document.querySelectorAll('.chart-container .chart-body');
    chartContainers.forEach(container => {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'loading-overlay';
        loadingOverlay.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        container.appendChild(loadingOverlay);
    });
    
    // Add loading state to summary cards
    const summaryValues = document.querySelectorAll('.summary-card .value');
    summaryValues.forEach(value => {
        value.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    });
}

/**
 * Updates summary cards with filtered data
 * @param {string} timePeriod - The selected time period
 * @param {string} reportType - The type of report
 */
function updateSummaryCards(timePeriod, reportType) {
    // In a real application, this data would come from an API
    // For demo purposes, we'll just generate some values
    
    const summaryCards = document.querySelectorAll('.summary-card');
    
    // Sample data for different time periods
    const summaryData = {
        'last-month': {
            expenses: 'KES 35,842',
            income: 'KES 52,600',
            savings: 'KES 16,758',
            budgetUtilization: '83%'
        },
        'last-quarter': {
            expenses: 'KES 102,542',
            income: 'KES 158,600',
            savings: 'KES 56,058',
            budgetUtilization: '78%'
        },
        'last-year': {
            expenses: 'KES 385,250',
            income: 'KES 630,000',
            savings: 'KES 244,750',
            budgetUtilization: '75%'
        },
        'custom': {
            expenses: 'KES 48,320',
            income: 'KES 65,200',
            savings: 'KES 16,880',
            budgetUtilization: '85%'
        }
    };
    
    // Update summary card values
    if (summaryData[timePeriod]) {
        const data = summaryData[timePeriod];
        summaryCards[0].querySelector('.value').textContent = data.expenses;
        summaryCards[1].querySelector('.value').textContent = data.income;
        summaryCards[2].querySelector('.value').textContent = data.savings;
        summaryCards[3].querySelector('.value').textContent = data.budgetUtilization;
    }
    
    // Update trends based on time period
    const trends = document.querySelectorAll('.summary-card .trend');
    
    // Sample trends for different time periods
    const trendData = {
        'last-month': [
            { value: 12, direction: 'up', isPositive: false },
            { value: 8, direction: 'up', isPositive: true },
            { value: 5, direction: 'up', isPositive: true },
            { value: 7, direction: 'up', isPositive: false }
        ],
        'last-quarter': [
            { value: 8, direction: 'up', isPositive: false },
            { value: 12, direction: 'up', isPositive: true },
            { value: 15, direction: 'up', isPositive: true },
            { value: 3, direction: 'down', isPositive: true }
        ],
        'last-year': [
            { value: 5, direction: 'down', isPositive: true },
            { value: 10, direction: 'up', isPositive: true },
            { value: 20, direction: 'up', isPositive: true },
            { value: 10, direction: 'down', isPositive: true }
        ],
        'custom': [
            { value: 15, direction: 'up', isPositive: false },
            { value: 7, direction: 'up', isPositive: true },
            { value: 4, direction: 'down', isPositive: false },
            { value: 9, direction: 'up', isPositive: false }
        ]
    };
    
    // Update trend values
    if (trendData[timePeriod]) {
        trendData[timePeriod].forEach((trend, index) => {
            const trendElement = trends[index];
            const iconClass = trend.direction === 'up' ? 'fa-arrow-up' : 'fa-arrow-down';
            const cssClass = trend.isPositive ? 'positive' : 'negative';
            
            trendElement.innerHTML = `
                <i class="fas ${iconClass}"></i> ${trend.value}% vs previous period
            `;
            
            trendElement.className = `trend ${cssClass}`;
        });
    }
}

/**
 * Updates charts with filtered data
 * @param {string} timePeriod - The selected time period
 * @param {Object} dateRange - Custom date range (if applicable)
 * @param {string} reportType - The type of report
 */
function updateChartsWithFilteredData(timePeriod, dateRange, reportType) {
    // Remove loading overlays
    const loadingOverlays = document.querySelectorAll('.loading-overlay');
    loadingOverlays.forEach(overlay => overlay.remove());
    
    // Sample data for expense breakdown
    const expenseBreakdownData = {
        'last-month': {
            categories: ['Food & Groceries', 'Transportation', 'Utilities', 'Education', 'Entertainment', 'Others'],
            values: [5650, 1300, 6350, 1200, 900, 4200]
        },
        'last-quarter': {
            categories: ['Food & Groceries', 'Transportation', 'Utilities', 'Education', 'Entertainment', 'Others'],
            values: [16800, 4250, 19500, 5600, 3200, 12800]
        },
        'last-year': {
            categories: ['Food & Groceries', 'Transportation', 'Utilities', 'Education', 'Entertainment', 'Others'],
            values: [68000, 18500, 75600, 24000, 15900, 42000]
        },
        'custom': {
            categories: ['Food & Groceries', 'Transportation', 'Utilities', 'Education', 'Entertainment', 'Others'],
            values: [7800, 2100, 8900, 1800, 1500, 5800]
        }
    };
    
    // Sample data for trend chart
    const trendData = {
        'last-month': {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            expenses: [8500, 9200, 8100, 10042],
            income: [13000, 13200, 13000, 13400]
        },
        'last-quarter': {
            labels: ['Month 1', 'Month 2', 'Month 3'],
            expenses: [32500, 34800, 35242],
            income: [48000, 52500, 58100]
        },
        'last-year': {
            labels: ['Q1', 'Q2', 'Q3', 'Q4'],
            expenses: [92500, 98700, 96800, 97250],
            income: [140000, 152000, 165000, 173000]
        },
        'custom': {
            labels: ['Period 1', 'Period 2', 'Period 3'],
            expenses: [15200, 16500, 16620],
            income: [22000, 21500, 21700]
        }
    };
    
    // Update expense breakdown chart
    if (expenseBreakdownData[timePeriod] && window.expenseChart) {
        const data = expenseBreakdownData[timePeriod];
        window.expenseChart.data.labels = data.categories;
        window.expenseChart.data.datasets[0].data = data.values;
        window.expenseChart.update();
    }
    
    // Update trend chart
    if (trendData[timePeriod] && window.trendChart) {
        const data = trendData[timePeriod];
        window.trendChart.data.labels = data.labels;
        window.trendChart.data.datasets[0].data = data.expenses;
        window.trendChart.data.datasets[1].data = data.income;
        window.trendChart.update();
    }
}

/**
 * Gets a readable text for the selected time period
 * @param {string} timePeriod - The selected time period
 * @param {Object} dateRange - Custom date range (if applicable)
 * @returns {string} - Readable time period text
 */
function getTimePeriodText(timePeriod, dateRange) {
    switch (timePeriod) {
        case 'last-month':
            return 'the last month';
        case 'last-quarter':
            return 'the last quarter';
        case 'last-year':
            return 'the last year';
        case 'custom':
            if (dateRange) {
                return `the period ${dateRange.from} to ${dateRange.to}`;
            } else {
                return 'the custom period';
            }
        default:
            return 'the selected period';
    }
}

/**
 * Filters transactions by category
 * @param {string} category - The category to filter by
 */
function filterTransactionsByCategory(category) {
    const tableRows = document.querySelectorAll('.report-table tbody tr');
    
    if (category === 'all') {
        // Show all rows
        tableRows.forEach(row => {
            row.style.display = '';
        });
    } else {
        // Filter rows by category
        tableRows.forEach(row => {
            const rowCategory = row.cells[2].textContent.trim().toLowerCase();
            if (rowCategory.includes(category.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }
}

/**
 * Filters transactions by search term
 * @param {string} searchTerm - The search term
 */
function filterTransactionsBySearch(searchTerm) {
    const tableRows = document.querySelectorAll('.report-table tbody tr');
    
    tableRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Setup currency toggle functionality
 */
function setupCurrencyToggle() {
    const currencyBtn = document.querySelector('.currency-toggle');
    
    if (currencyBtn) {
        currencyBtn.addEventListener('click', function() {
            // Create dropdown menu if it doesn't exist
            if (!document.querySelector('.currency-dropdown')) {
                const dropdown = document.createElement('div');
                dropdown.className = 'currency-dropdown';
                
                dropdown.innerHTML = `
                    <ul>
                        <li data-currency="KES">KES - Kenyan Shilling</li>
                        <li data-currency="USD">USD - US Dollar</li>
                        <li data-currency="EUR">EUR - Euro</li>
                        <li data-currency="GBP">GBP - British Pound</li>
                    </ul>
                `;
                
                // Position the dropdown
                const buttonRect = this.getBoundingClientRect();
                dropdown.style.position = 'absolute';
                dropdown.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;
                dropdown.style.right = `${document.body.clientWidth - buttonRect.right - window.scrollX}px`;
                
                document.body.appendChild(dropdown);
                
                // Add event listeners to currency options
                dropdown.querySelectorAll('li').forEach(item => {
                    item.addEventListener('click', function() {
                        const currency = this.getAttribute('data-currency');
                        changeCurrency(currency);
                        dropdown.remove();
                    });
                });
                
                // Close dropdown when clicking outside
                document.addEventListener('click', function(event) {
                    if (!dropdown.contains(event.target) && event.target !== currencyBtn) {
                        dropdown.remove();
                    }
                }, { once: true });
            } else {
                // If dropdown exists, remove it
                document.querySelector('.currency-dropdown').remove();
            }
        });
    }
}

/**
 * Changes the currency display across the app
 * @param {string} currency - The new currency code
 */
function changeCurrency(currency) {
    // Update currency toggle button
    const currencyBtn = document.querySelector('.currency-toggle');
    if (currencyBtn) {
        currencyBtn.innerHTML = `${currency} <i class="fas fa-chevron-down"></i>`;
    }
    
    // For a real app, this would make an API call to convert values
    // For demo purposes, we'll just simulate conversion rates
    const conversionRates = {
        'KES': 1,
        'USD': 0.0065,
        'EUR': 0.0060,
        'GBP': 0.0051
    };
    
    const rate = conversionRates[currency] || 1;
    
    // Update money values across the page
    const moneyElements = document.querySelectorAll('.value, td:nth-child(4)');
    
    moneyElements.forEach(element => {
        const text = element.textContent;
        if (text.includes('KES')) {
            // Extract the number
            const match = text.match(/KES\s+([\d,]+(\.\d+)?)/);
            if (match) {
                const value = parseFloat(match[1].replace(/,/g, ''));
                const convertedValue = (value * rate).toFixed(2);
                const formattedValue = new Intl.NumberFormat().format(convertedValue);
                element.textContent = text.replace(/KES\s+[\d,]+(\.\d+)?/, `${currency} ${formattedValue}`);
            }
        }
    });
    
    // Show notification
    showNotification(`Currency changed to ${currency}`, 'info');
}

/**
 * Updates the table with new data
 * @param {Array} data - Array of transaction objects
 */
function updateTableWithNewData(data) {
    const tableBody = document.querySelector('.report-table tbody');
    tableBody.innerHTML = '';
    
    data.forEach(item => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${item.date}</td>
            <td>${item.description}</td>
            <td><span class="category-badge ${item.category.class}">${item.category.name}</span></td>
            <td>${item.amount}</td>
            <td>${item.paymentMethod}</td>
            <td>
                <button class="btn-icon" title="View transaction options" aria-label="View transaction options">
                    <i class="fas fa-ellipsis-v"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Reattach event listeners to new rows
    const actionButtons = document.querySelectorAll('.report-table .btn-icon');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Get the transaction details from the row
            const row = this.closest('tr');
            const date = row.cells[0].textContent;
            const description = row.cells[1].textContent;
            const amount = row.cells[3].textContent;
            
            // Create and show action menu
            showTransactionActionMenu(this, { date, description, amount });
        });
    });
    
    // Add click handlers for transaction rows
    const tableRows = document.querySelectorAll('.report-table tbody tr');
    
    tableRows.forEach(row => {
        row.addEventListener('click', function() {
            // Show transaction details modal
            const date = this.cells[0].textContent;
            const description = this.cells[1].textContent;
            const category = this.cells[2].querySelector('.category-badge').textContent;
            const amount = this.cells[3].textContent;
            const paymentMethod = this.cells[4].textContent;
            
            showTransactionDetailsModal({ date, description, category, amount, paymentMethod });
        });
    });
}

/**
 * Updates the pagination buttons state based on current page
 * @param {number} currentPage - The current page number
 */
function updatePaginationState(currentPage) {
    const previousButton = document.querySelector('.pagination-buttons button:first-child');
    const nextButton = document.querySelector('.pagination-buttons button:last-child');
    const totalPages = document.querySelectorAll('.pagination-buttons button:not([aria-label^="Previous"]):not([aria-label^="Next"])').length;
    
    // Handle previous button state
    if (currentPage === 1) {
        previousButton.setAttribute('disabled', '');
    } else {
        previousButton.removeAttribute('disabled');
    }
    
    // Handle next button state
    if (currentPage === totalPages) {
        nextButton.setAttribute('disabled', '');
    } else {
        nextButton.removeAttribute('disabled');
    }
}

/**
 * Shows an action menu for a transaction
 * @param {HTMLElement} button - The button that was clicked
 * @param {Object} transaction - The transaction details
 */
function showTransactionActionMenu(button, transaction) {
    // Remove any existing menu
    const existingMenu = document.querySelector('.transaction-action-menu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // Create new menu
    const menu = document.createElement('div');
    menu.className = 'transaction-action-menu';
    
    menu.innerHTML = `
        <ul>
            <li><i class="fas fa-eye"></i> View Details</li>
            <li><i class="fas fa-edit"></i> Edit Transaction</li>
            <li><i class="fas fa-receipt"></i> View Receipt</li>
            <li><i class="fas fa-tags"></i> Change Category</li>
            <li class="text-danger"><i class="fas fa-trash"></i> Delete</li>
        </ul>
    `;
    
    // Position the menu
    const buttonRect = button.getBoundingClientRect();
    menu.style.position = 'absolute';
    menu.style.top = `${buttonRect.bottom + window.scrollY + 5}px`;
    menu.style.right = `${document.body.clientWidth - buttonRect.right - window.scrollX}px`;
    
    document.body.appendChild(menu);
    
    // Add event listeners to menu items
    menu.querySelectorAll('li').forEach(item => {
        item.addEventListener('click', function() {
            const action = this.textContent.trim();
            
            if (action.includes('View Details')) {
                // Show transaction details modal
                menu.remove();
                showTransactionDetailsModal({
                    ...transaction,
                    category: button.closest('tr').cells[2].querySelector('.category-badge').textContent,
                    paymentMethod: button.closest('tr').cells[4].textContent
                });
            }
            else if (action.includes('Delete')) {
                // Show delete confirmation
                menu.remove();
                showDeleteConfirmation(transaction);
            }
            else {
                // Other actions would have their own handlers
                menu.remove();
                showNotification(`${action} for ${transaction.description}`, 'info');
            }
        });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!menu.contains(event.target) && event.target !== button) {
            menu.remove();
        }
    }, { once: true });
}