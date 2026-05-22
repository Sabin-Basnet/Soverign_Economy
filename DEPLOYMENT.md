# GeoLedger Protocol - Deployment & Operations Guide

## 🚀 Production Deployment

### System Requirements
- **Python**: 3.8+
- **Node.js**: 14+
- **RAM**: 2GB minimum
- **Disk**: 100MB for database + dependencies
- **Network**: Unrestricted WebSocket connections

---

## 📋 Pre-Deployment Checklist

- [ ] Python environment configured
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized (`python init_db.py`)
- [ ] Frontend dependencies installed (`cd frontend && npm install`)
- [ ] Zero-sum invariant verified: `curl http://localhost:8000/api/v1/analytics/invariant-check`
- [ ] All 5 test players created with correct balances (1M total)
- [ ] CORS origins configured for frontend domain

---

## 🔧 Server Startup

### Backend (Terminal 1)
```bash
# Activate environment
economy\Scripts\activate

# Start FastAPI server (production: use gunicorn)
python main.py
```

Expected output:
```
[SERVER] GeoLedger Protocol Engine initialized
[OK] Zero-sum invariant verified. Total circulation: 1,000,000.00
INFO:     Started server process [1234]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Frontend (Terminal 2)
```bash
cd frontend
npm start
```

Expected output:
```
webpack compiled successfully
Local:            http://localhost:3000
On Your Network:  http://192.168.x.x:3000
```

---

## 🧪 Initial Health Checks

### 1. Backend Health
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "zero_sum_valid": true,
  "total_circulation": 1000000.0,
  "active_ws_connections": 0
}
```

### 2. Database Integrity
```bash
curl http://localhost:8000/api/v1/analytics/invariant-check
```

**Expected Response:**
```json
{
  "valid": true,
  "total_circulation": 1000000.0,
  "genesis_target": 1000000.0,
  "error": ""
}
```

### 3. Test Transfer
```bash
curl -X POST http://localhost:8000/api/v1/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "sender_id": "BUYER_01",
    "receiver_id": "BUYER_02",
    "amount": 100.0
  }'
```

**Expected Response:**
```json
{
  "transaction_id": 1,
  "sender_id": "BUYER_01",
  "receiver_id": "BUYER_02",
  "amount": 100.0,
  "tax_amount": 2.0,
  "net_amount": 100.0,
  "sender_new_balance": 29900.0,
  "receiver_new_balance": 15100.0,
  "timestamp": "2026-05-22T11:00:00"
}
```

---

## 📊 Monitoring & Maintenance

### Daily Health Check Script
```bash
#!/bin/bash
# check_health.sh

echo "=== GeoLedger Health Check ==="
echo "[1] Server Status:"
curl -s http://localhost:8000/health | jq .

echo "\n[2] Zero-Sum Invariant:"
curl -s http://localhost:8000/api/v1/analytics/invariant-check | jq .

echo "\n[3] Current Metrics:"
curl -s http://localhost:8000/api/v1/analytics/metrics | jq .

echo "\n[4] Wealth Distribution:"
curl -s http://localhost:8000/api/v1/analytics/wealth-distribution | jq '.[] | {user_id, balance, percentage_of_total}' | head -20

echo "\n=== Check Complete ==="
```

### Database Backup
```bash
# Backup economy.db
copy economy.db economy.db.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup integrity
sqlite3 economy.db.backup "SELECT COUNT(*) FROM users; SELECT SUM(balance) FROM users;"
```

### Periodic Analytics Snapshots
The system automatically saves metrics every 5 minutes to `analytics_snapshot` table.

**Retrieve snapshot history:**
```bash
curl http://localhost:8000/api/v1/analytics/metrics/history?limit=50 | jq .
```

---

## 🚨 Troubleshooting

### Issue: "Zero-Sum Invariant Violated"
```json
{
  "valid": false,
  "total_circulation": 999999.5,
  "error": "CRITICAL: Total circulation 999999.5 != genesis 1000000"
}
```

**Solution:**
1. Immediate stop transaction processing
2. Identify failed transaction in `audit_log` table:
   ```sql
   SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;
   ```
3. Check for database corruption:
   ```sql
   PRAGMA integrity_check;
   ```
4. If corrupted, restore from backup

### Issue: WebSocket Connections Dropping
**Check server logs for:**
- Network timeouts
- Memory exhaustion
- Connection limit exceeded

