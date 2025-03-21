// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts
    initFinancialChart();
    initBudgetDonutChart();
    
    // Initialize UI interactions
    initUIInteractions();
});

// Financial Statistics Chart
function initFinancialChart() {
    const ctx = document.getElementById('financialChart').getContext('2d');
    
    // Data for the financial chart
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const incomeData = [9500, 11200, 10800, 12400, 13583, 14200];
    const expensesData = [7800, 8900, 8200, 9100, 8921, 9300];
    const savingsData = [1700, 2300, 2600, 3300, 4662, 4900];
    
    // Create gradient for income
    const incomeGradient = ctx.createLinearGradient(0, 0, 0, 250);
    incomeGradient.addColorStop(0, 'rgba(46, 202, 106, 0.3)');
    incomeGradient.addColorStop(1, 'rgba(46, 202, 106, 0.0)');
    
    // Create gradient for expenses
    const expensesGradient = ctx.createLinearGradient(0, 0, 0, 250);
    expensesGradient.addColorStop(0, 'rgba(255, 99, 132, 0.3)');
    expensesGradient.addColorStop(1, 'rgba(255, 99, 132, 0.0)');
    
    // Create gradient for savings
    const savingsGradient = ctx.createLinearGradient(0, 0, 0, 250);
    savingsGradient.addColorStop(0, 'rgba(54, 162, 235, 0.3)');
    savingsGradient.addColorStop(1, 'rgba(54, 162, 235, 0.0)');
    
    // Chart configuration
    const financialChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: months,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    borderColor: '#2ECA6A',
                    backgroundColor: incomeGradient,
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2,
                    pointBackgroundColor: '#2ECA6A',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Expenses',
                    data: expensesData,
                    borderColor: '#FF6384',
                    backgroundColor: expensesGradient,
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2,
                    pointBackgroundColor: '#FF6384',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Savings',
                    data: savingsData,
                    borderColor: '#36A2EB',
                    backgroundColor: savingsGradient,
                    tension: 0.4,
                    fill: true,
                    borderWidth: 2,
                    pointBackgroundColor: '#36A2EB',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 6,
                        padding: 20,
                        font: {
                            family: 'Inter',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    padding: 10,
                    bodyFont: {
                        family: 'Inter',
                        size: 12
                    },
                    titleFont: {
                        family: 'Inter',
                        size: 14,
                        weight: 'bold'
                    },
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': KES ' + context.raw.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 12
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        borderDash: [3, 3],
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        font: {
                            family: 'Inter',
                            size: 12
                        },
                        callback: function(value) {
                            return 'KES ' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Budget Donut Chart
function initBudgetDonutChart() {
    const ctx = document.getElementById('budgetDonutChart').getContext('2d');
    
    // Budget categories and their percentages
    const budgetData = {
        labels: ['Residential', 'Transportation', 'Education', 'Holiday', 'Others'],
        datasets: [{
            data: [25, 15, 30, 10, 20],
            backgroundColor: [
                '#4E73DF', // Residential
                '#1CC88A', // Transportation
                '#36B9CC', // Education
                '#F6C23E', // Holiday
                '#858796'  // Others
            ],
            borderWidth: 0,
            hoverOffset: 4
        }]
    };
    
    // Chart configuration
    const budgetDonutChart = new Chart(ctx, {
        type: 'doughnut',
        data: budgetData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            family: 'Inter',
                            size: 11
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.7)',
                    bodyFont: {
                        family: 'Inter',
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.raw + '%';
                        }
                    }
                }
            }
        }
    });
}

