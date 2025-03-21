// assets/js/apiClient.js
class ApiClient {
    constructor(baseUrl = '/api') {
      this.baseUrl = baseUrl;
      this.token = localStorage.getItem('auth_token');
    }
  
    // Set authentication token
    setToken(token) {
      this.token = token;
      localStorage.setItem('auth_token', token);
    }
  
    // Clear authentication token
    clearToken() {
      this.token = null;
      localStorage.removeItem('auth_token');
    }
  
    // Headers for authenticated requests
    getHeaders() {
      const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      };
  
      if (this.token) {
        headers['Authorization'] = `Bearer ${this.token}`;
      }
  
      return headers;
    }
  
    // Handle API responses and errors
    async handleResponse(response) {
      if (!response.ok) {
        if (response.status === 401) {
          this.clearToken();
          window.location.href = '/Authentication/login.html';
          throw new Error('Authentication required');
        }
  
        const error = await response.json();
        throw new Error(error.message || 'API request failed');
      }
  
      return response.json();
    }
  
    // GET request
    async get(endpoint) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders()
      });
      return this.handleResponse(response);
    }
  
    // POST request
    async post(endpoint, data) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      });
      return this.handleResponse(response);
    }
  
    // PUT request
    async put(endpoint, data) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: JSON.stringify(data)
      });
      return this.handleResponse(response);
    }
  
    // DELETE request
    async delete(endpoint) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'DELETE',
        headers: this.getHeaders()
      });
      return this.handleResponse(response);
    }
  }
  
  // Create and export a singleton instance
  const apiClient = new ApiClient();
  export default apiClient;