// assets/js/market-data/nse-stocks.js
import authService from '../services/authService.js';
import apiClient from '../apiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  // ===============================
  // State and Configuration
  // ===============================
  let state = {
    theme: localStorage.getItem('theme') || 'light',
    currentTab: 'all-stocks',
    currentView: 'cards',
    countdownValue: 30,
    countdownInterval: null,
    watchlist: JSON.parse(localStorage.getItem('watchlist')) || [],
    stocksData: []
  };

  // Check authentication for personalized features
  const isAuthenticated = authService.isAuthenticated();
  
  // ===============================
  // DOM Element References
  // ===============================
  const stocksTable = document.getElementById('stocksTable');
  const stocksTableBody = document.getElementById('stocksTableBody');
  const stocksGrid = document.querySelector('.stocks-grid');
  const searchInput = document.getElementById('searchStocks');
  const filterSelect = document.getElementById('filterStocks');
  const sortSelect = document.getElementById('sort-by');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const errorMessage = document.getElementById('errorMessage');
  const refreshButton = document.getElementById('refreshButton');
  const refreshCountdown = document.getElementById('refresh-countdown');
  const themeToggle = document.getElementById('theme-toggle');
  const viewButtons = document.querySelectorAll('.view-btn');
  const tabButtons = document.querySelectorAll('.tab-btn');
  const watchlistToggle = document.getElementById('watchlist-toggle');
  const watchlistSidebar = document.getElementById('watchlist-sidebar');
  const stockDetailModal = document.getElementById('stock-detail-modal');
  const closeModal = document.querySelector('.close-modal');
  const closeSidebar = document.querySelector('.close-sidebar');
  
  // ===============================
  // Initialization
  // ===============================
  function initializePage() {
    // Initialize theme
    document.documentElement.setAttribute('data-theme', state.theme);
    updateThemeToggleIcons();

    // Initialize countdown
    startCountdown();

    // Load stocks data
    loadStocksData();

    // Initialize charts if we have ApexCharts available
    if (typeof ApexCharts !== 'undefined') {
      initializeCharts();
    }

    // Initialize watchlist
    updateWatchlistUI();
    
    // Set up event listeners
    setupEventListeners();
  }
  
  // ===============================
  // Data Loading and Refresh
  // ===============================
  async function loadStocksData() {
    try {
      // Show loading indicator
      if (loadingIndicator) loadingIndicator.style.display = 'block';
      if (errorMessage) errorMessage.style.display = 'none';
      
      // Get stocks data
      const data = await marketDataService.getNseStocks();
      state.stocksData = data.stocks;
      
      // Render stocks table and cards
      renderStocksTable(state.stocksData);
      renderStocksGrid(state.stocksData);
      
      // Update last refreshed time
      updateLastRefreshedTime();
    } catch (error) {
      console.error('Error loading stocks data:', error);
      if (errorMessage) {
        errorMessage.textContent = 'Failed to load stocks data. Please try again.';
        errorMessage.style.display = 'block';
      }
    } finally {
      // Hide loading indicator
      if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
  }
  
  function startCountdown() {
    if (!refreshCountdown) return;
    
    state.countdownValue = 30;
    refreshCountdown.textContent = state.countdownValue;
    
    clearInterval(state.countdownInterval);
    
    state.countdownInterval = setInterval(function() {
      state.countdownValue--;
      refreshCountdown.textContent = state.countdownValue;
      
      if (state.countdownValue <= 0) {
        refreshStocksData();
      }
    }, 1000);
  }
  
  function refreshStocksData() {
    // Add a loading indicator to refresh button
    if (refreshButton) {
      refreshButton.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
    }
    
    // Load new data
    loadStocksData().then(() => {
      // Reset refresh button and countdown
      if (refreshButton) {
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
      }
      startCountdown();
    });
  }
  
  function updateLastRefreshedTime() {
    const lastUpdatedElement = document.getElementById('lastUpdatedTime');
    if (lastUpdatedElement) {
      const now = new Date();
      const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      lastUpdatedElement.textContent = timeString;
    }
  }
  
  // ===============================
  // Stock Rendering Functions
  // ===============================
  function renderStocksTable(stocks) {
    if (!stocksTableBody) return;
    
    // Clear existing rows
    stocksTableBody.innerHTML = '';
    
    if (stocks.length === 0) {
      stocksTableBody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center">No stocks found</td>
        </tr>
      `;
      return;
    }
    
    // Add rows for each stock
    stocks.forEach(stock => {
      const row = document.createElement('tr');
      row.dataset.symbol = stock.symbol;
      
      // Calculate price change percentage
      const changePercent = ((stock.currentPrice - stock.previousClose) / stock.previousClose) * 100;
      const isPositive = changePercent >= 0;
      
      row.innerHTML = `
        <td>
          <span class="watchlist-icon ${isInWatchlist(stock.symbol) ? 'active fas' : 'far'} fa-star" 
                title="${isInWatchlist(stock.symbol) ? 'Remove from watchlist' : 'Add to watchlist'}"></span>
        </td>
        <td>${stock.symbol}</td>
        <td>
          <a href="stock-details.html?symbol=${stock.symbol}" class="stock-name">
            ${stock.companyName}
          </a>
        </td>
        <td>${stock.currentPrice.toFixed(2)}</td>
        <td class="${isPositive ? 'up' : 'down'}">
          ${isPositive ? '+' : ''}${(stock.currentPrice - stock.previousClose).toFixed(2)}
        </td>
        <td class="${isPositive ? 'up' : 'down'}">
          ${isPositive ? '+' : ''}${changePercent.toFixed(2)}%
        </td>
        <td>${stock.volume.toLocaleString()}</td>
        <td>
          <button class="view-details-btn" data-symbol="${stock.symbol}">
            Details
          </button>
        </td>
      `;
      
      stocksTableBody.appendChild(row);
    });
    
    // Add event listeners to buttons and icons
    addTableEventListeners();
  }
  
  function renderStocksGrid(stocks) {
    if (!stocksGrid) return;
    
    // Clear existing cards
    stocksGrid.innerHTML = '';
    
    if (stocks.length === 0) {
      stocksGrid.innerHTML = `
        <div class="empty-state">
          <i class="fas fa-search"></i>
          <p>No stocks found</p>
        </div>
      `;
      return;
    }
    
    // Add card for each stock
    stocks.forEach(stock => {
      const changePercent = ((stock.currentPrice - stock.previousClose) / stock.previousClose) * 100;
      const isPositive = changePercent >= 0;
      
      const card = document.createElement('div');
      card.className = 'stock-card';
      card.dataset.symbol = stock.symbol;
      
      card.innerHTML = `
        <div class="card-header">
          <div class="stock-info">
            <h3 class="stock-symbol">${stock.symbol}</h3>
            <p class="stock-name">${stock.companyName}</p>
          </div>
          <button class="watchlist-btn ${isInWatchlist(stock.symbol) ? 'active' : ''}" 
                  title="${isInWatchlist(stock.symbol) ? 'Remove from watchlist' : 'Add to watchlist'}">
            <i class="${isInWatchlist(stock.symbol) ? 'fas' : 'far'} fa-star"></i>
          </button>
        </div>
        
        <div class="card-body">
          <div class="price-info">
            <h4 class="stock-price">KES ${stock.currentPrice.toFixed(2)}</h4>
            <p class="stock-change ${isPositive ? 'up' : 'down'}">
              <i class="fas ${isPositive ? 'fa-caret-up' : 'fa-caret-down'}"></i>
              ${isPositive ? '+' : ''}${(stock.currentPrice - stock.previousClose).toFixed(2)} 
              (${isPositive ? '+' : ''}${changePercent.toFixed(2)}%)
            </p>
          </div>
          
          <div class="stock-details">
            <div class="detail-item">
              <span class="label">Volume</span>
              <span class="value">${formatLargeNumber(stock.volume)}</span>
            </div>
            <div class="detail-item">
              <span class="label">P/E</span>
              <span class="value">${stock.pe ? stock.pe.toFixed(2) : 'N/A'}</span>
            </div>
            <div class="detail-item">
              <span class="label">Div Yield</span>
              <span class="value">${stock.dividendYield ? stock.dividendYield.toFixed(2) + '%' : 'N/A'}</span>
            </div>
          </div>
        </div>
        
        <div class="card-footer">
          <button class="view-details-btn" data-symbol="${stock.symbol}">View Details</button>
        </div>
      `;
      
      stocksGrid.appendChild(card);
    });
    
    // Add event listeners to buttons
    addGridEventListeners();
  }
  
  function formatLargeNumber(num) {
    if (num >= 1000000000) {
      return (num / 1000000000).toFixed(1) + 'B';
    } else if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }
  
  // ===============================
  // Event Listeners
  // ===============================
  function setupEventListeners() {
    // Refresh button
    if (refreshButton) {
      refreshButton.addEventListener('click', refreshStocksData);
    }
    
    // Search input
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        filterStocks();
      });
    }
    
    // Filter select
    if (filterSelect) {
      filterSelect.addEventListener('change', () => {
        filterStocks();
      });
    }
    
    // Sort select
    if (sortSelect) {
      sortSelect.addEventListener('change', () => {
        sortStocks(sortSelect.value);
      });
    }
    
    // Theme toggle
    if (themeToggle) {
      themeToggle.addEventListener('click', toggleTheme);
    }
    
    // View switching
    if (viewButtons) {
      viewButtons.forEach(button => {
        button.addEventListener('click', () => {
          const view = button.dataset.view;
          switchView(view);
        });
      });
    }
    
    // Tab switching
    if (tabButtons) {
      tabButtons.forEach(button => {
        button.addEventListener('click', () => {
          const tabId = button.dataset.tab;
          switchTab(tabId);
        });
      });
    }
    
    // Watchlist toggle
    if (watchlistToggle) {
      watchlistToggle.addEventListener('click', () => {
        openWatchlistSidebar();
      });
    }
    
    // Close modal
    if (closeModal) {
      closeModal.addEventListener('click', () => {
        closeStockDetailModal();
      });
    }
    
    // Close sidebar
    if (closeSidebar) {
      closeSidebar.addEventListener('click', () => {
        closeWatchlistSidebar();
      });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
      if (stockDetailModal && e.target === stockDetailModal) {
        closeStockDetailModal();
      }
    });
  }
  
  function addTableEventListeners() {
    // Watchlist icons
    const watchlistIcons = document.querySelectorAll('.watchlist-icon');
    watchlistIcons.forEach(icon => {
      icon.addEventListener('click', (event) => {
        event.stopPropagation();
        const row = icon.closest('tr');
        const symbol = row.dataset.symbol;
        toggleWatchlistItem(symbol);
      });
    });
    
    // View details buttons
    const detailButtons = document.querySelectorAll('.stocks-table .view-details-btn');
    detailButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        const symbol = button.dataset.symbol;
        openStockDetailModal(symbol);
      });
    });
  }
  
  function addGridEventListeners() {
    // Watchlist buttons
    const watchlistButtons = document.querySelectorAll('.stocks-grid .watchlist-btn');
    watchlistButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        const card = button.closest('.stock-card');
        const symbol = card.dataset.symbol;
        toggleWatchlistItem(symbol);
      });
    });
    
    // View details buttons
    const detailButtons = document.querySelectorAll('.stocks-grid .view-details-btn');
    detailButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        const card = button.closest('.stock-card');
        const symbol = card.dataset.symbol;
        openStockDetailModal(symbol);
      });
    });
    
    // Make whole card clickable
    const stockCards = document.querySelectorAll('.stock-card');
    stockCards.forEach(card => {
      card.addEventListener('click', (event) => {
        if (!event.target.closest('.watchlist-btn')) {
          const symbol = card.dataset.symbol;
          openStockDetailModal(symbol);
        }
      });
    });
  }
  
  // ===============================
  // Search, Filter and Sort Functions
  // ===============================
  function filterStocks() {
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const filterValue = filterSelect ? filterSelect.value : 'all';
    
    let filteredStocks = state.stocksData || [];
    
    // Apply search filter
    if (searchTerm) {
      filteredStocks = filteredStocks.filter(stock => {
        return stock.symbol.toLowerCase().includes(searchTerm) || 
               stock.companyName.toLowerCase().includes(searchTerm);
      });
    }
    
    // Apply category filter
    if (filterValue !== 'all') {
      filteredStocks = filteredStocks.filter(stock => {
        return stock.sector === filterValue;
      });
    }
    
    // Render filtered stocks
    renderStocksTable(filteredStocks);
    renderStocksGrid(filteredStocks);
  }
  
  function sortStocks(sortBy) {
    if (!state.stocksData) return;
    
    let sortedStocks = [...state.stocksData];
    
    switch (sortBy) {
      case 'name':
        sortedStocks.sort((a, b) => a.companyName.localeCompare(b.companyName));
        break;
        
      case 'symbol':
        sortedStocks.sort((a, b) => a.symbol.localeCompare(b.symbol));
        break;
        
      case 'price-high':
        sortedStocks.sort((a, b) => b.currentPrice - a.currentPrice);
        break;
        
      case 'price-low':
        sortedStocks.sort((a, b) => a.currentPrice - b.currentPrice);
        break;
        
      case 'change-high':
        sortedStocks.sort((a, b) => {
          const changeA = ((a.currentPrice - a.previousClose) / a.previousClose) * 100;
          const changeB = ((b.currentPrice - b.previousClose) / b.previousClose) * 100;
          return changeB - changeA;
        });
        break;
        
      case 'change-low':
        sortedStocks.sort((a, b) => {
          const changeA = ((a.currentPrice - a.previousClose) / a.previousClose) * 100;
          const changeB = ((b.currentPrice - b.previousClose) / b.previousClose) * 100;
          return changeA - changeB;
        });
        break;
        
      case 'volume-high':
        sortedStocks.sort((a, b) => b.volume - a.volume);
        break;
        
      default:
        // No sorting needed
        break;
    }
    
    // Render sorted stocks
    renderStocksTable(sortedStocks);
    renderStocksGrid(sortedStocks);
  }
  
  // ===============================
  // UI Functions (View, Tab, Theme)
  // ===============================
  function switchView(view) {
    if (!stocksGrid || !stocksTable) return;
    
    if (view === 'cards') {
      stocksGrid.style.display = 'grid';
      stocksTable.style.display = 'none';
    } else {
      stocksGrid.style.display = 'none';
      stocksTable.style.display = 'table';
    }
    
    // Update active view button
    if (viewButtons) {
      viewButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
      });
    }
    
    state.currentView = view;
  }
  
  function switchTab(tabId) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(tab => {
      tab.classList.remove('active');
    });
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
      selectedTab.classList.add('active');
    }
    
    // Update active tab button
    if (tabButtons) {
      tabButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabId);
      });
    }
    
    state.currentTab = tabId;
  }
  
  function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', state.theme);
    localStorage.setItem('theme', state.theme);
    updateThemeToggleIcons();
  }
  
  function updateThemeToggleIcons() {
    if (!themeToggle) return;
    
    const darkIcon = themeToggle.querySelector('.dark-icon');
    const lightIcon = themeToggle.querySelector('.light-icon');
    
    if (darkIcon && lightIcon) {
      if (state.theme === 'dark') {
        darkIcon.style.opacity = '0';
        darkIcon.style.transform = 'rotate(90deg)';
        lightIcon.style.opacity = '1';
        lightIcon.style.transform = 'rotate(0)';
      } else {
        darkIcon.style.opacity = '1';
        darkIcon.style.transform = 'rotate(0)';
        lightIcon.style.opacity = '0';
        lightIcon.style.transform = 'rotate(-90deg)';
      }
    }
  }
  
  // ===============================
  // Modal & Sidebar Functions
  // ===============================
  function openStockDetailModal(symbol) {
    if (!stockDetailModal) return;
    
    // Fetch stock details
    getStockDetails(symbol).then(stock => {
      // Update modal content
      const modalTitle = stockDetailModal.querySelector('h2');
      if (modalTitle) {
        modalTitle.textContent = `${stock.companyName} (${stock.symbol})`;
      }
      
      // Update other modal content based on stock details
      updateModalContent(stock);
      
      // Show modal
      stockDetailModal.classList.add('show');
      
      // Prevent body scrolling
      document.body.style.overflow = 'hidden';
    });
  }
  
  function closeStockDetailModal() {
    if (!stockDetailModal) return;
    
    // Hide modal
    stockDetailModal.classList.remove('show');
    
    // Re-enable body scrolling
    document.body.style.overflow = '';
  }
  
  function openWatchlistSidebar() {
    if (!watchlistSidebar) return;
    
    // Update watchlist content
    updateWatchlistSidebar();
    
    // Show sidebar
    watchlistSidebar.classList.add('show');
    
    // Prevent body scrolling
    document.body.style.overflow = 'hidden';
  }
  
  function closeWatchlistSidebar() {
    if (!watchlistSidebar) return;
    
    // Hide sidebar
    watchlistSidebar.classList.remove('show');
    
    // Re-enable body scrolling
    document.body.style.overflow = '';
  }
  
  function updateModalContent(stock) {
    if (!stockDetailModal) return;
    
    // Get modal sections
    const priceInfo = stockDetailModal.querySelector('.price-info');
    const stockDetails = stockDetailModal.querySelector('.stock-details');
    const stockDescription = stockDetailModal.querySelector('.stock-description');
    
    if (priceInfo) {
      const changePercent = ((stock.currentPrice - stock.previousClose) / stock.previousClose) * 100;
      const isPositive = changePercent >= 0;
      
      priceInfo.innerHTML = `
        <h3 class="current-price">KES ${stock.currentPrice.toFixed(2)}</h3>
        <p class="price-change ${isPositive ? 'up' : 'down'}">
          <i class="fas ${isPositive ? 'fa-caret-up' : 'fa-caret-down'}"></i>
          ${isPositive ? '+' : ''}${(stock.currentPrice - stock.previousClose).toFixed(2)} 
          (${isPositive ? '+' : ''}${changePercent.toFixed(2)}%)
        </p>
      `;
    }
    
    if (stockDetails) {
      stockDetails.innerHTML = `
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">Open</span>
            <span class="value">KES ${stock.open ? stock.open.toFixed(2) : 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="label">Previous Close</span>
            <span class="value">KES ${stock.previousClose.toFixed(2)}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">Day High</span>
            <span class="value">KES ${stock.dayHigh ? stock.dayHigh.toFixed(2) : 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="label">Day Low</span>
            <span class="value">KES ${stock.dayLow ? stock.dayLow.toFixed(2) : 'N/A'}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">52w High</span>
            <span class="value">KES ${stock.yearHigh ? stock.yearHigh.toFixed(2) : 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="label">52w Low</span>
            <span class="value">KES ${stock.yearLow ? stock.yearLow.toFixed(2) : 'N/A'}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">Volume</span>
            <span class="value">${formatLargeNumber(stock.volume)}</span>
          </div>
          <div class="detail-item">
            <span class="label">Avg. Volume</span>
            <span class="value">${stock.avgVolume ? formatLargeNumber(stock.avgVolume) : 'N/A'}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">Market Cap</span>
            <span class="value">${stock.marketCap ? formatLargeNumber(stock.marketCap) : 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="label">P/E Ratio</span>
            <span class="value">${stock.pe ? stock.pe.toFixed(2) : 'N/A'}</span>
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-item">
            <span class="label">Dividend Yield</span>
            <span class="value">${stock.dividendYield ? stock.dividendYield.toFixed(2) + '%' : 'N/A'}</span>
          </div>
          <div class="detail-item">
            <span class="label">Sector</span>
            <span class="value">${stock.sector || 'N/A'}</span>
          </div>
        </div>
      `;
    }
    
    if (stockDescription) {
      stockDescription.innerHTML = `
        <p>${stock.description || 'No description available.'}</p>
      `;
    }
    
    // Initialize stock chart if chart container exists
    const chartContainer = stockDetailModal.querySelector('#stock-chart');
    if (chartContainer && typeof ApexCharts !== 'undefined') {
      initializeStockChart(chartContainer, stock.symbol);
    }
  }
  
  // ===============================
  // Watchlist Functions
  // ===============================
  function isInWatchlist(symbol) {
    return state.watchlist.includes(symbol);
  }
  
  function toggleWatchlistItem(symbol) {
    if (isInWatchlist(symbol)) {
      removeFromWatchlist(symbol);
    } else {
      addToWatchlist(symbol);
    }
  }
  
  function addToWatchlist(symbol) {
    if (!isAuthenticated) {
      alert('Please log in to add stocks to your watchlist');
      window.location.href = '/Authentication/login.html';
      return;
    }
    
    if (!isInWatchlist(symbol)) {
      try {
        // Add to API
        apiClient.post('/watchlist/add', { symbol });
        
        // Update local state
        state.watchlist.push(symbol);
        localStorage.setItem('watchlist', JSON.stringify(state.watchlist));
        
        // Update UI
        updateWatchlistUI();
        
        // Show success message
        showNotification(`${symbol} added to your watchlist`, 'success');
      } catch (error) {
        console.error('Error adding to watchlist:', error);
        showNotification('Failed to add to watchlist. Please try again.', 'error');
      }
    }
  }
  
  function removeFromWatchlist(symbol) {
    if (isInWatchlist(symbol)) {
      try {
        // Remove from API
        apiClient.post('/watchlist/remove', { symbol });
        
        // Update local state
        state.watchlist = state.watchlist.filter(item => item !== symbol);
        localStorage.setItem('watchlist', JSON.stringify(state.watchlist));
        
        // Update UI
        updateWatchlistUI();
        
        // Show success message
        showNotification(`${symbol} removed from your watchlist`, 'success');
      } catch (error) {
        console.error('Error removing from watchlist:', error);
        showNotification('Failed to remove from watchlist. Please try again.', 'error');
      }
    }
  }
  
  function updateWatchlistUI() {
    // Update watchlist buttons in grid view
    const watchlistButtons = document.querySelectorAll('.watchlist-btn');
    watchlistButtons.forEach(button => {
      const card = button.closest('.stock-card');
      if (card) {
        const symbol = card.dataset.symbol;
        const isWatched = isInWatchlist(symbol);
        
        button.classList.toggle('active', isWatched);
        button.title = isWatched ? 'Remove from watchlist' : 'Add to watchlist';
        button.innerHTML = `<i class="${isWatched ? 'fas' : 'far'} fa-star"></i>`;
      }
    });
    
    // Update watchlist icons in table view
    const watchlistIcons = document.querySelectorAll('.watchlist-icon');
    watchlistIcons.forEach(icon => {
      const row = icon.closest('tr');
      if (row) {
        const symbol = row.dataset.symbol;
        const isWatched = isInWatchlist(symbol);
        
        icon.classList.toggle('active', isWatched);
        icon.classList.toggle('fas', isWatched);
        icon.classList.toggle('far', !isWatched);
        icon.title = isWatched ? 'Remove from watchlist' : 'Add to watchlist';
      }
    });
    
    // Update watchlist sidebar
    updateWatchlistSidebar();
  }
  
  function updateWatchlistSidebar() {
    if (!watchlistSidebar) return;
    
    const watchlistItems = watchlistSidebar.querySelector('.watchlist-items');
    const emptyState = watchlistSidebar.querySelector('.watchlist-empty');
    
    if (!watchlistItems || !emptyState) return;
    
    if (state.watchlist.length === 0) {
      // Show empty state
      watchlistItems.innerHTML = '';
      emptyState.style.display = 'block';
    } else {
      // Hide empty state
      emptyState.style.display = 'none';
      
      // Clear current items
      watchlistItems.innerHTML = '';
      
      // Add watchlist items
      state.watchlist.forEach(symbol => {
        getStockDetails(symbol).then(stock => {
          const changePercent = ((stock.currentPrice - stock.previousClose) / stock.previousClose) * 100;
          const isPositive = changePercent >= 0;
          
          const item = document.createElement('div');
          item.className = 'watchlist-item';
          
          item.innerHTML = `
            <div class="watchlist-item-header">
              <div class="stock-info">
                <h4 class="stock-symbol">${stock.symbol}</h4>
                <p class="stock-name">${stock.companyName}</p>
              </div>
              <button class="remove-watchlist-btn" title="Remove from watchlist" data-symbol="${stock.symbol}">
                <i class="fas fa-times"></i>
              </button>
            </div>
            <div class="watchlist-item-body">
              <div class="price-info">
                <h5 class="stock-price">KES ${stock.currentPrice.toFixed(2)}</h5>
                <p class="stock-change ${isPositive ? 'up' : 'down'}">
                  <i class="fas ${isPositive ? 'fa-caret-up' : 'fa-caret-down'}"></i>
                  ${isPositive ? '+' : ''}${(stock.currentPrice - stock.previousClose).toFixed(2)} 
                  (${isPositive ? '+' : ''}${changePercent.toFixed(2)}%)
                </p>
              </div>
            </div>
          `;
          
          watchlistItems.appendChild(item);
          
          // Add event listener for remove button
          const removeBtn = item.querySelector('.remove-watchlist-btn');
          if (removeBtn) {
            removeBtn.addEventListener('click', (event) => {
              event.stopPropagation();
              removeFromWatchlist(symbol);
            });
          }
          
          // Make item clickable to show stock details
          item.addEventListener('click', (event) => {
            if (!event.target.closest('.remove-watchlist-btn')) {
              openStockDetailModal(symbol);
            }
          });
        });
      });
    }
  }
  
  // ===============================
  // Chart Initialization Functions
  // ===============================
  function initializeCharts() {
    // Initialize featured stock chart if element exists
    const featuredChartContainer = document.getElementById('featured-chart-container');
    if (featuredChartContainer) {
      initializeFeaturedChart(featuredChartContainer);
    }
    
    // Initialize mini charts for each stock card in grid
    initializeMiniCharts();
    
    // Initialize market trend chart
    const marketTrendChart = document.getElementById('market-trend-chart');
    if (marketTrendChart) {
      initializeMarketTrendChart(marketTrendChart);
    }
  }
  
  function initializeFeaturedChart(container) {
    // Sample data for demonstration
    const data = generateChartData(180, 20, 21, 0.5);
    
    const options = {
      series: [{
        name: 'Stock Price',
        data: data
      }],
      chart: {
        type: 'line',
        height: 300,
        toolbar: {
          show: false
        },
        animations: {
          enabled: true,
          easing: 'easeinout',
          speed: 800
        },
        foreColor: getComputedStyle(document.documentElement).getPropertyValue('--color-text-secondary')
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      colors: [getComputedStyle(document.documentElement).getPropertyValue('--color-primary')],
      xaxis: {
        type: 'datetime',
        labels: {
          datetimeUTC: false,
          format: 'HH:mm'
        },
        tooltip: {
          enabled: false
        }
      },
      yaxis: {
        labels: {
          formatter: function(value) {
            return 'KES ' + value.toFixed(2);
          }
        }
      },
      tooltip: {
        x: {
          format: 'HH:mm, dd MMM'
        },
        y: {
          formatter: function(value) {
            return 'KES ' + value.toFixed(2);
          }
        }
      },
      grid: {
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-border')
      }
    };
    
    const chart = new ApexCharts(container, options);
    chart.render();
    
    // Add event listeners for chart period buttons
    const periodButtons = document.querySelectorAll('.time-btn');
    if (periodButtons) {
      periodButtons.forEach(button => {
        button.addEventListener('click', () => {
          periodButtons.forEach(btn => btn.classList.remove('active'));
          button.classList.add('active');
          
          const period = button.dataset.period;
          updateChartPeriod(chart, period);
        });
      });
    }
    
    // Add event listeners for chart type buttons
    const chartTypeButtons = document.querySelectorAll('.chart-type-btn');
    if (chartTypeButtons) {
      chartTypeButtons.forEach(button => {
        button.addEventListener('click', () => {
          chartTypeButtons.forEach(btn => btn.classList.remove('active'));
          button.classList.add('active');
          
          const chartType = button.dataset.chartType;
          updateChartType(chart, chartType);
        });
      });
    }
  }
  
  function initializeMiniCharts() {
    const stockCards = document.querySelectorAll('.stock-card');
    
    stockCards.forEach(card => {
      const miniChartContainer = card.querySelector('.mini-chart');
      if (!miniChartContainer) return;
      
      const symbol = card.dataset.symbol;
      const isGainer = card.classList.contains('gainer');
      
      const options = {
        chart: {
          type: 'area',
          height: 60,
          sparkline: { enabled: true }
        },
        stroke: {
          curve: 'smooth',
          width: 2
        },
        fill: {
          opacity: 0.3
        },
        colors: [
          isGainer 
            ? getComputedStyle(document.documentElement).getPropertyValue('--color-up')
            : getComputedStyle(document.documentElement).getPropertyValue('--color-down')
        ],
        series: [{
          data: generateChartData(30, isGainer ? 100 : 100, isGainer ? 120 : 80, 5)
        }],
        tooltip: {
          enabled: false
        }
      };
      
      new ApexCharts(miniChartContainer, options).render();
    });
  }
  
  function initializeMarketTrendChart(container) {
    const options = {
      series: [{
        name: 'NSE 20 Index',
        data: generateChartData(90, 1800, 1850, 20)
      }],
      chart: {
        type: 'area',
        height: 200,
        toolbar: {
          show: false
        }
      },
      stroke: {
        curve: 'smooth',
        width: 2
      },
      colors: [getComputedStyle(document.documentElement).getPropertyValue('--color-primary')],
      fill: {
        type: 'gradient',
        gradient: {
          shadeIntensity: 1,
          opacityFrom: 0.7,
          opacityTo: 0.3,
          stops: [0, 90, 100]
        }
      },
      xaxis: {
        type: 'datetime',
        labels: {
          datetimeUTC: false,
          format: 'dd MMM'
        }
      },
      yaxis: {
        labels: {
          formatter: function(value) {
            return value.toFixed(0);
          }
        }
      },
      tooltip: {
        x: {
          format: 'dd MMM yyyy'
        }
      },
      grid: {
        borderColor: getComputedStyle(document.documentElement).getPropertyValue('--color-border')
      }
    };
    
    new ApexCharts(container, options).render();
  }
  
  function initializeStockChart(container, symbol) {
    // Fetch historical data for the stock
    fetchHistoricalData(symbol).then(data => {
      const options = {
        series: [{
          name: symbol,
          data: data
        }],
        chart: {
          type: 'candlestick',
          height: 350,
          toolbar: {
            show: true,
            tools: {
              download: true,
              selection: true,
              zoom: true,
              zoomin: true,
              zoomout: true,
              pan: true,
              reset: true
            }
          }
        },
        xaxis: {
          type: 'datetime'
        },
        yaxis: {
          tooltip: {
            enabled: true
          },
          labels: {
            formatter: function(value) {
              return 'KES ' + value.toFixed(2);
            }
          }
        },
        tooltip: {
          enabled: true
        }
      };
      
      new ApexCharts(container, options).render();
    });
  }
  
  // ===============================
  // Helper Functions
  // ===============================
  function generateChartData(days, baseValue, targetValue, volatility) {
    const data = [];
    const now = new Date();
    let value = baseValue;
    const increment = (targetValue - baseValue) / days;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Add some randomness to simulate real market data
      const randomFactor = (Math.random() - 0.5) * volatility;
      value += increment + randomFactor;
      
      data.push({
        x: date.getTime(),
        y: parseFloat(value.toFixed(2))
      });
    }
    
    return data;
  }
  
  function generateCandlestickData(days) {
    const data = [];
    const now = new Date();
    let baseValue = 20;
    
    for (let i = days; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      
      // Simulate OHLC data
      const open = baseValue + (Math.random() - 0.5) * 0.5;
      const close = open + (Math.random() - 0.5) * 0.8;
      const high = Math.max(open, close) + Math.random() * 0.3;
      const low = Math.min(open, close) - Math.random() * 0.3;
      
      data.push({
        x: date.getTime(),
        y: [
          parseFloat(open.toFixed(2)),
          parseFloat(high.toFixed(2)),
          parseFloat(low.toFixed(2)),
          parseFloat(close.toFixed(2))
        ]
      });
      
      baseValue = close;
    }
    
    return data;
  }
  
  function updateChartPeriod(chart, period) {
    // Simulate different time periods by updating the chart data
    let days;
    let baseValue = 20;
    let targetValue = 20.45;
    let volatility = 0.5;
    
    switch (period) {
      case '1D':
        days = 1;
        break;
      case '1W':
        days = 7;
        break;
      case '1M':
        days = 30;
        break;
      case '3M':
        days = 90;
        break;
      case '1Y':
        days = 365;
        baseValue = 18;
        volatility = 1;
        break;
      case '5Y':
        days = 1825;
        baseValue = 15;
        volatility = 2;
        break;
      default:
        days = 1;
    }
    
    chart.updateSeries([{
      data: generateChartData(days, baseValue, targetValue, volatility)
    }]);
  }
  
  function updateChartType(chart, chartType) {
    chart.updateOptions({
      chart: {
        type: chartType === 'candle' ? 'candlestick' : 'line'
      }
    });
    
    // If changing to candlestick, need to update data format
    if (chartType === 'candle') {
      const candleData = generateCandlestickData(30);
      chart.updateSeries([{
        data: candleData
      }]);
    } else {
      chart.updateSeries([{
        data: generateChartData(30, 20, 20.45, 0.5)
      }]);
    }
  }
  
  function showNotification(message, type = 'info') {
    // Check if notification container exists, create if not
    let container = document.querySelector('.notification-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'notification-container';
      document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <p>${message}</p>
      <button class="close-notification">&times;</button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Add event listener for close button
    const closeBtn = notification.querySelector('.close-notification');
    closeBtn.addEventListener('click', () => {
      notification.classList.add('fade-out');
      setTimeout(() => {
        notification.remove();
      }, 300);
    });
    
    // Auto remove after 5 seconds
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 5000);
  }
  
  // ===============================
  // API Functions
  // ===============================
  async function getStockDetails(symbol) {
    try {
      // Try to get from API first
      const response = await marketDataService.getStockDetails(symbol);
      return response;
    } catch (error) {
      console.error('Error fetching stock details:', error);
      
      // Fallback to mock data
      return {
        symbol: symbol,
        companyName: symbol,
        currentPrice: 20 + Math.random() * 10,
        previousClose: 20 + Math.random() * 10,
        open: 20 + Math.random() * 10,
        dayHigh: 22 + Math.random() * 10,
        dayLow: 19 + Math.random() * 10,
        yearHigh: 25 + Math.random() * 10,
        yearLow: 15 + Math.random() * 10,
        volume: Math.floor(Math.random() * 10000000),
        avgVolume: Math.floor(Math.random() * 5000000),
        marketCap: Math.floor(Math.random() * 1000000000),
        pe: 10 + Math.random() * 20,
        dividendYield: Math.random() * 10,
        sector: 'Unknown',
        description: 'No description available for this stock.'
      };
    }
  }
  
  async function fetchHistoricalData(symbol) {
    try {
      // Try to get from API first
      const response = await marketDataService.getHistoricalData(symbol);
      return response;
    } catch (error) {
      console.error('Error fetching historical data:', error);
      
      // Fallback to generated data
      return generateCandlestickData(90);
    }
  }
  
  // Initialize the page
  initializePage();
});