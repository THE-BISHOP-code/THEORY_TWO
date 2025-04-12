-- Seed: test_data
-- Created at: 2023-07-01 00:00:00

-- Insert test admin user
INSERT INTO users (discord_id, username, avatar, discriminator, email, is_admin, created_at, updated_at)
VALUES ('123456789012345678', 'Admin User', 'abcdef1234567890', '0001', 'admin@example.com', 1, NOW(), NOW());

-- Insert test regular user
INSERT INTO users (discord_id, username, avatar, discriminator, email, is_admin, created_at, updated_at)
VALUES ('876543210987654321', 'Test User', '0987654321fedcba', '0002', 'user@example.com', 0, NOW(), NOW());

-- Insert test servers
INSERT INTO servers (discord_id, name, icon, owner, created_at, updated_at)
VALUES 
('111111111111111111', 'Test Server 1', 'server_icon_1', 1, NOW(), NOW()),
('222222222222222222', 'Test Server 2', 'server_icon_2', 0, NOW(), NOW());

-- Insert user-server relationships
INSERT INTO user_servers (user_id, server_id, permissions)
VALUES 
(1, 1, '8'), -- Admin user has admin permissions on Server 1
(1, 2, '8'), -- Admin user has admin permissions on Server 2
(2, 1, '0'); -- Regular user has no special permissions on Server 1

-- Insert subscriptions
INSERT INTO subscriptions (user_id, tier, status, payment_id, starts_at, expires_at, created_at, updated_at)
VALUES 
(1, 'Abysswalker', 'active', 'payment_123', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), NOW(), NOW()),
(2, 'Seeker', 'active', 'payment_456', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), NOW(), NOW());

-- Insert bot configurations
INSERT INTO bot_configs (user_id, server_id, config, created_at, updated_at)
VALUES 
(1, 1, '{"bot_name":"BISHOP","bot_avatar":"","bot_status":"online","bot_activity":"listening","bot_activity_text":"/spectre","bot_description":"Advanced AI assistant for Discord","embed_color":"#3498db","features":{"spectre_enabled":true,"vault_enabled":true,"exchange_enabled":true,"executor_enabled":true}}', NOW(), NOW());

-- Insert API tokens
INSERT INTO tokens (user_id, name, token, type, last_used_at, created_at)
VALUES 
(1, 'Test Token', 'abcdef1234567890abcdef1234567890', 'read', NOW(), NOW());

-- Insert market listings
INSERT INTO market_listings (uid, user_id, title, description, content, saves, stars, is_public, created_at, updated_at)
VALUES 
('abc123', 1, 'Test Listing', 'This is a test listing', 'Test content for the listing', 5, 10, 1, NOW(), NOW());

-- Insert market saves
INSERT INTO market_saves (user_id, listing_id, created_at)
VALUES 
(2, 1, NOW());

-- Insert market stars
INSERT INTO market_stars (user_id, listing_id, created_at)
VALUES 
(2, 1, NOW());

-- Insert market comments
INSERT INTO market_comments (listing_id, user_id, content, created_at, updated_at)
VALUES 
(1, 2, 'This is a test comment', NOW(), NOW());
