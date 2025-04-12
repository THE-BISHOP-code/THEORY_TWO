/**
 * BISHOP Website - Main JavaScript
 * Production-level implementation with advanced features
 *
 * @version 1.0.0
 * @author BISHOP Team
 */

// Register service worker for PWA support
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(error => {
                console.log('ServiceWorker registration failed: ', error);
            });
    });
}

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initAnimations();

    // Initialize header scroll effect
    initHeaderScroll();

    // Initialize smooth scrolling for anchor links
    initSmoothScroll();

    // Initialize parallax effects
    initParallax();

    // Initialize interactive character
    initCharacter();

    // Initialize counters
    initCounters();

    // Initialize contact form
    initContactForm();

    // Initialize tooltips
    initTooltips();

    // Initialize lazy loading
    initLazyLoading();

    // Initialize theme switcher
    initThemeSwitcher();

    // Initialize analytics
    initAnalytics();

    // Initialize cookie consent
    initCookieConsent();
});

/**
 * Initialize fade-in animations on scroll
 */
function initAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

/**
 * Initialize header scroll effect
 */
function initHeaderScroll() {
    const header = document.querySelector('header');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

/**
 * Initialize smooth scrolling for anchor links
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Initialize parallax effects
 */
function initParallax() {
    const parallaxElements = document.querySelectorAll('.parallax');

    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;

        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            const offset = scrollY * speed;

            element.style.transform = `translateY(${offset}px)`;
        });
    });
}

/**
 * Initialize interactive character
 */
function initCharacter() {
    const character = document.querySelector('.hero-character');
    if (!character) return;

    // Random idle animation
    setInterval(() => {
        const randomAnim = Math.floor(Math.random() * 3);

        switch(randomAnim) {
            case 0:
                character.classList.add('character-blink');
                setTimeout(() => {
                    character.classList.remove('character-blink');
                }, 300);
                break;
            case 1:
                character.classList.add('character-tilt');
                setTimeout(() => {
                    character.classList.remove('character-tilt');
                }, 500);
                break;
            case 2:
                character.classList.add('character-float');
                setTimeout(() => {
                    character.classList.remove('character-float');
                }, 1000);
                break;
        }
    }, 5000);

    // Mouse follow effect
    document.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth - 0.5;
        const mouseY = e.clientY / window.innerHeight - 0.5;

        character.style.transform = `translate(${mouseX * 20}px, ${mouseY * 20}px)`;
    });
}

/**
 * Animate counting up for numbers
 * @param {HTMLElement} element - The element containing the number
 * @param {number} target - The target number to count to
 * @param {number} duration - The duration of the animation in milliseconds
 */
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);

    function updateCounter() {
        start += increment;

        if (start >= target) {
            element.textContent = target.toLocaleString();
            return;
        }

        element.textContent = Math.floor(start).toLocaleString();
        requestAnimationFrame(updateCounter);
    }

    updateCounter();
}

/**
 * Initialize counters animation
 */
function initCounters() {
    const counters = document.querySelectorAll('.counter');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.dataset.target);
                animateCounter(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.5
    });

    counters.forEach(counter => {
        observer.observe(counter);
    });
}

/**
 * Show a notification
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (success, error, info)
 * @param {number} duration - How long to show the notification in milliseconds
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Trigger animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Remove after duration
    setTimeout(() => {
        notification.classList.remove('show');

        // Remove from DOM after animation completes
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, duration);
}

/**
 * Copy text to clipboard
 * @param {string} text - The text to copy
 * @returns {Promise} - Resolves when copied
 */
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text)
        .then(() => {
            showNotification('Copied to clipboard!', 'success');
            return true;
        })
        .catch(err => {
            console.error('Failed to copy: ', err);
            showNotification('Failed to copy to clipboard', 'error');
            return false;
        });
}

/**
 * Format a date
 * @param {Date|string} date - The date to format
 * @param {boolean} includeTime - Whether to include the time
 * @returns {string} - The formatted date
 */
function formatDate(date, includeTime = false) {
    const d = new Date(date);

    const options = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };

    if (includeTime) {
        options.hour = '2-digit';
        options.minute = '2-digit';
    }

    return d.toLocaleDateString('en-US', options);
}

/**
 * Validate an email address
 * @param {string} email - The email to validate
 * @returns {boolean} - Whether the email is valid
 */
function isValidEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Initialize contact form validation
 */
function initContactForm() {
    const form = document.querySelector('.contact-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const nameInput = form.querySelector('input[name="name"]');
        const emailInput = form.querySelector('input[name="email"]');
        const messageInput = form.querySelector('textarea[name="message"]');

        let isValid = true;

        // Validate name
        if (!nameInput.value.trim()) {
            showInputError(nameInput, 'Please enter your name');
            isValid = false;
        } else {
            clearInputError(nameInput);
        }

        // Validate email
        if (!emailInput.value.trim()) {
            showInputError(emailInput, 'Please enter your email');
            isValid = false;
        } else if (!isValidEmail(emailInput.value)) {
            showInputError(emailInput, 'Please enter a valid email');
            isValid = false;
        } else {
            clearInputError(emailInput);
        }

        // Validate message
        if (!messageInput.value.trim()) {
            showInputError(messageInput, 'Please enter your message');
            isValid = false;
        } else {
            clearInputError(messageInput);
        }

        if (isValid) {
            // Simulate form submission
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="loading-spinner"></span> Sending...';

            setTimeout(() => {
                form.reset();
                submitButton.disabled = false;
                submitButton.textContent = 'Send Message';
                showNotification('Your message has been sent!', 'success');
            }, 1500);
        }
    });
}

/**
 * Show an error message for an input
 * @param {HTMLElement} input - The input element
 * @param {string} message - The error message
 */
function showInputError(input, message) {
    const formGroup = input.closest('.form-group');
    formGroup.classList.add('has-error');

    let errorElement = formGroup.querySelector('.form-error');

    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        formGroup.appendChild(errorElement);
    }

    errorElement.textContent = message;
}

/**
 * Clear an error message for an input
 * @param {HTMLElement} input - The input element
 */
function clearInputError(input) {
    const formGroup = input.closest('.form-group');
    formGroup.classList.remove('has-error');

    const errorElement = formGroup.querySelector('.form-error');
    if (errorElement) {
        errorElement.remove();
    }
}

/**
 * Initialize tooltips
 */
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');

    tooltips.forEach(tooltip => {
        const tooltipText = tooltip.getAttribute('data-tooltip');
        const tooltipElement = document.createElement('span');
        tooltipElement.className = 'tooltip-text';
        tooltipElement.textContent = tooltipText;

        tooltip.classList.add('tooltip');
        tooltip.appendChild(tooltipElement);
    });
}

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
    // Check if Intersection Observer is supported
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img.lazy');

        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                    }
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        lazyImages.forEach(img => {
            imageObserver.observe(img);
        });
    } else {
        // Fallback for browsers that don't support Intersection Observer
        const lazyImages = document.querySelectorAll('img.lazy');

        function lazyLoad() {
            const scrollTop = window.pageYOffset;

            lazyImages.forEach(img => {
                if (img.offsetTop < window.innerHeight + scrollTop) {
                    img.src = img.dataset.src;
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                    }
                    img.classList.remove('lazy');
                }
            });

            if (lazyImages.length === 0) {
                document.removeEventListener('scroll', lazyLoad);
                window.removeEventListener('resize', lazyLoad);
                window.removeEventListener('orientationChange', lazyLoad);
            }
        }

        document.addEventListener('scroll', lazyLoad);
        window.addEventListener('resize', lazyLoad);
        window.addEventListener('orientationChange', lazyLoad);
    }
}

/**
 * Initialize theme switcher
 */
function initThemeSwitcher() {
    const themeSwitcher = document.querySelector('.theme-switcher');
    if (!themeSwitcher) return;

    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'light') {
        document.documentElement.classList.add('light-theme');
        themeSwitcher.classList.add('light');
    } else if (savedTheme === 'dark' || prefersDark) {
        document.documentElement.classList.add('dark-theme');
        themeSwitcher.classList.add('dark');
    }

    // Toggle theme on click
    themeSwitcher.addEventListener('click', () => {
        if (document.documentElement.classList.contains('light-theme')) {
            document.documentElement.classList.remove('light-theme');
            document.documentElement.classList.add('dark-theme');
            themeSwitcher.classList.remove('light');
            themeSwitcher.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark-theme');
            document.documentElement.classList.add('light-theme');
            themeSwitcher.classList.remove('dark');
            themeSwitcher.classList.add('light');
            localStorage.setItem('theme', 'light');
        }
    });
}