// Initialize UI interactions
function initUIInteractions() {
    // Theme toggle functionality
    const themeToggle = document.querySelector('.theme-toggle');
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // Toggle icon between moon and sun
        const icon = this.querySelector('i');
        if (icon.classList.contains('fa-moon')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    });
    
    // Chatbot toggle functionality
    const chatbotToggle = document.querySelector('.chatbot-toggle');
    chatbotToggle.addEventListener('click', function() {
        // Create chatbot dialog if it doesn't exist
        if (!document.querySelector('.chatbot-dialog')) {
            createChatbotDialog();
        } else {
            // Toggle visibility of existing dialog
            const dialog = document.querySelector('.chatbot-dialog');
            dialog.classList.toggle('active');
        }
    });
    
    // Financial statistics period buttons
    const periodButtons = document.querySelectorAll('.section-actions .btn-outline');
    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            periodButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Here you would update the financial chart data based on the selected period
            // For demonstration purposes, we'll just log the selected period
            console.log('Selected period:', this.textContent.trim());
        });
    });
    
    // Currency toggle dropdown
    const currencyToggle = document.querySelector('.currency-toggle');
    currencyToggle.addEventListener('click', function() {
        // Create currency dropdown if it doesn't exist
        if (!document.querySelector('.currency-dropdown')) {
            const dropdown = document.createElement('div');
            dropdown.className = 'currency-dropdown';
            
            const currencies = ['KES', 'USD', 'EUR', 'GBP'];
            currencies.forEach(currency => {
                const option = document.createElement('div');
                option.className = 'currency-option';
                option.textContent = currency;
                option.addEventListener('click', function() {
                    currencyToggle.innerHTML = currency + ' <i class="fas fa-chevron-down"></i>';
                    dropdown.remove();
                    // Here you would update all currency displays throughout the dashboard
                });
                dropdown.appendChild(option);
            });
            
            document.querySelector('.header-actions').appendChild(dropdown);
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function closeDropdown(e) {
                if (!dropdown.contains(e.target) && e.target !== currencyToggle) {
                    dropdown.remove();
                    document.removeEventListener('click', closeDropdown);
                }
            });
        } else {
            document.querySelector('.currency-dropdown').remove();
        }
    });
    
    // Add transaction button
    const addExpenseButton = document.querySelector('.menu-item a[href="#"]');
    if (addExpenseButton && addExpenseButton.textContent.includes('Add Expense')) {
        addExpenseButton.addEventListener('click', function(e) {
            e.preventDefault();
            createAddExpenseModal();
        });
    }
}

