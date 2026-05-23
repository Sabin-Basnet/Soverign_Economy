import React, { useEffect, useRef, useState, useCallback } from 'react';
import './MapComponent.css';

/**
 * Real-World GPS Map Component
 * Integrates Google Maps API with location-based gameplay
 * 
 * Features:
 * - Real GPS tracking with fallback to manual placement
 * - Shop/POI markers on map
 * - Joystick-based movement
 * - Proximity detection and interaction UI
 */

const KATHMANDU_CENTER = { lat: 27.7128, lng: 85.3272 };
const DEFAULT_RADIUS = 5000; // meters
const API_BASE = "http://localhost:8000";

const MapComponent = ({ 
  userId, 
  onLocationUpdate, 
  isConnected 
}) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  
  // Location state
  const [playerLocation, setPlayerLocation] = useState(null);
  const [nearbyLocations, setNearbyLocations] = useState([]);
  const [nearbyPOIs, setNearbyPOIs] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [gpsEnabled, setGpsEnabled] = useState(false);
  const [accuracy, setAccuracy] = useState(null);
  
  // UI state
  const [showGeolocationPrompt, setShowGeolocationPrompt] = useState(true);
  const [joystickActive, setJoystickActive] = useState(false);
  const [interactionDistance, setInteractionDistance] = useState(null);
  
  // Markers
  const playerMarkerRef = useRef(null);
  const locationMarkersRef = useRef({});
  const poiMarkersRef = useRef({});
  
  // Geolocation tracking
  const geolocationWatchId = useRef(null);

  // ============= Map Initialization =============
  useEffect(() => {
    if (!window.google) {
      console.error("Google Maps not loaded. Add script to index.html");
      return;
    }

    if (mapInstanceRef.current) return; // Already initialized

    const map = new window.google.maps.Map(mapRef.current, {
      zoom: 15,
      center: KATHMANDU_CENTER,
      mapTypeControl: true,
      fullscreenControl: true,
      streetViewControl: false,
      styles: [
        {
          featureType: "poi",
          stylers: [{ visibility: "off" }]
        }
      ]
    });

    mapInstanceRef.current = map;

    // Add initial player marker
    const playerMarker = new window.google.maps.Marker({
      map: map,
      title: userId,
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 10,
        fillColor: "#4285F4",
        fillOpacity: 0.9,
        strokeColor: "#fff",
        strokeWeight: 2
      }
    });

    playerMarkerRef.current = playerMarker;
  }, [userId]);

  // ============= Geolocation Handler =============
  const startGeolocation = useCallback(() => {
    if (!navigator.geolocation) {
      alert("Geolocation not available in your browser");
      setShowGeolocationPrompt(false);
      return;
    }

    // Get current position first
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        updatePlayerLocation(latitude, longitude, accuracy, 'gps');
        setGpsEnabled(true);
        setShowGeolocationPrompt(false);

        // Watch position for continuous updates
        const watchId = navigator.geolocation.watchPosition(
          (position) => {
            const { latitude, longitude, accuracy } = position.coords;
            updatePlayerLocation(latitude, longitude, accuracy, 'gps');
          },
          (error) => {
            console.error("Geolocation error:", error);
            setGpsEnabled(false);
          },
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
          }
        );

        geolocationWatchId.current = watchId;
      },
      (error) => {
        console.error("Geolocation error:", error);
        alert("Could not access location. Using manual placement.");
        setShowGeolocationPrompt(false);
      }
    );
  }, []);

  // ============= Manual Location Placement =============
  const handleMapClick = useCallback((e) => {
    if (!mapInstanceRef.current) return;
    
    const lat = e.latLng.lat();
    const lng = e.latLng.lng();
    updatePlayerLocation(lat, lng, null, 'manual');
  }, []);

  // ============= Update Player Location =============
  const updatePlayerLocation = useCallback(
    async (latitude, longitude, accuracyMeters = null, source = 'manual') => {
      setPlayerLocation({ lat: latitude, lng: longitude });
      setAccuracy(accuracyMeters);

      // Update map
      if (playerMarkerRef.current && mapInstanceRef.current) {
        playerMarkerRef.current.setPosition({
          lat: latitude,
          lng: longitude
        });
        mapInstanceRef.current.panTo({
          lat: latitude,
          lng: longitude
        });
      }

      // Send to server
      if (onLocationUpdate) {
        onLocationUpdate({ latitude, longitude, source });
      }

      // Fetch nearby locations
      fetchNearbyLocations(latitude, longitude);
      fetchNearbyPOIs(latitude, longitude);
    },
    [onLocationUpdate]
  );

  // ============= Fetch Nearby Locations =============
  const fetchNearbyLocations = useCallback(async (latitude, longitude) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/locations/nearby`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude,
          longitude,
          radius_meters: DEFAULT_RADIUS
        })
      });

      const data = await res.json();
      setNearbyLocations(data.locations || []);

      // Add/update markers
      data.locations?.forEach(location => {
        addLocationMarker(location);
      });
    } catch (err) {
      console.error("Failed to fetch nearby locations:", err);
    }
  }, []);

  // ============= Fetch Nearby POIs =============
  const fetchNearbyPOIs = useCallback(async (latitude, longitude) => {
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/pois/nearby?latitude=${latitude}&longitude=${longitude}&radius_meters=${DEFAULT_RADIUS}`
      );

      const data = await res.json();
      setNearbyPOIs(data.pois || []);

      // Add/update markers
      data.pois?.forEach(poi => {
        addPOIMarker(poi);
      });
    } catch (err) {
      console.error("Failed to fetch nearby POIs:", err);
    }
  }, []);

  // ============= Add Location Marker =============
  const addLocationMarker = useCallback((location) => {
    if (!mapInstanceRef.current) return;

    const markerId = location.location_id;

    // Remove old marker if exists
    if (locationMarkersRef.current[markerId]) {
      locationMarkersRef.current[markerId].setMap(null);
    }

    // Create new marker
    const marker = new window.google.maps.Marker({
      map: mapInstanceRef.current,
      position: {
        lat: location.latitude,
        lng: location.longitude
      },
      title: location.location_name,
      icon: {
        path: window.google.maps.SymbolPath.ROUNDED_SQUARE,
        scale: 8,
        fillColor: location.location_type === 'trading_post' ? '#FF6B6B' : '#51CF66',
        fillOpacity: 0.8,
        strokeColor: '#fff',
        strokeWeight: 1
      }
    });

    marker.addListener('click', () => {
      setSelectedLocation(location);
      // Show info window
      if (!marker.infoWindow) {
        marker.infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 10px;">
              <h3>${location.location_name}</h3>
              <p>${location.location_type}</p>
              <p>Distance: ${Math.round(location.distance_meters)}m</p>
              <button onclick="console.log('Interact with location')">Shop</button>
            </div>
          `
        });
      }
      marker.infoWindow.open(mapInstanceRef.current, marker);
    });

    locationMarkersRef.current[markerId] = marker;
  }, []);

  // ============= Add POI Marker =============
  const addPOIMarker = useCallback((poi) => {
    if (!mapInstanceRef.current) return;

    const markerId = poi.poi_id;

    // Remove old marker if exists
    if (poiMarkersRef.current[markerId]) {
      poiMarkersRef.current[markerId].setMap(null);
    }

    // Create new marker
    const poiIconMap = {
      landmark: { color: '#FFD700' },
      quest_hub: { color: '#FF69B4' },
      arena: { color: '#FF4500' },
      resource_spot: { color: '#32CD32' }
    };

    const iconColor = poiIconMap[poi.poi_type]?.color || '#808080';

    const marker = new window.google.maps.Marker({
      map: mapInstanceRef.current,
      position: {
        lat: poi.latitude,
        lng: poi.longitude
      },
      title: poi.poi_name,
      icon: {
        path: window.google.maps.SymbolPath.BACKWARD_CLOSED_ARROW,
        scale: 8,
        fillColor: iconColor,
        fillOpacity: 0.8,
        strokeColor: '#fff',
        strokeWeight: 1
      }
    });

    marker.addListener('click', () => {
      if (!marker.infoWindow) {
        marker.infoWindow = new window.google.maps.InfoWindow({
          content: `
            <div style="padding: 10px;">
              <h3>${poi.poi_name}</h3>
              <p>${poi.poi_type}</p>
              <p>Reward: ${poi.reward_amount} ${poi.reward_type}</p>
            </div>
          `
        });
      }
      marker.infoWindow.open(mapInstanceRef.current, marker);
    });

    poiMarkersRef.current[markerId] = marker;
  }, []);

  // ============= Joystick Movement =============
  const handleJoystickStart = useCallback((e) => {
    setJoystickActive(true);
  }, []);

  const handleJoystickMove = useCallback(
    (e) => {
      if (!joystickActive || !playerLocation) return;

      const deltaLat = e.deltaY * 0.0001; // ~10m per 100px
      const deltaLng = e.deltaX * 0.0001;

      const newLat = playerLocation.lat + deltaLat;
      const newLng = playerLocation.lng + deltaLng;

      updatePlayerLocation(newLat, newLng, null, 'joystick');
    },
    [joystickActive, playerLocation, updatePlayerLocation]
  );

  const handleJoystickEnd = useCallback(() => {
    setJoystickActive(false);
  }, []);

  // Cleanup geolocation on unmount
  useEffect(() => {
    return () => {
      if (geolocationWatchId.current !== null) {
        navigator.geolocation.clearWatch(geolocationWatchId.current);
      }
    };
  }, []);

  return (
    <div className="map-component">
      {/* Geolocation Prompt */}
      {showGeolocationPrompt && (
        <div className="geolocation-prompt">
          <p>Allow access to your location for a better experience?</p>
          <button onClick={startGeolocation} className="btn-primary">
            Enable GPS
          </button>
          <button onClick={() => setShowGeolocationPrompt(false)} className="btn-secondary">
            Skip (Use Manual)
          </button>
        </div>
      )}

      {/* Map Container */}
      <div 
        ref={mapRef} 
        className="map-container"
        onClick={(e) => {
          if (e.target === mapRef.current) {
            const bounds = mapRef.current.getBoundingClientRect();
            const centerPoint = mapInstanceRef.current?.getCenter();
            if (centerPoint) {
              handleMapClick({ latLng: centerPoint });
            }
          }
        }}
      />

      {/* Player Info Panel */}
      <div className="player-info-panel">
        <h3>🎮 {userId}</h3>
        {playerLocation && (
          <div>
            <p>📍 {playerLocation.lat.toFixed(4)}, {playerLocation.lng.toFixed(4)}</p>
            {accuracy && <p>📡 Accuracy: {Math.round(accuracy)}m</p>}
            {gpsEnabled && <p style={{ color: '#51CF66' }}>✓ GPS Active</p>}
          </div>
        )}

        <div className="quick-stats">
          <p>Nearby Shops: {nearbyLocations.length}</p>
          <p>Nearby POIs: {nearbyPOIs.length}</p>
        </div>

        {selectedLocation && (
          <div className="location-detail">
            <h4>{selectedLocation.location_name}</h4>
            <p>{selectedLocation.location_type}</p>
            <p>Distance: {Math.round(selectedLocation.distance_meters)}m</p>
            <button className="btn-interact">Enter Shop</button>
          </div>
        )}
      </div>

      {/* Joystick/Drag Zone */}
      <div
        className={`joystick-zone ${joystickActive ? 'active' : ''}`}
        onMouseDown={handleJoystickStart}
        onMouseMove={handleJoystickMove}
        onMouseUp={handleJoystickEnd}
        onMouseLeave={handleJoystickEnd}
        title="Click and drag to move (or use GPS)"
      >
        {joystickActive && <div className="joystick-indicator">↔️ Moving...</div>}
      </div>

      {/* Location List Sidebar */}
      <div className="locations-sidebar">
        <h4>🏪 Nearby Shops ({nearbyLocations.length})</h4>
        {nearbyLocations.slice(0, 5).map(loc => (
          <div
            key={loc.location_id}
            className="location-item"
            onClick={() => setSelectedLocation(loc)}
          >
            <p className="location-name">{loc.location_name}</p>
            <p className="location-distance">{Math.round(loc.distance_meters)}m away</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MapComponent;
