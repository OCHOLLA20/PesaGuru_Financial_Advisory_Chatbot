// C:\xampp\htdocs\PesaGuru\client\assets\js\Authentication\logout.js
import { handleLogout } from '../middleware/authMiddleware.js';
import apiClient from '../apiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  // Get logout button element
  const logoutButton = document.getElementById('logout-btn');
  
  if (logoutButton) {
    // Add click event listener to logout button
    logoutButton.addEventListener('click', async (event) => {
      event.preventDefault();
      
      try {
        // Call API to invalidate session/token on server side
        await apiClient.post('/auth/logout');
        
        // Handle client-side logout (clear local storage, cookies, etc.)
        handleLogout();
        
        // Redirect to login page or home page
        window.location.href = '/index.html';
      } catch (error) {
        console.error('Error during logout:', error);
        // Attempt client-side logout even if API call fails
        handleLogout();
        window.location.href = '/index.html';
      }
    });
  }
  
  // Check for logout parameter in URL (for logout links)
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('logout') === 'true') {
    // Perform logout immediately if accessed via logout link
    handleLogout();
    // Remove the parameter from URL
    window.history.replaceState({}, document.title, window.location.pathname);
    // Redirect to login page
    window.location.href = '/index.html';
  }
});