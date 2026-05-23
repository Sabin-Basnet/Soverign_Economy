"""
Pydantic Models for GeoLedger Protocol
Ensures type-safe API payloads and database representations
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime


# ============= P2P Transfer Models =============
class TransferRequest(BaseModel):
    """POST /api/v1/transfer payload"""
    sender_id: str
    receiver_id: str
    amount: float = Field(..., gt=0, description="Amount must be positive")
    
    @validator('sender_id', 'receiver_id')
    def validate_ids(cls, v):
        if not v or len(v) < 3:
            raise ValueError("ID must be at least 3 characters")
        return v


class TransferResponse(BaseModel):
    """Response after safe transfer"""
    transaction_id: int
    sender_id: str
    receiver_id: str
    amount: float
    tax_amount: float
    net_amount: float
    sender_new_balance: float
    receiver_new_balance: float
    timestamp: datetime


# ============= Spatial Models =============
class PlayerPosition(BaseModel):
    """Player spatial coordinates (legacy grid-based)"""
    user_id: str
    location_x: float
    location_y: float
    bearing: float = 0.0


class PlayerGPSPosition(BaseModel):
    """Player real-world GPS coordinates"""
    user_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy_meters: Optional[float] = None
    source: Literal["gps", "manual", "joystick"] = "gps"


class PlayerMoveEvent(BaseModel):
    """WebSocket: player_move event payload"""
    event: Literal["player_move"]
    payload: PlayerPosition


class PlayerGPSMoveEvent(BaseModel):
    """WebSocket: player_gps_move event payload (real-world)"""
    event: Literal["player_gps_move"]
    payload: PlayerGPSPosition


class SectorBroadcast(BaseModel):
    """Broadcast to nearby players (sector-partitioned)"""
    event: str
    data: dict
    sender_id: str
    distance: float


# ============= Real-World Location Models =============
class LocationCreate(BaseModel):
    """POST /api/v1/locations/create - Register a new shop"""
    owner_id: str
    location_name: str
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_type: Literal["shop", "bank", "trading_post", "guild_hall"] = "shop"


class LocationResponse(BaseModel):
    """Shop/Location response"""
    location_id: str
    owner_id: str
    location_name: str
    description: Optional[str]
    latitude: float
    longitude: float
    location_type: str
    balance: float
    created_at: datetime


class LocationNearbyRequest(BaseModel):
    """GET /api/v1/locations/nearby - Find nearby shops"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(default=1000.0, gt=0)


class LocationNearbyResponse(BaseModel):
    """Nearby locations response"""
    location_id: str
    location_name: str
    location_type: str
    latitude: float
    longitude: float
    distance_meters: float
    balance: float


class POIResponse(BaseModel):
    """Point of Interest response"""
    poi_id: str
    poi_name: str
    description: Optional[str]
    latitude: float
    longitude: float
    poi_type: str
    reward_type: Optional[str]
    reward_amount: Optional[float]
    interaction_radius_meters: float


class MapStateResponse(BaseModel):
    """Complete map state for rendering"""
    player_position: PlayerGPSPosition
    nearby_locations: list[LocationNearbyResponse]
    nearby_pois: list[POIResponse]
    nearby_players: list[PlayerGPSPosition]  # Opt-in location sharing


class ProximityEventCreate(BaseModel):
    """Log a proximity event (arrival at location/POI)"""
    user_id: str
    location_id: Optional[str] = None
    poi_id: Optional[str] = None
    event_type: Literal["arrived", "departed", "interacted", "completed_quest"]
    distance_meters: Optional[float] = None


# ============= Escrow Models =============
class EscrowCreateRequest(BaseModel):
    """POST /api/v1/escrow/create - Initiate logistics contract"""
    buyer_id: str
    seller_id: str
    shop_id: str
    amount: float = Field(..., gt=0)
    delivery_threshold: float = 1.0


class EscrowCompleteRequest(BaseModel):
    """POST /api/v1/escrow/complete - Fulfill delivery"""
    escrow_id: int
    courier_id: str
    buyer_location_x: float
    buyer_location_y: float


class EscrowResponse(BaseModel):
    """Escrow state response"""
    escrow_id: int
    buyer_id: str
    seller_id: str
    courier_id: Optional[str]
    amount: float
    tax_amount: float
    state: Literal["locked", "in_transit", "completed", "cancelled"]
    created_at: datetime


# ============= User & Wallet Models =============
class UserBalance(BaseModel):
    """Current user balance state"""
    user_id: str
    username: str
    balance: float
    user_type: str


class UserProfile(BaseModel):
    """Full user profile with metadata"""
    user_id: str
    username: str
    balance: float
    user_type: str
    position: Optional[PlayerPosition] = None
    created_at: datetime


# ============= Analytics Models =============
class EconomicMetrics(BaseModel):
    """System-wide economic indicators"""
    total_circulation: float
    velocity_of_money: float
    gini_coefficient: float
    treasury_balance: float
    num_active_players: int
    num_transactions: int
    captured_at: datetime


class TransactionRecord(BaseModel):
    """Immutable transaction audit record"""
    transaction_id: int
    sender_id: str
    receiver_id: str
    amount: float
    tx_type: str
    timestamp: datetime


# ============= Error Models =============
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    code: int
