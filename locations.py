"""
Location Management Engine for Real-World Commerce
Handles shop/POI registration, proximity detection, and location-based transactions
"""

import sqlite3
import json
from typing import List, Tuple, Dict, Optional
from datetime import datetime
from geo_utils import haversine_distance, find_nearby_locations, is_within_radius


class LocationManager:
    """Manages real-world locations, shops, and POIs"""
    
    DB_PATH = "economy.db"
    VELOCITY_TAX_RATE = 0.02  # 2% transaction tax
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    # ========== LOCATION MANAGEMENT ==========
    
    def create_location(
        self,
        location_id: str,
        owner_id: str,
        location_name: str,
        latitude: float,
        longitude: float,
        location_type: str = "shop",
        description: str = None,
        initial_balance: float = 50000.0
    ) -> Dict:
        """
        Register a new location (shop, trading post, etc.)
        
        Args:
            location_id: Unique identifier
            owner_id: User ID of shop owner
            location_name: Display name
            latitude: GPS latitude
            longitude: GPS longitude
            location_type: Type of location
            description: Optional description
            initial_balance: Starting balance
        
        Returns:
            Location dict
        
        Raises:
            ValueError: If location already exists or coordinates invalid
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO locations 
                (location_id, owner_id, location_name, description, latitude, longitude, 
                 location_type, balance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (location_id, owner_id, location_name, description, latitude, longitude, 
                  location_type, initial_balance))
            
            conn.commit()
            
            return {
                "location_id": location_id,
                "owner_id": owner_id,
                "location_name": location_name,
                "latitude": latitude,
                "longitude": longitude,
                "location_type": location_type,
                "description": description,
                "balance": initial_balance
            }
        
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Location at coordinates already exists")
            raise ValueError(f"Location {location_id} already exists")
    
    
    def get_location(self, location_id: str) -> Optional[Dict]:
        """Get location by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM locations WHERE location_id = ?
        """, (location_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    
    def find_nearby_locations(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 1000.0,
        location_type: Optional[str] = None
    ) -> List[Tuple[Dict, float]]:
        """
        Find all locations within radius of coordinates.
        
        Returns:
            List of (location_dict, distance_meters) sorted by distance
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM locations WHERE 1=1"
        params = []
        
        if location_type:
            query += " AND location_type = ?"
            params.append(location_type)
        
        cursor.execute(query, params)
        locations = [dict(row) for row in cursor.fetchall()]
        
        # Filter by distance on application side (more flexible)
        results = []
        for loc in locations:
            distance = haversine_distance(
                latitude, longitude,
                loc['latitude'], loc['longitude']
            )
            if distance <= radius_meters:
                results.append((loc, distance))
        
        # Sort by distance
        results.sort(key=lambda x: x[1])
        return results
    
    
    def list_locations_by_owner(self, owner_id: str) -> List[Dict]:
        """Get all locations owned by a user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM locations 
            WHERE owner_id = ?
            ORDER BY created_at DESC
        """, (owner_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    
    # ========== POI MANAGEMENT ==========
    
    def create_poi(
        self,
        poi_id: str,
        poi_name: str,
        latitude: float,
        longitude: float,
        poi_type: str = "landmark",
        description: str = None,
        reward_type: str = None,
        reward_amount: float = None,
        interaction_radius_meters: float = 100.0,
        interaction_cooldown_minutes: int = 60
    ) -> Dict:
        """
        Create a new Point of Interest (game spot).
        
        Args:
            poi_id: Unique identifier
            poi_name: Display name
            latitude, longitude: GPS coordinates
            poi_type: Type (landmark, quest_hub, arena, etc.)
            reward_type: Type of reward (token_bonus, quest, etc.)
            reward_amount: Reward value (if token_bonus)
            interaction_radius_meters: How close player must be
            interaction_cooldown_minutes: Cooldown between interactions
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO pois 
                (poi_id, poi_name, description, latitude, longitude, poi_type,
                 reward_type, reward_amount, interaction_radius_meters, 
                 interaction_cooldown_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (poi_id, poi_name, description, latitude, longitude, poi_type,
                  reward_type, reward_amount, interaction_radius_meters, 
                  interaction_cooldown_minutes))
            
            conn.commit()
            
            return {
                "poi_id": poi_id,
                "poi_name": poi_name,
                "latitude": latitude,
                "longitude": longitude,
                "poi_type": poi_type,
                "reward_type": reward_type,
                "reward_amount": reward_amount,
                "interaction_radius_meters": interaction_radius_meters,
                "description": description
            }
        
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"POI {poi_id} already exists")
    
    
    def find_nearby_pois(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float = 5000.0
    ) -> List[Tuple[Dict, float]]:
        """Find all POIs within radius"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pois WHERE is_active = 1")
        pois = [dict(row) for row in cursor.fetchall()]
        
        results = []
        for poi in pois:
            distance = haversine_distance(
                latitude, longitude,
                poi['latitude'], poi['longitude']
            )
            if distance <= radius_meters:
                results.append((poi, distance))
        
        results.sort(key=lambda x: x[1])
        return results
    
    
    def get_poi(self, poi_id: str) -> Optional[Dict]:
        """Get POI by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pois WHERE poi_id = ?", (poi_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    
    # ========== PROXIMITY EVENTS ==========
    
    def log_proximity_event(
        self,
        user_id: str,
        event_type: str,
        location_id: Optional[str] = None,
        poi_id: Optional[str] = None,
        distance_meters: Optional[float] = None
    ) -> Dict:
        """
        Log a proximity event (arrival, departure, interaction, etc.)
        
        Args:
            user_id: Player ID
            event_type: "arrived", "departed", "interacted", "completed_quest"
            location_id: If event at a shop/location
            poi_id: If event at a POI
            distance_meters: Distance to location/POI
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO proximity_events 
            (user_id, location_id, poi_id, event_type, distance_meters)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, location_id, poi_id, event_type, distance_meters))
        
        event_id = cursor.lastrowid
        conn.commit()
        
        return {
            "event_id": event_id,
            "user_id": user_id,
            "event_type": event_type,
            "location_id": location_id,
            "poi_id": poi_id,
            "distance_meters": distance_meters,
            "timestamp": datetime.now().isoformat()
        }
    
    
    def get_player_proximity_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent proximity events for a player"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM proximity_events 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    
    # ========== INTERACTION DETECTION ==========
    
    def check_location_interaction(
        self,
        user_id: str,
        user_latitude: float,
        user_longitude: float,
        location_id: str
    ) -> bool:
        """Check if player is within interaction radius of location"""
        location = self.get_location(location_id)
        if not location:
            return False
        
        distance = haversine_distance(
            user_latitude, user_longitude,
            location['latitude'], location['longitude']
        )
        
        # Standard interaction radius: 50 meters
        return distance <= 50.0
    
    
    def check_poi_interaction(
        self,
        user_id: str,
        user_latitude: float,
        user_longitude: float,
        poi_id: str
    ) -> bool:
        """Check if player is within interaction radius of POI"""
        poi = self.get_poi(poi_id)
        if not poi:
            return False
        
        distance = haversine_distance(
            user_latitude, user_longitude,
            poi['latitude'], poi['longitude']
        )
        
        return distance <= poi['interaction_radius_meters']
    
    
    def get_interactable_locations(
        self,
        user_id: str,
        user_latitude: float,
        user_longitude: float,
        interaction_radius: float = 50.0
    ) -> List[Dict]:
        """Get all locations player can interact with from current position"""
        nearby = self.find_nearby_locations(
            user_latitude, user_longitude,
            radius_meters=interaction_radius * 2  # Look slightly further
        )
        
        return [
            {**loc, "distance_meters": dist}
            for loc, dist in nearby
            if dist <= interaction_radius
        ]
    
    
    def get_interactable_pois(
        self,
        user_id: str,
        user_latitude: float,
        user_longitude: float
    ) -> List[Dict]:
        """Get all POIs player can interact with from current position"""
        nearby = self.find_nearby_pois(user_latitude, user_longitude)
        
        return [
            {
                **poi, 
                "distance_meters": dist,
                "can_interact": dist <= poi['interaction_radius_meters']
            }
            for poi, dist in nearby
        ]
    
    
    # ========== LOCATION-BASED TRANSACTIONS ==========
    
    def update_location_balance(
        self,
        location_id: str,
        amount_change: float
    ) -> float:
        """
        Update location balance (for shop transactions).
        
        Args:
            location_id: Shop ID
            amount_change: Amount to add/subtract (+ or -)
        
        Returns:
            New balance
        
        Raises:
            ValueError: If insufficient funds or location not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Use row-level locking
        cursor.execute("""
            SELECT balance FROM locations WHERE location_id = ? FOR UPDATE
        """, (location_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Location {location_id} not found")
        
        current_balance = row[0]
        new_balance = current_balance + amount_change
        
        if new_balance < 0:
            raise ValueError(f"Insufficient location balance")
        
        cursor.execute("""
            UPDATE locations SET balance = ?, updated_at = CURRENT_TIMESTAMP
            WHERE location_id = ?
        """, (new_balance, location_id))
        
        conn.commit()
        return new_balance
    
    
    def verify_location_balance(self) -> Tuple[bool, float]:
        """Verify all locations have non-negative balance"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as bad_count FROM locations WHERE balance < 0
        """)
        
        bad_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(balance) FROM locations")
        total = cursor.fetchone()[0] or 0
        
        return bad_count == 0, total
