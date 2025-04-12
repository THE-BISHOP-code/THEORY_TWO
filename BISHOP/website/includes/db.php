<?php
/**
 * BISHOP Website - Database Functions
 *
 * This file contains functions for database operations.
 */

/**
 * Connect to the database
 *
 * @return PDO Database connection
 */
function db_connect() {
    try {
        $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4';
        $options = [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ];

        return new PDO($dsn, DB_USER, DB_PASS, $options);
    } catch (PDOException $e) {
        // Log error and display friendly message
        error_log('Database connection failed: ' . $e->getMessage());

        // In development, you might want to see the actual error
        if (ini_get('display_errors')) {
            die('Database connection failed: ' . $e->getMessage());
        } else {
            die('Database connection failed. Please try again later.');
        }
    }
}

/**
 * Execute a query and return the result
 *
 * @param string $query SQL query
 * @param array $params Parameters for prepared statement
 * @return array|false Query results or false on failure
 */
function db_query($query, $params = []) {
    global $db;

    try {
        $stmt = $db->prepare($query);
        $stmt->execute($params);
        return $stmt->fetchAll();
    } catch (PDOException $e) {
        error_log('Query failed: ' . $e->getMessage());
        return false;
    }
}

/**
 * Execute a query and return a single row
 *
 * @param string $query SQL query
 * @param array $params Parameters for prepared statement
 * @return array|false Single row or false on failure
 */
function db_query_row($query, $params = []) {
    global $db;

    try {
        $stmt = $db->prepare($query);
        $stmt->execute($params);
        return $stmt->fetch();
    } catch (PDOException $e) {
        error_log('Query failed: ' . $e->getMessage());
        return false;
    }
}

/**
 * Execute a query and return a single value
 *
 * @param string $query SQL query
 * @param array $params Parameters for prepared statement
 * @return mixed|false Single value or false on failure
 */
function db_query_value($query, $params = []) {
    global $db;

    try {
        $stmt = $db->prepare($query);
        $stmt->execute($params);
        return $stmt->fetchColumn();
    } catch (PDOException $e) {
        error_log('Query failed: ' . $e->getMessage());
        return false;
    }
}

/**
 * Execute a query that doesn't return a result (INSERT, UPDATE, DELETE)
 *
 * @param string $query SQL query
 * @param array $params Parameters for prepared statement
 * @return int|false Number of affected rows or false on failure
 */
function db_execute($query, $params = []) {
    global $db;

    try {
        $stmt = $db->prepare($query);
        $stmt->execute($params);
        return $stmt->rowCount();
    } catch (PDOException $e) {
        error_log('Query failed: ' . $e->getMessage());
        return false;
    }
}

/**
 * Get the ID of the last inserted row
 *
 * @return int Last inserted ID
 */
function db_last_insert_id() {
    global $db;
    return (int)$db->lastInsertId();
}

/**
 * Begin a transaction
 *
 * @return bool Success
 */
function db_begin_transaction() {
    global $db;
    return $db->beginTransaction();
}

/**
 * Commit a transaction
 *
 * @return bool Success
 */
function db_commit() {
    global $db;
    return $db->commit();
}

/**
 * Rollback a transaction
 *
 * @return bool Success
 */
function db_rollback() {
    global $db;
    return $db->rollBack();
}

/**
 * Get user by Discord ID
 *
 * @param string $discord_id Discord user ID
 * @return array|false User data or false if not found
 */
function get_user_by_discord_id($discord_id) {
    return db_query_row(
        "SELECT * FROM users WHERE discord_id = ?",
        [$discord_id]
    );
}

/**
 * Create or update user from Discord data
 *
 * @param array $discord_user Discord user data
 * @return int User ID
 */
function save_user_from_discord($discord_user) {
    $user = get_user_by_discord_id($discord_user['id']);

    if ($user) {
        // Update existing user
        db_execute(
            "UPDATE users SET
            username = ?,
            avatar = ?,
            discriminator = ?,
            email = ?,
            updated_at = NOW()
            WHERE discord_id = ?",
            [
                $discord_user['username'],
                $discord_user['avatar'],
                $discord_user['discriminator'] ?? '0',
                $discord_user['email'] ?? null,
                $discord_user['id']
            ]
        );

        return (int)$user['id'];
    } else {
        // Create new user
        db_execute(
            "INSERT INTO users
            (discord_id, username, avatar, discriminator, email, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, NOW(), NOW())",
            [
                $discord_user['id'],
                $discord_user['username'],
                $discord_user['avatar'],
                $discord_user['discriminator'] ?? '0',
                $discord_user['email'] ?? null
            ]
        );

        return (int)db_last_insert_id();
    }
}

/**
 * Get user's servers
 *
 * @param int $user_id User ID
 * @return array User's servers
 */
function get_user_servers($user_id) {
    return db_query(
        "SELECT s.* FROM servers s
        JOIN user_servers us ON s.id = us.server_id
        WHERE us.user_id = ?
        ORDER BY s.name ASC",
        [$user_id]
    );
}

/**
 * Get user's subscription tier
 *
 * @param int $user_id User ID
 * @return string Tier name (Drifter, Seeker, Abysswalker)
 */
function get_user_tier($user_id) {
    $tier = db_query_value(
        "SELECT tier FROM subscriptions
        WHERE user_id = ? AND status = 'active' AND expires_at > NOW()
        ORDER BY tier DESC
        LIMIT 1",
        [$user_id]
    );

    return $tier ?: 'Drifter';
}

/**
 * Check if user has Abysswalker tier
 *
 * @param int $user_id User ID
 * @return bool True if user has Abysswalker tier
 */
function is_abysswalker($user_id) {
    return get_user_tier($user_id) === 'Abysswalker';
}

/**
 * Get user's tokens
 *
 * @param int $user_id User ID
 * @return array User's tokens
 */
function get_user_tokens($user_id) {
    return db_query(
        "SELECT * FROM tokens WHERE user_id = ? ORDER BY created_at DESC",
        [$user_id]
    );
}

/**
 * Get user's bot configurations
 *
 * @param int $user_id User ID
 * @return array User's bot configurations
 */
function get_user_bot_configs($user_id) {
    return db_query(
        "SELECT bc.*, s.name as server_name, s.icon as server_icon
        FROM bot_configs bc
        JOIN servers s ON bc.server_id = s.id
        WHERE bc.user_id = ?
        ORDER BY bc.updated_at DESC",
        [$user_id]
    );
}

/**
 * Save bot configuration
 *
 * @param int $user_id User ID
 * @param int $server_id Server ID
 * @param array $config Configuration data
 * @return bool Success
 */
function save_bot_config($user_id, $server_id, $config) {
    $existing = db_query_row(
        "SELECT id FROM bot_configs WHERE user_id = ? AND server_id = ?",
        [$user_id, $server_id]
    );

    if ($existing) {
        // Update existing config
        return db_execute(
            "UPDATE bot_configs SET
            config = ?,
            updated_at = NOW()
            WHERE id = ?",
            [
                json_encode($config),
                $existing['id']
            ]
        );
    } else {
        // Create new config
        return db_execute(
            "INSERT INTO bot_configs
            (user_id, server_id, config, created_at, updated_at)
            VALUES (?, ?, ?, NOW(), NOW())",
            [
                $user_id,
                $server_id,
                json_encode($config)
            ]
        );
    }
}
