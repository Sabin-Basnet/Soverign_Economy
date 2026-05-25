-- Core Users Ledger (Zero-Sum Invariant Protection)
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    balance REAL NOT NULL CHECK(balance >= 0),
    user_type TEXT DEFAULT 'player',  -- 'player', 'merchant', 'government'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- P2P & Commerce Transactions (Immutable Audit Trail)
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    tx_type TEXT DEFAULT 'transfer',  -- 'transfer', 'purchase', 'tax'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(user_id),
    FOREIGN KEY(receiver_id) REFERENCES users(user_id)
);

-- Permanent Commercial Anchor Points (Shops)
CREATE TABLE IF NOT EXISTS shops (
    shop_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    shop_name TEXT NOT NULL,
    location_x REAL NOT NULL,
    location_y REAL NOT NULL,
    balance REAL NOT NULL CHECK(balance >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(merchant_id) REFERENCES users(user_id)
);

-- Logistics Escrow (Multi-State Transaction Locking)
CREATE TABLE IF NOT EXISTS escrow (
    escrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    courier_id TEXT,
    shop_id TEXT,
    amount REAL NOT NULL CHECK(amount > 0),
    tax_amount REAL NOT NULL CHECK(tax_amount >= 0),
    state TEXT DEFAULT 'locked',  -- 'locked', 'in_transit', 'completed', 'cancelled'
    delivery_threshold REAL DEFAULT 1.0,  -- Distance threshold for delivery
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY(buyer_id) REFERENCES users(user_id),
    FOREIGN KEY(seller_id) REFERENCES users(user_id),
    FOREIGN KEY(courier_id) REFERENCES users(user_id),
    FOREIGN KEY(shop_id) REFERENCES shops(shop_id)
);

-- Real-Time Player Spatial Coordinates
-- CREATE TABLE IF NOT EXISTS player_positions (
--     position_id INTEGER PRIMARY KEY AUTOINCREMENT,
--     user_id TEXT NOT NULL,
--     location_x REAL NOT NULL,
--     location_y REAL NOT NULL,
--     bearing REAL DEFAULT 0.0,
--     updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY(user_id) REFERENCES users(user_id),
--     UNIQUE(user_id)
-- );

-- Treasury Audit Log (Fiscal Policy Execution)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,  -- 'velocity_tax', 'escrow_completion', 'manual_transfer'
    sender_id TEXT,
    receiver_id TEXT,
    amount REAL,
    metadata TEXT,  -- JSON string for additional context
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Snapshot (Periodic Aggregation)
CREATE TABLE IF NOT EXISTS analytics_snapshot (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_circulation REAL NOT NULL,
    velocity_of_money REAL,
    gini_coefficient REAL,
    treasury_balance REAL,
    num_active_players INTEGER,
    num_transactions INTEGER,
    captured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- by myself
CREATE TABLE IF NOT EXISTS locations (
    location_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    location_name TEXT NOT NULL,
    description TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    location_type TEXT DEFAULT 'shop',  -- 'shop', 'bank', 'trading_post', 'guild_hall'
    balance REAL NOT NULL CHECK(balance >= 0)
);

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
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS user_location_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accuracy_meters REAL,  -- GPS accuracy from device
    source TEXT DEFAULT 'gps',  -- 'gps', 'manual', 'joystick'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_positions (
    user_id TEXT PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);