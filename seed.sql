-- Genesis Block: Fixed 1,000,000 Token Distribution
INSERT OR IGNORE INTO users (user_id, username, balance, user_type) VALUES
('GOV_01', 'State_Treasury', 800000.00, 'government'),
('MERCH_01', 'Local_Shop', 150000.00, 'merchant'),
('BUYER_01', 'Player_One', 30000.00, 'player'),
('BUYER_02', 'Player_Two', 15000.00, 'player'),
('COURIER_01', 'Delivery_Node', 5000.00, 'player'),
('PLAYER_001', 'Player_001', 50000.00, 'player'),
('PLAYER_002', 'Player_002', 50000.00, 'player'),
('PLAYER_003', 'Player_003', 50000.00, 'player'),
('MERCHANT_001', 'Merchant_001', 100000.00, 'merchant');

-- Permanent Shop Anchors (Commercial Endpoints)
INSERT OR IGNORE INTO shops (shop_id, merchant_id, shop_name, location_x, location_y, balance) VALUES
('SHOP_01', 'MERCH_01', 'Central_Market', 100.0, 100.0, 150000.00);