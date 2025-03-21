document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initApp();
});

/**
 * Initialize all application components
 */
function initApp() {
    initThemeToggle();
    initNotifications();
    initSidebar();
    initCryptoTable();
    initCharts();
    initTabs();
    initModals();
    initPriceAlerts();
    initTimeRangeSelection();
    initChartTypeSelection();
    initTechnicalIndicators();
    
    // Add event listeners for global actions
    document.getElementById('refresh-button').addEventListener('click', refreshData);
    document.getElementById('chat-with-pesaguru').addEventListener('click', openChatbot);
    document.getElementById('currency-selector').addEventListener('change', changeCurrency);
    document.getElementById('watchlist-button').addEventListener('click', toggleWatchlist);
    document.getElementById('load-more-crypto').addEventListener('click', loadMoreCryptos);
    document.getElementById('refresh-insights').addEventListener('click', refreshInsights);
    document.getElementById('region-selector').addEventListener('change', changeRegion);
}

/**
 * Theme toggle functionality
 */
function initThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle-button');
    
    // Load saved theme preference
    const savedTheme = localStorage.getItem('darkTheme');
    if (savedTheme === 'true') {
        document.body.classList.add('dark-theme');
    }
    
    themeToggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        
        // Save preference to local storage
        const isDarkTheme = document.body.classList.contains('dark-theme');
        localStorage.setItem('darkTheme', isDarkTheme);
    });
}

/**
 * Mobile sidebar toggle
 */
function initSidebar() {
    const backButton = document.getElementById('back-button');
    const sidebar = document.querySelector('.sidebar');
    
    backButton.addEventListener('click', function() {
        if (window.innerWidth < 992) {
            sidebar.classList.toggle('active');
        } else {
            // Navigate back to previous page
            window.history.back();
        }
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (window.innerWidth < 992 && 
            !event.target.closest('.sidebar') && 
            !event.target.closest('#back-button') && 
            sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
        }
    });
}

/**
 * Notification system functionality
 */
function initNotifications() {
    const notificationBtn = document.getElementById('notification-button');
    const notificationDropdown = document.getElementById('notification-dropdown');
    const markAllReadBtn = document.getElementById('mark-all-read');
    
    notificationBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationDropdown.classList.toggle('active');
    });
    
    markAllReadBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        const notifications = document.querySelectorAll('.notification-item');
        notifications.forEach(notification => {
            notification.classList.add('read');
        });
        updateNotificationCount();
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!notificationBtn.contains(event.target) && !notificationDropdown.contains(event.target)) {
            notificationDropdown.classList.remove('active');
        }
    });
    
    // Load notifications (mock data)
    loadNotifications();
}

function loadNotifications() {
    const notificationList = document.getElementById('notification-list');
    const mockNotifications = [
        {
            id: 1,
            title: 'Bitcoin Price Alert',
            message: 'Bitcoin has risen above KES 6,500,000',
            time: '10 minutes ago',
            read: false
        },
        {
            id: 2,
            title: 'Market Update',
            message: 'Crypto market cap has increased by 3.2% in the last 24 hours',
            time: '2 hours ago',
            read: false
        },
        {
            id: 3,
            title: 'New Regulation Update',
            message: 'CBK has issued new guidelines for cryptocurrency transactions',
            time: '1 day ago',
            read: true
        }
    ];
    
    notificationList.innerHTML = '';
    
    mockNotifications.forEach(notification => {
        const notificationItem = document.createElement('div');
        notificationItem.classList.add('notification-item');
        if (notification.read) {
            notificationItem.classList.add('read');
        }
        
        notificationItem.innerHTML = `
            <div class="notification-header">
                <h4>${notification.title}</h4>
                <span class="notification-time">${notification.time}</span>
            </div>
            <p class="notification-message">${notification.message}</p>
        `;
        
        notificationList.appendChild(notificationItem);
    });
    
    updateNotificationCount();
}

function updateNotificationCount() {
    const notificationCount = document.getElementById('notification-count');
    const unreadNotifications = document.querySelectorAll('.notification-item:not(.read)').length;
    
    notificationCount.textContent = unreadNotifications;
    
    if (unreadNotifications === 0) {
        notificationCount.style.display = 'none';
    } else {
        notificationCount.style.display = 'flex';
    }
}

/**
 * Cryptocurrency table functionality
 */
function initCryptoTable() {
    // Fetch crypto data
    fetchCryptoData();
    
    // Add event listeners for table actions
    const tableBody = document.getElementById('crypto-table-body');
    
    tableBody.addEventListener('click', function(e) {
        const target = e.target;
        
        // Handle add to watchlist button
        if (target.closest('.btn-add-watchlist')) {
            e.stopPropagation();
            const row = target.closest('.crypto-row');
            const coinId = row.getAttribute('data-id');
            toggleWatchlistCoin(coinId, target.closest('.btn-add-watchlist'));
        }
        
        // Handle set alert button
        if (target.closest('.btn-set-alert')) {
            e.stopPropagation();
            const row = target.closest('.crypto-row');
            const coinId = row.getAttribute('data-id');
            openCreateAlertModal(coinId);
        }
        
        // Handle row click to show details
        if (target.closest('.crypto-row') && 
            !target.closest('.btn-add-watchlist') && 
            !target.closest('.btn-set-alert')) {
            const row = target.closest('.crypto-row');
            const coinId = row.getAttribute('data-id');
            openCryptoDetailsModal(coinId);
        }
    });
}

