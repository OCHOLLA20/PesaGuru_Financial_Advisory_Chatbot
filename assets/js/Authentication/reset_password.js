// C:\xampp\htdocs\PesaGuru\client\assets\js\Authentication\reset_password.js
import { validatePassword } from '../middleware/validationMiddleware.js';
import apiClient from '../apiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  const resetPasswordForm = document.getElementById('reset-password-form');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm-password');
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');
  const resetButton = document.getElementById('reset-btn');
  
  // Get reset token from URL
  const urlParams = new URLSearchParams(window.location.search);
  const resetToken = urlParams.get('token');
  
  // Redirect if no token found
  if (!resetToken) {
    window.location.href = '/forgot-password.html';
    return;
  }
  
  // Validate password strength
  const isPasswordValid = (password) => {
    return validatePassword(password);
  };
  
  // Validate passwords match
  const doPasswordsMatch = (password, confirmPassword) => {
    return password === confirmPassword;
  };
  
  // Show field error
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
  
  // Set up real-time validation for password
  if (passwordInput) {
    passwordInput.addEventListener('input', () => {
      const password = passwordInput.value;
      
      if (password.length > 0 && !isPasswordValid(password)) {
        showFieldError('password', 'Password must be at least 8 characters with letters and numbers');
      } else {
        clearFieldError('password');
      }
      
      // Check confirm password if it has a value
      if (confirmPasswordInput && confirmPasswordInput.value) {
        if (!doPasswordsMatch(password, confirmPasswordInput.value)) {
          showFieldError('confirm-password', 'Passwords do not match');
        } else {
          clearFieldError('confirm-password');
        }
      }
    });
  }
  
  // Set up real-time validation for confirm password
  if (confirmPasswordInput) {
    confirmPasswordInput.addEventListener('input', () => {
      const confirmPassword = confirmPasswordInput.value;
      const password = passwordInput ? passwordInput.value : '';
      
      if (confirmPassword.length > 0 && !doPasswordsMatch(password, confirmPassword)) {
        showFieldError('confirm-password', 'Passwords do not match');
      } else {
        clearFieldError('confirm-password');
      }
    });
  }
  
  // Handle form submission
  if (resetPasswordForm) {
    resetPasswordForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      
      // Clear previous messages
      if (errorMessage) {
        errorMessage.textContent = '';
        errorMessage.style.display = 'none';
      }
      
      if (successMessage) {
        successMessage.textContent = '';
        successMessage.style.display = 'none';
      }
      
      // Get form values
      const password = passwordInput ? passwordInput.value : '';
      const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
      
      // Validate input
      let isValid = true;
      
      if (!isPasswordValid(password)) {
        showFieldError('password', 'Password must be at least 8 characters with letters and numbers');
        isValid = false;
      } else {
        clearFieldError('password');
      }
      
      if (!doPasswordsMatch(password, confirmPassword)) {
        showFieldError('confirm-password', 'Passwords do not match');
        isValid = false;
      } else {
        clearFieldError('confirm-password');
      }
      
      if (!isValid) {
        return;
      }
      
      // Disable button while processing
      if (resetButton) {
        resetButton.disabled = true;
        resetButton.textContent = 'Processing...';
      }
      
      try {
        // Send reset password request to server
        await apiClient.post('/auth/reset-password', {
          token: resetToken,
          password: password,
          confirmPassword: confirmPassword
        });
        
        // Show success message
        if (successMessage) {
          successMessage.textContent = 'Password has been reset successfully';
          successMessage.style.display = 'block';
        }
        
        // Clear form
        resetPasswordForm.reset();
        
        // Redirect to login page after a delay
        setTimeout(() => {
          window.location.href = '/login.html?reset=success';
        }, 3000);
      } catch (error) {
        console.error('Password reset error:', error);
        
        // Handle specific error cases
        if (error.response) {
          const { status, data } = error.response;
          
          if (status === 400 && data.errors) {
            // Validation errors
            Object.entries(data.errors).forEach(([field, message]) => {
              const fieldMap = {
                'password': 'password',
                'confirmPassword': 'confirm-password'
              };
              
              const mappedField = fieldMap[field] || field;
              showFieldError(mappedField, Array.isArray(message) ? message[0] : message);
            });
          } else if (status === 404 || status === 410) {
            // Token not found or expired
            if (errorMessage) {
              errorMessage.textContent = 'This password reset link has expired or is invalid';
              errorMessage.style.display = 'block';
            }
            
            // Redirect to forgot password page after a delay
            setTimeout(() => {
              window.location.href = '/forgot-password.html?expired=true';
            }, 3000);
          } else {
            // General error
            if (errorMessage) {
              errorMessage.textContent = data.message || 'Failed to reset password. Please try again.';
              errorMessage.style.display = 'block';
            }
          }
        } else {
          // Network error
          if (errorMessage) {
            errorMessage.textContent = 'Connection error. Please check your internet and try again.';
            errorMessage.style.display = 'block';
          }
        }
      } finally {
        // Re-enable button
        if (resetButton) {
          resetButton.disabled = false;
          resetButton.textContent = 'Reset Password';
        }
      }
    });
  }
  
  // Handle back to login button if present
  const backToLoginBtn = document.getElementById('back-to-login');
  if (backToLoginBtn) {
    backToLoginBtn.addEventListener('click', (event) => {
      event.preventDefault();
      window.location.href = '/login.html';
    });
  }
});