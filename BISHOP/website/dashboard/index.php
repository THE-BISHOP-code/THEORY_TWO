<?php
/**
 * BISHOP Website - Dashboard Home
 * 
 * Main dashboard page for logged-in users.
 */
require_once '../includes/config.php';

// Require login
require_login();

// Get user data
$user = get_current_user();
$user_id = $user['id'];

// Get user's tier
$tier = get_user_tier($user_id);

// Get user's servers
$servers = get_available_servers($user_id);

// Get user's bot configurations
$bot_configs = get_user_bot_configs($user_id);

// Flash message
$flash = get_flash_message();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - <?php echo SITE_NAME; ?></title>
    
    <!-- Favicon -->
    <link rel="icon" href="/assets/img/favicon.ico">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <aside class="dashboard-sidebar">
            <div class="sidebar-header">
                <a href="/" class="sidebar-logo">
                    <img src="/assets/img/logo.png" alt="<?php echo SITE_NAME; ?> Logo">
                    <span><?php echo SITE_NAME; ?></span>
                </a>
            </div>
            
            <nav class="sidebar-nav">
                <a href="/dashboard/" class="sidebar-nav-item active">
                    <span class="sidebar-nav-icon"><i class="fas fa-home"></i></span>
                    Dashboard
                </a>
                <a href="/dashboard/bot-settings.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-robot"></i></span>
                    Bot Settings
                </a>
                <a href="/dashboard/tokens.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-key"></i></span>
                    API Tokens
                </a>
                <a href="/dashboard/config.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-cogs"></i></span>
                    Configuration
                </a>
                <a href="/dashboard/servers.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-server"></i></span>
                    Servers
                </a>
                <a href="/dashboard/logs.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-list"></i></span>
                    Logs
                </a>
                <a href="/dashboard/support.php" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-question-circle"></i></span>
                    Support
                </a>
            </nav>
            
            <div class="sidebar-footer">
                <div class="user-info">
                    <div class="user-avatar">
                        <img src="<?php echo get_discord_avatar_url($_SESSION['discord_id'], $_SESSION['avatar']); ?>" alt="User Avatar">
                    </div>
                    <div class="user-details">
                        <div class="user-name"><?php echo h($_SESSION['username']); ?></div>
                        <div class="user-role"><?php echo $tier; ?></div>
                    </div>
                </div>
                <a href="/dashboard/logout.php" class="btn btn-secondary" style="margin-top: 1rem; width: 100%;">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </aside>
        
        <!-- Main Content -->
        <main class="dashboard-main">
            <header class="dashboard-header">
                <button class="toggle-sidebar">
                    <i class="fas fa-bars"></i>
                </button>
                
                <div>
                    <h1>Dashboard</h1>
                </div>
                
                <div>
                    <span class="badge"><?php echo $tier; ?></span>
                </div>
            </header>
            
            <div class="dashboard-content">
                <?php if ($flash): ?>
                    <div class="alert alert-<?php echo $flash['type']; ?>">
                        <?php echo $flash['message']; ?>
                    </div>
                <?php endif; ?>
                
                <div class="dashboard-grid">
                    <!-- System Stats -->
                    <div class="dashboard-panel">
                        <div class="panel-header">
                            <h2 class="panel-title">
                                <i class="fas fa-chart-line panel-icon"></i>
                                System Status
                            </h2>
                            <div class="panel-actions">
                                <button class="panel-action" title="Refresh" onclick="updateSystemStats()">
                                    <i class="fas fa-sync-alt"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-microchip"></i>
                                </div>
                                <div class="stat-value cpu-usage">25%</div>
                                <div class="stat-label">CPU Usage</div>
                                <div class="progress">
                                    <div class="progress-bar" style="width: 25%; background-color: var(--accent-blue);"></div>
                                </div>
                            </div>
                            
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-memory"></i>
                                </div>
                                <div class="stat-value ram-usage">40%</div>
                                <div class="stat-label">RAM Usage</div>
                                <div class="progress">
                                    <div class="progress-bar" style="width: 40%; background-color: var(--accent-blue);"></div>
                                </div>
                            </div>
                            
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-clock"></i>
                                </div>
                                <div class="stat-value uptime" data-uptime="3600">01:00:00</div>
                                <div class="stat-label">Uptime</div>
                            </div>
                            
                            <div class="stat-card">
                                <div class="stat-icon">
                                    <i class="fas fa-server"></i>
                                </div>
                                <div class="stat-value"><?php echo count($servers); ?></div>
                                <div class="stat-label">Servers</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Bot Status -->
                    <div class="dashboard-panel">
                        <div class="panel-header">
                            <h2 class="panel-title">
                                <i class="fas fa-robot panel-icon"></i>
                                Bot Status
                            </h2>
                            <div class="panel-actions">
                                <a href="/dashboard/bot-settings.php" class="panel-action" title="Settings">
                                    <i class="fas fa-cog"></i>
                                </a>
                            </div>
                        </div>
                        
                        <div class="bot-preview">
                            <div class="bot-avatar">
                                <img src="/assets/img/bot-avatar.png" alt="Bot Avatar">
                            </div>
                            <div class="bot-info">
                                <div class="bot-name">BISHOP</div>
                                <div class="bot-status">
                                    <span class="bot-status-indicator"></span>
                                    <span>Online</span>
                                </div>
                                <div class="bot-description">
                                    Advanced AI assistant for Discord
                                </div>
                            </div>
                        </div>
                        
                        <?php if ($tier === 'Abysswalker'): ?>
                            <div class="server-list">
                                <?php foreach ($bot_configs as $config): ?>
                                    <div class="server-card">
                                        <div class="server-icon">
                                            <img src="<?php echo get_discord_server_icon_url($config['server_discord_id'], $config['server_icon']); ?>" alt="Server Icon">
                                        </div>
                                        <div class="server-name"><?php echo h($config['server_name']); ?></div>
                                        <div class="server-members">Last updated: <?php echo format_date($config['updated_at'], true); ?></div>
                                    </div>
                                <?php endforeach; ?>
                                
                                <?php if (count($bot_configs) < 2): ?>
                                    <a href="/dashboard/bot-settings.php" class="server-card">
                                        <div class="server-icon">
                                            <i class="fas fa-plus" style="font-size: 2rem; color: var(--text-muted);"></i>
                                        </div>
                                        <div class="server-name">Add Server</div>
                                        <div class="server-members">Configure bot for a new server</div>
                                    </a>
                                <?php endif; ?>
                            </div>
                        <?php else: ?>
                            <div class="upgrade-message">
                                <p>Upgrade to Abysswalker tier to customize your bot for up to 2 servers.</p>
                                <a href="/pricing.php#abysswalker" class="btn btn-primary">Upgrade Now</a>
                            </div>
                        <?php endif; ?>
                    </div>
                </div>
                
                <div class="dashboard-grid">
                    <!-- Quick Actions -->
                    <div class="dashboard-panel">
                        <div class="panel-header">
                            <h2 class="panel-title">
                                <i class="fas fa-bolt panel-icon"></i>
                                Quick Actions
                            </h2>
                        </div>
                        
                        <div class="quick-actions">
                            <a href="/dashboard/bot-settings.php" class="quick-action-btn">
                                <i class="fas fa-robot"></i>
                                <span>Configure Bot</span>
                            </a>
                            <a href="/dashboard/tokens.php" class="quick-action-btn">
                                <i class="fas fa-key"></i>
                                <span>Manage Tokens</span>
                            </a>
                            <a href="/dashboard/config.php" class="quick-action-btn">
                                <i class="fas fa-cogs"></i>
                                <span>Edit Config</span>
                            </a>
                            <a href="/dashboard/logs.php" class="quick-action-btn">
                                <i class="fas fa-list"></i>
                                <span>View Logs</span>
                            </a>
                        </div>
                    </div>
                    
                    <!-- Tier Information -->
                    <div class="dashboard-panel">
                        <div class="panel-header">
                            <h2 class="panel-title">
                                <i class="fas fa-crown panel-icon"></i>
                                Your Tier: <?php echo $tier; ?>
                            </h2>
                        </div>
                        
                        <div class="tier-info">
                            <?php $features = get_tier_features($tier); ?>
                            <div class="tier-features">
                                <div class="tier-feature">
                                    <i class="fas fa-comment"></i>
                                    <div>
                                        <strong>Replies per Conversation</strong>
                                        <span><?php echo $features['replies']; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-save"></i>
                                    <div>
                                        <strong>Max Saved Files</strong>
                                        <span><?php echo $features['saves']; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-clock"></i>
                                    <div>
                                        <strong>Cooldown</strong>
                                        <span><?php echo $features['cooldown']; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-robot"></i>
                                    <div>
                                        <strong>Custom Bot</strong>
                                        <span><?php echo $features['custom_bot'] ? 'Yes' : 'No'; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-terminal"></i>
                                    <div>
                                        <strong>Premium Commands</strong>
                                        <span><?php echo $features['premium_commands'] ? 'Yes' : 'No'; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-exchange-alt"></i>
                                    <div>
                                        <strong>Market Access</strong>
                                        <span><?php echo $features['market_access']; ?></span>
                                    </div>
                                </div>
                                <div class="tier-feature">
                                    <i class="fas fa-headset"></i>
                                    <div>
                                        <strong>Support</strong>
                                        <span><?php echo $features['support']; ?></span>
                                    </div>
                                </div>
                            </div>
                            
                            <?php if ($tier !== 'Abysswalker'): ?>
                                <div class="upgrade-cta">
                                    <p>Upgrade to unlock more features and customize your bot!</p>
                                    <a href="/pricing.php" class="btn btn-primary">Upgrade Now</a>
                                </div>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="/assets/js/main.js"></script>
    <script src="/assets/js/dashboard.js"></script>
</body>
</html>
