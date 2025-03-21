import authService from '../services/authService.js';

// Function to check if user is authenticated
export function checkAuth(redirectUrl = '/Authentication/login.html') {
  // Check if user is authenticated
  if (!authService.isAuthenticated()) {
    // Get current page path for redirect after login
    const currentPath = window.location.pathname;
    
    // Redirect to login page with return URL
    window.location.href = `${redirectUrl}?redirect=${encodeURIComponent(currentPath)}`;
    return false;
  }
  
  return true;
}

// Function to redirect if already authenticated
export function redirectIfAuth(redirectUrl = '/User_Profile_and_Settings/profile_overview.html') {
  // Check if user is already authenticated
  if (authService.isAuthenticated()) {
    window.location.href = redirectUrl;
    return true;
  }
  
  return false;
}

// Function to handle redirect after login
export function handleRedirectAfterLogin() {
  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const redirectPath = urlParams.get('redirect');
  
  // If redirect parameter exists, redirect there
  if (redirectPath) {
    window.location.href = redirectPath;
    return true;
  }
  
  return false;
}

// Function to apply auth check to a page
export function applyAuthCheck(redirectUrl = '/Authentication/login.html') {
  document.addEventListener('DOMContentLoaded', () => {
    checkAuth(redirectUrl);
  });
}

// Function to initialize login page with redirect handling
export function initLoginPage() {
  document.addEventListener('DOMContentLoaded', () => {
    // Redirect if already authenticated
    if (redirectIfAuth()) return;
    
    // Get login form
    const loginForm = document.getElementById('loginForm');
    
    // Add form submission handler
    loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      
      // Get form data
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      
      try {
        // Attempt login
        await authService.login(email, password);
        
        // Handle redirect after login
        if (!handleRedirectAfterLogin()) {
          // Default redirect
          window.location.href = '/User_Profile_and_Settings/profile_overview.html';
        }
      } catch (error) {
        // Handle login error
        const errorElement = document.getElementById('loginError');
        if (errorElement) {
          errorElement.textContent = error.message || 'Login failed. Please check your credentials.';
          errorElement.style.display = 'block';
        } else {
          alert('Login failed. Please check your credentials.');
        }
      }
    });
  });
}