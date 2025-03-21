document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initializeBootstrapComponents();
    
    // Setup theme toggle functionality
    setupThemeToggle();
    
    // Setup video player modal
    setupVideoPlayerModal();
    
    // Setup notification modal
    setupNotificationModal();
    
    // Setup filter and sort functionalities
    setupFilterAndSort();
    
    // Setup learning track progress animation
    setupProgressAnimation();
    
    // Setup language switcher
    setupLanguageSwitcher();
    
    // Initialize save/bookmark functionality
    setupBookmarkFunctionality();
});

/**
 * Initialize Bootstrap components like tooltips, popovers
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers if needed
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup theme toggle between light and dark mode
 */
function setupThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;
    const themeIcon = themeToggle.querySelector('i');
    
    // Check for saved theme preference or respect OS preference
    const savedTheme = localStorage.getItem('pesaGuruTheme');
    
    if (savedTheme) {
        body.classList.add(savedTheme);
        updateThemeIcon(themeIcon, savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        body.classList.add('dark-mode');
        body.classList.remove('light-mode');
        updateThemeIcon(themeIcon, 'dark-mode');
    }
    
    // Theme toggle click event
    themeToggle.addEventListener('click', function() {
        if (body.classList.contains('light-mode')) {
            body.classList.remove('light-mode');
            body.classList.add('dark-mode');
            localStorage.setItem('pesaGuruTheme', 'dark-mode');
            updateThemeIcon(themeIcon, 'dark-mode');
        } else {
            body.classList.remove('dark-mode');
            body.classList.add('light-mode');
            localStorage.setItem('pesaGuruTheme', 'light-mode');
            updateThemeIcon(themeIcon, 'light-mode');
        }
    });
}

/**
 * Update theme icon based on current theme
 */
function updateThemeIcon(iconElement, theme) {
    if (theme === 'dark-mode') {
        iconElement.classList.remove('fa-moon');
        iconElement.classList.add('fa-sun');
    } else {
        iconElement.classList.remove('fa-sun');
        iconElement.classList.add('fa-moon');
    }
}

/**
 * Setup video player modal functionality
 */
