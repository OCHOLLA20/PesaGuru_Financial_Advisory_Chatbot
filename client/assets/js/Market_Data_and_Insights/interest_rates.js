document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components and data
    initializeSidebar();
    initializeNotifications();
    initializeThemeToggle();
    initializeCharts();
    initializeRatesData();
    initializeAlerts();
    initializeModals();
    initializeChatbotPrompt();
});

/**
 * Sidebar functionality
 */
function initializeSidebar() {
    const toggleButton = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    toggleButton.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        
        // Update the toggle button icon
        const isCollapsed = sidebar.classList.contains('collapsed');
        toggleButton.innerHTML = isCollapsed ? '→' : '<span></span>';
    });
    
    // Back button functionality
    const backButton = document.querySelector('.back-button');
    if (backButton) {
        backButton.addEventListener('click', function() {
            window.history.back();
        });
    }
}

/**
 * Notifications handling
 */
function initializeNotifications() {
    const notificationsButton = document.getElementById('notificationsButton');
    const notificationsDropdown = document.getElementById('notificationsDropdown');
    
    if (notificationsButton && notificationsDropdown) {
        // Toggle dropdown on click instead of hover (better for mobile)
        notificationsButton.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationsDropdown.classList.toggle('visible');
        });
        
        // Close dropdown when clicking elsewhere
        document.addEventListener('click', function() {
            if (notificationsDropdown.classList.contains('visible')) {
                notificationsDropdown.classList.remove('visible');
            }
        });
        
        // Prevent dropdown from closing when clicking inside it
        notificationsDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
    
    // Handle notification badge
    updateNotificationBadge();
}

/**
 * Update notification badge count
 */
function updateNotificationBadge() {
    const badge = document.querySelector('.notification-badge');
    const notificationItems = document.querySelectorAll('.notification-item');
    
    if (badge && notificationItems) {
        const unreadCount = notificationItems.length;
        badge.textContent = unreadCount;
        
        if (unreadCount === 0) {
            badge.style.display = 'none';
        } else {
            badge.style.display = 'flex';
        }
    }
}

/**
 * Theme toggling (dark/light mode)
 */
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    
    if (themeToggle) {
        // Check for saved theme preference or respect OS preference
        const prefersDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme === 'dark' || (!savedTheme && prefersDarkMode)) {
            document.body.classList.add('dark-mode');
            themeToggle.querySelector('.label').textContent = 'Light Mode';
        }
        
        // Toggle theme on click
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const isDarkMode = document.body.classList.contains('dark-mode');
            
            // Update toggle button text
            themeToggle.querySelector('.label').textContent = isDarkMode ? 'Light Mode' : 'Dark Mode';
            
            // Save preference
            localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
        });
    }
}

/**
 * Chart rendering and configuration
 */
function initializeCharts() {
    // We'll use a mock implementation since we don't have a real charting library
    // In a real implementation, you would use libraries like Chart.js, ApexCharts, or Highcharts
    
    // Time period selector for main chart
    const periodButtons = document.querySelectorAll('.period-button');
    
    if (periodButtons) {
        periodButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                periodButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get selected period
                const period = this.getAttribute('data-period');
                
                // Update chart data based on period
                updateMainChart(period);
            });
        });
    }
    
    // Initialize the main rates chart with default period (6m)
    updateMainChart('6m');
    
    // Initialize the global rates chart
    initializeGlobalRatesChart();
    
    // Initialize the forecast mini-chart
    initializeForecastChart();
    
    // Toggle between chart and table view for global rates
    const viewToggleButtons = document.querySelectorAll('.toggle-chart-view-button');
    
    if (viewToggleButtons) {
        viewToggleButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Get the view to show
                const viewType = this.getAttribute('data-view');
                
                // Remove active class from all buttons
                viewToggleButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Show/hide views
                const chartView = document.querySelector('.global-rates-chart-view');
                const tableView = document.querySelector('.global-rates-table-view');
                
                if (chartView && tableView) {
                    if (viewType === 'chart') {
                        chartView.classList.remove('hidden');
                        tableView.classList.add('hidden');
                    } else {
                        chartView.classList.add('hidden');
                        tableView.classList.remove('hidden');
                    }
                }
            });
        });
    }
    
    // Chart download and fullscreen options
    const chartOptions = document.querySelectorAll('.chart-option-button');
    
    if (chartOptions) {
        chartOptions.forEach(option => {
            option.addEventListener('click', function() {
                const action = this.getAttribute('data-option');
                
                if (action === 'download') {
                    // Mock implementation for downloading chart data
                    alert('Downloading chart data as CSV...');
                    // In a real implementation, you would generate and download a CSV file
                    
                } else if (action === 'fullscreen') {
                    // Mock implementation for fullscreen chart
                    const chartContainer = document.querySelector('.chart-wrapper');
                    if (chartContainer) {
                        if (document.fullscreenElement) {
                            document.exitFullscreen();
                        } else {
                            chartContainer.requestFullscreen();
                        }
                    }
                }
            });
        });
    }
}