function fetchCryptoData() {
    // In a real implementation, this would be an API call to CoinGecko or similar
    // For now, using mock data
    const mockCryptoData = [
        {
            id: 'bitcoin',
            name: 'Bitcoin',
            symbol: 'BTC',
            current_price: {
                kes: 6500000,
                usd: 57000,
                eur: 52000
            },
            price_change_percentage_24h: 2.5,
            price_change_percentage_7d: -1.2,
            market_cap: {
                kes: 123400000000000,
                usd: 1080000000000,
                eur: 984000000000
            },
            total_volume: {
                kes: 5670000000000,
                usd: 49700000000,
                eur: 45200000000
            }
        },
        {
            id: 'ethereum',
            name: 'Ethereum',
            symbol: 'ETH',
            current_price: {
                kes: 345000,
                usd: 3020,
                eur: 2750
            },
            price_change_percentage_24h: 1.8,
            price_change_percentage_7d: 3.5,
            market_cap: {
                kes: 41500000000000,
                usd: 363000000000,
                eur: 330000000000
            },
            total_volume: {
                kes: 1680000000000,
                usd: 14700000000,
                eur: 13400000000
            }
        },
        {
            id: 'solana',
            name: 'Solana',
            symbol: 'SOL',
            current_price: {
                kes: 138000,
                usd: 1210,
                eur: 1100
            },
            price_change_percentage_24h: 4.2,
            price_change_percentage_7d: 12.5,
            market_cap: {
                kes: 6650000000000,
                usd: 58200000000,
                eur: 53000000000
            },
            total_volume: {
                kes: 980000000000,
                usd: 8580000000,
                eur: 7800000000
            }
        },
        {
            id: 'cardano',
            name: 'Cardano',
            symbol: 'ADA',
            current_price: {
                kes: 6270,
                usd: 55,
                eur: 50
            },
            price_change_percentage_24h: -0.8,
            price_change_percentage_7d: 5.1,
            market_cap: {
                kes: 2195000000000,
                usd: 19200000000,
                eur: 17500000000
            },
            total_volume: {
                kes: 57000000000,
                usd: 500000000,
                eur: 455000000
            }
        },
        {
            id: 'ripple',
            name: 'XRP',
            symbol: 'XRP',
            current_price: {
                kes: 6840,
                usd: 60,
                eur: 54.5
            },
            price_change_percentage_24h: 0.5,
            price_change_percentage_7d: -2.3,
            market_cap: {
                kes: 3420000000000,
                usd: 30000000000,
                eur: 27300000000
            },
            total_volume: {
                kes: 114000000000,
                usd: 1000000000,
                eur: 910000000
            }
        }
    ];
    
    updateCryptoTable(mockCryptoData);
    updateMarketOverview(mockCryptoData);
}

