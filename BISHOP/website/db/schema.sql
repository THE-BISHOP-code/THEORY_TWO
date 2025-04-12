-- BISHOP Website Database Schema

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discord_id VARCHAR(32) NOT NULL UNIQUE,
    username VARCHAR(128) NOT NULL,
    avatar VARCHAR(128),
    discriminator VARCHAR(4),
    email VARCHAR(255),
    is_admin TINYINT(1) DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Servers table
CREATE TABLE servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discord_id VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    icon VARCHAR(128),
    owner TINYINT(1) DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- User-Server relationship
CREATE TABLE user_servers (
    user_id INT NOT NULL,
    server_id INT NOT NULL,
    permissions VARCHAR(32) NOT NULL,
    PRIMARY KEY (user_id, server_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- Subscriptions table
CREATE TABLE subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    tier ENUM('Drifter', 'Seeker', 'Abysswalker') NOT NULL DEFAULT 'Drifter',
    status ENUM('active', 'canceled', 'expired') NOT NULL DEFAULT 'active',
    payment_id VARCHAR(128),
    starts_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Bot configurations
CREATE TABLE bot_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    server_id INT NOT NULL,
    config TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY (user_id, server_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

-- API tokens
CREATE TABLE tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(128) NOT NULL,
    token VARCHAR(128) NOT NULL UNIQUE,
    type ENUM('read', 'write', 'admin') NOT NULL DEFAULT 'read',
    last_used_at DATETIME,
    expires_at DATETIME,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Logs
CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    server_id INT,
    action VARCHAR(128) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE SET NULL
);

-- Market listings
CREATE TABLE market_listings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(32) NOT NULL UNIQUE,
    user_id INT NOT NULL,
    title VARCHAR(128) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    saves INT DEFAULT 0,
    stars INT DEFAULT 0,
    is_public TINYINT(1) DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Market saves
CREATE TABLE market_saves (
    user_id INT NOT NULL,
    listing_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (user_id, listing_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (listing_id) REFERENCES market_listings(id) ON DELETE CASCADE
);

-- Market stars
CREATE TABLE market_stars (
    user_id INT NOT NULL,
    listing_id INT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (user_id, listing_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (listing_id) REFERENCES market_listings(id) ON DELETE CASCADE
);

-- Market comments
CREATE TABLE market_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (listing_id) REFERENCES market_listings(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_users_discord_id ON users(discord_id);
CREATE INDEX idx_servers_discord_id ON servers(discord_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_bot_configs_user_id ON bot_configs(user_id);
CREATE INDEX idx_bot_configs_server_id ON bot_configs(server_id);
CREATE INDEX idx_tokens_user_id ON tokens(user_id);
CREATE INDEX idx_tokens_token ON tokens(token);
CREATE INDEX idx_logs_user_id ON logs(user_id);
CREATE INDEX idx_logs_server_id ON logs(server_id);
CREATE INDEX idx_logs_action ON logs(action);
CREATE INDEX idx_market_listings_user_id ON market_listings(user_id);
CREATE INDEX idx_market_listings_uid ON market_listings(uid);
CREATE INDEX idx_market_saves_user_id ON market_saves(user_id);
CREATE INDEX idx_market_saves_listing_id ON market_saves(listing_id);
CREATE INDEX idx_market_stars_user_id ON market_stars(user_id);
CREATE INDEX idx_market_stars_listing_id ON market_stars(listing_id);
CREATE INDEX idx_market_comments_listing_id ON market_comments(listing_id);
CREATE INDEX idx_market_comments_user_id ON market_comments(user_id);
