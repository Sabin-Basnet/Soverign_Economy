"""
PROTOCOL SOVEREIGN ECONOMY (GeoLedger)
Real-Time Spatial Commerce Engine with Immutable Fixed-Supply Ledger + Real-World GPS

Integrated REST API Server combining:
- Phase 2: Financial Engine (bank.py)
- Phase 3: Spatial Pipeline (spatial.py)
- Phase 4: Analytics (analytics.py)
- Phase 5: Real-World Locations (locations.py)
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json

from bank import BankingEngine
from spatial import SpatialManager
from analytics import AnalyticsEngine
from locations import LocationManager
from models import (
    TransferRequest, TransferResponse, EscrowCreateRequest, EscrowCompleteRequest,
    PlayerMoveEvent, EconomicMetrics, UserBalance,
    LocationCreate, LocationResponse, LocationNearbyRequest, LocationNearbyResponse,
    POIResponse, MapStateResponse, PlayerGPSPosition, PlayerGPSMoveEvent,
    ProximityEventCreate
)

# ============= Initialization =============
banking_engine = BankingEngine()
spatial_manager = SpatialManager()
analytics_engine = AnalyticsEngine()
location_manager = LocationManager()

# Periodic task for analytics snapshots
analytics_task = None


async def periodic_analytics():
    """Periodically save economic metrics snapshots (every 5 minutes)"""
    while True:
        try:
            analytics_engine.save_metrics_snapshot()
            print("[ANALYTICS] Snapshot saved")
        except Exception as e:
            print(f"[ANALYTICS] Error: {e}")
        await asyncio.sleep(300)  # 5 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI startup/shutdown lifecycle"""
    # Startup
    global analytics_task
    analytics_task = asyncio.create_task(periodic_analytics())
    print("[SERVER] GeoLedger Protocol Engine initialized")
    
    # Verify zero-sum invariant on startup
    is_valid, total, msg = analytics_engine.verify_zero_sum_invariant()
    if not is_valid:
        print(f"[WARNING] {msg}")
    else:
        print(f"[OK] Zero-sum invariant verified. Total circulation: {total:,.2f}")
    
    yield
    
    # Shutdown
    if analytics_task:
        analytics_task.cancel()
    print("[SERVER] Shutdown complete")


