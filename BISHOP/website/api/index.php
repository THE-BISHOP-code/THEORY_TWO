<?php
/**
 * BISHOP Website - API Endpoint
 * 
 * Handles API requests for the dashboard to interact with the bot configuration.
 */
require_once '../includes/config.php';

// Set content type to JSON
header('Content-Type: application/json');

// CORS headers for development
if (isset($_SERVER['HTTP_ORIGIN'])) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Max-Age: 86400');    // cache for 1 day
}

// Access-Control headers are received during OPTIONS requests
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_METHOD'])) {
        header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
    }
    
    if (isset($_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'])) {
        header("Access-Control-Allow-Headers: {$_SERVER['HTTP_ACCESS_CONTROL_REQUEST_HEADERS']}");
    }
    
    exit(0);
}

// Check if user is logged in
if (!is_logged_in()) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Get user data
$user_id = get_current_user_id();
$tier = get_user_tier($user_id);

// Check if user has Abysswalker tier for certain endpoints
$abysswalker_endpoints = [
    'bot/config',
    'bot/appearance',
    'bot/tokens',
    'bot/commands'
];

// Get request path
$request_uri = $_SERVER['REQUEST_URI'];
$base_path = '/api/';
$path = substr($request_uri, strpos($request_uri, $base_path) + strlen($base_path));
$path = strtok($path, '?');

// Check if endpoint requires Abysswalker tier
if (in_array($path, $abysswalker_endpoints) && $tier !== 'Abysswalker') {
    http_response_code(403);
    echo json_encode(['error' => 'This feature is only available to Abysswalker tier users.']);
    exit;
}

// Get request method
$method = $_SERVER['REQUEST_METHOD'];

// Get request data
$data = [];
if ($method === 'POST' || $method === 'PUT') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON']);
        exit;
    }
}

// API rate limiting
$rate_limit = 60; // requests per minute
$rate_limit_window = 60; // seconds
$rate_limit_key = "rate_limit:{$user_id}:" . floor(time() / $rate_limit_window);

// Check if rate limit is exceeded
$current_requests = isset($_SESSION[$rate_limit_key]) ? $_SESSION[$rate_limit_key] : 0;

if ($current_requests >= $rate_limit) {
    http_response_code(429);
    echo json_encode(['error' => 'Rate limit exceeded. Please try again later.']);
    exit;
}

// Increment rate limit counter
$_SESSION[$rate_limit_key] = $current_requests + 1;

// Log API request
$log_data = [
    'user_id' => $user_id,
    'method' => $method,
    'path' => $path,
    'ip_address' => $_SERVER['REMOTE_ADDR'],
    'created_at' => date('Y-m-d H:i:s')
];

db_execute(
    "INSERT INTO logs (user_id, action, details, ip_address, created_at) 
    VALUES (?, ?, ?, ?, ?)",
    [
        $user_id,
        "API Request: {$method} {$path}",
        json_encode($data),
        $_SERVER['REMOTE_ADDR'],
        date('Y-m-d H:i:s')
    ]
);

// Route API request
switch ($path) {
    case 'user':
        handleUserRequest($method, $data);
        break;
    
    case 'servers':
        handleServersRequest($method, $data);
        break;
    
    case 'bot/config':
        handleBotConfigRequest($method, $data);
        break;
    
    case 'bot/appearance':
        handleBotAppearanceRequest($method, $data);
        break;
    
    case 'bot/tokens':
        handleBotTokensRequest($method, $data);
        break;
    
    case 'bot/commands':
        handleBotCommandsRequest($method, $data);
        break;
    
    case 'stats':
        handleStatsRequest($method, $data);
        break;
    
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
        break;
}

