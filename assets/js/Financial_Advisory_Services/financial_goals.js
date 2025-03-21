import authService from '../services/authService.js';

document.addEventListener('DOMContentLoaded', async () => {
  // ====================================
  // Authentication Check
  // ====================================
  if (!authService.isAuthenticated()) {
    window.location.href = '/Authentication/login.html?redirect=/Financial_Advisory_Services/financial_goals.html';
    return;
  }
  
  // ====================================
  // DOM Element References
  // ====================================
  // Core Elements
  const goalsContainer = document.getElementById('goalsContainer');
  const goalForm = document.getElementById('addGoalForm');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const errorMessage = document.getElementById('errorMessage');
  const addGoalButton = document.getElementById('addGoalButton');
  const goalModal = document.getElementById('goalModal');
  const closeModalButton = document.getElementById('closeModal');
  const categorySelect = document.getElementById('goalCategory');
  
  // UI Elements
  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const themeToggle = document.getElementById('themeToggle');
  const notificationBtn = document.getElementById('notificationBtn');
  const notificationPanel = document.getElementById('notificationPanel');
  const searchInput = document.getElementById('searchInput');
  const filterButtons = document.querySelectorAll('.filter-btn[data-filter]');
  const currencySelect = document.getElementById('currencySelect');
  const vizButtons = document.querySelectorAll('.viz-btn');
  const chartView = document.getElementById('chartView');
  const timelineView = document.getElementById('timelineView');
  const setupAutoBtn = document.getElementById('setupAutoBtn');
  const autoContributionModal = document.getElementById('autoContributionModal');
  const closeAutoModal = document.getElementById('closeAutoModal');
  const cancelAutoSetup = document.getElementById('cancelAutoSetup');
  const sortDropdown = document.querySelector('.sort-dropdown');
  const currentSortOption = document.getElementById('currentSortOption');
  const sortOptions = document.querySelectorAll('.sort-dropdown-content a');
  const toggleInputs = document.querySelectorAll('.toggle-input');
  const filterDropdown = document.querySelector('.filter-dropdown');
  const filterDropdownContent = document.querySelector('.filter-dropdown-content');
  const markAllReadBtn = document.querySelector('.mark-all-read-btn');
  const markReadBtns = document.querySelectorAll('.mark-read-btn');
  
  // Form-related Elements
  const frequency = document.getElementById('frequency');
  const weeklyOptions = document.getElementById('weeklyOptions');
  const monthlyOptions = document.getElementById('monthlyOptions');
  const endCondition = document.getElementById('endCondition');
  const endDateContainer = document.getElementById('endDateContainer');
  
  // ====================================
  // State Management
  // ====================================
  let state = {
    goals: [],
    filteredGoals: [],
    categories: [],
    currentFilter: 'all',
    currentSort: 'deadline',
    currentView: 'list',
    theme: localStorage.getItem('pesaguru-theme') || 'light',
    charts: {
      goalsPieChart: null,
      goalsProgressChart: null
    }
  };
  
  // ====================================
  // Initialization
  // ====================================
  async function init() {
    try {
      // Initialize theme
      initTheme();
      
      // Load goals data
      await loadGoalCategories();
      await loadGoals();
      
      // Initialize charts if elements exist
      if (document.getElementById('goalsPieChart') && document.getElementById('goalsProgressChart')) {
        initCharts();
      }
      
      // Set up UI event listeners
      setupEventListeners();
      
      // Update notification count if applicable
      if (notificationBtn) {
        updateNotificationCount();
      }
    } catch (error) {
      console.error('Initialization error:', error);
      showToast('Failed to initialize application. Please refresh the page.', 'error');
    }
  }
  
  // ====================================
  // Goal Management Functions
  // ====================================
  async function loadGoalCategories() {
    try {
      const categories = await financialGoalsService.getGoalCategories();
      state.categories = categories;
      
      // Populate category dropdown
      if (categorySelect) {
        categorySelect.innerHTML = '';
        
        categories.forEach(category => {
          const option = document.createElement('option');
          option.value = category.id;
          option.textContent = category.name;
          categorySelect.appendChild(option);
        });
      }
    } catch (error) {
      console.error('Error loading goal categories:', error);
      showToast('Failed to load goal categories', 'error');
    }
  }
  
  async function loadGoals() {
    try {
      // Show loading indicator
      if (loadingIndicator) loadingIndicator.style.display = 'block';
      if (errorMessage) errorMessage.style.display = 'none';
      if (goalsContainer) goalsContainer.innerHTML = '';
      
      const goals = await financialGoalsService.getGoals();
      state.goals = goals;
      state.filteredGoals = goals;
      
      if (goals.length === 0) {
        renderEmptyState();
        return;
      }
      
      // Render goal cards
      renderGoals(goals);
    } catch (error) {
      console.error('Error loading goals:', error);
      if (errorMessage) {
        errorMessage.textContent = 'Failed to load your financial goals. Please try again.';
        errorMessage.style.display = 'block';
      }
    } finally {
      if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
  }
  
  function renderEmptyState() {
    if (!goalsContainer) return;
    
    goalsContainer.innerHTML = `
      <div class="empty-state">
        <img src="/assets/images/illustrations/empty-goals.svg" alt="No goals" />
        <h3>You don't have any financial goals yet</h3>
        <p>Set your first financial goal to start planning your future.</p>
        <button class="btn btn-primary" id="emptyStateAddGoal">
          <i class="fa fa-plus"></i> Add Your First Goal
        </button>
      </div>
    `;
    
    // Add event listener to empty state button
    const emptyStateButton = document.getElementById('emptyStateAddGoal');
    if (emptyStateButton) {
      emptyStateButton.addEventListener('click', () => {
        if (addGoalButton) addGoalButton.click();
      });
    }
  }
  
  function renderGoals(goals) {
    if (!goalsContainer) return;
    
    // Clear container
    goalsContainer.innerHTML = '';
    
    // Render each goal card
    goals.forEach(goal => {
      renderGoalCard(goal);
    });
    
    // Update charts with new data if they exist
    updateChartsWithGoals(goals);
  }
  
  function renderGoalCard(goal) {
    if (!goalsContainer) return;
    
    // Calculate progress percentage
    const progress = (goal.currentAmount / goal.targetAmount) * 100;
    const daysRemaining = getDaysRemaining(goal.targetDate);
    
    const goalCard = document.createElement('div');
    goalCard.classList.add('goal-card');
    goalCard.dataset.priority = goal.priority.toLowerCase();
    goalCard.dataset.id = goal.id;
    
    goalCard.innerHTML = `
      <div class="goal-header">
        <div class="goal-title">
          <h3>${goal.name}</h3>
          <span class="goal-priority ${getPriorityClass(goal.priority)}">
            ${goal.priority}
          </span>
        </div>
        <div class="goal-actions-top">
          <button class="btn edit-btn" title="Edit Goal">
            <i class="fa fa-edit"></i>
          </button>
          <button class="btn more-btn" title="More Options">
            <i class="fa fa-ellipsis-v"></i>
          </button>
        </div>
      </div>
      
      <div class="goal-amount">
        <span class="current-amount">${formatCurrency(goal.currentAmount)}</span>
        <span class="target-amount">of ${formatCurrency(goal.targetAmount)}</span>
      </div>
      
      <div class="goal-progress">
        <div class="progress-bar">
          <div class="progress-fill" style="width: ${progress.toFixed(0)}%"></div>
        </div>
        <div class="progress-stats">
          <div class="progress-percentage">${progress.toFixed(0)}%</div>
          <p>Complete</p>
        </div>
      </div>
      
      <div class="goal-details">
        <div class="info-item">
          <span class="info-label">Target Date</span>
          <span class="info-value">${formatDate(goal.targetDate)}</span>
        </div>
        <div class="goal-date ${daysRemaining < 30 ? 'urgent' : ''}">
          ${formatDaysRemaining(daysRemaining)}
        </div>
      </div>
      
      <div class="goal-category">
        <i class="${getCategoryIcon(goal.category)}"></i> ${goal.categoryName}
      </div>
      
      <div class="goal-actions">
        <button class="btn btn-sm deposit-btn" data-goal-id="${goal.id}">
          <i class="fa fa-plus-circle"></i> Add Funds
        </button>
        <button class="btn btn-sm adjust-btn" data-goal-id="${goal.id}">
          <i class="fa fa-sliders"></i> Adjust
        </button>
        <button class="btn btn-sm btn-view-plan" data-goal-id="${goal.id}">
          <i class="fa fa-chart-line"></i> View Plan
        </button>
      </div>
    `;
    
    // Add to goals container
    goalsContainer.appendChild(goalCard);
    
    // Add event listeners to buttons
    const depositButton = goalCard.querySelector('.deposit-btn');
    const adjustButton = goalCard.querySelector('.adjust-btn');
    const viewPlanButton = goalCard.querySelector('.btn-view-plan');
    const editButton = goalCard.querySelector('.edit-btn');
    
    if (depositButton) {
      depositButton.addEventListener('click', () => handleAddFunds(goal));
    }
    
    if (viewPlanButton) {
      viewPlanButton.addEventListener('click', () => handleViewPlan(goal));
    }
    
    if (editButton) {
      editButton.addEventListener('click', () => handleEditGoal(goal));
    }
    
    if (adjustButton) {
      adjustButton.addEventListener('click', () => handleAdjustGoal(goal));
    }
  }
  
  // ====================================
  // Event Handlers for Goal Actions
  // ====================================
  async function handleAddFunds(goal) {
    const amount = prompt(`Enter amount to add to "${goal.name}":`, '0');
    if (amount === null) return;
    
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      alert('Please enter a valid positive amount');
      return;
    }
    
    try {
      // Track progress by adding funds
      await financialGoalsService.trackGoalProgress(goal.id, {
        amount: numAmount,
        date: new Date().toISOString().split('T')[0],
        description: 'Manual addition'
      });
      
      // Reload goals
      await loadGoals();
      
      // Show success message
      showToast(`Added ${formatCurrency(numAmount)} to "${goal.name}"`, 'success');
    } catch (error) {
      console.error('Error adding funds:', error);
      showToast('Failed to add funds. Please try again.', 'error');
    }
  }
  
  async function handleEditGoal(goal) {
    // Set form to edit mode
    if (!goalForm) return;
    
    goalForm.dataset.mode = 'edit';
    goalForm.dataset.goalId = goal.id;
    
    // Populate form with goal data
    document.getElementById('goalName').value = goal.name;
    document.getElementById('targetAmount').value = goal.targetAmount;
    document.getElementById('currentAmount').value = goal.currentAmount;
    document.getElementById('targetDate').value = goal.targetDate;
    document.getElementById('goalCategory').value = goal.category;
    document.getElementById('goalPriority').value = goal.priority;
    document.getElementById('goalDescription').value = goal.description;
    
    // Show modal
    openModal(goalModal);
  }
  
  async function handleViewPlan(goal) {
    window.location.href = `/Financial_Advisory_Services/goal_plan.html?goalId=${goal.id}`;
  }
  
  async function handleAdjustGoal(goal) {
    // This function would handle adjusting goal parameters
    // For now, just call the edit function 
    handleEditGoal(goal);
  }
  
  // ====================================
  // Form Submission Handlers
  // ====================================
  async function handleGoalFormSubmit(event) {
    event.preventDefault();
    
    if (!goalForm) return;
    
    // Get form data
    const formData = {
      name: document.getElementById('goalName').value,
      targetAmount: parseFloat(document.getElementById('targetAmount').value),
      currentAmount: parseFloat(document.getElementById('currentAmount').value) || 0,
      targetDate: document.getElementById('targetDate').value,
      category: document.getElementById('goalCategory').value,
      priority: document.getElementById('goalPriority').value,
      description: document.getElementById('goalDescription').value
    };
    
    try {
      // Show loading
      const submitButton = document.getElementById('formSubmitButton');
      const submitSpinner = document.getElementById('formSubmitSpinner');
      
      if (submitButton) submitButton.disabled = true;
      if (submitSpinner) submitSpinner.style.display = 'inline-block';
      
      if (goalForm.dataset.mode === 'create') {
        // Create new goal
        await financialGoalsService.createGoal(formData);
      } else {
        // Update existing goal
        await financialGoalsService.updateGoal(goalForm.dataset.goalId, formData);
      }
      
      // Close modal
      closeModal(goalModal);
      
      // Reload goals
      await loadGoals();
      
      // Show success message
      showToast('Goal saved successfully!', 'success');
    } catch (error) {
      console.error('Error saving goal:', error);
      showToast('Failed to save goal. Please try again.', 'error');
    } finally {
      // Reset loading state
      const submitButton = document.getElementById('formSubmitButton');
      const submitSpinner = document.getElementById('formSubmitSpinner');
      
      if (submitButton) submitButton.disabled = false;
      if (submitSpinner) submitSpinner.style.display = 'none';
    }
  }
  
  async function handleAutoContributionSubmit(e) {
    e.preventDefault();
    
    // Get form values
    const goalSelection = document.getElementById('autoGoal').value;
    const fundingSource = document.getElementById('fundingSource').value;
    const amount = document.getElementById('contributionAmount').value;
    const frequencyValue = document.getElementById('frequency').value;
    const startDate = document.getElementById('startDate').value;
    const endConditionValue = document.getElementById('endCondition').value;
    
    try {
      // In a real application, this would connect to the backend service
      // For now, we'll just show a success message
      showToast('Auto-contribution set up successfully!', 'success');
      
      // Reset form and close modal
      const autoContributionForm = document.getElementById('autoContributionForm');
      if (autoContributionForm) autoContributionForm.reset();
      closeModal(autoContributionModal);
      
      // Reload goals to show the auto-contribution
      await loadGoals();
    } catch (error) {
      console.error('Error setting up auto-contribution:', error);
      showToast('Failed to set up auto-contribution. Please try again.', 'error');
    }
  }
  
  // ====================================
  // UI Control Functions
  // ====================================
  function setupEventListeners() {
    // Goal Management Listeners
    if (addGoalButton) {
      addGoalButton.addEventListener('click', () => {
        if (goalForm) {
          // Reset form
          goalForm.reset();
          goalForm.dataset.mode = 'create';
          goalForm.dataset.goalId = '';
          
          // Set default date to 1 year from now
          const nextYear = new Date();
          nextYear.setFullYear(nextYear.getFullYear() + 1);
          const targetDateInput = document.getElementById('targetDate');
          if (targetDateInput) targetDateInput.valueAsDate = nextYear;
        }
        
        // Show modal
        openModal(goalModal);
      });
    }
    
    if (closeModalButton) {
      closeModalButton.addEventListener('click', () => closeModal(goalModal));
    }
    
    // Close modal when clicking outside
    if (goalModal) {
      window.addEventListener('click', (event) => {
        if (event.target === goalModal) {
          closeModal(goalModal);
        }
      });
    }
    
    // Form submission
    if (goalForm) {
      goalForm.addEventListener('submit', handleGoalFormSubmit);
    }
    
    // Theme Management
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Sidebar Toggle
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', toggleSidebar);
    }
    
    // Search & Filtering
    if (searchInput) {
      searchInput.addEventListener('input', (e) => searchGoals(e.target.value));
    }
    
    if (filterButtons) {
      filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const filter = btn.getAttribute('data-filter');
          if (filter) filterGoals(filter);
        });
      });
    }
    
    // Sorting
    if (sortDropdown) {
      const sortBtn = sortDropdown.querySelector('.sort-btn');
      if (sortBtn) {
        sortBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          const dropdownContent = document.querySelector('.sort-dropdown-content');
          if (dropdownContent) dropdownContent.classList.toggle('active');
        });
      }
      
      if (sortOptions) {
        sortOptions.forEach(option => {
          option.addEventListener('click', (e) => {
            e.preventDefault();
            const sortValue = option.getAttribute('data-sort');
            if (sortValue) sortGoals(sortValue);
            const dropdownContent = document.querySelector('.sort-dropdown-content');
            if (dropdownContent) dropdownContent.classList.remove('active');
          });
        });
      }
    }
    
    // Auto Contribution Modal
    if (setupAutoBtn && autoContributionModal) {
      setupAutoBtn.addEventListener('click', () => openModal(autoContributionModal));
    }
    
    if (closeAutoModal) {
      closeAutoModal.addEventListener('click', () => closeModal(autoContributionModal));
    }
    
    if (cancelAutoSetup) {
      cancelAutoSetup.addEventListener('click', () => closeModal(autoContributionModal));
    }
    
    // Auto Contribution Form
    const autoContributionForm = document.getElementById('autoContributionForm');
    if (autoContributionForm) {
      autoContributionForm.addEventListener('submit', handleAutoContributionSubmit);
    }
    
    // Form Controls
    if (frequency) {
      frequency.addEventListener('change', () => {
        if (frequency.value) handleFrequencyChange(frequency.value);
      });
    }
    
    if (endCondition) {
      endCondition.addEventListener('change', () => {
        if (endCondition.value) handleEndConditionChange(endCondition.value);
      });
    }
    
    // Toggle buttons
    if (toggleInputs) {
      toggleInputs.forEach(checkbox => {
        checkbox.addEventListener('change', () => toggleAutoContributionStatus(checkbox));
      });
    }
    
    // Visualization Toggle
    if (vizButtons) {
      vizButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const vizType = btn.getAttribute('data-viz');
          if (vizType) toggleVisualization(vizType);
        });
      });
    }
    
    // Currency Change
    if (currencySelect) {
      currencySelect.addEventListener('change', () => {
        changeCurrency(currencySelect.value);
        // Refresh UI with new currency
        renderGoals(state.filteredGoals);
      });
    }
    
    // Notification Panel
    if (notificationBtn && notificationPanel) {
      notificationBtn.addEventListener('click', toggleNotificationPanel);
    }
    
    if (markAllReadBtn) {
      markAllReadBtn.addEventListener('click', markAllNotificationsRead);
    }
    
    if (markReadBtns) {
      markReadBtns.forEach(btn => {
        btn.addEventListener('click', () => markNotificationRead(btn));
      });
    }
    
    // Filter Dropdown
    if (filterDropdown && filterDropdownContent) {
      filterDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
        filterDropdownContent.classList.toggle('active');
      });
    }
    
    // Close dropdowns when clicking elsewhere
    document.addEventListener('click', closeAllDropdowns);
  }
  
  function openModal(modal) {
    if (!modal) return;
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }
  
  function closeModal(modal) {
    if (!modal) return;
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
  
  function initTheme() {
    if (state.theme === 'dark') {
      document.body.classList.add('dark-mode');
      if (themeToggle && themeToggle.querySelector('i')) {
        themeToggle.querySelector('i').classList.remove('fa-moon');
        themeToggle.querySelector('i').classList.add('fa-sun');
      }
    }
  }
  
  function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    
    if (state.theme === 'dark') {
      document.body.classList.add('dark-mode');
      if (themeToggle && themeToggle.querySelector('i')) {
        themeToggle.querySelector('i').classList.remove('fa-moon');
        themeToggle.querySelector('i').classList.add('fa-sun');
      }
    } else {
      document.body.classList.remove('dark-mode');
      if (themeToggle && themeToggle.querySelector('i')) {
        themeToggle.querySelector('i').classList.remove('fa-sun');
        themeToggle.querySelector('i').classList.add('fa-moon');
      }
    }
    
    localStorage.setItem('pesaguru-theme', state.theme);
    
    // Recreate charts with updated theme colors if they exist
    if (state.charts.goalsPieChart || state.charts.goalsProgressChart) {
      initCharts();
    }
  }
  
  function toggleSidebar() {
    document.body.classList.toggle('sidebar-collapsed');
  }
  
  function toggleNotificationPanel() {
    if (notificationPanel) {
      notificationPanel.classList.toggle('active');
    }
  }
  
  function markAllNotificationsRead() {
    const unreadNotifications = document.querySelectorAll('.notification-item.unread');
    unreadNotifications.forEach(notification => {
      notification.classList.remove('unread');
    });
    updateNotificationCount();
  }
  
  function markNotificationRead(btn) {
    const notification = btn.closest('.notification-item');
    if (notification) {
      notification.classList.remove('unread');
      updateNotificationCount();
    }
  }
  
  function updateNotificationCount() {
    const unreadCount = document.querySelectorAll('.notification-item.unread').length;
    const badge = document.getElementById('notificationCount');
    
    if (badge) {
      if (unreadCount > 0) {
        badge.textContent = unreadCount;
        badge.style.display = 'flex';
      } else {
        badge.style.display = 'none';
      }
    }
  }
  
  function closeAllDropdowns() {
    document.querySelectorAll('.filter-dropdown-content, .sort-dropdown-content').forEach(dropdown => {
      dropdown.classList.remove('active');
    });
  }
  
  // ====================================
  // Search, Filter and Sort Functions
  // ====================================
  function searchGoals(query) {
    query = query.toLowerCase().trim();
    
    if (query === '') {
      state.filteredGoals = state.goals;
    } else {
      state.filteredGoals = state.goals.filter(goal => 
        goal.name.toLowerCase().includes(query) ||
        goal.description?.toLowerCase().includes(query)
      );
    }
    
    renderGoals(state.filteredGoals);
  }
  
  function filterGoals(filterValue) {
    // Update active filter button if UI elements exist
    if (filterButtons) {
      filterButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-filter') === filterValue) {
          btn.classList.add('active');
        }
      });
    }
    
    state.currentFilter = filterValue;
    
    if (filterValue === 'all') {
      state.filteredGoals = state.goals;
    } else {
      state.filteredGoals = state.goals.filter(goal => 
        goal.priority.toLowerCase() === filterValue
      );
    }
    
    renderGoals(state.filteredGoals);
  }
  
  function sortGoals(sortValue) {
    state.currentSort = sortValue;
    
    // Update current sort option in UI if element exists
    if (currentSortOption) {
      currentSortOption.textContent = sortValue.charAt(0).toUpperCase() + sortValue.slice(1);
    }
    
    let sortedGoals = [...state.filteredGoals];
    
    switch (sortValue) {
      case 'deadline':
        sortedGoals.sort((a, b) => new Date(a.targetDate) - new Date(b.targetDate));
        break;
      case 'priority': {
        const priorityMap = { 'high': 1, 'medium': 2, 'low': 3 };
        sortedGoals.sort((a, b) => 
          priorityMap[a.priority.toLowerCase()] - priorityMap[b.priority.toLowerCase()]
        );
        break;
      }
      case 'progress':
        sortedGoals.sort((a, b) => {
          const progressA = (a.currentAmount / a.targetAmount) * 100;
          const progressB = (b.currentAmount / b.targetAmount) * 100;
          return progressB - progressA; // Higher percentage first
        });
        break;
      case 'amount':
        sortedGoals.sort((a, b) => b.targetAmount - a.targetAmount);
        break;
      case 'name':
        sortedGoals.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }
    
    state.filteredGoals = sortedGoals;
    renderGoals(sortedGoals);
  }
  
  function toggleVisualization(viewType) {
    if (!vizButtons || !chartView || !timelineView) return;
    
    vizButtons.forEach(btn => {
      btn.classList.remove('active');
      if (btn.getAttribute('data-viz') === viewType) {
        btn.classList.add('active');
      }
    });
    
    if (viewType === 'chart') {
      chartView.classList.add('active');
      timelineView.classList.remove('active');
    } else {
      chartView.classList.remove('active');
      timelineView.classList.add('active');
    }
    
    state.currentView = viewType;
  }
  
  function changeCurrency(currency) {
    // This would normally update all currency displays with real exchange rates
    console.log(`Currency changed to ${currency}`);
    
    // Re-render charts with the new currency
    if (state.charts.goalsPieChart || state.charts.goalsProgressChart) {
      initCharts();
    }
  }
  
  function handleFrequencyChange(value) {
    if (!weeklyOptions || !monthlyOptions) return;
    
    weeklyOptions.classList.add('hidden');
    monthlyOptions.classList.add('hidden');
    
    if (value === 'weekly' || value === 'bi-weekly') {
      weeklyOptions.classList.remove('hidden');
    } else if (value === 'monthly' || value === 'quarterly') {
      monthlyOptions.classList.remove('hidden');
    }
  }
  
  function handleEndConditionChange(value) {
    if (!endDateContainer) return;
    
    if (value === 'specific-date') {
      endDateContainer.classList.remove('hidden');
    } else {
      endDateContainer.classList.add('hidden');
    }
  }
  
  function toggleAutoContributionStatus(checkbox) {
    const card = checkbox.closest('.auto-contribution-card');
    if (!card) return;
    
    const statusBadge = card.querySelector('.status-badge');
    if (!statusBadge) return;
    
    if (checkbox.checked) {
      card.classList.remove('paused');
      statusBadge.textContent = 'Active';
      statusBadge.classList.remove('paused');
      statusBadge.classList.add('active');
    } else {
      card.classList.add('paused');
      statusBadge.textContent = 'Paused';
      statusBadge.classList.remove('active');
      statusBadge.classList.add('paused');
    }
  }
  
  // ====================================
  // Chart Functions
  // ====================================
  function initCharts() {
    if (!document.getElementById('goalsPieChart') || !document.getElementById('goalsProgressChart')) return;
    
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js not available');
      return;
    }
    
    const isDarkMode = document.body.classList.contains('dark-mode');
    const textColor = isDarkMode ? '#e0e0e0' : '#333333';
    const gridColor = isDarkMode ? '#404040' : '#e0e0e0';
    
    // Get currency symbol
    const currency = currencySelect ? currencySelect.value : 'KES';
    
    // Destroy existing charts if they exist
    if (state.charts.goalsPieChart) state.charts.goalsPieChart.destroy();
    if (state.charts.goalsProgressChart) state.charts.goalsProgressChart.destroy();
    
    // Prepare chart data from goals
    const chartData = prepareChartData();
    
    // Goals allocation pie chart
    const pieCtx = document.getElementById('goalsPieChart').getContext('2d');
    state.charts.goalsPieChart = new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.labels,
        datasets: [{
          data: chartData.targetAmounts,
          backgroundColor: [
            '#ff6b6b', '#6b66ff', '#66b3ff', '#66ffcc', '#b366ff',
            '#ffd866', '#ff66b3', '#66ffd8', '#b3ff66', '#ff8c66'
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: textColor,
              font: { size: 12 }
            }
          },
          title: {
            display: true,
            text: 'Goal Allocation',
            color: textColor,
            font: { size: 16, weight: 'bold' }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.label || '';
                if (label) label += ': ';
                const value = context.parsed;
                label += `${currency} ${value.toLocaleString()}`;
                return label;
              }
            }
          }
        }
      }
    });
    
    // Goals progress bar chart
    const progressCtx = document.getElementById('goalsProgressChart').getContext('2d');
    state.charts.goalsProgressChart = new Chart(progressCtx, {
      type: 'bar',
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: 'Current',
            data: chartData.currentAmounts,
            backgroundColor: '#0066cc',
            borderWidth: 0
          },
          {
            label: 'Target',
            data: chartData.targetAmounts,
            backgroundColor: '#cccccc',
            borderWidth: 0
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: false,
            grid: { color: gridColor },
            ticks: {
              color: textColor,
              callback: function(value) {
                return currency + ' ' + value.toLocaleString();
              }
            }
          },
          y: {
            stacked: false,
            grid: { display: false },
            ticks: { color: textColor }
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: textColor,
              font: { size: 12 }
            }
          },
          title: {
            display: true,
            text: 'Goal Progress',
            color: textColor,
            font: { size: 16, weight: 'bold' }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) label += ': ';
                const value = context.parsed.x;
                label += `${currency} ${value.toLocaleString()}`;
                return label;
              }
            }
          }
        }
      }
    });
  }
  
  function prepareChartData() {
    // Use filtered goals for chart data
    const goals = state.filteredGoals;
    
    return {
      labels: goals.map(goal => goal.name),
      currentAmounts: goals.map(goal => goal.currentAmount),
      targetAmounts: goals.map(goal => goal.targetAmount),
      categories: goals.map(goal => goal.categoryName),
      progress: goals.map(goal => (goal.currentAmount / goal.targetAmount) * 100)
    };
  }
  
  function updateChartsWithGoals(goals) {
    if (!state.charts.goalsPieChart || !state.charts.goalsProgressChart) return;
    
    const chartData = prepareChartData();
    
    state.charts.goalsPieChart.data.labels = chartData.labels;
    state.charts.goalsPieChart.data.datasets[0].data = chartData.targetAmounts;
    state.charts.goalsPieChart.update();
    
    state.charts.goalsProgressChart.data.labels = chartData.labels;
    state.charts.goalsProgressChart.data.datasets[0].data = chartData.currentAmounts;
    state.charts.goalsProgressChart.data.datasets[1].data = chartData.targetAmounts;
    state.charts.goalsProgressChart.update();
  }
  
  // ====================================
  // Helper Functions
  // ====================================
  function getDaysRemaining(targetDate) {
    const target = new Date(targetDate);
    const today = new Date();
    const diffTime = target.getTime() - today.getTime();
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }
  
  function formatDaysRemaining(days) {
    if (days < 0) {
      return 'Overdue';
    } else if (days === 0) {
      return 'Due today';
    } else if (days === 1) {
      return 'Due tomorrow';
    } else if (days < 30) {
      return `${days} days left`;
    } else {
      const months = Math.floor(days / 30);
      return `${months} ${months === 1 ? 'month' : 'months'} left`;
    }
  }
  
  function getPriorityClass(priority) {
    switch (priority.toLowerCase()) {
      case 'high':
      case 'essential':
        return 'priority-high';
      case 'medium':
      case 'important':
        return 'priority-medium';
      case 'low':
      case 'optional':
        return 'priority-low';
      default:
        return '';
    }
  }
  
  function getCategoryIcon(category) {
    // Map category IDs to Font Awesome icons
    const categoryIcons = {
      1: 'fa fa-home', // Home
      2: 'fa fa-car', // Vehicle
      3: 'fa fa-graduation-cap', // Education
      4: 'fa fa-plane', // Travel
      5: 'fa fa-briefcase', // Retirement
      6: 'fa fa-heartbeat', // Health
      7: 'fa fa-gift', // Major Purchase
      8: 'fa fa-piggy-bank', // General Savings
      9: 'fa fa-hand-holding-usd' // Debt Repayment
    };
    
    return categoryIcons[category] || 'fa fa-target';
  }
  
  function formatCurrency(value) {
    const currency = currencySelect ? currencySelect.value : 'KES';
    
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-KE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.classList.add('toast', `toast-${type}`);
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);
    
    // Remove toast after delay
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 3000);
  }
  
  // Initialize the application
  init();
});