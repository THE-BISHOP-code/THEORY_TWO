/**
 * BISHOP Dashboard - JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar toggle
    initSidebarToggle();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize server selection
    initServerSelection();
    
    // Initialize token management
    initTokenManagement();
    
    // Initialize bot customization
    initBotCustomization();
    
    // Initialize configuration panels
    initConfigPanels();
    
    // Initialize data charts
    initDataCharts();
    
    // Initialize real-time updates
    initRealTimeUpdates();
});

/**
 * Initialize sidebar toggle for mobile
 */
function initSidebarToggle() {
    const toggleButton = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.dashboard-sidebar');
    
    if (!toggleButton || !sidebar) return;
    
    toggleButton.addEventListener('click', () => {
        sidebar.classList.toggle('show');
    });
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 992 && 
            sidebar.classList.contains('show') && 
            !sidebar.contains(e.target) && 
            e.target !== toggleButton) {
            sidebar.classList.remove('show');
        }
    });
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
 * Initialize server selection
 */
function initServerSelection() {
    const serverCards = document.querySelectorAll('.server-card');
    
    serverCards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove selected class from all cards
            serverCards.forEach(c => c.classList.remove('selected'));
            
            // Add selected class to clicked card
            card.classList.add('selected');
            
            // Update server-specific content
            const serverId = card.getAttribute('data-server-id');
            updateServerContent(serverId);
        });
    });
}

/**
 * Update content based on selected server
 * @param {string} serverId - The ID of the selected server
 */
function updateServerContent(serverId) {
    // This would typically fetch server-specific data from the backend
    console.log(`Updating content for server: ${serverId}`);
    
    // Show loading state
    const contentAreas = document.querySelectorAll('[data-server-content]');
    contentAreas.forEach(area => {
        area.innerHTML = '<div class="loading-spinner"></div>';
    });
    
    // Simulate API call
    setTimeout(() => {
        // Update content areas with server-specific data
        contentAreas.forEach(area => {
            const contentType = area.getAttribute('data-server-content');
            
            switch(contentType) {
                case 'stats':
                    area.innerHTML = generateServerStats(serverId);
                    break;
                case 'channels':
                    area.innerHTML = generateServerChannels(serverId);
                    break;
                case 'roles':
                    area.innerHTML = generateServerRoles(serverId);
                    break;
                default:
                    area.innerHTML = `<p>No data available for ${contentType}</p>`;
            }
        });
        
        // Initialize any new components
        initDataCharts();
    }, 1000);
}

/**
 * Generate server stats HTML
 * @param {string} serverId - The server ID
 * @returns {string} - HTML content
 */
function generateServerStats(serverId) {
    // This would be populated with real data from the API
    return `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-users"></i></div>
                <div class="stat-value">128</div>
                <div class="stat-label">Members</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-hashtag"></i></div>
                <div class="stat-value">15</div>
                <div class="stat-label">Channels</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-tag"></i></div>
                <div class="stat-value">8</div>
                <div class="stat-label">Roles</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon"><i class="fas fa-comment"></i></div>
                <div class="stat-value">1,254</div>
                <div class="stat-label">Messages Today</div>
            </div>
        </div>
        <div class="data-chart" id="server-activity-chart"></div>
    `;
}

/**
 * Generate server channels HTML
 * @param {string} serverId - The server ID
 * @returns {string} - HTML content
 */
