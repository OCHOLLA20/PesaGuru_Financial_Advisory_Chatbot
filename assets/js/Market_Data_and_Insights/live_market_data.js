document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
    
    // Load initial data
    loadMarketData();
    
    // Set up auto-refresh
    setupAutoRefresh();
    
    // Initialize charts
    initializeCharts();
});

// Global variables
let autoRefreshInterval;
let isAutoRefreshEnabled = false;
let currentChartType = 'line';
let currentChartPeriod = '1D';
let currentChartAsset = 'NSE20';
let mainChart = null; // Will hold the chart instance

/**
 * Initialize dashboard elements and state
 */
function initializeDashboard() {
    // Set user name if available in local storage
    const username = localStorage.getItem('username') || 'User';
    document.getElementById('username').textContent = username;
    
    // Check dark mode preference
    const darkModeEnabled = localStorage.getItem('darkMode') === 'true';
    if (darkModeEnabled) {
        document.body.classList.add('dark-mode');
        document.querySelector('.dark-mode-toggle i').classList.replace('fa-moon', 'fa-sun');
    }
    
    // Set default currency
    const savedCurrency = localStorage.getItem('preferredCurrency') || 'KES';
    document.getElementById('currency-selector').value = savedCurrency;
    
    // Initialize view mode (grid or list)
    const viewMode = localStorage.getItem('viewMode') || 'grid';
    if (viewMode === 'list') {
        document.querySelector('.btn-grid').classList.remove('active');
        document.querySelector('.btn-list').classList.add('active');
        document.querySelector('.dashboard-grid').classList.add('list-view');
    }
    
    console.log('Dashboard initialized');
}

/**
 * Set up all event listeners for the dashboard
 */
function setupEventListeners() {
    // View toggle (Grid vs List)
    const gridBtn = document.querySelector('.btn-grid');
    const listBtn = document.querySelector('.btn-list');
    
    gridBtn.addEventListener('click', function() {
        gridBtn.classList.add('active');
        listBtn.classList.remove('active');
        document.querySelector('.dashboard-grid').classList.remove('list-view');
        localStorage.setItem('viewMode', 'grid');
    });
    
    listBtn.addEventListener('click', function() {
        listBtn.classList.add('active');
        gridBtn.classList.remove('active');
        document.querySelector('.dashboard-grid').classList.add('list-view');
        localStorage.setItem('viewMode', 'list');
    });
    
    // Auto-refresh toggle
    const refreshBtn = document.getElementById('refresh-data');
    refreshBtn.addEventListener('click', function() {
        toggleAutoRefresh();
        this.classList.toggle('active');
    });
    
    // Currency selector
    document.getElementById('currency-selector').addEventListener('change', function() {
        const selectedCurrency = this.value;
        localStorage.setItem('preferredCurrency', selectedCurrency);
        updateCurrencyDisplay(selectedCurrency);
        // Refresh market data with new currency
        loadMarketData();
    });
    
    // Dark mode toggle
    document.querySelector('.dark-mode-toggle').addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', isDarkMode);
        
        // Toggle icon
        const icon = this.querySelector('i');
        if (isDarkMode) {
            icon.classList.replace('fa-moon', 'fa-sun');
        } else {
            icon.classList.replace('fa-sun', 'fa-moon');
        }
    });
    
    // Card expand buttons
    document.querySelectorAll('.btn-expand').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.dashboard-card');
            expandCard(card);
        });
    });
    
    // Card refresh buttons
    document.querySelectorAll('.card-actions .btn-refresh').forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.dashboard-card');
            refreshCardData(card);
        });
    });
    
    // Chart period selectors
    document.querySelectorAll('.period-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.period-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentChartPeriod = this.dataset.period;
            updateChart();
        });
    });
    
    // Chart type selectors
    document.querySelectorAll('.chart-type-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.chart-type-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            currentChartType = this.dataset.type;
            updateChart();
        });
    });
    
    // Chart asset selector
    document.getElementById('chart-asset-selector').addEventListener('change', function() {
        currentChartAsset = this.value;
        updateChart();
    });
    
    // News filter buttons
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const filter = this.dataset.filter;
            filterNews(filter);
        });
    });
    
    // Add to watchlist button
    document.querySelector('.btn-add').addEventListener('click', function() {
        openAddToWatchlistModal();
    });
    
    // Alert buttons in watchlist
    document.querySelectorAll('.btn-alert').forEach(button => {
        button.addEventListener('click', function() {
            const watchlistItem = this.closest('.watchlist-item');
            const assetName = watchlistItem.querySelector('.asset-name').textContent;
            const assetTicker = watchlistItem.querySelector('.asset-ticker').textContent;
            const currentPrice = watchlistItem.querySelector('.current-price').textContent;
            openSetAlertModal(assetName, assetTicker, currentPrice);
        });
    });
    
    // Remove from watchlist buttons
    document.querySelectorAll('.btn-remove').forEach(button => {
        button.addEventListener('click', function() {
            const watchlistItem = this.closest('.watchlist-item');
            removeFromWatchlist(watchlistItem);
        });
    });
    
    // Modal close buttons
    document.querySelectorAll('.close-modal').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Add Selected Assets button in watchlist modal
    document.querySelector('.btn-add-selected').addEventListener('click', function() {
        addSelectedToWatchlist();
        closeModal(document.getElementById('add-to-watchlist-modal'));
    });
    
    // Create Alert button in alert modal
    document.querySelector('.btn-create').addEventListener('click', function() {
        createAlert();
        closeModal(document.getElementById('set-alert-modal'));
    });
    
    // Cancel buttons in modals
    document.querySelectorAll('.btn-cancel').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal);
        });
    });
    
    // Create new alert button
    document.querySelector('.btn-create-alert').addEventListener('click', function() {
        openSetAlertModal();
    });
    
    // Edit alert buttons
    document.querySelectorAll('.btn-edit-alert').forEach(button => {
        button.addEventListener('click', function() {
            const alertItem = this.closest('.alert-settings-item');
            const assetName = alertItem.querySelector('.alert-asset-name').textContent;
            const alertCondition = alertItem.querySelector('.alert-condition').textContent;
            editAlert(assetName, alertCondition);
        });
    });
    
    // Delete alert buttons
    document.querySelectorAll('.btn-delete-alert').forEach(button => {
        button.addEventListener('click', function() {
            const alertItem = this.closest('.alert-settings-item');
            deleteAlert(alertItem);
        });
    });
    
    // Category buttons in the "Add to Watchlist" modal
    document.querySelectorAll('.category-btn').forEach(button => {
        button.addEventListener('click', function() {
            document.querySelectorAll('.category-btn').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const category = this.dataset.category;
            filterAssetsByCategory(category);
        });
    });
    
    // Search input in the "Add to Watchlist" modal
    document.querySelector('.search-input').addEventListener('input', function() {
        const searchTerm = this.value.trim().toLowerCase();
        searchAssets(searchTerm);
    });
    
    console.log('Event listeners set up');
}

