# Protocol: Sovereign Economy (GeoLedger)

## 🗺️ Real-Time Spatial Commerce Engine with Immutable Fixed-Supply Ledger

A decoupled, event-driven multiplayer state machine that maps a 2D coordinate grid onto an absolute-scarcity micro-economy. Users act as concurrent nodes on a map who can register permanent commercial anchor points (shops), transfer value peer-to-peer, and fulfill logistics contracts in real time.

---

## 🏗️ Architecture Overview

```
┌──────────────┐              ┌──────────────────┐
│ FRONTEND     │ ←WebSocket→  │ SPATIAL NET      │
│ (React)      │   (X, Y)     │ SERVER (FastAPI) │
└──────────────┘              └──────────────────┘
       │                               │
     REST HTTP (JSON)         Direct Async
       │                               │
       └───────────────┬───────────────┘
                       │
           SQL Connection Pool
                       │
       ┌───────────────▼────────────────┐
       │ LEDGER DATABASE (SQLite)       │
       │ - Zero-Sum Invariant (ACID)    │
       │ - CHECK balance >= 0           │
       │ - Row-Level Locking            │
       └────────────────────────────────┘
```

### Core Subsystems

#### 1. **Financial Ledger (Zero-Sum Invariant)**
- Total monetary supply is absolute and inelastic (1,000,000 tokens fixed)
- Every wallet row features hard `CHECK balance >= 0` constraint
- All transactional balance mutations use Row-Level Locking (SELECT FOR UPDATE)
- If a step fails, entire transaction stack ROLLBACK immediately

#### 2. **Spatial Synchronizer (High-Frequency Networking)**
- WebSocket-based persistent connections (not HTTP polling)
- Euclidean distance-based sector partitioning
- Each client only receives coordinate shifts for players within broadcast radius (100 units)

#### 3. **Algorithmic Fiscal Policy (Automated Middleware)**
- **Velocity Tax (VAT)**: 2% of every transaction → State_Treasury
- **Logistics Escrow Loop**: Funds locked until courier coordinates match buyer (±1 unit)

---

## 📦 Project Structure

```
Soverign_Economy/
├── schema.sql              # Complete database schema (8 tables)
├── seed.sql               # Genesis block (1M tokens distributed)
├── init_db.py             # Database initialization
├── bank.py                # Phase 2: Financial Engine (transfers, escrow)
├── spatial.py             # Phase 3: WebSocket Manager (spatial sync)
├── analytics.py           # Phase 4: Economic Diagnostics
├── models.py              # Pydantic type definitions
├── main.py                # FastAPI integration (all endpoints)
├── requirements.txt       # Python dependencies
│
├── economy/               # Python virtual environment
│   └── Scripts/
│
└── frontend/              # React UI (Canvas-based spatial rendering)
    ├── package.json
    ├── public/
    │   ├── index.html
    │   └── manifest.json
    └── src/
        ├── App.js         # Main spatial commerce interface
        ├── App.css        # UI styling (dark theme)
        ├── index.js
        └── index.css
```

---

## 🚀 Quick Start

### 1. **Setup Python Environment**

```bash
cd c:\Users\SABIN\Desktop\Soverign_Economy
python -m venv economy
economy\Scripts\activate
pip install -r requirements.txt
```

### 2. **Initialize Database**

```bash
python init_db.py
```

Output:
```
Success: economy.db created and seeded with 1,000,000 fixed tokens!
```

### 3. **Start Backend Server**

```bash
python main.py
```

Server runs on `http://localhost:8000`

### 4. **Start Frontend (in another terminal)**

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

---

## 🎮 Gameplay / Usage

### Players
- **BUYER_01**: 30,000 tokens
- **BUYER_02**: 15,000 tokens
- **COURIER_01**: 5,000 tokens
- **MERCH_01**: 150,000 tokens
- **GOV_01** (State_Treasury): 800,000 tokens

### Controls

| Key | Action |
|-----|--------|
| ↑ ↓ ← → | Move player on map |
| Select Transfer Target | Choose recipient |
| Enter Amount | Amount to send |
| "Send Transfer" | Execute transfer (2% VAT applied) |