**Solution:**
1. Increase OS file descriptor limits
2. Configure connection pooling in FastAPI
3. Monitor active connection count: `curl http://localhost:8000 | jq .active_connections`

### Issue: Slow Transaction Processing
**Debug:**
```sql
-- Check transaction volume
SELECT COUNT(*) FROM transactions;
SELECT * FROM transactions ORDER BY timestamp DESC LIMIT 5;

-- Check lock contention (if enabled)
PRAGMA database_list;
```

**Optimize:**
- Implement batch transaction processing
- Add database indexing on frequently queried columns
- Consider PostgreSQL for production scalability

---

## 🔐 Security Considerations

### 1. Input Validation
- All user inputs validated via Pydantic models
- Amount fields use `gt=0` constraint
- IDs must be 3+ characters

### 2. Database Access
- No raw SQL injection possible (parameterized queries only)
- Row-level locking prevents race conditions
- Transactions auto-rollback on any error

### 3. Frontend Security
- NO business logic in frontend
- All validation happens server-side
- CORS configured to restrict cross-origin requests

### 4. API Rate Limiting (TODO)
Consider implementing per-endpoint rate limits:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/transfer")
@limiter.limit("10/minute")
async def transfer_funds(req: TransferRequest):
    ...
```

---

## 🌍 Production Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_PATH=economy.db

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=false  # Disable auto-reload in production

# Frontend
FRONTEND_URL=http://localhost:3000

# Fiscal Policy
VELOCITY_TAX_RATE=0.02
TREASURY_ID=GOV_01

# WebSocket
BROADCAST_RADIUS=100.0
MAX_CONNECTIONS=1000
```

Load in `main.py`:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: str = "economy.db"
    host: str = "0.0.0.0"
    port: int = 8000
    velocity_tax_rate: float = 0.02
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 📈 Scaling Considerations

### Vertical Scaling (Single Server)
- Increase Python workers: `uvicorn main:app --workers 4`
- Enable connection pooling
- Optimize database indexes

### Horizontal Scaling (Multiple Servers)
- Deploy backend to load balancer (nginx/HAProxy)
- Use shared PostgreSQL database (not SQLite)
- Implement Redis for WebSocket session management
- Use reverse proxy to route WebSocket connections

### Database Scaling
**SQLite → PostgreSQL Migration:**

1. Export schema and data:
   ```bash
   sqlite3 economy.db .dump > dump.sql
   ```

2. Create PostgreSQL tables
3. Import data
4. Update connection string in `bank.py`, `spatial.py`, `analytics.py`

---

## 🧯 Disaster Recovery

### Full System Restore from Backup
```bash
# 1. Restore database
copy economy.db.backup economy.db

# 2. Verify zero-sum invariant
curl http://localhost:8000/api/v1/analytics/invariant-check

# 3. Restart services
python main.py
cd frontend && npm start
```

### Transaction Rollback (Manual)
If a transaction is found to violate invariants:

```sql
-- View problematic transaction
SELECT * FROM transactions WHERE transaction_id = X;
SELECT * FROM audit_log WHERE metadata LIKE '%transaction_id: X%';

-- Manual reversal (only if absolutely necessary)
BEGIN;
  UPDATE users SET balance = balance + 100.0 WHERE user_id = 'BUYER_01';
  UPDATE users SET balance = balance - 100.0 WHERE user_id = 'BUYER_02';
  UPDATE users SET balance = balance - 2.0 WHERE user_id = 'GOV_01';
COMMIT;

-- Verify
SELECT * FROM users;
SELECT SUM(balance) FROM users;
```

---

## 📞 Support & Alerts

### Critical Alerts to Monitor
- Zero-sum invariant violation
- WebSocket connection failures
- Database disk full
- Transaction processing > 1 second

### Log Locations
- Backend: Console (stdout)
- Frontend: Browser DevTools Console
- Database: SQLite logs (if enabled)

### Performance Metrics
```bash
# Get current system metrics
curl http://localhost:8000/api/v1/analytics/metrics | jq '{
  velocity: .velocity_of_money,
  gini: .gini_coefficient,
  transactions: .num_transactions,
  active_players: .num_active_players
}'
```

---

**Last Updated**: May 22, 2026  
**Version**: 1.0.0
