// assets/js/services/authService.js
import apiClient from '../apiClient.js';

export default {
  // Login user
  async login(email, password) {
    const data = await apiClient.post('/auth/login', { email, password });
    if (data.token) {
      apiClient.setToken(data.token);
    }
    return data;
  },

  // Register new user
  async register(userData) {
    return apiClient.post('/auth/register', userData);
  },

  // Logout user
  async logout() {
    const result = await apiClient.post('/auth/logout', {});
    apiClient.clearToken();
    return result;
  },

  // Request password reset
  async forgotPassword(email) {
    return apiClient.post('/auth/forgot-password', { email });
  },

  // Reset password with token
  async resetPassword(token, password, passwordConfirmation) {
    return apiClient.post('/auth/reset-password', {
      token,
      password,
      password_confirmation: passwordConfirmation
    });
  },
  
  // Check if user is authenticated
  isAuthenticated() {
    return !!apiClient.token;
  }
};