/**
 * Load market data for all sections
 */
function loadMarketData() {
    // In a real application, this would fetch data from an API
    // For this demo, we'll use the data that's already in the HTML
    
    // Simulate fetching new data
    const loadingStart = performance.now();
    
    // Show loading indicators
    document.querySelectorAll('.dashboard-card').forEach(card => {
        const cardBody = card.querySelector('.card-body');
        cardBody.classList.add('loading');
    });
    
    // Simulate API delay
    setTimeout(() => {
        // For a real app, this is where you would update DOM elements with new data
        updateMarketIndexes();
        updateForexRates();
        updateCryptoPrices();
        updateCommodityPrices();
        updateBondYields();
        
        // Update timestamps to current time
        updateTimestamps();
        
        // Remove loading indicators
        document.querySelectorAll('.dashboard-card').forEach(card => {
            const cardBody = card.querySelector('.card-body');
            cardBody.classList.remove('loading');
        });
        
        const loadingEnd = performance.now();
        console.log(`Market data loaded in ${Math.round(loadingEnd - loadingStart)}ms`);
    }, 1000); // Simulate 1 second loading time
}

/**
 * Update market indexes with randomized data for demo
 */
function updateMarketIndexes() {
    const indexes = document.querySelectorAll('.market-index-item');
    
    indexes.forEach(item => {
        // Get current value and randomly adjust it
        const valueElement = item.querySelector('.index-value');
        const currentValue = parseFloat(valueElement.textContent.replace(/,/g, ''));
        const changePercent = (Math.random() * 2 - 1) * 1.5; // Random between -1.5% and +1.5%
        const changeValue = currentValue * (changePercent / 100);
        const newValue = currentValue + changeValue;
        
        // Update value
        valueElement.textContent = formatNumber(newValue);
        
        // Update change display
        const changeElement = item.querySelector('.index-change');
        const changeValueElement = item.querySelector('.change-value');
        const changePercentElement = item.querySelector('.change-percent');
        const changeIcon = item.querySelector('.index-change i');
        
        changeValueElement.textContent = (changeValue >= 0 ? '+' : '') + formatNumber(changeValue);
        changePercentElement.textContent = `(${(changeValue >= 0 ? '+' : '')}${changePercent.toFixed(2)}%)`;
        
        if (changeValue >= 0) {
            changeElement.className = 'index-change positive';
            changeIcon.className = 'fas fa-arrow-up';
        } else {
            changeElement.className = 'index-change negative';
            changeIcon.className = 'fas fa-arrow-down';
        }
    });
}

