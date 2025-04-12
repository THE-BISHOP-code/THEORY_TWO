<?php
/**
 * BISHOP Website - Authentication Functions
 *
 * This file contains functions for user authentication with Discord OAuth.
 */

/**
 * Get Discord OAuth URL
 *
 * @return string Discord OAuth URL
 */
function get_discord_oauth_url() {
    $params = [
        'client_id' => DISCORD_CLIENT_ID,
        'redirect_uri' => DISCORD_REDIRECT_URI,
        'response_type' => 'code',
        'scope' => 'identify email guilds'
    ];

    return 'https://discord.com/api/oauth2/authorize?' . http_build_query($params);
}

/**
 * Exchange authorization code for access token
 *
 * @param string $code Authorization code from Discord
 * @return array|false Access token data or false on failure
 */
function exchange_code($code) {
    $data = [
        'client_id' => DISCORD_CLIENT_ID,
        'client_secret' => DISCORD_CLIENT_SECRET,
        'grant_type' => 'authorization_code',
        'code' => $code,
        'redirect_uri' => DISCORD_REDIRECT_URI
    ];

    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($data)
        ]
    ];

    $context = stream_context_create($options);
    $result = file_get_contents(DISCORD_API_ENDPOINT . '/oauth2/token', false, $context);

    if ($result === false) {
        return false;
    }

    return json_decode($result, true);
}

/**
 * Get Discord user data using access token
 *
 * @param string $access_token Discord access token
 * @return array|false User data or false on failure
 */
function get_discord_user($access_token) {
    $options = [
        'http' => [
            'header' => "Authorization: Bearer $access_token\r\n",
            'method' => 'GET'
        ]
    ];

    $context = stream_context_create($options);
    $result = file_get_contents(DISCORD_API_ENDPOINT . '/users/@me', false, $context);

    if ($result === false) {
        return false;
    }

    return json_decode($result, true);
}

/**
 * Get Discord user's guilds using access token
 *
 * @param string $access_token Discord access token
 * @return array|false User's guilds or false on failure
 */
function get_discord_guilds($access_token) {
    $options = [
        'http' => [
            'header' => "Authorization: Bearer $access_token\r\n",
            'method' => 'GET'
        ]
    ];

    $context = stream_context_create($options);
    $result = file_get_contents(DISCORD_API_ENDPOINT . '/users/@me/guilds', false, $context);

    if ($result === false) {
        return false;
    }

    return json_decode($result, true);
}

/**
 * Process Discord login
 *
 * @param string $code Authorization code from Discord
 * @return bool Success
 */
function process_discord_login($code) {
    // Exchange code for token
    $token_data = exchange_code($code);
    if (!$token_data || !isset($token_data['access_token'])) {
        return false;
    }

    // Get user data
    $discord_user = get_discord_user($token_data['access_token']);
    if (!$discord_user || !isset($discord_user['id'])) {
        return false;
    }

    // Get user's guilds
    $discord_guilds = get_discord_guilds($token_data['access_token']);

    // Save user to database
    $user_id = save_user_from_discord($discord_user);

    // Save user's guilds
    if ($discord_guilds) {
        save_user_guilds($user_id, $discord_guilds);
    }

    // Set session data
    $_SESSION['user_id'] = $user_id;
    $_SESSION['discord_id'] = $discord_user['id'];
    $_SESSION['username'] = $discord_user['username'];
    $_SESSION['avatar'] = $discord_user['avatar'];
    $_SESSION['access_token'] = $token_data['access_token'];
    $_SESSION['refresh_token'] = $token_data['refresh_token'];
    $_SESSION['expires_at'] = time() + $token_data['expires_in'];

    return true;
}

/**
 * Save user's guilds to database
 *
 * @param int $user_id User ID
 * @param array $guilds Discord guilds data
 * @return bool Success
 */
function save_user_guilds($user_id, $guilds) {
    global $db;

    try {
        // Start transaction
        db_begin_transaction();

        // Remove existing user-server associations
        db_execute("DELETE FROM user_servers WHERE user_id = ?", [$user_id]);

        // Insert servers and user-server associations
        foreach ($guilds as $guild) {
            // Check if server exists
            $server = db_query_row(
                "SELECT id FROM servers WHERE discord_id = ?",
                [$guild['id']]
            );

            if ($server) {
                $server_id = $server['id'];

                // Update server data
                db_execute(
                    "UPDATE servers SET
                    name = ?,
                    icon = ?,
                    owner = ?,
                    updated_at = NOW()
                    WHERE id = ?",
                    [
                        $guild['name'],
                        $guild['icon'],
                        $guild['owner'] ? 1 : 0,
                        $server_id
                    ]
                );
            } else {
                // Insert new server
                db_execute(
                    "INSERT INTO servers
                    (discord_id, name, icon, owner, created_at, updated_at)
                    VALUES (?, ?, ?, ?, NOW(), NOW())",
                    [
                        $guild['id'],
                        $guild['name'],
                        $guild['icon'],
                        $guild['owner'] ? 1 : 0
                    ]
                );

                $server_id = db_last_insert_id();
            }

            // Insert user-server association
            db_execute(
                "INSERT INTO user_servers
                (user_id, server_id, permissions)
                VALUES (?, ?, ?)",
                [
                    $user_id,
                    $server_id,
                    $guild['permissions']
                ]
            );
        }

        // Commit transaction
        db_commit();
        return true;
    } catch (Exception $e) {
        // Rollback transaction on error
        db_rollback();
        error_log('Failed to save user guilds: ' . $e->getMessage());
        return false;
    }
}

