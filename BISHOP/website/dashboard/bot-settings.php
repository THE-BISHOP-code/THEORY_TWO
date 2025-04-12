<?php
/**
 * BISHOP Website - Bot Settings
 * 
 * Allows Abysswalker tier users to customize their bot.
 */
require_once '../includes/config.php';

// Require login and Abysswalker tier
require_login();
require_abysswalker();

// Get user data
$user = get_current_user();
$user_id = $user['id'];

// Get user's servers
$servers = get_available_servers($user_id);

// Check if a server is selected
$selected_server_id = isset($_GET['server']) ? (int)$_GET['server'] : null;

// If no server is selected, use the first available server
if (!$selected_server_id && !empty($servers)) {
    $selected_server_id = $servers[0]['id'];
}

// Get the selected server
$selected_server = null;
foreach ($servers as $server) {
    if ($server['id'] === $selected_server_id) {
        $selected_server = $server;
        break;
    }
}

// Get bot configuration for the selected server
$bot_config = $selected_server ? get_user_bot_config($user_id, $selected_server_id) : null;

// Process form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // Validate server ID
    if (!$selected_server) {
        flash_message('error', 'Invalid server selected.');
        header('Location: /dashboard/bot-settings.php');
        exit;
    }
    
    // Get form data
    $bot_name = isset($_POST['bot_name']) ? trim($_POST['bot_name']) : '';
    $bot_status = isset($_POST['bot_status']) ? trim($_POST['bot_status']) : '';
    $bot_activity = isset($_POST['bot_activity']) ? trim($_POST['bot_activity']) : '';
    $bot_activity_text = isset($_POST['bot_activity_text']) ? trim($_POST['bot_activity_text']) : '';
    $bot_description = isset($_POST['bot_description']) ? trim($_POST['bot_description']) : '';
    $embed_color = isset($_POST['embed_color']) ? trim($_POST['embed_color']) : '';
    
    // Validate data
    $errors = [];
    
    if (empty($bot_name)) {
        $errors[] = 'Bot name is required.';
    } elseif (strlen($bot_name) > 32) {
        $errors[] = 'Bot name must be 32 characters or less.';
    }
    
    if (strlen($bot_status) > 128) {
        $errors[] = 'Bot status must be 128 characters or less.';
    }
    
    if (strlen($bot_activity_text) > 128) {
        $errors[] = 'Bot activity text must be 128 characters or less.';
    }
    
    if (strlen($bot_description) > 256) {
        $errors[] = 'Bot description must be 256 characters or less.';
    }
    
    // Process features
    $features = [
        'spectre_enabled' => isset($_POST['spectre_enabled']),
        'vault_enabled' => isset($_POST['vault_enabled']),
        'exchange_enabled' => isset($_POST['exchange_enabled']),
        'executor_enabled' => isset($_POST['executor_enabled'])
    ];
    
    // If no errors, save the configuration
    if (empty($errors)) {
        // Prepare config data
        $config = [
            'bot_name' => $bot_name,
            'bot_status' => $bot_status,
            'bot_activity' => $bot_activity,
            'bot_activity_text' => $bot_activity_text,
            'bot_description' => $bot_description,
            'embed_color' => $embed_color,
            'features' => $features
        ];
        
        // Handle avatar upload
        if (isset($_FILES['bot_avatar']) && $_FILES['bot_avatar']['error'] === UPLOAD_ERR_OK) {
            $avatar_tmp = $_FILES['bot_avatar']['tmp_name'];
            $avatar_name = $_FILES['bot_avatar']['name'];
            $avatar_ext = strtolower(pathinfo($avatar_name, PATHINFO_EXTENSION));
            
            // Validate image
            $allowed_exts = ['jpg', 'jpeg', 'png', 'gif'];
            if (in_array($avatar_ext, $allowed_exts)) {
                // Generate unique filename
                $avatar_filename = 'bot_avatar_' . $user_id . '_' . $selected_server_id . '.' . $avatar_ext;
                $avatar_path = ASSETS_PATH . '/uploads/' . $avatar_filename;
                
                // Create uploads directory if it doesn't exist
                if (!file_exists(ASSETS_PATH . '/uploads')) {
                    mkdir(ASSETS_PATH . '/uploads', 0755, true);
                }
                
                // Move uploaded file
                if (move_uploaded_file($avatar_tmp, $avatar_path)) {
                    $config['bot_avatar'] = '/assets/uploads/' . $avatar_filename;
                } else {
                    $errors[] = 'Failed to upload avatar image.';
                }
            } else {
                $errors[] = 'Avatar must be a JPG, PNG, or GIF image.';
            }
        }
        
        // Save config if no errors
        if (empty($errors)) {
            if (save_bot_config($user_id, $selected_server_id, $config)) {
                flash_message('success', 'Bot configuration saved successfully.');
                header('Location: /dashboard/bot-settings.php?server=' . $selected_server_id);
                exit;
            } else {
                $errors[] = 'Failed to save bot configuration.';
            }
        }
    }
    
    // If there are errors, display them
    if (!empty($errors)) {
        $error_message = implode('<br>', $errors);
        flash_message('error', $error_message);
    }
}

