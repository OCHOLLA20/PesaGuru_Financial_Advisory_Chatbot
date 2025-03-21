document.addEventListener('DOMContentLoaded', function() {
    // Form elements
    const expenseForm = document.getElementById('expenseForm');
    const recurringExpenseToggle = document.getElementById('recurringExpense');
    const recurringOptions = document.getElementById('recurringOptions');
    const receiptUpload = document.getElementById('receiptUpload');
    const fileName = document.getElementById('fileName');
    const cancelButton = document.getElementById('cancelButton');
    const saveExpenseButton = document.getElementById('saveExpenseButton');
    
    // Modal elements
    const successModal = document.getElementById('successModal');
    const closeModal = document.querySelector('.close-modal');
    const addAnotherButton = document.getElementById('addAnotherButton');
    const viewDashboardButton = document.getElementById('viewDashboardButton');
    
    // Template buttons
    const templateButtons = document.querySelectorAll('.btn-use-template');
    const createTemplateButton = document.querySelector('.btn-create-template');
    
    // Theme toggle
    const themeToggle = document.querySelector('.theme-toggle');
    
    // Chatbot toggle
    const chatbotToggle = document.querySelector('.chatbot-toggle');
    
    // Set default date to today
    document.getElementById('expenseDate').valueAsDate = new Date();
    
    // Toggle recurring expense options
    recurringExpenseToggle.addEventListener('change', function() {
        if (this.checked) {
            recurringOptions.classList.remove('hidden');
        } else {
            recurringOptions.classList.add('hidden');
        }
    });
    
    // Display file name when receipt is uploaded
    receiptUpload.addEventListener('change', function() {
        if (this.files.length > 0) {
            fileName.textContent = this.files[0].name;
        } else {
            fileName.textContent = 'No file chosen';
        }
    });
    
    // Handle form submission
    expenseForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Basic form validation
        const title = document.getElementById('expenseTitle').value;
        const amount = document.getElementById('expenseAmount').value;
        const date = document.getElementById('expenseDate').value;
        const category = document.getElementById('expenseCategory').value;
        
        if (!title || !amount || !date || !category) {
            alert('Please fill in all required fields.');
            return;
        }
        
        // In a real application, you would send the data to a server here
        // For this demo, we'll just show the success modal
        successModal.style.display = 'flex';
        
        // You could store the expense data in localStorage for persistence
        saveExpenseToLocalStorage({
            title,
            amount,
            date,
            category,
            paymentMethod: document.getElementById('paymentMethod').value,
            description: document.getElementById('expenseDescription').value,
            isRecurring: recurringExpenseToggle.checked,
            frequency: document.getElementById('frequency').value,
            endDate: document.getElementById('endDate').value
        });
        
        // Update the chart
        updateCategoryChart();
    });
    
    // Cancel button
    cancelButton.addEventListener('click', function() {
        if (confirm('Are you sure you want to discard this expense?')) {
            expenseForm.reset();
            document.getElementById('expenseDate').valueAsDate = new Date();
            recurringOptions.classList.add('hidden');
            fileName.textContent = 'No file chosen';
        }
    });
    
    // Close modal
    closeModal.addEventListener('click', function() {
        successModal.style.display = 'none';
    });
    
    // Click outside modal to close
    window.addEventListener('click', function(e) {
        if (e.target === successModal) {
            successModal.style.display = 'none';
        }
    });
    
    // Add another expense
    addAnotherButton.addEventListener('click', function() {
        successModal.style.display = 'none';
        expenseForm.reset();
        document.getElementById('expenseDate').valueAsDate = new Date();
        recurringOptions.classList.add('hidden');
        fileName.textContent = 'No file chosen';
    });
    
    // View dashboard
    viewDashboardButton.addEventListener('click', function() {
        window.location.href = '../../index.html';
    });
    
    // Use expense template
    templateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateCard = this.closest('.template-card');
            const templateTitle = templateCard.querySelector('h3').textContent;
            const templateAmount = templateCard.querySelector('p').textContent.split('•')[1].trim().replace('KES ', '').replace(',', '');
            const templateFrequency = templateCard.querySelector('p').textContent.split('•')[0].trim().toLowerCase();
            
            // Fill the form with template data
            document.getElementById('expenseTitle').value = templateTitle;
            document.getElementById('expenseAmount').value = templateAmount;
            
            // Set category based on template title
            const categorySelect = document.getElementById('expenseCategory');
            switch (templateTitle) {
                case 'Rent Payment':
                    categorySelect.value = 'residential';
                    break;
                case 'Electricity Bill':
                case 'Internet':
                    categorySelect.value = 'utilities';
                    break;
                case 'Groceries':
                    categorySelect.value = 'food';
                    break;
                default:
                    categorySelect.value = 'other';
            }
            
            // Set recurring if applicable
            if (templateFrequency !== 'one-time') {
                recurringExpenseToggle.checked = true;
                recurringOptions.classList.remove('hidden');
                
                // Set frequency
                const frequencySelect = document.getElementById('frequency');
                if (templateFrequency === 'daily') frequencySelect.value = 'daily';
                if (templateFrequency === 'weekly') frequencySelect.value = 'weekly';
                if (templateFrequency === 'monthly') frequencySelect.value = 'monthly';
                if (templateFrequency === 'yearly') frequencySelect.value = 'yearly';
            }
            
            // Scroll to form
            document.querySelector('.add-expense-section').scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Create new template
    createTemplateButton.addEventListener('click', function() {
        const title = document.getElementById('expenseTitle').value;
        const amount = document.getElementById('expenseAmount').value;
        
        if (!title || !amount) {
            alert('Please fill in at least the expense title and amount to create a template.');
            return;
        }
        
        const frequency = recurringExpenseToggle.checked ? document.getElementById('frequency').value : 'one-time';
        
        // In a real application, you would save this template to the server
        // For now, we'll just alert the user
        alert(`Template "${title}" created successfully!`);
    });
    
    // Toggle dark/light theme
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const icon = this.querySelector('i');
        
        if (document.body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
        
        // Save preference to localStorage
        localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
        
        // Update chart colors if chart exists
        updateCategoryChart();
    });
    
    // Toggle chatbot widget
    chatbotToggle.addEventListener('click', function() {
        // In a real application, you would toggle the chatbot UI here
        alert('PesaGuru Assistant is coming soon!');
    });
    
    // Load saved theme preference
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        const icon = themeToggle.querySelector('i');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
    
    // Initialize category chart
    initCategoryChart();
    
    // Functions
    
    // Save expense to localStorage
    function saveExpenseToLocalStorage(expense) {
        let expenses = JSON.parse(localStorage.getItem('expenses')) || [];
        expenses.push({
            ...expense,
            id: Date.now(), // Use timestamp as a simple unique ID
            timestamp: new Date().toISOString()
        });
        localStorage.setItem('expenses', JSON.stringify(expenses));
    }
    
    // Initialize category spending chart
    function initCategoryChart() {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        // Get expense data from localStorage or use sample data
        const expenses = JSON.parse(localStorage.getItem('expenses')) || [];
        
        // Calculate spending by category
        const categoryData = calculateCategorySpending(expenses);
        
        // Chart colors (will be updated based on theme)
        const isDarkMode = document.body.classList.contains('dark-mode');
        const textColor = isDarkMode ? '#FFFFFF' : '#333333';
        
        // Create the chart
        window.categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: categoryData.labels,
                datasets: [{
                    data: categoryData.values,
                    backgroundColor: [
                        '#FF6384',
                        '#36A2EB',
                        '#FFCE56',
                        '#4BC0C0',
                        '#9966FF',
                        '#FF9F40',
                        '#7CFC00',
                        '#FF6B6B',
                        '#8A2BE2',
                        '#20B2AA',
                        '#FFD700'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: textColor,
                            font: {
                                family: 'Inter, sans-serif',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: KES ${value.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Update category chart
    function updateCategoryChart() {
        if (!window.categoryChart) {
            initCategoryChart();
            return;
        }
        
        // Get updated expense data
        const expenses = JSON.parse(localStorage.getItem('expenses')) || [];
        
        // Recalculate category spending
        const categoryData = calculateCategorySpending(expenses);
        
        // Update chart data
        window.categoryChart.data.labels = categoryData.labels;
        window.categoryChart.data.datasets[0].data = categoryData.values;
        
        // Update chart options based on theme
        const isDarkMode = document.body.classList.contains('dark-mode');
        const textColor = isDarkMode ? '#FFFFFF' : '#333333';
        window.categoryChart.options.plugins.legend.labels.color = textColor;
        
        // Update the chart
        window.categoryChart.update();
    }
    
    // Calculate spending by category
    function calculateCategorySpending(expenses) {
        // If no expenses, return sample data
        if (expenses.length === 0) {
            return {
                labels: ['Food & Dining', 'Transportation', 'Utilities', 'Entertainment', 'Shopping'],
                values: [15000, 7500, 5000, 3200, 8700]
            };
        }
        
        // Create a map of categories and their total spending
        const categoryMap = {};
        
        // Process each expense
        expenses.forEach(expense => {
            const category = getCategoryLabel(expense.category);
            const amount = parseFloat(expense.amount);
            
            if (!isNaN(amount)) {
                if (categoryMap[category]) {
                    categoryMap[category] += amount;
                } else {
                    categoryMap[category] = amount;
                }
            }
        });
        
        // Convert to arrays for chart
        const labels = Object.keys(categoryMap);
        const values = Object.values(categoryMap);
        
        return { labels, values };
    }
    
    // Get user-friendly category label
    function getCategoryLabel(categoryValue) {
        const categoryMap = {
            'residential': 'Residential Costs',
            'transportation': 'Transportation',
            'food': 'Food & Dining',
            'utilities': 'Utilities',
            'entertainment': 'Entertainment',
            'education': 'Education',
            'shopping': 'Shopping',
            'health': 'Health & Medical',
            'travel': 'Travel',
            'subscription': 'Subscriptions',
            'other': 'Other'
        };
        
        return categoryMap[categoryValue] || 'Other';
    }
});