document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const goalForm = document.getElementById('goalForm');
    const resetFormBtn = document.getElementById('resetFormBtn');
    const projectionContainer = document.getElementById('projectionContainer');
    const noDataMessage = document.querySelector('.no-data-message');
    const projectionDetails = document.querySelector('.projection-details');
    const timeToGoalElement = document.getElementById('timeToGoal');
    const requiredDepositElement = document.getElementById('requiredDeposit');
    const saveProjectionBtn = document.getElementById('saveProjectionBtn');
    const exportGoalsBtn = document.getElementById('exportGoalsBtn');
    const chatbotToggle = document.querySelector('.chatbot-toggle');
    const addFundsModal = document.getElementById('addFundsModal');
    const addFundsForm = document.getElementById('addFundsForm');
    const useTemplateButtons = document.querySelectorAll('.use-template');
    const themeToggle = document.querySelector('.theme-toggle');
    
    // Chart instance
    let projectionChart = null;

    // Set default target date to 1 year from now
    const defaultDate = new Date();
    defaultDate.setFullYear(defaultDate.getFullYear() + 1);
    document.getElementById('targetDate').valueAsDate = defaultDate;

    // Event Listeners
    goalForm.addEventListener('submit', handleGoalFormSubmit);
    resetFormBtn.addEventListener('click', resetForm);
    saveProjectionBtn.addEventListener('click', saveGoal);
    exportGoalsBtn.addEventListener('click', exportGoals);
    chatbotToggle.addEventListener('click', toggleChatbot);
    themeToggle.addEventListener('click', toggleTheme);
    
    // Add funds modal events
    const addFundsBtns = document.querySelectorAll('.btn-icon[title="Add funds"]');
    addFundsBtns.forEach(btn => {
        btn.addEventListener('click', showAddFundsModal);
    });
    
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    document.querySelector('.cancel-modal').addEventListener('click', closeModal);
    addFundsForm.addEventListener('submit', handleAddFunds);

    // Template buttons
    useTemplateButtons.forEach(button => {
        button.addEventListener('click', applyTemplate);
    });

    // Real-time calculation as user types
    ['goalAmount', 'initialDeposit', 'targetDate', 'depositFrequency'].forEach(id => {
        document.getElementById(id).addEventListener('input', calculateProjection);
    });

    // Functions
    function handleGoalFormSubmit(e) {
        e.preventDefault();
        calculateProjection();
        
        // Scroll to projection if needed
        projectionContainer.scrollIntoView({ behavior: 'smooth' });
    }

    function calculateProjection() {
        const goalAmount = parseFloat(document.getElementById('goalAmount').value) || 0;
        const initialDeposit = parseFloat(document.getElementById('initialDeposit').value) || 0;
        const targetDateValue = document.getElementById('targetDate').value;
        const depositFrequency = document.getElementById('depositFrequency').value;
        
        // Validate inputs
        if (goalAmount <= 0 || !targetDateValue) {
            hideProjection();
            return;
        }

        // Calculate time difference
        const currentDate = new Date();
        const targetDate = new Date(targetDateValue);
        
        if (targetDate <= currentDate) {
            alert('Target date must be in the future');
            return;
        }

        // Remaining amount to save
        const remainingAmount = goalAmount - initialDeposit;
        
        // Time calculations
        const timeDiff = targetDate.getTime() - currentDate.getTime();
        const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));
        const monthsDiff = Math.ceil(daysDiff / 30);
        const weeksDiff = Math.ceil(daysDiff / 7);
        
        // Calculate required deposit based on frequency
        let requiredDeposit = 0;
        let depositPeriods = 0;
        let timeUnit = '';
        
        switch(depositFrequency) {
            case 'weekly':
                depositPeriods = weeksDiff;
                timeUnit = 'weeks';
                break;
            case 'biweekly':
                depositPeriods = Math.ceil(weeksDiff / 2);
                timeUnit = 'bi-weekly periods';
                break;
            case 'monthly':
                depositPeriods = monthsDiff;
                timeUnit = 'months';
                break;
            case 'quarterly':
                depositPeriods = Math.ceil(monthsDiff / 3);
                timeUnit = 'quarters';
                break;
        }
        
        requiredDeposit = remainingAmount / depositPeriods;
        
        // Show projection
        timeToGoalElement.textContent = `${depositPeriods} ${timeUnit} (${daysDiff} days)`;
        requiredDepositElement.textContent = `KES ${requiredDeposit.toFixed(2)} per ${depositFrequency.slice(0, -2)}${depositFrequency.endsWith('ly') ? 'ly' : ''}`;
        
        showProjection();
        
        // Create/update projection chart
        createProjectionChart(initialDeposit, requiredDeposit, depositPeriods, depositFrequency);
    }

    function createProjectionChart(initialDeposit, requiredDeposit, periods, frequency) {
        // Destroy previous chart if exists
        if (projectionChart) {
            projectionChart.destroy();
        }
        
        // Create data points for the chart
        const labels = [];
        const projectedData = [];
        
        // Add initial point
        labels.push('Start');
        projectedData.push(initialDeposit);
        
        // Generate time labels based on frequency
        let timeLabel = '';
        switch(frequency) {
            case 'weekly':
                timeLabel = 'Week';
                break;
            case 'biweekly':
                timeLabel = 'Period';
                break;
            case 'monthly':
                timeLabel = 'Month';
                break;
            case 'quarterly':
                timeLabel = 'Quarter';
                break;
        }
        
        // Generate future projections
        for (let i = 1; i <= periods; i++) {
            labels.push(`${timeLabel} ${i}`);
            projectedData.push(initialDeposit + (requiredDeposit * i));
        }
        
        // Get chart context
        const ctx = document.getElementById('projectionChart').getContext('2d');
        
        // Create chart
        projectionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Projected Savings',
                    data: projectedData,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'KES ' + value.toLocaleString();
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'KES ' + context.raw.toFixed(2);
                            }
                        }
                    }
                }
            }
        });
    }

    function showProjection() {
        noDataMessage.classList.add('hidden');
        projectionDetails.classList.remove('hidden');
    }

    function hideProjection() {
        noDataMessage.classList.remove('hidden');
        projectionDetails.classList.add('hidden');
    }

    function resetForm() {
        goalForm.reset();
        
        // Reset to default date (1 year from now)
        document.getElementById('targetDate').valueAsDate = defaultDate;
        
        hideProjection();
    }

    function saveGoal() {
        const goalName = document.getElementById('goalName').value;
        const goalAmount = parseFloat(document.getElementById('goalAmount').value);
        const initialDeposit = parseFloat(document.getElementById('initialDeposit').value) || 0;
        const targetDate = document.getElementById('targetDate').value;
        const goalCategory = document.getElementById('goalCategory').value;
        
        if (!goalName || !goalAmount || !targetDate || !goalCategory) {
            alert('Please fill in all required fields');
            return;
        }
        
        // In a real application, this would save to a database or localStorage
        // For now, we'll just show a success message
        alert(`Goal "${goalName}" has been saved successfully!`);
        
        // In a real application, we would:
        // 1. Save the goal data
        // 2. Refresh the goals table
        // 3. Reset the form
        
        // For this demo, we'll just reset the form
        resetForm();
        
        // Scroll to goals table
        document.querySelector('.current-goals').scrollIntoView({ behavior: 'smooth' });
    }

    function applyTemplate(e) {
        const goalName = e.target.getAttribute('data-goal');
        const category = e.target.getAttribute('data-category');
        
        // Set form values based on template
        document.getElementById('goalName').value = goalName;
        document.getElementById('goalCategory').value = category;
        
        // Set default amounts based on category
        switch(category) {
            case 'emergency':
                document.getElementById('goalAmount').value = 100000;
                document.getElementById('initialDeposit').value = 10000;
                break;
            case 'vacation':
                document.getElementById('goalAmount').value = 50000;
                document.getElementById('initialDeposit').value = 5000;
                break;
            case 'education':
                document.getElementById('goalAmount').value = 150000;
                document.getElementById('initialDeposit').value = 15000;
                break;
            default:
                document.getElementById('goalAmount').value = 50000;
                document.getElementById('initialDeposit').value = 5000;
        }
        
        // Calculate projection with new values
        calculateProjection();
        
        // Smooth scroll to the form
        goalForm.scrollIntoView({ behavior: 'smooth' });
    }

    function showAddFundsModal(e) {
        // In a real application, we would get the goal data from the clicked row
        // For now, we'll use the parent row to get goal info
        const row = e.target.closest('tr');
        const goalName = row.cells[0].textContent;
        const progressText = row.querySelector('.progress-text').textContent;
        const progressValue = parseInt(progressText);
        
        // Set values in the modal
        document.getElementById('goalTitle').value = goalName;
        document.getElementById('currentProgressText').textContent = progressText;
        document.getElementById('currentProgressBar').style.width = progressText;
        
        // Show modal
        addFundsModal.style.display = 'flex';
    }

    function closeModal() {
        addFundsModal.style.display = 'none';
        addFundsForm.reset();
    }

    function handleAddFunds(e) {
        e.preventDefault();
        
        const amount = parseFloat(document.getElementById('addAmount').value);
        const source = document.getElementById('fundSource').value;
        const goalName = document.getElementById('goalTitle').value;
        
        if (!amount || amount <= 0) {
            alert('Please enter a valid amount');
            return;
        }
        
        // In a real application, this would update the database
        alert(`Successfully added KES ${amount.toFixed(2)} to "${goalName}" from ${source}!`);
        
        // Close modal
        closeModal();
        
        // In a real app, we would refresh the goals table here
    }

    function exportGoals() {
        // In a real application, this would generate a CSV or PDF
        alert('Your goals have been exported!');
    }

    function toggleChatbot() {
        // In a real application, this would show/hide a chatbot interface
        alert('Chatbot functionality would be implemented here');
    }

    function toggleTheme() {
        document.body.classList.toggle('dark-mode');
        const icon = themeToggle.querySelector('i');
        
        if (document.body.classList.contains('dark-mode')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
        }
    }
});