/**
 * Update main interest rates chart based on selected time period
 */
function updateMainChart(period) {
    // This is a mock implementation
    // In a real implementation, you would fetch data for the selected period
    // and update the chart using your chosen charting library
    
    const chartPlaceholder = document.querySelector('#mainRatesChart .chart-placeholder');
    
    if (chartPlaceholder) {
        // Update the placeholder text to show the selected period
        chartPlaceholder.innerHTML = `
            <p>Chart loading...</p>
            <p class="placeholder-text">This chart will display interest rate trends for the past ${getPeriodText(period)}. In a real implementation, this would be an interactive chart showing CBK rate, T-bill rates, and commercial bank rates.</p>
        `;
    }
    
    // If using a real chart library, you would update the chart data here
    console.log(`Updating main chart with period: ${period}`);
}

/**
 * Get human-readable text for time period
 */
function getPeriodText(period) {
    switch(period) {
        case '6m': return '6 months';
        case '1y': return '1 year';
        case '5y': return '5 years';
        default: return period;
    }
}

/**
 * Initialize the global rates comparison chart
 */
function initializeGlobalRatesChart() {
    // Mock implementation
    const chartPlaceholder = document.querySelector('#globalRatesChart .chart-placeholder');
    
    if (chartPlaceholder) {
        chartPlaceholder.innerHTML = `
            <p>Chart loading...</p>
            <p class="placeholder-text">This chart will display global interest rate comparisons. In a real implementation, this would be an interactive chart comparing central bank rates across major economies.</p>
        `;
    }
}

/**
 * Initialize the forecast mini-chart
 */
function initializeForecastChart() {
    // Mock implementation
    const chartPlaceholder = document.querySelector('#cbkForecastChart .chart-placeholder');
    
    if (chartPlaceholder) {
        chartPlaceholder.innerHTML = `
            <p>Forecast chart loading...</p>
        `;
    }
}

/**
 * Rates data handling
 */
function initializeRatesData() {
    // Refresh button functionality
    const refreshButton = document.getElementById('refreshButton');
    
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshRatesData();
        });
    }
    
    // Section refresh buttons
    const sectionRefreshButtons = document.querySelectorAll('.refresh-section-button');
    
    if (sectionRefreshButtons) {
        sectionRefreshButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Get the parent section
                const section = this.closest('section');
                refreshSectionData(section);
            });
        });
    }
    
    // Currency selector
    const currencySelect = document.getElementById('currencySelect');
    
    if (currencySelect) {
        currencySelect.addEventListener('change', function() {
            const selectedCurrency = this.value;
            updateCurrencyDisplay(selectedCurrency);
        });
    }
    
    // History button
    const historyButton = document.getElementById('historyButton');
    
    if (historyButton) {
        historyButton.addEventListener('click', function() {
            showRatesHistory();
        });
    }
}

/**
 * Refresh all rates data
 */
