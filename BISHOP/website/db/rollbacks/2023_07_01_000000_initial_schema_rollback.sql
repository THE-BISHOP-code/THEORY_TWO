-- Rollback for migration: initial_schema
-- Created at: 2023-07-01 00:00:00

-- Drop indexes
DROP INDEX IF EXISTS idx_market_comments_user_id ON market_comments;
DROP INDEX IF EXISTS idx_market_comments_listing_id ON market_comments;
DROP INDEX IF EXISTS idx_market_stars_listing_id ON market_stars;
DROP INDEX IF EXISTS idx_market_stars_user_id ON market_stars;
DROP INDEX IF EXISTS idx_market_saves_listing_id ON market_saves;
DROP INDEX IF EXISTS idx_market_saves_user_id ON market_saves;
DROP INDEX IF EXISTS idx_market_listings_uid ON market_listings;
DROP INDEX IF EXISTS idx_market_listings_user_id ON market_listings;
DROP INDEX IF EXISTS idx_logs_action ON logs;
DROP INDEX IF EXISTS idx_logs_server_id ON logs;
DROP INDEX IF EXISTS idx_logs_user_id ON logs;
DROP INDEX IF EXISTS idx_tokens_token ON tokens;
DROP INDEX IF EXISTS idx_tokens_user_id ON tokens;
DROP INDEX IF EXISTS idx_bot_configs_server_id ON bot_configs;
DROP INDEX IF EXISTS idx_bot_configs_user_id ON bot_configs;
DROP INDEX IF EXISTS idx_subscriptions_status ON subscriptions;
DROP INDEX IF EXISTS idx_subscriptions_user_id ON subscriptions;
DROP INDEX IF EXISTS idx_servers_discord_id ON servers;
DROP INDEX IF EXISTS idx_users_discord_id ON users;

-- Drop tables
DROP TABLE IF EXISTS market_comments;
DROP TABLE IF EXISTS market_stars;
DROP TABLE IF EXISTS market_saves;
DROP TABLE IF EXISTS market_listings;
DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS tokens;
DROP TABLE IF EXISTS bot_configs;
DROP TABLE IF EXISTS subscriptions;
DROP TABLE IF EXISTS user_servers;
DROP TABLE IF EXISTS servers;
DROP TABLE IF EXISTS users;
