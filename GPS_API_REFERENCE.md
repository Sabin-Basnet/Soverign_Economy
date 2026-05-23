# Real-World GPS API Reference

Quick reference for all new location-based endpoints.

## Base URL
```
http://localhost:8000/api/v1
```

## Locations (Shops)

### Create Location
```
POST /locations/create
Content-Type: application/json

{
  "owner_id": "MERCH_001",
  "location_name": "My Shop",
  "description": "Optional description",
  "latitude": 27.7128,
  "longitude": 85.3272,
  "location_type": "shop"  // or "bank", "trading_post", "guild_hall"
}

Response: 201 Created
{
  "location_id": "LOC_MERCH_001_MY_SHOP",
  "owner_id": "MERCH_001",
  "location_name": "My Shop",
  "latitude": 27.7128,
  "longitude": 85.3272,
  "location_type": "shop",
  "balance": 50000.0,
  "created_at": "2026-05-23T10:30:00"
}
```

### Get Location Details
```
GET /locations/{location_id}

Response: 200 OK
{
  "location_id": "LOC_THAMEL_BOOKSHOP",
  "owner_id": "MERCH_001",
  "location_name": "Pilgrim Book House",
  "latitude": 27.7155,
  "longitude": 85.3125,
  "location_type": "shop",
  "balance": 50000.0
}
```

### Find Nearby Locations
```
POST /locations/nearby
Content-Type: application/json

{
  "latitude": 27.7155,
  "longitude": 85.3125,
  "radius_meters": 5000
}

Response: 200 OK
{
  "count": 3,
  "locations": [
    {
      "location_id": "LOC_THAMEL_BOOKSHOP",
      "location_name": "Pilgrim Book House",
      "location_type": "shop",
      "latitude": 27.7155,
      "longitude": 85.3125,
      "distance_meters": 0.0,
      "balance": 50000.0
    },
    {
      "location_id": "LOC_THAMEL_RESTAURANT",
      "location_name": "The Bhaktapur Kitchen",
      "location_type": "shop",
      "latitude": 27.7165,
      "longitude": 85.3135,
      "distance_meters": 157.3,
      "balance": 75000.0
    }
  ]
}
```

### List Owner's Locations
```
GET /locations/owner/{owner_id}

Response: 200 OK
{
  "count": 2,
  "locations": [...]
}
```

## Points of Interest (POIs)

### Get All POIs
```
GET /pois

Response: 200 OK
{
  "count": 6,
  "pois": [
    {
      "poi_id": "POI_KATHMANDU_DURBAR",
      "poi_name": "Kathmandu Durbar Square",
      "description": "Historic royal palace square",
      "latitude": 27.7030,
      "longitude": 85.3300,
      "poi_type": "landmark",
      "reward_type": "token_bonus",
      "reward_amount": 100.0,
      "interaction_radius_meters": 200.0,
      "is_active": 1
    }
  ]
}
```

### Find Nearby POIs
```
GET /pois/nearby?latitude=27.7128&longitude=85.3272&radius_meters=5000

Response: 200 OK
{
  "count": 3,
  "pois": [
    {
      "poi_id": "POI_KATHMANDU_DURBAR",
      "poi_name": "Kathmandu Durbar Square",
      "latitude": 27.7030,
      "longitude": 85.3300,
      "poi_type": "landmark",
      "reward_type": "token_bonus",
      "reward_amount": 100.0,
      "distance_meters": 780.5
    }
  ]
}
```

## Player Position

### Update Player Position
```
POST /player/position
Content-Type: application/json

{
  "user_id": "PLAYER_001",
  "latitude": 27.7155,
  "longitude": 85.3125,
  "accuracy_meters": 5.0,
  "source": "gps"  // "gps", "manual", or "joystick"
}

Response: 200 OK
{
  "user_id": "PLAYER_001",
  "latitude": 27.7155,
  "longitude": 85.3125,
  "updated": true
}
```

## Map State