function refreshRatesData() {
    // Display loading indicator
    showLoadingIndicator();
    
    // Mock API call delay
    setTimeout(function() {
        // Update last updated timestamp
        const lastUpdatedElement = document.querySelector('.update-info');
        if (lastUpdatedElement) {
            const now = new Date();
            lastUpdatedElement.textContent = `Last updated: ${formatDate(now)}, ${formatTime(now)}`;
        }
        
        // Refresh all charts
        updateMainChart(document.querySelector('.period-button.active').getAttribute('data-period'));
        initializeGlobalRatesChart();
        initializeForecastChart();
        
        // Hide loading indicator
        hideLoadingIndicator();
        
        // Show success message
        showToast('Data refreshed successfully');
    }, 1500);
}

/**
 * Refresh data for a specific section
 */
function refreshSectionData(section) {
    // Show section-specific loading indicator
    showSectionLoadingIndicator(section);
    
    // Mock API call delay
    setTimeout(function() {
        // Refresh section-specific data
        if (section.classList.contains('rates-detail-section')) {
            // Refresh Kenyan rates
            console.log('Refreshing Kenyan rates data');
        } else if (section.classList.contains('global-rates-section')) {
            // Refresh global rates
            console.log('Refreshing global rates data');
            initializeGlobalRatesChart();
        }
        
        // Hide section loading indicator
        hideSectionLoadingIndicator(section);
        
        // Show success message
        showToast('Section data refreshed');
    }, 1000);
}

/**
 * Update display for selected currency
 */
function updateCurrencyDisplay(currency) {
    // In a real implementation, you would convert all displayed rates to the selected currency
    console.log(`Updating rates display for currency: ${currency}`);
    
    // Show toast notification
    showToast(`Currency changed to ${currency}`);
}

/**
 * Show rates history
 */
