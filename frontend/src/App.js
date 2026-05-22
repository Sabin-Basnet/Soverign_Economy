import React, { useEffect, useRef, useState } from 'react';
import './App.css';

/**
 * GeoLedger Protocol Frontend
 * Real-time spatial commerce visualization with WebSocket sync
 * 
 * ARCHITECTURE:
 * - Canvas-based spatial rendering (hardware accelerated)
 * - WebSocket for movement broadcasts (server-filtered by proximity)
 * - REST API for transactions/escrow/analytics
 * - NO BUSINESS LOGIC - all validation server-side
 */

const API_BASE = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/ws";

const App = () => {
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const animationRef = useRef(null);
  
  // Game state
  const [userId, setUserId] = useState("BUYER_01");
  const [players, setPlayers] = useState({});
  const [balance, setBalance] = useState(0);
  const [metrics, setMetrics] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [transferAmount, setTransferAmount] = useState(0);

  // ============= WebSocket Setup =============
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`${WS_URL}/${userId}`);
      
      ws.onopen = () => {
        console.log(`[WS] Connected as ${userId}`);
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.event === "player_move") {
          setPlayers(prev => ({
            ...prev,
            [msg.data.user_id]: {
              x: msg.data.coordinates.x,
              y: msg.data.coordinates.y,
              bearing: msg.data.bearing || 0
            }
          }));
        }
      };
      
      ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        setIsConnected(false);
      };
      
      ws.onclose = () => {
        console.log("[WS] Disconnected");
        setIsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userId]);

  // ============= Balance Fetch =============
  useEffect(() => {
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

  // ============= Metrics Fetch =============
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/analytics/metrics`);
        const data = await res.json();
        setMetrics(data);
      } catch (err) {
        console.error("Metrics fetch failed:", err);
      }
    };
    
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Every 10s
    return () => clearInterval(interval);
  }, []);

  // ============= Player Movement =============
  const movePlayer = (dx, dy) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    // Get current position from players state
    const current = players[userId] || { x: 50, y: 50, bearing: 0 };
    const newX = Math.max(0, Math.min(canvas.width, current.x + dx));
    const newY = Math.max(0, Math.min(canvas.height, current.y + dy));
    const bearing = Math.atan2(dy, dx) * (180 / Math.PI);
    
    setPlayers(prev => ({
      ...prev,
      [userId]: { x: newX, y: newY, bearing }
    }));
    
    // Send to server
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        event: "player_move",
        payload: {
          user_id: userId,
          location_x: newX,
          location_y: newY,
          bearing: bearing
        }
      }));
    }
  };

  // ============= Keyboard Input =============
  useEffect(() => {
    const handleKeyPress = (e) => {
      const step = 5;
      if (e.key === "ArrowUp") movePlayer(0, -step);
      if (e.key === "ArrowDown") movePlayer(0, step);
      if (e.key === "ArrowLeft") movePlayer(-step, 0);
      if (e.key === "ArrowRight") movePlayer(step, 0);
    };
    
    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [players, userId]);

  // ============= Canvas Rendering =============
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    
    const render = () => {
      // Clear canvas
      ctx.fillStyle = "#1a1a2e";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw grid
      ctx.strokeStyle = "#444";
      ctx.lineWidth = 1;
      for (let i = 0; i < canvas.width; i += 50) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
      }
      for (let i = 0; i < canvas.height; i += 50) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(canvas.width, i);
        ctx.stroke();
      }
      
      // Draw all players
      Object.entries(players).forEach(([pid, pos]) => {
        const isCurrentPlayer = pid === userId;
        
        // Player circle
        ctx.fillStyle = isCurrentPlayer ? "#00ff00" : "#0088ff";
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, 10, 0, 2 * Math.PI);
        ctx.fill();
        
        // Player label
        ctx.fillStyle = "#fff";
        ctx.font = "12px Arial";
        ctx.textAlign = "center";
        ctx.fillText(pid, pos.x, pos.y - 20);
        
        // Bearing indicator (arrow)
        const angle = (pos.bearing * Math.PI) / 180;
        const arrowLength = 15;
        const endX = pos.x + arrowLength * Math.cos(angle);
        const endY = pos.y + arrowLength * Math.sin(angle);
        ctx.strokeStyle = isCurrentPlayer ? "#00ff00" : "#0088ff";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(pos.x, pos.y);
        ctx.lineTo(endX, endY);
        ctx.stroke();
      });
      
      // Draw shops (fixed anchors)
      ctx.fillStyle = "#ffaa00";
      ctx.fillRect(95, 95, 10, 10);
      ctx.fillStyle = "#fff";
      ctx.font = "11px Arial";
      ctx.textAlign = "center";
      ctx.fillText("SHOP_01", 100, 115);
      
      // Draw treasury
      ctx.fillStyle = "#ff6666";
      ctx.fillRect(10, 10, 15, 15);
      ctx.fillStyle = "#fff";
      ctx.font = "10px Arial";
      ctx.fillText("GOV", 17.5, 42);
      
      animationRef.current = requestAnimationFrame(render);
    };
    
    render();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [players, userId]);

  // ============= Transfer Handler =============
  const handleTransfer = async () => {
    if (!selectedTarget || transferAmount <= 0) {
      alert("Select target and amount");
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/api/v1/transfer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sender_id: userId,
          receiver_id: selectedTarget,
          amount: transferAmount
        })
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert(`Transfer successful!\n\nAmount: ${data.amount}\nTax: ${data.tax_amount}\nNew Balance: ${data.sender_new_balance}`);
        setBalance(data.sender_new_balance);
        setTransferAmount(0);
      } else {
        alert(`Transfer failed: ${data.detail}`);
      }
    } catch (err) {
      console.error("Transfer error:", err);
      alert("Transfer error: " + err.message);
    }
  };

  // ============= UI Render =============
  return (
    <div className="app">
      <header>
        <h1>🗺️ GeoLedger Protocol - Spatial Commerce Engine</h1>
        <div className="status">
          <span>
            {isConnected ? "✅ Connected" : "❌ Disconnected"}
          </span>
          <span>Balance: {balance.toFixed(2)} tokens</span>
          {metrics && (
            <span>
              Velocity: {metrics.velocity_of_money.toFixed(3)} | 
              Gini: {metrics.gini_coefficient.toFixed(3)}
            </span>
          )}
        </div>
      </header>

      <div className="container">
        <div className="canvas-container">
          <canvas
            ref={canvasRef}
            width={600}
            height={400}
            className="game-canvas"
            title="Arrow keys to move"
          />
          <div className="canvas-legend">
            <div>🟢 You</div>
            <div>🔵 Other Players</div>
            <div>🟠 Shops</div>
            <div>🔴 Treasury</div>
          </div>
        </div>

        <aside className="control-panel">
          <div className="section">
            <h3>Player Control</h3>
            <label>
              Current User:
              <select value={userId} onChange={(e) => setUserId(e.target.value)}>
                <option>BUYER_01</option>
                <option>BUYER_02</option>
                <option>COURIER_01</option>
                <option>MERCH_01</option>
              </select>
            </label>
            <p className="hint">Use arrow keys to move</p>
          </div>

          <div className="section">
            <h3>Transfer Funds</h3>
            <label>
              To:
              <select value={selectedTarget} onChange={(e) => setSelectedTarget(e.target.value)}>
                <option value="">-- Select --</option>
                <option>BUYER_02</option>
                <option>MERCH_01</option>
                <option>COURIER_01</option>
              </select>
            </label>
            <label>
              Amount:
              <input
                type="number"
                value={transferAmount}
                onChange={(e) => setTransferAmount(parseFloat(e.target.value))}
                min="0"
              />
            </label>
            <button onClick={handleTransfer} className="btn-primary">
              Send Transfer (2% VAT)
            </button>
          </div>

          <div className="section">
            <h3>Network Status</h3>
            <div className="status-box">
              <strong>WS Connection:</strong> {isConnected ? "Active" : "Offline"}
            </div>
            <div className="status-box">
              <strong>Nearby Players:</strong> {Object.keys(players).length}
            </div>
            {metrics && (
              <div className="status-box">
                <strong>Treasury:</strong> {metrics.treasury_balance.toFixed(0)}
                <br />
                <strong>Circulation:</strong> {metrics.total_circulation.toFixed(0)}
                <br />
                <strong>Active Players:</strong> {metrics.num_active_players}
              </div>
            )}
          </div>
        </aside>
      </div>

      <footer>
        <p>GeoLedger v1.0 | Zero-Sum Economy | Server-Side Validation</p>
      </footer>
    </div>
  );
};

export default App;