/**
 * Update forex rates with randomized data for demo
 */
function updateForexRates() {
    const forexItems = document.querySelectorAll('.forex-item');
    
    forexItems.forEach(item => {
        // Get current value and randomly adjust it
        const valueElement = item.querySelector('.forex-value');
        const currentValue = parseFloat(valueElement.textContent);
        const changePercent = (Math.random() * 2 - 1) * 1.2; // Random between -1.2% and +1.2%
        const changeValue = currentValue * (changePercent / 100);
        const newValue = currentValue + changeValue;
        
        // Update value
        valueElement.textContent = newValue.toFixed(2);
        
        // Update change display
        const changeElement = item.querySelector('.forex-change');
        const changeValueElement = item.querySelector('.change-value');
        const changePercentElement = item.querySelector('.change-percent');
        const changeIcon = item.querySelector('.forex-change i');
        
        changeValueElement.textContent = (changeValue >= 0 ? '+' : '') + changeValue.toFixed(2);
        changePercentElement.textContent = `(${(changeValue >= 0 ? '+' : '')}${changePercent.toFixed(2)}%)`;
        
        if (changeValue >= 0) {
            changeElement.className = 'forex-change positive';
            changeIcon.className = 'fas fa-arrow-up';
        } else {
            changeElement.className = 'forex-change negative';
            changeIcon.className = 'fas fa-arrow-down';
        }
    });
}

/**
 * Update crypto prices with randomized data for demo
 */
function updateCryptoPrices() {
    const cryptoItems = document.querySelectorAll('.crypto-item');
    
    // Update market sentiment
    const sentimentValue = 45 + Math.random() * 40; // Random between 45% and 85%
    const sentimentMeter = document.querySelector('.meter-progress');
    const sentimentText = document.querySelector('.sentiment-value');
    
    sentimentMeter.style.width = `${sentimentValue}%`;
    sentimentText.textContent = `${sentimentValue > 60 ? 'Bullish' : 'Neutral'} (${sentimentValue.toFixed(0)}%)`;
    
    cryptoItems.forEach(item => {
        // Get current value and randomly adjust it
        const valueElement = item.querySelector('.crypto-value');
        const valueParts = valueElement.textContent.split(' ');
        const currentValue = parseFloat(valueParts[0].replace(/,/g, ''));
        const currency = valueParts[1];
        
        const changePercent = (Math.random() * 6 - 2); // Random between -2% and +4%
        const changeValue = currentValue * (changePercent / 100);
        const newValue = currentValue + changeValue;
        
        // Update value
        valueElement.textContent = `${formatNumber(newValue)} ${currency}`;
        
        // Update change display
        const changeElement = item.querySelector('.crypto-change');
        const changeValueElement = item.querySelector('.change-value');
        const changePercentElement = item.querySelector('.change-percent');
        
        changeValueElement.textContent = (changeValue >= 0 ? '+' : '') + formatNumber(changeValue);
        changePercentElement.textContent = `(${(changeValue >= 0 ? '+' : '')}${changePercent.toFixed(2)}%)`;
        
        // Update volume with small random change
        const volumeElement = item.querySelector('.volume-indicator');
        const currentVolume = parseFloat(volumeElement.textContent.replace('Vol: ', '').replace('B', ''));
        const newVolume = currentVolume + (Math.random() * 2 - 1);
        volumeElement.textContent = `Vol: ${Math.max(0.1, newVolume).toFixed(1)}B`;
        
        if (changeValue >= 0) {
            changeElement.className = 'crypto-change positive';
        } else {
            changeElement.className = 'crypto-change negative';
        }
    });
}

/**
 * Update commodity prices with randomized data for demo
 */
