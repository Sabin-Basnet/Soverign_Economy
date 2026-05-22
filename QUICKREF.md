# GeoLedger Protocol - Quick Reference Guide

## 📁 File Structure at a Glance

| File | Purpose | Phase |
|------|---------|-------|
| `schema.sql` | 8-table database schema | 1 |
| `seed.sql` | Genesis block (1M tokens) | 1 |
| `init_db.py` | Create & seed database | 1 |
| `models.py` | Pydantic type definitions | 2-4 |
| `bank.py` | Transfer, escrow, VAT logic | 2 |
| `spatial.py` | WebSocket, proximity broadcasting | 3 |
| `analytics.py` | Metrics, audit logs, health checks | 4 |
| `main.py` | FastAPI server integration | 2-4 |
| `requirements.txt` | Python dependencies | Setup |
| `frontend/src/App.js` | React UI with Canvas | 3 |
| `frontend/src/App.css` | Styling (dark theme) | 3 |
| `README.md` | Project overview | Docs |
| `ARCHITECTURE.md` | Deep technical design | Docs |
| `DEPLOYMENT.md` | Operations guide | Ops |

---

## 🚀 Startup Commands

### Initial Setup (One-Time)
```bash
cd Soverign_Economy
python -m venv economy
economy\Scripts\activate
pip install -r requirements.txt
python init_db.py
```

### Development Startup (Two Terminals)

**Terminal 1 (Backend):**
```bash
economy\Scripts\activate
python main.py
# Server: http://localhost:8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install  # first time only
npm start
# Client: http://localhost:3000
```

---

## 🧪 Quick API Tests

### Get User Balance
```bash
curl http://localhost:8000/api/v1/balance/BUYER_01
```

### Transfer Funds (2% VAT automatic)
```bash
curl -X POST http://localhost:8000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{"sender_id":"BUYER_01","receiver_id":"BUYER_02","amount":100}'
```

### Check Zero-Sum Invariant
```bash
curl http://localhost:8000/api/v1/analytics/invariant-check
```

### Get Economic Metrics
```bash
curl http://localhost:8000/api/v1/analytics/metrics
```

### View Wealth Distribution
```bash
curl http://localhost:8000/api/v1/analytics/wealth-distribution
```

---

## 💾 Database Queries (SQLite)

### Connect to Database
```bash
sqlite3 economy.db
```

### View All Users & Balances
```sql
SELECT user_id, username, balance FROM users ORDER BY balance DESC;
```

### Verify Zero-Sum
```sql
SELECT 
  COUNT(*) as num_users,
  SUM(balance) as total_balance,
  (SUM(balance) = 1000000) as is_valid
FROM users;
```

### View Recent Transactions
```sql
SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 10;
```

### View Tax Audit Trail
```sql
SELECT * FROM audit_log WHERE event_type = 'velocity_tax' LIMIT 10;
```

### Check Escrow States
```sql
SELECT escrow_id, buyer_id, seller_id, state, amount FROM escrow;
```

### Player Positions
```sql
SELECT user_id, location_x, location_y, bearing FROM player_positions;
```

---

## 🎮 Test Scenarios

### Scenario 1: Simple P2P Transfer
```bash
# Before
curl http://localhost:8000/api/v1/balance/BUYER_01  # 30,000
curl http://localhost:8000/api/v1/balance/BUYER_02  # 15,000

# Transfer
curl -X POST http://localhost:8000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{"sender_id":"BUYER_01","receiver_id":"BUYER_02","amount":1000}'

# After
curl http://localhost:8000/api/v1/balance/BUYER_01  # 28,980 (1000+20 tax)
curl http://localhost:8000/api/v1/balance/BUYER_02  # 16,000
```

### Scenario 2: Insufficient Balance (Should Fail)
```bash
curl -X POST http://localhost:8000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{"sender_id":"BUYER_02","receiver_id":"BUYER_01","amount":100000}'
# Response: 400 Bad Request - Insufficient balance
```

### Scenario 3: Escrow Logistics
```bash
# 1. Create escrow
curl -X POST http://localhost:8000/api/v1/escrow/create \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id":"BUYER_01",
    "seller_id":"MERCH_01",
    "shop_id":"SHOP_01",
    "amount":500,
    "delivery_threshold":1.0
  }'
# Response: {"escrow_id": 1, "state": "locked", ...}

# 2. Complete escrow (courier at buyer location)
curl -X POST http://localhost:8000/api/v1/escrow/complete \
  -H "Content-Type: application/json" \
  -d '{
    "escrow_id":1,
    "courier_id":"COURIER_01",
    "buyer_location_x":50.0,
    "buyer_location_y":50.0
  }'
# Response: {"state": "completed", ...}
```

---

## 🔴 Common Issues & Fixes

### Issue: "Database locked"
```
sqlite3.OperationalError: database is locked
```
**Fix:**
```bash
# Kill existing processes
taskkill /F /IM python.exe
# Restart server
python main.py
```

### Issue: "Zero-sum invariant violated"
**Diagnosis:**
```sql
SELECT SUM(balance) FROM users;
-- Should be exactly 1,000,000
```
**Recovery:**
- Restore from `economy.db.backup`
- Or identify failed transaction in `audit_log` and manually reverse

### Issue: WebSocket "Cannot connect"
**Check:**
- Is backend running? `curl http://localhost:8000/`
- Is frontend pointing to correct WS_URL?
- Check browser console for errors

### Issue: Transfer takes > 1 second
**Optimize:**
```sql
-- Add index on sender_id
CREATE INDEX idx_transactions_sender ON transactions(sender_id);

-- Check lock contention
PRAGMA database_list;
```

---

## 📊 Key Numbers (Genesis State)

| User | Type | Balance | Percentage |
|------|------|---------|-----------|
| GOV_01 | Government | 800,000 | 80.0% |
| MERCH_01 | Merchant | 150,000 | 15.0% |
| BUYER_01 | Player | 30,000 | 3.0% |
| BUYER_02 | Player | 15,000 | 1.5% |
| COURIER_01 | Player | 5,000 | 0.5% |
| **TOTAL** | - | **1,000,000** | **100%** |

---

## 🧮 VAT Calculation Examples

| Scenario | Amount | Tax (2%) | Net to Receiver | Total Debit |
|----------|--------|----------|-----------------|------------|
| $100 transfer | $100 | $2.00 | $100 | $102.00 |
| $500 escrow | $500 | $10.00 | $500 | $510.00 |
| $1,000 transfer | $1,000 | $20.00 | $1,000 | $1,020.00 |

Tax always goes to `GOV_01` (State_Treasury).

---

## 🔧 Configuration Variables

### BankingEngine (`bank.py`)
```python
VELOCITY_TAX_RATE = 0.02        # 2% VAT
TREASURY_ID = "GOV_01"          # Tax recipient
DB_PATH = "economy.db"
```

### SpatialManager (`spatial.py`)
```python
BROADCAST_RADIUS = 100.0        # Euclidean units
DB_PATH = "economy.db"
```

### AnalyticsEngine (`analytics.py`)
```python
DB_PATH = "economy.db"
```

### Frontend (`App.js`)
```javascript
const API_BASE = "http://localhost:8000"
const WS_URL = "ws://localhost:8000/ws"
```

---

## 📈 Monitoring Commands

### System Health (One-Liner)
```bash
curl -s http://localhost:8000/health | jq '{status, zero_sum_valid, total_circulation}'
```

### Active Connections
```bash
curl -s http://localhost:8000 | jq .active_connections
```

### Recent Transactions
```bash
curl -s http://localhost:8000/api/v1/analytics/audit-log?limit=5 | jq '.[] | {event_type, amount, timestamp}'
```

### Gini Coefficient (Wealth Inequality)
```bash
curl -s http://localhost:8000/api/v1/analytics/metrics | jq .gini_coefficient
# Lower = more equal, Higher = more unequal
```

### Velocity of Money (Activity Level)
```bash
curl -s http://localhost:8000/api/v1/analytics/metrics | jq .velocity_of_money
# Higher = more active economy
```

---

## 📝 Debugging Checklist

- [ ] Database file exists: `ls economy.db`
- [ ] All 5 users created: `sqlite3 economy.db "SELECT COUNT(*) FROM users"`
- [ ] Total balance is 1M: `sqlite3 economy.db "SELECT SUM(balance) FROM users"`
- [ ] Backend running: `curl http://localhost:8000/`
- [ ] Frontend running: `curl http://localhost:3000/`
- [ ] WebSocket connects: Check browser DevTools Network tab
- [ ] Zero-sum invariant valid: `curl .../api/v1/analytics/invariant-check`

---

## 🎯 Next Steps for Development

1. **Add Rate Limiting** (`slowapi` library)
2. **Implement PostgreSQL** for horizontal scaling
3. **Add Redis Caching** for analytics queries
4. **Enable HTTPS/WSS** for production
5. **Add User Authentication** (JWT tokens)
6. **Create Admin Dashboard** (React component)
7. **Implement Persistent WebSocket Sessions** (Redis)
8. **Add Rollback/Undo Functionality** for transactions
9. **Implement Shop Management** endpoints
10. **Create Mobile Client** (React Native)

---

## 📚 Documentation Files

- **README.md** - Project overview & quick start
- **ARCHITECTURE.md** - Deep technical design & invariants
- **DEPLOYMENT.md** - Operations, monitoring, scaling
- **QUICKREF.md** ← You are here

---

**Last Updated**: May 22, 2026  
**Protocol Version**: 1.0.0