### Get Complete Map State
```
GET /map/state?user_id=PLAYER_001&latitude=27.7155&longitude=85.3125&radius_meters=5000

Response: 200 OK
{
  "player_position": {
    "user_id": "PLAYER_001",
    "latitude": 27.7155,
    "longitude": 85.3125,
    "accuracy_meters": 5.0,
    "source": "gps"
  },
  "nearby_locations": [
    {
      "location_id": "LOC_THAMEL_BOOKSHOP",
      "location_name": "Pilgrim Book House",
      "location_type": "shop",
      "latitude": 27.7155,
      "longitude": 85.3125,
      "distance_meters": 0.0,
      "balance": 50000.0
    }
  ],
  "nearby_pois": [
    {
      "poi_id": "POI_THAMEL_PARK",
      "poi_name": "Thamel Green Space",
      "latitude": 27.7175,
      "longitude": 85.3140,
      "poi_type": "quest_hub",
      "reward_type": "quest",
      "reward_amount": 250.0,
      "interaction_radius_meters": 100.0
    }
  ],
  "nearby_players": []
}
```

## Proximity Events

### Log Proximity Event
```
POST /proximity-events
Content-Type: application/json

{
  "user_id": "PLAYER_001",
  "location_id": "LOC_THAMEL_BOOKSHOP",  // optional
  "poi_id": null,                         // optional
  "event_type": "arrived",                // "arrived", "departed", "interacted", "completed_quest"
  "distance_meters": 50.0
}

Response: 200 OK
{
  "event_id": 1,
  "user_id": "PLAYER_001",
  "event_type": "arrived",
  "location_id": "LOC_THAMEL_BOOKSHOP",
  "poi_id": null,
  "distance_meters": 50.0,
  "timestamp": "2026-05-23T10:30:00"
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

Common status codes:
- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Testing Examples

### Find shops in Thamel, Kathmandu
```bash
curl -X POST http://localhost:8000/api/v1/locations/nearby \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 27.7175,
    "longitude": 85.3140,
    "radius_meters": 1000
  }'
```

### Get map state for player
```bash
curl "http://localhost:8000/api/v1/map/state?user_id=PLAYER_001&latitude=27.7175&longitude=85.3140&radius_meters=5000"
```

### Update player position from GPS
```bash
curl -X POST http://localhost:8000/api/v1/player/position \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "PLAYER_001",
    "latitude": 27.7155,
    "longitude": 85.3125,
    "accuracy_meters": 8.5,
    "source": "gps"
  }'
```

### Create a new shop
```bash
curl -X POST http://localhost:8000/api/v1/locations/create \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "MERCH_NEW",
    "location_name": "My New Shop",
    "latitude": 27.7200,
    "longitude": 85.3200,
    "location_type": "shop"
  }'
```

## Data Types

### Location Types
- `"shop"` - General store
- `"bank"` - Financial institution
- `"trading_post"` - High-value trading
- `"guild_hall"` - Guild headquarters

### POI Types
- `"landmark"` - Historic/cultural site
- `"quest_hub"` - Quest starting point
- `"arena"` - PvP/competition zone
- `"resource_spot"` - Resource gathering location
- `"dungeon"` - Difficulty/adventure

### Event Types
- `"arrived"` - Player entered location area
- `"departed"` - Player left location area
- `"interacted"` - Player interacted with location/POI
- `"completed_quest"` - Player completed quest at POI

### Position Sources
- `"gps"` - From device GPS
- `"manual"` - User manually placed on map
- `"joystick"` - Calculated from joystick input

## Coordinates Reference

### Kathmandu Test Area
- Center: 27.7128°N, 85.3272°E
- Thamel (tourist district): 27.7155-27.7175°N, 85.3120-85.3150°E
- Durbar Square: 27.7029-27.7030°N, 85.3299-85.3310°E
- Swayambhu: 27.6558°N, 85.2917°E
- Patan: 27.6747°N, 85.3279°E

### Approximate Scale
- 0.0001° ≈ 10-11 meters
- 0.001° ≈ 100-111 meters
- 0.01° ≈ 1 km
- 0.1° ≈ 10-11 km