/**
 * Check if user is logged in
 *
 * @return bool True if user is logged in
 */
function is_logged_in() {
    return isset($_SESSION['user_id']);
}

/**
 * Get current user ID
 *
 * @return int|false User ID or false if not logged in
 */
function get_current_user_id() {
    return is_logged_in() ? $_SESSION['user_id'] : false;
}

/**
 * Get current user data
 *
 * @return array|false User data or false if not logged in
 */
function get_current_user() {
    if (!is_logged_in()) {
        return false;
    }

    return db_query_row(
        "SELECT * FROM users WHERE id = ?",
        [$_SESSION['user_id']]
    );
}

/**
 * Check if access token needs refresh
 *
 * @return bool True if token needs refresh
 */
function token_needs_refresh() {
    return isset($_SESSION['expires_at']) && $_SESSION['expires_at'] < time() + 300; // Refresh if less than 5 minutes left
}

/**
 * Refresh access token
 *
 * @return bool Success
 */
function refresh_token() {
    if (!isset($_SESSION['refresh_token'])) {
        return false;
    }

    $data = [
        'client_id' => DISCORD_CLIENT_ID,
        'client_secret' => DISCORD_CLIENT_SECRET,
        'grant_type' => 'refresh_token',
        'refresh_token' => $_SESSION['refresh_token']
    ];

    $options = [
        'http' => [
            'header' => "Content-type: application/x-www-form-urlencoded\r\n",
            'method' => 'POST',
            'content' => http_build_query($data)
        ]
    ];

    $context = stream_context_create($options);
    $result = file_get_contents(DISCORD_API_ENDPOINT . '/oauth2/token', false, $context);

    if ($result === false) {
        return false;
    }

    $token_data = json_decode($result, true);

    if (!isset($token_data['access_token'])) {
        return false;
    }

    // Update session data
    $_SESSION['access_token'] = $token_data['access_token'];
    $_SESSION['refresh_token'] = $token_data['refresh_token'];
    $_SESSION['expires_at'] = time() + $token_data['expires_in'];

    return true;
}

/**
 * Logout user
 *
 * @return void
 */
function logout() {
    // Clear session data
    $_SESSION = [];

    // Destroy session
    if (ini_get("session.use_cookies")) {
        $params = session_get_cookie_params();
        setcookie(
            session_name(),
            '',
            time() - 42000,
            $params["path"],
            $params["domain"],
            $params["secure"],
            $params["httponly"]
        );
    }

    session_destroy();
}

/**
 * Require login
 *
 * @param string $redirect_url URL to redirect to after login
 * @return void
 */
function require_login($redirect_url = null) {
    if (!is_logged_in()) {
        // Set redirect URL in session
        if ($redirect_url) {
            $_SESSION['redirect_after_login'] = $redirect_url;
        } else {
            $_SESSION['redirect_after_login'] = $_SERVER['REQUEST_URI'];
        }

        // Redirect to login page
        header('Location: /login.php');
        exit;
    }

    // Check if token needs refresh
    if (token_needs_refresh()) {
        refresh_token();
    }
}

/**
 * Check if user is admin
 *
 * @return bool True if user is admin
 */
function is_admin() {
    if (!is_logged_in()) {
        return false;
    }

    $user = get_current_user();
    return $user && $user['is_admin'] == 1;
}

/**
 * Require admin
 *
 * @return void
 */
function require_admin() {
    require_login();

    if (!is_admin()) {
        // Redirect to dashboard with error message
        $_SESSION['error'] = 'You do not have permission to access that page.';
        header('Location: /dashboard/');
        exit;
    }
}

/**
 * Check if user has Abysswalker tier
 *
 * @return bool True if user has Abysswalker tier
 */
function require_abysswalker() {
    require_login();

    if (!is_abysswalker(get_current_user_id())) {
        // Redirect to dashboard with error message
        $_SESSION['error'] = 'This feature is only available to Abysswalker tier users.';
        header('Location: /dashboard/');
        exit;
    }

    return true;
}
