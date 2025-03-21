// assets/js/services/marketDataService.js
import apiClient from '../apiClient.js';

export default {
  // Get NSE stocks data
  async getNseStocks() {
    return apiClient.get('/market-data/nse-stocks');
  },
  
  // Get specific stock details
  async getStockDetails(symbol) {
    return apiClient.get(`/market-data/stocks/${symbol}`);
  },
  
  // Get forex rates
  async getForexRates() {
    return apiClient.get('/market-data/forex-rates');
  },
  
  // Get interest rates
  async getInterestRates() {
    return apiClient.get('/market-data/interest-rates');
  },
  
  // Get cryptocurrency trends
  async getCryptoTrends() {
    return apiClient.get('/market-data/crypto-trends');
  },
  
  // Get historical data for a symbol
  async getHistoricalData(symbol, period) {
    return apiClient.get(`/market-data/historical/${symbol}?period=${period}`);
  },
  
  // Get market news
  async getMarketNews() {
    return apiClient.get('/market-data/news');
  }
};