function updateCryptoTable(data) {
    const tableBody = document.getElementById('crypto-table-body');
    const currency = document.getElementById('currency-selector').value;
    
    // Clear existing data
    tableBody.innerHTML = '';
    
    data.forEach((crypto, index) => {
        const row = document.createElement('tr');
        row.classList.add('crypto-row');
        row.setAttribute('data-id', crypto.id);
        
        const price = formatCurrency(crypto.current_price[currency.toLowerCase()], currency);
        const marketCap = formatCurrency(crypto.market_cap[currency.toLowerCase()], currency, true);
        const volume = formatCurrency(crypto.total_volume[currency.toLowerCase()], currency, true);
        
        const change24h = crypto.price_change_percentage_24h.toFixed(2);
        const change7d = crypto.price_change_percentage_7d.toFixed(2);
        
        const change24hTrend = crypto.price_change_percentage_24h >= 0 ? 'up' : 'down';
        const change7dTrend = crypto.price_change_percentage_7d >= 0 ? 'up' : 'down';
        
        const change24hSign = crypto.price_change_percentage_24h >= 0 ? '+' : '';
        const change7dSign = crypto.price_change_percentage_7d >= 0 ? '+' : '';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td class="crypto-name">
                <img src="../../assets/images/crypto/${crypto.symbol.toLowerCase()}.png" alt="${crypto.name}" class="crypto-icon" onerror="this.src='../../assets/images/crypto/default.png'">
                <div class="crypto-info">
                    <span class="crypto-fullname">${crypto.name}</span>
                    <span class="crypto-symbol">${crypto.symbol}</span>
                </div>
            </td>
            <td class="crypto-price">${price}</td>
            <td class="crypto-change-24h" data-trend="${change24hTrend}">${change24hSign}${change24h}%</td>
            <td class="crypto-change-7d" data-trend="${change7dTrend}">${change7dSign}${change7d}%</td>
            <td class="crypto-market-cap">${marketCap}</td>
            <td class="crypto-volume">${volume}</td>
            <td class="crypto-actions">
                <button class="btn btn-icon btn-add-watchlist" title="Add to Watchlist">
                    <span class="icon-star-outline"></span>
                </button>
                <button class="btn btn-icon btn-set-alert" title="Set Price Alert">
                    <span class="icon-bell"></span>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Update timestamp
    const now = new Date();
    document.getElementById('data-last-updated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

function updateMarketOverview(data) {
    // Calculate market metrics
    let totalMarketCap = 0;
    let totalVolume = 0;
    
    data.forEach(crypto => {
        totalMarketCap += crypto.market_cap.usd;
        totalVolume += crypto.total_volume.usd;
    });
    
    // Update market cap
    const marketCap = formatCurrency(totalMarketCap, 'USD', true);
    document.getElementById('global-market-cap').textContent = marketCap;
    
    // Update 24h volume
    const volume = formatCurrency(totalVolume, 'USD', true);
    document.getElementById('global-volume').textContent = volume;
    
    // Mock data for BTC dominance and market cap change
    const btcDominance = '42.8%';
    const marketCapChange = '+1.8%';
    
    document.getElementById('btc-dominance').textContent = btcDominance;
    document.getElementById('market-cap-change').textContent = marketCapChange;
    document.getElementById('market-cap-change').setAttribute('data-trend', 'up');
    
    // Mock data for fear & greed index
    const fearGreedValue = 65;
    let fearGreedLabel = 'Neutral';
    let fearGreedLevel = 'neutral';
    
    if (fearGreedValue <= 25) {
        fearGreedLabel = 'Fear';
        fearGreedLevel = 'fear';
    } else if (fearGreedValue >= 75) {
        fearGreedLabel = 'Greed';
        fearGreedLevel = 'greed';
    }
    
    document.getElementById('fear-greed-value').textContent = fearGreedValue;
    document.getElementById('fear-greed-label').textContent = fearGreedLabel;
    document.getElementById('fear-greed-value').setAttribute('data-level', fearGreedLevel);
}

/**
 * Charts initialization and functionality
 */
function initCharts() {
    // In a real implementation, we would use chart.js, apexcharts, or a similar library
    initPriceChart();
    initPredictionCharts();
    initSentimentChart();
    initDetailChart('bitcoin'); // Initialize detail chart with default coin
}

function initPriceChart() {
    // Remove chart placeholder
    const placeholder = document.querySelector('.chart-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    
    // Here, you would initialize your charting library
    console.log('Price chart initialized');
    
    // Example with Chart.js (uncomment if using Chart.js):
    /*
    const ctx = document.getElementById('price-chart').getContext('2d');
    const priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: generateDateLabels(30), // Last 30 days
            datasets: [{
                label: 'Bitcoin Price',
                data: generatePriceData(30, 55000, 58000),
                borderColor: '#2563eb',
                tension: 0.4,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `$${context.raw.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    */
}

function initPredictionCharts() {
    // Here, you would initialize prediction charts
    console.log('Prediction charts initialized');
}

function initSentimentChart() {
    // Here, you would initialize sentiment distribution chart
    console.log('Sentiment chart initialized');
}

function initDetailChart(coinId) {
    // Here, you would initialize detail chart in modal
    console.log(`Detail chart for ${coinId} initialized`);
}

function updateChartTimeRange(timeRange) {
    console.log(`Updating chart to ${timeRange} timeframe`);
    // Here, you would update the chart data based on the selected time range
}

function updateChartType(chartType) {
    console.log(`Switching to ${chartType} chart type`);
    // Here, you would update the chart type
}

/**
 * Tab navigation functionality
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the tab to show
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Add active class to current tab and button
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });
}

/**
 * Modal functionality
 */
function initModals() {
    // Alert Modal
    const createAlertBtn = document.getElementById('create-alert');
    const createFirstAlertBtn = document.getElementById('create-first-alert');
    const closeAlertModalBtn = document.getElementById('close-alert-modal');
    const cancelAlertBtn = document.getElementById('cancel-alert');
    const saveAlertBtn = document.getElementById('save-alert');
    const createAlertModal = document.getElementById('create-alert-modal');
    
    if (createAlertBtn) {
        createAlertBtn.addEventListener('click', function() {
            openCreateAlertModal();
        });
    }
    
    if (createFirstAlertBtn) {
        createFirstAlertBtn.addEventListener('click', function() {
            openCreateAlertModal();
        });
    }
    
    if (closeAlertModalBtn) {
        closeAlertModalBtn.addEventListener('click', function() {
            createAlertModal.classList.remove('active');
        });
    }
    
    if (cancelAlertBtn) {
        cancelAlertBtn.addEventListener('click', function() {
            createAlertModal.classList.remove('active');
        });
    }
    
    if (saveAlertBtn) {
        saveAlertBtn.addEventListener('click', function() {
            saveAlert();
            createAlertModal.classList.remove('active');
        });
    }
    
    // Crypto Details Modal
    const closeDetailsModalBtn = document.getElementById('close-details-modal');
    const detailsModal = document.getElementById('crypto-details-modal');
    const addToWatchlistBtn = document.getElementById('add-to-watchlist-btn');
    const setPriceAlertBtn = document.getElementById('set-price-alert-btn');
    
    if (closeDetailsModalBtn) {
        closeDetailsModalBtn.addEventListener('click', function() {
            detailsModal.classList.remove('active');
        });
    }
    
    if (addToWatchlistBtn) {
        addToWatchlistBtn.addEventListener('click', function() {
            const coinId = detailsModal.getAttribute('data-coin-id');
            toggleWatchlistCoin(coinId);
            detailsModal.classList.remove('active');
        });
    }
    
    if (setPriceAlertBtn) {
        setPriceAlertBtn.addEventListener('click', function() {
            const coinId = detailsModal.getAttribute('data-coin-id');
            detailsModal.classList.remove('active');
            openCreateAlertModal(coinId);
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === createAlertModal) {
            createAlertModal.classList.remove('active');
        }
        
        if (event.target === detailsModal) {
            detailsModal.classList.remove('active');
        }
    });
}

function openCreateAlertModal(coinId = null) {
    const modal = document.getElementById('create-alert-modal');
    const coinSelect = document.getElementById('alert-coin');
    
    // Reset form
    document.getElementById('alert-form').reset();
    
    // Pre-select coin if provided
    if (coinId && coinSelect) {
        coinSelect.value = coinId;
    }
    
    // Update value currency based on selected currency
    const currency = document.getElementById('currency-selector').value;
    if (document.getElementById('value-currency')) {
        document.getElementById('value-currency').textContent = currency;
    }
    
    // Show modal
    modal.classList.add('active');
}

function openCryptoDetailsModal(coinId) {
    const modal = document.getElementById('crypto-details-modal');
    
    // Set coin ID attribute
    modal.setAttribute('data-coin-id', coinId);
    
    // Fetch coin details (mock data for now)
    const coinDetails = getCoinDetails(coinId);
    
    // Update modal with coin details
    document.getElementById('detail-crypto-name').textContent = `${coinDetails.name} (${coinDetails.symbol})`;
    document.getElementById('detail-current-price').textContent = formatCurrency(coinDetails.current_price.kes, 'KES');
    
    const priceChange = coinDetails.price_change_percentage_24h;
    const priceChangeSign = priceChange >= 0 ? '+' : '';
    const priceTrend = priceChange >= 0 ? 'up' : 'down';
    
    document.getElementById('detail-price-change').textContent = `${priceChangeSign}${priceChange.toFixed(2)}%`;
    document.getElementById('detail-price-change').setAttribute('data-trend', priceTrend);
    
    document.getElementById('detail-24h-high').textContent = formatCurrency(coinDetails.high_24h.kes, 'KES');
    document.getElementById('detail-24h-low').textContent = formatCurrency(coinDetails.low_24h.kes, 'KES');
    document.getElementById('detail-ath').textContent = formatCurrency(coinDetails.ath.kes, 'KES');
    
    document.getElementById('detail-market-cap').textContent = formatCurrency(coinDetails.market_cap.kes, 'KES', true);
    document.getElementById('detail-volume').textContent = formatCurrency(coinDetails.total_volume.kes, 'KES', true);
    document.getElementById('detail-supply').textContent = `${formatNumber(coinDetails.circulating_supply)} ${coinDetails.symbol}`;
    document.getElementById('detail-max-supply').textContent = coinDetails.max_supply ? 
        `${formatNumber(coinDetails.max_supply)} ${coinDetails.symbol}` : 'Unlimited';
    
    // Update AI analysis
    document.getElementById('detail-ai-analysis').innerHTML = `<p>${coinDetails.ai_analysis}</p>`;
    
    // Initialize chart
    initDetailChart(coinId);
    
    // Show modal
    modal.classList.add('active');
}

function getCoinDetails(coinId) {
    // Mock data for coin details
    const mockCoinDetails = {
        bitcoin: {
            id: 'bitcoin',
            name: 'Bitcoin',
            symbol: 'BTC',
            current_price: {
                kes: 6500000,
                usd: 57000,
                eur: 52000
            },
            price_change_percentage_24h: 2.5,
            high_24h: {
                kes: 6550000,
                usd: 57400,
                eur: 52300
            },
            low_24h: {
                kes: 6350000,
                usd: 55650,
                eur: 50700
            },
            ath: {
                kes: 7800000,
                usd: 69000,
                eur: 63000
            },
            market_cap: {
                kes: 123400000000000,
                usd: 1080000000000,
                eur: 984000000000
            },
            total_volume: {
                kes: 5670000000000,
                usd: 49700000000,
                eur: 45200000000
            },
            circulating_supply: 19230000,
            max_supply: 21000000,
            ai_analysis: 'Bitcoin is showing strong bullish momentum with increasing institutional adoption. Technical indicators suggest continued upward movement with resistance at KES 6,800,000. Trading volumes have increased by 15% in the last 24 hours, indicating growing market interest.'
        },
        ethereum: {
            id: 'ethereum',
            name: 'Ethereum',
            symbol: 'ETH',
            current_price: {
                kes: 345000,
                usd: 3020,
                eur: 2750
            },
            price_change_percentage_24h: 1.8,
            high_24h: {
                kes: 350000,
                usd: 3065,
                eur: 2790
            },
            low_24h: {
                kes: 338000,
                usd: 2960,
                eur: 2695
            },
            ath: {
                kes: 512000,
                usd: 4480,
                eur: 4080
            },
            market_cap: {
                kes: 41500000000000,
                usd: 363000000000,
                eur: 330000000000
            },
            total_volume: {
                kes: 1680000000000,
                usd: 14700000000,
                eur: 13400000000
            },
            circulating_supply: 120200000,
            max_supply: null,
            ai_analysis: 'Ethereum has been consolidating above KES 340,000 with growing network activity. The upcoming protocol upgrades and increased institutional interest provide a positive outlook. Watch for a potential breakout if it maintains support at current levels.'
        },
        solana: {
            id: 'solana',
            name: 'Solana',
            symbol: 'SOL',
            current_price: {
                kes: 138000,
                usd: 1210,
                eur: 1100
            },
            price_change_percentage_24h: 4.2,
            high_24h: {
                kes: 142000,
                usd: 1245,
                eur: 1133
            },
            low_24h: {
                kes: 132500,
                usd: 1160,
                eur: 1055
            },
            ath: {
                kes: 295000,
                usd: 2580,
                eur: 2350
            },
            market_cap: {
                kes: 6650000000000,
                usd: 58200000000,
                eur: 53000000000
            },
            total_volume: {
                kes: 980000000000,
                usd: 8580000000,
                eur: 7800000000
            },
            circulating_supply: 48200000,
            max_supply: null,
            ai_analysis: 'Solana continues to show strong performance with growing institutional adoption for its high-speed infrastructure. The recent bullish trend is supported by increased DApp development and NFT activity on the platform.'
        },
        cardano: {
            id: 'cardano',
            name: 'Cardano',
            symbol: 'ADA',
            current_price: {
                kes: 6270,
                usd: 55,
                eur: 50
            },
            price_change_percentage_24h: -0.8,
            high_24h: {
                kes: 6330,
                usd: 55.5,
                eur: 50.5
            },
            low_24h: {
                kes: 6100,
                usd: 53.5,
                eur: 48.7
            },
            ath: {
                kes: 38000,
                usd: 333,
                eur: 303
            },
            market_cap: {
                kes: 2195000000000,
                usd: 19200000000,
                eur: 17500000000
            },
            total_volume: {
                kes: 57000000000,
                usd: 500000000,
                eur: 455000000
            },
            circulating_supply: 35000000000,
            max_supply: 45000000000,
            ai_analysis: 'Cardano is consolidating at current levels while continuing to roll out its development roadmap. The recent smart contract upgrades provide a foundation for increased DeFi activity, which could drive future price action.'
        },
        ripple: {
            id: 'ripple',
            name: 'XRP',
            symbol: 'XRP',
            current_price: {
                kes: 6840,
                usd: 60,
                eur: 54.5
            },
            price_change_percentage_24h: 0.5,
            high_24h: {
                kes: 6900,
                usd: 60.5,
                eur: 55
            },
            low_24h: {
                kes: 6780,
                usd: 59.5,
                eur: 54
            },
            ath: {
                kes: 39900,
                usd: 350,
                eur: 318
            },
            market_cap: {
                kes: 3420000000000,
                usd: 30000000000,
                eur: 27300000000
            },
            total_volume: {
                kes: 114000000000,
                usd: 1000000000,
                eur: 910000000
            },
            circulating_supply: 50000000000,
            max_supply: 100000000000,
            ai_analysis: 'XRP price action has been relatively stable as the market waits for further regulatory clarity. Long-term outlook remains tied to adoption of Ripple technology in the banking sector and outcomes of ongoing legal proceedings.'
        }
    };
    
    // Return data for requested coin or bitcoin as fallback
    return mockCoinDetails[coinId] || mockCoinDetails.bitcoin;
}

/**
 * Price Alerts functionality
 */
function initPriceAlerts() {
    const alertsContainer = document.getElementById('alerts-container');
    
    if (alertsContainer) {
        // Event delegation for alert actions
        alertsContainer.addEventListener('click', function(e) {
            const target = e.target;
            
            // Edit alert
            if (target.closest('.btn-edit-alert')) {
                const alertId = target.closest('.alert-card').getAttribute('data-id');
                editAlert(alertId);
            }
            
            // Delete alert
            if (target.closest('.btn-delete-alert')) {
                const alertId = target.closest('.alert-card').getAttribute('data-id');
                deleteAlert(alertId);
            }
        });
    }
}

function saveAlert() {
    const alertForm = document.getElementById('alert-form');
    const coin = document.getElementById('alert-coin').value;
    const condition = document.getElementById('alert-condition').value;
    const value = document.getElementById('alert-value').value;
    const notifyPush = document.getElementById('notify-push').checked;
    const notifyEmail = document.getElementById('notify-email').checked;
    const notifySms = document.getElementById('notify-sms').checked;
    
    // Validate form
    if (!coin || !condition || !value) {
        alert('Please fill in all required fields');
        return;
    }
    
    // Get coin details
    const coinDetails = getCoinDetails(coin);
    
    // Create alert ID
    const alertId = `alert-${Date.now()}`;
    
    // Create notification methods string
    let notificationMethods = [];
    if (notifyPush) notificationMethods.push('Push');
    if (notifyEmail) notificationMethods.push('Email');
    if (notifySms) notificationMethods.push('SMS');
    
    // Format condition text
    let conditionText = '';
    switch(condition) {
        case 'price_above':
            conditionText = 'Price rises above';
            break;
        case 'price_below':
            conditionText = 'Price drops below';
            break;
        case 'percent_increase':
            conditionText = 'Increases by';
            break;
        case 'percent_decrease':
            conditionText = 'Decreases by';
            break;
    }
    
    // Format value
    let formattedValue = '';
    if (condition === 'percent_increase' || condition === 'percent_decrease') {
        formattedValue = `${value}%`;
    } else {
        const currency = document.getElementById('currency-selector').value;
        formattedValue = formatCurrency(parseFloat(value), currency);
    }
    
    // Create alert HTML
    const alertHTML = `
        <div class="alert-card" data-id="${alertId}">
            <div class="alert-header">
                <div class="alert-coin">
                    <img src="../../assets/images/crypto/${coinDetails.symbol.toLowerCase()}.png" alt="${coinDetails.name}" class="alert-coin-icon" onerror="this.src='../../assets/images/crypto/default.png'">
                    <span class="alert-coin-name">${coinDetails.name} (${coinDetails.symbol})</span>
                </div>
                <div class="alert-actions">
                    <button class="btn btn-icon btn-edit-alert" title="Edit Alert">
                        <span class="icon-edit"></span>
                    </button>
                    <button class="btn btn-icon btn-delete-alert" title="Delete Alert">
                        <span class="icon-delete"></span>
                    </button>
                </div>
            </div>
            <div class="alert-details">
                <div class="alert-condition">
                    <span class="condition-type">${conditionText}</span>
                    <span class="condition-value">${formattedValue}</span>
                </div>
                <div class="alert-notification-method">
                    <span class="icon-notification"></span>
                    <span>${notificationMethods.join(' & ') || 'None'}</span>
                </div>
            </div>
            <div class="alert-status active">
                <span class="status-indicator"></span>
                <span class="status-text">Active</span>
            </div>
        </div>
    `;
    
    // Add alert to container
    const alertsContainer = document.getElementById('alerts-container');
    const noAlertsMessage = document.getElementById('no-alerts');
    
    // First hide the "no alerts" message if it's showing
    if (noAlertsMessage) {
        noAlertsMessage.style.display = 'none';
    }
    
    // Insert new alert at the beginning
    alertsContainer.insertAdjacentHTML('afterbegin', alertHTML);
    
    // Show success message
    showToast('Price alert created successfully');
}

function editAlert(alertId) {
    // In a real implementation, we would load the alert data and open the edit modal
    console.log(`Editing alert: ${alertId}`);
    
    // For now, just open the create alert modal
    openCreateAlertModal();
}

function deleteAlert(alertId) {
    // Confirm deletion
    if (confirm('Are you sure you want to delete this alert?')) {
        // Remove alert from DOM
        const alertCard = document.querySelector(`.alert-card[data-id="${alertId}"]`);
        if (alertCard) {
            alertCard.remove();
        }
        
        // Check if we have any alerts left
        const alertsContainer = document.getElementById('alerts-container');
        const noAlertsMessage = document.getElementById('no-alerts');
        
        if (alertsContainer && noAlertsMessage && alertsContainer.querySelectorAll('.alert-card').length === 0) {
            noAlertsMessage.style.display = 'flex';
        }
        
        // Show success message
        showToast('Price alert deleted');
    }
}

/**
 * Time range selection functionality
 */
function initTimeRangeSelection() {
    const timeRangeButtons = document.querySelectorAll('.time-range-buttons .btn');
    
    timeRangeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            timeRangeButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get selected time range
            const timeRange = this.getAttribute('data-range');
            
            // Update chart with selected time range
            updateChartTimeRange(timeRange);
        });
    });
}

/**
 * Chart type selection functionality
 */
function initChartTypeSelection() {
    const lineChartBtn = document.getElementById('line-chart-btn');
    const candleChartBtn = document.getElementById('candle-chart-btn');
    
    if (lineChartBtn && candleChartBtn) {
        lineChartBtn.addEventListener('click', function() {
            lineChartBtn.classList.add('active');
            candleChartBtn.classList.remove('active');
            updateChartType('line');
        });
        
        candleChartBtn.addEventListener('click', function() {
            candleChartBtn.classList.add('active');
            lineChartBtn.classList.remove('active');
            updateChartType('candlestick');
        });
    }
}

/**
 * Technical indicators functionality
 */
function initTechnicalIndicators() {
    const indicatorToggles = document.querySelectorAll('.indicator-toggle input');
    
    indicatorToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const indicator = this.id.replace('toggle-', '');
            const enabled = this.checked;
            
            toggleTechnicalIndicator(indicator, enabled);
        });
    });
}

