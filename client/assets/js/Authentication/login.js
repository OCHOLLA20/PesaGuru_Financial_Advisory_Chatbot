document.addEventListener('DOMContentLoaded', function() {
    // API endpoints
    const API_BASE_URL = 'https://api.pesaguru.co.ke/v1';
    const AUTH_ENDPOINTS = {
      LOGIN: `${API_BASE_URL}/auth/login`,
      OTP_REQUEST: `${API_BASE_URL}/auth/otp/request`,
      OTP_VERIFY: `${API_BASE_URL}/auth/otp/verify`,
      REFRESH_TOKEN: `${API_BASE_URL}/auth/refresh`,
      LOGOUT: `${API_BASE_URL}/auth/logout`
    };
  
    // Get DOM elements
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const loginBtn = document.getElementById('loginBtn');
    const languageSelector = document.getElementById('languageSelector');
    const otpLoginBtn = document.getElementById('otpLoginBtn');
    const liveChatBtn = document.getElementById('liveChat');
    const rememberMeCheckbox = document.getElementById('rememberMe');
    
    // Add a theme toggle button (it's in CSS but missing from HTML)
    const themeToggleBtn = document.createElement('button');
    themeToggleBtn.className = 'theme-toggle';
    themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
    themeToggleBtn.setAttribute('aria-label', 'Toggle dark mode');
    themeToggleBtn.setAttribute('title', 'Toggle dark mode');
    document.body.appendChild(themeToggleBtn);
    
    // Check if user has a saved theme preference
    initTheme();
    
    // Check if user has saved credentials and if there's an active session
    initSavedCredentials();
    checkExistingSession();
    
    // Add event listeners
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', togglePasswordVisibility);
    }
    
    if (languageSelector) {
        languageSelector.addEventListener('change', changeLanguage);
    }
    
    if (otpLoginBtn) {
        otpLoginBtn.addEventListener('click', handleOtpLogin);
    }
    
    if (liveChatBtn) {
        liveChatBtn.addEventListener('click', openLiveChat);
    }
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
    
    /**
     * Check if user already has a valid session
     */
    function checkExistingSession() {
        const token = getAuthToken();
        
        if (token) {
            // Validate token with backend
            fetch(`${API_BASE_URL}/auth/validate`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (response.ok) {
                    // Token is valid, redirect to dashboard
                    window.location.href = '../dashboard.html';
                } else if (response.status === 401) {
                    // Token expired, try to refresh
                    return refreshAuthToken();
                } else {
                    // Other error, clear tokens
                    clearAuthTokens();
                }
            })
            .catch(error => {
                console.error('Session validation error:', error);
                clearAuthTokens();
            });
        }
    }
    
    /**
     * Handle login form submission
     * @param {Event} event - The form submit event
     */
    function handleLogin(event) {
        event.preventDefault();
        
        // Get form values
        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const rememberMe = rememberMeCheckbox.checked;
        
        // Basic form validation
        if (!validateForm(email, password)) {
            return;
        }
        
        // Show loading state
        setLoadingState(true);
        
        // If remember me is checked, store the email in localStorage
        if (rememberMe) {
            localStorage.setItem('pesaguru_email', email);
        } else {
            localStorage.removeItem('pesaguru_email');
        }
        
        // Prepare login payload
        const loginData = {
            email: email,
            password: password,
            device_info: getDeviceInfo()
        };
        
        // Make API request
        fetch(AUTH_ENDPOINTS.LOGIN, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept-Language': getCurrentLanguage(),
                'X-App-Version': '1.0.0'
            },
            body: JSON.stringify(loginData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Login failed');
                });
            }
            return response.json();
        })
        .then(data => {
            // Store auth tokens securely
            storeAuthTokens(data.access_token, data.refresh_token, rememberMe);
            
            // Store user profile data
            if (data.user) {
                localStorage.setItem('pesaguru_user', JSON.stringify({
                    id: data.user.id,
                    name: data.user.name,
                    email: data.user.email,
                    phone: data.user.phone,
                    profile_image: data.user.profile_image
                }));
            }
            
            // Track successful login
            trackLoginEvent('email_password', true);
            
            // Redirect to dashboard
            window.location.href = '../dashboard.html';
        })
        .catch(error => {
            console.error('Login failed:', error);
            
            // Check for specific error codes to provide better UX
            if (error.message.includes('locked')) {
                showError('Your account is locked. Please contact support or reset your password.');
            } else if (error.message.includes('verification')) {
                showError('Please verify your email address first. Check your inbox for a verification link.');
                // Could redirect to verification page
                // window.location.href = 'verification.html?email=' + encodeURIComponent(email);
            } else {
                showError(error.message || 'Invalid email or password. Please try again.');
            }
            
            // Track failed login
            trackLoginEvent('email_password', false, error.message);
            
            setLoadingState(false);
        });
    }
    
    /**
     * Refresh the auth token using refresh token
     * @returns {Promise} - Promise that resolves when token is refreshed
     */
    function refreshAuthToken() {
        const refreshToken = getRefreshToken();
        
        if (!refreshToken) {
            clearAuthTokens();
            return Promise.reject(new Error('No refresh token available'));
        }
        
        return fetch(AUTH_ENDPOINTS.REFRESH_TOKEN, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-App-Version': '1.0.0'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Unable to refresh session');
            }
            return response.json();
        })
        .then(data => {
            storeAuthTokens(data.access_token, data.refresh_token, true);
            
            // Token refreshed successfully, redirect to dashboard
            window.location.href = '../dashboard.html';
        })
        .catch(error => {
            console.error('Token refresh failed:', error);
            clearAuthTokens();
            showError('Your session has expired. Please log in again.');
            return Promise.reject(error);
        });
    }
    
    /**
     * Handle OTP login button click - initiates the OTP login flow
     */
    function handleOtpLogin() {
        const email = emailInput.value.trim();
        
        if (!email) {
            emailInput.style.borderColor = 'var(--error-color)';
            showError('Please enter your email or phone number to receive OTP');
            return;
        }
        
        // Show loading state
        setLoadingState(true);
        
        // Determine if input is email or phone
        const isPhone = !email.includes('@');
        const otpData = {
            [isPhone ? 'phone' : 'email']: email,
            device_info: getDeviceInfo()
        };
        
        // Request OTP from server
        fetch(AUTH_ENDPOINTS.OTP_REQUEST, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept-Language': getCurrentLanguage(),
                'X-App-Version': '1.0.0'
            },
            body: JSON.stringify(otpData)
        })
        .then(response => {
            setLoadingState(false);
            
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to send OTP');
                });
            }
            
            return response.json();
        })
        .then(data => {
            // Store request ID for verification
            sessionStorage.setItem('otp_request_id', data.request_id);
            
            // Store contact info for verification page
            sessionStorage.setItem('otp_contact', email);
            
            // Redirect to OTP verification page
            window.location.href = `otp-verification.html?method=${isPhone ? 'phone' : 'email'}`;
        })
        .catch(error => {
            console.error('OTP request failed:', error);
            showError(error.message || 'Could not send OTP. Please try again.');
            setLoadingState(false);
        });
    }
    
    /**
     * Get device information for security tracking
     * @returns {Object} - Device info object
     */
    function getDeviceInfo() {
        return {
            platform: navigator.platform,
            user_agent: navigator.userAgent,
            screen_resolution: `${window.screen.width}x${window.screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language
        };
    }
    
    /**
     * Securely store authentication tokens
     * @param {string} accessToken - JWT access token
     * @param {string} refreshToken - JWT refresh token
     * @param {boolean} rememberMe - Whether to store tokens persistently
     */
    function storeAuthTokens(accessToken, refreshToken, rememberMe) {
        if (rememberMe) {
            // For persistent login, store in localStorage (in production, consider more secure options)
            localStorage.setItem('pesaguru_access_token', accessToken);
            localStorage.setItem('pesaguru_refresh_token', refreshToken);
        } else {
            // For session-only login, use sessionStorage which is cleared on tab close
            sessionStorage.setItem('pesaguru_access_token', accessToken);
            sessionStorage.setItem('pesaguru_refresh_token', refreshToken);
        }
        
        // Store token expiry time (if available in decoded JWT)
        try {
            const tokenParts = accessToken.split('.');
            if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                if (payload.exp) {
                    const storage = rememberMe ? localStorage : sessionStorage;
                    storage.setItem('pesaguru_token_expiry', payload.exp * 1000); // Convert to milliseconds
                }
            }
        } catch (e) {
            console.error('Failed to parse token expiry:', e);
        }
    }
    
    /**
     * Get the current auth token from storage
     * @returns {string|null} - JWT token or null if not found
     */
    function getAuthToken() {
        return localStorage.getItem('pesaguru_access_token') || 
               sessionStorage.getItem('pesaguru_access_token');
    }
    
    /**
     * Get the refresh token from storage
     * @returns {string|null} - Refresh token or null if not found
     */
    function getRefreshToken() {
        return localStorage.getItem('pesaguru_refresh_token') || 
               sessionStorage.getItem('pesaguru_refresh_token');
    }
    
    /**
     * Clear all auth tokens from storage
     */
    function clearAuthTokens() {
        // Clear from both storage types to be safe
        localStorage.removeItem('pesaguru_access_token');
        localStorage.removeItem('pesaguru_refresh_token');
        localStorage.removeItem('pesaguru_token_expiry');
        
        sessionStorage.removeItem('pesaguru_access_token');
        sessionStorage.removeItem('pesaguru_refresh_token');
        sessionStorage.removeItem('pesaguru_token_expiry');
    }
    
    /**
     * Track login events for analytics
     * @param {string} method - Login method used
     * @param {boolean} success - Whether login was successful
     * @param {string} error - Error message if any
     */
    function trackLoginEvent(method, success, error = null) {
        // Analytics event tracking
        const eventData = {
            event: 'login_attempt',
            login_method: method,
            success: success,
            error: error,
            timestamp: new Date().toISOString()
        };
        
        // Send to analytics endpoint (non-blocking)
        fetch(`${API_BASE_URL}/analytics/event`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData),
            // Don't wait for response
            keepalive: true
        }).catch(err => console.error('Analytics error:', err));
    }
    
    /**
     * Get current language setting
     * @returns {string} - Current language code
     */
    function getCurrentLanguage() {
        return localStorage.getItem('pesaguru_language') || 'en';
    }
    
    /**
     * Validate the form inputs
     * @param {string} email - The email or phone input
     * @param {string} password - The password input
     * @returns {boolean} - True if valid, false otherwise
     */
    function validateForm(email, password) {
        // Reset previous error styles
        emailInput.style.borderColor = '';
        passwordInput.style.borderColor = '';
        
        let isValid = true;
        
        // Validate email/phone
        if (!email) {
            emailInput.style.borderColor = 'var(--error-color)';
            showError('Email or phone number is required');
            isValid = false;
        } else if (isEmail(email) && !validateEmail(email)) {
            emailInput.style.borderColor = 'var(--error-color)';
            showError('Please enter a valid email address');
            isValid = false;
        } else if (!isEmail(email) && !validatePhone(email)) {
            emailInput.style.borderColor = 'var(--error-color)';
            showError('Please enter a valid phone number (e.g., +254XXXXXXXXX)');
            isValid = false;
        }
        
        // Validate password
        if (!password) {
            passwordInput.style.borderColor = 'var(--error-color)';
            showError('Password is required');
            isValid = false;
        } else if (password.length < 6) {
            passwordInput.style.borderColor = 'var(--error-color)';
            showError('Password must be at least 6 characters');
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Check if the input looks like an email
     * @param {string} input - Input to check
     * @returns {boolean} - True if it looks like an email
     */
    function isEmail(input) {
        return input.includes('@');
    }
    
    /**
     * Validate email format
     * @param {string} email - Email to validate
     * @returns {boolean} - True if valid
     */
    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    /**
     * Validate phone number format
     * @param {string} phone - Phone to validate
     * @returns {boolean} - True if valid
     */
    function validatePhone(phone) {
        // Allow for international format with + and digits
        // Kenyan numbers start with +254 or 0
        const re = /^(\+254|0)[7|1][0-9]{8}$/;
        return re.test(phone);
    }
    
    /**
     * Display error message
     * @param {string} message - Error message to display
     */
    function showError(message) {
        // Remove any existing error
        removeError();
        
        // Create error element
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = 'var(--error-color)';
        errorDiv.style.marginBottom = '1rem';
        errorDiv.style.fontSize = '0.9rem';
        errorDiv.textContent = message;
        
        // Insert before the login button
        loginForm.insertBefore(errorDiv, loginBtn.parentNode);
        
        // Automatically remove after 5 seconds
        setTimeout(removeError, 5000);
    }
    
    /**
     * Remove error message
     */
    function removeError() {
        const errorDiv = document.querySelector('.error-message');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
    
    /**
     * Set loading state for login button
     * @param {boolean} isLoading - Whether to show loading state
     */
    function setLoadingState(isLoading) {
        if (isLoading) {
            loginBtn.classList.add('btn-loading');
            loginBtn.disabled = true;
            
            // Also disable OTP button
            if (otpLoginBtn) {
                otpLoginBtn.disabled = true;
            }
        } else {
            loginBtn.classList.remove('btn-loading');
            loginBtn.disabled = false;
            
            // Re-enable OTP button
            if (otpLoginBtn) {
                otpLoginBtn.disabled = false;
            }
        }
    }
    
    /**
     * Toggle password visibility
     */
    function togglePasswordVisibility() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        
        // Toggle icon
        const icon = togglePasswordBtn.querySelector('i');
        if (icon) {
            icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
        }
    }
    
    /**
     * Change language based on selector
     */
    function changeLanguage() {
        const selectedLanguage = languageSelector.value;
        localStorage.setItem('pesaguru_language', selectedLanguage);
        
        // Load language strings from API
        fetch(`${API_BASE_URL}/localization/${selectedLanguage}`)
            .then(response => response.json())
            .then(langData => {
                // Update page text with new language strings
                updatePageLanguage(langData);
            })
            .catch(error => {
                console.error('Error loading language:', error);
                // Fallback to hardcoded translations for demo
                fallbackLanguageUpdate(selectedLanguage);
            });
    }
    
    /**
     * Update page text with language data from API
     * @param {Object} langData - Language strings from API
     */
    function updatePageLanguage(langData) {
        // Map each element to its corresponding language key
        const elementsToUpdate = {
            '.welcome-text': 'welcome_text',
            '.form-label[for="email"]': 'email_label',
            '.form-label[for="password"]': 'password_label',
            'label[for="rememberMe"]': 'remember_me',
            '.forgot-password': 'forgot_password',
            '.btn-text': 'login_button',
            '.divider span': 'or_text',
            '.otp-btn': 'otp_button',
            '.signup-link': 'signup_link'
        };
        
        // Update each element with the corresponding language string
        for (const [selector, key] of Object.entries(elementsToUpdate)) {
            const element = document.querySelector(selector);
            if (element && langData[key]) {
                // Special case for elements that might contain HTML
                if (key === 'otp_button') {
                    element.innerHTML = `<i class="fas fa-sms"></i> ${langData[key]}`;
                } else if (key === 'signup_link') {
                    element.innerHTML = langData[key].replace('{link}', '<a href="register.html">').replace('{/link}', '</a>');
                } else {
                    element.textContent = langData[key];
                }
            }
        }
    }
    
    /**
     * Fallback language implementation when API is unavailable
     * @param {string} lang - Language code
     */
    function fallbackLanguageUpdate(lang) {
        if (lang === 'sw') {
            // Swahili translations
            document.querySelector('.welcome-text').textContent = 'Ingia kwenye akaunti yako ya PesaGuru kwa usalama.';
            document.querySelector('.form-label[for="email"]').textContent = 'Barua pepe au Nambari ya Simu';
            document.querySelector('.form-label[for="password"]').textContent = 'Nywila';
            document.querySelector('label[for="rememberMe"]').textContent = 'Nikumbuke';
            document.querySelector('.forgot-password').textContent = 'Umesahau Nywila?';
            document.querySelector('.btn-text').textContent = 'Ingia';
            document.querySelector('.divider span').textContent = 'au';
            document.querySelector('.otp-btn').innerHTML = '<i class="fas fa-sms"></i> Ingia kwa OTP';
            document.querySelector('.signup-link').innerHTML = 'Huna akaunti? <a href="register.html">Jisajili hapa</a>';
        } else {
            // English (default)
            document.querySelector('.welcome-text').textContent = 'Securely access your PesaGuru account.';
            document.querySelector('.form-label[for="email"]').textContent = 'Email or Phone Number';
            document.querySelector('.form-label[for="password"]').textContent = 'Password';
            document.querySelector('label[for="rememberMe"]').textContent = 'Remember me';
            document.querySelector('.forgot-password').textContent = 'Forgot Password?';
            document.querySelector('.btn-text').textContent = 'Login';
            document.querySelector('.divider span').textContent = 'or';
            document.querySelector('.otp-btn').innerHTML = '<i class="fas fa-sms"></i> Login with OTP';
            document.querySelector('.signup-link').innerHTML = 'Don\'t have an account? <a href="register.html">Sign up here</a>';
        }
    }
    
    /**
     * Open live chat support
     */
    function openLiveChat(event) {
        event.preventDefault();
        
        // Check if the chat widget script has been loaded
        if (typeof window.PesaGuruChat === 'undefined') {
            // Load the chat widget script dynamically
            const script = document.createElement('script');
            script.src = '../assets/js/chat/widget.js';
            script.onload = initializeChat;
            document.body.appendChild(script);
        } else {
            // Chat widget already loaded, just initialize it
            initializeChat();
        }
    }
    
    /**
     * Initialize the chat widget
     */
    function initializeChat() {
        window.PesaGuruChat.init({
            containerId: 'chat-container',
            apiKey: 'CHAT_WIDGET_API_KEY',
            user: {
                // Pass user info if available
                email: emailInput.value || null
            },
            lang: getCurrentLanguage(),
            theme: document.body.getAttribute('data-theme') || 'light'
        });
        
        window.PesaGuruChat.open();
    }
    
    /**
     * Toggle between light and dark theme
     */
    function toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        // Update theme
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('pesaguru_theme', newTheme);
        
        // Update theme toggle icon
        const icon = themeToggleBtn.querySelector('i');
        if (icon) {
            icon.className = newTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
        
        // If chat widget is loaded, update its theme too
        if (typeof window.PesaGuruChat !== 'undefined') {
            window.PesaGuruChat.updateTheme(newTheme);
        }
    }
    
    /**
     * Initialize theme based on user preference
     */
    function initTheme() {
        const savedTheme = localStorage.getItem('pesaguru_theme');
        
        if (savedTheme) {
            document.body.setAttribute('data-theme', savedTheme);
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                icon.className = savedTheme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
            }
        }
    }
    
    /**
     * Load saved credentials if available
     */
    function initSavedCredentials() {
        const savedEmail = localStorage.getItem('pesaguru_email');
        
        if (savedEmail) {
            emailInput.value = savedEmail;
            rememberMeCheckbox.checked = true;
        }
        
        // Initialize language
        const savedLanguage = localStorage.getItem('pesaguru_language');
        if (savedLanguage) {
            languageSelector.value = savedLanguage;
            // Call changeLanguage to update UI text
            changeLanguage();
        }
    }
  });