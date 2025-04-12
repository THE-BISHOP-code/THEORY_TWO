<?php
/**
 * BISHOP Website - General Functions
 * 
 * This file contains general utility functions for the website.
 */

/**
 * Display a flash message
 * 
 * @param string $type Message type (success, error, info, warning)
 * @param string $message Message text
 * @return void
 */
function flash_message($type, $message) {
    $_SESSION['flash'] = [
        'type' => $type,
        'message' => $message
    ];
}

/**
 * Get and clear flash message
 * 
 * @return array|null Flash message or null if none
 */
function get_flash_message() {
    if (isset($_SESSION['flash'])) {
        $flash = $_SESSION['flash'];
        unset($_SESSION['flash']);
        return $flash;
    }
    
    return null;
}

/**
 * Sanitize output for HTML display
 * 
 * @param string $text Text to sanitize
 * @return string Sanitized text
 */
function h($text) {
    return htmlspecialchars($text, ENT_QUOTES, 'UTF-8');
}

/**
 * Get Discord avatar URL
 * 
 * @param string $user_id Discord user ID
 * @param string $avatar Avatar hash
 * @param int $size Avatar size (default: 128)
 * @return string Avatar URL
 */
function get_discord_avatar_url($user_id, $avatar, $size = 128) {
    if (!$avatar) {
        // Default avatar
        $discriminator = isset($_SESSION['discriminator']) ? $_SESSION['discriminator'] : '0';
        $default_avatar = $discriminator % 5;
        return "https://cdn.discordapp.com/embed/avatars/{$default_avatar}.png?size={$size}";
    }
    
    // User avatar
    $extension = strpos($avatar, 'a_') === 0 ? 'gif' : 'png';
    return "https://cdn.discordapp.com/avatars/{$user_id}/{$avatar}.{$extension}?size={$size}";
}

/**
 * Get Discord server icon URL
 * 
 * @param string $server_id Discord server ID
 * @param string $icon Icon hash
 * @param int $size Icon size (default: 128)
 * @return string Icon URL
 */
function get_discord_server_icon_url($server_id, $icon, $size = 128) {
    if (!$icon) {
        // Default icon (Discord doesn't provide one, so use a placeholder)
        return "/assets/img/default-server-icon.png";
    }
    
    // Server icon
    $extension = strpos($icon, 'a_') === 0 ? 'gif' : 'png';
    return "https://cdn.discordapp.com/icons/{$server_id}/{$icon}.{$extension}?size={$size}";
}

/**
 * Format date
 * 
 * @param string $date Date string
 * @param bool $include_time Whether to include time
 * @return string Formatted date
 */
function format_date($date, $include_time = false) {
    $format = $include_time ? 'M j, Y g:i A' : 'M j, Y';
    return date($format, strtotime($date));
}

/**
 * Get bot configuration from JSON file
 * 
 * @return array Bot configuration
 */
function get_bot_config() {
    $config_path = BOT_CONFIG_PATH;
    
    if (!file_exists($config_path)) {
        return [];
    }
    
    $config_json = file_get_contents($config_path);
    return json_decode($config_json, true);
}

/**
 * Save bot configuration to JSON file
 * 
 * @param array $config Bot configuration
 * @return bool Success
 */
function save_bot_config($config) {
    $config_path = BOT_CONFIG_PATH;
    
    // Create backup
    if (file_exists($config_path)) {
        $backup_path = $config_path . '.bak';
        copy($config_path, $backup_path);
    }
    
    // Save new config
    $config_json = json_encode($config, JSON_PRETTY_PRINT);
    return file_put_contents($config_path, $config_json) !== false;
}

/**
 * Get user's bot configuration
 * 
 * @param int $user_id User ID
 * @param int $server_id Server ID
 * @return array Bot configuration
 */
function get_user_bot_config($user_id, $server_id) {
    $config = db_query_row(
        "SELECT config FROM bot_configs WHERE user_id = ? AND server_id = ?",
        [$user_id, $server_id]
    );
    
    if ($config) {
        return json_decode($config['config'], true);
    }
    
    // Return default config
    return [
        'bot_name' => 'BISHOP',
        'bot_avatar' => '',
        'bot_status' => 'online',
        'bot_activity' => 'listening',
        'bot_activity_text' => '/spectre',
        'bot_description' => 'Advanced AI assistant for Discord',
        'embed_color' => '#3498db',
        'features' => [
            'spectre_enabled' => true,
            'vault_enabled' => true,
            'exchange_enabled' => true,
            'executor_enabled' => true
        ]
    ];
}

/**
 * Get available servers for user
 * 
 * @param int $user_id User ID
 * @return array Available servers
 */