function setupVideoPlayerModal() {
    const playButtons = document.querySelectorAll('.play-button');
    const videoModal = new bootstrap.Modal(document.getElementById('videoPlayerModal'));
    const videoFrame = document.getElementById('videoFrame');
    const videoTitle = document.getElementById('videoPlayerModalLabel');
    const videoDescription = document.getElementById('videoDescription');
    const instructorName = document.querySelector('.instructor-info h6');
    const instructorRole = document.querySelector('.instructor-info p');
    const instructorImg = document.querySelector('.instructor-img');
    
    // Video database - in a real app this would come from a backend API
    const videoDatabase = {
        'forex-basics-123': {
            title: 'Forex Trading Fundamentals',
            description: 'Learn how to analyze forex markets and make informed trading decisions. This comprehensive tutorial covers currency pairs, market hours, leverage, and basic trading strategies.',
            videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
            instructor: {
                name: 'James Mwangi',
                role: 'Forex Trading Expert, PesaGuru Advisor',
                image: '../../assets/images/Learning_Resources/instructor-forex.jpg'
            }
        },
        'portfolio-diversification-456': {
            title: 'Portfolio Diversification Strategies',
            description: 'Advanced techniques to diversify your investment portfolio and minimize risk while maximizing returns. Learn about asset allocation, sector rotation, and global diversification.',
            videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
            instructor: {
                name: 'Sarah Mwakazi',
                role: 'Investment Strategist, CFA',
                image: '../../assets/images/Learning_Resources/instructor-investment.jpg'
            }
        },
        'credit-score-789': {
            title: 'Improve Your Credit Score',
            description: 'Practical tips to build and maintain a good credit score in Kenya. Learn how credit reporting works, factors that influence your score, and strategies to improve it.',
            videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
            instructor: {
                name: 'Daniel Ochieng',
                role: 'Credit Specialist, Financial Coach',
                image: '../../assets/images/Learning_Resources/instructor-credit.jpg'
            }
        }
    };
    
    // Default video info for videos not in database
    const defaultVideo = {
        description: 'Learn more about financial concepts with expert guidance from PesaGuru advisors.',
        instructor: {
            name: 'PesaGuru Instructor',
            role: 'Financial Advisor',
            image: '../../assets/images/Learning_Resources/instructor.jpg'
        }
    };
    
    // Setup click handlers for all play buttons
    playButtons.forEach(button => {
        button.addEventListener('click', function() {
            const videoId = this.getAttribute('data-video-id');
            let videoData;
            
            if (videoId && videoDatabase[videoId]) {
                // Get video from database if it exists
                videoData = videoDatabase[videoId];
                videoTitle.textContent = videoData.title;
                videoDescription.textContent = videoData.description;
                instructorName.textContent = videoData.instructor.name;
                instructorRole.textContent = videoData.instructor.role;
                instructorImg.src = videoData.instructor.image;
                videoFrame.src = videoData.videoUrl;
            } else {
                // Fallback to card data if video not in database
                const cardBody = this.closest('.card') ? this.closest('.card').querySelector('.card-body') : null;
                
                if (cardBody) {
                    const title = cardBody.querySelector('.card-title').textContent;
                    const description = cardBody.querySelector('.card-text').textContent;
                    
                    videoTitle.textContent = title;
                    videoDescription.textContent = description;
                } else if (this.closest('.featured-video')) {
                    // Handle featured videos in carousel
                    const featuredContent = this.closest('.featured-video').querySelector('.featured-content');
                    const title = featuredContent.querySelector('h4').textContent;
                    const description = featuredContent.querySelector('p').textContent;
                    
                    videoTitle.textContent = title;
                    videoDescription.textContent = description;
                }
                
                // Set default instructor info
                instructorName.textContent = defaultVideo.instructor.name;
                instructorRole.textContent = defaultVideo.instructor.role;
                instructorImg.src = defaultVideo.instructor.image;
                videoFrame.src = "https://www.youtube.com/embed/dQw4w9WgXcQ"; // Placeholder
            }
            
            // Show the modal
            videoModal.show();
            
            // Track video view (would connect to analytics in a real app)
            trackVideoView(videoTitle.textContent);
        });
    });
    
    // Handle video modal close - pause video when modal is closed
    document.getElementById('videoPlayerModal').addEventListener('hidden.bs.modal', function () {
        videoFrame.src = '';
    });
    
    // Setup comments section
    setupCommentsSection();
}

/**
 * Track video views for analytics
 */
function trackVideoView(videoTitle) {
    console.log('Video view tracked:', videoTitle);
    // In a real app, this would send analytics data to the server
}

/**
 * Setup comments functionality for the video player
 */