function toggleTechnicalIndicator(indicator, enabled) {
    console.log(`${enabled ? 'Showing' : 'Hiding'} ${indicator} indicator`);
    // In a real implementation, we would update the chart to show/hide indicators
}

/**
 * Utility functions
 */
function formatCurrency(value, currency, compact = false) {
    const currencySymbol = {
        'KES': 'KES',
        'USD': '$',
        'EUR': '€'
    };
    
    let formattedValue;
    
    if (compact) {
        // Format with K, M, B, T for large numbers
        const tier = Math.log10(Math.abs(value)) / 3 | 0;
        if (tier === 0) {
            formattedValue = value;
        } else {
            const suffix = ['', 'K', 'M', 'B', 'T'][tier];
            const scale = Math.pow(10, tier * 3);
            const scaled = value / scale;
            formattedValue = scaled.toFixed(1) + suffix;
        }
    } else {
        // Standard formatting with commas
        formattedValue = value.toLocaleString();
    }
    
    return `${currencySymbol[currency]} ${formattedValue}`;
}

function formatNumber(value, compact = false) {
    if (value === null) {
        return 'Unlimited';
    }
    
    if (compact) {
        // Format with K, M, B, T for large numbers
        const tier = Math.log10(Math.abs(value)) / 3 | 0;
        if (tier === 0) {
            return value.toLocaleString();
        } else {
            const suffix = ['', 'K', 'M', 'B', 'T'][tier];
            const scale = Math.pow(10, tier * 3);
            const scaled = value / scale;
            return scaled.toFixed(1) + suffix;
        }
    } else {
        // Standard formatting with commas
        return value.toLocaleString();
    }
}

