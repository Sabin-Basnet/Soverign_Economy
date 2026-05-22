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
    """Player spatial coordinates"""
    user_id: str
    location_x: float
    location_y: float
    bearing: float = 0.0


class PlayerMoveEvent(BaseModel):
    """WebSocket: player_move event payload"""
    event: Literal["player_move"]
    payload: PlayerPosition


class SectorBroadcast(BaseModel):
    """Broadcast to nearby players (sector-partitioned)"""
    event: str
    data: dict
    sender_id: str
    distance: float


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
