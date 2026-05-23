"""
Geo-spatial utilities for real-world location-based game.
Handles distance calculations, proximity detection, and coordinate conversions.
"""

import math
from typing import Tuple, List, Dict
from dataclasses import dataclass


@dataclass
class Coordinate:
    """GPS coordinate representation."""
    latitude: float
    longitude: float
    
    def __iter__(self):
        """Allow tuple unpacking: lat, lng = coord"""
        return iter((self.latitude, self.longitude))


def haversine_distance(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """
    Calculate great-circle distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lng1: First coordinate (degrees)
        lat2, lng2: Second coordinate (degrees)
    
    Returns:
        Distance in meters
    
    Reference:
        https://en.wikipedia.org/wiki/Haversine_formula
    """
    R = 6371000  # Earth radius in meters
    
    # Convert to radians
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lng2 - lng1)
    
    # Haversine formula
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def is_within_radius(
    user_lat: float, user_lng: float,
    target_lat: float, target_lng: float,
    radius_meters: float
) -> bool:
    """
    Check if user is within radius of target coordinate.
    
    Args:
        user_lat, user_lng: User's current position
        target_lat, target_lng: Target location
        radius_meters: Interaction radius
    
    Returns:
        True if user is within radius
    """
    distance = haversine_distance(user_lat, user_lng, target_lat, target_lng)
    return distance <= radius_meters


def find_nearby_locations(
    user_lat: float, user_lng: float,
    locations: List[Dict],
    radius_meters: float = 1000.0
) -> List[Tuple[Dict, float]]:
    """
    Find all locations within radius of user position.
    
    Args:
        user_lat, user_lng: User's current position
        locations: List of dicts with 'latitude', 'longitude', and other fields
        radius_meters: Search radius
    
    Returns:
        List of (location, distance_meters) sorted by distance
    """
    results = []
    
    for location in locations:
        distance = haversine_distance(
            user_lat, user_lng,
            location['latitude'], location['longitude']
        )
        if distance <= radius_meters:
            results.append((location, distance))
    
    # Sort by distance (closest first)
    results.sort(key=lambda x: x[1])
    return results


def bearing_between_points(
    lat1: float, lng1: float,
    lat2: float, lng2: float
) -> float:
    """
    Calculate initial bearing between two coordinates.
    
    Returns:
        Bearing in degrees (0-360, where 0=North, 90=East)
    """
    φ1 = math.radians(lat1)
    φ2 = math.radians(lat2)
    Δλ = math.radians(lng2 - lng1)
    
    y = math.sin(Δλ) * math.cos(φ2)
    x = math.cos(φ1) * math.sin(φ2) - math.sin(φ1) * math.cos(φ2) * math.cos(Δλ)
    
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360


def destination_from_bearing(
    lat: float, lng: float,
    bearing_degrees: float,
    distance_meters: float
) -> Tuple[float, float]:
    """
    Calculate destination coordinate given starting point, bearing, and distance.
    
    Useful for joystick-based movement.
    
    Args:
        lat, lng: Starting coordinate
        bearing_degrees: Direction (0=North, 90=East, etc.)
        distance_meters: Distance to travel
    
    Returns:
        (new_latitude, new_longitude)
    """
    R = 6371000  # Earth radius in meters
    
    φ1 = math.radians(lat)
    λ1 = math.radians(lng)
    bearing_rad = math.radians(bearing_degrees)
    
    # Angular distance in radians
    δ = distance_meters / R
    
    φ2 = math.asin(
        math.sin(φ1) * math.cos(δ) +
        math.cos(φ1) * math.sin(δ) * math.cos(bearing_rad)
    )
    
    λ2 = λ1 + math.atan2(
        math.sin(bearing_rad) * math.sin(δ) * math.cos(φ1),
        math.cos(δ) - math.sin(φ1) * math.sin(φ2)
    )
    
    return (math.degrees(φ2), math.degrees(λ2))


def bounding_box(
    lat: float, lng: float,
    radius_meters: float
) -> Dict[str, float]:
    """
    Calculate bounding box for a circular region.
    
    Useful for database queries (e.g., WHERE lat BETWEEN min_lat AND max_lat).
    
    Args:
        lat, lng: Center coordinate
        radius_meters: Radius of circle
    
    Returns:
        Dict with 'min_lat', 'max_lat', 'min_lng', 'max_lng'
    """
    R = 6371000  # Earth radius in meters
    
    # 1 degree of latitude is approximately 111,111 meters
    lat_delta = math.degrees(radius_meters / R)
    
    # Longitude delta depends on latitude
    lng_delta = math.degrees(radius_meters / (R * math.cos(math.radians(lat))))
    
    return {
        'min_lat': lat - lat_delta,
        'max_lat': lat + lat_delta,
        'min_lng': lng - lng_delta,
        'max_lng': lng + lng_delta,
    }


# Default Kathmandu, Nepal coordinates for testing
KATHMANDU_CENTER = Coordinate(27.7128, 85.3272)
DEFAULT_INTERACTION_RADIUS = 100.0  # meters
DEFAULT_SEARCH_RADIUS = 5000.0  # 5 km