function updateCommodityPrices() {
    const commodityItems = document.querySelectorAll('.commodity-item');
    
    commodityItems.forEach(item => {
        // Get current value and randomly adjust it
        const valueElement = item.querySelector('.commodity-value');
        const valueParts = valueElement.textContent.split(' ');
        const currentValue = parseFloat(valueParts[0]);
        const unit = valueParts[1];
        
        const changePercent = (Math.random() * 3 - 1); // Random between -1% and +2%
        const changeValue = currentValue * (changePercent / 100);
        const newValue = currentValue + changeValue;
        
        // Update value
        valueElement.textContent = `${newValue.toFixed(2)} ${unit}`;
        
        // Update change display
        const changeElement = item.querySelector('.commodity-change');
        const changeValueElement = item.querySelector('.change-value');
        const changePercentElement = item.querySelector('.change-percent');
        const changeIcon = item.querySelector('.commodity-change i');
        
        changeValueElement.textContent = (changeValue >= 0 ? '+' : '') + changeValue.toFixed(2);
        changePercentElement.textContent = `(${(changeValue >= 0 ? '+' : '')}${changePercent.toFixed(2)}%)`;
        
        if (changeValue >= 0) {
            changeElement.className = 'commodity-change positive';
            changeIcon.className = 'fas fa-arrow-up';
        } else {
            changeElement.className = 'commodity-change negative';
            changeIcon.className = 'fas fa-arrow-down';
        }
    });
}

/**
 * Update bond yields with randomized data for demo
 */
function updateBondYields() {
    const bondItems = document.querySelectorAll('.bond-item');
    
    bondItems.forEach(item => {
        // Get current value and randomly adjust it
        const valueElement = item.querySelector('.bond-value');
        const currentValue = parseFloat(valueElement.textContent);
        const changeValue = (Math.random() * 0.3 - 0.1).toFixed(2); // Random between -0.1% and +0.2%
        const newValue = (currentValue + parseFloat(changeValue)).toFixed(2);
        
        // Update value
        valueElement.textContent = `${newValue}%`;
        
        // Update change display
        const changeElement = item.querySelector('.bond-change');
        const changeValueElement = item.querySelector('.change-value');
        const changeIcon = item.querySelector('.bond-change i');
        
        changeValueElement.textContent = (changeValue >= 0 ? '+' : '') + `${changeValue}%`;
        
        if (changeValue >= 0) {
            changeElement.className = 'bond-change positive';
            changeIcon.className = 'fas fa-arrow-up';
        } else {
            changeElement.className = 'bond-change negative';
            changeIcon.className = 'fas fa-arrow-down';
        }
    });
}

/**
 * Update all timestamps to the current time
 */
