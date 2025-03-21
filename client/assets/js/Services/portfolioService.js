// assets/js/services/portfolioService.js
import apiClient from '../apiClient.js';

export default {
  // Get user portfolio
  async getPortfolio() {
    return apiClient.get('/portfolio');
  },
  
  // Add investment to portfolio
  async addInvestment(investmentData) {
    return apiClient.post('/portfolio/investments', investmentData);
  },
  
  // Update investment
  async updateInvestment(investmentId, investmentData) {
    return apiClient.put(`/portfolio/investments/${investmentId}`, investmentData);
  },
  
  // Delete investment
  async deleteInvestment(investmentId) {
    return apiClient.delete(`/portfolio/investments/${investmentId}`);
  },
  
  // Get portfolio performance
  async getPerformance(period) {
    return apiClient.get(`/portfolio/performance?period=${period}`);
  },
  
  // Get investment recommendations
  async getRecommendations() {
    return apiClient.get('/portfolio/recommendations');
  },
  
  // Get risk assessment
  async getRiskAssessment() {
    return apiClient.get('/portfolio/risk-assessment');
  }
};