/**
 * BISHOP Website - Preloader Script
 * Enhances the loading experience with a smooth preloader
 * 
 * @version 1.0.0
 * @author BISHOP Team
 */

// Create preloader element
const preloader = document.createElement('div');
preloader.className = 'preloader';
preloader.innerHTML = `
    <div class="preloader-logo">
        <img src="/assets/img/logo.png" alt="BISHOP Logo">
    </div>
    <div class="preloader-progress">
        <div class="preloader-bar"></div>
    </div>
`;

// Add preloader to the DOM
document.body.appendChild(preloader);

// Track loading progress
let progress = 0;
const progressBar = preloader.querySelector('.preloader-bar');

// Simulate loading progress
const interval = setInterval(() => {
    progress += Math.random() * 10;
    
    if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        
        // Hide preloader after a short delay
        setTimeout(() => {
            preloader.classList.add('loaded');
            
            // Remove preloader from DOM after animation completes
            setTimeout(() => {
                document.body.removeChild(preloader);
            }, 500);
        }, 500);
    }
    
    // Update progress bar
    progressBar.style.width = `${progress}%`;
}, 200);

// Ensure preloader is removed if page loads quickly
window.addEventListener('load', () => {
    progress = 100;
    progressBar.style.width = '100%';
    
    clearInterval(interval);
    
    // Hide preloader after a short delay
    setTimeout(() => {
        preloader.classList.add('loaded');
        
        // Remove preloader from DOM after animation completes
        setTimeout(() => {
            if (document.body.contains(preloader)) {
                document.body.removeChild(preloader);
            }
        }, 500);
    }, 500);
});

// Create scroll progress indicator
const scrollProgress = document.createElement('div');
scrollProgress.className = 'scroll-progress';
document.body.appendChild(scrollProgress);

// Update scroll progress on scroll
window.addEventListener('scroll', () => {
    const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    const progress = (scrollTop / scrollHeight) * 100;
    
    scrollProgress.style.width = `${progress}%`;
});

// Create back to top button
const backToTop = document.createElement('div');
backToTop.className = 'back-to-top';
backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
document.body.appendChild(backToTop);

// Show/hide back to top button on scroll
window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
});

// Scroll to top when button is clicked
backToTop.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

// Create offline indicator
const offlineIndicator = document.createElement('div');
offlineIndicator.className = 'offline-indicator';
offlineIndicator.innerHTML = '<i class="fas fa-wifi"></i> You are offline';
document.body.appendChild(offlineIndicator);

// Show/hide offline indicator based on network status
window.addEventListener('online', () => {
    offlineIndicator.classList.remove('show');
});

window.addEventListener('offline', () => {
    offlineIndicator.classList.add('show');
});

// Check initial network status
if (!navigator.onLine) {
    offlineIndicator.classList.add('show');
}

// Create skip link for accessibility
const skipLink = document.createElement('a');
skipLink.href = '#main';
skipLink.className = 'skip-link';
skipLink.textContent = 'Skip to main content';
document.body.insertBefore(skipLink, document.body.firstChild);

// Add notification container
const notificationContainer = document.createElement('div');
notificationContainer.className = 'notification-container';
document.body.appendChild(notificationContainer);

// Global function to create notifications
window.createNotification = function(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    notification.innerHTML = `
        <div class="notification-icon"><i class="fas fa-${icon}"></i></div>
        <div class="notification-content">${message}</div>
        <button class="notification-close"><i class="fas fa-times"></i></button>
    `;
    
    notificationContainer.appendChild(notification);
    
    // Show notification with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Close button functionality
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.remove('show');
        
        // Remove from DOM after animation completes
        setTimeout(() => {
            notificationContainer.removeChild(notification);
        }, 300);
    });
    
    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                
                // Remove from DOM after animation completes
                setTimeout(() => {
                    if (notification.parentNode) {
                        notificationContainer.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
    }
    
    return notification;
};
