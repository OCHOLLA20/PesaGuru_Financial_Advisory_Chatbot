// assets/js/services/financialGoalsService.js
import apiClient from '../apiClient.js';

export default {
  // Get all financial goals
  async getGoals() {
    return apiClient.get('/financial-goals');
  },
  
  // Get a specific goal
  async getGoal(goalId) {
    return apiClient.get(`/financial-goals/${goalId}`);
  },
  
  // Create a new goal
  async createGoal(goalData) {
    return apiClient.post('/financial-goals', goalData);
  },
  
  // Update an existing goal
  async updateGoal(goalId, goalData) {
    return apiClient.put(`/financial-goals/${goalId}`, goalData);
  },
  
  // Delete a goal
  async deleteGoal(goalId) {
    return apiClient.delete(`/financial-goals/${goalId}`);
  },
  
  // Track progress towards a goal
  async trackGoalProgress(goalId, progressData) {
    return apiClient.post(`/financial-goals/${goalId}/progress`, progressData);
  },
  
  // Get goal categories
  async getGoalCategories() {
    return apiClient.get('/financial-goals/categories');
  },
  
  // Get recommended savings plan for a goal
  async getRecommendedSavingsPlan(goalId) {
    return apiClient.get(`/financial-goals/${goalId}/savings-plan`);
  }
};