function updateTimestamps() {
    const now = new Date();
    const formattedDate = `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
    
    // Update the recommendation timestamp
    const recommendationTimestamp = document.querySelector('.recommendation-timestamp');
    if (recommendationTimestamp) {
        recommendationTimestamp.textContent = `Updated: ${formattedDate}`;
    }
    
    // Update news timestamps (in a real app, these would have real relative times)
    document.querySelectorAll('.news-time').forEach((element, index) => {
        // Just a demo to show different times
        const minutesAgo = [5, 15, 45, 120][index] || 30;
        element.textContent = `${minutesAgo} minutes ago`;
    });
}

/**
 * Set up auto-refresh functionality
 */
function setupAutoRefresh() {
    // Check if auto-refresh was previously enabled
    const wasEnabled = localStorage.getItem('autoRefreshEnabled') === 'true';
    if (wasEnabled) {
        toggleAutoRefresh(true);
        document.getElementById('refresh-data').classList.add('active');
    }
}

/**
 * Toggle auto-refresh functionality
 */
function toggleAutoRefresh(forceState = null) {
    isAutoRefreshEnabled = forceState !== null ? forceState : !isAutoRefreshEnabled;
    
    // Store preference
    localStorage.setItem('autoRefreshEnabled', isAutoRefreshEnabled);
    
    // Clear existing interval if any
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    
    // Set up new interval if enabled
    if (isAutoRefreshEnabled) {
        autoRefreshInterval = setInterval(loadMarketData, 60000); // Refresh every minute
        console.log('Auto-refresh enabled, refreshing every minute');
    } else {
        console.log('Auto-refresh disabled');
    }
    
    // Update button text
    const refreshBtn = document.getElementById('refresh-data');
    if (isAutoRefreshEnabled) {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Auto-Refresh On';
    } else {
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Auto-Refresh';
    }
}

/**
 * Update currency display throughout the dashboard
 */
function updateCurrencyDisplay(currency) {
    // This would update currency symbols throughout the UI
    console.log(`Currency updated to ${currency}`);
    
    // In a real application, you would update all price displays to the new currency
    // This might involve currency conversion API calls
}

/**
 * Expand a dashboard card to full screen
 */
function expandCard(card) {
    card.classList.toggle('expanded');
    
    if (card.classList.contains('expanded')) {
        card.style.position = 'fixed';
        card.style.top = '0';
        card.style.left = '0';
        card.style.width = '100%';
        card.style.height = '100%';
        card.style.zIndex = '1000';
        card.style.borderRadius = '0';
        
        // Change expand icon to compress icon
        const expandBtn = card.querySelector('.btn-expand i');
        expandBtn.classList.replace('fa-expand-alt', 'fa-compress-alt');
        
        // If this is the chart card, resize the chart
        if (card.id === 'interactive-charts' && mainChart) {
            mainChart.resize();
        }
    } else {
        card.style.position = '';
        card.style.top = '';
        card.style.left = '';
        card.style.width = '';
        card.style.height = '';
        card.style.zIndex = '';
        card.style.borderRadius = '';
        
        // Change compress icon back to expand icon
        const expandBtn = card.querySelector('.btn-expand i');
        expandBtn.classList.replace('fa-compress-alt', 'fa-expand-alt');
        
        // If this is the chart card, resize the chart
        if (card.id === 'interactive-charts' && mainChart) {
            setTimeout(() => mainChart.resize(), 300); // Wait for transition to complete
        }
    }
}

/**
 * Refresh data for a specific card
 */
function refreshCardData(card) {
    const cardBody = card.querySelector('.card-body');
    cardBody.classList.add('loading');
    
    // Simulate API delay
    setTimeout(() => {
        // In a real app, this would update with fresh data from an API
        switch(card.id) {
            case 'stock-indexes':
                updateMarketIndexes();
                break;
            case 'forex-rates':
                updateForexRates();
                break;
            case 'crypto-prices':
                updateCryptoPrices();
                break;
            case 'commodity-prices':
                updateCommodityPrices();
                break;
            case 'bond-yields':
                updateBondYields();
                break;
            case 'interactive-charts':
                updateChart();
                break;
            case 'ai-insights':
                updateTimestamps();
                break;
            case 'financial-news':
                updateTimestamps();
                break;
        }
        
        cardBody.classList.remove('loading');
        
        // Add a quick flash effect to show the data was refreshed
        cardBody.classList.add('refreshed');
        setTimeout(() => {
            cardBody.classList.remove('refreshed');
        }, 500);
        
        console.log(`Refreshed data for ${card.id}`);
    }, 700); // Simulate loading delay
}

/**
 * Initialize charts
 */
function initializeCharts() {
    // In a real application, this would use a charting library like Chart.js, ApexCharts, or a financial chart library
    
    console.log('Initializing charts with default settings');
    console.log(`Chart Type: ${currentChartType}`);
    console.log(`Chart Period: ${currentChartPeriod}`);
    console.log(`Chart Asset: ${currentChartAsset}`);
    
    // Remove placeholder if it exists
    const chartContainer = document.getElementById('main-chart');
    const placeholder = chartContainer.querySelector('.chart-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    
    // Create a canvas for the chart
    const canvas = document.createElement('canvas');
    canvas.id = 'chart-canvas';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    chartContainer.appendChild(canvas);
    
    // In a real app, this is where you would initialize your chart library
    // mainChart = new Chart(canvas.getContext('2d'), {...options});
    
    // For this demo, we'll fake it with a placeholder
    canvas.style.display = 'none';
    placeholder.style.display = 'flex';
    
    // Initialize with random data
    updateChartStats();
}

/**
 * Update chart when settings change
 */
function updateChart() {
    console.log('Updating chart with new settings');
    console.log(`Chart Type: ${currentChartType}`);
    console.log(`Chart Period: ${currentChartPeriod}`);
    console.log(`Chart Asset: ${currentChartAsset}`);
    
    // In a real app, this would update the chart with new data and settings
    // mainChart.update({...new options});
    
    // For demo, we'll just update the stat values
    updateChartStats();
}

/**
 * Update chart statistics
 */
function updateChartStats() {
    // In a real app, these would be actual values from your data
    let statValues = {
        open: '4,872.45',
        high: '4,915.78',
        low: '4,852.33',
        close: '4,897.12',
        volume: '1.45B'
    };
    
    // Generate some random variations for demo purposes
    if (currentChartAsset === 'BTCUSD') {
        const basePrice = 58432.75;
        statValues = {
            open: formatNumber(basePrice - Math.random() * 1000),
            high: formatNumber(basePrice + Math.random() * 1000),
            low: formatNumber(basePrice - Math.random() * 1500),
            close: formatNumber(basePrice + Math.random() * 500),
            volume: formatVolume(32.5 + Math.random() * 5)
        };
    } else if (currentChartAsset === 'KESUSD') {
        const baseRate = 128.75;
        statValues = {
            open: formatNumber(baseRate - Math.random() * 0.5, 2),
            high: formatNumber(baseRate + Math.random() * 0.3, 2),
            low: formatNumber(baseRate - Math.random() * 0.7, 2),
            close: formatNumber(baseRate + Math.random() * 0.1, 2),
            volume: formatVolume(0.5 + Math.random() * 0.3)
        };
    } else if (currentChartAsset === 'GOLD') {
        const basePrice = 2045.32;
        statValues = {
            open: formatNumber(basePrice - Math.random() * 10, 2),
            high: formatNumber(basePrice + Math.random() * 15, 2),
            low: formatNumber(basePrice - Math.random() * 12, 2),
            close: formatNumber(basePrice + Math.random() * 8, 2),
            volume: formatVolume(0.8 + Math.random() * 0.5)
        };
    }
    
    // Update the DOM elements
    document.getElementById('stat-open').textContent = statValues.open;
    document.getElementById('stat-high').textContent = statValues.high;
    document.getElementById('stat-low').textContent = statValues.low;
    document.getElementById('stat-close').textContent = statValues.close;
    document.getElementById('stat-volume').textContent = statValues.volume;
}

/**
 * Format number with commas for thousands
 */
function formatNumber(number, decimals = 2) {
    return number.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Format volume with B for billions, M for millions
 */
function formatVolume(number) {
    if (number >= 1) {
        return `${number.toFixed(1)}B`;
    } else {
        return `${(number * 1000).toFixed(1)}M`;
    }
}

/**
 * Filter news by category
 */
function filterNews(filter) {
    console.log(`Filtering news by: ${filter}`);
    
    // Get all news items
    const newsItems = document.querySelectorAll('.news-item');
    
    // For demo purposes, we'll just show/hide randomly
    if (filter === 'all') {
        newsItems.forEach(item => {
            item.style.display = 'block';
        });
    } else {
        newsItems.forEach(item => {
            // Randomly determine if this item should be shown for this filter
            const shouldShow = Math.random() > 0.5;
            item.style.display = shouldShow ? 'block' : 'none';
        });
    }
}

/**
 * Open the "Add to Watchlist" modal
 */
function openAddToWatchlistModal() {
    const modal = document.getElementById('add-to-watchlist-modal');
    modal.style.display = 'flex';
    
    // Focus on search input
    const searchInput = modal.querySelector('.search-input');
    searchInput.focus();
    
    // In a real app, this is where you would load available assets
    loadAvailableAssets();
}

/**
 * Open the "Set Alert" modal
 */
function openSetAlertModal(assetName = null, assetTicker = null, currentPrice = null) {
    const modal = document.getElementById('set-alert-modal');
    modal.style.display = 'flex';
    
    // If asset info is provided, update the modal
    if (assetName && currentPrice) {
        const alertAssetName = modal.querySelector('.alert-asset-name');
        const alertCurrentPrice = modal.querySelector('.current-price');
        
        alertAssetName.textContent = assetName + (assetTicker ? ` (${assetTicker})` : '');
        alertCurrentPrice.textContent = `Current Price: ${currentPrice}`;
        
        // Set a default alert price slightly above current
        const priceParts = currentPrice.split(' ');
        const price = parseFloat(priceParts[0].replace(/,/g, ''));
        const currency = priceParts[1] || '';
        
        document.getElementById('alert-price').value = (price * 1.05).toFixed(2);
        modal.querySelector('.currency-label').textContent = currency;
    }
}

/**
 * Close any modal
 */
function closeModal(modal) {
    modal.style.display = 'none';
}

/**
 * Load available assets for the watchlist modal
 */
function loadAvailableAssets() {
    // For demo, we'll just simulate loading
    const searchResults = document.querySelector('.search-results');
    searchResults.innerHTML = '<div class="loading-indicator">Loading assets...</div>';
    
    // Simulate API delay
    setTimeout(() => {
        // This would be populated with real data in a production app
        searchResults.innerHTML = `
            <div class="asset-result">
                <input type="checkbox" id="asset-1" class="asset-checkbox">
                <label for="asset-1">
                    <img src="../../assets/images/stocks/equity.png" alt="Equity Group" class="asset-icon">
                    <div class="asset-info">
                        <span class="asset-name">Equity Group Holdings</span>
                        <span class="asset-ticker">EQTY.NR</span>
                    </div>
                    <span class="asset-price">52.75 KES</span>
                </label>
            </div>
            <div class="asset-result">
                <input type="checkbox" id="asset-2" class="asset-checkbox">
                <label for="asset-2">
                    <img src="../../assets/images/stocks/kcb.png" alt="KCB Group" class="asset-icon">
                    <div class="asset-info">
                        <span class="asset-name">KCB Group</span>
                        <span class="asset-ticker">KCB.NR</span>
                    </div>
                    <span class="asset-price">39.45 KES</span>
                </label>
            </div>
            <div class="asset-result">
                <input type="checkbox" id="asset-3" class="asset-checkbox">
                <label for="asset-3">
                    <img src="../../assets/images/stocks/bamburi.png" alt="Bamburi Cement" class="asset-icon">
                    <div class="asset-info">
                        <span class="asset-name">Bamburi Cement</span>
                        <span class="asset-ticker">BAMB.NR</span>
                    </div>
                    <span class="asset-price">41.80 KES</span>
                </label>
            </div>
        `;
        
        // Add event listeners to checkboxes
        const checkboxes = document.querySelectorAll('.asset-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateAddSelectedButton);
        });
        
        console.log('Assets loaded');
    }, 800);
}

/**
 * Update the state of the "Add Selected" button
 */
function updateAddSelectedButton() {
    const checkboxes = document.querySelectorAll('.asset-checkbox:checked');
    const addButton = document.querySelector('.btn-add-selected');
    
    if (checkboxes.length > 0) {
        addButton.disabled = false;
        addButton.textContent = `Add Selected (${checkboxes.length})`;
    } else {
        addButton.disabled = true;
        addButton.textContent = 'Add Selected';
    }
}

/**
 * Add selected assets to watchlist
 */
function addSelectedToWatchlist() {
    const checkboxes = document.querySelectorAll('.asset-checkbox:checked');
    console.log(`Adding ${checkboxes.length} assets to watchlist`);
    
    // In a real app, this would add the selected assets to the user's watchlist
    // and then refresh the watchlist display
    
    // For demo, just show an alert
    alert(`${checkboxes.length} assets added to your watchlist!`);
}

/**
 * Remove an item from the watchlist
 */
function removeFromWatchlist(watchlistItem) {
    const assetName = watchlistItem.querySelector('.asset-name').textContent;
    console.log(`Removing ${assetName} from watchlist`);
    
    // Animate removal
    watchlistItem.style.opacity = '0';
    watchlistItem.style.height = '0';
    watchlistItem.style.overflow = 'hidden';
    
    // In a real app, this would call an API to remove the asset
    // For demo, we'll just remove the DOM element after animation
    setTimeout(() => {
        watchlistItem.remove();
    }, 300);
}

/**
 * Create a price alert
 */
function createAlert() {
    // Get alert settings from form
    const assetName = document.querySelector('.alert-asset-name').textContent;
    const alertType = document.querySelector('input[name="alert-type"]:checked').value;
    const targetPrice = document.getElementById('alert-price').value;
    const currency = document.querySelector('.currency-label').textContent;
    
    const notifyApp = document.getElementById('notify-app').checked;
    const notifyEmail = document.getElementById('notify-email').checked;
    const notifySMS = document.getElementById('notify-sms').checked;
    
    console.log(`Creating alert for ${assetName}`);
    console.log(`Alert type: ${alertType}`);
    console.log(`Target price: ${targetPrice} ${currency}`);
    console.log(`Notification methods: ${notifyApp ? 'App ' : ''}${notifyEmail ? 'Email ' : ''}${notifySMS ? 'SMS' : ''}`);
    
    // In a real app, this would call an API to create the alert
    // For demo, add the new alert to the alerts list
    const alertsList = document.querySelector('.alerts-list');
    const alertConditionText = alertType === 'above' ? 
        `Price rises above ${targetPrice} ${currency}` : 
        `Price drops below ${targetPrice} ${currency}`;
    
    const newAlertItem = document.createElement('li');
    newAlertItem.className = 'alert-settings-item';
    newAlertItem.innerHTML = `
        <div class="alert-details">
            <span class="alert-asset-name">${assetName}</span>
            <span class="alert-condition">${alertConditionText}</span>
        </div>
        <div class="alert-actions">
            <button class="btn-edit-alert" title="Edit Alert"><i class="fas fa-pencil-alt"></i></button>
            <button class="btn-delete-alert" title="Delete Alert"><i class="fas fa-trash"></i></button>
        </div>
    `;
    
    // Add event listeners to new buttons
    newAlertItem.querySelector('.btn-edit-alert').addEventListener('click', function() {
        editAlert(assetName, alertConditionText);
    });
    
    newAlertItem.querySelector('.btn-delete-alert').addEventListener('click', function() {
        deleteAlert(newAlertItem);
    });
    
    alertsList.appendChild(newAlertItem);
}

/**
 * Edit an existing alert
 */
function editAlert(assetName, alertCondition) {
    console.log(`Editing alert for ${assetName}: ${alertCondition}`);
    
    // Extract price from condition
    const priceMatch = alertCondition.match(/(above|below) (\d+\.?\d*) (\w+)/);
    if (priceMatch) {
        const alertType = priceMatch[1] === 'above' ? 'above' : 'below';
        const price = priceMatch[2];
        const currency = priceMatch[3];
        
        // Open the alert modal with pre-filled values
        openSetAlertModal(assetName, '', `${price} ${currency}`);
        
        // Set the alert type radio button
        const alertTypeRadio = document.getElementById(`price-${alertType}`);
        if (alertTypeRadio) {
            alertTypeRadio.checked = true;
        }
    } else {
        // If we can't parse the condition, just open the modal
        openSetAlertModal(assetName);
    }
}

/**
 * Delete an alert
 */
function deleteAlert(alertItem) {
    const assetName = alertItem.querySelector('.alert-asset-name').textContent;
    console.log(`Deleting alert for ${assetName}`);
    
    // Confirm deletion
    if (confirm(`Are you sure you want to delete the alert for ${assetName}?`)) {
        // Animate removal
        alertItem.style.opacity = '0';
        alertItem.style.height = '0';
        alertItem.style.overflow = 'hidden';
        
        // In a real app, this would call an API to delete the alert
        // For demo, we'll just remove the DOM element after animation
        setTimeout(() => {
            alertItem.remove();
        }, 300);
    }
}

/**
 * Filter assets by category in the watchlist modal
 */
function filterAssetsByCategory(category) {
    console.log(`Filtering assets by category: ${category}`);
    
    // In a real app, this would filter the assets in the modal
    // For this demo, we'll just simulate loading with a delay
    const searchResults = document.querySelector('.search-results');
    searchResults.innerHTML = '<div class="loading-indicator">Loading ' + category + '...</div>';
    
    // Simulate API delay and then reload assets
    setTimeout(() => {
        loadAvailableAssets();
    }, 500);
}

/**
 * Search assets in the watchlist modal
 */
function searchAssets(searchTerm) {
    console.log(`Searching for assets: ${searchTerm}`);
    
    // In a real app, this would filter assets based on search term
    // For demo, if search term exists, show fewer results
    if (searchTerm.length > 0) {
        const assetResults = document.querySelectorAll('.asset-result');
        assetResults.forEach((result, index) => {
            // Just a simple demo - hide some results based on search
            if (index % 2 === 1) {
                result.style.display = 'none';
            } else {
                result.style.display = 'block';
            }
        });
    } else {
        // If search is cleared, show all
        const assetResults = document.querySelectorAll('.asset-result');
        assetResults.forEach(result => {
            result.style.display = 'block';
        });
    }
}

/**
 * Handle clicks outside modals to close them
 */
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            closeModal(modal);
        }
    });
});

/**
 * Handle escape key to close modals
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal[style*="display: flex"]');
        openModals.forEach(modal => {
            closeModal(modal);
        });
    }
});

// CSS helper for refreshed animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
    .card-body.loading {
        opacity: 0.7;
        pointer-events: none;
    }
    
    .card-body.refreshed {
        animation: refresh-flash 0.5s;
    }
    
    @keyframes refresh-flash {
        0% { background-color: rgba(44, 110, 203, 0.1); }
        100% { background-color: transparent; }
    }
    
    .dashboard-grid.list-view {
        display: flex;
        flex-direction: column;
    }
    
    .loading-indicator {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
        color: var(--text-muted);
    }
    
    .asset-result {
        display: flex;
        align-items: center;
        padding: 10px;
        border-bottom: 1px solid var(--border-color);
    }
    
    .asset-result label {
        display: flex;
        align-items: center;
        flex: 1;
        cursor: pointer;
    }
    
    .asset-result .asset-icon {
        width: 24px;
        height: 24px;
        margin-right: 10px;
    }
    
    .asset-result .asset-info {
        flex: 1;
    }
    
    .asset-result .asset-name {
        display: block;
        font-weight: 500;
    }
    
    .asset-result .asset-ticker {
        font-size: 0.8rem;
        color: var(--text-muted);
    }
    
    .asset-result .asset-price {
        font-weight: 600;
    }
`;
document.head.appendChild(styleSheet);