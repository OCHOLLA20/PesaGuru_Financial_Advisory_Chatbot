// Main application namespace
const PesaGuru = {
    // Configuration
    config: {
        apiEndpoint: 'https://api.pesaguru.co.ke/v1',
        defaultLanguage: 'en',
        autoSaveInterval: 30000, // 30 seconds
        notificationSound: '../../assets/sounds/notification.mp3',
        maxHistoryLength: 50,
        speechRecognitionSupported: 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window,
        chartsEnabled: typeof Chart !== 'undefined',
    },

    // User state
    user: {
        id: null,
        name: null,
        email: null,
        preferences: {
            darkMode: false,
            fontSize: 'medium',
            language: 'en',
            voiceInput: false,
            chatSounds: true,
            autoSave: true,
            emailNotifications: true,
            smsNotifications: false,
            pushNotifications: true
        },
        financialProfile: {
            monthlyIncome: 180000,
            monthlySavings: 35000,
            monthlyExpenses: 125000,
            totalSavings: 528000,
            totalInvestments: 2450000,
            budget: {
                total: 125000,
                spent: 81250, // 65% of budget
                categories: {
                    housing: { budget: 35000, spent: 35000 },
                    food: { budget: 25000, spent: 28000 },
                    transport: { budget: 12000, spent: 15000 },
                    entertainment: { budget: 8000, spent: 12000 },
                    utilities: { budget: 10000, spent: 10000 },
                    savings: { budget: 30000, spent: 25000 }
                }
            },
            goals: [
                {
                    id: 'goal-1',
                    type: 'emergency',
                    name: 'Emergency Fund',
                    targetAmount: 2000000,
                    currentAmount: 1200000,
                    startDate: '2023-06-01',
                    targetDate: '2025-12-31',
                    monthlyContribution: 25000
                }
            ],
            investments: [
                {
                    id: 'inv-1',
                    type: 'stock',
                    name: 'Safaricom',
                    symbol: 'SCOM',
                    amount: 1000000,
                    purchaseDate: '2022-01-15',
                    currentValue: 1125000,
                    returnRate: 12.5
                },
                {
                    id: 'inv-2',
                    type: 'stock',
                    name: 'KCB Group',
                    symbol: 'KCB',
                    amount: 700000,
                    purchaseDate: '2022-03-10',
                    currentValue: 758100,
                    returnRate: 8.3
                },
                {
                    id: 'inv-3',
                    type: 'government',
                    name: 'T-Bills (91 Day)',
                    amount: 500000,
                    purchaseDate: '2023-09-05',
                    currentValue: 551000,
                    returnRate: 10.2
                }
            ]
        }
    },

    // Chat state
    chat: {
        history: [],
        context: {},
        processing: false,
        saveTimeout: null,
        pinned: [],
        suggestions: [
            "How much did I spend on groceries?",
            "Show my investment portfolio",
            "What's my savings progress?",
            "Latest NSE market updates"
        ]
    },

    // Market data cache
    marketData: {
        nse: {
            index: 1850.25,
            change: 2.1,
            lastUpdated: null,
            topGainers: [
                { symbol: 'SCOM', name: 'Safaricom', price: 32.50, change: 3.4 },
                { symbol: 'EQTY', name: 'Equity Group', price: 45.75, change: 2.8 },
                { symbol: 'KCB', name: 'KCB Group', price: 38.25, change: 2.5 }
            ],
            topLosers: [
                { symbol: 'BAMB', name: 'Bamburi Cement', price: 42.75, change: -1.8 },
                { symbol: 'EABL', name: 'East African Breweries', price: 150.25, change: -1.5 },
                { symbol: 'COOP', name: 'Co-operative Bank', price: 12.10, change: -0.8 }
            ]
        },
        forex: {
            rates: [
                { currency: 'USD', rate: 147.25, change: 0.3 },
                { currency: 'EUR', rate: 159.83, change: -0.2 },
                { currency: 'GBP', rate: 182.76, change: 0.5 }
            ],
            lastUpdated: null
        },
        crypto: {
            rates: [
                { name: 'Bitcoin', symbol: 'BTC', price: 7506250, change: 1.8 },
                { name: 'Ethereum', symbol: 'ETH', price: 419675, change: 2.5 },
                { name: 'Solana', symbol: 'SOL', price: 22088, change: 3.2 }
            ],
            lastUpdated: null
        }
    },

    /**
     * Initialize the application
     */
    init: function() {
        this.loadUserPreferences();
        this.setupEventListeners();
        this.applyUserPreferences();
        this.renderCharts();
        this.setupAutosave();
        
        // Initialize user data
        this.user.id = 'user-12345';
        this.user.name = 'Sharon Bukaya';
        this.user.email = 'sharon.bukaya@example.com';
        
        console.log('PesaGuru initialized');
    },

    /**
     * Set up all event listeners
     */
    setupEventListeners: function() {
        // Tab navigation
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', this.handleTabChange.bind(this));
        });

        // Menu toggle
        const menuToggle = document.getElementById('menuToggle');
        if (menuToggle) {
            menuToggle.addEventListener('click', this.toggleSideNav.bind(this));
        }

        // Context panel toggle
        const collapseContextBtn = document.getElementById('collapseContextBtn');
        if (collapseContextBtn) {
            collapseContextBtn.addEventListener('click', this.toggleContextPanel.bind(this));
        }

        // Chat input
        const messageInput = document.getElementById('messageInput');
        const sendMessageBtn = document.getElementById('sendMessageBtn');
        
        if (messageInput && sendMessageBtn) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            sendMessageBtn.addEventListener('click', this.sendMessage.bind(this));
        }

        // Smart suggestions
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (messageInput) {
                    messageInput.value = e.target.textContent;
                    this.sendMessage();
                }
            });
        });

        // Voice input
        const voiceInputBtn = document.getElementById('voiceInputBtn');
        if (voiceInputBtn && this.config.speechRecognitionSupported) {
            voiceInputBtn.addEventListener('click', this.toggleVoiceInput.bind(this));
        } else if (voiceInputBtn) {
            voiceInputBtn.style.display = 'none';
        }

        // Attachment button
        const attachmentBtn = document.getElementById('attachmentBtn');
        if (attachmentBtn) {
            attachmentBtn.addEventListener('click', this.handleAttachment.bind(this));
        }

        // Floating Action Button
        const fabBtn = document.getElementById('fabBtn');
        if (fabBtn) {
            fabBtn.addEventListener('click', this.toggleFAB.bind(this));
            
            // FAB actions
            document.querySelectorAll('.fab-action').forEach(action => {
                action.addEventListener('click', this.handleFabAction.bind(this));
            });
        }

        // Modals
        this.setupModalListeners();

        // Notifications
        const notificationsBtn = document.getElementById('notificationsBtn');
        if (notificationsBtn) {
            notificationsBtn.addEventListener('click', () => {
                this.showModal('notificationsModal');
            });
        }

        // Search
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.showModal('searchModal');
                document.getElementById('searchInput')?.focus();
            });
        }

        // Profile dropdown
        const profileDropdown = document.getElementById('profileDropdown');
        if (profileDropdown) {
            profileDropdown.addEventListener('click', this.toggleProfileDropdown.bind(this));
        }

        // Card actions
        document.querySelectorAll('.card-action').forEach(btn => {
            btn.addEventListener('click', this.handleCardAction.bind(this));
        });
    },

    /**
     * Set up listeners for modals
     */
    setupModalListeners: function() {
        // Close buttons for all modals
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    modal.classList.remove('show');
                }
            });
        });

        // Close modals when clicking outside
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                }
            });
        });

        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal.show').forEach(modal => {
                    modal.classList.remove('show');
                });
            }
        });

        // Save settings button
        const saveSettingsBtn = document.getElementById('saveSettings');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => {
                this.saveUserPreferences();
                this.showToast('Settings saved successfully', 'success');
                document.getElementById('settingsModal')?.classList.remove('show');
            });
        }

        // Goal form save button
        const saveGoalBtn = document.getElementById('saveGoal');
        if (saveGoalBtn) {
            saveGoalBtn.addEventListener('click', this.saveFinancialGoal.bind(this));
        }

        // Notification actions
        document.querySelectorAll('.notification-actions button').forEach(btn => {
            btn.addEventListener('click', this.handleNotificationAction.bind(this));
        });

        // Mark all notifications as read
        const markAllReadBtn = document.getElementById('markAllRead');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => {
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread');
                });
                document.querySelector('.notification-badge')?.remove();
                this.showToast('All notifications marked as read', 'success');
            });
        }

        // Clear all notifications
        const clearNotificationsBtn = document.getElementById('clearNotifications');
        if (clearNotificationsBtn) {
            clearNotificationsBtn.addEventListener('click', () => {
                document.querySelector('.notifications-list').innerHTML = 
                    '<p class="empty-state">No notifications</p>';
                document.querySelector('.notification-badge')?.remove();
                this.showToast('All notifications cleared', 'success');
            });
        }

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.handleSearch.bind(this));
        }

        // Search categories
        document.querySelectorAll('.search-category').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.search-category').forEach(b => 
                    b.classList.remove('active'));
                e.target.classList.add('active');
                
                if (searchInput.value.trim()) {
                    this.handleSearch({ target: searchInput });
                }
            });
        });
    },

    /**
     * Handle tab changes
     * @param {Event} e - Click event
     */
    handleTabChange: function(e) {
        const tabName = e.target.closest('.tab-btn').dataset.tab;
        
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Show active tab content
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `${tabName}Tab`);
        });
        
        // Trigger any tab-specific initialization
        if (tabName === 'insights') {
            this.refreshMarketData();
        }
    },

    /**
     * Toggle side navigation
     */
    toggleSideNav: function() {
        const sideNav = document.getElementById('sideNav');
        if (sideNav) {
            sideNav.classList.toggle('show');
            
            const icon = document.querySelector('#menuToggle i');
            if (icon) {
                icon.className = sideNav.classList.contains('show') ? 
                    'fas fa-times' : 'fas fa-bars';
            }
        }
    },

    /**
     * Toggle context panel
     */
    toggleContextPanel: function() {
        const contextPanel = document.getElementById('contextPanel');
        const contextBody = contextPanel?.querySelector('.context-body');
        const icon = document.querySelector('#collapseContextBtn i');
        
        if (contextBody && icon) {
            const isCollapsed = contextBody.style.display === 'none';
            
            // Toggle visibility with animation
            if (isCollapsed) {
                contextBody.style.display = 'flex';
                icon.className = 'fas fa-chevron-up';
                
                // Animate height
                const height = contextBody.scrollHeight;
                contextBody.style.maxHeight = '0px';
                setTimeout(() => {
                    contextBody.style.maxHeight = `${height}px`;
                }, 10);
            } else {
                contextBody.style.maxHeight = '0px';
                icon.className = 'fas fa-chevron-down';
                
                // Hide after animation
                setTimeout(() => {
                    contextBody.style.display = 'none';
                }, 300);
            }
        }
    },

    /**
     * Send a message to the chatbot
     */
    sendMessage: function() {
        // Get message from input
        const messageInput = document.getElementById('messageInput');
        if (!messageInput) return;
        
        const message = messageInput.value.trim();
        if (!message || this.chat.processing) return;
        
        // Clear input
        messageInput.value = '';
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Process message and get bot response
        this.processChatbotResponse(message);
    },

    /**
     * Process user message and generate chatbot response
     * @param {string} message - User message
     */
    processChatbotResponse: function(message) {
        this.chat.processing = true;
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // In a real implementation, this would call an API
        // For demo purposes, we'll use a simulated response
        setTimeout(() => {
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Process the intent to determine the right response
            const intent = this.detectIntent(message);
            
            // Generate response based on intent
            let response;
            
            switch (intent) {
                case 'budget_inquiry':
                    response = this.generateBudgetResponse();
                    break;
                    
                case 'investment_inquiry':
                    response = this.generateInvestmentResponse();
                    break;
                    
                case 'savings_inquiry':
                    response = this.generateSavingsResponse();
                    break;
                    
                case 'market_inquiry':
                    response = this.generateMarketResponse();
                    break;
                    
                default:
                    // Default fallback response
                    response = {
                        text: "I'm not sure I understand your question about finances. Could you please provide more details or ask in a different way?",
                        type: 'text'
                    };
            }
            
            // Add bot response to chat
            this.addMessage(response, 'bot');
            
            // Update suggestions based on context
            this.updateSmartSuggestions(intent);
            
            this.chat.processing = false;
        }, 1500);
    },

    /**
     * Add a message to the chat history
     * @param {string|Object} message - Message text or object with message details
     * @param {string} sender - 'user' or 'bot'
     */
    addMessage: function(message, sender) {
        const chatHistory = document.getElementById('chatHistory');
        if (!chatHistory) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Create message content based on type
        let messageContent;
        
        if (typeof message === 'string') {
            // Simple text message
            messageContent = `
                <div class="message-avatar">
                    <img src="../../assets/images/${sender === 'user' ? 'user' : 'bot'}-avatar.png" alt="${sender === 'user' ? 'User' : 'Bot'} Avatar">
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <p>${message}</p>
                    </div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        } else {
            // Complex message with components
            let bubbleContent = '';
            
            if (message.text) {
                bubbleContent += `<p>${message.text}</p>`;
            }
            
            // Add card if present
            if (message.card) {
                bubbleContent += this.createCardHTML(message.card);
            }
            
            // Add chart if present
            if (message.chart) {
                bubbleContent += `
                    <div class="chart-container" id="${message.chart.id}">
                        <div class="chart-placeholder">
                            <p>${message.chart.title || 'Loading chart...'}</p>
                        </div>
                    </div>
                `;
            }
            
            messageContent = `
                <div class="message-avatar">
                    <img src="../../assets/images/${sender === 'user' ? 'user' : 'bot'}-avatar.png" alt="${sender === 'user' ? 'User' : 'Bot'} Avatar">
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        ${bubbleContent}
                    </div>
                    <div class="message-time">${timestamp}</div>
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageContent;
        chatHistory.appendChild(messageDiv);
        
        // Scroll to bottom
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Add to chat history array
        this.chat.history.push({
            sender,
            content: message,
            timestamp: new Date().toISOString()
        });
        
        // Create chart if needed
        if (typeof message === 'object' && message.chart) {
            this.createChart(message.chart.id, message.chart.type, message.chart.data, message.chart.options);
        }
        
        // Play notification sound for bot messages
        if (sender === 'bot' && this.user.preferences.chatSounds) {
            this.playNotificationSound();
        }
        
        // Truncate chat history if it gets too long
        if (this.chat.history.length > this.config.maxHistoryLength) {
            this.chat.history = this.chat.history.slice(-this.config.maxHistoryLength);
        }
    },

    /**
     * Show typing indicator in chat
     */
    showTypingIndicator: function() {
        const chatHistory = document.getElementById('chatHistory');
        if (!chatHistory) return;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <img src="../../assets/images/bot-avatar.png" alt="Bot Avatar">
            </div>
            <div class="message-content">
                <div class="message-bubble typing">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        
        chatHistory.appendChild(typingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    },

    /**
     * Hide typing indicator
     */
    hideTypingIndicator: function() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    },

    /**
     * Create HTML for a card component
     * @param {Object} card - Card data
     * @returns {string} HTML string
     */
    createCardHTML: function(card) {
        return `
            <div class="info-card">
                <div class="card-header">
                    <i class="${card.icon || 'fas fa-info-circle'}"></i>
                    <span>${card.title || 'Information'}</span>
                    <div class="card-actions">
                        <button class="card-action" title="Pin"><i class="fas fa-thumbtack"></i></button>
                        <button class="card-action" title="Expand"><i class="fas fa-expand"></i></button>
                    </div>
                </div>
                <div class="card-body">
                    ${card.content || ''}
                </div>
                ${card.buttons ? `
                    <div class="card-footer">
                        ${card.buttons.map(btn => `
                            <button class="btn-${btn.primary ? 'primary' : 'secondary'}" data-action="${btn.action || ''}">${btn.text}</button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    },

    /**
     * Update smart suggestions based on context
     * @param {string} intent - User intent
     */
    updateSmartSuggestions: function(intent) {
        const suggestionsDiv = document.getElementById('smartSuggestions');
        if (!suggestionsDiv) return;
        
        // Clear existing suggestions
        suggestionsDiv.innerHTML = '';
        
        // Get suggestions based on intent
        let suggestions;
        
        switch (intent) {
            case 'budget_inquiry':
                suggestions = [
                    "How can I reduce my expenses?",
                    "Show me spending by category",
                    "Create a new budget",
                    "Compare my budget to last month"
                ];
                break;
                
            case 'investment_inquiry':
                suggestions = [
                    "What stocks should I buy?",
                    "Show my investment performance",
                    "Recommend investment opportunities",
                    "What's my investment risk profile?"
                ];
                break;
                
            case 'savings_inquiry':
                suggestions = [
                    "How can I save more money?",
                    "Set a new savings goal",
                    "Best savings accounts in Kenya",
                    "When will I reach my savings goal?"
                ];
                break;
                
            case 'market_inquiry':
                suggestions = [
                    "How is Safaricom performing?",
                    "What's the USD to KES rate?",
                    "Top gainers in NSE today",
                    "Should I invest in T-bills now?"
                ];
                break;
                
            default:
                suggestions = this.chat.suggestions;
        }
        
        // Add new suggestions
        suggestions.forEach(suggestion => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.textContent = suggestion;
            btn.addEventListener('click', () => {
                document.getElementById('messageInput').value = suggestion;
                this.sendMessage();
            });
            
            suggestionsDiv.appendChild(btn);
        });
    },

    /**
     * Detect user intent from message
     * @param {string} message - User message
     * @returns {string} Intent type
     */
    detectIntent: function(message) {
        message = message.toLowerCase();
        
        if (message.includes('budget') || message.includes('spend') || message.includes('expense')) {
            return 'budget_inquiry';
        } else if (message.includes('invest') || message.includes('stock') || message.includes('portfolio')) {
            return 'investment_inquiry';
        } else if (message.includes('save') || message.includes('savings') || message.includes('goal')) {
            return 'savings_inquiry';
        } else if (message.includes('market') || message.includes('nse') || message.includes('forex') || 
                   message.includes('rate') || message.includes('crypto')) {
            return 'market_inquiry';
        }
        
        return 'general_inquiry';
    },

    /**
     * Generate budget response
     * @returns {Object} Response object
     */
    generateBudgetResponse: function() {
        const budget = this.user.financialProfile.budget;
        const daysLeft = 10; // Mock days left in month
        const spentPercentage = Math.round((budget.spent / budget.total) * 100);
        
        return {
            text: `Here's your budget status for this month:`,
            type: 'budget',
            card: {
                title: 'Monthly Budget Overview',
                icon: 'fas fa-money-bill-wave',
                content: `
                    <div class="finance-metric">
                        <span class="metric-label">Total Budget</span>
                        <span class="metric-value">KES ${budget.total.toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Spent So Far</span>
                        <span class="metric-value">KES ${budget.spent.toLocaleString()}</span>
                        <span class="metric-trend ${spentPercentage > 80 ? 'negative' : 'positive'}">
                            ${spentPercentage}%
                        </span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Remaining</span>
                        <span class="metric-value">KES ${(budget.total - budget.spent).toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Daily Budget Remaining</span>
                        <span class="metric-value">KES ${Math.round((budget.total - budget.spent) / daysLeft).toLocaleString()}/day</span>
                    </div>
                `,
                buttons: [
                    { text: 'View Details', action: 'view_budget_details', primary: true },
                    { text: 'Adjust Budget', action: 'adjust_budget', primary: false }
                ]
            },
            chart: {
                id: 'budgetChart' + Date.now(),
                type: 'bar',
                title: 'Budget vs. Spending by Category',
                data: {
                    labels: Object.keys(budget.categories).map(cat => cat.charAt(0).toUpperCase() + cat.slice(1)),
                    datasets: [
                        {
                            label: 'Budget',
                            data: Object.values(budget.categories).map(cat => cat.budget),
                            backgroundColor: 'rgba(67, 97, 238, 0.6)',
                            borderColor: 'rgba(67, 97, 238, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Spent',
                            data: Object.values(budget.categories).map(cat => cat.spent),
                            backgroundColor: 'rgba(247, 37, 133, 0.6)',
                            borderColor: 'rgba(247, 37, 133, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: false
                        }
                    }
                }
            }
        };
    },

    /**
     * Generate investment response
     * @returns {Object} Response object
     */
    generateInvestmentResponse: function() {
        const investments = this.user.financialProfile.investments;
        const totalInvested = investments.reduce((total, inv) => total + inv.amount, 0);
        const totalValue = investments.reduce((total, inv) => total + inv.currentValue, 0);
        const totalReturn = ((totalValue - totalInvested) / totalInvested) * 100;
        
        return {
            text: `Here's an overview of your investment portfolio:`,
            type: 'investment',
            card: {
                title: 'Investment Portfolio Summary',
                icon: 'fas fa-chart-line',
                content: `
                    <div class="finance-metric">
                        <span class="metric-label">Total Invested</span>
                        <span class="metric-value">KES ${totalInvested.toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Current Value</span>
                        <span class="metric-value">KES ${totalValue.toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Overall Return</span>
                        <span class="metric-value">${totalReturn.toFixed(1)}%</span>
                        <span class="metric-trend ${totalReturn >= 0 ? 'positive' : 'negative'}">
                            <i class="fas fa-arrow-${totalReturn >= 0 ? 'up' : 'down'}"></i>
                            KES ${Math.abs(totalValue - totalInvested).toLocaleString()}
                        </span>
                    </div>
                    
                    <div class="section-title">Investment Breakdown</div>
                    <div class="investment-list">
                        ${investments.map(inv => `
                            <div class="investment-item">
                                <div class="investment-info">
                                    <span class="investment-name">${inv.name}</span>
                                    <span class="investment-type">${inv.type.charAt(0).toUpperCase() + inv.type.slice(1)}</span>
                                </div>
                                <div class="investment-metrics">
                                    <span class="investment-value">KES ${inv.currentValue.toLocaleString()}</span>
                                    <span class="investment-return ${inv.returnRate >= 0 ? 'positive' : 'negative'}">
                                        ${inv.returnRate >= 0 ? '+' : ''}${inv.returnRate}%
                                    </span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `,
                buttons: [
                    { text: 'Investment Details', action: 'view_investments', primary: true },
                    { text: 'Add Investment', action: 'add_investment', primary: false }
                ]
            },
            chart: {
                id: 'investmentChart' + Date.now(),
                type: 'pie',
                title: 'Investment Allocation',
                data: {
                    labels: investments.map(inv => inv.name),
                    datasets: [{
                        data: investments.map(inv => inv.currentValue),
                        backgroundColor: [
                            'rgba(67, 97, 238, 0.7)',
                            'rgba(247, 37, 133, 0.7)',
                            'rgba(58, 12, 163, 0.7)',
                            'rgba(114, 9, 183, 0.7)',
                            'rgba(67, 97, 238, 0.7)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            }
        };
    },

    /**
     * Generate savings response
     * @returns {Object} Response object
     */
    generateSavingsResponse: function() {
        const goals = this.user.financialProfile.goals;
        const totalSavings = this.user.financialProfile.totalSavings;
        const monthlySavings = this.user.financialProfile.monthlySavings;
        const monthlyIncome = this.user.financialProfile.monthlyIncome;
        const savingsRate = (monthlySavings / monthlyIncome) * 100;
        
        return {
            text: `Here's your savings status:`,
            type: 'savings',
            card: {
                title: 'Savings Overview',
                icon: 'fas fa-piggy-bank',
                content: `
                    <div class="finance-metric">
                        <span class="metric-label">Total Savings</span>
                        <span class="metric-value">KES ${totalSavings.toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Monthly Savings</span>
                        <span class="metric-value">KES ${monthlySavings.toLocaleString()}</span>
                    </div>
                    <div class="finance-metric">
                        <span class="metric-label">Savings Rate</span>
                        <span class="metric-value">${savingsRate.toFixed(1)}% of income</span>
                        <span class="metric-trend ${savingsRate >= 20 ? 'positive' : 'negative'}">
                            <i class="fas fa-${savingsRate >= 20 ? 'check' : 'exclamation'}-circle"></i>
                            ${savingsRate >= 20 ? 'On track' : 'Below target'}
                        </span>
                    </div>
                    
                    ${goals.length > 0 ? `
                        <div class="section-title">Savings Goals</div>
                        ${goals.map(goal => {
                            const progress = (goal.currentAmount / goal.targetAmount) * 100;
                            const targetDate = new Date(goal.targetDate);
                            const now = new Date();
                            const monthsLeft = (targetDate.getFullYear() - now.getFullYear()) * 12 + 
                                              (targetDate.getMonth() - now.getMonth());
                            
                            return `
                                <div class="goal-item">
                                    <div class="goal-info">
                                        <span class="goal-name">${goal.name}</span>
                                        <div class="goal-progress-bar">
                                            <div class="progress" style="width: ${progress}%"></div>
                                        </div>
                                        <div class="goal-progress-info">
                                            <span>KES ${goal.currentAmount.toLocaleString()} of ${goal.targetAmount.toLocaleString()}</span>
                                            <span>${progress.toFixed(0)}%</span>
                                        </div>
                                    </div>
                                    <div class="goal-metrics">
                                        <div class="goal-metric">
                                            <span class="metric-label">Monthly</span>
                                            <span class="metric-value">KES ${goal.monthlyContribution.toLocaleString()}</span>
                                        </div>
                                        <div class="goal-metric">
                                            <span class="metric-label">Time Left</span>
                                            <span class="metric-value">${monthsLeft} months</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    ` : ''}
                `,
                buttons: [
                    { text: 'Set New Goal', action: 'set_savings_goal', primary: true },
                    { text: 'View All Goals', action: 'view_savings_goals', primary: false }
                ]
            }
        };
    },

    /**
     * Generate market response
     * @returns {Object} Response object
     */
    generateMarketResponse: function() {
        const nseData = this.marketData.nse;
        const forexData = this.marketData.forex;
        
        return {
            text: `Here's the current market overview:`,
            type: 'market',
            card: {
                title: 'Market Summary',
                icon: 'fas fa-chart-bar',
                content: `
                    <div class="section-title">NSE (Nairobi Securities Exchange)</div>
                    <div class="finance-metric">
                        <span class="metric-label">NSE 20 Index</span>
                        <span class="metric-value">${nseData.index.toLocaleString()}</span>
                        <span class="metric-trend ${nseData.change >= 0 ? 'positive' : 'negative'}">
                            <i class="fas fa-arrow-${nseData.change >= 0 ? 'up' : 'down'}"></i>
                            ${Math.abs(nseData.change).toFixed(1)}%
                        </span>
                    </div>
                    
                    <div class="market-columns">
                        <div class="market-column">
                            <div class="column-title positive">Top Gainers</div>
                            ${nseData.topGainers.slice(0, 3).map(stock => `
                                <div class="stock-item">
                                    <span class="stock-symbol">${stock.symbol}</span>
                                    <span class="stock-price">KES ${stock.price}</span>
                                    <span class="stock-change positive">+${stock.change}%</span>
                                </div>
                            `).join('')}
                        </div>
                        <div class="market-column">
                            <div class="column-title negative">Top Losers</div>
                            ${nseData.topLosers.slice(0, 3).map(stock => `
                                <div class="stock-item">
                                    <span class="stock-symbol">${stock.symbol}</span>
                                    <span class="stock-price">KES ${stock.price}</span>
                                    <span class="stock-change negative">${stock.change}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="section-title">Forex Exchange Rates (KES)</div>
                    <div class="forex-grid">
                        ${forexData.rates.map(rate => `
                            <div class="forex-item">
                                <div class="forex-currency">${rate.currency}</div>
                                <div class="forex-rate">${rate.rate.toFixed(2)}</div>
                                <div class="forex-change ${rate.change >= 0 ? 'negative' : 'positive'}">
                                    <i class="fas fa-arrow-${rate.change >= 0 ? 'up' : 'down'}"></i>
                                    ${Math.abs(rate.change).toFixed(1)}%
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `,
                buttons: [
                    { text: 'Market Details', action: 'view_market_details', primary: true },
                    { text: 'Trading View', action: 'view_trading', primary: false }
                ]
            }
        };
    },

    /**
     * Create or update a chart
     * @param {string} chartId - Container element ID
     * @param {string} type - Chart type (bar, line, pie, etc.)
     * @param {Object} data - Chart data
     * @param {Object} options - Chart options
     */
    createChart: function(chartId, type, data, options) {
        if (!this.config.chartsEnabled) return;
        
        const ctx = document.getElementById(chartId);
        if (!ctx) return;
        
        // Clear placeholder
        ctx.innerHTML = '';
        
        // Create canvas element
        const canvas = document.createElement('canvas');
        ctx.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: type,
            data: data,
            options: options || {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    },

    /**
     * Toggle voice input
     */
    toggleVoiceInput: function() {
        if (!this.config.speechRecognitionSupported) return;
        
        const voiceBtn = document.getElementById('voiceInputBtn');
        if (!voiceBtn) return;
        
        const isListening = voiceBtn.classList.contains('listening');
        
        if (isListening) {
            // Stop listening
            if (window.recognition) {
                window.recognition.stop();
            }
            
            voiceBtn.classList.remove('listening');
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        } else {
            // Start listening
            voiceBtn.classList.add('listening');
            voiceBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            window.recognition = new SpeechRecognition();
            
            window.recognition.lang = this.user.preferences.language === 'en' ? 'en-US' : 'sw-KE';
            window.recognition.continuous = false;
            window.recognition.interimResults = false;
            
            window.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
            };
            
            window.recognition.onend = () => {
                voiceBtn.classList.remove('listening');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                
                // Send message if we got a transcript
                if (document.getElementById('messageInput').value.trim()) {
                    setTimeout(() => this.sendMessage(), 500);
                }
            };
            
            window.recognition.onerror = (event) => {
                console.error('Speech recognition error', event.error);
                voiceBtn.classList.remove('listening');
                voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
                
                if (event.error === 'no-speech') {
                    this.showToast('No speech detected. Please try again.', 'warning');
                } else if (event.error === 'not-allowed') {
                    this.showToast('Microphone access denied. Check your browser permissions.', 'error');
                } else {
                    this.showToast('Voice recognition error. Please try again.', 'error');
                }
            };
            
            window.recognition.start();
        }
    },

    /**
     * Handle file attachment
     */
    handleAttachment: function() {
        // Create file input dynamically
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.pdf,.doc,.docx,.xls,.xlsx,.csv,.jpg,.jpeg,.png';
        fileInput.style.display = 'none';
        document.body.appendChild(fileInput);
        
        // Trigger click to open file dialog
        fileInput.click();
        
        // Handle file selection
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            // Show file being uploaded
            this.addMessage(`I'm uploading a file: ${file.name}`, 'user');
            
            // Simulate processing
            this.showTypingIndicator();
            
            setTimeout(() => {
                this.hideTypingIndicator();
                
                // Determine response based on file type
                let response;
                
                if (file.name.endsWith('.pdf') || file.name.endsWith('.doc') || file.name.endsWith('.docx')) {
                    response = {
                        text: `I've analyzed your document: ${file.name}`,
                        card: {
                            title: 'Document Analysis',
                            icon: 'fas fa-file-alt',
                            content: `
                                <p>This appears to be a financial document. I've extracted the following information:</p>
                                <ul>
                                    <li>Total Expenses: KES 125,000</li>
                                    <li>Total Income: KES 180,000</li>
                                    <li>Net Savings: KES 55,000</li>
                                </ul>
                                <p>Would you like me to import this data into your budget tracker?</p>
                            `,
                            buttons: [
                                { text: 'Import Data', action: 'import_data', primary: true },
                                { text: 'Just Save', action: 'save_file', primary: false }
                            ]
                        }
                    };
                } else if (file.name.endsWith('.xls') || file.name.endsWith('.xlsx') || file.name.endsWith('.csv')) {
                    response = {
                        text: `I've processed your spreadsheet: ${file.name}`,
                        card: {
                            title: 'Spreadsheet Analysis',
                            icon: 'fas fa-file-excel',
                            content: `
                                <p>I've analyzed your financial data and found the following:</p>
                                <ul>
                                    <li>3 months of transaction history</li>
                                    <li>152 transactions total</li>
                                    <li>Highest spending category: Food (28%)</li>
                                    <li>Notable income: Salary deposits (KES 180,000/month)</li>
                                </ul>
                                <p>Would you like me to categorize this data and create a spending report?</p>
                            `,
                            buttons: [
                                { text: 'Create Report', action: 'create_report', primary: true },
                                { text: 'Import Transactions', action: 'import_transactions', primary: false }
                            ]
                        }
                    };
                } else if (file.name.endsWith('.jpg') || file.name.endsWith('.jpeg') || file.name.endsWith('.png')) {
                    response = {
                        text: `I've received your image: ${file.name}`,
                        card: {
                            title: 'Receipt Processing',
                            icon: 'fas fa-receipt',
                            content: `
                                <p>This appears to be a receipt. I've extracted the following information:</p>
                                <ul>
                                    <li>Merchant: Carrefour Supermarket</li>
                                    <li>Date: March 14, 2025</li>
                                    <li>Total Amount: KES 5,240</li>
                                    <li>Payment Method: M-Pesa</li>
                                </ul>
                                <p>Would you like me to add this to your expenses?</p>
                            `,
                            buttons: [
                                { text: 'Add Expense', action: 'add_expense', primary: true },
                                { text: 'Cancel', action: 'cancel', primary: false }
                            ]
                        }
                    };
                } else {
                    response = {
                        text: `I've received your file: ${file.name}. How would you like me to process it?`
                    };
                }
                
                this.addMessage(response, 'bot');
            }, 2000);
            
            // Remove the input element
            document.body.removeChild(fileInput);
        });
    },

    /**
     * Toggle floating action button
     */
    toggleFAB: function() {
        const fabActions = document.getElementById('fabActions');
        const fabBtn = document.getElementById('fabBtn');
        
        if (fabActions && fabBtn) {
            const isExpanded = fabActions.classList.contains('show');
            
            if (isExpanded) {
                fabActions.classList.remove('show');
                fabBtn.innerHTML = '<i class="fas fa-plus"></i>';
            } else {
                fabActions.classList.add('show');
                fabBtn.innerHTML = '<i class="fas fa-times"></i>';
            }
        }
    },

    /**
     * Handle floating action button actions
     * @param {Event} e - Click event
     */
    handleFabAction: function(e) {
        const action = e.currentTarget.dataset.action;
        
        // Close FAB menu
        this.toggleFAB();
        
        // Handle different actions
        switch (action) {
            case 'goal':
                this.showModal('goalModal');
                break;
                
            case 'invest':
                this.addMessage('I want to invest now', 'user');
                this.processChatbotResponse('I want to invest now');
                break;
                
            case 'budget':
                this.addMessage('Update my budget', 'user');
                this.processChatbotResponse('Update my budget');
                break;
                
            case 'export':
                this.exportChatHistory();
                break;
        }
    },

    /**
     * Show a modal dialog
     * @param {string} modalId - Modal element ID
     */
    showModal: function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            
            // Focus first input if present
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    },

    /**
     * Handle notification actions
     * @param {Event} e - Click event
     */
    handleNotificationAction: function(e) {
        const action = e.currentTarget.title;
        const notificationItem = e.currentTarget.closest('.notification-item');
        
        if (action === 'Mark as read' && notificationItem) {
            notificationItem.classList.remove('unread');
            
            // Update badge count
            const unreadCount = document.querySelectorAll('.notification-item.unread').length;
            const badge = document.querySelector('.notification-badge');
            
            if (badge) {
                if (unreadCount === 0) {
                    badge.remove();
                } else {
                    badge.textContent = unreadCount;
                }
            }
        } else if (action === 'Delete' && notificationItem) {
            notificationItem.remove();
            
            // Update badge count if it was unread
            if (notificationItem.classList.contains('unread')) {
                const unreadCount = document.querySelectorAll('.notification-item.unread').length;
                const badge = document.querySelector('.notification-badge');
                
                if (badge) {
                    if (unreadCount === 0) {
                        badge.remove();
                    } else {
                        badge.textContent = unreadCount;
                    }
                }
            }
            
            // Show empty state if no notifications left
            const notificationsList = document.querySelector('.notifications-list');
            if (notificationsList && notificationsList.children.length === 0) {
                notificationsList.innerHTML = '<p class="empty-state">No notifications</p>';
            }
        }
    },

    /**
     * Handle card actions
     * @param {Event} e - Click event
     */
    handleCardAction: function(e) {
        const action = e.currentTarget.title;
        const card = e.currentTarget.closest('.info-card');
        
        if (action === 'Pin' && card) {
            // Clone card and add to pinned area
            this.showToast('Card pinned to dashboard', 'success');
        } else if (action === 'Expand' && card) {
            // Expand card in a modal
            const cardContent = card.outerHTML;
            
            // Create and show modal
            const modal = document.createElement('div');
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>${card.querySelector('.card-header span').textContent}</h2>
                        <button class="close-modal" aria-label="Close">×</button>
                    </div>
                    <div class="modal-body">
                        ${cardContent}
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Show modal
            setTimeout(() => modal.classList.add('show'), 10);
            
            // Add close event
            modal.querySelector('.close-modal').addEventListener('click', () => {
                modal.classList.remove('show');
                setTimeout(() => document.body.removeChild(modal), 300);
            });
            
            // Close when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.remove('show');
                    setTimeout(() => document.body.removeChild(modal), 300);
                }
            });
        }
    },

    /**
     * Toggle profile dropdown
     */
    toggleProfileDropdown: function() {
        // Implementation would depend on the HTML structure
        // This is a placeholder
        this.showToast('Profile menu clicked', 'info');
    },

    /**
     * Handle search
     * @param {Event} e - Input event
     */
    handleSearch: function(e) {
        const query = e.target.value.trim().toLowerCase();
        const resultsDiv = document.querySelector('.search-results');
        
        if (!resultsDiv) return;
        
        if (!query) {
            resultsDiv.innerHTML = '<p class="search-placeholder">Type to search across all PesaGuru features...</p>';
            return;
        }
        
        // Get active category
        const activeCategory = document.querySelector('.search-category.active').dataset.category;
        
        // Simulate search results based on query and category
        let results = [];
        
        if (activeCategory === 'all' || activeCategory === 'chat') {
            // Chat history results
            results.push({
                type: 'chat',
                icon: 'fas fa-comment',
                title: 'Budget Overview',
                description: 'Conversation about your monthly budget from yesterday',
                date: 'Mar 15, 2025'
            });
        }
        
        if (activeCategory === 'all' || activeCategory === 'tools') {
            // Tools results
            results.push({
                type: 'tool',
                icon: 'fas fa-calculator',
                title: 'Loan Calculator',
                description: 'Calculate loan payments and compare options',
                action: 'Open Tool'
            });
        }
        
        if (activeCategory === 'all' || activeCategory === 'insights') {
            // Insights results
            results.push({
                type: 'insight',
                icon: 'fas fa-chart-line',
                title: 'Stock Performance',
                description: 'Analysis of your investment portfolio performance',
                action: 'View Insight'
            });
        }
        
        if (activeCategory === 'all' || activeCategory === 'learn') {
            // Learning results
            results.push({
                type: 'learn',
                icon: 'fas fa-graduation-cap',
                title: 'Investment Basics',
                description: 'Course on understanding the fundamentals of investing',
                progress: '40% Complete'
            });
        }
        
        // Render results
        if (results.length === 0) {
            resultsDiv.innerHTML = '<p class="empty-state">No results found for "' + query + '"</p>';
        } else {
            resultsDiv.innerHTML = results.map(result => {
                let resultHTML = `
                    <div class="search-result ${result.type}">
                        <div class="result-icon"><i class="${result.icon}"></i></div>
                        <div class="result-content">
                            <div class="result-title">${result.title}</div>
                            <div class="result-description">${result.description}</div>
                `;
                
                if (result.date) {
                    resultHTML += `<div class="result-date">${result.date}</div>`;
                }
                
                if (result.progress) {
                    resultHTML += `<div class="result-progress">${result.progress}</div>`;
                }
                
                resultHTML += `</div>`;
                
                if (result.action) {
                    resultHTML += `<button class="btn-primary">${result.action}</button>`;
                }
                
                resultHTML += `</div>`;
                
                return resultHTML;
            }).join('');
            
            // Add event listeners to buttons
            resultsDiv.querySelectorAll('button').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.getElementById('searchModal').classList.remove('show');
                    this.showToast('Opening requested feature', 'success');
                });
            });
            
            // Make results clickable
            resultsDiv.querySelectorAll('.search-result').forEach(result => {
                result.addEventListener('click', (e) => {
                    if (e.target.tagName !== 'BUTTON') {
                        document.getElementById('searchModal').classList.remove('show');
                        this.showToast('Opening search result', 'success');
                    }
                });
            });
        }
    },

    /**
     * Save financial goal
     */
    saveFinancialGoal: function() {
        const form = document.getElementById('goalForm');
        if (!form) return;
        
        // Basic validation
        const goalType = document.getElementById('goalType').value;
        const goalName = document.getElementById('goalName').value;
        const goalAmount = parseFloat(document.getElementById('goalAmount').value);
        const currentAmount = parseFloat(document.getElementById('currentAmount').value || '0');
        const targetDate = document.getElementById('targetDate').value;
        const monthlyContribution = parseFloat(document.getElementById('monthlyContribution').value);
        
        if (!goalType || !goalName || !goalAmount || !targetDate || !monthlyContribution) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }
        
        // Create new goal
        const newGoal = {
            id: 'goal-' + Date.now(),
            type: goalType,
            name: goalName,
            targetAmount: goalAmount,
            currentAmount: currentAmount,
            startDate: new Date().toISOString().split('T')[0],
            targetDate: targetDate,
            monthlyContribution: monthlyContribution
        };
        
        // Add to user's goals
        this.user.financialProfile.goals.push(newGoal);
        
        // Close modal
        document.getElementById('goalModal').classList.remove('show');
        
        // Reset form
        form.reset();
        
        // Show confirmation in chat
        this.addMessage('I want to set a new financial goal', 'user');
        
        const progress = (currentAmount / goalAmount) * 100;
        const targetDateObj = new Date(targetDate);
        const now = new Date();
        const monthsLeft = (targetDateObj.getFullYear() - now.getFullYear()) * 12 + 
                          (targetDateObj.getMonth() - now.getMonth());
        
        const response = {
            text: `I've created your new financial goal!`,
            card: {
                title: 'New Financial Goal',
                icon: 'fas fa-bullseye',
                content: `
                    <div class="goal-item">
                        <div class="goal-info">
                            <span class="goal-name">${goalName}</span>
                            <div class="goal-progress-bar">
                                <div class="progress" style="width: ${progress}%"></div>
                            </div>
                            <div class="goal-progress-info">
                                <span>KES ${currentAmount.toLocaleString()} of ${goalAmount.toLocaleString()}</span>
                                <span>${progress.toFixed(0)}%</span>
                            </div>
                        </div>
                        <div class="goal-metrics">
                            <div class="goal-metric">
                                <span class="metric-label">Monthly</span>
                                <span class="metric-value">KES ${monthlyContribution.toLocaleString()}</span>
                            </div>
                            <div class="goal-metric">
                                <span class="metric-label">Time Left</span>
                                <span class="metric-value">${monthsLeft} months</span>
                            </div>
                        </div>
                    </div>
                    
                    <p>At your current contribution rate, you'll reach your goal by ${targetDateObj.toLocaleDateString()}.</p>
                    <p>Would you like to set up automatic monthly transfers to this goal?</p>
                `,
                buttons: [
                    { text: 'Set Up Transfers', action: 'setup_transfers', primary: true },
                    { text: 'Not Now', action: 'cancel', primary: false }
                ]
            }
        };
        
        this.addMessage(response, 'bot');
        
        // Show success toast
        this.showToast('Financial goal created successfully', 'success');
    },

    /**
     * Refresh market data
     */
    refreshMarketData: function() {
        // In a real implementation, this would fetch the latest data from API
        // For demo purposes, just simulate an update
        
        // Update last updated timestamp
        this.marketData.nse.lastUpdated = new Date();
        this.marketData.forex.lastUpdated = new Date();
        this.marketData.crypto.lastUpdated = new Date();
        
        // Render charts
        this.renderCharts();
        
        this.showToast('Market data refreshed', 'success');
    },

    /**
     * Render all charts in the application
     */
    renderCharts: function() {
        if (!this.config.chartsEnabled) return;
        
        // NSE Market Chart
        const nseChart = document.getElementById('nseMarketChart');
        if (nseChart) {
            nseChart.innerHTML = '';
            
            const canvas = document.createElement('canvas');
            nseChart.appendChild(canvas);
            
            // Example data - in a real app, this would come from API
            new Chart(canvas, {
                type: 'line',
                data: {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'NSE 20 Index',
                        data: [1820, 1835, 1810, 1845, 1830, 1850],
                        borderColor: 'rgba(67, 97, 238, 1)',
                        backgroundColor: 'rgba(67, 97, 238, 0.1)',
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
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
        
        // Budget Chart
        const budgetChart = document.getElementById('budgetChart');
        if (budgetChart) {
            budgetChart.innerHTML = '';
            
            const canvas = document.createElement('canvas');
            budgetChart.appendChild(canvas);
            
            const budget = this.user.financialProfile.budget;
            
            new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: Object.keys(budget.categories).map(cat => cat.charAt(0).toUpperCase() + cat.slice(1)),
                    datasets: [
                        {
                            label: 'Budget',
                            data: Object.values(budget.categories).map(cat => cat.budget),
                            backgroundColor: 'rgba(67, 97, 238, 0.6)',
                            borderColor: 'rgba(67, 97, 238, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Spent',
                            data: Object.values(budget.categories).map(cat => cat.spent),
                            backgroundColor: 'rgba(247, 37, 133, 0.6)',
                            borderColor: 'rgba(247, 37, 133, 1)',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
    },

    /**
     * Export chat history as text file
     */
    exportChatHistory: function() {
        if (this.chat.history.length === 0) {
            this.showToast('No chat history to export', 'warning');
            return;
        }
        
        let text = 'PesaGuru Chat History\n';
        text += `Exported on: ${new Date().toLocaleString()}\n\n`;
        
        this.chat.history.forEach(msg => {
            const sender = msg.sender === 'user' ? 'You' : 'PesaGuru';
            const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            text += `[${time}] ${sender}: `;
            
            if (typeof msg.content === 'string') {
                text += msg.content;
            } else if (msg.content.text) {
                text += msg.content.text;
            } else {
                text += '[Financial Information]';
            }
            
            text += '\n\n';
        });
        
        // Create and download file
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `PesaGuru-Chat-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showToast('Chat history exported successfully', 'success');
    },

    /**
     * Play notification sound
     */
    playNotificationSound: function() {
        if (!this.user.preferences.chatSounds) return;
        
        try {
            const audio = new Audio(this.config.notificationSound);
            audio.volume = 0.5;
            audio.play();
        } catch (error) {
            console.error('Error playing notification sound:', error);
        }
    },

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {number} duration - Display duration in ms
     */
    showToast: function(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' ? 'check-circle' : 
                    type === 'error' ? 'times-circle' :
                    type === 'warning' ? 'exclamation-triangle' : 'info-circle';
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas fa-${icon}"></i>
            </div>
            <div class="toast-content">${message}</div>
            <button class="toast-close">×</button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Auto remove after duration
        const timeout = setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toastContainer.removeChild(toast), 300);
        }, duration);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(timeout);
            toast.classList.remove('show');
            setTimeout(() => toastContainer.removeChild(toast), 300);
        });
    },

    /**
     * Load user preferences from localStorage
     */
    loadUserPreferences: function() {
        try {
            const savedPrefs = localStorage.getItem('pesaguru_preferences');
            if (savedPrefs) {
                this.user.preferences = JSON.parse(savedPrefs);
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
        }
    },

    /**
     * Save user preferences to localStorage
     */
    saveUserPreferences: function() {
        try {
            // Update preferences from form inputs
            this.user.preferences.darkMode = document.getElementById('darkMode').checked;
            this.user.preferences.fontSize = document.getElementById('fontSize').value;
            this.user.preferences.language = document.getElementById('language').value;
            this.user.preferences.voiceInput = document.getElementById('voiceInput').checked;
            this.user.preferences.chatSounds = document.getElementById('chatSounds').checked;
            this.user.preferences.autoSave = document.getElementById('autoSave').checked;
            this.user.preferences.emailNotifications = document.getElementById('emailNotifications').checked;
            this.user.preferences.smsNotifications = document.getElementById('smsNotifications').checked;
            this.user.preferences.pushNotifications = document.getElementById('pushNotifications').checked;
            
            // Save to localStorage
            localStorage.setItem('pesaguru_preferences', JSON.stringify(this.user.preferences));
            
            // Apply preferences
            this.applyUserPreferences();
        } catch (error) {
            console.error('Error saving preferences:', error);
            this.showToast('Error saving preferences', 'error');
        }
    },

    /**
     * Apply user preferences to UI
     */
    applyUserPreferences: function() {
        // Dark mode
        document.body.classList.toggle('dark-mode', this.user.preferences.darkMode);
        
        // Font size
        document.body.classList.remove('text-small', 'text-medium', 'text-large');
        document.body.classList.add(`text-${this.user.preferences.fontSize}`);
        
        // Update form controls to match preferences
        if (document.getElementById('darkMode')) {
            document.getElementById('darkMode').checked = this.user.preferences.darkMode;
        }
        
        if (document.getElementById('fontSize')) {
            document.getElementById('fontSize').value = this.user.preferences.fontSize;
        }
        
        if (document.getElementById('language')) {
            document.getElementById('language').value = this.user.preferences.language;
        }
        
        if (document.getElementById('voiceInput')) {
            document.getElementById('voiceInput').checked = this.user.preferences.voiceInput;
        }
        
        if (document.getElementById('chatSounds')) {
            document.getElementById('chatSounds').checked = this.user.preferences.chatSounds;
        }
        
        if (document.getElementById('autoSave')) {
            document.getElementById('autoSave').checked = this.user.preferences.autoSave;
        }
        
        if (document.getElementById('emailNotifications')) {
            document.getElementById('emailNotifications').checked = this.user.preferences.emailNotifications;
        }
        
        if (document.getElementById('smsNotifications')) {
            document.getElementById('smsNotifications').checked = this.user.preferences.smsNotifications;
        }
        
        if (document.getElementById('pushNotifications')) {
            document.getElementById('pushNotifications').checked = this.user.preferences.pushNotifications;
        }
        
        // Update autosave
        this.setupAutosave();
    },

    /**
     * Set up autosaving of conversation
     */
    setupAutosave: function() {
        // Clear existing timeout
        if (this.chat.saveTimeout) {
            clearTimeout(this.chat.saveTimeout);
        }
        
        // Set up new timeout if enabled
        if (this.user.preferences.autoSave) {
            this.chat.saveTimeout = setInterval(() => {
                // In a real implementation, this would save to a server
                console.log('Auto-saving conversation...');
            }, this.config.autoSaveInterval);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    PesaGuru.init();
});

document.addEventListener("DOMContentLoaded", function () {
    let storedUsername = localStorage.getItem("username"); // Fetch username from localStorage
    if (storedUsername) {
        document.getElementById("username").textContent = storedUsername;
    } else {
        document.getElementById("username").textContent = "Guest"; // Fallback if no name is found
    }
});

document.getElementById("openLoanCalculator").addEventListener("click", function(event) {
    event.preventDefault(); // Prevent default link behavior
    document.getElementById("loanCalculatorModal").style.display = "block";
});

document.querySelector(".close").addEventListener("click", function() {
    document.getElementById("loanCalculatorModal").style.display = "none";
});
