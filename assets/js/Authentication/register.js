import { validateEmail, validatePassword } from '../middleware/validationMiddleware.js';
import { saveAuthToken, redirectToIntended } from '../middleware/authMiddleware.js';
import apiClient from '../apiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('register-form');
  const fullNameInput = document.getElementById('full-name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm-password');
  const mobileInput = document.getElementById('mobile');
  const errorMessage = document.getElementById('error-message');
  const registerButton = document.getElementById('register-btn');
  
  // Field validation functions
  const validators = {
    fullName: (value) => {
      return value.trim().length >= 3;
    },
    email: (value) => {
      return validateEmail(value);
    },
    password: (value) => {
      return validatePassword(value);
    },
    confirmPassword: (value, password) => {
      return value === password;
    },
    mobile: (value) => {
      // Basic phone number validation
      return /^\d{10,15}$/.test(value.replace(/\D/g, ''));
    }
  };
  
  // Show specific field error
  const showFieldError = (field, message) => {
    const errorElement = document.getElementById(`${field}-error`);
    if (errorElement) {
      errorElement.textContent = message;
      errorElement.style.display = 'block';
      document.getElementById(field).classList.add('is-invalid');
    }
  };
  
  // Clear field error
  const clearFieldError = (field) => {
    const errorElement = document.getElementById(`${field}-error`);
    if (errorElement) {
      errorElement.textContent = '';
      errorElement.style.display = 'none';
      document.getElementById(field).classList.remove('is-invalid');
    }
  };
  
  // Clear all errors
  const clearAllErrors = () => {
    ['full-name', 'email', 'password', 'confirm-password', 'mobile'].forEach(field => {
      clearFieldError(field);
    });
    
    if (errorMessage) {
      errorMessage.textContent = '';
      errorMessage.style.display = 'none';
    }
  };
  
  // Setup input validation as user types
  if (fullNameInput) {
    fullNameInput.addEventListener('input', () => {
      const value = fullNameInput.value.trim();
      if (value.length > 0 && !validators.fullName(value)) {
        showFieldError('full-name', 'Name must be at least 3 characters');
      } else {
        clearFieldError('full-name');
      }
    });
  }
  
  if (emailInput) {
    emailInput.addEventListener('input', () => {
      const value = emailInput.value.trim();
      if (value.length > 0 && !validators.email(value)) {
        showFieldError('email', 'Please enter a valid email address');
      } else {
        clearFieldError('email');
      }
    });
  }
  
  if (passwordInput) {
    passwordInput.addEventListener('input', () => {
      const value = passwordInput.value;
      if (value.length > 0 && !validators.password(value)) {
        showFieldError('password', 'Password must be at least 8 characters with letters and numbers');
      } else {
        clearFieldError('password');
      }
      
      // Check confirm password match if it has a value
      if (confirmPasswordInput && confirmPasswordInput.value.length > 0) {
        if (!validators.confirmPassword(confirmPasswordInput.value, value)) {
          showFieldError('confirm-password', 'Passwords do not match');
        } else {
          clearFieldError('confirm-password');
        }
      }
    });
  }
  
  if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener('input', () => {
      const value = confirmPasswordInput.value;
      const passwordValue = passwordInput ? passwordInput.value : '';
      
      if (value.length > 0 && !validators.confirmPassword(value, passwordValue)) {
        showFieldError('confirm-password', 'Passwords do not match');
      } else {
        clearFieldError('confirm-password');
      }
    });
  }
  
  if (mobileInput) {
    mobileInput.addEventListener('input', () => {
      const value = mobileInput.value.trim();
      if (value.length > 0 && !validators.mobile(value)) {
        showFieldError('mobile', 'Please enter a valid phone number');
      } else {
        clearFieldError('mobile');
      }
    });
  }
  
  // Handle form submission
  if (registerForm) {
    registerForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      clearAllErrors();
      
      // Get form values
      const fullName = fullNameInput ? fullNameInput.value.trim() : '';
      const email = emailInput ? emailInput.value.trim() : '';
      const password = passwordInput ? passwordInput.value : '';
      const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
      const mobile = mobileInput ? mobileInput.value.trim() : '';
      
      // Validate all fields
      let isValid = true;
      
      if (!validators.fullName(fullName)) {
        showFieldError('full-name', 'Name must be at least 3 characters');
        isValid = false;
      }
      
      if (!validators.email(email)) {
        showFieldError('email', 'Please enter a valid email address');
        isValid = false;
      }
      
      if (!validators.password(password)) {
        showFieldError('password', 'Password must be at least 8 characters with letters and numbers');
        isValid = false;
      }
      
      if (!validators.confirmPassword(confirmPassword, password)) {
        showFieldError('confirm-password', 'Passwords do not match');
        isValid = false;
      }
      
      if (!validators.mobile(mobile)) {
        showFieldError('mobile', 'Please enter a valid phone number');
        isValid = false;
      }
      
      if (!isValid) {
        return;
      }
      
      // Disable submit button while processing
      if (registerButton) {
        registerButton.disabled = true;
        registerButton.textContent = 'Creating Account...';
      }
      
      try {
        // Prepare registration data
        const userData = {
          fullName,
          email,
          password,
          mobile
        };
        
        // Send registration request to server
        const response = await apiClient.post('/auth/register', userData);
        
        // Handle successful registration
        if (response.data && response.data.token) {
          // Save authentication token
          saveAuthToken(response.data.token);
          
          // Show success message if needed
          const successMessage = document.getElementById('success-message');
          if (successMessage) {
            successMessage.textContent = 'Registration successful! Redirecting...';
            successMessage.style.display = 'block';
          }
          
          // Redirect to dashboard or intended page
          setTimeout(() => {
            redirectToIntended('/dashboard.html');
          }, 1500);
        } else {
          // Registration succeeded but no token returned
          window.location.href = '/login.html?registered=true';
        }
      } catch (error) {
        console.error('Registration error:', error);
        
        // Handle specific error cases
        if (error.response) {
          const { status, data } = error.response;
          
          if (status === 422 && data.errors) {
            // Validation errors from server
            Object.entries(data.errors).forEach(([field, message]) => {
              const fieldMap = {
                'fullName': 'full-name',
                'email': 'email',
                'password': 'password',
                'mobile': 'mobile'
              };
              
              const mappedField = fieldMap[field] || field;
              showFieldError(mappedField, Array.isArray(message) ? message[0] : message);
            });
          } else if (status === 409) {
            // Email already exists
            showFieldError('email', 'This email is already registered');
          } else {
            // General error
            if (errorMessage) {
              errorMessage.textContent = data.message || 'Registration failed. Please try again.';
              errorMessage.style.display = 'block';
            }
          }
        } else {
          // Network or other error
          if (errorMessage) {
            errorMessage.textContent = 'Connection error. Please check your internet and try again.';
            errorMessage.style.display = 'block';
          }
        }
      } finally {
        // Re-enable submit button
        if (registerButton) {
          registerButton.disabled = false;
          registerButton.textContent = 'Register';
        }
      }
    });
  }
  
  // Handle login link
  const loginLink = document.getElementById('login-link');
  if (loginLink) {
    loginLink.addEventListener('click', (event) => {
      event.preventDefault();
      window.location.href = '/login.html';
    });
  }
  
  // Check if user is already logged in
  if (document.cookie.includes('auth_token=') || localStorage.getItem('auth_token')) {
    // Redirect to dashboard
    window.location.href = '/dashboard.html';
  }
});