function get_available_servers($user_id) {
    // Get user's tier
    $tier = get_user_tier($user_id);
    
    // Get servers where user has admin permissions
    $servers = db_query(
        "SELECT s.*, us.permissions 
        FROM servers s
        JOIN user_servers us ON s.id = us.server_id
        WHERE us.user_id = ? AND (us.permissions & 8) = 8
        ORDER BY s.name ASC",
        [$user_id]
    );
    
    // Filter based on tier
    $max_servers = 1; // Default for Drifter
    
    if ($tier === 'Seeker') {
        $max_servers = 1;
    } elseif ($tier === 'Abysswalker') {
        $max_servers = 2;
    }
    
    // Get servers that already have bot configs
    $configured_servers = db_query(
        "SELECT server_id FROM bot_configs WHERE user_id = ?",
        [$user_id]
    );
    
    $configured_server_ids = array_column($configured_servers, 'server_id');
    
    // Mark servers as configured and available
    foreach ($servers as &$server) {
        $server['configured'] = in_array($server['id'], $configured_server_ids);
        $server['available'] = count($configured_server_ids) < $max_servers || $server['configured'];
    }
    
    return $servers;
}

/**
 * Check if string starts with substring
 * 
 * @param string $haystack String to search in
 * @param string $needle Substring to search for
 * @return bool True if string starts with substring
 */
function starts_with($haystack, $needle) {
    return substr($haystack, 0, strlen($needle)) === $needle;
}

/**
 * Check if string ends with substring
 * 
 * @param string $haystack String to search in
 * @param string $needle Substring to search for
 * @return bool True if string ends with substring
 */
function ends_with($haystack, $needle) {
    return substr($haystack, -strlen($needle)) === $needle;
}

/**
 * Generate a random string
 * 
 * @param int $length String length
 * @return string Random string
 */
function random_string($length = 32) {
    $chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $chars_length = strlen($chars);
    $random_string = '';
    
    for ($i = 0; $i < $length; $i++) {
        $random_string .= $chars[random_int(0, $chars_length - 1)];
    }
    
    return $random_string;
}

/**
 * Get current page URL
 * 
 * @return string Current page URL
 */
function current_url() {
    $protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
    return $protocol . '://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'];
}

/**
 * Get base URL
 * 
 * @return string Base URL
 */
function base_url() {
    $protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
    return $protocol . '://' . $_SERVER['HTTP_HOST'];
}

/**
 * Redirect to URL
 * 
 * @param string $url URL to redirect to
 * @return void
 */
function redirect($url) {
    header("Location: $url");
    exit;
}

/**
 * Get active page for navigation
 * 
 * @return string Active page
 */
function get_active_page() {
    $uri = $_SERVER['REQUEST_URI'];
    
    if ($uri === '/' || $uri === '/index.php') {
        return 'home';
    }
    
    if (starts_with($uri, '/about')) {
        return 'about';
    }
    
    if (starts_with($uri, '/pricing')) {
        return 'pricing';
    }
    
    if (starts_with($uri, '/contact')) {
        return 'contact';
    }
    
    if (starts_with($uri, '/dashboard')) {
        return 'dashboard';
    }
    
    return '';
}

/**
 * Check if page is active
 * 
 * @param string $page Page to check
 * @return bool True if page is active
 */
function is_active($page) {
    return get_active_page() === $page;
}

/**
 * Get active class for navigation
 * 
 * @param string $page Page to check
 * @return string Active class or empty string
 */
function active_class($page) {
    return is_active($page) ? 'active' : '';
}

/**
 * Format file size
 * 
 * @param int $bytes File size in bytes
 * @return string Formatted file size
 */
function format_file_size($bytes) {
    $units = ['B', 'KB', 'MB', 'GB', 'TB'];
    
    $bytes = max($bytes, 0);
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
    $pow = min($pow, count($units) - 1);
    
    $bytes /= pow(1024, $pow);
    
    return round($bytes, 2) . ' ' . $units[$pow];
}

/**
 * Get tier features
 * 
 * @param string $tier Tier name (Drifter, Seeker, Abysswalker)
 * @return array Tier features
 */
function get_tier_features($tier) {
    $features = [
        'Drifter' => [
            'replies' => 3,
            'saves' => 5,
            'cooldown' => '10 minutes',
            'custom_bot' => false,
            'premium_commands' => false,
            'market_access' => 'read-only',
            'support' => 'community'
        ],
        'Seeker' => [
            'replies' => 5,
            'saves' => 12,
            'cooldown' => '2 minutes',
            'custom_bot' => false,
            'premium_commands' => true,
            'market_access' => 'full',
            'support' => 'priority'
        ],
        'Abysswalker' => [
            'replies' => 7,
            'saves' => 30,
            'cooldown' => 'none',
            'custom_bot' => true,
            'premium_commands' => true,
            'market_access' => 'full',
            'support' => 'dedicated'
        ]
    ];
    
    return $features[$tier] ?? $features['Drifter'];
}
