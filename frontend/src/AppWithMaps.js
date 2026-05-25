import React, { useState, useRef, useCallback } from 'react';
import MapComponent from './MapComponent';
import './App.css';

/**
 * GeoLedger Protocol - Real-World GPS Edition
 * 
 * Main app component that orchestrates:
 * - Real-world location tracking (GPS/manual)
 * - Financial transactions (existing economy)
 * - Location-based interactions (shops, POIs)
 * - Multiplayer spatial sync
 */

const API_BASE = "http://localhost:8000";

const AppWithMaps = () => {
  const [userId, setUserId] = useState("PLAYER_001");
  const [balance, setBalance] = useState(0);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [selectedShop, setSelectedShop] = useState(null);
  const [showTransferUI, setShowTransferUI] = useState(false);
  const [transferAmount, setTransferAmount] = useState(0);
  const [joystickActive, setJoystickActive] = useState(false);
  const [joystickPos, setJoystickPos] = useState({ x: 0, y: 0 });
  const joystickRef = useRef(null);

  // ============= Location Update Handler =============
  const handleLocationUpdate = useCallback(
    async (locationData) => {
      setCurrentLocation(locationData);

      // Send position to backend
      try {
        const res = await fetch(`${API_BASE}/api/v1/player/position`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            latitude: locationData.latitude,
            longitude: locationData.longitude,
            accuracy_meters: locationData.accuracy_meters,
            source: locationData.source
          })
        });

        if (!res.ok) {
          console.error("Failed to update position");
        }
      } catch (err) {
        console.error("Position update error:", err);
      }
    },
    [userId]
  );

  // ============= Balance Fetch =============
  React.useEffect(() => {
    const fetchBalance = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/balance/${userId}`);
        const data = await res.json();
        setBalance(data.balance);
      } catch (err) {
        console.error("Balance fetch failed:", err);
      }
    };

    fetchBalance();
    const interval = setInterval(fetchBalance, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, [userId]);

  // ============= Joystick Handler =============
  const handleJoystickStart = useCallback((e) => {
    setJoystickActive(true);
  }, []);

  const handleJoystickMove = useCallback((e) => {
    if (!joystickActive || !joystickRef.current) return;

    const rect = joystickRef.current.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left - centerX;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top - centerY;

    const distance = Math.sqrt(x * x + y * y);
    const maxDistance = 40;
    const limitedX = distance > maxDistance ? (x / distance) * maxDistance : x;
    const limitedY = distance > maxDistance ? (y / distance) * maxDistance : y;

    setJoystickPos({ x: limitedX, y: limitedY });
  }, [joystickActive]);

  const handleJoystickEnd = useCallback(() => {
    setJoystickActive(false);
    setJoystickPos({ x: 0, y: 0 });
  }, []);

  React.useEffect(() => {
    if (joystickActive) {
      window.addEventListener('mousemove', handleJoystickMove);
      window.addEventListener('touchmove', handleJoystickMove);
      window.addEventListener('mouseup', handleJoystickEnd);
      window.addEventListener('touchend', handleJoystickEnd);
      return () => {
        window.removeEventListener('mousemove', handleJoystickMove);
        window.removeEventListener('touchmove', handleJoystickMove);
        window.removeEventListener('mouseup', handleJoystickEnd);
        window.removeEventListener('touchend', handleJoystickEnd);
      };
    }
  }, [joystickActive, handleJoystickMove, handleJoystickEnd]);

  // ============= Transaction Handler =============
  const handleTransfer = async (receiverId, amount) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/transfer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender_id: userId,
          receiver_id: receiverId,
          amount: amount
        })
      });

      if (res.ok) {
        const data = await res.json();
        console.log("Transfer successful:", data);
        setShowTransferUI(false);
        setTransferAmount(0);
        // Balance will auto-refresh
      } else {
        const error = await res.json();
        alert(`Transfer failed: ${error.detail}`);
      }
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  // ============= Shop Interaction =============
  const handleShopInteraction = useCallback(async (shop) => {
    setSelectedShop(shop);
    setShowTransferUI(true);
    setTransferAmount(100); // Default amount

    // Log proximity event
    try {
      await fetch(`${API_BASE}/api/v1/proximity-events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          location_id: shop.location_id,
          event_type: 'interacted',
          distance_meters: shop.distance_meters
        })
      });
    } catch (err) {
      console.error("Failed to log proximity event:", err);
    }
  }, [userId]);

  return (
    <div className="app-container">
      {/* Top Control Bar */}
      <div className="app-header">
        <div className="player-selector-panel">
          <label>🎮 Player:</label>
          <select 
            value={userId} 
            onChange={(e) => setUserId(e.target.value)}
            className="player-select"
          >
            <option>PLAYER_001</option>
            <option>PLAYER_002</option>
            <option>PLAYER_003</option>
            <option>MERCHANT_001</option>
          </select>
        </div>

        <div className="balance-panel">
          <div className="balance-display">
            <span className="balance-label">💰 Wallet:</span>
            <span className="balance-amount">{(balance || 0).toFixed(2)}</span>
            <span className="token-symbol">⚡</span>
          </div>
        </div>

        {currentLocation && (
          <div className="location-panel">
            <span>📍 {(currentLocation.latitude || 0).toFixed(4)}</span>
            <span>|</span>
            <span>{(currentLocation.longitude || 0).toFixed(4)}</span>
            <span className="location-source">({currentLocation.source})</span>
          </div>
        )}
      </div>

      {/* Main Content Area */}
      <div className="map-main-content">
        {/* Left Sidebar - Joystick */}
        <div className="left-sidebar">
          <div className="control-panel">
            <h3>🕹️ Movement</h3>
            <div 
              ref={joystickRef}
              className={`joystick-container ${joystickActive ? 'active' : ''}`}
              onMouseDown={handleJoystickStart}
              onTouchStart={handleJoystickStart}
            >
              <div className="joystick-outer">
                <div 
                  className="joystick-inner"
                  style={{
                    transform: `translate(${joystickPos.x}px, ${joystickPos.y}px)`
                  }}
                />
              </div>
              <p className="joystick-label">
                {joystickActive ? '↔️ Moving...' : 'Drag to move'}
              </p>
            </div>
          </div>

          {currentLocation && (
            <div className="info-panel">
              <h3>📍 Location</h3>
              <div className="info-item">
                <span className="label">Latitude:</span>
                <span className="value">{(currentLocation.latitude || 0).toFixed(6)}</span>
              </div>
              <div className="info-item">
                <span className="label">Longitude:</span>
                <span className="value">{(currentLocation.longitude || 0).toFixed(6)}</span>
              </div>
              <div className="info-item">
                <span className="label">Source:</span>
                <span className={`value source-${currentLocation.source}`}>
                  {currentLocation.source}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Center - Map */}
        <div className="map-center">
          <MapComponent
            userId={userId}
            onLocationUpdate={handleLocationUpdate}
            isConnected={true}
          />
        </div>

        {/* Right Sidebar - Info Panel */}
        <div className="right-sidebar">
          <div className="quick-actions">
            <h3>⚡ Quick Actions</h3>
            <button className="action-btn transfer-btn">
              💳 Send Transfer
            </button>
            <button className="action-btn shop-btn">
              🏪 Find Shops
            </button>
            <button className="action-btn poi-btn">
              🎯 Nearby POIs
            </button>
          </div>

          {selectedShop ? (
            <div className="selected-shop-panel">
              <h3>{selectedShop.location_name}</h3>
              <div className="shop-details">
                <p><strong>Type:</strong> {selectedShop.location_type}</p>
                <p><strong>Distance:</strong> {Math.round(selectedShop.distance_meters)}m</p>
              </div>
              <button 
                className="btn-interact"
                onClick={() => handleShopInteraction(selectedShop)}
              >
                Interact
              </button>
            </div>
          ) : (
            <div className="no-selection">
              <p>Click a shop marker to interact</p>
            </div>
          )}
        </div>
      </div>

      {/* Shop Interaction Modal */}
      {showTransferUI && selectedShop && (
        <div className="modal-overlay" onClick={() => setShowTransferUI(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setShowTransferUI(false)}
            >
              ✕
            </button>

            <h3>🏪 {selectedShop.location_name}</h3>
            <p className="shop-type">{selectedShop.location_type}</p>
            <p className="shop-distance">
              Distance: {Math.round(selectedShop.distance_meters)}m
            </p>

            <div className="transfer-form">
              <label>Amount to Transfer:</label>
              <input
                type="number"
                value={transferAmount}
                onChange={(e) => setTransferAmount(parseFloat(e.target.value))}
                min="0"
                max={balance || 0}
                step="10"
              />

              <div className="transfer-summary">
                <p>Amount: {(transferAmount || 0).toFixed(2)} ⚡</p>
                <p>Tax (2%): {((transferAmount || 0) * 0.02).toFixed(2)} ⚡</p>
                <p className="total">
                  Total: {((transferAmount || 0) * 1.02).toFixed(2)} ⚡
                </p>
              </div>

              <button
                className="btn-buy"
                onClick={() =>
                  handleTransfer(selectedShop.owner_id, transferAmount)
                }
                disabled={transferAmount <= 0 || transferAmount * 1.02 > (balance || 0)}
              >
                Complete Purchase
              </button>

              <button
                className="btn-cancel"
                onClick={() => setShowTransferUI(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Debug Panel (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-panel">
          <h4>Debug Info</h4>
          <p>User: {userId}</p>
          <p>
            Location: {currentLocation
              ? `${(currentLocation.latitude || 0).toFixed(4)}, ${(currentLocation.longitude || 0).toFixed(4)}`
              : 'Not set'}
          </p>
          <p>Balance: {(balance || 0).toFixed(2)}</p>
        </div>
      )}
    </div>
  );
};

export default AppWithMaps;