// Flash message
$flash = get_flash_message();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Settings - <?php echo SITE_NAME; ?></title>
    
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
                <a href="/dashboard/" class="sidebar-nav-item">
                    <span class="sidebar-nav-icon"><i class="fas fa-home"></i></span>
                    Dashboard
                </a>
                <a href="/dashboard/bot-settings.php" class="sidebar-nav-item active">
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
                        <div class="user-role">Abysswalker</div>
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
                    <h1>Bot Settings</h1>
                </div>
                
                <div>
                    <span class="badge">Abysswalker</span>
                </div>
            </header>
            
            <div class="dashboard-content">
                <?php if ($flash): ?>
                    <div class="alert alert-<?php echo $flash['type']; ?>">
                        <?php echo $flash['message']; ?>
                    </div>
                <?php endif; ?>
                
                <!-- Server Selection -->
                <div class="dashboard-panel">
                    <div class="panel-header">
                        <h2 class="panel-title">
                            <i class="fas fa-server panel-icon"></i>
                            Select Server
                        </h2>
                    </div>
                    
                    <div class="server-list">
                        <?php foreach ($servers as $server): ?>
                            <?php if ($server['available']): ?>
                                <a href="/dashboard/bot-settings.php?server=<?php echo $server['id']; ?>" class="server-card <?php echo $server['id'] === $selected_server_id ? 'selected' : ''; ?>">
                                    <div class="server-icon">
                                        <img src="<?php echo get_discord_server_icon_url($server['discord_id'], $server['icon']); ?>" alt="Server Icon">
                                    </div>
                                    <div class="server-name"><?php echo h($server['name']); ?></div>
                                    <div class="server-members">
                                        <?php echo $server['configured'] ? 'Configured' : 'Not Configured'; ?>
                                    </div>
                                </a>
                            <?php else: ?>
                                <div class="server-card disabled">
                                    <div class="server-icon">
                                        <img src="<?php echo get_discord_server_icon_url($server['discord_id'], $server['icon']); ?>" alt="Server Icon">
                                    </div>
                                    <div class="server-name"><?php echo h($server['name']); ?></div>
                                    <div class="server-members">
                                        Upgrade to add more servers
                                    </div>
                                </div>
                            <?php endif; ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                
                <?php if ($selected_server): ?>
                    <!-- Bot Customization -->
                    <div class="dashboard-panel">
                        <div class="panel-header">
                            <h2 class="panel-title">
                                <i class="fas fa-robot panel-icon"></i>
                                Customize Bot for <?php echo h($selected_server['name']); ?>
                            </h2>
                        </div>
                        
                        <div class="bot-preview">
                            <div class="bot-avatar">
                                <img src="<?php echo $bot_config['bot_avatar'] ? $bot_config['bot_avatar'] : '/assets/img/bot-avatar.png'; ?>" alt="Bot Avatar">
                            </div>
                            <div class="bot-info">
                                <div class="bot-name"><?php echo h($bot_config['bot_name']); ?></div>
                                <div class="bot-status">
                                    <span class="bot-status-indicator"></span>
                                    <span><?php echo h($bot_config['bot_status']); ?></span>
                                </div>
                                <div class="bot-description">
                                    <?php echo h($bot_config['bot_description']); ?>
                                </div>
                            </div>
                        </div>
                        
                        <form id="bot-customization-form" action="/dashboard/bot-settings.php?server=<?php echo $selected_server_id; ?>" method="post" enctype="multipart/form-data">
                            <div class="form-group">
                                <label for="bot-name">Bot Name</label>
                                <input type="text" id="bot-name" name="bot_name" class="form-control" value="<?php echo h($bot_config['bot_name']); ?>" maxlength="32" required>
                                <div class="form-text">The name of your bot (max 32 characters).</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="bot-avatar">Bot Avatar</label>
                                <input type="file" id="bot-avatar" name="bot_avatar" class="form-control" accept="image/jpeg,image/png,image/gif">
                                <div class="form-text">Upload a square image (recommended size: 128x128 pixels).</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="bot-status">Bot Status</label>
                                <input type="text" id="bot-status" name="bot_status" class="form-control" value="<?php echo h($bot_config['bot_status']); ?>" maxlength="128">
                                <div class="form-text">The status message shown in Discord (max 128 characters).</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="bot-activity">Bot Activity</label>
                                <select id="bot-activity" name="bot_activity" class="form-control">
                                    <option value="playing" <?php echo $bot_config['bot_activity'] === 'playing' ? 'selected' : ''; ?>>Playing</option>
                                    <option value="streaming" <?php echo $bot_config['bot_activity'] === 'streaming' ? 'selected' : ''; ?>>Streaming</option>
                                    <option value="listening" <?php echo $bot_config['bot_activity'] === 'listening' ? 'selected' : ''; ?>>Listening to</option>
                                    <option value="watching" <?php echo $bot_config['bot_activity'] === 'watching' ? 'selected' : ''; ?>>Watching</option>
                                    <option value="competing" <?php echo $bot_config['bot_activity'] === 'competing' ? 'selected' : ''; ?>>Competing in</option>
                                </select>
                                <div class="form-text">The type of activity shown in Discord.</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="bot-activity-text">Activity Text</label>
                                <input type="text" id="bot-activity-text" name="bot_activity_text" class="form-control" value="<?php echo h($bot_config['bot_activity_text']); ?>" maxlength="128">
                                <div class="form-text">The text shown after the activity type (max 128 characters).</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="bot-description">Bot Description</label>
                                <textarea id="bot-description" name="bot_description" class="form-control" rows="3" maxlength="256"><?php echo h($bot_config['bot_description']); ?></textarea>
                                <div class="form-text">A short description of your bot (max 256 characters).</div>
                            </div>
                            
                            <div class="form-group">
                                <label for="embed-color">Embed Color</label>
                                <input type="color" id="embed-color" name="embed_color" class="form-control" value="<?php echo h($bot_config['embed_color']); ?>">
                                <div class="form-text">The color used for embeds in Discord.</div>
                            </div>
                            
                            <div class="form-group">
                                <label>Bot Accent Color</label>
                                <div class="color-picker">
                                    <div class="color-option" style="background-color: #3498db;" data-color="#3498db"></div>
                                    <div class="color-option" style="background-color: #2ecc71;" data-color="#2ecc71"></div>
                                    <div class="color-option" style="background-color: #e74c3c;" data-color="#e74c3c"></div>
                                    <div class="color-option" style="background-color: #f1c40f;" data-color="#f1c40f"></div>
                                    <div class="color-option" style="background-color: #9b59b6;" data-color="#9b59b6"></div>
                                    <div class="color-option" style="background-color: #1abc9c;" data-color="#1abc9c"></div>
                                    <div class="color-option" style="background-color: #e67e22;" data-color="#e67e22"></div>
                                    <div class="color-option" style="background-color: #34495e;" data-color="#34495e"></div>
                                </div>
                                <div class="form-text">The accent color used for the bot's avatar border.</div>
                            </div>
                            
                            <h3>Features</h3>
                            
                            <div class="form-group">
                                <div class="form-check">
                                    <label class="toggle-switch">
                                        <input type="checkbox" name="spectre_enabled" <?php echo $bot_config['features']['spectre_enabled'] ? 'checked' : ''; ?>>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <label>Enable Spectre (AI Interaction)</label>
                                </div>
                                <div class="form-text">Allow users to interact with the AI assistant using /spectre.</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="form-check">
                                    <label class="toggle-switch">
                                        <input type="checkbox" name="vault_enabled" <?php echo $bot_config['features']['vault_enabled'] ? 'checked' : ''; ?>>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <label>Enable Vault (Content Management)</label>
                                </div>
                                <div class="form-text">Allow users to save and manage content using /vault.</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="form-check">
                                    <label class="toggle-switch">
                                        <input type="checkbox" name="exchange_enabled" <?php echo $bot_config['features']['exchange_enabled'] ? 'checked' : ''; ?>>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <label>Enable Exchange (Community Marketplace)</label>
                                </div>
                                <div class="form-text">Allow users to share and discover content using /the_exchange.</div>
                            </div>
                            
                            <div class="form-group">
                                <div class="form-check">
                                    <label class="toggle-switch">
                                        <input type="checkbox" name="executor_enabled" <?php echo $bot_config['features']['executor_enabled'] ? 'checked' : ''; ?>>
                                        <span class="toggle-slider"></span>
                                    </label>
                                    <label>Enable Executor (Command Execution)</label>
                                </div>
                                <div class="form-text">Allow users to execute saved commands using /commit.</div>
                            </div>
                            
                            <div class="form-actions">
                                <button type="submit" class="btn btn-primary">Save Changes</button>
                                <a href="/dashboard/" class="btn btn-secondary">Cancel</a>
                            </div>
                        </form>
                    </div>
                <?php elseif (!empty($servers)): ?>
                    <div class="alert alert-info">
                        Please select a server to customize your bot.
                    </div>
                <?php else: ?>
                    <div class="alert alert-warning">
                        You don't have any servers where you have administrator permissions. Please add the bot to a server where you have administrator permissions.
                    </div>
                <?php endif; ?>
            </div>
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="/assets/js/main.js"></script>
    <script src="/assets/js/dashboard.js"></script>
</body>
</html>