/**
 * Handle user requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleUserRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get user data
            $user = get_current_user();
            $tier = get_user_tier($user_id);
            
            // Remove sensitive data
            unset($user['password']);
            
            // Add tier information
            $user['tier'] = $tier;
            $user['tier_features'] = get_tier_features($tier);
            
            echo json_encode($user);
            break;
        
        case 'PUT':
            // Update user data
            if (!isset($data['username'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Username is required']);
                break;
            }
            
            $result = db_execute(
                "UPDATE users SET username = ?, updated_at = NOW() WHERE id = ?",
                [$data['username'], $user_id]
            );
            
            if ($result) {
                echo json_encode(['success' => true, 'message' => 'User updated successfully']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to update user']);
            }
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle servers requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleServersRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get user's servers
            $servers = get_available_servers($user_id);
            echo json_encode($servers);
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle bot config requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleBotConfigRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get server ID from query string
            $server_id = isset($_GET['server_id']) ? (int)$_GET['server_id'] : null;
            
            if (!$server_id) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID is required']);
                break;
            }
            
            // Get bot configuration
            $config = get_user_bot_config($user_id, $server_id);
            echo json_encode($config);
            break;
        
        case 'PUT':
            // Update bot configuration
            if (!isset($data['server_id'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID is required']);
                break;
            }
            
            $server_id = (int)$data['server_id'];
            unset($data['server_id']);
            
            $result = save_bot_config($user_id, $server_id, $data);
            
            if ($result) {
                echo json_encode(['success' => true, 'message' => 'Bot configuration updated successfully']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to update bot configuration']);
            }
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle bot appearance requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleBotAppearanceRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get server ID from query string
            $server_id = isset($_GET['server_id']) ? (int)$_GET['server_id'] : null;
            
            if (!$server_id) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID is required']);
                break;
            }
            
            // Get bot configuration
            $config = get_user_bot_config($user_id, $server_id);
            
            // Extract appearance data
            $appearance = [
                'bot_name' => $config['bot_name'],
                'bot_avatar' => $config['bot_avatar'],
                'bot_status' => $config['bot_status'],
                'bot_activity' => $config['bot_activity'],
                'bot_activity_text' => $config['bot_activity_text'],
                'bot_description' => $config['bot_description'],
                'embed_color' => $config['embed_color']
            ];
            
            echo json_encode($appearance);
            break;
        
        case 'PUT':
            // Update bot appearance
            if (!isset($data['server_id'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID is required']);
                break;
            }
            
            $server_id = (int)$data['server_id'];
            unset($data['server_id']);
            
            // Get current config
            $config = get_user_bot_config($user_id, $server_id);
            
            // Update appearance data
            $config['bot_name'] = $data['bot_name'] ?? $config['bot_name'];
            $config['bot_status'] = $data['bot_status'] ?? $config['bot_status'];
            $config['bot_activity'] = $data['bot_activity'] ?? $config['bot_activity'];
            $config['bot_activity_text'] = $data['bot_activity_text'] ?? $config['bot_activity_text'];
            $config['bot_description'] = $data['bot_description'] ?? $config['bot_description'];
            $config['embed_color'] = $data['embed_color'] ?? $config['embed_color'];
            
            $result = save_bot_config($user_id, $server_id, $config);
            
            if ($result) {
                echo json_encode(['success' => true, 'message' => 'Bot appearance updated successfully']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to update bot appearance']);
            }
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle bot tokens requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleBotTokensRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get user's tokens
            $tokens = get_user_tokens($user_id);
            
            // Mask token values
            foreach ($tokens as &$token) {
                $token['token'] = substr($token['token'], 0, 8) . '...' . substr($token['token'], -8);
            }
            
            echo json_encode($tokens);
            break;
        
        case 'POST':
            // Create new token
            if (!isset($data['name']) || !isset($data['type'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Name and type are required']);
                break;
            }
            
            // Generate token
            $token = bin2hex(random_bytes(32));
            
            // Save token
            $result = db_execute(
                "INSERT INTO tokens (user_id, name, token, type, created_at) 
                VALUES (?, ?, ?, ?, NOW())",
                [
                    $user_id,
                    $data['name'],
                    $token,
                    $data['type']
                ]
            );
            
            if ($result) {
                echo json_encode([
                    'success' => true,
                    'message' => 'Token created successfully',
                    'token' => $token
                ]);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to create token']);
            }
            break;
        
        case 'DELETE':
            // Delete token
            if (!isset($data['token_id'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Token ID is required']);
                break;
            }
            
            $result = db_execute(
                "DELETE FROM tokens WHERE id = ? AND user_id = ?",
                [$data['token_id'], $user_id]
            );
            
            if ($result) {
                echo json_encode(['success' => true, 'message' => 'Token deleted successfully']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to delete token']);
            }
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle bot commands requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleBotCommandsRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get server ID from query string
            $server_id = isset($_GET['server_id']) ? (int)$_GET['server_id'] : null;
            
            if (!$server_id) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID is required']);
                break;
            }
            
            // Get bot configuration
            $config = get_user_bot_config($user_id, $server_id);
            
            // Extract commands data
            $commands = $config['commands'] ?? [];
            
            echo json_encode($commands);
            break;
        
        case 'PUT':
            // Update bot commands
            if (!isset($data['server_id']) || !isset($data['commands'])) {
                http_response_code(400);
                echo json_encode(['error' => 'Server ID and commands are required']);
                break;
            }
            
            $server_id = (int)$data['server_id'];
            
            // Get current config
            $config = get_user_bot_config($user_id, $server_id);
            
            // Update commands data
            $config['commands'] = $data['commands'];
            
            $result = save_bot_config($user_id, $server_id, $config);
            
            if ($result) {
                echo json_encode(['success' => true, 'message' => 'Bot commands updated successfully']);
            } else {
                http_response_code(500);
                echo json_encode(['error' => 'Failed to update bot commands']);
            }
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}

/**
 * Handle stats requests
 * 
 * @param string $method Request method
 * @param array $data Request data
 */
function handleStatsRequest($method, $data) {
    $user_id = get_current_user_id();
    
    switch ($method) {
        case 'GET':
            // Get server ID from query string
            $server_id = isset($_GET['server_id']) ? (int)$_GET['server_id'] : null;
            
            // Get stats data
            $stats = [
                'user' => [
                    'servers' => count(get_available_servers($user_id)),
                    'tokens' => count(get_user_tokens($user_id)),
                    'tier' => get_user_tier($user_id)
                ]
            ];
            
            // Add server-specific stats if server ID is provided
            if ($server_id) {
                // Get server data
                $server = db_query_row(
                    "SELECT * FROM servers WHERE id = ?",
                    [$server_id]
                );
                
                if ($server) {
                    // Get bot configuration
                    $config = get_user_bot_config($user_id, $server_id);
                    
                    // Add server stats
                    $stats['server'] = [
                        'name' => $server['name'],
                        'members' => rand(50, 500), // Placeholder for demo
                        'channels' => rand(5, 20), // Placeholder for demo
                        'commands' => count($config['commands'] ?? []),
                        'features_enabled' => array_sum($config['features'] ?? [])
                    ];
                }
            }
            
            echo json_encode($stats);
            break;
        
        default:
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            break;
    }
}