function setupCommentsSection() {
    const commentForm = document.querySelector('.comment-form');
    const commentsList = document.querySelector('.comments-list');
    
    // Sample comments - in a real app these would come from a database
    const sampleComments = [
        {
            user: 'John Kamau',
            avatar: '../../assets/images/Learning_Resources/user-avatar-1.jpg',
            comment: 'This was really helpful! I finally understand how forex markets work.',
            time: '2 hours ago',
            likes: 5
        },
        {
            user: 'Mary Wanjiku',
            avatar: '../../assets/images/Learning_Resources/user-avatar-2.jpg',
            comment: 'Could you explain more about leverage risks? I\'m still confused about that part.',
            time: '1 day ago',
            likes: 2
        },
        {
            user: 'Timothy Omondi',
            avatar: '../../assets/images/Learning_Resources/user-avatar-3.jpg',
            comment: 'Great tutorial! Looking forward to the advanced series.',
            time: '3 days ago',
            likes: 8
        }
    ];
    
    // Populate comments when modal opens
    document.getElementById('videoPlayerModal').addEventListener('show.bs.modal', function () {
        commentsList.innerHTML = '';
        
        sampleComments.forEach(comment => {
            const commentElement = document.createElement('div');
            commentElement.className = 'comment mb-3 p-3 border rounded';
            commentElement.innerHTML = `
                <div class="d-flex">
                    <img src="${comment.avatar}" alt="${comment.user}" class="rounded-circle me-2" width="40" height="40">
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <h6 class="mb-0">${comment.user}</h6>
                            <small class="text-muted">${comment.time}</small>
                        </div>
                        <p class="mb-1">${comment.comment}</p>
                        <div>
                            <button class="btn btn-sm btn-link text-muted like-button">
                                <i class="far fa-thumbs-up me-1"></i> ${comment.likes}
                            </button>
                            <button class="btn btn-sm btn-link text-muted reply-button">Reply</button>
                        </div>
                    </div>
                </div>
            `;
            commentsList.appendChild(commentElement);
        });
        
        // Set up like buttons
        const likeButtons = commentsList.querySelectorAll('.like-button');
        likeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const likeIcon = this.querySelector('i');
                if (likeIcon.classList.contains('far')) {
                    likeIcon.classList.replace('far', 'fas');
                    this.classList.add('text-primary');
                    this.classList.remove('text-muted');
                    const likes = parseInt(this.textContent) + 1;
                    this.innerHTML = `<i class="fas fa-thumbs-up me-1"></i> ${likes}`;
                } else {
                    likeIcon.classList.replace('fas', 'far');
                    this.classList.remove('text-primary');
                    this.classList.add('text-muted');
                    const likes = parseInt(this.textContent) - 1;
                    this.innerHTML = `<i class="far fa-thumbs-up me-1"></i> ${likes}`;
                }
            });
        });
        
        // Set up reply buttons
        const replyButtons = commentsList.querySelectorAll('.reply-button');
        replyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const commentElement = this.closest('.comment');
                const replyForm = document.createElement('div');
                replyForm.className = 'reply-form mt-2';
                replyForm.innerHTML = `
                    <div class="d-flex">
                        <input type="text" class="form-control form-control-sm me-2" placeholder="Write a reply...">
                        <button class="btn btn-sm btn-primary">Reply</button>
                    </div>
                `;
                // Only add the reply form if it doesn't already exist
                if (!commentElement.querySelector('.reply-form')) {
                    commentElement.appendChild(replyForm);
                }
            });
        });
    });
    
    // Handle comment submission
    if (commentForm) {
        const commentButton = commentForm.querySelector('button');
        const commentTextarea = commentForm.querySelector('textarea');
        
        commentButton.addEventListener('click', function() {
            const commentText = commentTextarea.value.trim();
            if (commentText) {
                // Create new comment element
                const newComment = document.createElement('div');
                newComment.className = 'comment mb-3 p-3 border rounded';
                newComment.innerHTML = `
                    <div class="d-flex">
                        <img src="../../assets/images/Learning_Resources/user-avatar-me.jpg" alt="Me" class="rounded-circle me-2" width="40" height="40">
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <h6 class="mb-0">You</h6>
                                <small class="text-muted">Just now</small>
                            </div>
                            <p class="mb-1">${commentText}</p>
                            <div>
                                <button class="btn btn-sm btn-link text-muted like-button">
                                    <i class="far fa-thumbs-up me-1"></i> 0
                                </button>
                                <button class="btn btn-sm btn-link text-muted reply-button">Reply</button>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add the new comment to the top of the list
                commentsList.insertBefore(newComment, commentsList.firstChild);
                
                // Clear the textarea
                commentTextarea.value = '';
                
                // Setup the new like and reply buttons
                const likeButton = newComment.querySelector('.like-button');
                likeButton.addEventListener('click', function() {
                    const likeIcon = this.querySelector('i');
                    if (likeIcon.classList.contains('far')) {
                        likeIcon.classList.replace('far', 'fas');
                        this.classList.add('text-primary');
                        this.classList.remove('text-muted');
                        const likes = parseInt(this.textContent) + 1;
                        this.innerHTML = `<i class="fas fa-thumbs-up me-1"></i> ${likes}`;
                    } else {
                        likeIcon.classList.replace('fas', 'far');
                        this.classList.remove('text-primary');
                        this.classList.add('text-muted');
                        const likes = parseInt(this.textContent) - 1;
                        this.innerHTML = `<i class="far fa-thumbs-up me-1"></i> ${likes}`;
                    }
                });
                
                const replyButton = newComment.querySelector('.reply-button');
                replyButton.addEventListener('click', function() {
                    const commentElement = this.closest('.comment');
                    const replyForm = document.createElement('div');
                    replyForm.className = 'reply-form mt-2';
                    replyForm.innerHTML = `
                        <div class="d-flex">
                            <input type="text" class="form-control form-control-sm me-2" placeholder="Write a reply...">
                            <button class="btn btn-sm btn-primary">Reply</button>
                        </div>
                    `;
                    // Only add the reply form if it doesn't already exist
                    if (!commentElement.querySelector('.reply-form')) {
                        commentElement.appendChild(replyForm);
                    }
                });
            }
        });
    }
}

/**
 * Setup notification modal functionality
 */
function setupNotificationModal() {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationModal = new bootstrap.Modal(document.getElementById('notificationModal'));
    
    notificationBtn.addEventListener('click', function() {
        notificationModal.show();
        
        // In a real app, this would mark notifications as read on the server
        setTimeout(() => {
            const badgeElement = notificationBtn.querySelector('.badge');
            if (badgeElement) {
                badgeElement.style.display = 'none';
            }
        }, 3000);
    });
}

/**
 * Setup filter and sort functionalities
 */
function setupFilterAndSort() {
    // Difficulty filter buttons
    const difficultyButtons = document.querySelectorAll('input[name="difficulty"]');
    const cards = document.querySelectorAll('.card');
    
    difficultyButtons.forEach(button => {
        button.addEventListener('change', function() {
            const selectedDifficulty = this.id;
            
            cards.forEach(card => {
                const badgeElement = card.querySelector('.badge');
                if (!badgeElement) return;
                
                const cardDifficulty = badgeElement.textContent.toLowerCase();
                
                if (selectedDifficulty === 'all' || cardDifficulty === selectedDifficulty) {
                    card.closest('.col').style.display = 'block';
                } else {
                    card.closest('.col').style.display = 'none';
                }
            });
        });
    });
    
    // Sort dropdown
    const sortSelect = document.querySelector('.sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const selectedOption = this.value;
            // In a real app, this would re-fetch sorted videos from the server
            console.log('Sorting by:', selectedOption);
            
            // Show sorting feedback to user
            const sortingToast = document.createElement('div');
            sortingToast.className = 'toast align-items-center text-white bg-primary border-0 position-fixed bottom-0 end-0 m-3';
            sortingToast.setAttribute('role', 'alert');
            sortingToast.setAttribute('aria-live', 'assertive');
            sortingToast.setAttribute('aria-atomic', 'true');
            sortingToast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-sort me-2"></i> Sorting videos by ${selectedOption}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            document.body.appendChild(sortingToast);
            
            const toast = new bootstrap.Toast(sortingToast);
            toast.show();
            
            // Remove toast after it's hidden
            sortingToast.addEventListener('hidden.bs.toast', function() {
                sortingToast.remove();
            });
        });
    }
    
    // Search functionality
    const searchInput = document.querySelector('input[type="text"][placeholder="Search tutorials..."]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(event) {
            // Trigger search on Enter key
            if (event.key === 'Enter') {
                const searchTerm = this.value.toLowerCase().trim();
                if (searchTerm.length > 0) {
                    searchVideos(searchTerm);
                }
            }
        });
        
        // Also handle the search button click
        const searchButton = searchInput.nextElementSibling;
        if (searchButton) {
            searchButton.addEventListener('click', function() {
                const searchTerm = searchInput.value.toLowerCase().trim();
                if (searchTerm.length > 0) {
                    searchVideos(searchTerm);
                }
            });
        }
    }
}

/**
 * Search videos functionality
 */
function searchVideos(searchTerm) {
    const cards = document.querySelectorAll('.card');
    let resultsFound = 0;
    
    cards.forEach(card => {
        const cardTitle = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const cardText = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
        const cardContent = cardTitle + ' ' + cardText;
        
        if (cardContent.includes(searchTerm)) {
            card.closest('.col').style.display = 'block';
            card.classList.add('border-primary');
            setTimeout(() => {
                card.classList.remove('border-primary');
            }, 2000);
            resultsFound++;
        } else {
            card.closest('.col').style.display = 'none';
        }
    });
    
    // Show search results feedback
    const searchToast = document.createElement('div');
    searchToast.className = 'toast align-items-center text-white bg-primary border-0 position-fixed bottom-0 end-0 m-3';
    searchToast.setAttribute('role', 'alert');
    searchToast.setAttribute('aria-live', 'assertive');
    searchToast.setAttribute('aria-atomic', 'true');
    searchToast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-search me-2"></i> Found ${resultsFound} results for "${searchTerm}"
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    document.body.appendChild(searchToast);
    
    const toast = new bootstrap.Toast(searchToast);
    toast.show();
    
    // Remove toast after it's hidden
    searchToast.addEventListener('hidden.bs.toast', function() {
        searchToast.remove();
    });
}

/**
 * Setup progress animation for learning tracks
 */
function setupProgressAnimation() {
    // Animate progress bars when they come into view
    const progressBars = document.querySelectorAll('.progress-bar');
    
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Get the width class from the element
                    const progressClasses = Array.from(entry.target.classList)
                        .filter(className => className.startsWith('progress-'));
                    
                    // If it has a specific width class, animate to that width
                    if (progressClasses.length > 0) {
                        const width = progressClasses[0].split('-')[1];
                        entry.target.style.width = `${width}%`;
                    }
                    
                    // Unobserve after animation
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        progressBars.forEach(bar => {
            // Set initial width to 0 for animation
            bar.style.width = '0%';
            observer.observe(bar);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        progressBars.forEach(bar => {
            const progressClasses = Array.from(bar.classList)
                .filter(className => className.startsWith('progress-'));
            
            if (progressClasses.length > 0) {
                const width = progressClasses[0].split('-')[1];
                bar.style.width = `${width}%`;
            }
        });
    }
}

/**
 * Setup language switcher functionality
 */
function setupLanguageSwitcher() {
    const languageButtons = document.querySelectorAll('input[name="language"]');
    
    languageButtons.forEach(button => {
        button.addEventListener('change', function() {
            const selectedLanguage = this.id;
            console.log('Language changed to:', selectedLanguage);
            
            // In a real app, this would update UI language and reload video content
            
            // Show language change feedback
            const langToast = document.createElement('div');
            langToast.className = 'toast align-items-center text-white bg-success border-0 position-fixed bottom-0 end-0 m-3';
            langToast.setAttribute('role', 'alert');
            langToast.setAttribute('aria-live', 'assertive');
            langToast.setAttribute('aria-atomic', 'true');
            langToast.innerHTML = `
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-language me-2"></i> Language changed to ${selectedLanguage}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            `;
            document.body.appendChild(langToast);
            
            const toast = new bootstrap.Toast(langToast);
            toast.show();
            
            // Remove toast after it's hidden
            langToast.addEventListener('hidden.bs.toast', function() {
                langToast.remove();
            });
        });
    });
}

