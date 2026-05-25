import React, { useEffect, useRef, useState, useCallback } from 'react';
import './MapComponent.css';

/**
 * Real-World GPS Map Component using Leaflet.js
 * 100% free - uses OpenStreetMap (no API key required)
 * 
 * Features:
 * - Real GPS tracking with fallback to manual placement
 * - Shop/POI markers on map
 * - Joystick-based movement
 * - Proximity detection and interaction UI
 */

const DHARAN_CENTER = { lat: 26.8124, lng: 87.2845 };
const DEFAULT_RADIUS = 5000; // meters
const API_BASE = "http://localhost:8000";

const MapComponent = ({ 
  userId, 
  onLocationUpdate, 
  isConnected 
}) => {
  const mapRef = useRef(null);
  const leafletMapRef = useRef(null);
  
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
  
  // Markers
  const playerMarkerRef = useRef(null);
  const locationMarkersRef = useRef({});
  const poiMarkersRef = useRef({});
  
  // Geolocation tracking
  const geolocationWatchId = useRef(null);

  // ============= Map Initialization =============
  useEffect(() => {
    if (leafletMapRef.current) return; // Already initialized

    // Create map using Leaflet
    const map = window.L.map(mapRef.current).setView([DHARAN_CENTER.lat, DHARAN_CENTER.lng], 15);

    // Add OpenStreetMap tile layer (100% free, no API key needed!)
    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    leafletMapRef.current = map;

    // Add initial player marker
    const playerMarker = window.L.circleMarker([DHARAN_CENTER.lat, DHARAN_CENTER.lng], {
      radius: 10,
      fillColor: '#4285F4',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9
    }).addTo(map);

    playerMarker.bindPopup(`<b>${userId}</b><br/>Your Position`);
    playerMarkerRef.current = playerMarker;

    // Allow map clicks for manual placement
    map.on('click', (e) => {
      updatePlayerLocation(e.latlng.lat, e.latlng.lng, null, 'manual');
    });
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

  // ============= Update Player Location =============
  const updatePlayerLocation = useCallback(
    async (latitude, longitude, accuracyMeters = null, source = 'manual') => {
      setPlayerLocation({ lat: latitude, lng: longitude });
      setAccuracy(accuracyMeters);

      // Update map
      if (playerMarkerRef.current && leafletMapRef.current) {
        playerMarkerRef.current.setLatLng([latitude, longitude]);
        leafletMapRef.current.panTo([latitude, longitude]);
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
    if (!leafletMapRef.current) return;

    const markerId = location.location_id;

    // Remove old marker if exists
    if (locationMarkersRef.current[markerId]) {
      leafletMapRef.current.removeLayer(locationMarkersRef.current[markerId]);
    }

    // Create new marker with appropriate icon color
    const markerColor = location.location_type === 'trading_post' ? '#FF6B6B' : '#51CF66';

    const marker = window.L.circleMarker([location.latitude, location.longitude], {
      radius: 8,
      fillColor: markerColor,
      color: '#fff',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(leafletMapRef.current);

    const popupContent = `
      <div style="padding: 5px;">
        <h4>${location.location_name}</h4>
        <p>${location.location_type}</p>
        <p>Distance: ${Math.round(location.distance_meters)}m</p>
      </div>
    `;

    marker.bindPopup(popupContent);
    marker.on('click', () => {
      setSelectedLocation(location);
    });

    locationMarkersRef.current[markerId] = marker;
  }, []);

  // ============= Add POI Marker =============
  const addPOIMarker = useCallback((poi) => {
    if (!leafletMapRef.current) return;

    const markerId = poi.poi_id;

    // Remove old marker if exists
    if (poiMarkersRef.current[markerId]) {
      leafletMapRef.current.removeLayer(poiMarkersRef.current[markerId]);
    }

    // Create new marker with appropriate icon color
    const poiColorMap = {
      landmark: '#FFD700',
      quest_hub: '#FF69B4',
      arena: '#FF4500',
      resource_spot: '#32CD32'
    };

    const markerColor = poiColorMap[poi.poi_type] || '#808080';

    const marker = window.L.circleMarker([poi.latitude, poi.longitude], {
      radius: 7,
      fillColor: markerColor,
      color: '#fff',
      weight: 1,
      opacity: 1,
      fillOpacity: 0.8
    }).addTo(leafletMapRef.current);

    const popupContent = `
      <div style="padding: 5px;">
        <h4>${poi.poi_name}</h4>
        <p>${poi.poi_type}</p>
        <p>Reward: ${poi.reward_amount} ${poi.reward_type}</p>
      </div>
    `;

    marker.bindPopup(popupContent);

    poiMarkersRef.current[markerId] = marker;
  }, []);

  // Joystick ref
  const joystickRef = useRef(null);
  const joystickStartPos = useRef(null);

  // ============= Joystick Movement =============
  const handleJoystickStart = useCallback((e) => {
    setJoystickActive(true);
    const rect = joystickRef.current.getBoundingClientRect();
    joystickStartPos.current = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2
    };
  }, []);

  const handleJoystickMove = useCallback(
    (e) => {
      if (!joystickActive || !playerLocation || !joystickStartPos.current) return;

      const clientX = e.clientX || (e.touches && e.touches[0]?.clientX) || 0;
      const clientY = e.clientY || (e.touches && e.touches[0]?.clientY) || 0;
      
      const deltaX = (clientX - joystickStartPos.current.x) / 500;
      const deltaY = (clientY - joystickStartPos.current.y) / 500;

      const newLat = playerLocation.lat - deltaY * 0.01;
      const newLng = playerLocation.lng + deltaX * 0.01;

      updatePlayerLocation(newLat, newLng, null, 'joystick');
    },
    [joystickActive, playerLocation, updatePlayerLocation]
  );

  const handleJoystickEnd = useCallback(() => {
    setJoystickActive(false);
    joystickStartPos.current = null;
  }, []);

  // Attach global mousemove listener when joystick is active
  useEffect(() => {
    if (!joystickActive) return;

    window.addEventListener('mousemove', handleJoystickMove);
    window.addEventListener('mouseup', handleJoystickEnd);
    window.addEventListener('touchmove', handleJoystickMove);
    window.addEventListener('touchend', handleJoystickEnd);

    return () => {
      window.removeEventListener('mousemove', handleJoystickMove);
      window.removeEventListener('mouseup', handleJoystickEnd);
      window.removeEventListener('touchmove', handleJoystickMove);
      window.removeEventListener('touchend', handleJoystickEnd);
    };
  }, [joystickActive, handleJoystickMove, handleJoystickEnd]);

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
      <div ref={mapRef} className="map-container" />

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
        ref={joystickRef}
        className={`joystick-zone ${joystickActive ? 'active' : ''}`}
        onMouseDown={handleJoystickStart}
        onTouchStart={handleJoystickStart}
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
