// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Element references
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    const toggleChatbotBtn = document.getElementById('toggleChatbot');
    const closeChatbotBtn = document.getElementById('closeChatbot');
    const chatbotDialog = document.getElementById('chatbotDialog');
    const userMessageInput = document.getElementById('userMessage');
    const sendMessageBtn = document.getElementById('sendMessage');
    const chatbotMessages = document.getElementById('chatbotMessages');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const strategyTabs = document.querySelectorAll('.strategy-tab');
    const alertPreferencesForm = document.getElementById('alertPreferences');
    const updateRatesBtn = document.getElementById('updateRates');
    const refreshScoreBtn = document.getElementById('refreshScore');
    const backButton = document.getElementById('backButton');
    const refreshData = document.getElementById('refreshData');
    const viewReports = document.getElementById('viewReports');
    
    // Initialize theme from localStorage if available
    initTheme();
    
    // Event listeners
    themeToggle.addEventListener('change', toggleTheme);
    toggleChatbotBtn.addEventListener('click', openChatbot);
    closeChatbotBtn.addEventListener('click', closeChatbot);
    sendMessageBtn.addEventListener('click', sendMessage);
    userMessageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Loan category tabs
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            switchLoanTab(button);
        });
    });
    
    // Repayment strategy tabs
    strategyTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            switchStrategyTab(tab);
        });
    });
    
    // Alert preferences form
    if (alertPreferencesForm) {
        alertPreferencesForm.addEventListener('submit', saveAlertPreferences);
    }
    
    // Other button events
    if (updateRatesBtn) {
        updateRatesBtn.addEventListener('click', updateRates);
    }
    
    if (refreshScoreBtn) {
        refreshScoreBtn.addEventListener('click', refreshCreditScore);
    }
    
    if (backButton) {
        backButton.addEventListener('click', navigateBack);
    }
    
    if (refreshData) {
        refreshData.addEventListener('click', refreshPageData);
    }
    
    if (viewReports) {
        viewReports.addEventListener('click', viewFinancialReports);
    }
    
    // Initialize chatbot suggestions
    const chatbotPreview = document.getElementById('chatbotPreview');
    if (chatbotPreview) {
        const suggestions = chatbotPreview.querySelectorAll('.suggestion');
        suggestions.forEach(suggestion => {
            suggestion.addEventListener('click', () => {
                openChatbot();
                const questionText = suggestion.textContent.replace('Ask about: ', '').replace(/"/g, '');
                userMessageInput.value = questionText;
                // Auto-send after a short delay to simulate user typing
                setTimeout(() => {
                    sendMessage();
                }, 500);
            });
        });
    }
    
    // Theme toggle functionality
    function initTheme() {
        const savedTheme = localStorage.getItem('pesaGuruTheme');
        if (savedTheme === 'dark') {
            body.classList.add('dark-mode');
            themeToggle.checked = true;
        }
    }
    
    function toggleTheme() {
        if (themeToggle.checked) {
            body.classList.add('dark-mode');
            localStorage.setItem('pesaGuruTheme', 'dark');
        } else {
            body.classList.remove('dark-mode');
            localStorage.setItem('pesaGuruTheme', 'light');
        }
    }
    
    // Chatbot functionality
    function openChatbot() {
        chatbotDialog.classList.add('show');
        userMessageInput.focus();
    }
    
    function closeChatbot() {
        chatbotDialog.classList.remove('show');
    }
    
    function sendMessage() {
        const message = userMessageInput.value.trim();
        if (message === '') return;
        
        // Create and append user message
        addMessageToChat('user', message);
        
        // Clear input field
        userMessageInput.value = '';
        
        // Simulate AI thinking with a delay
        setTimeout(() => {
            const response = getChatbotResponse(message);
            addMessageToChat('bot', response);
            
            // Auto-scroll to the bottom of chat
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }, 1000);
    }
    
    function addMessageToChat(sender, message) {
        const now = new Date();
        const timeString = now.getHours() + ':' + now.getMinutes().toString().padStart(2, '0');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
            </div>
            <span class="message-time">${timeString}</span>
        `;
        
        chatbotMessages.appendChild(messageDiv);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    // Simple chatbot responses based on keywords
    function getChatbotResponse(message) {
        const lowerMessage = message.toLowerCase();
        
        if (lowerMessage.includes('credit score') || lowerMessage.includes('improve my credit')) {
            return "To improve your credit score, focus on these key factors: 1) Pay all bills on time, 2) Reduce credit card balances below 30% of your limit, 3) Don't close old credit accounts, 4) Limit applications for new credit, and 5) Regularly check your credit report for errors. Would you like me to analyze your specific credit situation?";
        }
        else if (lowerMessage.includes('best loan') || lowerMessage.includes('loan for my business')) {
            return "Based on your business profile, I recommend exploring the KCB Business Loan which offers competitive rates starting at 13% for established businesses. Equity Bank's Biashara Loan is also suitable with flexible collateral requirements. Would you like me to compare specific features of these loans?";
        }
        else if (lowerMessage.includes('interest rate')) {
            return "Current interest rates for personal loans in Kenya range from 13-19% depending on the bank and your credit profile. For business loans, rates typically range from 12-16%. The Central Bank Rate (CBR) is currently at 9.5%. Would you like specific rates from particular banks?";
        }
        else if (lowerMessage.includes('debt') || lowerMessage.includes('repayment')) {
            return "Looking at your current debt profile, the Avalanche Method would save you approximately KES 23,800 in interest compared to your current repayment approach. This involves prioritizing your Equity credit card (19.5% interest) first, then moving to your KCB personal loan. Would you like a detailed repayment schedule?";
        }
        else if (lowerMessage.includes('loan eligibility') || lowerMessage.includes('qualify')) {
            return "Loan eligibility typically depends on: 1) Credit score (680+ preferred), 2) Debt-to-income ratio (below 40% ideal), 3) Employment stability (min. 6 months), and 4) Collateral for secured loans. With your current profile, you likely qualify for loans up to KES 2.5M. Would you like me to pre-check your eligibility for specific loan products?";
        }
        else {
            return "Thank you for your question. I can provide information about loan options, credit scores, debt repayment strategies, and financial planning in Kenya. Could you please specify which aspect of loans or credit you'd like to learn more about?";
        }
    }
    
    // Tab switching functionality
    function switchLoanTab(selectedTab) {
        // Remove active class from all tabs
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });
        
        // Add active class to selected tab
        selectedTab.classList.add('active');
        
        // Update loan table content based on selected category
        const category = selectedTab.dataset.category;
        updateLoanTable(category);
    }
    
    function switchStrategyTab(selectedTab) {
        // Remove active class from all strategy tabs
        strategyTabs.forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Add active class to selected strategy tab
        selectedTab.classList.add('active');
        
        // Hide all strategy content sections
        const strategyContents = document.querySelectorAll('.strategy-content');
        strategyContents.forEach(content => {
            content.classList.remove('active');
        });
        
        // Show selected strategy content
        const strategy = selectedTab.dataset.strategy;
        const selectedContent = document.getElementById(`${strategy}-strategy`);
        if (selectedContent) {
            selectedContent.classList.add('active');
        }
    }
    
    // Update loan table based on category
    function updateLoanTable(category) {
        const loanTable = document.getElementById('loanTable');
        if (!loanTable) return;
        
        const tableBody = loanTable.querySelector('tbody');
        tableBody.innerHTML = ''; // Clear existing rows
        
        // Get loan data for selected category
        const loans = getLoanData(category);
        
        // Generate and append table rows
        loans.forEach(loan => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${loan.lender}</td>
                <td>${loan.interestRate}</td>
                <td>${loan.term}</td>
                <td>${loan.monthlyPayment}</td>
                <td>${loan.totalRepayable}</td>
                <td>${loan.eligibility}</td>
                <td><button class="btn btn-sm btn-primary">Apply</button></td>
            `;
            tableBody.appendChild(row);
        });
        
        // Add event listeners to new Apply buttons
        const applyButtons = tableBody.querySelectorAll('.btn-primary');
        applyButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Get the lender name from the parent row
                const lenderCell = button.closest('tr').querySelector('td:first-child');
                const lenderName = lenderCell ? lenderCell.textContent : 'selected lender';
                
                // Show alert for demo purposes
                alert(`Redirecting to application form for ${lenderName}. In a real application, this would take you to the lender's website or a secure application form.`);
            });
        });
    }
    
    // Simulated loan data by category
    function getLoanData(category) {
        const loanData = {
            personal: [
                { lender: 'KCB Bank', interestRate: '13.5%', term: '12-48 months', monthlyPayment: 'KES 12,350', totalRepayable: 'KES 592,800', eligibility: 'Good (680+)' },
                { lender: 'Equity Bank', interestRate: '14.0%', term: '12-60 months', monthlyPayment: 'KES 12,500', totalRepayable: 'KES 600,000', eligibility: 'Fair (620+)' },
                { lender: 'Co-operative Bank', interestRate: '14.5%', term: '12-72 months', monthlyPayment: 'KES 12,720', totalRepayable: 'KES 610,560', eligibility: 'Fair (600+)' },
                { lender: 'NCBA Bank', interestRate: '13.0%', term: '12-36 months', monthlyPayment: 'KES 12,200', totalRepayable: 'KES 585,600', eligibility: 'Good (650+)' },
                { lender: 'M-Shwari', interestRate: '7.5% (monthly)', term: '1 month', monthlyPayment: 'KES 5,375', totalRepayable: 'KES 5,375', eligibility: 'Any' }
            ],
            business: [
                { lender: 'KCB Bank', interestRate: '12.5%', term: '12-84 months', monthlyPayment: 'KES 22,900', totalRepayable: 'KES 1,922,760', eligibility: 'Business 2+ yrs' },
                { lender: 'Equity Bank', interestRate: '13.0%', term: '12-60 months', monthlyPayment: 'KES 23,200', totalRepayable: 'KES 1,392,000', eligibility: 'Business 1+ yr' },
                { lender: 'ABSA Bank', interestRate: '12.9%', term: '12-72 months', monthlyPayment: 'KES 23,150', totalRepayable: 'KES 1,666,800', eligibility: 'Business 1.5+ yrs' },
                { lender: 'DTB', interestRate: '13.5%', term: '12-60 months', monthlyPayment: 'KES 23,450', totalRepayable: 'KES 1,407,000', eligibility: 'Business 2+ yrs' },
                { lender: 'Stanbic Bank', interestRate: '12.8%', term: '12-84 months', monthlyPayment: 'KES 22,850', totalRepayable: 'KES 1,919,400', eligibility: 'Business 1+ yr' }
            ],
            mortgage: [
                { lender: 'KCB Bank', interestRate: '11.5%', term: '5-25 years', monthlyPayment: 'KES 73,500', totalRepayable: 'KES 22,050,000', eligibility: 'Excellent (720+)' },
                { lender: 'Housing Finance', interestRate: '12.0%', term: '5-20 years', monthlyPayment: 'KES 75,200', totalRepayable: 'KES 18,048,000', eligibility: 'Good (680+)' },
                { lender: 'Stanbic Bank', interestRate: '11.8%', term: '5-25 years', monthlyPayment: 'KES 74,400', totalRepayable: 'KES 22,320,000', eligibility: 'Good (690+)' },
                { lender: 'NCBA Bank', interestRate: '12.3%', term: '5-20 years', monthlyPayment: 'KES 75,900', totalRepayable: 'KES 18,216,000', eligibility: 'Good (670+)' },
                { lender: 'ABSA Bank', interestRate: '11.7%', term: '5-25 years', monthlyPayment: 'KES 74,150', totalRepayable: 'KES 22,245,000', eligibility: 'Good (680+)' }
            ],
            education: [
                { lender: 'HELB', interestRate: '4.0%', term: '1-15 years', monthlyPayment: 'KES 2,200', totalRepayable: 'KES 396,000', eligibility: 'Enrolled Student' },
                { lender: 'KCB Bank', interestRate: '12.0%', term: '1-5 years', monthlyPayment: 'KES 5,200', totalRepayable: 'KES 312,000', eligibility: 'Any' },
                { lender: 'Equity Bank', interestRate: '13.0%', term: '1-6 years', monthlyPayment: 'KES 5,400', totalRepayable: 'KES 388,800', eligibility: 'Any' },
                { lender: 'Co-operative Bank', interestRate: '12.5%', term: '1-5 years', monthlyPayment: 'KES 5,300', totalRepayable: 'KES 318,000', eligibility: 'Any' },
                { lender: 'Wings to Fly', interestRate: '0.0%', term: 'Varies', monthlyPayment: 'N/A', totalRepayable: 'Scholarship', eligibility: 'Needs-based' }
            ],
            emergency: [
                { lender: 'M-Shwari', interestRate: '7.5% (monthly)', term: '1 month', monthlyPayment: 'KES 5,375', totalRepayable: 'KES 5,375', eligibility: 'Any' },
                { lender: 'Tala', interestRate: '15.0% (monthly)', term: '1 month', monthlyPayment: 'KES 5,750', totalRepayable: 'KES 5,750', eligibility: 'Any' },
                { lender: 'Branch', interestRate: '17.5% (monthly)', term: '1 month', monthlyPayment: 'KES 5,875', totalRepayable: 'KES 5,875', eligibility: 'Any' },
                { lender: 'KCB M-Pesa', interestRate: '8.64% (monthly)', term: '1 month', monthlyPayment: 'KES 5,432', totalRepayable: 'KES 5,432', eligibility: 'Any' },
                { lender: 'Zenka', interestRate: '20.0% (monthly)', term: '1 month', monthlyPayment: 'KES 6,000', totalRepayable: 'KES 6,000', eligibility: 'Any' }
            ]
        };
        
        return loanData[category] || loanData.personal;
    }
    
    // Form submission for alert preferences
    function saveAlertPreferences(e) {
        e.preventDefault();
        
        // In a real application, this would send data to the server
        // For demo purposes, show a success message
        alert('Alert preferences saved successfully! In a production environment, these settings would be saved to your profile.');
    }
    
    // Update interest rates
    function updateRates() {
        // Simulate updating rates with loading indicator
        const updateRatesBtn = document.getElementById('updateRates');
        if (!updateRatesBtn) return;
        
        const originalText = updateRatesBtn.innerHTML;
        updateRatesBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        updateRatesBtn.disabled = true;
        
        // Simulate network request
        setTimeout(() => {
            updateRatesBtn.innerHTML = '<i class="fas fa-check"></i> Updated!';
            
            // Refresh loan table data with "updated" rates
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) {
                updateLoanTable(activeTab.dataset.category);
            }
            
            // Reset button after delay
            setTimeout(() => {
                updateRatesBtn.innerHTML = originalText;
                updateRatesBtn.disabled = false;
            }, 2000);
        }, 1500);
    }
    
    // Refresh credit score function
    function refreshCreditScore() {
        // Simulate refreshing credit score with loading indicator
        const refreshScoreBtn = document.getElementById('refreshScore');
        if (!refreshScoreBtn) return;
        
        const originalText = refreshScoreBtn.innerHTML;
        refreshScoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        refreshScoreBtn.disabled = true;
        
        // Simulate network request
        setTimeout(() => {
            // Update score with random +/- 5 points change
            const scoreValueElement = document.querySelector('.score-value');
            if (scoreValueElement) {
                const currentScore = parseInt(scoreValueElement.textContent);
                const change = Math.floor(Math.random() * 11) - 5; // Random number between -5 and +5
                const newScore = currentScore + change;
                
                scoreValueElement.textContent = newScore;
                
                // Update score updated time
                const scoreUpdatedElement = document.querySelector('.score-updated p');
                if (scoreUpdatedElement) {
                    const now = new Date();
                    scoreUpdatedElement.textContent = `Last updated: ${now.toLocaleDateString()}`;
                }
                
                // Show a notification
                alert(`Credit score refreshed! Your score ${change >= 0 ? 'increased' : 'decreased'} by ${Math.abs(change)} points.`);
            }
            
            // Reset button
            refreshScoreBtn.innerHTML = originalText;
            refreshScoreBtn.disabled = false;
        }, 2000);
    }
    
    // Navigation function
    function navigateBack() {
        // In a real application, this would navigate back
        // For demo purposes, show an alert
        alert('In a production environment, this would navigate back to the previous page.');
    }
    
    // Refresh all page data
    function refreshPageData() {
        // Simulate refreshing all page data
        const refreshBtn = document.getElementById('refreshData');
        if (!refreshBtn) return;
        
        const originalText = refreshBtn.innerHTML;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        refreshBtn.disabled = true;
        
        // Simulate network request
        setTimeout(() => {
            refreshBtn.innerHTML = '<i class="fas fa-check"></i> Refreshed!';
            
            // Reset button after delay
            setTimeout(() => {
                refreshBtn.innerHTML = originalText;
                refreshBtn.disabled = false;
                
                // Show notification
                alert('All data has been refreshed with the latest information.');
            }, 1000);
        }, 2000);
    }
    
    // View financial reports function
    function viewFinancialReports() {
        // In a real application, this would navigate to reports
        // For demo purposes, show an alert
        alert('In a production environment, this would navigate to your personalized financial reports and analytics dashboard.');
    }
    
    // Initialize the first loan tab
    updateLoanTable('personal');
});