/**
 * Setup bookmark/save functionality
 */
function setupBookmarkFunctionality() {
    const bookmarkButtons = document.querySelectorAll('.btn-outline-secondary[data-bs-toggle="tooltip"][title="Save for later"]');
    
    bookmarkButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const icon = this.querySelector('i');
            const card = this.closest('.card');
            const videoTitle = card.querySelector('.card-title').textContent;
            
            if (icon.classList.contains('far') || !icon.classList.contains('fas')) {
                // Save the video
                icon.classList.remove('far');
                icon.classList.add('fas');
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-primary');
                
                // Show saved feedback
                showToast(`<i class="fas fa-bookmark me-2"></i> "${videoTitle}" saved to your library`, 'success');
                
                // In a real app, this would send data to the server
                saveVideo(videoTitle);
            } else {
                // Unsave the video
                icon.classList.remove('fas');
                icon.classList.add('far');
                this.classList.remove('btn-primary');
                this.classList.add('btn-outline-secondary');
                
                // Show unsaved feedback
                showToast(`<i class="fas fa-times me-2"></i> "${videoTitle}" removed from your library`, 'danger');
                
                // In a real app, this would send data to the server
                unsaveVideo(videoTitle);
            }
        });
    });
}

/**
 * Save video to user library
 */
function saveVideo(videoTitle) {
    console.log('Video saved:', videoTitle);
    // In a real app, this would save to user profile on the server
}

/**
 * Remove video from user library
 */
function unsaveVideo(videoTitle) {
    console.log('Video unsaved:', videoTitle);
    // In a real app, this would remove from user profile on the server
}

/**
 * Show toast notification
 */
function showToast(message, type = 'primary') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}