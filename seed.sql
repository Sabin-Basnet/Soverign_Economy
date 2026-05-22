-- Genesis Block: Fixed 1,000,000 Token Distribution
INSERT OR IGNORE INTO users (user_id, username, balance, user_type) VALUES
('GOV_01', 'State_Treasury', 800000.00, 'government'),
('MERCH_01', 'Local_Shop', 150000.00, 'merchant'),
('BUYER_01', 'Player_One', 30000.00, 'player'),
('BUYER_02', 'Player_Two', 15000.00, 'player'),
('COURIER_01', 'Delivery_Node', 5000.00, 'player');

-- Permanent Shop Anchors (Commercial Endpoints)
INSERT OR IGNORE INTO shops (shop_id, merchant_id, shop_name, location_x, location_y, balance) VALUES
('SHOP_01', 'MERCH_01', 'Central_Market', 100.0, 100.0, 150000.00);

-- Initial Player Positions (Spatial Seed)
INSERT OR IGNORE INTO player_positions (user_id, location_x, location_y, bearing) VALUES
('BUYER_01', 50.0, 50.0, 0.0),
('BUYER_02', 75.0, 75.0, 90.0),
('COURIER_01', 100.0, 100.0, 180.0),
('MERCH_01', 100.0, 100.0, 0.0);