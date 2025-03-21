import { validateEmail } from '../middleware/validationMiddleware.js';
import apiClient from '../apiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  // Get DOM elements
  const forgotPasswordForm = document.getElementById('forgot-password-form');
  const emailInput = document.getElementById('email');
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');
  const submitButton = document.getElementById('submit-btn');
  const backToLoginBtn = document.getElementById('back-to-login');
  
  // Track submission status to prevent duplicate submissions
  let isSubmitting = false;

  /**
   * Display error message with specified text
   * @param {string} message - Error message to display
   */
  const showError = (message) => {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    successMessage.style.display = 'none';
    // Add shake animation for better UX
    errorMessage.classList.add('shake');
    // Remove animation class after animation completes
    setTimeout(() => errorMessage.classList.remove('shake'), 500);
    // Set focus to email input for accessibility
    emailInput.focus();
  };

  /**
   * Display success message with specified text
   * @param {string} message - Success message to display
   */
  const showSuccess = (message) => {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    errorMessage.style.display = 'none';
  };

  /**
   * Set button state during form submission
   * @param {boolean} loading - Whether the form is submitting
   */
  const setButtonState = (loading) => {
    isSubmitting = loading;
    submitButton.disabled = loading;
    submitButton.setAttribute('aria-busy', loading ? 'true' : 'false');
    
    if (loading) {
      // Save original text and show loading spinner
      submitButton.dataset.originalText = submitButton.textContent;
      submitButton.innerHTML = '<span class="spinner"></span> Processing...';
    } else {
      // Restore original text
      submitButton.textContent = submitButton.dataset.originalText || 'Reset Password';
    }
  };

  // Handle form submission
  if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      
      // Prevent multiple submissions
      if (isSubmitting) return;
      
      // Reset messages
      errorMessage.style.display = 'none';
      successMessage.style.display = 'none';
      
      // Get and validate email
      const email = emailInput.value.trim();
      
      if (!email) {
        showError('Please enter your email address');
        return;
      }
      
      if (!validateEmail(email)) {
        showError('Please enter a valid email address');
        return;
      }
      
      // Set loading state
      setButtonState(true);
      
      try {
        // Add CSRF token if your app uses it
        // const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        
        // Send forgot password request to server
        const response = await apiClient.post('/auth/forgot-password', { 
          email,
          // csrfToken
        });
        
        // Show success message
        showSuccess('Password reset instructions have been sent to your email. Please check your inbox, including spam folder.');
        
        // Clear input field
        emailInput.value = '';
        
        // Redirect after a delay with countdown
        let secondsLeft = 5;
        const countdownInterval = setInterval(() => {
          secondsLeft--;
          if (secondsLeft <= 0) {
            clearInterval(countdownInterval);
            window.location.href = '/index.html';
          } else {
            successMessage.textContent = `Password reset instructions have been sent to your email. Redirecting in ${secondsLeft} seconds...`;
          }
        }, 1000);
        
      } catch (error) {
        console.error('Error in forgot password process:', error);
        
        // Handle different error scenarios
        if (error.response) {
          switch (error.response.status) {
            case 404:
              showError('Email not found in our records');
              break;
            case 429:
              showError('Too many attempts. Please try again later');
              break;
            case 403:
              showError('Access forbidden. Please try again later');
              break;
            default:
              showError(error.response.data?.message || 'An error occurred. Please try again later');
          }
        } else if (error.request) {
          // Network error
          showError('Network error. Please check your internet connection');
        } else {
          showError('An unexpected error occurred. Please try again later');
        }
      } finally {
        // Reset button state
        setButtonState(false);
      }
    });
  }

  // Live email validation as user types
  if (emailInput) {
    // Debounce function to limit validation frequency
    const debounce = (func, delay) => {
      let debounceTimer;
      return function() {
        const context = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => func.apply(context, args), delay);
      };
    };
    
    // Validate email with debounce
    emailInput.addEventListener('input', debounce(() => {
      const email = emailInput.value.trim();
      
      if (email.length > 0) {
        if (!validateEmail(email)) {
          emailInput.classList.add('is-invalid');
          emailInput.setAttribute('aria-invalid', 'true');
        } else {
          emailInput.classList.remove('is-invalid');
          emailInput.setAttribute('aria-invalid', 'false');
          // If there was an error message about invalid email, clear it
          if (errorMessage.textContent.includes('valid email')) {
            errorMessage.style.display = 'none';
          }
        }
      } else {
        emailInput.classList.remove('is-invalid');
        emailInput.setAttribute('aria-invalid', 'false');
      }
    }, 300));
  }

  // Handle back to login button
  if (backToLoginBtn) {
    backToLoginBtn.addEventListener('click', (event) => {
      event.preventDefault();
      window.location.href = '/index.html';
    });
  }
  
  // Add keyboard accessibility - Enter key for submission
  emailInput?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !submitButton.disabled) {
      event.preventDefault();
      submitButton.click();
    }
  });
  
  // Support for "Need help?" chatbot integration
  const chatbotHelpBtn = document.getElementById('chatbot-help');
  if (chatbotHelpBtn) {
    chatbotHelpBtn.addEventListener('click', (event) => {
      event.preventDefault();
      // Launch PesaGuru chatbot with context
      window.PesaGuruChatbot?.launch('password_reset_help');
    });
  }
});