/**
 * Initialize Google Analytics
 */
function initAnalytics() {
    // Only load analytics if user has consented to cookies
    if (localStorage.getItem('cookie-consent') === 'accepted') {
        // Google Analytics code
        window.dataLayer = window.dataLayer || [];
        function gtag() { dataLayer.push(arguments); }
        gtag('js', new Date());
        gtag('config', 'G-XXXXXXXXXX'); // Replace with your Google Analytics ID

        // Load the analytics script
        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX'; // Replace with your Google Analytics ID
        document.head.appendChild(script);
    }
}

/**
 * Initialize cookie consent banner
 */
function initCookieConsent() {
    // Check if user has already made a choice
    if (localStorage.getItem('cookie-consent')) {
        return;
    }

    // Create cookie consent banner
    const banner = document.createElement('div');
    banner.className = 'cookie-banner';
    banner.innerHTML = `
        <div class="cookie-content">
            <p>We use cookies to enhance your experience on our website. By continuing to browse, you agree to our <a href="/cookies.php">Cookie Policy</a>.</p>
            <div class="cookie-buttons">
                <button class="btn btn-secondary cookie-decline">Decline</button>
                <button class="btn btn-primary cookie-accept">Accept</button>
            </div>
        </div>
    `;

    document.body.appendChild(banner);

    // Show banner with animation
    setTimeout(() => {
        banner.classList.add('show');
    }, 1000);

    // Handle accept button
    banner.querySelector('.cookie-accept').addEventListener('click', () => {
        localStorage.setItem('cookie-consent', 'accepted');
        banner.classList.remove('show');

        // Initialize analytics after consent
        initAnalytics();

        // Remove banner after animation
        setTimeout(() => {
            document.body.removeChild(banner);
        }, 300);
    });

    // Handle decline button
    banner.querySelector('.cookie-decline').addEventListener('click', () => {
        localStorage.setItem('cookie-consent', 'declined');
        banner.classList.remove('show');

        // Remove banner after animation
        setTimeout(() => {
            document.body.removeChild(banner);
        }, 300);
    });
}

/**
 * Detect browser and device
 * @returns {Object} Browser and device information
 */
function detectBrowser() {
    const userAgent = navigator.userAgent;
    let browser = 'Unknown';
    let version = 'Unknown';
    let os = 'Unknown';
    let mobile = false;

    // Detect browser
    if (userAgent.indexOf('Firefox') > -1) {
        browser = 'Firefox';
        version = userAgent.match(/Firefox\/(\d+\.\d+)/)[1];
    } else if (userAgent.indexOf('Chrome') > -1 && userAgent.indexOf('Edge') === -1 && userAgent.indexOf('Edg') === -1) {
        browser = 'Chrome';
        version = userAgent.match(/Chrome\/(\d+\.\d+)/)[1];
    } else if (userAgent.indexOf('Safari') > -1 && userAgent.indexOf('Chrome') === -1) {
        browser = 'Safari';
        version = userAgent.match(/Version\/(\d+\.\d+)/)[1];
    } else if (userAgent.indexOf('Edge') > -1 || userAgent.indexOf('Edg') > -1) {
        browser = 'Edge';
        version = userAgent.match(/Edge?\/(\d+\.\d+)/)[1];
    } else if (userAgent.indexOf('MSIE') > -1 || userAgent.indexOf('Trident') > -1) {
        browser = 'Internet Explorer';
        version = userAgent.match(/(?:MSIE |rv:)(\d+\.\d+)/)[1];
    }

    // Detect OS
    if (userAgent.indexOf('Windows') > -1) {
        os = 'Windows';
    } else if (userAgent.indexOf('Mac') > -1) {
        os = 'MacOS';
    } else if (userAgent.indexOf('Linux') > -1) {
        os = 'Linux';
    } else if (userAgent.indexOf('Android') > -1) {
        os = 'Android';
        mobile = true;
    } else if (userAgent.indexOf('iPhone') > -1 || userAgent.indexOf('iPad') > -1) {
        os = 'iOS';
        mobile = true;
    }

    return { browser, version, os, mobile };
}

/**
 * Check if the website is being loaded in an iframe
 * @returns {boolean} True if in iframe
 */
function isInIframe() {
    try {
        return window.self !== window.top;
    } catch (e) {
        return true;
    }
}
