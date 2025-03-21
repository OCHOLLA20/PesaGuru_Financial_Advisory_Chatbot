document.addEventListener('DOMContentLoaded', () => {
    // ===== INITIALIZE UI COMPONENTS =====
    initNavigation();
    initContentSections();
    initStrategyTabs();
    initModals();
    initFilters();
    initFloatingActions();
    initDarkMode();
    initWatchlist();
    
    // Add event listener to all interactive elements
    addInteractiveElementsEvents();
});

// ===== NAVIGATION FUNCTIONS =====

function initNavigation() {
    // Toggle left navigation collapse
    const collapseNavBtn = document.getElementById('collapseNav');
    const leftNavigation = document.querySelector('.left-navigation');
    const mainContent = document.querySelector('.main-content');
    
    if (collapseNavBtn) {
        collapseNavBtn.addEventListener('click', () => {
            leftNavigation.classList.toggle('collapsed');
            mainContent.classList.toggle('nav-collapsed');
        });
    }
    
    // Toggle navigation sections
    const sectionHeaders = document.querySelectorAll('.nav-section .section-header');
    
    sectionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.nav-section');
            const sectionItems = section.querySelector('.section-items');
            
            // Toggle section expanded/collapsed state
            header.classList.toggle('collapsed');
            
            // Toggle section items visibility with smooth animation
            if (sectionItems.style.maxHeight) {
                sectionItems.style.maxHeight = null;
            } else {
                sectionItems.style.maxHeight = sectionItems.scrollHeight + 'px';
            }
        });
    });
    
    // Mobile navigation toggle (for responsive design)
    const mobileNavToggle = document.createElement('button');
    mobileNavToggle.className = 'mobile-nav-toggle';
    mobileNavToggle.innerHTML = '<i class="fas fa-bars"></i>';
    mobileNavToggle.setAttribute('aria-label', 'Toggle Navigation');
    
    document.querySelector('.header').prepend(mobileNavToggle);
    
    mobileNavToggle.addEventListener('click', () => {
        leftNavigation.classList.toggle('active');
        document.body.classList.toggle('nav-open');
    });
    
    // Close mobile navigation when clicking outside
    document.addEventListener('click', (e) => {
        const isNavigation = e.target.closest('.left-navigation');
        const isNavToggle = e.target.closest('.mobile-nav-toggle');
        
        if (!isNavigation && !isNavToggle && leftNavigation.classList.contains('active')) {
            leftNavigation.classList.remove('active');
            document.body.classList.remove('nav-open');
        }
    });
}

// ===== CONTENT SECTIONS FUNCTIONS =====

function initContentSections() {
    // Toggle content sections expand/collapse
    const expandBtns = document.querySelectorAll('.section-controls .expand-btn');
    
    expandBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.closest('.content-section');
            const sectionContent = section.querySelector('.section-content');
            
            section.classList.toggle('collapsed');
            
            if (section.classList.contains('collapsed')) {
                sectionContent.style.display = 'none';
                btn.innerHTML = '<i class="fas fa-chevron-right"></i>';
                btn.setAttribute('title', 'Expand section');
            } else {
                sectionContent.style.display = 'block';
                btn.innerHTML = '<i class="fas fa-chevron-down"></i>';
                btn.setAttribute('title', 'Collapse section');
            }
        });
    });
    
    // Bookmark functionality
    const bookmarkBtns = document.querySelectorAll('.section-controls .bookmark-btn');
    
    bookmarkBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
            
            if (btn.classList.contains('active')) {
                btn.innerHTML = '<i class="fas fa-bookmark"></i>';
                btn.setAttribute('title', 'Remove bookmark');
                showToast('Section bookmarked!');
            } else {
                btn.innerHTML = '<i class="far fa-bookmark"></i>';
                btn.setAttribute('title', 'Bookmark section');
                showToast('Bookmark removed');
            }
        });
    });
}

// ===== STRATEGY TABS FUNCTIONS =====