function showRatesHistory() {
    // In a real implementation, you would show a modal or navigate to a history page
    alert('This would show a detailed history of interest rates over time');
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    // Create and show a full-page loading indicator
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="loading-spinner"></div>
        <p>Refreshing data...</p>
    `;
    
    document.body.appendChild(loadingOverlay);
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

/**
 * Show section loading indicator
 */
function showSectionLoadingIndicator(section) {
    // Create and append a section-specific loading indicator
    const sectionLoader = document.createElement('div');
    sectionLoader.className = 'section-loader';
    sectionLoader.innerHTML = `
        <div class="loading-spinner small"></div>
        <p>Updating...</p>
    `;
    
    section.appendChild(sectionLoader);
}

/**
 * Hide section loading indicator
 */
function hideSectionLoadingIndicator(section) {
    const sectionLoader = section.querySelector('.section-loader');
    if (sectionLoader) {
        sectionLoader.remove();
    }
}

/**
 * Show toast notification
 */
function showToast(message) {
    // Create and show a toast message
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('visible'), 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Format date for display
 */
function formatDate(date) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

/**
 * Format time for display
 */
function formatTime(date) {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const formattedHours = hours % 12 || 12;
    const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
    return `${formattedHours}:${formattedMinutes} ${ampm}`;
}

/**
 * Alerts management
 */
function initializeAlerts() {
    // New alert button
    const newAlertButton = document.querySelector('.new-alert-button');
    const alertSetupForm = document.querySelector('.alert-setup-form');
    const activeAlerts = document.querySelector('.active-alerts');
    const cancelButton = document.querySelector('.cancel-button');
    
    if (newAlertButton && alertSetupForm && activeAlerts) {
        newAlertButton.addEventListener('click', function() {
            // Show the alert setup form
            alertSetupForm.classList.remove('hidden');
            activeAlerts.classList.add('hidden');
        });
    }
    
    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            // Hide the alert setup form
            alertSetupForm.classList.add('hidden');
            activeAlerts.classList.remove('hidden');
        });
    }
    
    // Alert form submission
    const alertForm = document.getElementById('newAlertForm');
    
    if (alertForm) {
        alertForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveNewAlert();
        });
    }
    
    // Condition-dependent threshold field
    const alertCondition = document.getElementById('alertCondition');
    const thresholdGroup = document.getElementById('thresholdGroup');
    
    if (alertCondition && thresholdGroup) {
        alertCondition.addEventListener('change', function() {
            const value = this.value;
            
            // Show threshold input for certain conditions
            if (value === 'exceeds' || value === 'falls-below') {
                thresholdGroup.classList.remove('hidden');
            } else {
                thresholdGroup.classList.add('hidden');
            }
        });
    }
    
    // Edit/delete alert buttons
    const editAlertButtons = document.querySelectorAll('.edit-alert-button');
    const deleteAlertButtons = document.querySelectorAll('.delete-alert-button');
    
    if (editAlertButtons) {
        editAlertButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alertItem = this.closest('.alert-item');
                editAlert(alertItem);
            });
        });
    }
    
    if (deleteAlertButtons) {
        deleteAlertButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alertItem = this.closest('.alert-item');
                deleteAlert(alertItem);
            });
        });
    }
}

/**
 * Save new alert from form data
 */
function saveNewAlert() {
    // Get form data
    const alertName = document.getElementById('alertName').value;
    const rateType = document.getElementById('rateType');
    const rateTypeText = rateType.options[rateType.selectedIndex].text;
    const alertCondition = document.getElementById('alertCondition');
    const conditionText = alertCondition.options[alertCondition.selectedIndex].text;
    
    // Get threshold if needed
    let conditionDisplay = '';
    if (alertCondition.value === 'exceeds' || alertCondition.value === 'falls-below') {
        const threshold = document.getElementById('rateThreshold').value;
        conditionDisplay = `When ${rateTypeText} ${conditionText} ${threshold}%`;
    } else {
        conditionDisplay = `When ${rateTypeText} ${conditionText}`;
    }
    
    // Get notification methods
    const notificationMethods = [];
    document.querySelectorAll('input[name="notificationMethod"]:checked').forEach(checkbox => {
        notificationMethods.push(checkbox.value);
    });
    
    const notificationDisplay = `Notify via: ${notificationMethods.map(m => capitalize(m)).join(', ')}`;
    
    // Create new alert item
    createAlertItem(alertName, conditionDisplay, notificationDisplay);
    
    // Reset form and hide it
    document.getElementById('newAlertForm').reset();
    document.querySelector('.alert-setup-form').classList.add('hidden');
    document.querySelector('.active-alerts').classList.remove('hidden');
    
    // Show success message
    showToast('Alert created successfully');
}

/**
 * Create a new alert item in the UI
 */
function createAlertItem(name, condition, notification) {
    const alertsList = document.querySelector('.alerts-list');
    
    if (alertsList) {
        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        alertItem.innerHTML = `
            <div class="alert-details">
                <div class="alert-name">${name}</div>
                <div class="alert-condition">${condition}</div>
                <div class="alert-notification">${notification}</div>
            </div>
            <div class="alert-actions">
                <button class="edit-alert-button">Edit</button>
                <button class="delete-alert-button">Delete</button>
            </div>
        `;
        
        // Add event listeners for the new buttons
        alertItem.querySelector('.edit-alert-button').addEventListener('click', function() {
            editAlert(alertItem);
        });
        
        alertItem.querySelector('.delete-alert-button').addEventListener('click', function() {
            deleteAlert(alertItem);
        });
        
        // Add to the list
        alertsList.appendChild(alertItem);
    }
}

/**
 * Edit existing alert
 */
function editAlert(alertItem) {
    // In a real implementation, you would populate the form with the alert data
    // and switch to edit mode
    const alertName = alertItem.querySelector('.alert-name').textContent;
    
    // Show the alert setup form
    document.querySelector('.alert-setup-form').classList.remove('hidden');
    document.querySelector('.active-alerts').classList.add('hidden');
    
    // Populate form with existing data (simplified implementation)
    document.getElementById('alertName').value = alertName;
    
    // Show message
    showToast(`Editing alert: ${alertName}`);
}

/**
 * Delete alert
 */
function deleteAlert(alertItem) {
    if (confirm('Are you sure you want to delete this alert?')) {
        // Animate removal
        alertItem.style.opacity = '0';
        setTimeout(() => {
            alertItem.remove();
            showToast('Alert deleted');
        }, 300);
    }
}

/**
 * Modal handling
 */
function initializeModals() {
    // Comparison modal
    const comparisonModal = document.getElementById('comparisonModal');
    const compareButtons = document.querySelectorAll('button.table-action-button');
    
    if (comparisonModal && compareButtons) {
        // Open modal for comparison
        compareButtons.forEach(button => {
            if (button.textContent.includes('Compare')) {
                button.addEventListener('click', function() {
                    const rateType = this.closest('tr').querySelector('td:first-child').textContent;
                    openComparisonModal(rateType);
                });
            }
        });
        
        // Close modal button
        const closeModalButton = comparisonModal.querySelector('.close-modal-button');
        if (closeModalButton) {
            closeModalButton.addEventListener('click', function() {
                comparisonModal.style.display = 'none';
            });
        }
        
        // Close modal when clicking outside
        comparisonModal.addEventListener('click', function(e) {
            if (e.target === comparisonModal) {
                comparisonModal.style.display = 'none';
            }
        });
    }
    
    // Calculate loan impact
    const calculateImpactButton = document.querySelector('.calculate-impact-button');
    if (calculateImpactButton) {
        calculateImpactButton.addEventListener('click', function() {
            const loanAmount = document.querySelector('.loan-amount-input').value;
            if (loanAmount) {
                calculateLoanImpact(parseFloat(loanAmount));
            } else {
                showToast('Please enter a loan amount');
            }
        });
    }
}

/**
 * Open the bank comparison modal
 */
function openComparisonModal(rateType) {
    const comparisonModal = document.getElementById('comparisonModal');
    const modalBody = comparisonModal.querySelector('.modal-body');
    const modalHeader = comparisonModal.querySelector('.modal-header h2');
    
    if (comparisonModal && modalBody && modalHeader) {
        // Update modal title
        modalHeader.textContent = `${rateType} - Bank Comparison`;
        
        // Show loading placeholder
        modalBody.innerHTML = `
            <div class="comparison-placeholder">
                <p>Loading comparison data...</p>
            </div>
        `;
        
        // Show the modal
        comparisonModal.style.display = 'flex';
        
        // Mock API delay
        setTimeout(function() {
            // Mock data for bank comparison
            // In a real implementation, you would fetch this data from your API
            const bankData = [
                { name: 'Equity Bank', rate: '16.45%', min: '14.50%', max: '18.00%', change: '+0.20%' },
                { name: 'KCB', rate: '16.75%', min: '15.00%', max: '18.50%', change: '+0.25%' },
                { name: 'Co-operative Bank', rate: '17.25%', min: '15.25%', max: '19.00%', change: '+0.30%' },
                { name: 'ABSA', rate: '16.90%', min: '14.75%', max: '18.25%', change: '+0.15%' },
                { name: 'NCBA', rate: '17.40%', min: '15.50%', max: '19.25%', change: '+0.20%' },
                { name: 'Standard Chartered', rate: '16.50%', min: '14.25%', max: '18.75%', change: '+0.10%' }
            ];
            
            // Create comparison table
            let tableHTML = `
                <table class="rates-table">
                    <thead>
                        <tr>
                            <th>Bank</th>
                            <th>Average Rate</th>
                            <th>Minimum Rate</th>
                            <th>Maximum Rate</th>
                            <th>Recent Change</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Add bank data rows
            bankData.forEach(bank => {
                const changeClass = bank.change.startsWith('+') ? 'increase' : 'decrease';
                
                tableHTML += `
                    <tr>
                        <td>${bank.name}</td>
                        <td class="rate-value">${bank.rate}</td>
                        <td>${bank.min}</td>
                        <td>${bank.max}</td>
                        <td class="rate-change ${changeClass}">${bank.change}</td>
                    </tr>
                `;
            });
            
            tableHTML += `
                    </tbody>
                </table>
                <div class="modal-footer" style="margin-top: 20px; text-align: center;">
                    <p>Data source: Central Bank of Kenya, Updated Mar 8, 2025</p>
                    <button class="calculator-button" style="margin-top: 15px; display: inline-block;">Calculate Loan with Selected Bank</button>
                </div>
            `;
            
            // Update modal content
            modalBody.innerHTML = tableHTML;
        }, 1000);
    }
}

