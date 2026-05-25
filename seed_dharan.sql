-- Test Data: Dharan, Nepal (Eastern Nepal)
-- Dharan center: ~26.8124° N, 87.2845° E

-- ===== TEST SHOPS (Locations) in Dharan =====
-- Main Bazaar area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance) 
VALUES ('LOC_DHARAN_BOOKSHOP', 'MERCH_001', 'Dharan Books & Supplies', 'Books, stationery, tech', 26.8130, 87.2840, 'shop', 50000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_RESTAURANT', 'MERCH_002', 'Annapurna Restaurant', 'Traditional Nepali food', 26.8140, 87.2850, 'shop', 75000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_CAFE', 'MERCH_003', 'Himalayan Cafe', 'Coffee & snacks', 26.8125, 87.2835, 'shop', 40000.0)
ON CONFLICT DO NOTHING;

-- Bazaar Road area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_HANDICRAFT', 'MERCH_004', 'Dharan Crafts', 'Local crafts & souvenirs', 26.8110, 87.2860, 'shop', 60000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_TRADING', 'MERCH_005', 'Eastern Trading Post', 'Wholesale trading hub', 26.8115, 87.2875, 'trading_post', 120000.0)
ON CONFLICT DO NOTHING;

-- Hospital Road area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_PHARMACY', 'MERCH_006', 'Health & Wellness', 'Medicine & supplies', 26.8105, 87.2900, 'shop', 35000.0)
ON CONFLICT DO NOTHING;

-- Near B.P. Mandal Chowk
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DHARAN_GENERAL', 'MERCH_007', 'General Store Dharan', 'All essentials', 26.8118, 87.2828, 'shop', 55000.0)
ON CONFLICT DO NOTHING;

-- ===== TEST POIS (Points of Interest) in Dharan =====
-- Bazaar Road landmark
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_BAZAAR', 'Dharan Main Bazaar', 'Heart of Dharan commerce', 26.8130, 87.2850, 'landmark', 'token_bonus', 100.0, 200.0, 120)
ON CONFLICT DO NOTHING;

-- Hospital Road landmark
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_HOSPITAL', 'Dharan Hospital', 'Major healthcare hub', 26.8105, 87.2900, 'landmark', 'token_bonus', 80.0, 150.0, 120)
ON CONFLICT DO NOTHING;

-- Education landmark (Dharan College)
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_COLLEGE', 'Dharan College District', 'Educational hub', 26.8095, 87.2920, 'landmark', 'token_bonus', 120.0, 200.0, 120)
ON CONFLICT DO NOTHING;

-- Central Park/Green Space
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_PARK', 'Dharan Central Park', 'Local park & meeting spot', 26.8145, 87.2810, 'quest_hub', 'quest', 250.0, 100.0, 60)
ON CONFLICT DO NOTHING;

-- B.P. Mandal Chowk landmark
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_CHOWK', 'B.P. Mandal Chowk', 'City center landmark', 26.8118, 87.2828, 'landmark', 'token_bonus', 90.0, 150.0, 120)
ON CONFLICT DO NOTHING;

-- Trading Arena
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_DHARAN_ARENA', 'Dharan Trading Hub', 'PvP trading zone', 26.8115, 87.2875, 'arena', 'quest', 500.0, 150.0, 30)
ON CONFLICT DO NOTHING;

-- ===== TEST USER LOCATIONS =====
-- Simulate some test players in Dharan
INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_001', 26.8130, 87.2850, 5.0, 'manual')
ON CONFLICT DO NOTHING;

INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_002', 26.8110, 87.2860, 8.0, 'manual')
ON CONFLICT DO NOTHING;

INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_003', 26.8105, 87.2900, 10.0, 'manual')
ON CONFLICT DO NOTHING;

-- Update main player_positions table with GPS coordinates
UPDATE player_positions 
SET latitude = 26.8130, longitude = 87.2850
WHERE user_id = 'PLAYER_001';

UPDATE player_positions 
SET latitude = 26.8110, longitude = 87.2860
WHERE user_id = 'PLAYER_002';

UPDATE player_positions 
SET latitude = 26.8105, longitude = 87.2900
WHERE user_id = 'PLAYER_003';