// Create chatbot dialog
function createChatbotDialog() {
    const dialog = document.createElement('div');
    dialog.className = 'chatbot-dialog active';
    
    const header = document.createElement('div');
    header.className = 'chatbot-header';
    header.innerHTML = `
        <h3>PesaGuru Assistant</h3>
        <button class="close-chatbot"><i class="fas fa-times"></i></button>
    `;
    
    const body = document.createElement('div');
    body.className = 'chatbot-body';
    body.innerHTML = `
        <div class="chatbot-message bot">
            <div class="message-content">
                Hello Hailey! How can I help you manage your finances today?
            </div>
        </div>
    `;
    
    const footer = document.createElement('div');
    footer.className = 'chatbot-footer';
    footer.innerHTML = `
        <input type="text" placeholder="Type your question here...">
        <button class="send-message"><i class="fas fa-paper-plane"></i></button>
    `;
    
    dialog.appendChild(header);
    dialog.appendChild(body);
    dialog.appendChild(footer);
    
    document.querySelector('.chatbot-widget').appendChild(dialog);
    
    // Close button functionality
    dialog.querySelector('.close-chatbot').addEventListener('click', function() {
        dialog.classList.remove('active');
    });
    
    // Send message functionality
    const input = dialog.querySelector('input');
    const sendButton = dialog.querySelector('.send-message');
    
    const sendMessage = function() {
        const message = input.value.trim();
        if (message) {
            // Add user message
            const userMessage = document.createElement('div');
            userMessage.className = 'chatbot-message user';
            userMessage.innerHTML = `
                <div class="message-content">${message}</div>
            `;
            body.appendChild(userMessage);
            
            // Clear input
            input.value = '';
            
            // Scroll to bottom
            body.scrollTop = body.scrollHeight;
            
            // Simulate bot response after a short delay
            setTimeout(function() {
                const botResponse = document.createElement('div');
                botResponse.className = 'chatbot-message bot';
                botResponse.innerHTML = `
                    <div class="message-content">
                        I'll help you with "${message}". Based on your recent spending pattern, I'd recommend focusing on reducing your "Residential Costs" to meet your savings goal faster.
                    </div>
                `;
                body.appendChild(botResponse);
                body.scrollTop = body.scrollHeight;
            }, 1000);
        }
    };
    
    sendButton.addEventListener('click', sendMessage);
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Create Add Expense Modal
function createAddExpenseModal() {
    // Remove existing modal if present
    if (document.querySelector('.modal-overlay')) {
        document.querySelector('.modal-overlay').remove();
    }
    
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    
    const modal = document.createElement('div');
    modal.className = 'modal add-expense-modal';
    
    modal.innerHTML = `
        <div class="modal-header">
            <h3>Add New Expense</h3>
            <button class="close-modal"><i class="fas fa-times"></i></button>
        </div>
        <div class="modal-body">
            <form id="add-expense-form">
                <div class="form-group">
                    <label for="expense-title">Expense Title</label>
                    <input type="text" id="expense-title" placeholder="e.g. Grocery Shopping" required>
                </div>
                
                <div class="form-group">
                    <label for="expense-amount">Amount (KES)</label>
                    <input type="number" id="expense-amount" placeholder="0.00" min="0" step="0.01" required>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="expense-category">Category</label>
                        <select id="expense-category" required>
                            <option value="">Select Category</option>
                            <option value="residential">Residential</option>
                            <option value="transportation">Transportation</option>
                            <option value="education">Education</option>
                            <option value="holiday">Holiday</option>
                            <option value="food">Food & Dining</option>
                            <option value="entertainment">Entertainment</option>
                            <option value="healthcare">Healthcare</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="expense-date">Date</label>
                        <input type="date" id="expense-date" required>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="expense-notes">Notes (Optional)</label>
                    <textarea id="expense-notes" placeholder="Add any additional details"></textarea>
                </div>
                
                <div class="form-actions">
                    <button type="button" class="btn-outline cancel-btn">Cancel</button>
                    <button type="submit" class="btn-primary">Add Expense</button>
                </div>
            </form>
        </div>
    `;
    
    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expense-date').value = today;
    
    // Close modal functionality
    const closeBtn = document.querySelector('.close-modal');
    const cancelBtn = document.querySelector('.cancel-btn');
    
    const closeModal = function() {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.remove(), 300);
    };
    
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            closeModal();
        }
    });
    
    // Form submission
    const form = document.getElementById('add-expense-form');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form values
        const title = document.getElementById('expense-title').value;
        const amount = document.getElementById('expense-amount').value;
        const category = document.getElementById('expense-category').value;
        const date = document.getElementById('expense-date').value;
        const notes = document.getElementById('expense-notes').value;
        
        // Log the values (in a real app, you would save these to a database)
        console.log('New Expense:', {
            title,
            amount: parseFloat(amount),
            category,
            date,
            notes
        });
        
        // Show success message
        const successMsg = document.createElement('div');
        successMsg.className = 'success-toast';
        successMsg.textContent = 'Expense added successfully!';
        document.body.appendChild(successMsg);
        
        // Remove success message after 3 seconds
        setTimeout(() => {
            successMsg.classList.add('fade-out');
            setTimeout(() => successMsg.remove(), 300);
        }, 3000);
        
        // Close the modal
        closeModal();
    });
}

// Add window resize event listener to ensure charts are responsive
window.addEventListener('resize', function() {
    // Force charts to resize when window is resized
    Chart.instances.forEach(chart => {
        chart.resize();
    });
});