function initStrategyTabs() {
    const tabBtns = document.querySelectorAll('.strategies-tabs .tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and panels
            document.querySelectorAll('.strategies-tabs .tab-btn').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.querySelectorAll('.strategies-tabs .tab-panel').forEach(panel => {
                panel.classList.remove('active');
            });
            
            // Add active class to clicked button and corresponding panel
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            const tabPanel = document.getElementById(`${tabId}-panel`);
            
            if (tabPanel) {
                tabPanel.classList.add('active');
                tabPanel.classList.add('fade-in');
                
                // Remove animation class after animation completes
                setTimeout(() => {
                    tabPanel.classList.remove('fade-in');
                }, 500);
            }
        });
    });
}

// ===== MODALS FUNCTIONS =====

function initModals() {
    // Settings modal
    const settingsBtn = document.querySelector('.header-btn.settings');
    const settingsModal = document.getElementById('settingsModal');
    
    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', () => {
            settingsModal.classList.add('active');
        });
    }
    
    // Notifications modal
    const notificationsBtn = document.querySelector('.header-btn.notifications');
    const notificationsModal = document.getElementById('notificationsModal');
    
    if (notificationsBtn && notificationsModal) {
        notificationsBtn.addEventListener('click', () => {
            notificationsModal.classList.add('active');
            // Reset notification badge
            const badge = notificationsBtn.querySelector('.notification-badge');
            if (badge) {
                badge.style.display = 'none';
            }
        });
    }
    
    // Close modals
    const closeModalBtns = document.querySelectorAll('.close-modal');
    
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal');
            modal.classList.remove('active');
        });
    });
    
    // Close modal when clicking outside
    document.addEventListener('click', (e) => {
        const modals = document.querySelectorAll('.modal.active');
        
        modals.forEach(modal => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
    
    // Settings functionality
    const darkModeToggle = document.getElementById('darkMode');
    const textSizeSelect = document.getElementById('textSize');
    const languageSelect = document.getElementById('language');
    const contentLevelSelect = document.getElementById('contentLevel');
    
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', () => {
            document.body.classList.toggle('dark-mode', darkModeToggle.checked);
            localStorage.setItem('darkMode', darkModeToggle.checked);
        });
    }
    
    if (textSizeSelect) {
        textSizeSelect.addEventListener('change', () => {
            const textSize = textSizeSelect.value;
            document.documentElement.style.fontSize = 
                textSize === 'Small' ? '14px' : 
                textSize === 'Medium' ? '16px' : '18px';
            localStorage.setItem('textSize', textSize);
        });
    }
    
    // Apply saved settings when page loads
    const savedDarkMode = localStorage.getItem('darkMode') === 'true';
    const savedTextSize = localStorage.getItem('textSize');
    
    if (darkModeToggle) {
        darkModeToggle.checked = savedDarkMode;
        document.body.classList.toggle('dark-mode', savedDarkMode);
    }
    
    if (textSizeSelect && savedTextSize) {
        textSizeSelect.value = savedTextSize;
        document.documentElement.style.fontSize = 
            savedTextSize === 'Small' ? '14px' : 
            savedTextSize === 'Medium' ? '16px' : '18px';
    }
    
    // Save settings button functionality
    const saveSettingsBtn = document.querySelector('#settingsModal .primary-btn');
    
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', () => {
            // Save all settings to localStorage
            if (darkModeToggle) localStorage.setItem('darkMode', darkModeToggle.checked);
            if (textSizeSelect) localStorage.setItem('textSize', textSizeSelect.value);
            if (languageSelect) localStorage.setItem('language', languageSelect.value);
            if (contentLevelSelect) localStorage.setItem('contentLevel', contentLevelSelect.value);
            
            // Close modal
            settingsModal.classList.remove('active');
            
            // Show confirmation
            showToast('Settings saved successfully!');
        });
    }
    
    // Notification actions
    const notificationActionBtns = document.querySelectorAll('.notification-actions button');
    
    notificationActionBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const notificationItem = btn.closest('.notification-item');
            
            if (btn.innerHTML.includes('fa-check')) {
                // Mark as read
                notificationItem.classList.remove('unread');
            } else if (btn.innerHTML.includes('fa-trash')) {
                // Remove notification with animation
                notificationItem.style.opacity = '0';
                setTimeout(() => {
                    notificationItem.remove();
                }, 300);
            }
        });
    });
    
    // Mark all as read button
    const markAllReadBtn = document.querySelector('#notificationsModal .primary-btn');
    
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', () => {
            const unreadItems = document.querySelectorAll('.notification-item.unread');
            unreadItems.forEach(item => {
                item.classList.remove('unread');
            });
            showToast('All notifications marked as read');
        });
    }
}

