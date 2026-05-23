-- Migration: Add GPS/Real-World Coordinates Support
-- This migration adds latitude/longitude to existing tables and creates new location-based tables

-- ===== STEP 1: Migrate existing shop table =====
-- Add GPS columns to shops table
ALTER TABLE shops ADD COLUMN latitude REAL;
ALTER TABLE shops ADD COLUMN longitude REAL;
ALTER TABLE shops ADD COLUMN shop_type TEXT DEFAULT 'general';  -- 'general', 'food', 'service', 'trading'

-- Add index for nearby shop queries
CREATE INDEX IF NOT EXISTS idx_shops_location ON shops(latitude, longitude);

-- ===== STEP 2: Migrate player positions table =====
-- Add GPS columns to player_positions
ALTER TABLE player_positions ADD COLUMN latitude REAL;
ALTER TABLE player_positions ADD COLUMN longitude REAL;

-- Add index for nearby player queries
CREATE INDEX IF NOT EXISTS idx_player_positions_location ON player_positions(latitude, longitude);

-- ===== STEP 3: Create new locations table (named shops with more metadata) =====
CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    location_name TEXT NOT NULL,
    description TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    location_type TEXT DEFAULT 'shop',  -- 'shop', 'bank', 'trading_post', 'guild_hall'
    balance REAL NOT NULL CHECK(balance >= 0),
    max_balance REAL,  -- Optional inventory cap
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(owner_id) REFERENCES users(user_id),
    UNIQUE(latitude, longitude)  -- One location per coordinate (prevent duplicates)
);

CREATE INDEX IF NOT EXISTS idx_locations_owner ON locations(owner_id);
CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(location_type);
CREATE INDEX IF NOT EXISTS idx_locations_coords ON locations(latitude, longitude);

-- ===== STEP 4: Create POIs (Points of Interest) table =====
CREATE TABLE IF NOT EXISTS pois (
    poi_id TEXT PRIMARY KEY,
    poi_name TEXT NOT NULL,
    description TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    poi_type TEXT DEFAULT 'landmark',  -- 'landmark', 'quest_hub', 'resource_spot', 'arena', 'dungeon'
    reward_type TEXT,  -- 'token_bonus', 'item', 'quest', 'experience'
    reward_amount REAL,  -- For token bonuses
    interaction_radius_meters REAL DEFAULT 100.0,  -- How close player must be to interact
    interaction_cooldown_minutes INTEGER DEFAULT 60,  -- How often can player interact
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pois_type ON pois(poi_type);
CREATE INDEX IF NOT EXISTS idx_pois_coords ON pois(latitude, longitude);

-- ===== STEP 5: Create user location tracking table =====
CREATE TABLE IF NOT EXISTS user_location_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy_meters REAL,  -- GPS accuracy from device
    source TEXT DEFAULT 'gps',  -- 'gps', 'manual', 'joystick'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_location_history_user ON user_location_history(user_id, timestamp);

-- ===== STEP 6: Create proximity events log =====
CREATE TABLE IF NOT EXISTS proximity_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    location_id TEXT,  -- NULL if it's a POI
    poi_id TEXT,  -- NULL if it's a location
    event_type TEXT NOT NULL,  -- 'arrived', 'departed', 'interacted', 'completed_quest'
    distance_meters REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(location_id) REFERENCES locations(location_id),
    FOREIGN KEY(poi_id) REFERENCES pois(poi_id)
);

CREATE INDEX IF NOT EXISTS idx_proximity_events_user ON proximity_events(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_proximity_events_location ON proximity_events(location_id, timestamp);

-- ===== STEP 7: Create user preferences table =====
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    location_sharing_enabled BOOLEAN DEFAULT 0,
    gps_enabled BOOLEAN DEFAULT 0,
    preferred_language TEXT DEFAULT 'en',
    notification_enabled BOOLEAN DEFAULT 1,
    radius_preference_meters REAL DEFAULT 1000.0,  -- How far to show locations
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- ===== STEP 8: Add verification indices =====
CREATE VIEW IF NOT EXISTS v_zero_sum_check AS
SELECT 
    (SELECT COALESCE(SUM(balance), 0) FROM users) as total_user_balance,
    (SELECT COALESCE(SUM(balance), 0) FROM locations) as total_location_balance,
    (SELECT COALESCE(SUM(balance), 0) FROM users) + 
    (SELECT COALESCE(SUM(balance), 0) FROM locations) as grand_total;
