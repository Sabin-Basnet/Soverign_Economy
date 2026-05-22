"""
PROTOCOL SOVEREIGN ECONOMY (GeoLedger)
Real-Time Spatial Commerce Engine with Immutable Fixed-Supply Ledger

Integrated REST API Server combining:
- Phase 2: Financial Engine (bank.py)
- Phase 3: Spatial Pipeline (spatial.py)
- Phase 4: Analytics (analytics.py)
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json

from bank import BankingEngine
from spatial import SpatialManager
from analytics import AnalyticsEngine
from models import (
    TransferRequest, TransferResponse, EscrowCreateRequest, EscrowCompleteRequest,
    PlayerMoveEvent, EconomicMetrics, UserBalance
)

# ============= Initialization =============
banking_engine = BankingEngine()
spatial_manager = SpatialManager()
analytics_engine = AnalyticsEngine()

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


# ============= Health & Status =============

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