// ===== FILTERS FUNCTIONS =====

function initFilters() {
    // News filters
    const newsFilterBtns = document.querySelectorAll('.news-filters .filter-btn');
    
    newsFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            newsFilterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Here you would implement actual filtering logic
            // For demo purposes, we'll just show a feedback toast
            const filterType = btn.textContent.trim();
            showToast(`Showing ${filterType} news`);
        });
    });
    
    // Resource filters
    const resourceFilterBtns = document.querySelectorAll('.resource-filters .filter-btn');
    
    resourceFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            resourceFilterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Filter resources based on selected category
            const filterType = btn.textContent.trim();
            const resourceCards = document.querySelectorAll('.resource-card');
            
            resourceCards.forEach(card => {
                if (filterType === 'All Resources') {
                    card.style.display = 'block';
                } else {
                    const badge = card.querySelector('.resource-badge');
                    if (badge && badge.textContent.trim() === filterType) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            });
        });
    });
    
    // Pagination
    const paginationBtns = document.querySelectorAll('.news-pagination .pagination-btn');
    
    paginationBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if (!btn.classList.contains('active') && !btn.title.includes('Previous') && !btn.title.includes('Next')) {
                document.querySelectorAll('.news-pagination .pagination-btn').forEach(b => {
                    if (!b.title.includes('Previous') && !b.title.includes('Next')) {
                        b.classList.remove('active');
                    }
                });
                btn.classList.add('active');
                
                // Here you would implement actual pagination logic
                // For demo purposes, we'll just show a feedback toast
                showToast(`Navigated to page ${btn.textContent.trim()}`);
            } else if (btn.title.includes('Previous') || btn.title.includes('Next')) {
                // Handle previous/next navigation
                const activePage = document.querySelector('.news-pagination .pagination-btn.active:not([title])');
                if (activePage) {
                    const currentPage = parseInt(activePage.textContent.trim());
                    let newPage = currentPage;
                    
                    if (btn.title.includes('Next') && currentPage < 4) {
                        newPage = currentPage + 1;
                    } else if (btn.title.includes('Previous') && currentPage > 1) {
                        newPage = currentPage - 1;
                    }
                    
                    if (newPage !== currentPage) {
                        const targetPageBtn = document.querySelector(`.news-pagination .pagination-btn:not([title]):nth-of-type(${newPage + 1})`);
                        if (targetPageBtn) {
                            activePage.classList.remove('active');
                            targetPageBtn.classList.add('active');
                            showToast(`Navigated to page ${newPage}`);
                        }
                    }
                }
            }
        });
    });
}

// ===== FLOATING ACTIONS FUNCTIONS =====

function initFloatingActions() {
    // Scroll to top button
    const scrollTopBtn = document.querySelector('.scroll-top-btn');
    
    if (scrollTopBtn) {
        // Show/hide button based on scroll position
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollTopBtn.style.display = 'flex';
            } else {
                scrollTopBtn.style.display = 'none';
            }
        });
        
        // Scroll to top when clicked
        scrollTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Chat button
    const chatBtn = document.querySelector('.chat-btn');
    
    if (chatBtn) {
        chatBtn.addEventListener('click', () => {
            // Redirect to chatbot page or open chat modal
            window.location.href = '../../Chatbot_Interaction/chatbot.html';
        });
    }
    
    // Feedback button
    const feedbackBtn = document.querySelector('.feedback-btn');
    
    if (feedbackBtn) {
        feedbackBtn.addEventListener('click', () => {
            // Redirect to feedback page or open feedback modal
            window.location.href = '../../Support_and_Assistance/feedback.html';
        });
    }
}

