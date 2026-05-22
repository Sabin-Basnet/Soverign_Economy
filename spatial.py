"""
PHASE 3: Spatial WebSocket Manager
- Real-time coordinate synchronization
- Sector-based proximity broadcasting
- Euclidean distance filtering
"""

import json
import math
import sqlite3
from typing import Set, Dict, Tuple, Optional
from datetime import datetime
from models import PlayerMoveEvent, SectorBroadcast
from contextlib import contextmanager

DB_PATH = "economy.db"
BROADCAST_RADIUS = 100.0  # Euclidean distance for sector partitioning


class SpatialManager:
    """Manages player positions and broadcasts movement events to nearby clients"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # In-memory connection map: user_id -> WebSocket connection
        self.active_connections: Dict[str, object] = {}

    @contextmanager
    def get_connection(self):
        """Database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def register_connection(self, user_id: str, websocket_connection: object):
        """Register a new active WebSocket connection"""
        self.active_connections[user_id] = websocket_connection
        print(f"[SPATIAL] Registered connection for {user_id}")

    def unregister_connection(self, user_id: str):
        """Disconnect and remove a player"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"[SPATIAL] Unregistered connection for {user_id}")

    def get_nearby_players(
        self, user_id: str, radius: float = BROADCAST_RADIUS
    ) -> Dict[str, Tuple[float, float]]:
        """
        Find all players within broadcast radius using Euclidean distance.
        
        Returns: {user_id: (x, y), ...}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get requesting player's position
            cursor.execute(
                "SELECT location_x, location_y FROM player_positions WHERE user_id = ?",
                (user_id,)
            )
            pos_row = cursor.fetchone()
            if not pos_row:
                return {}
            
            px, py = pos_row['location_x'], pos_row['location_y']
            
            # Fetch all other player positions
            cursor.execute(
                "SELECT user_id, location_x, location_y FROM player_positions WHERE user_id != ?",
                (user_id,)
            )
            
            nearby = {}
            for row in cursor.fetchall():
                other_user_id = row['user_id']
                ox, oy = row['location_x'], row['location_y']
                
                # Calculate Euclidean distance
                distance = math.sqrt((ox - px) ** 2 + (oy - py) ** 2)
                
                # Include if within radius
                if distance <= radius:
                    nearby[other_user_id] = (ox, oy)
            
            return nearby

    def update_position(self, event: PlayerMoveEvent) -> bool:
        """
        Update player position in database and return success.
        
        Broadcast strategy:
        - Update DB first (source of truth)
        - Query nearby players
        - Only send to WebSocket connections within radius
        """
        user_id = event.payload.user_id
        x = event.payload.location_x
        y = event.payload.location_y
        bearing = event.payload.bearing
        
        # === UPDATE DATABASE ===
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO player_positions (user_id, location_x, location_y, bearing)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    location_x = ?, location_y = ?, bearing = ?, updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, x, y, bearing, x, y, bearing)
            )
        
        print(f"[SPATIAL] Updated position: {user_id} -> ({x:.1f}, {y:.1f})")
        return True

    async def broadcast_to_nearby(self, event: PlayerMoveEvent):
        """
        Broadcast movement event only to players within BROADCAST_RADIUS.
        
        This is the core spatial partitioning strategy:
        - No global broadcasts (scales poorly)
        - Each client only receives updates for nearby entities
        - Reduces WebSocket message volume
        """
        user_id = event.payload.user_id
        
        # Find nearby players
        nearby = self.get_nearby_players(user_id, radius=BROADCAST_RADIUS)
        
        # Build broadcast message
        broadcast_msg = {
            "event": "player_move",
            "data": {
                "user_id": user_id,
                "coordinates": {
                    "x": event.payload.location_x,
                    "y": event.payload.location_y
                },
                "bearing": event.payload.bearing,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Send only to connected nearby players
        for nearby_user_id in nearby.keys():
            if nearby_user_id in self.active_connections:
                conn = self.active_connections[nearby_user_id]
                try:
                    # This is pseudocode; actual implementation depends on WebSocket library
                    await conn.send_json(broadcast_msg)
                    print(f"[SPATIAL] Broadcasted to {nearby_user_id}")
                except Exception as e:
                    print(f"[SPATIAL] Failed to broadcast to {nearby_user_id}: {e}")

    def get_all_positions(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Retrieve all player positions (for admin dashboard/analytics).
        
        Returns: {user_id: (x, y, bearing), ...}
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, location_x, location_y, bearing FROM player_positions")
            
            positions = {}
            for row in cursor.fetchall():
                positions[row['user_id']] = (
                    row['location_x'],
                    row['location_y'],
                    row['bearing']
                )
            return positions

    def get_sector_members(self, sector_x: float, sector_y: float, sector_size: float = 100.0) -> list:
        """
        Retrieve all players in a specific sector grid cell.
        
        This enables further optimization: divide map into sectors,
        only update players in affected sectors.
        """
        sector_x_min = sector_x * sector_size
        sector_x_max = sector_x_min + sector_size
        sector_y_min = sector_y * sector_size
        sector_y_max = sector_y_min + sector_size
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, location_x, location_y FROM player_positions
                WHERE location_x BETWEEN ? AND ? AND location_y BETWEEN ? AND ?
                """,
                (sector_x_min, sector_x_max, sector_y_min, sector_y_max)
            )
            
            return [
                {
                    "user_id": row['user_id'],
                    "x": row['location_x'],
                    "y": row['location_y']
                }
                for row in cursor.fetchall()
            ]

    def calculate_map_bounds(self) -> Dict[str, float]:
        """
        Calculate active play area boundaries from all player positions.
        Useful for frontend viewport optimization.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    MIN(location_x) as min_x, MAX(location_x) as max_x,
                    MIN(location_y) as min_y, MAX(location_y) as max_y
                FROM player_positions
                """
            )
            row = cursor.fetchone()
            if row and row['min_x'] is not None:
                return {
                    "min_x": row['min_x'],
                    "max_x": row['max_x'],
                    "min_y": row['min_y'],
                    "max_y": row['max_y']
                }
            return {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}
