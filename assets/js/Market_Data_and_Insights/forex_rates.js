// Use strict mode for better error handling and performance
'use strict';

// Main PesaGuru Forex application namespace
const PesaGuru = {
  // Configuration
  config: {
    apiBaseUrl: '/api',
    refreshInterval: 300000, // 5 minutes
    cacheExpiry: 600000, // 10 minutes
    defaultCurrency: 'USD',
    chartTimeframes: {
      '1D': 1,
      '1W': 7,
      '1M': 30,
      '3M': 90, 
      '6M': 180,
      '1Y': 365
    },
    colors: {
      primary: '#2c6ecb',
      secondary: '#f5b942',
      positive: '#34a853',
      negative: '#ea4335',
      neutral: '#fbbc05'
    }
  },
  
  // State management
  state: {
    lastUpdated: null,
    cache: new Map(),
    activeCurrency: 'USD-KES',
    activeTimeframe: '1M',
    charts: {},
    alertsEnabled: false,
    userPreferences: {},
    isLoading: false,
    offline: false
  },
  
  // Initialization function
  init() {
    // Check browser support
    this.checkBrowserSupport();
    
    // Load user preferences from localStorage
    this.loadUserPreferences();
    
    // Initialize components
    this.initComponents()
      .then(() => {
        console.log('PesaGuru Forex dashboard initialized successfully');
        this.showToast('Dashboard loaded successfully', 'success');
      })
      .catch(error => {
        console.error('Failed to initialize PesaGuru dashboard:', error);
        this.showToast('Failed to initialize dashboard. Please refresh the page.', 'error');
      });
      
    // Setup offline handling
    this.setupOfflineHandler();
    
    // Setup automatic refresh
    this.setupAutoRefresh();
  },
  
  // Check browser support for required features
  checkBrowserSupport() {
    if (!window.localStorage || !window.fetch) {
      this.showUnsupportedBrowserMessage();
    }
  },
  
  // Initialize all components
  async initComponents() {
    // Show loading state
    this.setLoading(true);
    
    try {
      // Initialize all UI components in parallel
      await Promise.all([
        this.currencyConverter.init(),
        this.forexTable.init(),
        this.forexChart.init(),
        this.aiInsights.init(),
        this.alertSystem.init(),
        this.economicCalendar.init(),
        this.forexNews.init(),
        this.tradingSignals.init(),
        this.pythonIntegration.init()
      ]);
      
      // Set up event listeners for global components
      this.setupEventListeners();
      
      // Update last updated timestamp
      this.updateLastUpdatedTime();
    } catch (error) {
      console.error('Component initialization error:', error);
      throw new Error('Failed to initialize one or more components');
    } finally {
      // Hide loading state
      this.setLoading(false);
    }
  },
  
  // Set up event listeners
  setupEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshAllData());
    }
    
    // Theme toggle if present
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    // Chat button
    const openChatButton = document.getElementById('open-chat');
    if (openChatButton) {
      openChatButton.addEventListener('click', () => {
        window.location.href = '../Chatbot_Interaction/chatbot.html';
      });
    }
    
    // Handle visibility change to refresh data when tab becomes visible
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && 
          this.state.lastUpdated && 
          (Date.now() - this.state.lastUpdated > this.config.refreshInterval)) {
        this.refreshAllData();
      }
    });
    
    // Window resize event for responsive adjustments
    window.addEventListener('resize', this.utils.debounce(() => {
      if (this.state.charts.forexChart) {
        this.state.charts.forexChart.resize();
      }
    }, 250));
  },
  
  // Set up automatic refresh
  setupAutoRefresh() {
    setInterval(() => {
      // Only refresh if the page is visible and not already loading
      if (document.visibilityState === 'visible' && !this.state.isLoading) {
        this.refreshAllData();
      }
    }, this.config.refreshInterval);
  },
  
  // Set up offline detection
  setupOfflineHandler() {
    window.addEventListener('online', () => {
      this.state.offline = false;
      this.showToast('Back online! Refreshing data...', 'success');
      this.refreshAllData();
    });
    
    window.addEventListener('offline', () => {
      this.state.offline = true;
      this.showToast('You are offline. Some features may be unavailable.', 'warning', 0);
    });
  },
  
  // Refresh all data
  async refreshAllData() {
    if (this.state.isLoading) return;
    
    // Set loading state
    this.setLoading(true);
    
    // Add refresh animation to button
    const refreshButton = document.getElementById('refresh-data');
    if (refreshButton) {
      refreshButton.classList.add('refreshing');
      refreshButton.setAttribute('disabled', 'true');
    }
    
    try {
      // Clear cache
      this.state.cache.clear();
      
      // Refresh all components in parallel
      await Promise.all([
        this.forexTable.refresh(),
        this.forexChart.refresh(),
        this.aiInsights.refresh(),
        this.forexNews.refresh(),
        this.tradingSignals.refresh(),
        this.economicCalendar.refresh()
      ]);
      
      // Update last updated time
      this.updateLastUpdatedTime();
      
      this.showToast('Data refreshed successfully', 'success');
    } catch (error) {
      console.error('Error refreshing data:', error);
      this.showToast('Failed to refresh data. Please try again.', 'error');
    } finally {
      // Remove refresh animation and re-enable button
      if (refreshButton) {
        refreshButton.classList.remove('refreshing');
        refreshButton.removeAttribute('disabled');
      }
      
      // Clear loading state
      this.setLoading(false);
    }
  },
  
  // Set loading state
  setLoading(isLoading) {
    this.state.isLoading = isLoading;
    
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.style.display = isLoading ? 'flex' : 'none';
    }
  },
  
  // Toggle between light and dark theme
  toggleTheme() {
    const body = document.body;
    const isDarkTheme = body.classList.contains('dark-theme');
    
    // Toggle theme class
    body.classList.toggle('dark-theme', !isDarkTheme);
    
    // Save preference
    this.state.userPreferences.darkTheme = !isDarkTheme;
    this.saveUserPreferences();
    
    // Update charts with new theme
    this.forexChart.updateTheme(!isDarkTheme);
    
    this.showToast(`${!isDarkTheme ? 'Dark' : 'Light'} theme activated`, 'info');
  },
  
  // Update last updated time
  updateLastUpdatedTime() {
    const now = new Date();
    this.state.lastUpdated = now.getTime();
    
    const lastUpdateElement = document.getElementById('last-update-time');
    if (lastUpdateElement) {
      lastUpdateElement.textContent = this.utils.formatDateTime(now);
    }
  },
  
  // Show toast notification
  showToast(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container';
      document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas ${this.getIconForToastType(type)}"></i>
        <span>${message}</span>
      </div>
      <button class="toast-close"><i class="fas fa-times"></i></button>
    `;
    
    // Add close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        toast.classList.add('toast-hiding');
        setTimeout(() => {
          toastContainer.removeChild(toast);
        }, 300);
      });
    }
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Auto-remove after duration (if duration > 0)
    if (duration > 0) {
      setTimeout(() => {
        if (document.body.contains(toast)) {
          toast.classList.add('toast-hiding');
          setTimeout(() => {
            if (document.body.contains(toast) && toastContainer.contains(toast)) {
              toastContainer.removeChild(toast);
            }
          }, 300);
        }
      }, duration);
    }
    
    // Add visible class for animation
    setTimeout(() => {
      toast.classList.add('toast-visible');
    }, 10);
    
    return toast;
  },
  
  // Get icon for toast notification type
  getIconForToastType(type) {
    switch (type) {
      case 'success': return 'fa-check-circle';
      case 'error': return 'fa-exclamation-circle';
      case 'warning': return 'fa-exclamation-triangle';
      case 'info':
      default: return 'fa-info-circle';
    }
  },
  
  // Show unsupported browser message
  showUnsupportedBrowserMessage() {
    const content = document.querySelector('.content-wrapper');
    if (content) {
      content.innerHTML = `
        <div class="unsupported-browser">
          <i class="fas fa-exclamation-triangle"></i>
          <h2>Unsupported Browser</h2>
          <p>Your browser does not support some features required by PesaGuru. Please update your browser or try a different one.</p>
          <p>We recommend using the latest version of Chrome, Firefox, Safari, or Edge.</p>
        </div>
      `;
    }
  },
  
  // Save user preferences to localStorage
  saveUserPreferences() {
    try {
      localStorage.setItem('pesaGuruPreferences', JSON.stringify(this.state.userPreferences));
    } catch (error) {
      console.error('Failed to save preferences:', error);
    }
  },
  
  // Load user preferences from localStorage
  loadUserPreferences() {
    try {
      const savedPreferences = localStorage.getItem('pesaGuruPreferences');
      if (savedPreferences) {
        this.state.userPreferences = JSON.parse(savedPreferences);
        
        // Apply theme if saved
        if (this.state.userPreferences.darkTheme) {
          document.body.classList.add('dark-theme');
        }
        
        // Apply other preferences
        if (this.state.userPreferences.currency) {
          this.state.activeCurrency = this.state.userPreferences.currency;
        }
        
        if (this.state.userPreferences.timeframe) {
          this.state.activeTimeframe = this.state.userPreferences.timeframe;
        }
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
      this.state.userPreferences = {};
    }
  },
  
  // =================== DATA SERVICES ===================
  
  dataService: {
    // Fetch data with caching
    async fetchWithCache(endpoint, params = {}, forceRefresh = false) {
      // Create cache key
      const cacheKey = `${endpoint}:${JSON.stringify(params)}`;
      
      // Check if cached and not expired
      if (!forceRefresh && PesaGuru.state.cache.has(cacheKey)) {
        const cachedData = PesaGuru.state.cache.get(cacheKey);
        if (Date.now() - cachedData.timestamp < PesaGuru.config.cacheExpiry) {
          return cachedData.data;
        }
      }
      
      try {
        // If offline, throw error
        if (PesaGuru.state.offline) {
          throw new Error('Cannot fetch data while offline');
        }
        
        // Convert params to query string
        const queryString = Object.keys(params)
          .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
          .join('&');
          
        const url = `${PesaGuru.config.apiBaseUrl}/${endpoint}${queryString ? '?' + queryString : ''}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Cache the result
        PesaGuru.state.cache.set(cacheKey, {
          data,
          timestamp: Date.now()
        });
        
        return data;
      } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        
        // If there's cached data, return it even if expired
        if (PesaGuru.state.cache.has(cacheKey)) {
          const cachedData = PesaGuru.state.cache.get(cacheKey);
          PesaGuru.showToast('Using cached data due to connection issues', 'warning');
          return cachedData.data;
        }
        
        // Otherwise, throw the error
        throw error;
      }
    },
    
    // Fetch forex rates
    async fetchForexRates() {
      // In a real app, this would call a real API endpoint
      // For demo, we'll simulate the response
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            resolve({
              base: 'KES',
              timestamp: Date.now(),
              rates: {
                'USD': 0.00723,
                'EUR': 0.00662,
                'GBP': 0.00562,
                'JPY': 1.084,
                'AED': 0.0266,
                'ZAR': 0.133,
                'CNY': 0.0522,
                'INR': 0.602,
                'UGX': 27.3,
                'TZS': 18.4
              },
              changes: {
                'USD': 0.02, // +2%
                'EUR': -0.01, // -1%
                'GBP': 0.005, // +0.5%
                'JPY': -0.015, // -1.5%
                'AED': 0.01, // +1%
                'ZAR': -0.02, // -2%
                'CNY': 0.003, // +0.3%
                'INR': 0.001, // +0.1% 
                'UGX': -0.005, // -0.5%
                'TZS': 0.01 // +1%
              }
            });
          } catch (error) {
            reject(error);
          }
        }, 500);
      });
    },
    
    // Fetch historical forex data
    async fetchHistoricalRates(currencyPair, timeframe) {
      // In a real app, this would call a real API endpoint
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            // Generate simulated historical data
            const dates = [];
            const rates = [];
            const maRates = [];
            
            const days = PesaGuru.config.chartTimeframes[timeframe] || 30;
            const today = new Date();
            
            // Start with a base rate
            let baseRate = currencyPair.includes('USD') ? 138 : 
                          currencyPair.includes('EUR') ? 151 : 
                          currencyPair.includes('GBP') ? 176 : 92;
            
            for (let i = days; i >= 0; i--) {
              const date = new Date();
              date.setDate(today.getDate() - i);
              dates.push(PesaGuru.utils.formatDate(date, 'short'));
              
              // Simulate some random movement in rates
              const randomChange = (Math.random() - 0.5) * 2;
              baseRate = baseRate + randomChange;
              rates.push(baseRate);
              
              // Calculate 7-day moving average
              if (i <= days - 7) {
                const lastSevenDays = rates.slice(-7);
                const sum = lastSevenDays.reduce((a, b) => a + b, 0);
                maRates.push(sum / 7);
              } else {
                maRates.push(null);
              }
            }
            
            resolve({
              dates: dates,
              rates: rates,
              movingAverage: maRates
            });
          } catch (error) {
            reject(error);
          }
        }, 600);
      });
    },
    
    // Fetch economic calendar events
    async fetchEconomicEvents(date) {
      // In a real app, this would call a real API endpoint
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            resolve([
              {
                time: '10:00 AM',
                country: 'US',
                event: 'Federal Reserve Interest Rate Decision',
                impact: 'high'
              },
              {
                time: '2:30 PM',
                country: 'EU',
                event: 'ECB Economic Bulletin',
                impact: 'medium'
              },
              {
                time: '5:00 PM',
                country: 'KE',
                event: 'Treasury Bill Auction Results',
                impact: 'medium'
              },
              {
                time: '11:45 AM',
                country: 'UK',
                event: 'Manufacturing PMI',
                impact: 'low'
              }
            ]);
          } catch (error) {
            reject(error);
          }
        }, 300);
      });
    },
    
    // Fetch forex news
    async fetchForexNews() {
      // In a real app, this would call a real API endpoint
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            resolve([
              {
                time: '1 hour ago',
                title: 'CBK Holds Key Interest Rate at 9.5% Amid Inflation Concerns',
                summary: 'The Central Bank of Kenya maintained its benchmark interest rate, citing ongoing inflation pressures and volatility in global markets.',
                url: '#',
                source: 'KenyaForex'
              },
              {
                time: '3 hours ago',
                title: 'Kenyan Shilling Strengthens Against Dollar on Improved Exports',
                summary: 'The KES gained 0.8% against the USD following positive export data from the agricultural sector.',
                url: '#',
                source: 'Financial Times'
              },
              {
                time: '5 hours ago',
                title: 'IMF Projects 4.8% Growth for Kenya in 2025',
                summary: 'The International Monetary Fund has revised its economic growth forecast for Kenya, citing improved agricultural output and tourism recovery.',
                url: '#',
                source: 'Reuters'
              },
              {
                time: '1 day ago',
                title: 'East African Community Currency Integration Plans Progress',
                summary: 'The EAC monetary union implementation timeline has been updated, with new targets for regional currency integration.',
                url: '#',
                source: 'East African Business Weekly'
              }
            ]);
          } catch (error) {
            reject(error);
          }
        }, 400);
      });
    },
    
    // Fetch trading signals
    async fetchTradingSignals(timeframe) {
      // In a real app, this would call a real API endpoint
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            resolve([
              {
                pair: 'USD/KES',
                signal: 'BUY',
                direction: 'up',
                strength: 7.5,
                indicators: {
                  rsi: 'positive',
                  macd: 'positive',
                  ema: 'positive',
                  bb: 'neutral'
                }
              },
              {
                pair: 'EUR/KES',
                signal: 'SELL',
                direction: 'down',
                strength: 6.0,
                indicators: {
                  rsi: 'negative',
                  macd: 'negative',
                  ema: 'neutral',
                  bb: 'negative'
                }
              },
              {
                pair: 'GBP/KES',
                signal: 'HOLD',
                direction: 'stable',
                strength: 5.5,
                indicators: {
                  rsi: 'neutral',
                  macd: 'negative',
                  ema: 'positive',
                  bb: 'neutral'
                }
              },
              {
                pair: 'JPY/KES',
                signal: 'BUY',
                direction: 'up',
                strength: 6.8,
                indicators: {
                  rsi: 'positive',
                  macd: 'neutral',
                  ema: 'positive',
                  bb: 'positive'
                }
              }
            ]);
          } catch (error) {
            reject(error);
          }
        }, 450);
      });
    },
    
    // Generate AI market insights
    async generateAIInsights() {
      // In a real app, this would call a real API endpoint
      return new Promise((resolve, reject) => {
        setTimeout(() => {
          try {
            resolve({
              sentiment: 'neutral',
              analysis: 'The Kenyan Shilling is showing moderate stability against major currencies. Recent central bank interventions and steady forex reserves have helped maintain KES at current levels. However, emerging global economic concerns and potential changes in US interest rates may create some volatility in the USD/KES pair in the coming weeks. Exporters should monitor the GBP/KES pair closely as Brexit-related developments continue to affect cross-border trade dynamics.',
              predictions: [
                {
                  pair: 'USD/KES',
                  direction: 'up',
                  value: '+1.2%',
                  confidence: 'Medium',
                  details: 'Expected to rise due to increased import demand and US economic strength'
                },
                {
                  pair: 'EUR/KES',
                  direction: 'down',
                  value: '-0.8%',
                  confidence: 'High',
                  details: 'ECB policy and eurozone inflation concerns weighing on EUR'
                },
                {
                  pair: 'GBP/KES',
                  direction: 'stable',
                  value: '±0.3%',
                  confidence: 'Medium',
                  details: 'Mixed signals from UK economic data offsetting each other'
                },
                {
                  pair: 'JPY/KES',
                  direction: 'up',
                  value: '+0.5%',
                  confidence: 'Low',
                  details: 'Safe-haven flows may strengthen JPY if global volatility increases'
                }
              ],
              riskAnalysis: {
                globalFactors: ['US Federal Reserve policy changes', 'Oil price volatility', 'Global trade tensions'],
                localFactors: ['CBK intervention', 'Export performance', 'Political stability']
              },
              technicalIndicators: {
                'USD/KES': {
                  supportLevels: [130.25, 129.80],
                  resistanceLevels: [132.50, 133.40],
                  trend: 'Upward channel'
                }
              }
            });
          } catch (error) {
            reject(error);
          }
        }, 700);
      });
    }
  },
  
  // =================== CURRENCY CONVERTER MODULE ===================
  
  currencyConverter: {
    // DOM elements
    elements: {
      amountFrom: null,
      currencyFrom: null,
      amountTo: null,
      currencyTo: null,
      swapButton: null,
      fromCurrencyCode: null,
      toCurrencyCode: null,
      conversionRateEl: null,
      bidRateEl: null,
      askRateEl: null
    },
    
    // Initialize currency converter module
    async init() {
      // Get all required DOM elements
      this.elements = {
        amountFrom: document.getElementById('amount-from'),
        currencyFrom: document.getElementById('currency-from'),
        amountTo: document.getElementById('amount-to'),
        currencyTo: document.getElementById('currency-to'),
        swapButton: document.getElementById('swap-currencies'),
        fromCurrencyCode: document.getElementById('from-currency-code'),
        toCurrencyCode: document.getElementById('to-currency-code'),
        conversionRateEl: document.getElementById('conversion-rate'),
        bidRateEl: document.getElementById('bid-rate'),
        askRateEl: document.getElementById('ask-rate')
      };
      
      // Set default values from user preferences
      if (PesaGuru.state.userPreferences.lastConversion) {
        const lastConversion = PesaGuru.state.userPreferences.lastConversion;
        
        if (this.elements.currencyFrom && lastConversion.from) {
          this.elements.currencyFrom.value = lastConversion.from;
        }
        
        if (this.elements.currencyTo && lastConversion.to) {
          this.elements.currencyTo.value = lastConversion.to;
        }
        
        if (this.elements.amountFrom && lastConversion.amount) {
          this.elements.amountFrom.value = lastConversion.amount;
        }
      }
      
      // Update currency codes display
      if (this.elements.fromCurrencyCode) {
        this.elements.fromCurrencyCode.textContent = this.elements.currencyFrom.value;
      }
      
      if (this.elements.toCurrencyCode) {
        this.elements.toCurrencyCode.textContent = this.elements.currencyTo.value;
      }
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Do initial conversion
      await this.updateConversionRate();
    },
    
    // Set up event listeners
    setupEventListeners() {
      if (this.elements.amountFrom) {
        this.elements.amountFrom.addEventListener('input', () => this.updateConversion());
      }
      
      if (this.elements.currencyFrom) {
        this.elements.currencyFrom.addEventListener('change', () => {
          if (this.elements.fromCurrencyCode) {
            this.elements.fromCurrencyCode.textContent = this.elements.currencyFrom.value;
          }
          this.updateConversionRate();
          this.saveConversionPreference();
        });
      }
      
      if (this.elements.currencyTo) {
        this.elements.currencyTo.addEventListener('change', () => {
          if (this.elements.toCurrencyCode) {
            this.elements.toCurrencyCode.textContent = this.elements.currencyTo.value;
          }
          this.updateConversionRate();
          this.saveConversionPreference();
        });
      }
      
      if (this.elements.swapButton) {
        this.elements.swapButton.addEventListener('click', () => this.swapCurrencies());
      }
    },
    
    // Save the current conversion preference
    saveConversionPreference() {
      if (!PesaGuru.state.userPreferences) {
        PesaGuru.state.userPreferences = {};
      }
      
      PesaGuru.state.userPreferences.lastConversion = {
        from: this.elements.currencyFrom.value,
        to: this.elements.currencyTo.value,
        amount: this.elements.amountFrom.value
      };
      
      PesaGuru.saveUserPreferences();
    },
    
    // Swap the currencies
    swapCurrencies() {
      const { currencyFrom, currencyTo, fromCurrencyCode, toCurrencyCode } = this.elements;
      
      // Save current values
      const tempCurrency = currencyFrom.value;
      
      // Swap values with animation
      currencyFrom.classList.add('swap-animation');
      currencyTo.classList.add('swap-animation');
      
      setTimeout(() => {
        // Swap the actual values
        currencyFrom.value = currencyTo.value;
        currencyTo.value = tempCurrency;
        
        // Update currency codes display
        fromCurrencyCode.textContent = currencyFrom.value;
        toCurrencyCode.textContent = currencyTo.value;
        
        // Remove animation classes
        currencyFrom.classList.remove('swap-animation');
        currencyTo.classList.remove('swap-animation');
        
        // Update conversion rates
        this.updateConversionRate();
        
        // Save preference
        this.saveConversionPreference();
      }, 300);
    },
    
    // Update conversion rate
    async updateConversionRate() {
      const { currencyFrom, currencyTo, conversionRateEl, bidRateEl, askRateEl } = this.elements;
      
      try {
        // Fetch rates
        const data = await PesaGuru.dataService.fetchForexRates();
        
        let rate;
        
        if (currencyFrom.value === 'KES' && data.rates[currencyTo.value]) {
          // Converting from KES to another currency
          rate = data.rates[currencyTo.value];
        } else if (currencyTo.value === 'KES' && data.rates[currencyFrom.value]) {
          // Converting from another currency to KES
          rate = 1 / data.rates[currencyFrom.value];
        } else if (data.rates[currencyFrom.value] && data.rates[currencyTo.value]) {
          // Cross rate (neither is KES)
          rate = data.rates[currencyTo.value] / data.rates[currencyFrom.value];
        } else {
          rate = 1;
        }
        
        // Add subtle animation to indicate update
        conversionRateEl.classList.add('rate-update');
        setTimeout(() => conversionRateEl.classList.remove('rate-update'), 500);
        
        // Display rate
        conversionRateEl.textContent = rate.toFixed(6);
        
        // Simulated bid/ask spread - in a real app, this would come from the API
        const spread = rate * 0.02; // 2% spread as example
        bidRateEl.textContent = (rate - spread/2).toFixed(6);
        askRateEl.textContent = (rate + spread/2).toFixed(6);
        
        // Update the conversion amount
        this.updateConversion();
      } catch (error) {
        console.error('Error updating conversion rate:', error);
        PesaGuru.showToast('Failed to update conversion rate', 'error');
      }
    },
    
    // Update conversion amount
    updateConversion() {
      const { amountFrom, amountTo, conversionRateEl } = this.elements;
      
      // Get values
      const amount = parseFloat(amountFrom.value) || 0;
      const rate = parseFloat(conversionRateEl.textContent) || 0;
      
      // Calculate conversion
      const convertedAmount = amount * rate;
      
      // Add animation to indicate update
      amountTo.classList.add('amount-update');
      setTimeout(() => amountTo.classList.remove('amount-update'), 500);
      
      // Update output
      amountTo.value = convertedAmount.toFixed(2);
      
      // Save preference
      this.saveConversionPreference();
    }
  },
  
  // =================== FOREX RATES TABLE MODULE ===================
  
  forexTable: {
    // DOM elements
    elements: {
      forexRatesBody: null
    },
    
    // Currency information
    currencies: {
      'USD': 'US Dollar',
      'EUR': 'Euro',
      'GBP': 'British Pound',
      'JPY': 'Japanese Yen',
      'AED': 'UAE Dirham',
      'ZAR': 'South African Rand',
      'CNY': 'Chinese Yuan',
      'INR': 'Indian Rupee',
      'UGX': 'Ugandan Shilling',
      'TZS': 'Tanzanian Shilling'
    },
    
    // Initialize forex rates table
    async init() {
      // Get DOM elements
      this.elements = {
        forexRatesBody: document.getElementById('forex-rates-body')
      };
      
      // Fetch and display rates
      return this.refresh();
    },
    
    // Refresh the forex rates table
    async refresh() {
      if (!this.elements.forexRatesBody) return;
      
      try {
        // Show loading state
        this.elements.forexRatesBody.innerHTML = `
          <tr class="loading-row">
            <td colspan="4">
              <div class="loading-spinner"></div>
              <span>Loading latest rates...</span>
            </td>
          </tr>
        `;
        
        // Fetch rates
        const data = await PesaGuru.dataService.fetchForexRates();
        
        // Update table
        this.updateTable(data);
        
        return data;
      } catch (error) {
        console.error('Error refreshing forex rates table:', error);
        
        // Show error state
        this.elements.forexRatesBody.innerHTML = `
          <tr class="error-row">
            <td colspan="4">
              <i class="fas fa-exclamation-circle"></i>
              <span>Failed to load rates. Please try again.</span>
            </td>
          </tr>
        `;
        
        throw error;
      }
    },
    
    // Update the table with new data
    updateTable(data) {
      const { forexRatesBody } = this.elements;
      
      // Clear table
      forexRatesBody.innerHTML = '';
      
      // Create table rows for each currency
      Object.keys(this.currencies).forEach(code => {
        if (data.rates[code]) {
          const row = document.createElement('tr');
          
          // Calculate rate to KES (inverse of rate from KES)
          const rateToKes = 1 / data.rates[code];
          
          // Calculate daily change
          const change = data.changes[code];
          const changeClass = change >= 0 ? 'positive' : 'negative';
          const changeArrow = change >= 0 ? '▲' : '▼';
          const changePercent = Math.abs(change * 100).toFixed(2) + '%';
          
          // Create row HTML
          row.innerHTML = `
            <td>
              <div class="currency-name">
                <img src="../../../assets/images/flags/${code.toLowerCase()}.png" alt="${code}" class="currency-flag">
                <span>${this.currencies[code]}</span>
              </div>
            </td>
            <td>${code}</td>
            <td>${rateToKes.toFixed(4)}</td>
            <td class="${changeClass}">${changeArrow} ${changePercent}</td>
          `;
          
          // Add row to table with delay for staggered animation
          setTimeout(() => {
            forexRatesBody.appendChild(row);
            
            // Add fade-in animation
            setTimeout(() => {
              row.classList.add('visible');
            }, 50);
          }, Object.keys(this.currencies).indexOf(code) * 100);
        }
      });
    }
  },
  
  // =================== FOREX CHART MODULE ===================
  
  forexChart: {
    // DOM elements
    elements: {
      chartContainer: null,
      chartCanvas: null,
      currencySelect: null,
      timeframeSelect: null,
      chartInfo: null
    },
    
    // Chart instance
    chart: null,
    
    // Chart data
    data: {
      currencyPair: null,
      timeframe: null,
      historical: null
    },
    
    // Initialize forex chart
    async init() {
      // Get DOM elements
      this.elements = {
        chartContainer: document.getElementById('chart-container'),
        chartCanvas: document.getElementById('forex-chart'),
        currencySelect: document.getElementById('chart-currency'),
        timeframeSelect: document.getElementById('chart-timeframe'),
        chartInfo: document.getElementById('chart-info')
      };
      
      // Set initial values from user preferences or state
      if (this.elements.currencySelect) {
        this.elements.currencySelect.value = PesaGuru.state.activeCurrency;
      }
      
      if (this.elements.timeframeSelect) {
        this.elements.timeframeSelect.value = PesaGuru.state.activeTimeframe;
      }
      
      // Setup event listeners
      this.setupEventListeners();
      
      // Create initial chart
      await this.updateChart();
      
      // Store chart instance in global state
      PesaGuru.state.charts.forexChart = this.chart;
    },
    
    // Set up event listeners
    setupEventListeners() {
      if (this.elements.currencySelect) {
        this.elements.currencySelect.addEventListener('change', () => {
          // Save preference
          PesaGuru.state.activeCurrency = this.elements.currencySelect.value;
          PesaGuru.state.userPreferences.currency = this.elements.currencySelect.value;
          PesaGuru.saveUserPreferences();
          
          // Update chart
          this.updateChart();
        });
      }
      
      if (this.elements.timeframeSelect) {
        this.elements.timeframeSelect.addEventListener('change', () => {
          // Save preference
          PesaGuru.state.activeTimeframe = this.elements.timeframeSelect.value;
          PesaGuru.state.userPreferences.timeframe = this.elements.timeframeSelect.value;
          PesaGuru.saveUserPreferences();
          
          // Update chart
          this.updateChart();
        });
      }
    },
    
    // Refresh the chart
    async refresh() {
      return this.updateChart(true);
    },
    
    // Update the chart with new data
    async updateChart(forceRefresh = false) {
      const { chartCanvas, currencySelect, timeframeSelect, chartInfo } = this.elements;
      
      if (!chartCanvas) return;
      
      try {
        // Show loading state
        if (chartInfo) {
          chartInfo.innerHTML = `
            <div class="chart-loading">
              <div class="loading-spinner"></div>
              <span>Loading chart data...</span>
            </div>
          `;
        }
        
        // Get selected values
        const selectedCurrencyPair = currencySelect ? currencySelect.value : PesaGuru.state.activeCurrency;
        const selectedTimeframe = timeframeSelect ? timeframeSelect.value : PesaGuru.state.activeTimeframe;
        
        // Skip if no change and not forced refresh
        if (!forceRefresh && 
            this.data.currencyPair === selectedCurrencyPair && 
            this.data.timeframe === selectedTimeframe &&
            this.data.historical) {
          return;
        }
        
        // Fetch data
        const chartData = await PesaGuru.dataService.fetchHistoricalRates(
          selectedCurrencyPair,
          selectedTimeframe
        );
        
        // Save data
        this.data = {
          currencyPair: selectedCurrencyPair,
          timeframe: selectedTimeframe,
          historical: chartData
        };
        
        // Render chart
        this.renderChart(chartData);
        
        // Clear loading state
        if (chartInfo) {
          chartInfo.innerHTML = '';
        }
        
        return chartData;
      } catch (error) {
        console.error('Error updating forex chart:', error);
        
        // Show error state
        if (chartInfo) {
          chartInfo.innerHTML = `
            <div class="chart-error">
              <i class="fas fa-exclamation-circle"></i>
              <span>Failed to load chart data</span>
            </div>
          `;
        }
        
        throw error;
      }
    },
    
    // Render the chart with the provided data
    renderChart(data) {
      const { chartCanvas } = this.elements;
      const ctx = chartCanvas.getContext('2d');
      
      // Determine if dark theme is active
      const isDarkTheme = document.body.classList.contains('dark-theme');
      
      // Destroy previous chart if it exists
      if (this.chart) {
        this.chart.destroy();
      }
      
      // Set chart colors based on theme
      const colors = {
        gridColor: isDarkTheme ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)',
        textColor: isDarkTheme ? '#e0e0e0' : '#666666',
        lineColor: PesaGuru.config.colors.primary,
        maLineColor: PesaGuru.config.colors.secondary,
        areaColor: isDarkTheme ? 'rgba(44, 110, 203, 0.15)' : 'rgba(44, 110, 203, 0.1)'
      };
      
      // Get currency pair name for display
      const currencyPair = this.data.currencyPair.replace('-', '/');
      
      // Create gradient for area fill
      const gradient = ctx.createLinearGradient(0, 0, 0, 250);
      gradient.addColorStop(0, colors.areaColor);
      gradient.addColorStop(1, 'rgba(44, 110, 203, 0)');
      
      // Create annotations for technical analysis (if any)
      const annotations = {
        line1: {
          type: 'line',
          mode: 'horizontal',
          scaleID: 'y',
          value: Math.max(...data.rates) * 0.98, // Support level near top
          borderColor: 'rgba(99, 255, 132, 0.5)',
          borderWidth: 1,
          borderDash: [5, 5],
          label: {
            content: 'Support',
            enabled: true,
            position: 'right'
          }
        },
        line2: {
          type: 'line',
          mode: 'horizontal',
          scaleID: 'y',
          value: Math.min(...data.rates) * 1.02, // Resistance level near bottom
          borderColor: 'rgba(255, 99, 132, 0.5)',
          borderWidth: 1,
          borderDash: [5, 5],
          label: {
            content: 'Resistance',
            enabled: true,
            position: 'right'
          }
        }
      };
      
      // Create new chart
      this.chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: data.dates,
          datasets: [
            {
              label: `${currencyPair} Rate`,
              data: data.rates,
              borderColor: colors.lineColor,
              backgroundColor: gradient,
              fill: true,
              tension: 0.4,
              borderWidth: 2,
              pointRadius: 2,
              pointHoverRadius: 5
            },
            {
              label: '7-Day Moving Average',
              data: data.movingAverage,
              borderColor: colors.maLineColor,
              borderWidth: 2,
              borderDash: [5, 5],
              pointRadius: 0,
              fill: false,
              tension: 0.4
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            annotation: {
              annotations: annotations
            },
            legend: {
              display: true,
              position: 'top',
              labels: {
                color: colors.textColor,
                usePointStyle: true,
                padding: 15
              }
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: isDarkTheme ? '#333' : 'rgba(255, 255, 255, 0.9)',
              titleColor: isDarkTheme ? '#fff' : '#666',
              bodyColor: isDarkTheme ? '#ddd' : '#333',
              borderColor: isDarkTheme ? '#555' : '#ddd',
              borderWidth: 1,
              padding: 10,
              caretSize: 8,
              cornerRadius: 4,
              displayColors: true,
              callbacks: {
                label: (context) => {
                  let label = context.dataset.label || '';
                  if (label) {
                    label += ': ';
                  }
                  if (context.parsed.y !== null) {
                    label += context.parsed.y.toFixed(4);
                  }
                  return label;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                color: colors.gridColor,
                display: true,
                drawBorder: true,
                drawOnChartArea: true,
                drawTicks: true
              },
              ticks: {
                color: colors.textColor,
                maxRotation: 0,
                autoSkipPadding: 15,
                callback: function(value, index, values) {
                  // Show fewer labels on small screens
                  if (window.innerWidth < 768) {
                    return index % 3 === 0 ? this.getLabelForValue(value) : '';
                  }
                  return this.getLabelForValue(value);
                }
              }
            },
            y: {
              grid: {
                color: colors.gridColor
              },
              ticks: {
                color: colors.textColor,
                callback: function(value) {
                  return value.toFixed(2);
                }
              },
              // Don't start from zero to better visualize changes
              beginAtZero: false
            }
          }
        }
      });
      
      // Add chart instance to state
      PesaGuru.state.charts.forexChart = this.chart;
    },
    
    // Update chart theme when theme changes
    updateTheme(isDarkTheme) {
      if (this.data.historical) {
        this.renderChart(this.data.historical);
      }
    },

    // Resize chart when container size changes
    resize() {
      if (this.chart) {
        this.chart.resize();
      }
    }
  },
  
  // =================== AI INSIGHTS MODULE ===================
  
  aiInsights: {
    // DOM elements
    elements: {
      sentimentBadge: null,
      aiAnalysisText: null,
      predictionContainer: null,
      riskFactorsList: null,
      technicalLevelsContainer: null,
      insightActions: null
    },
    
    // Insights data
    data: null,
    
    // Initialize AI insights module
    async init() {
      // Get DOM elements
      this.elements = {
        sentimentBadge: document.querySelector('.sentiment-badge'),
        aiAnalysisText: document.getElementById('ai-analysis-text'),
        predictionContainer: document.getElementById('prediction-container'),
        riskFactorsList: document.getElementById('risk-factors-list'),
        technicalLevelsContainer: document.getElementById('technical-levels-container'),
        insightActions: document.querySelector('.insight-actions')
      };
      
      // Setup event listeners
      this.setupEventListeners();
      
      // Load initial insights
      return this.refresh();
    },
    
    // Set up event listeners
    setupEventListeners() {
      // Share insights button
      const shareButton = document.querySelector('.share-insights');
      if (shareButton) {
        shareButton.addEventListener('click', () => this.shareInsights());
      }
      
      // Save insights button
      const saveButton = document.querySelector('.save-insights');
      if (saveButton) {
        saveButton.addEventListener('click', () => this.saveInsights());
      }
      
      // Expand/collapse buttons
      const expandButtons = document.querySelectorAll('.expand-section');
      expandButtons.forEach(button => {
        button.addEventListener('click', (e) => {
          const section = e.target.closest('.insight-section');
          if (section) {
            section.classList.toggle('expanded');
            
            // Update button text
            if (section.classList.contains('expanded')) {
              e.target.innerHTML = 'Show Less <i class="fas fa-chevron-up"></i>';
            } else {
              e.target.innerHTML = 'Show More <i class="fas fa-chevron-down"></i>';
            }
          }
        });
      });
    },
    
    // Refresh AI insights
    async refresh() {
      try {
        // Show loading state
        this.setLoadingState(true);
        
        // Fetch insights
        this.data = await PesaGuru.dataService.generateAIInsights();
        
        // Update UI
        this.updateInsights();
        
        return this.data;
      } catch (error) {
        console.error('Error refreshing AI insights:', error);
        
        // Show error state
        this.setErrorState();
        
        throw error;
      } finally {
        // Hide loading state
        this.setLoadingState(false);
      }
    },
    
    // Set loading state
    setLoadingState(isLoading) {
      const { aiAnalysisText, predictionContainer } = this.elements;
      
      if (isLoading) {
        if (aiAnalysisText) {
          aiAnalysisText.innerHTML = `
            <div class="loading-state">
              <div class="loading-spinner"></div>
              <span>Generating AI insights...</span>
            </div>
          `;
        }
        
        if (predictionContainer) {
          predictionContainer.innerHTML = `
            <div class="loading-state">
              <div class="loading-spinner"></div>
            </div>
          `;
        }
      }
    },
    
    // Set error state
    setErrorState() {
      const { aiAnalysisText, predictionContainer, sentimentBadge } = this.elements;
      
      if (aiAnalysisText) {
        aiAnalysisText.innerHTML = `
          <div class="error-state">
            <i class="fas fa-exclamation-circle"></i>
            <span>Failed to generate AI insights. Please try again.</span>
          </div>
        `;
      }
      
      if (predictionContainer) {
        predictionContainer.innerHTML = '';
      }
      
      if (sentimentBadge) {
        sentimentBadge.textContent = 'N/A';
        sentimentBadge.className = 'sentiment-badge neutral';
      }
    },
    
    // Update insights UI with new data
    updateInsights() {
      if (!this.data) return;
      
      this.updateSentimentBadge();
      this.updateAnalysisText();
      this.updatePredictions();
      this.updateRiskFactors();
      this.updateTechnicalLevels();
    },
    
    // Update sentiment badge
    updateSentimentBadge() {
      const { sentimentBadge } = this.elements;
      if (!sentimentBadge) return;
      
      // Update text and class
      sentimentBadge.textContent = this.data.sentiment.toUpperCase();
      
      // Remove existing classes
      sentimentBadge.className = 'sentiment-badge';
      
      // Add new class based on sentiment
      sentimentBadge.classList.add(this.data.sentiment.toLowerCase());
      
      // Add animation
      sentimentBadge.classList.add('badge-update');
      setTimeout(() => sentimentBadge.classList.remove('badge-update'), 500);
    },
    
    // Update analysis text
    updateAnalysisText() {
      const { aiAnalysisText } = this.elements;
      if (!aiAnalysisText) return;
      
      // Add highlight animation
      aiAnalysisText.style.opacity = 0;
      
      setTimeout(() => {
        // Update text
        aiAnalysisText.textContent = this.data.analysis;
        
        // Animate back in
        aiAnalysisText.style.opacity = 1;
      }, 300);
    },
    
    // Update predictions
    updatePredictions() {
      const { predictionContainer } = this.elements;
      if (!predictionContainer || !this.data.predictions) return;
      
      // Clear container
      predictionContainer.innerHTML = '';
      
      // Add each prediction card with delay for animation
      this.data.predictions.forEach((prediction, index) => {
        setTimeout(() => {
          const predictionCard = document.createElement('div');
          predictionCard.className = 'prediction-card';
          
          // Create HTML content
          predictionCard.innerHTML = `
            <h5>${prediction.pair}</h5>
            <div class="prediction-arrow ${prediction.direction}">
              <i class="fas fa-arrow-${this.getDirectionIcon(prediction.direction)}"></i>
            </div>
            <p class="prediction-value">${prediction.value}</p>
            <p class="confidence">Confidence: ${prediction.confidence}</p>
            ${prediction.details ? `<p class="prediction-details">${prediction.details}</p>` : ''}
          `;
          
          // Add to container
          predictionContainer.appendChild(predictionCard);
          
          // Add entrance animation
          setTimeout(() => {
            predictionCard.classList.add('visible');
          }, 50);
        }, index * 100);
      });
    },
    
    // Update risk factors
    updateRiskFactors() {
      const { riskFactorsList } = this.elements;
      if (!riskFactorsList || !this.data.riskAnalysis) return;
      
      // Clear existing content
      riskFactorsList.innerHTML = '';
      
      // Create sections for global and local factors
      if (this.data.riskAnalysis.globalFactors && this.data.riskAnalysis.globalFactors.length > 0) {
        const globalSection = document.createElement('div');
        globalSection.className = 'risk-section';
        globalSection.innerHTML = `
          <h6 class="risk-section-title">Global Factors</h6>
          <ul>
            ${this.data.riskAnalysis.globalFactors.map(factor => `<li>${factor}</li>`).join('')}
          </ul>
        `;
        riskFactorsList.appendChild(globalSection);
      }
      
      if (this.data.riskAnalysis.localFactors && this.data.riskAnalysis.localFactors.length > 0) {
        const localSection = document.createElement('div');
        localSection.className = 'risk-section';
        localSection.innerHTML = `
          <h6 class="risk-section-title">Local Factors</h6>
          <ul>
            ${this.data.riskAnalysis.localFactors.map(factor => `<li>${factor}</li>`).join('')}
          </ul>
        `;
        riskFactorsList.appendChild(localSection);
      }
    },
    
    // Update technical levels
    updateTechnicalLevels() {
      const { technicalLevelsContainer } = this.elements;
      if (!technicalLevelsContainer || !this.data.technicalIndicators) return;
      
      // Clear existing content
      technicalLevelsContainer.innerHTML = '';
      
      // Add technical levels for each currency pair
      Object.keys(this.data.technicalIndicators).forEach(pair => {
        const indicators = this.data.technicalIndicators[pair];
        
        const levelsCard = document.createElement('div');
        levelsCard.className = 'technical-card';
        
        // Create content
        levelsCard.innerHTML = `
          <h6>${pair}</h6>
          <div class="levels-container">
            <div class="level-group">
              <span class="level-label">Support</span>
              <div class="level-values">
                ${indicators.supportLevels.map(level => `<span class="level-value">${level}</span>`).join('')}
              </div>
            </div>
            <div class="level-group">
              <span class="level-label">Resistance</span>
              <div class="level-values">
                ${indicators.resistanceLevels.map(level => `<span class="level-value">${level}</span>`).join('')}
              </div>
            </div>
          </div>
          <div class="trend">
            <span class="trend-label">Trend:</span>
            <span class="trend-value">${indicators.trend}</span>
          </div>
        `;
        
        technicalLevelsContainer.appendChild(levelsCard);
      });
    },
    
    // Share insights
    shareInsights() {
      // In a real app, this would open a sharing dialog
      // For demo, show a toast
      PesaGuru.showToast('Sharing insights feature coming soon', 'info');
      
      // Example of what a sharing feature might include:
      /*
      const shareData = {
        title: 'PesaGuru Forex Insights',
        text: this.data.analysis,
        url: window.location.href
      };
      
      if (navigator.share) {
        navigator.share(shareData)
          .then(() => PesaGuru.showToast('Insights shared successfully', 'success'))
          .catch(error => {
            console.error('Error sharing:', error);
            PesaGuru.showToast('Failed to share insights', 'error');
          });
      } else {
        // Fallback for browsers that don't support the Web Share API
        this.showShareModal();
      }
      */
    },
    
    // Save insights
    saveInsights() {
      // In a real app, this would save insights to user's saved items
      // For demo, save to localStorage
      try {
        const savedInsights = JSON.parse(localStorage.getItem('pesaGuruSavedInsights') || '[]');
        
        // Add current insights with timestamp
        savedInsights.push({
          id: Date.now(),
          timestamp: new Date().toISOString(),
          sentiment: this.data.sentiment,
          analysis: this.data.analysis,
          predictions: this.data.predictions
        });
        
        // Save to localStorage
        localStorage.setItem('pesaGuruSavedInsights', JSON.stringify(savedInsights));
        
        PesaGuru.showToast('Insights saved successfully', 'success');
      } catch (error) {
        console.error('Error saving insights:', error);
        PesaGuru.showToast('Failed to save insights', 'error');
      }
    },
    
    // Get direction icon
    getDirectionIcon(direction) {
      switch (direction) {
        case 'up': return 'up';
        case 'down': return 'down';
        case 'stable':
        default: return 'minus';
      }
    }
  },
  
  // =================== ALERT SYSTEM MODULE ===================
  
  alertSystem: {
    // DOM elements
    elements: {
      alertForm: null,
      alertsList: null,
      alertModal: null
    },
    
    // Initialize alert system
    async init() {
      // Get DOM elements
      this.elements = {
        alertForm: document.getElementById('alert-form'),
        alertsList: document.getElementById('alerts-list'),
        alertModal: document.getElementById('alert-modal')
      };
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Load existing alerts
      this.loadUserAlerts();
      
      return Promise.resolve();
    },
    
    // Set up event listeners
    setupEventListeners() {
      const { alertForm, alertModal } = this.elements;
      
      // Alert form submission
      if (alertForm) {
        alertForm.addEventListener('submit', e => this.createAlert(e));
      }
      
      // Close modal button
      const closeModal = alertModal ? alertModal.querySelector('.close-modal') : null;
      if (closeModal) {
        closeModal.addEventListener('click', () => this.hideModal());
      }
      
      // Modal OK button
      const modalOkButton = alertModal ? alertModal.querySelector('.modal-content .btn-primary') : null;
      if (modalOkButton) {
        modalOkButton.addEventListener('click', () => this.hideModal());
      }
      
      // Close modal when clicking outside
      if (alertModal) {
        window.addEventListener('click', event => {
          if (event.target === alertModal) {
            this.hideModal();
          }
        });
      }
      
      // Enable/disable alert button
      const enableAlertsBtn = document.getElementById('enable-alerts');
      if (enableAlertsBtn) {
        enableAlertsBtn.addEventListener('click', () => this.toggleAlerts());
      }
    },
    
    // Toggle alerts on/off
    toggleAlerts() {
      PesaGuru.state.alertsEnabled = !PesaGuru.state.alertsEnabled;
      
      // Update button text
      const enableAlertsBtn = document.getElementById('enable-alerts');
      if (enableAlertsBtn) {
        if (PesaGuru.state.alertsEnabled) {
          enableAlertsBtn.innerHTML = 'Alerts Active <i class="fas fa-bell"></i>';
          enableAlertsBtn.classList.add('active');
          PesaGuru.showToast('Alerts are now active', 'success');
        } else {
          enableAlertsBtn.innerHTML = 'Enable Alerts <i class="fas fa-bell-slash"></i>';
          enableAlertsBtn.classList.remove('active');
          PesaGuru.showToast('Alerts are now disabled', 'info');
        }
      }
      
      // Save preference
      PesaGuru.state.userPreferences.alertsEnabled = PesaGuru.state.alertsEnabled;
      PesaGuru.saveUserPreferences();
      
      // In a real app, this would also start/stop the alert checking service
    },
    
    // Show modal
    showModal() {
      const { alertModal } = this.elements;
      if (alertModal) {
        alertModal.style.display = 'flex';
        
        // Add animation class
        setTimeout(() => {
          alertModal.classList.add('visible');
        }, 10);
      }
    },
    
    // Hide modal
    hideModal() {
      const { alertModal } = this.elements;
      if (alertModal) {
        alertModal.classList.remove('visible');
        
        // Remove display after animation
        setTimeout(() => {
          alertModal.style.display = 'none';
        }, 300);
      }
    },
    
    // Create new alert
    createAlert(e) {
      e.preventDefault();
      
      const { alertForm } = this.elements;
      
      // Get form values
      const alertCurrency = document.getElementById('alert-currency').value;
      const alertType = document.getElementById('alert-type').value;
      const alertValue = document.getElementById('alert-value').value;
      const notifyEmail = document.getElementById('notify-email').checked;
      const notifySms = document.getElementById('notify-sms').checked;
      const notifyPush = document.getElementById('notify-push').checked;
      
      // Validate input
      if (!alertCurrency || !alertType || !alertValue) {
        PesaGuru.showToast('Please fill all required fields', 'warning');
        return;
      }
      
      // Create alert object
      const alertId = Date.now();
      const newAlert = {
        id: alertId,
        currency: alertCurrency,
        type: alertType,
        value: alertValue,
        notifications: {
          email: notifyEmail,
          sms: notifySms,
          push: notifyPush
        },
        created: new Date().toISOString(),
        active: true
      };
      
      // Save alert
      const userAlerts = JSON.parse(localStorage.getItem('pesaGuruForexAlerts') || '[]');
      userAlerts.push(newAlert);
      localStorage.setItem('pesaGuruForexAlerts', JSON.stringify(userAlerts));
      
      // Update display
      this.loadUserAlerts();
      
      // Reset form
      alertForm.reset();
      
      // Show success modal
      this.showModal();
      
      // Enable alerts if not already enabled
      if (!PesaGuru.state.alertsEnabled) {
        this.toggleAlerts();
      }
    },
    
    // Load and display user alerts
    loadUserAlerts() {
      const { alertsList } = this.elements;
      if (!alertsList) return;
      
      // Get alerts from localStorage
      const userAlerts = JSON.parse(localStorage.getItem('pesaGuruForexAlerts') || '[]');
      
      // Show message if no alerts
      if (userAlerts.length === 0) {
        alertsList.innerHTML = '<p class="no-alerts-message">You don\'t have any active alerts. Create one above.</p>';
        return;
      }
      
      // Clear list
      alertsList.innerHTML = '';
      
      // Add each alert to the list
      userAlerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert-item';
        
        // Add 'active' class if alert is active
        if (alert.active) {
          alertElement.classList.add('active');
        }
        
        // Format alert type for display
        let formattedType = '';
        switch (alert.type) {
          case 'above':
            formattedType = 'Price Above';
            break;
          case 'below':
            formattedType = 'Price Below';
            break;
          case 'percent-change':
            formattedType = 'Change (24h)';
            break;
        }
        
        // Format notifications
        const notifications = [];
        if (alert.notifications.email) notifications.push('Email');
        if (alert.notifications.sms) notifications.push('SMS');
        if (alert.notifications.push) notifications.push('Push');
        
        // Create HTML
        alertElement.innerHTML = `
          <div class="alert-details">
            <h5>${alert.currency.replace('-', '/')} - ${formattedType}</h5>
            <p>Target: ${alert.type === 'percent-change' ? alert.value + '%' : alert.value}</p>
            <p class="alert-meta">
              <span>Via: ${notifications.join(', ')}</span>
              <span>Created: ${PesaGuru.utils.formatDate(new Date(alert.created))}</span>
            </p>
          </div>
          <div class="alert-actions">
            <button class="btn-toggle ${alert.active ? 'active' : ''}" data-alert-id="${alert.id}">
              <i class="fas ${alert.active ? 'fa-bell' : 'fa-bell-slash'}"></i>
            </button>
            <button class="btn-delete" data-alert-id="${alert.id}">
              <i class="fas fa-trash-alt"></i>
            </button>
          </div>
        `;
        
        // Add to list
        alertsList.appendChild(alertElement);
        
        // Add toggle functionality
        const toggleButton = alertElement.querySelector(`.btn-toggle[data-alert-id="${alert.id}"]`);
        if (toggleButton) {
          toggleButton.addEventListener('click', () => this.toggleAlert(alert.id));
        }
        
        // Add delete functionality
        const deleteButton = alertElement.querySelector(`.btn-delete[data-alert-id="${alert.id}"]`);
        if (deleteButton) {
          deleteButton.addEventListener('click', () => this.deleteAlert(alert.id));
        }
      });
    },
    
    // Toggle alert active state
    toggleAlert(alertId) {
      // Get alerts from localStorage
      const userAlerts = JSON.parse(localStorage.getItem('pesaGuruForexAlerts') || '[]');
      
      // Find and update the alert
      const updatedAlerts = userAlerts.map(alert => {
        if (alert.id === alertId) {
          alert.active = !alert.active;
        }
        return alert;
      });
      
      // Save updated alerts
      localStorage.setItem('pesaGuruForexAlerts', JSON.stringify(updatedAlerts));
      
      // Update display
      this.loadUserAlerts();
      
      // Show toast
      const alert = updatedAlerts.find(a => a.id === alertId);
      if (alert) {
        PesaGuru.showToast(
          `Alert ${alert.active ? 'activated' : 'deactivated'}: ${alert.currency.replace('-', '/')}`,
          alert.active ? 'success' : 'info'
        );
      }
    },
    
    // Delete alert
    deleteAlert(alertId) {
      // Get alerts from localStorage
      const userAlerts = JSON.parse(localStorage.getItem('pesaGuruForexAlerts') || '[]');
      
      // Find alert to delete (for feedback message)
      const alertToDelete = userAlerts.find(alert => alert.id === alertId);
      
      // Filter out the alert to delete
      const updatedAlerts = userAlerts.filter(alert => alert.id !== alertId);
      
      // Save updated alerts
      localStorage.setItem('pesaGuruForexAlerts', JSON.stringify(updatedAlerts));
      
      // Update display
      this.loadUserAlerts();
      
      // Show toast
      if (alertToDelete) {
        PesaGuru.showToast(
          `Alert deleted: ${alertToDelete.currency.replace('-', '/')}`,
          'info'
        );
      }
    }
  },
  
  // =================== ECONOMIC CALENDAR MODULE ===================
  
  economicCalendar: {
    // DOM elements
    elements: {
      prevDayBtn: null,
      nextDayBtn: null,
      currentDateDisplay: null,
      eventsContainer: null
    },
    
    // Current date
    currentDate: new Date(),
    
    // Initialize economic calendar
    async init() {
      // Get DOM elements
      this.elements = {
        prevDayBtn: document.getElementById('prev-day'),
        nextDayBtn: document.getElementById('next-day'),
        currentDateDisplay: document.getElementById('calendar-current-date'),
        eventsContainer: document.getElementById('economic-events')
      };
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Set initial date display
      this.updateDateDisplay();
      
      // Load events for current date
      return this.loadEvents();
    },
    
    // Set up event listeners
    setupEventListeners() {
      const { prevDayBtn, nextDayBtn } = this.elements;
      
      // Previous day button
      if (prevDayBtn) {
        prevDayBtn.addEventListener('click', () => this.changeDate(-1));
      }
      
      // Next day button
      if (nextDayBtn) {
        nextDayBtn.addEventListener('click', () => this.changeDate(1));
      }
    },
    
    // Change date by offset days
    changeDate(offset) {
      // Create new date object to avoid mutating the original
      const newDate = new Date(this.currentDate);
      newDate.setDate(newDate.getDate() + offset);
      
      // Update current date
      this.currentDate = newDate;
      
      // Update date display
      this.updateDateDisplay();
      
      // Load events for new date
      this.loadEvents();
    },
    
    // Update date display
    updateDateDisplay() {
      const { currentDateDisplay } = this.elements;
      
      if (currentDateDisplay) {
        currentDateDisplay.textContent = PesaGuru.utils.formatDate(this.currentDate);
        
        // Add animation
        currentDateDisplay.classList.add('date-change');
        setTimeout(() => currentDateDisplay.classList.remove('date-change'), 500);
      }
    },
    
    // Refresh events
    async refresh() {
      return this.loadEvents(true);
    },
    
    // Load events for current date
    async loadEvents(forceRefresh = false) {
      const { eventsContainer } = this.elements;
      if (!eventsContainer) return;
      
      try {
        // Show loading state
        eventsContainer.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Loading events...</p></div>';
        
        // Fetch events for current date
        const events = await PesaGuru.dataService.fetchEconomicEvents(this.currentDate);
        
        // Display events
        this.displayEvents(events);
        
        return events;
      } catch (error) {
        console.error('Error loading economic events:', error);
        
        // Show error state
        eventsContainer.innerHTML = `
          <div class="error-container">
            <i class="fas fa-exclamation-circle"></i>
            <p>Failed to load economic events. Please try again.</p>
          </div>
        `;
        
        throw error;
      }
    },
    
    // Display events
    displayEvents(events) {
      const { eventsContainer } = this.elements;
      if (!eventsContainer) return;
      
      // Clear container
      eventsContainer.innerHTML = '';
      
      // Show message if no events
      if (events.length === 0) {
        eventsContainer.innerHTML = '<p class="no-events">No economic events scheduled for this date.</p>';
        return;
      }
      
      // Create elements for each event with staggered animation
      events.forEach((event, index) => {
        setTimeout(() => {
          const eventItem = document.createElement('div');
          eventItem.className = 'event-item';
          
          // Create HTML content
          eventItem.innerHTML = `
            <div class="event-time">${event.time}</div>
            <div class="event-details">
              <span class="event-country">
                <img src="../../../assets/images/flags/${event.country.toLowerCase()}.png" alt="${event.country}" class="flag-icon">
                ${event.country}
              </span>
              <span class="event-title">${event.event}</span>
              <span class="event-impact ${event.impact}">${event.impact.charAt(0).toUpperCase() + event.impact.slice(1)} Impact</span>
            </div>
          `;
          
          // Add to container
          eventsContainer.appendChild(eventItem);
          
          // Add animation class after a short delay
          setTimeout(() => {
            eventItem.classList.add('visible');
          }, 50);
        }, index * 100);
      });
    }
  },
  
  // =================== FOREX NEWS MODULE ===================
  
  forexNews: {
    // DOM elements
    elements: {
      newsContainer: null,
      newsFilter: null
    },
    
    // Initialize forex news
    async init() {
      // Get DOM elements
      this.elements = {
        newsContainer: document.getElementById('forex-news'),
        newsFilter: document.getElementById('news-filter')
      };
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Load initial news
      return this.refresh();
    },
    
    // Set up event listeners
    setupEventListeners() {
      const { newsFilter } = this.elements;
      
      // News filter
      if (newsFilter) {
        newsFilter.addEventListener('change', () => this.filterNews());
      }
    },
    
    // Refresh news
    async refresh() {
      try {
        // Show loading state
        this.setLoadingState(true);
        
        // Fetch news
        const news = await PesaGuru.dataService.fetchForexNews();
        
        // Display news
        this.displayNews(news);
        
        return news;
      } catch (error) {
        console.error('Error refreshing forex news:', error);
        
        // Show error state
        this.setErrorState();
        
        throw error;
      } finally {
        // Hide loading state
        this.setLoadingState(false);
      }
    },
    
    // Set loading state
    setLoadingState(isLoading) {
      const { newsContainer } = this.elements;
      if (!newsContainer) return;
      
      if (isLoading) {
        newsContainer.innerHTML = '<div class="loading-container"><div class="loading-spinner"></div><p>Loading news...</p></div>';
      }
    },
    
    // Set error state
    setErrorState() {
      const { newsContainer } = this.elements;
      if (!newsContainer) return;
      
      newsContainer.innerHTML = `
        <div class="error-container">
          <i class="fas fa-exclamation-circle"></i>
          <p>Failed to load news. Please try again.</p>
        </div>
      `;
    },
    
    // Display news
    displayNews(articles) {
      const { newsContainer, newsFilter } = this.elements;
      if (!newsContainer) return;
      
      // Store articles for filtering
      this.articles = articles;
      
      // Get filter value if available
      const filterValue = newsFilter ? newsFilter.value : 'all';
      
      // Apply filter
      const filteredArticles = this.filterArticles(articles, filterValue);
      
      // Clear container
      newsContainer.innerHTML = '';
      
      // Show message if no articles
      if (filteredArticles.length === 0) {
        newsContainer.innerHTML = '<p class="no-news">No news articles available.</p>';
        return;
      }
      
      // Create elements for each article with staggered animation
      filteredArticles.forEach((article, index) => {
        setTimeout(() => {
          const articleItem = document.createElement('div');
          articleItem.className = 'article-item';
          
          // Create HTML content
          articleItem.innerHTML = `
            <div class="article-time">${article.time}</div>
            <div class="article-details">
              <span class="article-source">${article.source}</span>
              <h5 class="article-title">${article.title}</h5>
              <p class="article-summary">${article.summary}</p>
              <a href="${article.url}" class="read-more" target="_blank">Read More <i class="fas fa-external-link-alt"></i></a>
            </div>
          `;
          
          // Add to container
          newsContainer.appendChild(articleItem);
          
          // Add animation class after a short delay
          setTimeout(() => {
            articleItem.classList.add('visible');
          }, 50);
        }, index * 150);
      });
    },
    
    // Filter news based on selection
    filterNews() {
      const { newsFilter } = this.elements;
      if (!newsFilter || !this.articles) return;
      
      // Get filter value
      const filterValue = newsFilter.value;
      
      // Apply filter
      const filteredArticles = this.filterArticles(this.articles, filterValue);
      
      // Display filtered articles
      this.displayNews(filteredArticles);
    },
    
    // Filter articles based on criteria
    filterArticles(articles, filter) {
      if (filter === 'all') return articles;
      
      // In a real app, this would filter based on categories, sources, etc.
      // For demo, we'll just return all articles
      return articles;
    }
  },
  
  // =================== TRADING SIGNALS MODULE ===================
  
  tradingSignals: {
    // DOM elements
    elements: {
      signalsTimeframe: null,
      signalsBody: null
    },
    
    // Initialize trading signals
    async init() {
      // Get DOM elements
      this.elements = {
        signalsTimeframe: document.getElementById('signals-timeframe'),
        signalsBody: document.getElementById('signals-body')
      };
      
      // Set up event listeners
      this.setupEventListeners();
      
      // Load initial signals
      return this.refresh();
    },
    
    // Set up event listeners
    setupEventListeners() {
      const { signalsTimeframe } = this.elements;
      
      // Timeframe select
      if (signalsTimeframe) {
        signalsTimeframe.addEventListener('change', () => this.refresh());
      }
    },
    
    // Refresh trading signals
    async refresh() {
      const { signalsTimeframe, signalsBody } = this.elements;
      if (!signalsBody) return;
      
      try {
        // Show loading state
        signalsBody.innerHTML = `
          <tr class="loading-row">
            <td colspan="5">
              <div class="loading-spinner"></div>
              <span>Loading signals...</span>
            </td>
          </tr>
        `;
        
        // Get selected timeframe
        const timeframe = signalsTimeframe ? signalsTimeframe.value : '1D';
        
        // Fetch signals
        const signals = await PesaGuru.dataService.fetchTradingSignals(timeframe);
        
        // Display signals
        this.displaySignals(signals);
        
        return signals;
      } catch (error) {
        console.error('Error refreshing trading signals:', error);
        
        // Show error state
        signalsBody.innerHTML = `
          <tr class="error-row">
            <td colspan="5">
              <i class="fas fa-exclamation-circle"></i>
              <span>Failed to load signals. Please try again.</span>
            </td>
          </tr>
        `;
        
        throw error;
      }
    },
    
    // Display signals
    displaySignals(signals) {
      const { signalsBody } = this.elements;
      if (!signalsBody) return;
      
      // Clear container
      signalsBody.innerHTML = '';
      
      // Create rows for each signal with staggered animation
      signals.forEach((signal, index) => {
        setTimeout(() => {
          const row = document.createElement('tr');
          
          // Calculate strength percentage
          const strengthPercent = (signal.strength / 10) * 100;
          
          // Create HTML content
          row.innerHTML = `
            <td>${signal.pair}</td>
            <td><span class="signal-badge ${signal.signal.toLowerCase()}">${signal.signal}</span></td>
            <td><span class="direction-arrow ${signal.direction}"><i class="fas fa-arrow-${this.getDirectionIcon(signal.direction)}"></i></span></td>
            <td>
              <div class="strength-meter">
                <div class="strength-bar" style="width: ${strengthPercent}%" aria-label="Strength level: ${signal.strength} out of 10"></div>
              </div>
              <span class="strength-value">${signal.strength}/10</span>
            </td>
            <td>
              <div class="indicators">
                <span class="indicator-bubble rsi ${signal.indicators.rsi}">RSI</span>
                <span class="indicator-bubble macd ${signal.indicators.macd}">MACD</span>
                <span class="indicator-bubble ema ${signal.indicators.ema}">EMA</span>
                <span class="indicator-bubble bb ${signal.indicators.bb}">BB</span>
              </div>
            </td>
          `;
          
          // Add to container
          signalsBody.appendChild(row);
          
          // Add animation class
          setTimeout(() => {
            row.classList.add('visible');
          }, 50);
        }, index * 100);
      });
    },
    
    // Get direction icon
    getDirectionIcon(direction) {
      switch (direction) {
        case 'up': return 'up';
        case 'down': return 'down';
        case 'stable':
        default: return 'minus';
      }
    }
  },
  
  // =================== PYTHON ANALYSIS INTEGRATION ===================
  
  pythonIntegration: {
    // Status
    isInitialized: false,
    lastReportData: null,
    lastUpdateTime: null,
    
    // Initialize Python integration
    async init() {
      try {
        // Mock API call to backend Python service
        await this.fetchForexAnalysisData();
        
        this.isInitialized = true;
        return true;
      } catch (error) {
        console.error('Failed to initialize Python integration:', error);
        this.isInitialized = false;
        return false;
      }
    },
    
    // Fetch forex analysis data from Python backend
    async fetchForexAnalysisData() {
      try {
        // In production, this would be an API endpoint that executes the Python code
        // For demo, we'll use the mocked API from the original file
        const response = await fetch('/api/forex-analysis');
        
        if (!response.ok) {
          throw new Error('Failed to fetch forex analysis data');
        }
        
        const data = await response.json();
        this.lastReportData = data;
        this.lastUpdateTime = new Date();
        
        return data;
      } catch (error) {
        console.error('Error fetching forex analysis data:', error);
        
        // For demo, return mock data
        const mockData = this.getMockForexAnalysisData();
        this.lastReportData = mockData;
        this.lastUpdateTime = new Date();
        
        return mockData;
      }
    },
    
    // Generate mock forex analysis data for testing
    getMockForexAnalysisData() {
      return {
        currentRates: [
          { currencyName: 'US Dollar', currencyCode: 'USD', rateToKES: 130.25, dailyChange: 0.75 },
          { currencyName: 'Euro', currencyCode: 'EUR', rateToKES: 141.80, dailyChange: -0.45 },
          { currencyName: 'British Pound', currencyCode: 'GBP', rateToKES: 166.35, dailyChange: 0.28 },
          { currencyName: 'Japanese Yen', currencyCode: 'JPY', rateToKES: 0.8742, dailyChange: -0.32 },
          { currencyName: 'UAE Dirham', currencyCode: 'AED', rateToKES: 35.46, dailyChange: 0.15 },
          { currencyName: 'South African Rand', currencyCode: 'ZAR', rateToKES: 6.92, dailyChange: -1.20 }
        ],
        historicalData: {
          'USD/KES': [
            { date: '2025-02-13', rate: 129.12 },
            { date: '2025-02-14', rate: 129.35 },
            { date: '2025-02-15', rate: 129.48 },
            // More historical data points...
            { date: '2025-03-12', rate: 130.15 },
            { date: '2025-03-13', rate: 130.25 }
          ],
          'EUR/KES': [
            // Similar structure for EUR/KES
          ],
          'GBP/KES': [
            // Similar structure for GBP/KES
          ]
        },
        forecast: {
          'USD/KES': [
            { date: '2025-03-14', rate: 130.42 },
            { date: '2025-03-15', rate: 130.65 },
            // More forecast data points...
            { date: '2025-04-12', rate: 132.75 }
          ],
          'EUR/KES': [
            // Similar structure for EUR/KES forecast
          ],
          'GBP/KES': [
            // Similar structure for GBP/KES forecast
          ]
        },
        insights: [
          "USD/KES shows an upward trend over the last month, indicating potential pressure on Kenyan importers.",
          "EUR/KES volatility has increased following recent European Central Bank policy announcements.",
          "East African regional currencies demonstrate strong correlation, suggesting common economic factors.",
          "Short-term technical indicators suggest USD/KES resistance at 123.50 levels.",
          "Seasonal patterns indicate potential KES strengthening during Q2 agricultural export period."
        ],
        marketSentiment: "Neutral", // Can be "Bullish", "Bearish", or "Neutral"
        predictions: [
          { currencyPair: 'USD/KES', change: 1.2, confidence: 'Medium' },
          { currencyPair: 'EUR/KES', change: -0.8, confidence: 'High' },
          { currencyPair: 'GBP/KES', change: 0.3, confidence: 'Medium' }
        ],
        tradingSignals: [
          {
            currencyPair: 'USD/KES',
            direction: 'BUY',
            strength: 7.5,
            indicators: {
              rsi: 'positive',
              macd: 'positive',
              ema: 'positive',
              bb: 'neutral'
            }
          },
          {
            currencyPair: 'EUR/KES',
            direction: 'SELL',
            strength: 6.0,
            indicators: {
              rsi: 'negative',
              macd: 'negative',
              ema: 'neutral',
              bb: 'negative'
            }
          }
        ],
        riskAnalysis: {
          'USD/KES': { annualVolatility: 8.5, var95: 1.2, es95: 1.8 },
          'EUR/KES': { annualVolatility: 9.2, var95: 1.4, es95: 2.1 },
          'GBP/KES': { annualVolatility: 10.5, var95: 1.7, es95: 2.5 }
        }
      };
    }
  },
  
  // =================== UTILITY FUNCTIONS ===================
  
  utils: {
    // Format date
    formatDate(date, type = 'full') {
      if (!(date instanceof Date)) {
        date = new Date(date);
      }
      
      const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      };
      
      const shortOptions = {
        month: 'short',
        day: 'numeric'
      };
      
      if (type === 'short') {
        return date.toLocaleDateString('en-US', shortOptions);
      }
      
      return date.toLocaleDateString('en-US', options);
    },
    
    // Format date and time
    formatDateTime(date) {
      if (!(date instanceof Date)) {
        date = new Date(date);
      }
      
      const timeOptions = {
        hour: '2-digit',
        minute: '2-digit'
      };
      
      const dateOptions = {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      };
      
      const timeStr = date.toLocaleTimeString('en-US', timeOptions);
      const dateStr = date.toLocaleDateString('en-US', dateOptions);
      
      return `${timeStr}, ${dateStr}`;
    },
    
    // Debounce function to limit function calls
    debounce(func, wait = 300) {
      let timeout;
      
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },
    
    // Throttle function for rate limiting
    throttle(func, limit = 300) {
      let inThrottle;
      
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    },
    
    // Format number with commas
    formatNumber(number, decimals = 2) {
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }).format(number);
    },
    
    // Generate a random ID
    generateId(prefix = 'pesaguru') {
      return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    },
    
    // Simple cache implementation
    cache: {
      data: {},
      
      get(key) {
        const item = this.data[key];
        
        if (!item) return null;
        
        // Check if expired
        if (item.expiry && item.expiry < Date.now()) {
          delete this.data[key];
          return null;
        }
        
        return item.value;
      },
      
      set(key, value, ttl = 300000) { // Default 5 minutes
        this.data[key] = {
          value,
          expiry: ttl ? Date.now() + ttl : null
        };
      },
      
      remove(key) {
        delete this.data[key];
      },
      
      clear() {
        this.data = {};
      }
    },
    
    // Deep clone an object
    deepClone(obj) {
      try {
        return JSON.parse(JSON.stringify(obj));
      } catch (error) {
        console.error('Deep clone error:', error);
        return null;
      }
    },
    
    // Safe JSON parse
    safeJsonParse(str, fallback = {}) {
      try {
        return JSON.parse(str);
      } catch (error) {
        console.error('JSON parse error:', error);
        return fallback;
      }
    },
    
    // Check if object is empty
    isEmptyObject(obj) {
      return obj && Object.keys(obj).length === 0 && obj.constructor === Object;
    },
    
    // Convert object to query string
    objectToQueryString(obj) {
      return Object.keys(obj)
        .filter(key => obj[key] !== undefined && obj[key] !== null)
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(obj[key])}`)
        .join('&');
    },
    
    // Capitalize first letter of string
    capitalize(string) {
      if (!string) return '';
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
    
    // Format currency
    formatCurrency(amount, currency = 'KES') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    },
    
    // Format percentage
    formatPercentage(value, decimals = 2) {
      return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
      }).format(value / 100);
    },
    
    // Get relative time string
    getRelativeTimeString(date) {
      if (!(date instanceof Date)) {
        date = new Date(date);
      }
      
      const now = new Date();
      const diffInSeconds = Math.floor((now - date) / 1000);
      
      if (diffInSeconds < 60) {
        return 'just now';
      }
      
      const diffInMinutes = Math.floor(diffInSeconds / 60);
      if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
      }
      
      const diffInHours = Math.floor(diffInMinutes / 60);
      if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
      }
      
      const diffInDays = Math.floor(diffInHours / 24);
      if (diffInDays < 7) {
        return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
      }
      
      return this.formatDate(date, 'short');
    }
  }
};

// Initialize the application when DOM content is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Start performance measurement
  PesaGuru.performance.startMeasure('initialization');
  
  // Initialize the app
  PesaGuru.init();
  
  // End performance measurement
  PesaGuru.performance.endMeasure('initialization');
  
  // Register service worker for offline support
  // PesaGuru.serviceWorker.register();
});

// For development & testing - Stub the API call with mock data
// In production, remove this code and implement the actual API integration
let originalFetch = window.fetch;
window.fetch = function(url) {
  if (url === '/api/forex-analysis') {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          ok: true,
          json: () => Promise.resolve(PesaGuru.pythonIntegration.getMockForexAnalysisData())
        });
      }, 500); // Simulate network delay
    });
  }
  return originalFetch.apply(this, arguments);
};