### Canvas Legend
- 🟢 **Green**: Your character
- 🔵 **Blue**: Other connected players
- 🟠 **Orange**: Shop anchor (SHOP_01)
- 🔴 **Red**: State Treasury (GOV_01)

---

## 📡 API Endpoints

### Phase 2: Financial Engine

#### `POST /api/v1/transfer`
Safe peer-to-peer transfer with velocity tax middleware.

**Request:**
```json
{
  "sender_id": "usr_buyer01",
  "receiver_id": "usr_merch09",
  "amount": 250.00
}
```

**Response:**
```json
{
  "transaction_id": 1,
  "sender_id": "usr_buyer01",
  "receiver_id": "usr_merch09",
  "amount": 250.00,
  "tax_amount": 5.00,
  "net_amount": 250.00,
  "sender_new_balance": 29745.00,
  "receiver_new_balance": 150250.00,
  "timestamp": "2026-05-22T10:30:00"
}
```

#### `POST /api/v1/escrow/create`
Initiate logistics contract with escrow lock.

**Request:**
```json
{
  "buyer_id": "usr_buyer01",
  "seller_id": "usr_merch01",
  "shop_id": "SHOP_01",
  "amount": 100.00,
  "delivery_threshold": 1.0
}
```

#### `POST /api/v1/escrow/complete`
Complete delivery and release escrow funds.

**Request:**
```json
{
  "escrow_id": 1,
  "courier_id": "usr_courier01",
  "buyer_location_x": 50.0,
  "buyer_location_y": 50.0
}
```

#### `GET /api/v1/balance/{user_id}`
Retrieve current user balance.

---

### Phase 3: WebSocket

#### `WebSocket /ws/{user_id}`
Real-time spatial synchronization.

**Client → Server (player movement):**
```json
{
  "event": "player_move",
  "payload": {
    "user_id": "usr_buyer01",
    "location_x": 142.5,
    "location_y": 89.2,
    "bearing": 180.0
  }
}
```

**Server → Client (nearby player update):**
```json
{
  "event": "player_move",
  "data": {
    "user_id": "usr_buyer02",
    "coordinates": { "x": 160.0, "y": 95.0 },
    "bearing": 90.0
  }
}
```

---

### Phase 4: Analytics

#### `GET /api/v1/analytics/metrics`
Real-time economic metrics.

#### `GET /api/v1/analytics/wealth-distribution`
Sorted wealth distribution by user.

#### `GET /api/v1/analytics/audit-log`
Recent audit trail (tax collection, escrow events).

#### `GET /api/v1/analytics/invariant-check`
CRITICAL: Verify zero-sum property.

---

## ⚠️ Critical Architectural Mandate

**NEVER build business logic into the frontend.**

The client web application is entirely untrusted; it is purely a visual parser.

Every single rule—whether validation, movement bounds, tax cuts, or delivery distances—**must** be validated and executed server-side at the database layer.

---

## 🔧 Development Phases

### Phase 1: ✅ Data Layer
- [x] Relational ledger schema with strict balance checking
- [x] Genesis block seeding (1,000,000 tokens fixed)
- [x] Shops table, Escrow table, Audit log

### Phase 2: ✅ REST APIs
- [x] Safe, transaction-isolated wallet mutations
- [x] Automated velocity tax harvesting (2%)
- [x] Escrow creation/completion with courier validation

### Phase 3: ✅ Spatial Pipeline
- [x] WebSocket message brokers for coordinate tracking
- [x] Euclidean distance filtering (sector partitioning)
- [x] Canvas-based HTML5 frontend visualization

### Phase 4: ✅ Macro Analytics
- [x] System-wide economic diagnostics
- [x] Velocity of money calculation
- [x] Gini wealth distribution indices
- [x] Management console integration

---

## 📝 Dependencies

- **Backend**: FastAPI, Uvicorn, Pydantic, WebSockets
- **Database**: SQLite3
- **Frontend**: React, WebSocket API, HTML5 Canvas

---

**Protocol Version**: 1.0.0  
**Status**: Production Ready