// ===== DARK MODE FUNCTIONS =====

function initDarkMode() {
    const darkModeToggle = document.querySelector('.header-btn.theme-toggle');
    
    if (darkModeToggle) {
        // Check for saved dark mode preference
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        
        // Apply dark mode if saved preference exists
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            darkModeToggle.setAttribute('title', 'Toggle Light Mode');
        }
        
        // Toggle dark mode when clicked
        darkModeToggle.addEventListener('click', () => {
            document.body.classList.toggle('dark-mode');
            
            if (document.body.classList.contains('dark-mode')) {
                darkModeToggle.innerHTML = '<i class="fas fa-sun"></i>';
                darkModeToggle.setAttribute('title', 'Toggle Light Mode');
                localStorage.setItem('darkMode', 'true');
            } else {
                darkModeToggle.innerHTML = '<i class="fas fa-moon"></i>';
                darkModeToggle.setAttribute('title', 'Toggle Dark Mode');
                localStorage.setItem('darkMode', 'false');
            }
        });
    }
}

// ===== WATCHLIST FUNCTIONS =====

function initWatchlist() {
    // Remove watchlist item
    const removeWatchlistBtns = document.querySelectorAll('.watchlist-actions .icon-btn');
    
    removeWatchlistBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const watchlistItem = btn.closest('.watchlist-item');
            
            // Animate removal
            watchlistItem.style.opacity = '0';
            watchlistItem.style.transform = 'translateX(20px)';
            
            setTimeout(() => {
                watchlistItem.remove();
                showToast('Item removed from watchlist');
                
                // Check if watchlist is empty
                const remainingItems = document.querySelectorAll('.watchlist-item');
                if (remainingItems.length === 0) {
                    const watchlistContainer = document.querySelector('.watchlist-items');
                    watchlistContainer.innerHTML = '<p class="empty-watchlist">Your watchlist is empty. Add topics to track them here.</p>';
                }
            }, 300);
        });
    });
    
    // Add topic button
    const addTopicBtn = document.querySelector('.watchlist-header .secondary-btn');
    
    if (addTopicBtn) {
        addTopicBtn.addEventListener('click', () => {
            // In a real application, you would open a modal to select topics
            showToast('Add topic functionality would open a selection modal');
        });
    }
    
    // View updates button
    const viewUpdatesBtns = document.querySelectorAll('.watchlist-actions .text-btn');
    
    viewUpdatesBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const topicName = btn.closest('.watchlist-item').querySelector('h4').textContent;
            showToast(`Viewing updates for ${topicName}`);
        });
    });
}

// ===== INTERACTIVE ELEMENTS FUNCTIONS =====

