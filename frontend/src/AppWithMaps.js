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
      {/* Full-screen Map */}
      <MapComponent
        userId={userId}
        onLocationUpdate={handleLocationUpdate}
        isConnected={true}
      />

      {/* Top UI Bar */}
      <div className="app-header">
        <div className="player-info">
          <h2>🎮 {userId}</h2>
          <div className="balance-display">
            <span className="balance-label">Wallet:</span>
            <span className="balance-amount">{balance.toFixed(2)}</span>
            <span className="token-symbol">⚡</span>
          </div>
        </div>

        {currentLocation && (
          <div className="location-info">
            <span>📍 {currentLocation.latitude.toFixed(4)}, {currentLocation.longitude.toFixed(4)}</span>
            <span className="location-source">({currentLocation.source})</span>
          </div>
        )}
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
                max={balance}
                step="10"
              />

              <div className="transfer-summary">
                <p>Amount: {transferAmount.toFixed(2)} ⚡</p>
                <p>Tax (2%): {(transferAmount * 0.02).toFixed(2)} ⚡</p>
                <p className="total">
                  Total: {(transferAmount * 1.02).toFixed(2)} ⚡
                </p>
              </div>

              <button
                className="btn-buy"
                onClick={() =>
                  handleTransfer(selectedShop.owner_id, transferAmount)
                }
                disabled={transferAmount <= 0 || transferAmount * 1.02 > balance}
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
              ? `${currentLocation.latitude.toFixed(4)}, ${currentLocation.longitude.toFixed(4)}`
              : 'Not set'}
          </p>
          <p>Balance: {balance.toFixed(2)}</p>
        </div>
      )}
    </div>
  );
};

export default AppWithMaps;
