<?php
/**
 * BISHOP Website - Configuration File
 *
 * This file contains all the configuration settings for the website.
 * Production-level implementation with environment variables.
 */

// Load environment variables
require_once __DIR__ . '/env.php';

// Error reporting (disable in production)
$debug = env('DEBUG', false);
ini_set('display_errors', $debug ? 1 : 0);
ini_set('display_startup_errors', $debug ? 1 : 0);
error_reporting($debug ? E_ALL : 0);

// Session configuration
session_start();
ini_set('session.cookie_httponly', 1);
ini_set('session.use_only_cookies', 1);
ini_set('session.cookie_secure', 1);
ini_set('session.gc_maxlifetime', 86400); // 24 hours
session_name('BISHOP_SESSION');

// Database configuration
define('DB_HOST', env('DB_HOST', 'localhost'));
define('DB_NAME', env('DB_NAME', 'bishop_db'));
define('DB_USER', env('DB_USER', 'bishop_user'));
define('DB_PASS', env('DB_PASS', ''));

// Website configuration
define('SITE_NAME', env('SITE_NAME', 'BISHOP AI Assistant'));
define('SITE_URL', env('SITE_URL', 'https://example.com'));
define('SITE_EMAIL', env('SITE_EMAIL', 'contact@example.com'));
define('SITE_DESCRIPTION', env('SITE_DESCRIPTION', 'Advanced AI assistant for Discord with powerful server management tools'));

// Discord OAuth configuration
define('DISCORD_CLIENT_ID', env('DISCORD_CLIENT_ID', ''));
define('DISCORD_CLIENT_SECRET', env('DISCORD_CLIENT_SECRET', ''));
define('DISCORD_REDIRECT_URI', SITE_URL . '/login.php');
define('DISCORD_BOT_TOKEN', env('DISCORD_BOT_TOKEN', ''));
define('DISCORD_API_ENDPOINT', 'https://discord.com/api/v10');

// Bot configuration
define('BOT_CONFIG_PATH', env('BOT_CONFIG_PATH', '../config/config.json'));

// Pricing tiers
define('TIER_DRIFTER_PRICE', env('TIER_DRIFTER_PRICE', '0'));
define('TIER_SEEKER_PRICE', env('TIER_SEEKER_PRICE', '5.99'));
define('TIER_ABYSSWALKER_PRICE', env('TIER_ABYSSWALKER_PRICE', '14.99'));

// Security
define('JWT_SECRET', env('JWT_SECRET', ''));
define('ENCRYPTION_KEY', env('ENCRYPTION_KEY', ''));

// Google Analytics
define('GA_TRACKING_ID', env('GA_TRACKING_ID', ''));

// File Storage
define('STORAGE_DRIVER', env('STORAGE_DRIVER', 'local'));
define('STORAGE_PATH', env('STORAGE_PATH', '../storage'));
define('MAX_UPLOAD_SIZE', env('MAX_UPLOAD_SIZE', 10485760)); // 10MB in bytes

// Paths
define('ROOT_PATH', dirname(__DIR__));
define('INCLUDES_PATH', ROOT_PATH . '/includes');
define('ASSETS_PATH', ROOT_PATH . '/assets');
define('DASHBOARD_PATH', ROOT_PATH . '/dashboard');

// Time zone
date_default_timezone_set('UTC');

// Load functions
require_once INCLUDES_PATH . '/functions.php';
require_once INCLUDES_PATH . '/auth.php';
require_once INCLUDES_PATH . '/db.php';

// Initialize database connection
$db = db_connect();

// Set default headers
header('Content-Type: text/html; charset=utf-8');
header('X-Frame-Options: DENY');
header('X-XSS-Protection: 1; mode=block');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');
header('Permissions-Policy: geolocation=(), microphone=(), camera=()');

// Check if site is in maintenance mode
define('MAINTENANCE_MODE', false);
if (MAINTENANCE_MODE && !is_admin()) {
    include ROOT_PATH . '/maintenance.php';
    exit;
}