// Add styles for dynamic elements
const style = document.createElement('style');
style.innerHTML = `
    /* Chatbot Dialog */
    .chatbot-dialog {
        position: fixed;
        bottom: 80px;
        right: 20px;
        width: 320px;
        height: 400px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        z-index: 1000;
        overflow: hidden;
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.3s, transform 0.3s;
        pointer-events: none;
    }
    
    .chatbot-dialog.active {
        opacity: 1;
        transform: translateY(0);
        pointer-events: all;
    }
    
    .chatbot-header {
        padding: 15px;
        background: #4E73DF;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .chatbot-header h3 {
        margin: 0;
        font-size: 16px;
    }
    
    .close-chatbot {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 16px;
    }
    
    .chatbot-body {
        flex: 1;
        padding: 15px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    
    .chatbot-message {
        max-width: 80%;
        padding: 10px 15px;
        border-radius: 18px;
        margin-bottom: 5px;
    }
    
    .chatbot-message.bot {
        align-self: flex-start;
        background: #F2F4F7;
        border-bottom-left-radius: 5px;
    }
    
    .chatbot-message.user {
        align-self: flex-end;
        background: #4E73DF;
        color: white;
        border-bottom-right-radius: 5px;
    }
    
    .chatbot-footer {
        padding: 10px 15px;
        display: flex;
        align-items: center;
        border-top: 1px solid #eee;
    }
    
    .chatbot-footer input {
        flex: 1;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 20px;
        outline: none;
    }
    
    .send-message {
        background: #4E73DF;
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        margin-left: 10px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Modal Styles */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        opacity: 1;
        transition: opacity 0.3s;
    }
    
    .modal-overlay.fade-out {
        opacity: 0;
    }
    
    .modal {
        background: white;
        border-radius: 8px;
        width: 90%;
        max-width: 500px;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
    }
    
    .modal-header {
        padding: 15px 20px;
        border-bottom: 1px solid #eee;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .modal-header h3 {
        margin: 0;
        font-size: 18px;
    }
    
    .close-modal {
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
    }
    
    .modal-body {
        padding: 20px;
    }
    
    .form-group {
        margin-bottom: 15px;
    }
    
    .form-row {
        display: flex;
        gap: 15px;
    }
    
    .form-row .form-group {
        flex: 1;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: 500;
    }
    
    .form-group input,
    .form-group select,
    .form-group textarea {
        width: 100%;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 4px;
        font-family: 'Inter', sans-serif;
    }
    
    .form-group textarea {
        height: 80px;
        resize: vertical;
    }
    
    .form-actions {
        display: flex;
        justify-content: flex-end;
        gap: 15px;
        margin-top: 20px;
    }
    
    .btn-outline {
        padding: 10px 15px;
        background: none;
        border: 1px solid #4E73DF;
        color: #4E73DF;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
    }
    
    .btn-primary {
        padding: 10px 15px;
        background: #4E73DF;
        border: none;
        color: white;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
    }
    
    /* Success Toast */
    .success-toast {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #1CC88A;
        color: white;
        padding: 12px 24px;
        border-radius: 4px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        z-index: 1001;
        opacity: 1;
        transition: opacity 0.3s;
    }
    
    .success-toast.fade-out {
        opacity: 0;
    }
    
    /* Currency Dropdown */
    .currency-dropdown {
        position: absolute;
        top: 100%;
        background: white;
        border-radius: 4px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        z-index: 100;
    }
    
    .currency-option {
        padding: 10px 15px;
        cursor: pointer;
    }
    
    .currency-option:hover {
        background: #f5f5f5;
    }
    
    /* Dark Mode Styles */
    .dark-mode {
        background-color: #1a1a2e;
        color: #f5f5f5;
    }
    
    .dark-mode .sidebar,
    .dark-mode .card,
    .dark-mode .section,
    .dark-mode .payouts-table,
    .dark-mode .chatbot-dialog,
    .dark-mode .modal {
        background-color: #16213e;
    }
    
    .dark-mode .sidebar-menu a,
    .dark-mode .sidebar-footer a {
        color: #f5f5f5;
    }
    
    .dark-mode .card h3,
    .dark-mode .section h2 {
        color: #f5f5f5;
    }
    
    .dark-mode .payouts-table th,
    .dark-mode .payouts-table td {
        border-color: #24385b;
        color: #f5f5f5;
    }
    
    .dark-mode .transaction-item,
    .dark-mode .budget-category,
    .dark-mode .goal-item,
    .dark-mode .recommendation-item {
        background-color: #24385b;
    }
    
    .dark-mode .chatbot-message.bot {
        background-color: #24385b;
        color: #f5f5f5;
    }
    
    .dark-mode .chatbot-footer input,
    .dark-mode .form-group input,
    .dark-mode .form-group select,
    .dark-mode .form-group textarea {
        background-color: #24385b;
        color: #f5f5f5;
        border-color: #304a75;
    }
    
    .dark-mode .search-container input {
        background-color: #24385b;
        color: #f5f5f5;
    }
`;

document.head.appendChild(style);