# ============= FastAPI App Setup =============
app = FastAPI(
    title="Protocol: Sovereign Economy (GeoLedger)",
    description="Real-time spatial commerce engine with immutable ledger",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= PHASE 2: REST API Endpoints =============

@app.post("/api/v1/transfer", response_model=TransferResponse)
async def transfer_funds(req: TransferRequest):
    """
    Safe peer-to-peer transfer with velocity tax middleware.
    
    All transfers are subject to 2% VAT, automatically routed to State_Treasury.
    Uses row-level locking to prevent double-spend attacks.
    """
    try:
        result = banking_engine.transfer(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@app.post("/api/v1/escrow/create")
async def create_escrow(req: EscrowCreateRequest):
    """
    Initiate logistics contract with escrow lock.
    
    Funds are frozen until courier reaches buyer location.
    Both principal and tax are locked in escrow state.
    """
    try:
        result = banking_engine.create_escrow(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escrow creation failed: {str(e)}")


@app.post("/api/v1/escrow/complete")
async def complete_escrow(req: EscrowCompleteRequest):
    """
    Complete delivery and release escrow funds.
    
    Validates courier is within delivery_threshold distance of buyer.
    Releases principal to seller and tax to treasury.
    """
    try:
        result = banking_engine.complete_escrow(req)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escrow completion failed: {str(e)}")


@app.get("/api/v1/balance/{user_id}", response_model=UserBalance)
async def get_balance(user_id: str):
    """Retrieve current balance for a user"""
    try:
        return banking_engine.get_balance(user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============= PHASE 3: WebSocket Spatial Pipeline =============

class ConnectionManager:
    """Manages active WebSocket connections per user"""
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        spatial_manager.register_connection(user_id, websocket)
        print(f"[WS] {user_id} connected")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            spatial_manager.unregister_connection(user_id)
        print(f"[WS] {user_id} disconnected")

    async def broadcast_to_nearby(self, event: PlayerMoveEvent):
        """Send movement to all nearby connected players"""
        user_id = event.payload.user_id
        nearby = spatial_manager.get_nearby_players(user_id, radius=100.0)
        
        message = {
            "event": "player_move",
            "data": {
                "user_id": user_id,
                "coordinates": {
                    "x": event.payload.location_x,
                    "y": event.payload.location_y
                },
                "bearing": event.payload.bearing
            }
        }
        
        for nearby_user_id in nearby.keys():
            if nearby_user_id in self.active_connections:
                try:
                    await self.active_connections[nearby_user_id].send_json(message)
                except Exception as e:
                    print(f"[WS] Send failed to {nearby_user_id}: {e}")


connection_manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time spatial synchronization.
    
    Expected client messages:
    {
        "event": "player_move",
        "payload": {
            "user_id": "usr_buyer01",
            "coordinates": { "x": 142.5, "y": 89.2 },
            "bearing": 180.0
        }
    }
    """
    await connection_manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("event") == "player_move":
                # Parse movement event
                event = PlayerMoveEvent(**msg)
                
                # Update spatial database
                spatial_manager.update_position(event)
                
                # Broadcast to nearby players
                await connection_manager.broadcast_to_nearby(event)
            
            elif msg.get("event") == "ping":
                # Keep-alive heartbeat
                await websocket.send_json({"event": "pong"})
    
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
    except json.JSONDecodeError:
        print(f"[WS] Invalid JSON from {user_id}")
    except Exception as e:
        print(f"[WS] Error: {e}")
        connection_manager.disconnect(user_id)


# ============= PHASE 4: Analytics Endpoints =============

@app.get("/api/v1/analytics/metrics", response_model=EconomicMetrics)
async def get_current_metrics():
    """
    Retrieve real-time economic metrics.
    
    Returns:
    - total_circulation: Total tokens in system
    - velocity_of_money: Transaction rate (higher = more active)
    - gini_coefficient: Wealth distribution (0 = equal, 1 = unequal)
    - treasury_balance: State treasury balance
    - num_active_players: Players active in last hour
    - num_transactions: Total transaction count
    """
    return analytics_engine.get_metrics()


@app.get("/api/v1/analytics/metrics/history")
async def get_metrics_history(limit: int = 50):
    """Retrieve historical metric snapshots for trend analysis"""
    return analytics_engine.get_recent_metrics_history(limit)


@app.get("/api/v1/analytics/wealth-distribution")
async def get_wealth_distribution():
    """Get sorted wealth distribution across all users"""
    return analytics_engine.get_wealth_distribution()


@app.get("/api/v1/analytics/audit-log")
async def get_audit_log(limit: int = 100):
    """Retrieve recent audit trail (tax collection, escrow events)"""
    return analytics_engine.get_audit_trail(limit)


@app.get("/api/v1/analytics/invariant-check")
async def check_invariant():
    """
    CRITICAL: Verify zero-sum invariant.
    Should always return valid=true if system is working correctly.
    """
    is_valid, total, error = analytics_engine.verify_zero_sum_invariant()
    return {
        "valid": is_valid,
        "total_circulation": total,
        "genesis_target": 1_000_000.0,
        "error": error
    }


# ============= Spatial Admin Endpoints =============

@app.get("/api/v1/spatial/positions")
async def get_all_positions():
    """[Admin] Retrieve all player positions"""
    positions = spatial_manager.get_all_positions()
    return {
        "positions": {
            uid: {"x": pos[0], "y": pos[1], "bearing": pos[2]}
            for uid, pos in positions.items()
        }
    }


@app.get("/api/v1/spatial/bounds")
async def get_map_bounds():
    """[Admin] Get active play area boundaries"""
    return spatial_manager.calculate_map_bounds()


# ============= PHASE 5: Real-World Locations (GPS-Based) =============

@app.post("/api/v1/locations/create", response_model=LocationResponse)
async def create_location(req: LocationCreate):
    """
    Register a new real-world location (shop, trading post, etc.)
    
    Args:
        owner_id: User ID of location owner
        location_name: Display name
        latitude: GPS latitude
        longitude: GPS longitude
        location_type: shop, bank, trading_post, guild_hall
    """
    try:
        location_id = f"LOC_{req.owner_id}_{req.location_name[:10].replace(' ', '_').upper()}"
        result = location_manager.create_location(
            location_id=location_id,
            owner_id=req.owner_id,
            location_name=req.location_name,
            latitude=req.latitude,
            longitude=req.longitude,
            location_type=req.location_type,
            description=req.description,
            initial_balance=50000.0
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Location creation failed: {str(e)}")


@app.post("/api/v1/locations/nearby")
async def find_nearby_locations(req: LocationNearbyRequest) -> dict:
    """
    Find all shops/locations within radius of player's current position
    
    Args:
        latitude: Player's current latitude
        longitude: Player's current longitude
        radius_meters: Search radius (default 1km)
    
    Returns:
        List of nearby locations sorted by distance
    """
    try:
        nearby = location_manager.find_nearby_locations(
            latitude=req.latitude,
            longitude=req.longitude,
            radius_meters=req.radius_meters
        )
        
        return {
            "count": len(nearby),
            "locations": [
                LocationNearbyResponse(
                    location_id=loc['location_id'],
                    location_name=loc['location_name'],
                    location_type=loc['location_type'],
                    latitude=loc['latitude'],
                    longitude=loc['longitude'],
                    distance_meters=dist,
                    balance=loc['balance']
                )
                for loc, dist in nearby
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/locations/{location_id}", response_model=LocationResponse)
async def get_location(location_id: str):
    """Get details of a specific location"""
    try:
        location = location_manager.get_location(location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        return location
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/locations/owner/{owner_id}")
async def get_owner_locations(owner_id: str):
    """Get all locations owned by a user"""
    try:
        locations = location_manager.list_locations_by_owner(owner_id)
        return {"count": len(locations), "locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/pois")
async def get_all_pois() -> dict:
    """
    Get all Points of Interest (landmarks, quest hubs, arenas, etc.)
    
    Useful for map rendering of game spots
    """
    try:
        # For MVP, retrieve all POIs from database
        import sqlite3
        conn = sqlite3.connect("economy.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pois WHERE is_active = 1")
        pois = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "count": len(pois),
            "pois": pois
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/pois/nearby")
async def find_nearby_pois(latitude: float, longitude: float, radius_meters: float = 5000.0) -> dict:
    """Find POIs within radius of player position"""
    try:
        nearby = location_manager.find_nearby_pois(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        )
        
        return {
            "count": len(nearby),
            "pois": [
                {
                    "poi_id": poi['poi_id'],
                    "poi_name": poi['poi_name'],
                    "latitude": poi['latitude'],
                    "longitude": poi['longitude'],
                    "poi_type": poi['poi_type'],
                    "reward_type": poi['reward_type'],
                    "reward_amount": poi['reward_amount'],
                    "distance_meters": dist
                }
                for poi, dist in nearby
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/player/position")
async def update_player_position(position: PlayerGPSPosition) -> dict:
    """
    Update player's real-world GPS position
    
    Called when:
    - Device's GPS updates
    - User manually places themselves on map
    - Joystick-based movement (client calculates new coords)
    """
    try:
        import sqlite3
        conn = sqlite3.connect("economy.db")
        cursor = conn.cursor()
        
        # Update main player position
        cursor.execute("""
            INSERT INTO player_positions (user_id, latitude, longitude, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            updated_at = CURRENT_TIMESTAMP
        """, (position.user_id, position.latitude, position.longitude))
        
        # Log location history
        cursor.execute("""
            INSERT INTO user_location_history 
            (user_id, latitude, longitude, accuracy_meters, source)
            VALUES (?, ?, ?, ?, ?)
        """, (position.user_id, position.latitude, position.longitude, 
              position.accuracy_meters, position.source))
        
        conn.commit()
        conn.close()
        
        return {
            "user_id": position.user_id,
            "latitude": position.latitude,
            "longitude": position.longitude,
            "updated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/map/state")
async def get_map_state(
    user_id: str,
    latitude: float,
    longitude: float,
    radius_meters: float = 5000.0
) -> MapStateResponse:
    """
    Get complete map state for rendering
    
    Returns:
    - Player's current position
    - Nearby shops/locations
    - Nearby POIs
    - Nearby players (if location sharing enabled)
    """
    try:
        # Get player position
        player_pos = PlayerGPSPosition(
            user_id=user_id,
            latitude=latitude,
            longitude=longitude
        )
        
        # Get nearby locations
        nearby_locations = location_manager.find_nearby_locations(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        )
        
        nearby_locs = [
            LocationNearbyResponse(
                location_id=loc['location_id'],
                location_name=loc['location_name'],
                location_type=loc['location_type'],
                latitude=loc['latitude'],
                longitude=loc['longitude'],
                distance_meters=dist,
                balance=loc['balance']
            )
            for loc, dist in nearby_locations
        ]
        
        # Get nearby POIs
        nearby_pois = location_manager.find_nearby_pois(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters
        )
        
        nearby_poi_list = [
            POIResponse(
                poi_id=poi['poi_id'],
                poi_name=poi['poi_name'],
                description=poi['description'],
                latitude=poi['latitude'],
                longitude=poi['longitude'],
                poi_type=poi['poi_type'],
                reward_type=poi['reward_type'],
                reward_amount=poi['reward_amount'],
                interaction_radius_meters=poi['interaction_radius_meters']
            )
            for poi, dist in nearby_pois
        ]
        
        return MapStateResponse(
            player_position=player_pos,
            nearby_locations=nearby_locs,
            nearby_pois=nearby_poi_list,
            nearby_players=[]  # TODO: Implement with location sharing opt-in
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/proximity-events")
async def log_proximity_event(event: ProximityEventCreate) -> dict:
    """
    Log a proximity event (arrival, departure, interaction)
    
    Used for audit trail and quest tracking
    """
    try:
        result = location_manager.log_proximity_event(
            user_id=event.user_id,
            event_type=event.event_type,
            location_id=event.location_id,
            poi_id=event.poi_id,
            distance_meters=event.distance_meters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Server status"""
    return {
        "status": "running",
        "protocol": "GeoLedger",
        "version": "1.0.0",
        "active_connections": len(connection_manager.active_connections)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    is_valid, total, _ = analytics_engine.verify_zero_sum_invariant()
    return {
        "status": "healthy" if is_valid else "degraded",
        "zero_sum_valid": is_valid,
        "total_circulation": total,
        "active_ws_connections": len(connection_manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )