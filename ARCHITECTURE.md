# GeoLedger Protocol - Architecture & Design Document

## System Overview

GeoLedger is a **decoupled, event-driven multiplayer state machine** that enforces absolute scarcity economics through ACID database constraints and server-side validation.

```
User Input (Untrusted)
       ↓
  Frontend (React)
       ↓
  REST/WebSocket API
       ↓
  Business Logic Layer
       ├─→ BankingEngine (Phase 2)
       ├─→ SpatialManager (Phase 3)
       └─→ AnalyticsEngine (Phase 4)
       ↓
  Database Layer (SQLite)
  ├─ CHECK constraints
  ├─ Row-level locking
  └─ ACID transactions
       ↓
  Persistent State (economy.db)
```

---

## Core Invariants

### 1. Zero-Sum Invariant

**Mathematical Definition:**
$$\sum_{i=1}^{n} \text{balance}_i = 1,000,000 \text{ (constant)}$$

**Enforcement Layers:**

| Layer | Mechanism |
|-------|-----------|
| Database | `CHECK(balance >= 0)` constraint on all wallet rows |
| Transaction | `SELECT FOR UPDATE` row-level locking |
| Application | Pydantic validators + explicit amount calculations |
| Monitoring | Periodic `verify_zero_sum_invariant()` health check |

**Example Transaction Flow:**
```sql
-- TRANSFER 100 tokens from BUYER_01 to MERCH_01 (2% tax)

BEGIN TRANSACTION (SERIALIZABLE);
  
  -- LOCK PHASE: Acquire locks on all affected rows
  SELECT balance FROM users WHERE user_id = 'BUYER_01' FOR UPDATE;  
  -- Result: 29,900 (locked)
  
  SELECT balance FROM users WHERE user_id = 'MERCH_01' FOR UPDATE;
  -- Result: 150,000 (locked)
  
  SELECT balance FROM users WHERE user_id = 'GOV_01' FOR UPDATE;
  -- Result: 800,000 (locked)
  
  -- VALIDATION PHASE
  tax_amount = 100 * 0.02 = 2.0
  total_debit = 100 + 2.0 = 102.0
  if (29,900 >= 102.0) ✓ PASS
  
  -- MUTATION PHASE (atomic)
  UPDATE users SET balance = 29,900 - 102.0 = 29,798.0 
    WHERE user_id = 'BUYER_01';
  UPDATE users SET balance = 150,000 + 100.0 = 150,100.0 
    WHERE user_id = 'MERCH_01';
  UPDATE users SET balance = 800,000 + 2.0 = 800,002.0 
    WHERE user_id = 'GOV_01';
  
  -- AUDIT PHASE
  INSERT INTO transactions (sender_id, receiver_id, amount, tx_type)
    VALUES ('BUYER_01', 'MERCH_01', 100.0, 'purchase');
  INSERT INTO audit_log (event_type, sender_id, receiver_id, amount)
    VALUES ('velocity_tax', 'BUYER_01', 'GOV_01', 2.0);

COMMIT;

-- Final state verification
SELECT SUM(balance) FROM users;
-- Result: 1,000,000.0 ✓ INVARIANT MAINTAINED
```

**Why Locking is Critical:**

Without `SELECT FOR UPDATE`, race condition possible:

```
Timeline:
T1: BUYER_01 reads balance: 100
T2: BUYER_01 reads balance: 100 (same thread!)
T1: Sends 50 to MERCH_01
T2: Sends 50 to MERCH_01
Result: BUYER_01 balance: -50 (INVARIANT VIOLATED!)
```

With locking:
```
T1: SELECT FOR UPDATE on BUYER_01
T2: BLOCKED (waiting for lock release)
T1: UPDATE balance, COMMIT, release lock
T2: Acquires lock, reads new balance: 50
T2: Can only send 50 (respects new balance)
Result: BUYER_01 balance: 0 ✓
```

---

### 2. Spatial Partitioning Invariant

**Principle:** Minimize bandwidth by broadcasting only to nearby players.

**Implementation:**

```python
def get_nearby_players(user_id, radius=100.0):
    """Find all players within Euclidean distance"""
    
    my_pos = query_position(user_id)  # (x, y)
    
    all_positions = query_all_positions()
    
    nearby = {}
    for other_id, other_pos in all_positions.items():
        distance = sqrt((other_pos.x - my_pos.x)² + (other_pos.y - my_pos.y)²)
        if distance <= radius:
            nearby[other_id] = other_pos
    
    return nearby

async def broadcast_to_nearby(event: PlayerMoveEvent):
    """Send update only to connected players within range"""
    
    nearby = get_nearby_players(event.user_id)
    
    for nearby_user_id in nearby.keys():
        if nearby_user_id in active_connections:
            await active_connections[nearby_user_id].send_json(event)
```

**Performance Benefit:**

- **Global broadcast** (❌): $O(n)$ messages per movement
- **Spatial partition** (✅): $O(k)$ messages per movement, where $k << n$

For 10,000 players:
- Global: 10,000 messages/second (unusable)
- Spatial (radius=100, density=5): ~50 messages/second (feasible)

---

### 3. Velocity Tax Invariant

**Tax Formula:**
$$T_{\text{tax}} = T_{\text{amount}} \times 0.02$$

**Atomic Routing:**
Tax must reach Treasury in **same transaction** as principal:

```python
# ❌ WRONG (race condition possible)
update_sender(-amount)
update_receiver(+amount)
# [TIME GAP - system could crash]
update_treasury(+tax)

# ✅ CORRECT (all-or-nothing)
BEGIN
  update_sender(-(amount + tax))
  update_receiver(+amount)
  update_treasury(+tax)
  INSERT audit_log
COMMIT
```

**Treasury Address:** `GOV_01`

**Tax Destinations:**
| Event | Destination |
|-------|-------------|
| P2P Transfer | State_Treasury |
| Escrow Creation | State_Treasury (locked) |
| Escrow Completion | State_Treasury (released) |
| Every transaction | 2% VAT |

---

## Data Schema Architecture

### Users Table (Core Ledger)
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    balance REAL NOT NULL CHECK(balance >= 0),
    user_type TEXT,  -- 'player', 'merchant', 'government'
    created_at DATETIME
);
```

**Constraint Analysis:**
- `PRIMARY KEY`: Prevents duplicate wallets
- `CHECK(balance >= 0)`: Database-level enforcement (cannot be bypassed)
- `user_type`: Enables role-based queries (e.g., "sum balance by merchant")

### Transactions Table (Audit Trail)
```sql
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    tx_type TEXT,  -- 'transfer', 'purchase', 'tax'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(sender_id) REFERENCES users(user_id),
    FOREIGN KEY(receiver_id) REFERENCES users(user_id)
);
```

**Immutability:** No UPDATE/DELETE possible (append-only log)

### Escrow Table (Multi-State Contracts)
```sql
CREATE TABLE escrow (
    escrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    courier_id TEXT,
    state TEXT,  -- 'locked', 'in_transit', 'completed'
    amount REAL NOT NULL CHECK(amount > 0),
    tax_amount REAL NOT NULL CHECK(tax_amount >= 0),
    delivery_threshold REAL DEFAULT 1.0,
    created_at DATETIME,
    completed_at DATETIME,
    FOREIGN KEY(buyer_id) REFERENCES users(user_id),
    FOREIGN KEY(seller_id) REFERENCES users(user_id),
    FOREIGN KEY(courier_id) REFERENCES users(user_id)
);
```

**State Machine:**
```
[LOCKED] → [IN_TRANSIT] → [COMPLETED]
            (escrow funds held)
   ↓
[CANCELLED] (funds refunded)
```

### Player Positions Table (Spatial State)
```sql
CREATE TABLE player_positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL UNIQUE,
    location_x REAL NOT NULL,
    location_y REAL NOT NULL,
    bearing REAL DEFAULT 0.0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);
```

**Spatial Index Optimization (TODO):**
```sql
-- For faster nearby-player queries
CREATE INDEX idx_positions_location ON player_positions(location_x, location_y);

-- Or use R-tree index (SQLite)
CREATE VIRTUAL TABLE rtree_positions USING rtree(
  id,        -- rowid
  minx, maxx, -- location_x bounds
  miny, maxy  -- location_y bounds
);
```

---

## API Contract & Message Formats

### REST API Design

**Base URL:** `http://localhost:8000`

**Content-Type:** `application/json`

**Error Handling:**
```json
{
  "detail": "Insufficient balance. Have: 50, Need: 102 (amount + tax)"
}
// HTTP 400 Bad Request
```

### WebSocket Message Protocol

**Connection URL:** `ws://localhost:8000/ws/{user_id}`

**Incoming Messages (Client → Server):**

```typescript
interface PlayerMoveEvent {
  event: "player_move";
  payload: {
    user_id: string;
    location_x: number;
    location_y: number;
    bearing: number;  // degrees 0-360
  };
}

interface PingEvent {
  event: "ping";
}
```

**Outgoing Messages (Server → Client):**

```typescript
interface PlayerMoveUpdate {
  event: "player_move";
  data: {
    user_id: string;
    coordinates: { x: number; y: number };
    bearing: number;
    timestamp: string;  // ISO 8601
  };
}

interface PongEvent {
  event: "pong";
}
```

---

## Business Logic Layers

### Layer 1: BankingEngine (bank.py)

**Responsibilities:**
- Safe fund transfers with ACID guarantees
- Velocity tax calculation and routing
- Escrow state management
- Zero-sum invariant verification

**Key Methods:**

```python
def transfer(req: TransferRequest) -> TransferResponse:
    """
    Atomically transfer funds with velocity tax
    
    Ensures:
    - Sender has sufficient balance (amount + tax)
    - Tax is routed to treasury in same transaction
    - All-or-nothing semantics (ROLLBACK on any error)
    - Transaction logged to audit trail
    """

def create_escrow(req: EscrowCreateRequest) -> EscrowResponse:
    """
    Lock funds in escrow pending delivery
    
    Ensures:
    - Buyer balance is frozen (SELECT FOR UPDATE)
    - Tax amount pre-calculated and locked
    - Escrow ID returned for tracking
    """

def complete_escrow(req: EscrowCompleteRequest) -> EscrowResponse:
    """
    Release escrow upon delivery confirmation
    
    Ensures:
    - Courier is within delivery_threshold of buyer
    - Euclidean distance validated
    - Funds released to seller and tax to treasury
    - Escrow marked completed with timestamp
    """
```

### Layer 2: SpatialManager (spatial.py)

**Responsibilities:**
- Maintain real-time player position index
- Calculate Euclidean distances
- Partition players into sectors
- Broadcast movement events to nearby clients

**Key Methods:**

```python
def register_connection(user_id: str, websocket):
    """Store active WebSocket connection"""

def get_nearby_players(user_id, radius=100.0) -> Dict[str, Tuple]:
    """
    Return all players within radius using:
    distance = sqrt((dx)² + (dy)²)
    
    O(n) scan but typically n << total players
    (can optimize with spatial index)
    """

async def broadcast_to_nearby(event: PlayerMoveEvent):
    """
    Send movement event only to players within radius
    
    Reduces message volume: O(k) instead of O(n)
    """
```

### Layer 3: AnalyticsEngine (analytics.py)

**Responsibilities:**
- Calculate system-wide economic metrics
- Generate wealth distribution reports
- Verify zero-sum invariant
- Provide audit trail access

**Key Metrics:**

#### Velocity of Money
$$V = \frac{\sum_{i=1}^{m} T_i}{\sum_{j=1}^{n} B_j}$$

Where:
- $T_i$ = transactions in time window
- $B_j$ = current balances
- Higher V = more economic activity

#### Gini Coefficient
$$G = \frac{2 \sum_{i=1}^{n} i \cdot b_i}{n \sum_{i=1}^{n} b_i} - \frac{n+1}{n}$$

Where:
- $b_i$ = sorted balance (ascending)
- $G \in [0, 1]$ (0 = equality, 1 = inequality)

---

## Concurrency & Isolation

### Transaction Isolation Levels

**SQLite Default: DEFERRED**

```python
conn.execute("PRAGMA transaction_mode = IMMEDIATE")
```

**Isolation Guarantees:**

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Race Conditions |
|-------|-------------|----------------------|---------------|-----------------|
| SERIALIZABLE | ✓ | ✓ | ✓ | ✓ |
| REPEATABLE READ | ✓ | ✓ | ✗ | ✗ |
| READ COMMITTED | ✓ | ✗ | ✗ | ✗ |
| READ UNCOMMITTED | ✗ | ✗ | ✗ | ✗ |

**GeoLedger uses:**
- `SELECT FOR UPDATE` (row locks)
- Application-level transaction boundaries
- Explicit ROLLBACK on any error

### Connection Pool Strategy

```python
@contextmanager
def get_connection():
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA transaction_mode = IMMEDIATE")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**For Production (PostgreSQL):**
```python
from psycopg2.pool import SimpleConnectionPool

pool = SimpleConnectionPool(1, 20, "postgresql://...")

@contextmanager
def get_connection():
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
```

---

## Frontend Architecture

### React Component Hierarchy
```
App
├── Canvas (Spatial Visualization)
│   ├── Grid Rendering
│   ├── Player Circle (bearing indicator)
│   └── Shop/Treasury Anchors
├── ControlPanel
│   ├── PlayerControl (user select, movement hints)
│   ├── TransferForm (target, amount, send button)
│   └── NetworkStatus (connection, nearby players, metrics)
└── Header/Footer (status display)
```

### State Management
```javascript
const [userId, setUserId] = useState("BUYER_01");
const [players, setPlayers] = useState({});  // {user_id: {x, y, bearing}}
const [balance, setBalance] = useState(0);
const [isConnected, setIsConnected] = useState(false);
```

### WebSocket Integration
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.event === "player_move") {
    setPlayers(prev => ({
      ...prev,
      [msg.data.user_id]: {
        x: msg.data.coordinates.x,
        y: msg.data.coordinates.y,
        bearing: msg.data.bearing
      }
    }));
  }
};
```

**CRITICAL:** No validation in frontend. Server is source of truth.

---

## Error Handling Strategy

### Database Errors (Abort Transaction)
```python
try:
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", ...)
except sqlite3.IntegrityError as e:
    # CHECK constraint violated
    conn.rollback()
    raise ValueError("Zero-sum violation detected")
except sqlite3.OperationalError as e:
    # Database locked
    conn.rollback()
    raise RuntimeError("Database transaction timeout")
```

### API Errors (HTTP Codes)
| Scenario | Code | Message |
|----------|------|---------|
| Invalid amount (≤ 0) | 422 | Validation error |
| User not found | 404 | User not found |
| Insufficient balance | 400 | Insufficient balance |
| Escrow not found | 404 | Escrow not found |
| Courier too far | 400 | Courier too far from buyer |
| Server error | 500 | Internal server error |

### Client Resilience
```javascript
try {
  const res = await fetch(`/api/v1/transfer`, {
    method: "POST",
    body: JSON.stringify(transferRequest)
  });
  if (!res.ok) {
    const error = await res.json();
    alert(`Transfer failed: ${error.detail}`);
  }
} catch (err) {
  alert(`Network error: ${err.message}`);
}
```

---

## Security Model

### Defense-in-Depth

**Layer 1: Input Validation**
- Pydantic models enforce type safety
- Amount fields use `gt=0` (greater than zero)
- ID fields minimum length
- No raw string interpolation in SQL

**Layer 2: Database Constraints**
- PRIMARY KEY prevents duplicate wallets
- CHECK(balance >= 0) prevents overdrafts
- FOREIGN KEY enforces referential integrity
- NOT NULL on critical fields

**Layer 3: Application Logic**
- Row-level locking prevents race conditions
- Explicit transaction boundaries
- Complete ROLLBACK on any error
- No silent failures

**Layer 4: Frontend Validation**
- HTML5 input validation (visual only)
- JavaScript type checking (not security)
- Client-side calculations for display only

### Attack Vectors & Mitigations

| Attack | Vector | Mitigation |
|--------|--------|-----------|
| Double-spend | Direct DB access | CHECK constraints + ROW locks |
| Race condition | Concurrent transfers | SELECT FOR UPDATE |
| SQL injection | User input | Parameterized queries |
| Tax evasion | Modified frontend | Server-side tax calculation |
| Balance manipulation | XSS | No business logic in frontend |
| DDoS | Many connections | Rate limiting (TODO) |

---

## Deployment & Scalability

### Single-Server Deployment
- ✅ SQLite for data persistence
- ✅ FastAPI with Uvicorn
- ✅ In-memory WebSocket connections
- ✅ Suitable for < 100 concurrent players

### Multi-Server Deployment (TODO)
- PostgreSQL for shared state
- Redis for WebSocket routing
- Load balancer (nginx) for HTTP
- Message broker (RabbitMQ) for events

```
[Load Balancer]
     ↓ ↓ ↓
[Server1] [Server2] [Server3]
     ↓ ↓ ↓
  [PostgreSQL]
     ↓
  [Redis Cache]
```

---

**Version**: 1.0.0  
**Last Updated**: May 22, 2026
