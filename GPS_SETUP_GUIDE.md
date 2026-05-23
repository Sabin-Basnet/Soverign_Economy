# Real-World GPS Setup Guide

This guide explains how to set up and run the Sovereign Economy project with real-world GPS integration.

## Prerequisites

- Python 3.10+
- Node.js 16+
- Google Maps API key (free tier available)
- SQLite3
- Git

## Backend Setup

### 1. Install Python Dependencies

```bash
cd c:\Users\SABIN\Desktop\Soverign_Economy

# Create/activate virtual environment
python -m venv economy
economy\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
# Apply GPS migration
sqlite3 economy.db < migration_to_gps.sql

# Seed Kathmandu test data
sqlite3 economy.db < seed_kathmandu.sql

# Verify migration
sqlite3 economy.db ".tables"
# Output should show: locations, pois, proximity_events, user_location_history, user_preferences
```

### 3. Start Backend Server

```bash
python main.py

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs (Swagger UI)
# Health check: http://localhost:8000/health
```

## Frontend Setup

### 1. Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Maps JavaScript API**
4. Create an API key (from "Credentials" tab)
5. Restrict API key to your domain (optional but recommended)

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Update Google Maps API Key

Edit `frontend/public/index.html`:

```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY"></script>
```

Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual key.

### 4. Start React Development Server

```bash
npm start

# App opens at http://localhost:3000
```

## Testing MVP Features

### Test 1: Verify Database Setup

```bash
sqlite3 economy.db "SELECT COUNT(*) as shops FROM locations;"
# Should return: shops = 7 (Kathmandu test data)

sqlite3 economy.db "SELECT COUNT(*) as pois FROM pois;"
# Should return: pois = 6 (Landmarks, quest hubs, etc.)
```

### Test 2: Test API Endpoints

```bash
# Get all POIs
curl http://localhost:8000/api/v1/pois

# Find nearby locations (near Thamel, Kathmandu)
curl -X POST http://localhost:8000/api/v1/locations/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 27.7155,
    "longitude": 85.3125,
    "radius_meters": 2000
  }'

# Update player position
curl -X POST http://localhost:8000/api/v1/player/position \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "PLAYER_001",
    "latitude": 27.7155,
    "longitude": 85.3125,
    "accuracy_meters": 5.0,
    "source": "gps"
  }'

# Get complete map state
curl "http://localhost:8000/api/v1/map/state?user_id=PLAYER_001&latitude=27.7155&longitude=85.3125&radius_meters=5000"
```

### Test 3: Test Frontend

1. Open http://localhost:3000
2. When prompted, choose "Enable GPS" or "Skip"
3. If GPS enabled:
   - Browser will request location permission
   - Player position updates in real-time
4. If manual:
   - Click on map to place yourself
   - Or drag joystick zone (bottom-left)
5. Verify:
   - Shops appear as green markers (Thamel area)
   - POIs appear as colored markers
   - Sidebar shows nearby locations/distance
   - GPS accuracy shown in info panel

## Project Structure After Setup

```
Soverign_Economy/
├── economy.db                    # SQLite database with GPS data
├── migration_to_gps.sql         # Database schema migration
├── seed_kathmandu.sql           # Test data (7 shops, 6 POIs)
├── geo_utils.py                 # GPS math (Haversine, etc.)
├── locations.py                 # LocationManager class
├── main.py                      # FastAPI app with new endpoints
├── models.py                    # Updated Pydantic models
├── bank.py                      # Financial engine (unchanged)
├── spatial.py                   # WebSocket sync (unchanged)
├── analytics.py                 # Economic metrics (unchanged)
├── ROADMAP.md                   # Development roadmap
│
├── frontend/
│   ├── public/
│   │   └── index.html           # Updated with Google Maps script
│   └── src/
│       ├── MapComponent.js      # NEW: Google Maps component
│       ├── MapComponent.css     # NEW: Map styling
│       ├── App.js               # Updated to use MapComponent
│       └── ...
```

## API Endpoints (New)

All endpoints return JSON. Use `Content-Type: application/json`.

### Location Management

#### GET `/api/v1/locations/{location_id}`
Get details of a specific location

#### POST `/api/v1/locations/nearby`
Find shops within radius
```json
{
  "latitude": 27.7128,
  "longitude": 85.3272,
  "radius_meters": 1000
}
```

#### GET `/api/v1/locations/owner/{owner_id}`
Get all shops owned by a user

#### POST `/api/v1/locations/create`
Register a new shop (owner_id required)

### POI Management

#### GET `/api/v1/pois`
Get all Points of Interest

#### GET `/api/v1/pois/nearby`
Find POIs within radius
```
?latitude=27.7128&longitude=85.3272&radius_meters=5000
```

### Player Position

#### POST `/api/v1/player/position`
Update player's GPS location
```json
{
  "user_id": "PLAYER_001",
  "latitude": 27.7128,
  "longitude": 85.3272,
  "accuracy_meters": 5.0,
  "source": "gps"  # or "manual", "joystick"
}
```

#### GET `/api/v1/map/state`
Get complete map state for rendering
```
?user_id=PLAYER_001&latitude=27.7128&longitude=85.3272&radius_meters=5000
```

## Troubleshooting

### "Google Maps is not loaded"
- Verify `YOUR_GOOGLE_MAPS_API_KEY` is replaced in `index.html`
- Check API key restrictions (should include your domain)
- Clear browser cache and reload

### GPS not working
- Check browser location permissions
- Must be on HTTPS or localhost
- Some devices may not have GPS (use manual placement)

### "Location creation failed: Location at coordinates already exists"
- Can't have two shops at exact same GPS coordinates
- Try moving slightly (0.0001 degrees ≈ 10 meters)

### Shops don't appear on map
- Verify API returned locations: Check browser DevTools Network tab
- Verify map initialization: Check browser console
- Verify Kathmandu data was seeded: `sqlite3 economy.db "SELECT * FROM locations;"`

### "Cannot read property 'SymbolPath' of undefined"
- Google Maps script not loaded
- Check `index.html` has correct API key
- Reload page

## Next Steps (Phase 2)

After verifying MVP works:

1. **Admin Panel**: Create UI to add/edit shops and POIs
2. **Location Interaction**: Buy from shop when nearby
3. **Quest System**: Add quests/tasks at POIs
4. **Social Features**: Show nearby players (with opt-in)
5. **Real Data**: Import real shops using Google Places API
6. **Advanced Economy**: Shop rent, inventory, delivery quests

## Development Commands Cheat Sheet

```bash
# Terminal 1: Backend
cd Soverign_Economy
economy\Scripts\activate
python main.py

# Terminal 2: Frontend
cd Soverign_Economy\frontend
npm start

# Terminal 3: Database admin (optional)
sqlite3 economy.db
# .tables - show all tables
# SELECT * FROM locations; - view shops
# SELECT COUNT(*) FROM transactions; - view transaction count
```

## Production Deployment Notes

Before deploying to production:

1. **Environment Variables**: Move API keys to `.env` file
2. **CORS**: Update `main.py` allowed origins
3. **Database**: Migrate from SQLite to PostgreSQL for scalability
4. **Maps**: Consider maps clustering library for 1000+ locations
5. **Security**: Implement authentication/authorization

See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment guide.
