# Quick Start Checklist

Follow these steps to get the real-world GPS game running locally.

## ✅ Step-by-Step Setup

### 1️⃣ **Database Setup** (5 min)

```bash
cd c:\Users\SABIN\Desktop\Soverign_Economy

# Apply GPS migration
sqlite3 economy.db < migration_to_gps.sql

# Seed test data
sqlite3 economy.db < seed_kathmandu.sql

# Verify
sqlite3 economy.db "SELECT COUNT(*) as shops FROM locations;"
# Should show: shops = 7
```

**Expected output:**
- 7 test shops in Kathmandu (Thamel, Durbar, Patan)
- 6 test POIs (landmarks, quest hubs, arenas)

---

### 2️⃣ **Get Google Maps API Key** (10 min)

1. Go to: https://console.cloud.google.com/
2. Click **Create Project**
3. Go to **APIs & Services** → **Enabled APIs**
4. Enable **Maps JavaScript API**
5. Go to **Credentials** → **Create Credentials** → **API Key**
6. Copy your API key

**Save your API key** - you'll need it next!

---

### 3️⃣ **Update Frontend** (2 min)

Edit `frontend/public/index.html`:

Find this line:
```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY"></script>
```

Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual key from step 2.

---

### 4️⃣ **Start Backend** (1 min)

```bash
# Terminal 1
cd c:\Users\SABIN\Desktop\Soverign_Economy
economy\Scripts\activate
python main.py

# Wait for: "[SERVER] GeoLedger Protocol Engine initialized"
# Health check: http://localhost:8000/health
```

---

### 5️⃣ **Start Frontend** (1 min)

```bash
# Terminal 2
cd c:\Users\SABIN\Desktop\Soverign_Economy\frontend
npm install  # Only needed first time
npm start

# App opens at http://localhost:3000
```

---

### 6️⃣ **Test the Game** (5 min)

1. **Browser opens** → http://localhost:3000
2. **Geolocation prompt** → Click "Enable GPS" (or "Skip" to manually place)
3. **Map loads** → See Kathmandu centered, with shop/POI markers
4. **Verify:**
   - ✓ Blue dot = your player
   - ✓ Green markers = shops
   - ✓ Colored markers = POIs (landmarks, quests, arenas)
   - ✓ Sidebar shows "Nearby Shops"

---

## 🧪 Verify It's Working

### Check 1: Database
```bash
sqlite3 economy.db "SELECT location_name, location_type FROM locations LIMIT 5;"
# Should show: Pilgrim Book House, Bhaktapur Kitchen, etc.
```

### Check 2: API
```bash
# Terminal 3 (or PowerShell)
curl http://localhost:8000/api/v1/pois | python -m json.tool
# Should show 6 POIs with names, types, coordinates
```

### Check 3: Frontend
- Open http://localhost:3000
- Browser console (F12) should be clean (no errors)
- Map should load within 3 seconds

---

## 📱 Test Features

### Manual Location (No GPS)
1. Click map to place yourself
2. Click a nearby shop marker
3. Sidebar updates distance

### Joystick Movement
1. Drag the joystick zone (bottom-left)
2. Player marker moves on map
3. Nearby shops update

### View Shop Details
1. Click any green marker
2. Info window pops up
3. Shows name, type, distance

### Add New Shop (Admin)
```bash
curl -X POST http://localhost:8000/api/v1/locations/create \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "MERCH_TEST",
    "location_name": "Test Shop",
    "latitude": 27.7175,
    "longitude": 85.3140,
    "location_type": "shop"
  }'
```

---

## 🛠️ Common Issues & Fixes

### Issue: "Google Maps not loaded"
```
❌ Map appears blank
```
**Fix:**
- Check API key in `index.html` (not YOUR_GOOGLE_MAPS_API_KEY)
- Hard refresh browser (Ctrl+Shift+R)
- Check browser console for API errors