/**
 * Calculate and display loan impact based on rate changes
 */
function calculateLoanImpact(loanAmount) {
    if (!loanAmount || isNaN(loanAmount)) {
        showToast('Please enter a valid loan amount');
        return;
    }
    
    // Mock implementation of loan impact calculation
    // In a real implementation, you would use actual formulas
    const currentRate = 16.98; // From the page data
    const projectedRate = 17.28; // Current + projected increase
    const tenor = 12; // 12 months
    
    // Calculate current monthly payment (simplified)
    const currentMonthly = (loanAmount + (loanAmount * currentRate / 100 * tenor/12)) / tenor;
    
    // Calculate projected monthly payment
    const projectedMonthly = (loanAmount + (loanAmount * projectedRate / 100 * tenor/12)) / tenor;
    
    // Calculate the difference
    const monthlyDifference = projectedMonthly - currentMonthly;
    const totalDifference = monthlyDifference * tenor;
    
    // Display the result in a modal or alert
    alert(`
        Loan Impact Analysis
        --------------------
        Loan Amount: KES ${loanAmount.toLocaleString()}
        Current Rate: ${currentRate}%
        Projected Rate: ${projectedRate}%
        
        Current Monthly Payment: KES ${currentMonthly.toFixed(2).toLocaleString()}
        Projected Monthly Payment: KES ${projectedMonthly.toFixed(2).toLocaleString()}
        
        Monthly Increase: KES ${monthlyDifference.toFixed(2).toLocaleString()}
        Total Additional Cost: KES ${totalDifference.toFixed(2).toLocaleString()}
    `);
}

