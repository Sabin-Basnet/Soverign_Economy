-- Test Data: Kathmandu, Nepal (MVP Testing)
-- Kathmandu center: ~27.7128° N, 85.3272° E

-- ===== TEST SHOPS (Locations) =====
-- Thamel area (tourist district)
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance) 
VALUES ('LOC_THAMEL_BOOKSHOP', 'MERCH_001', 'Pilgrim Book House', 'English books & supplies', 27.7155, 85.3125, 'shop', 50000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_THAMEL_RESTAURANT', 'MERCH_002', 'The Bhaktapur Kitchen', 'Traditional Nepali cuisine', 27.7165, 85.3135, 'shop', 75000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_THAMEL_CAFE', 'MERCH_003', 'Nirvana Garden Cafe', 'Coffee & pastries', 27.7172, 85.3145, 'shop', 40000.0)
ON CONFLICT DO NOTHING;

-- Durbar Square area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DURBAR_HANDICRAFT', 'MERCH_004', 'Durbar Handicraft Co.', 'Local crafts & souvenirs', 27.7029, 85.3299, 'shop', 60000.0)
ON CONFLICT DO NOTHING;

INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_DURBAR_TRADING', 'MERCH_005', 'Silver Market', 'Traditional silver trading', 27.7015, 85.3310, 'trading_post', 120000.0)
ON CONFLICT DO NOTHING;

-- Kathmandu Durbar Square area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_SWAYAMBHU_SHOP', 'MERCH_006', 'Swayambhu Bazaar', 'Buddhist supplies & gifts', 27.6558, 85.2917, 'shop', 35000.0)
ON CONFLICT DO NOTHING;

-- Patan area
INSERT INTO locations (location_id, owner_id, location_name, description, latitude, longitude, location_type, balance)
VALUES ('LOC_PATAN_TRADING', 'MERCH_007', 'Patan Trading House', 'Ceramics & pottery', 27.6747, 85.3279, 'shop', 55000.0)
ON CONFLICT DO NOTHING;

-- ===== TEST POIS (Points of Interest) =====
-- Parks & landmarks
INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_KATHMANDU_DURBAR', 'Kathmandu Durbar Square', 'Historic royal palace square', 27.7030, 85.3300, 'landmark', 'token_bonus', 100.0, 200.0, 120)
ON CONFLICT DO NOTHING;

INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_SWAYAMBHU', 'Swayambhu Stupa', 'Ancient Buddhist temple', 27.6558, 85.2917, 'landmark', 'token_bonus', 150.0, 200.0, 120)
ON CONFLICT DO NOTHING;

INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_BOUDHA', 'Boudhanath Stupa', 'Large Buddhist stupa', 27.7219, 85.3635, 'landmark', 'token_bonus', 150.0, 250.0, 120)
ON CONFLICT DO NOTHING;

INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_THAMEL_PARK', 'Thamel Green Space', 'Local park & gathering spot', 27.7175, 85.3140, 'quest_hub', 'quest', 250.0, 100.0, 60)
ON CONFLICT DO NOTHING;

INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_PATAN_DURBAR', 'Patan Durbar Square', 'Historic Patan palace', 27.6747, 85.3279, 'landmark', 'token_bonus', 120.0, 200.0, 120)
ON CONFLICT DO NOTHING;

INSERT INTO pois (poi_id, poi_name, description, latitude, longitude, poi_type, reward_type, reward_amount, interaction_radius_meters, interaction_cooldown_minutes)
VALUES ('POI_THAMEL_ARENA', 'Thamel Trading Arena', 'PvP trading zone', 27.7160, 85.3130, 'arena', 'quest', 500.0, 150.0, 30)
ON CONFLICT DO NOTHING;

-- ===== TEST USER LOCATIONS =====
-- Simulate some test players in Kathmandu
INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_001', 27.7155, 85.3125, 5.0, 'manual')
ON CONFLICT DO NOTHING;

INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_002', 27.7029, 85.3299, 8.0, 'manual')
ON CONFLICT DO NOTHING;

INSERT INTO user_location_history (user_id, latitude, longitude, accuracy_meters, source)
VALUES ('PLAYER_003', 27.6558, 85.2917, 10.0, 'manual')
ON CONFLICT DO NOTHING;

-- Update main player_positions table with GPS coordinates
-- Note: This assumes these users exist in the users table
UPDATE player_positions 
SET latitude = 27.7175, longitude = 85.3140 
WHERE user_id = 'PLAYER_001';

UPDATE player_positions 
SET latitude = 27.7029, longitude = 85.3299 
WHERE user_id = 'PLAYER_002';

UPDATE player_positions 
SET latitude = 27.6558, longitude = 85.2917 
WHERE user_id = 'PLAYER_003';