### Issue: GPS not working
```
❌ No location prompt
```
**Fix:**
- Must be on `localhost` or HTTPS
- Check browser permissions (click lock icon)
- Try manual placement instead (click map)

### Issue: No shops appear
```
❌ Sidebar is empty
```
**Fix:**
1. Verify data seeded: `sqlite3 economy.db "SELECT COUNT(*) FROM locations;"`
2. If 0, run: `sqlite3 economy.db < seed_kathmandu.sql`
3. Reload page

### Issue: Backend won't start
```
❌ "Address already in use" or import error
```
**Fix:**
- Kill existing process: `taskkill /im python.exe /f`
- Or use different port: `python main.py --port 8001`
- Or check dependencies: `pip list | findstr fastapi`

### Issue: Frontend npm error
```
❌ "Cannot find module" or build fails
```
**Fix:**
```bash
cd frontend
rm -r node_modules package-lock.json
npm install
npm start
```

---

## 📊 Test Data Locations (Kathmandu)

**Shops (Green Markers):**
| Name | Area | Distance from Center |
|------|------|-----|
| Pilgrim Book House | Thamel | 1.2 km |
| The Bhaktapur Kitchen | Thamel | 1.3 km |
| Nirvana Garden Cafe | Thamel | 1.1 km |
| Durbar Handicraft Co. | Durbar Square | 0.8 km |
| Silver Market | Durbar Square | 0.9 km |
| Swayambhu Bazaar | Swayambhu | 5.4 km |
| Patan Trading House | Patan | 6.7 km |

**POIs (Colored Markers):**
| Name | Type | Reward |
|------|------|--------|
| Kathmandu Durbar Square | Landmark | 100 tokens |
| Swayambhu Stupa | Landmark | 150 tokens |
| Boudhanath Stupa | Landmark | 150 tokens |
| Thamel Green Space | Quest Hub | 250 tokens |
| Patan Durbar Square | Landmark | 120 tokens |
| Thamel Trading Arena | Arena | 500 tokens (PvP) |

---

## 🚀 Next Features to Build

After MVP is working:

- [ ] **Shop Interactions**: Buy items/services from shops
- [ ] **Quest System**: Pick up quests at POIs, earn rewards
- [ ] **Inventory**: Carry items, manage resources
- [ ] **Multiplayer**: See nearby players, trade in-person
- [ ] **Real Shops**: Import Google Places API data
- [ ] **Admin Panel**: Web UI to manage shops/POIs
- [ ] **Delivery Jobs**: Transport goods across map
- [ ] **Guild System**: Create/join guilds, control areas

---

## 📚 Documentation

- **[GPS_SETUP_GUIDE.md](GPS_SETUP_GUIDE.md)** - Detailed setup instructions
- **[GPS_API_REFERENCE.md](GPS_API_REFERENCE.md)** - API endpoint reference
- **[ROADMAP.md](ROADMAP.md)** - Development roadmap
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design
- **[README.md](README.md)** - Project overview

---

## ⏱️ Typical Setup Time

| Step | Time |
|------|------|
| Database migration | 5 min |
| Get API key | 10 min |
| Update frontend | 2 min |
| Start backend | 1 min |
| Start frontend | 1 min |
| **Total** | **≈20 minutes** |

**Ready to test?** Go to [Testing the Game](#-verify-its-working) above!

---

## 💡 Pro Tips

- **GPS Testing**: Use browser DevTools to fake location (F12 → Sensors)
- **Mobile Testing**: Use `npm start -- --host 0.0.0.0` to access from phone
- **Database GUI**: Install DBeaver to browse `economy.db` visually
- **API Testing**: Use Postman/Insomnia instead of curl for easier requests

---

## 🆘 Get Help

If stuck:

1. Check browser console (F12) for errors
2. Check terminal output for backend errors
3. Verify ports are free: `netstat -ano | findstr :8000`
4. Read error messages carefully - they're usually specific!
5. Check [GPS_SETUP_GUIDE.md](GPS_SETUP_GUIDE.md) troubleshooting section