function generateServerChannels(serverId) {
    // This would be populated with real data from the API
    return `
        <div class="channel-list">
            <div class="channel-category">
                <div class="channel-category-name">Text Channels</div>
                <div class="channel-item">
                    <i class="fas fa-hashtag"></i>
                    <span>general</span>
                </div>
                <div class="channel-item">
                    <i class="fas fa-hashtag"></i>
                    <span>bot-commands</span>
                </div>
                <div class="channel-item">
                    <i class="fas fa-hashtag"></i>
                    <span>announcements</span>
                </div>
            </div>
            <div class="channel-category">
                <div class="channel-category-name">Voice Channels</div>
                <div class="channel-item">
                    <i class="fas fa-volume-up"></i>
                    <span>General Voice</span>
                </div>
                <div class="channel-item">
                    <i class="fas fa-volume-up"></i>
                    <span>Gaming</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generate server roles HTML
 * @param {string} serverId - The server ID
 * @returns {string} - HTML content
 */
function generateServerRoles(serverId) {
    // This would be populated with real data from the API
    return `
        <div class="role-list">
            <div class="role-item" style="border-color: #e74c3c">
                <div class="role-name">Admin</div>
                <div class="role-members">3 members</div>
            </div>
            <div class="role-item" style="border-color: #3498db">
                <div class="role-name">Moderator</div>
                <div class="role-members">5 members</div>
            </div>
            <div class="role-item" style="border-color: #2ecc71">
                <div class="role-name">Member</div>
                <div class="role-members">120 members</div>
            </div>
        </div>
    `;
}

/**
 * Initialize token management
 */
function initTokenManagement() {
    // Token visibility toggle
    const tokenToggles = document.querySelectorAll('.token-visibility');
    
    tokenToggles.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const tokenValue = toggle.closest('.token-card').querySelector('.token-value');
            const tokenMask = tokenValue.querySelector('.token-mask');
            const tokenText = tokenValue.getAttribute('data-token');
            
            if (tokenMask.style.display === 'none') {
                // Hide token
                tokenMask.style.display = '';
                toggle.innerHTML = '<i class="fas fa-eye"></i>';
            } else {
                // Show token
                tokenMask.style.display = 'none';
                tokenMask.insertAdjacentHTML('afterend', `<span class="token-text">${tokenText}</span>`);
                toggle.innerHTML = '<i class="fas fa-eye-slash"></i>';
                
                // Auto-hide after 30 seconds
                setTimeout(() => {
                    const tokenTextElement = tokenValue.querySelector('.token-text');
                    if (tokenTextElement) {
                        tokenTextElement.remove();
                    }
                    tokenMask.style.display = '';
                    toggle.innerHTML = '<i class="fas fa-eye"></i>';
                }, 30000);
            }
        });
    });
    
    // Token copy
    const tokenCopyButtons = document.querySelectorAll('.token-copy');
    
    tokenCopyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tokenValue = button.closest('.token-card').querySelector('.token-value');
            const tokenText = tokenValue.getAttribute('data-token');
            
            copyToClipboard(tokenText);
        });
    });
    
    // New token form
    const newTokenForm = document.querySelector('#new-token-form');
    
    if (newTokenForm) {
        newTokenForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const nameInput = newTokenForm.querySelector('input[name="token-name"]');
            const typeSelect = newTokenForm.querySelector('select[name="token-type"]');
            
            if (!nameInput.value.trim()) {
                showInputError(nameInput, 'Please enter a name for the token');
                return;
            }
            
            // Show loading state
            const submitButton = newTokenForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="loading-spinner"></span> Generating...';
            
            // Simulate API call
            setTimeout(() => {
                // Reset form
                newTokenForm.reset();
                submitButton.disabled = false;
                submitButton.textContent = 'Generate Token';
                
                // Show success message
                showNotification('Token generated successfully!', 'success');
                
                // Add new token to list (in a real app, this would come from the API)
                const tokenList = document.querySelector('.token-list');
                const newToken = generateTokenCard({
                    id: 'new-token-' + Date.now(),
                    name: nameInput.value,
                    type: typeSelect.value,
                    value: generateRandomToken(),
                    created: new Date()
                });
                
                tokenList.insertAdjacentHTML('afterbegin', newToken);
                
                // Initialize new token card
                initTokenManagement();
            }, 1500);
        });
    }
}

/**
 * Generate a random token string
 * @returns {string} - A random token
 */
function generateRandomToken() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let token = '';
    
    for (let i = 0; i < 32; i++) {
        token += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    
    return token;
}

/**
 * Generate HTML for a token card
 * @param {Object} token - The token object
 * @returns {string} - HTML content
 */
function generateTokenCard(token) {
    return `
        <div class="token-card" data-token-id="${token.id}">
            <div class="token-header">
                <div class="token-name">${token.name} <span class="token-type">${token.type}</span></div>
                <div class="token-actions">
                    <button class="token-visibility" title="Toggle visibility"><i class="fas fa-eye"></i></button>
                    <button class="token-delete" title="Delete token"><i class="fas fa-trash"></i></button>
                </div>
            </div>
            <div class="token-value" data-token="${token.value}">
                <span class="token-mask">••••••••••••••••••••••••••••••••</span>
                <button class="token-copy" title="Copy to clipboard"><i class="fas fa-copy"></i></button>
            </div>
            <div class="token-info">
                Created: ${formatDate(token.created, true)}
            </div>
        </div>
    `;
}

/**
 * Initialize bot customization
 */
function initBotCustomization() {
    // Avatar preview
    const avatarInput = document.querySelector('#bot-avatar');
    const avatarPreview = document.querySelector('.bot-avatar img');
    
    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', () => {
            const file = avatarInput.files[0];
            
            if (file) {
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    avatarPreview.src = e.target.result;
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Bot name preview
    const nameInput = document.querySelector('#bot-name');
    const namePreview = document.querySelector('.bot-name');
    
    if (nameInput && namePreview) {
        nameInput.addEventListener('input', () => {
            namePreview.textContent = nameInput.value || 'BISHOP Bot';
        });
    }
    
    // Bot status preview
    const statusInput = document.querySelector('#bot-status');
    const statusPreview = document.querySelector('.bot-status span:last-child');
    
    if (statusInput && statusPreview) {
        statusInput.addEventListener('input', () => {
            statusPreview.textContent = statusInput.value || 'Online';
        });
    }
    
    // Bot description preview
    const descriptionInput = document.querySelector('#bot-description');
    const descriptionPreview = document.querySelector('.bot-description');
    
    if (descriptionInput && descriptionPreview) {
        descriptionInput.addEventListener('input', () => {
            descriptionPreview.textContent = descriptionInput.value || 'An advanced Discord bot with AI capabilities.';
        });
    }
    
    // Color picker
    const colorOptions = document.querySelectorAll('.color-option');
    const botAvatar = document.querySelector('.bot-avatar');
    
    colorOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Remove selected class from all options
            colorOptions.forEach(o => o.classList.remove('selected'));
            
            // Add selected class to clicked option
            option.classList.add('selected');
            
            // Update bot avatar border color
            const color = option.style.backgroundColor;
            botAvatar.style.borderColor = color;
        });
    });
    
    // Save customization form
    const customizationForm = document.querySelector('#bot-customization-form');
    
    if (customizationForm) {
        customizationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Show loading state
            const submitButton = customizationForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="loading-spinner"></span> Saving...';
            
            // Simulate API call
            setTimeout(() => {
                submitButton.disabled = false;
                submitButton.textContent = 'Save Changes';
                
                // Show success message
                showNotification('Bot customization saved successfully!', 'success');
            }, 1500);
        });
    }
}

/**
 * Initialize configuration panels
 */
function initConfigPanels() {
    // Toggle switches
    const toggleSwitches = document.querySelectorAll('.toggle-switch input');
    
    toggleSwitches.forEach(toggle => {
        toggle.addEventListener('change', () => {
            const configKey = toggle.getAttribute('data-config-key');
            const isEnabled = toggle.checked;
            
            // This would typically update the config via API
            console.log(`Setting ${configKey} to ${isEnabled}`);
            
            // Show notification
            showNotification(`${configKey} ${isEnabled ? 'enabled' : 'disabled'}`, 'info');
            
            // Update dependent elements
            updateDependentConfig(configKey, isEnabled);
        });
    });
    
    // Range inputs
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    
    rangeInputs.forEach(input => {
        const valueDisplay = input.nextElementSibling;
        
        // Initialize value display
        if (valueDisplay && valueDisplay.classList.contains('range-value')) {
            valueDisplay.textContent = input.value;
        }
        
        input.addEventListener('input', () => {
            // Update value display
            if (valueDisplay && valueDisplay.classList.contains('range-value')) {
                valueDisplay.textContent = input.value;
            }
            
            const configKey = input.getAttribute('data-config-key');
            console.log(`Setting ${configKey} to ${input.value}`);
        });
    });
    
    // Save config form
    const configForm = document.querySelector('#config-form');
    
    if (configForm) {
        configForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Show loading state
            const submitButton = configForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="loading-spinner"></span> Saving...';
            
            // Simulate API call
            setTimeout(() => {
                submitButton.disabled = false;
                submitButton.textContent = 'Save Configuration';
                
                // Show success message
                showNotification('Configuration saved successfully!', 'success');
            }, 1500);
        });
    }
}

/**
 * Update dependent configuration elements
 * @param {string} key - The configuration key that changed
 * @param {boolean} value - The new value
 */
function updateDependentConfig(key, value) {
    // Find elements that depend on this config
    const dependentElements = document.querySelectorAll(`[data-depends-on="${key}"]`);
    
    dependentElements.forEach(element => {
        const container = element.closest('.form-group, .config-section');
        
        if (value) {
            // Enable dependent element
            element.disabled = false;
            if (container) {
                container.classList.remove('disabled');
            }
        } else {
            // Disable dependent element
            element.disabled = true;
            if (container) {
                container.classList.add('disabled');
            }
        }
    });
}

/**
 * Initialize data charts
 */
function initDataCharts() {
    // This would typically use a charting library like Chart.js
    // For this example, we'll create a simple activity chart
    
    const activityChart = document.getElementById('server-activity-chart');
    
    if (activityChart) {
        // Create a simple bar chart with CSS
        const data = [25, 40, 60, 35, 50, 70, 45, 30, 55, 65, 75, 50];
        const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        let chartHTML = '<div class="simple-chart"><div class="chart-bars">';
        
        data.forEach((value, index) => {
            const height = value + '%';
            chartHTML += `
                <div class="chart-bar" style="height: ${height}">
                    <div class="chart-bar-value">${value}</div>
                    <div class="chart-bar-label">${labels[index]}</div>
                </div>
            `;
        });
        
        chartHTML += '</div></div>';
        
        activityChart.innerHTML = chartHTML;
    }
}

/**
 * Initialize real-time updates
 */
function initRealTimeUpdates() {
    // This would typically use WebSockets for real-time updates
    // For this example, we'll simulate updates with setInterval
    
    // Update system stats every 5 seconds
    setInterval(() => {
        updateSystemStats();
    }, 5000);
    
    // Update bot status every 10 seconds
    setInterval(() => {
        updateBotStatus();
    }, 10000);
}

/**
 * Update system statistics
 */
function updateSystemStats() {
    const cpuUsage = document.querySelector('.cpu-usage');
    const ramUsage = document.querySelector('.ram-usage');
    const uptime = document.querySelector('.uptime');
    
    if (cpuUsage) {
        const newValue = Math.floor(Math.random() * 30) + 10; // Random value between 10-40%
        cpuUsage.textContent = `${newValue}%`;
        
        // Update progress bar if exists
        const progressBar = cpuUsage.closest('.stat-card').querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${newValue}%`;
            
            // Update color based on value
            if (newValue < 20) {
                progressBar.style.backgroundColor = 'var(--accent-green)';
            } else if (newValue < 50) {
                progressBar.style.backgroundColor = 'var(--accent-blue)';
            } else if (newValue < 80) {
                progressBar.style.backgroundColor = 'var(--accent-gold)';
            } else {
                progressBar.style.backgroundColor = 'var(--accent-red)';
            }
        }
    }
    
    if (ramUsage) {
        const newValue = Math.floor(Math.random() * 40) + 20; // Random value between 20-60%
        ramUsage.textContent = `${newValue}%`;
        
        // Update progress bar if exists
        const progressBar = ramUsage.closest('.stat-card').querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${newValue}%`;
            
            // Update color based on value
            if (newValue < 20) {
                progressBar.style.backgroundColor = 'var(--accent-green)';
            } else if (newValue < 50) {
                progressBar.style.backgroundColor = 'var(--accent-blue)';
            } else if (newValue < 80) {
                progressBar.style.backgroundColor = 'var(--accent-gold)';
            } else {
                progressBar.style.backgroundColor = 'var(--accent-red)';
            }
        }
    }
    
    if (uptime) {
        // Increment uptime by 5 seconds
        const currentUptime = uptime.getAttribute('data-uptime') || '0';
        const newUptime = parseInt(currentUptime) + 5;
        uptime.setAttribute('data-uptime', newUptime.toString());
        
        // Format uptime
        const hours = Math.floor(newUptime / 3600);
        const minutes = Math.floor((newUptime % 3600) / 60);
        const seconds = newUptime % 60;
        
        uptime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
}

/**
 * Update bot status
 */
function updateBotStatus() {
    const botStatusIndicator = document.querySelector('.bot-status-indicator');
    const botStatusText = document.querySelector('.bot-status span:last-child');
    
    if (!botStatusIndicator || !botStatusText) return;
    
    // Simulate occasional status changes
    const random = Math.random();
    
    if (random < 0.05) {
        // 5% chance to show reconnecting
        botStatusIndicator.style.backgroundColor = 'var(--accent-gold)';
        botStatusText.textContent = 'Reconnecting...';
    } else if (random < 0.02) {
        // 2% chance to show offline
        botStatusIndicator.style.backgroundColor = 'var(--accent-red)';
        botStatusText.textContent = 'Offline';
    } else {
        // 93% chance to show online
        botStatusIndicator.style.backgroundColor = 'var(--accent-green)';
        botStatusText.textContent = document.querySelector('#bot-status')?.value || 'Online';
    }
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