function showToast(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.classList.add('toast');
    toast.textContent = message;
    
    // Add toast to body
    document.body.appendChild(toast);
    
    // Show toast
    setTimeout(() => {
        toast.classList.add('show');
        
        // Hide and remove toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }, 100);
}

/**
 * Action handlers
 */
function toggleWatchlistCoin(coinId, button = null) {
    console.log(`Toggle ${coinId} in watchlist`);
    
    // In a real implementation, we would add/remove the coin from the user's watchlist
    // For now, just toggle the button icon
    if (button) {
        const iconSpan = button.querySelector('span');
        
        if (iconSpan.classList.contains('icon-star-outline')) {
            iconSpan.classList.remove('icon-star-outline');
            iconSpan.classList.add('icon-star');
            button.setAttribute('title', 'Remove from Watchlist');
            showToast(`Added ${getCoinDetails(coinId).name} to watchlist`);
        } else {
            iconSpan.classList.remove('icon-star');
            iconSpan.classList.add('icon-star-outline');
            button.setAttribute('title', 'Add to Watchlist');
            showToast(`Removed ${getCoinDetails(coinId).name} from watchlist`);
        }
    }
}

function toggleWatchlist() {
    console.log('Toggling between all coins and watchlist');
    
    const watchlistButton = document.getElementById('watchlist-button');
    const iconSpan = watchlistButton.querySelector('span');
    
    if (iconSpan.classList.contains('icon-star-outline')) {
        iconSpan.classList.remove('icon-star-outline');
        iconSpan.classList.add('icon-star');
        watchlistButton.textContent = ' All Coins';
        watchlistButton.prepend(iconSpan);
        
        // In a real implementation, we would filter the table to show only watchlisted coins
        showToast('Showing watchlist only');
    } else {
        iconSpan.classList.remove('icon-star');
        iconSpan.classList.add('icon-star-outline');
        watchlistButton.textContent = ' My Watchlist';
        watchlistButton.prepend(iconSpan);
        
        // In a real implementation, we would show all coins
        showToast('Showing all coins');
    }
}

function loadMoreCryptos() {
    console.log('Loading more cryptocurrencies');
    
    // In a real implementation, we would fetch more cryptocurrency data
    // For now, just show a toast
    showToast('Loading more cryptocurrencies...');
    
    // Simulate loading delay
    setTimeout(() => {
        // Add more mock data to the table
        const mockAdditionalData = [
            {
                id: 'binancecoin',
                name: 'Binance Coin',
                symbol: 'BNB',
                current_price: {
                    kes: 57000,
                    usd: 500,
                    eur: 455
                },
                price_change_percentage_24h: 0.3,
                price_change_percentage_7d: 2.8,
                market_cap: {
                    kes: 9500000000000,
                    usd: 83000000000,
                    eur: 75500000000
                },
                total_volume: {
                    kes: 342000000000,
                    usd: 3000000000,
                    eur: 2730000000
                }
            },
            {
                id: 'polkadot',
                name: 'Polkadot',
                symbol: 'DOT',
                current_price: {
                    kes: 912,
                    usd: 8,
                    eur: 7.3
                },
                price_change_percentage_24h: -1.2,
                price_change_percentage_7d: -3.5,
                market_cap: {
                    kes: 1140000000000,
                    usd: 10000000000,
                    eur: 9100000000
                },
                total_volume: {
                    kes: 45600000000,
                    usd: 400000000,
                    eur: 364000000
                }
            }
        ];
        
        // Get existing data and add new data
        const tableBody = document.getElementById('crypto-table-body');
        const existingRowCount = tableBody.querySelectorAll('tr').length;
        
        const currency = document.getElementById('currency-selector').value;
        
        mockAdditionalData.forEach((crypto, index) => {
            const row = document.createElement('tr');
            row.classList.add('crypto-row');
            row.setAttribute('data-id', crypto.id);
            
            const price = formatCurrency(crypto.current_price[currency.toLowerCase()], currency);
            const marketCap = formatCurrency(crypto.market_cap[currency.toLowerCase()], currency, true);
            const volume = formatCurrency(crypto.total_volume[currency.toLowerCase()], currency, true);
            
            const change24h = crypto.price_change_percentage_24h.toFixed(2);
            const change7d = crypto.price_change_percentage_7d.toFixed(2);
            
            const change24hTrend = crypto.price_change_percentage_24h >= 0 ? 'up' : 'down';
            const change7dTrend = crypto.price_change_percentage_7d >= 0 ? 'up' : 'down';
            
            const change24hSign = crypto.price_change_percentage_24h >= 0 ? '+' : '';
            const change7dSign = crypto.price_change_percentage_7d >= 0 ? '+' : '';
            
            row.innerHTML = `
                <td>${existingRowCount + index + 1}</td>
                <td class="crypto-name">
                    <img src="../../assets/images/crypto/${crypto.symbol.toLowerCase()}.png" alt="${crypto.name}" class="crypto-icon" onerror="this.src='../../assets/images/crypto/default.png'">
                    <div class="crypto-info">
                        <span class="crypto-fullname">${crypto.name}</span>
                        <span class="crypto-symbol">${crypto.symbol}</span>
                    </div>
                </td>
                <td class="crypto-price">${price}</td>
                <td class="crypto-change-24h" data-trend="${change24hTrend}">${change24hSign}${change24h}%</td>
                <td class="crypto-change-7d" data-trend="${change7dTrend}">${change7dSign}${change7d}%</td>
                <td class="crypto-market-cap">${marketCap}</td>
                <td class="crypto-volume">${volume}</td>
                <td class="crypto-actions">
                    <button class="btn btn-icon btn-add-watchlist" title="Add to Watchlist">
                        <span class="icon-star-outline"></span>
                    </button>
                    <button class="btn btn-icon btn-set-alert" title="Set Price Alert">
                        <span class="icon-bell"></span>
                    </button>
                </td>
            `;
            
            tableBody.appendChild(row);
        });
        
        showToast('Loaded 2 more cryptocurrencies');
    }, 1000);
}

function changeCurrency() {
    const currency = document.getElementById('currency-selector').value;
    console.log(`Changing currency to ${currency}`);
    
    // In a real implementation, we would update all price displays
    // For now, just refresh the data
    fetchCryptoData();
    
    // Show toast
    showToast(`Currency changed to ${currency}`);
}

function changeRegion() {
    const region = document.getElementById('region-selector').value;
    console.log(`Changing region to ${region}`);
    
    // In a real implementation, we would update the regulation updates
    // For now, just show a toast
    showToast(`Region changed to ${region}`);
}

function refreshData() {
    console.log('Refreshing all data');
    
    // Show loading indication
    showToast('Refreshing data...');
    
    // In a real implementation, we would refresh all data
    // For now, just simulate a delay and refresh
    setTimeout(() => {
        fetchCryptoData();
        initCharts();
        updateNotificationCount();
        showToast('Data refreshed successfully');
    }, 1000);
}

function refreshInsights() {
    console.log('Refreshing AI insights');
    
    // Show loading indication
    showToast('Refreshing AI insights...');
    
    // In a real implementation, we would refresh the AI insights
    // For now, just simulate a delay
    setTimeout(() => {
        initPredictionCharts();
        initSentimentChart();
        showToast('AI insights refreshed successfully');
    }, 1000);
}

function openChatbot() {
    console.log('Opening chatbot');
    
    // In a real implementation, we would open the chatbot
    // For now, just show a toast
    showToast('Opening PesaGuru chatbot...');
    
    // Simulate redirect
    setTimeout(() => {
        window.location.href = '../Chatbot_Interaction/chatbot.html';
    }, 1000);
}

// Add this CSS for toast notifications
(function addToastStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background-color: var(--primary-color);
            color: white;
            padding: 12px 20px;
            border-radius: var(--border-radius-md);
            box-shadow: var(--shadow-md);
            z-index: 9999;
            transform: translateY(100px);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .dark-theme .toast {
            background-color: var(--primary-dark);
        }
    `;
    document.head.appendChild(style);
})();