/**
 * Chatbot prompt handling
 */
function initializeChatbotPrompt() {
    const chatbotPrompt = document.querySelector('.chatbot-prompt');
    const chatWithPesaGuruButton = document.querySelector('.chat-with-pesaguru-button');
    const closePromptButton = document.querySelector('.close-prompt-button');
    
    if (chatbotPrompt && chatWithPesaGuruButton && closePromptButton) {
        // Open chatbot on button click
        chatWithPesaGuruButton.addEventListener('click', function() {
            // In a real implementation, you would navigate to the chatbot page or open a chat widget
            window.location.href = '../Chatbot Interaction/chatbot.html?topic=interest_rates';
        });
        
        // Close prompt
        closePromptButton.addEventListener('click', function() {
            chatbotPrompt.style.display = 'none';
            
            // In a real implementation, you might save this preference
            localStorage.setItem('chatbot_prompt_hidden', 'true');
        });
        
        // Check if prompt should be hidden
        if (localStorage.getItem('chatbot_prompt_hidden') === 'true') {
            // You might want to show it again after some time
            // For this example, we'll still show it
        }
    }
}

/**
 * Helper function to capitalize first letter of a string
 */
function capitalize(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Additional CSS styles for elements created by JavaScript
 * These would normally be in the CSS file, but we're adding them here for completeness
 */
const dynamicStyles = document.createElement('style');
dynamicStyles.textContent = `
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.6);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 2000;
        color: white;
    }
    
    .loading-spinner {
        width: 50px;
        height: 50px;
        border: 5px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: white;
        animation: spin 1s linear infinite;
        margin-bottom: 15px;
    }
    
    .loading-spinner.small {
        width: 30px;
        height: 30px;
        border-width: 3px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    .section-loader {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 100;
    }
    
    .toast {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%) translateY(100px);
        background-color: var(--dark);
        color: white;
        padding: 12px 24px;
        border-radius: 4px;
        font-size: 14px;
        box-shadow: var(--shadow-lg);
        z-index: 2000;
        opacity: 0;
        transition: transform 0.3s ease, opacity 0.3s ease;
    }
    
    .toast.visible {
        opacity: 1;
        transform: translateX(-50%) translateY(0);
    }
    
    .sidebar.collapsed {
        width: var(--sidebar-collapsed-width);
    }
    
    .sidebar.collapsed .logo h1,
    .sidebar.collapsed .nav-section h3,
    .sidebar.collapsed .sidebar-nav a span:not(.icon),
    .sidebar.collapsed .sidebar-footer .label {
        display: none;
    }
    
    .main-content.expanded {
        margin-left: var(--sidebar-collapsed-width);
    }
    
    .notifications-dropdown.visible {
        display: block;
    }
`;

document.head.appendChild(dynamicStyles);