function addInteractiveElementsEvents() {
    // Tool cards
    const toolCards = document.querySelectorAll('.tool-card');
    
    toolCards.forEach(card => {
        const launchBtn = card.querySelector('.secondary-btn');
        
        if (launchBtn) {
            launchBtn.addEventListener('click', () => {
                const toolName = card.querySelector('h3').textContent;
                showToast(`Launching ${toolName}`);
            });
        }
    });
    
    // Video placeholders
    const videoPlaceholders = document.querySelectorAll('.video-placeholder');
    
    videoPlaceholders.forEach(placeholder => {
        placeholder.addEventListener('click', () => {
            // In a real application, you would load and play the video
            showToast('Video would play here');
        });
    });
    
    // Assessment button
    const assessmentBtn = document.querySelector('.quick-assessment .primary-btn');
    
    if (assessmentBtn) {
        assessmentBtn.addEventListener('click', () => {
            showToast('Starting investment profile assessment');
        });
    }
    
    // Recommendation buttons
    const recommendationBtn = document.querySelector('.recommendation-card.primary .primary-btn');
    
    if (recommendationBtn) {
        recommendationBtn.addEventListener('click', () => {
            showToast('Viewing detailed strategy information');
        });
    }
    
    // Alternative strategy buttons
    const altStrategyBtns = document.querySelectorAll('.alt-recommendation .text-btn');
    
    altStrategyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const strategyName = btn.closest('.alt-recommendation').querySelector('.strategy-name').textContent;
            showToast(`Viewing details for ${strategyName}`);
        });
    });
    
    // News item clicks
    const newsItems = document.querySelectorAll('.news-item');
    
    newsItems.forEach(item => {
        item.addEventListener('click', () => {
            const newsTitle = item.querySelector('.news-title').textContent;
            showToast(`Opening news article: ${newsTitle}`);
        });
    });
    
    // Resource cards
    const resourceCards = document.querySelectorAll('.resource-card');
    
    resourceCards.forEach(card => {
        const actionBtn = card.querySelector('.secondary-btn');
        
        if (actionBtn) {
            actionBtn.addEventListener('click', () => {
                const resourceName = card.querySelector('h3').textContent;
                const actionText = actionBtn.textContent.trim();
                showToast(`${actionText} ${resourceName}`);
            });
        }
    });
    
    // Webinar registration
    const registerBtns = document.querySelectorAll('.webinar-item .primary-btn');
    
    registerBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const webinarTitle = btn.closest('.webinar-item').querySelector('h4').textContent;
            showToast(`Registering for webinar: ${webinarTitle}`);
        });
    });
    
    // Reset progress button
    const resetProgressBtn = document.querySelector('.reset-progress');
    
    if (resetProgressBtn) {
        resetProgressBtn.addEventListener('click', () => {
            // Ask for confirmation before resetting
            if (confirm('Are you sure you want to reset your learning progress? This cannot be undone.')) {
                const progressFill = document.querySelector('.progress-fill');
                const progressPercentage = document.querySelector('.progress-percentage');
                const progressDetails = document.querySelector('.progress-details span');
                
                // Animate progress reset
                progressFill.style.width = '0%';
                progressFill.classList.remove('progress-37');
                progressPercentage.textContent = '0% Complete';
                progressDetails.textContent = '0 of 27 topics completed';
                
                showToast('Learning progress has been reset');
            }
        });
    }
}

// ===== UTILITY FUNCTIONS =====

function showToast(message) {
    // Check if a toast container already exists
    let toastContainer = document.querySelector('.toast-container');
    
    // If not, create one
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create a new toast
    const toast = document.createElement('div');
    toast.className = 'toast fade-in';
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-info-circle"></i>
            <span>${message}</span>
        </div>
        <button class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add the toast to the container
    toastContainer.appendChild(toast);
    
    // Close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    });
    
    // Auto-remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// ===== ADDITIONAL CSS FOR TOAST NOTIFICATIONS =====

// Create and append toast styles
const toastStyles = document.createElement('style');
toastStyles.textContent = `
    .toast-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 300px;
    }
    
    .toast {
        background-color: var(--white);
        color: var(--dark);
        border-left: 4px solid var(--primary-color);
        padding: 12px;
        border-radius: var(--border-radius-md);
        box-shadow: var(--shadow-lg);
        display: flex;
        align-items: center;
        justify-content: space-between;
        opacity: 1;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
    
    .toast.fade-in {
        animation: toastFadeIn 0.3s ease;
    }
    
    .toast.fade-out {
        opacity: 0;
        transform: translateX(20px);
    }
    
    .toast-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .toast-content i {
        color: var(--primary-color);
    }
    
    .toast-close {
        color: var(--medium);
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px;
        transition: color 0.2s ease;
    }
    
    .toast-close:hover {
        color: var(--dark);
    }
    
    @keyframes toastFadeIn {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    body.dark-mode .toast {
        background-color: var(--medium-dark);
        color: var(--white);
    }
`;

document.head.appendChild(toastStyles);