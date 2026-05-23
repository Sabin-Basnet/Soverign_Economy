# Sovereign Economy - Real-World Location Edition

## Vision
Transform the economy from grid-based to real-world GPS-enabled, inspired by Pokémon GO.

---

## MVP Phase 1: Real Maps Foundation (This Sprint)

### 1.1 Database Schema Updates
- [ ] Change coordinates from `(x, y)` grid → `(latitude, longitude)` GPS
- [ ] Add `locations` table for shops (name, lat, lng, owner_id, type)
- [ ] Add `pois` table for game spots (name, lat, lng, reward_type, reward_amount)
- [ ] Add `user_position` table tracking real-time player location + timestamp
- [ ] Add `proximity_events` table for logging shop/POI interactions

### 1.2 Backend API Additions
- [ ] `/locations/nearby` - Find shops within radius (meters)
- [ ] `/locations/create` - Admin endpoint to manually add shop (or CSV import)
- [ ] `/locations/import-csv` - Bulk import shops from CSV
- [ ] `/pois/list` - Get all POIs for map rendering
- [ ] `/pois/create` - Admin: Create new game spot
- [ ] `/player/position` - Update player current position (from GPS or manual)
- [ ] `/player/interactions` - Log when player reaches shop/POI
- [ ] `/map/state` - Get all shops + POIs + nearby players (for rendering)

### 1.3 Frontend Refactor
- [ ] Replace grid canvas with **Google Maps component**
- [ ] Add player location marker (blue dot)
- [ ] Show shops as map markers (green)
- [ ] Show POIs as different colored markers (yellow/red)
- [ ] Add location input: 
  - ✓ Browser geolocation (GPS)
  - ✓ Manual lat/lng search (fallback)
  - ✓ Test location button (Kathmandu default)
- [ ] Add joystick control for manual movement (drag on map)
- [ ] Real-time player marker updates via WebSocket

### 1.4 Admin Panel (Basic)
- [ ] Add shops page (list, create, edit, delete)
- [ ] CSV upload for bulk shop import
- [ ] Add POIs page (list, create, edit, delete)
- [ ] View all transactions + economic health

### 1.5 Testing & Calibration
- [ ] Use **Kathmandu, Nepal** as test location (~27.7° N, 85.3° E)
- [ ] Seed 5-10 test shops in downtown area
- [ ] Seed 5-10 test POIs (parks, landmarks)
- [ ] Test proximity detection at different distances (10m, 100m, 1km)
- [ ] Test joystick movement on map

---

## Phase 2: Enhanced Gameplay (Future Sprints)

### 2.1 Location-Based Activities
- [ ] Visit shop → Auto-open storefront UI
- [ ] Reach POI → Trigger mini-game/quest
- [ ] Area control → Guilds claim neighborhoods
- [ ] Geofencing → Enter/exit zone events

### 2.2 Social Features
- [ ] Local players visible on map (if opted in)
- [ ] Trade in person (hands must be ≤10m apart)
- [ ] Guild headquarters at specific location
- [ ] Chat/messages tied to locations

### 2.3 Real-World Integration
- [ ] Google Places API for real shops
- [ ] Weather API (affects transactions/movement)
- [ ] Time-based events (peak hours, night closing)
- [ ] Walking/running speed verification

### 2.4 Advanced Economy
- [ ] Shop inventory limits (local supply)
- [ ] Rent system (shops pay location tax)
- [ ] Delivery quests across city
- [ ] Price variation by location + demand

---

## Technical Architecture

### Before (Grid-Based)
```
Player: { user_id, x: int, y: int }
Distance: Euclidean (x², y²)
Map: 2D Canvas
```

### After (GPS-Based)
```
Player: { user_id, latitude: float, longitude: float, last_update: timestamp }
Shop: { shop_id, owner_id, name, latitude, longitude, type: enum }
POI: { poi_id, name, latitude, longitude, reward_type, reward_amount }
Distance: Haversine formula (great-circle distance in km/m)
Map: Google Maps API
```

### Key Implementation Details

#### Proximity Detection (Haversine Formula)
```python
def haversine_distance(lat1, lng1, lat2, lng2) -> float:
    """Returns distance in meters between two coordinates."""
    R = 6371000  # Earth radius in meters
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lng2 - lng1)
    
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c
```

#### Spatial Sync (Radius-Based)
```
Player moves → Sends (lat, lng) to server
Server finds all shops/POIs within 5km radius
Server sends updated map state to player
Frontend renders Google Map with markers
```

#### Transaction at Location
```
1. Player walks to shop (within 50m)
2. Shop becomes interactive on map
3. Player purchases → Funds transfer (existing economy logic)
4. Proximity event logged (audit trail)
5. If delivery job → Courier position tracked until ±50m of destination
```

---

## Testing Strategy

### MVP Testing (Local)
1. **Static test**: Add 3 test shops, verify they appear on map
2. **Proximity test**: Manually drag player marker within 50m of shop → Should highlight
3. **Transaction test**: Buy from shop, verify balance transfer + tax
4. **Joystick test**: Drag to move, drag to POI, check proximity detection

### Real-World Testing (Optional)
- Walk to a real shop location with phone
- Open app, verify location tracking
- Buy from shop via app
- Verify location in audit log

---

## MVP Deliverables (When Done)
✅ Database with GPS coordinates  
✅ Google Maps frontend with shop/POI markers  
✅ Location update endpoint  
✅ Proximity-based shop interaction  
✅ CSV import for shops  
✅ Basic admin panel  
✅ Joystick/drag movement  
✅ Test location (Kathmandu preset)  

---

## Git Workflow
```
main
 ├─ feature/real-maps-integration (current)
 │  ├─ db-schema-migration
 │  ├─ backend-api
 │  ├─ frontend-maps
 │  ├─ admin-panel
 │  └─ testing
```
