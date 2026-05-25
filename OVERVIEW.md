# Sovereign Economy - Project Overview

## What Is This?

A **real-world location-based game** like Pokémon GO, where players:

- 📍 Use **GPS or map** to find their location in the real world
- 🏪 Visit **shops** at real GPS coordinates and buy/sell items
- 🗺️ Discover **landmarks and quest locations** on the map
- 💰 Trade with other players using a **fixed-supply economy** (1 million tokens total)
- 🎮 Control their character with **joystick, GPS movement, or map clicks**

## How The Economy Works

- **Total Money**: 1,000,000 tokens (never changes)
- **Every Transaction**: Automatically takes 2% tax → government
- **Shops**: Can hold items, players buy from them
- **Balance**: No one can go negative (database prevents it)
- **Guarantee**: The total always = 1,000,000 (mathematically enforced)

## How It's Built

```
PLAYER (Mobile/Browser)
    ↓ (GPS Location + Map Clicks)
FRONTEND (React + Google Maps)
    ↓ (HTTP API + WebSocket)
BACKEND (Python/FastAPI)
    ↓ (SQL Queries)
DATABASE (SQLite)
```

## Key Files

| What | File |
|------|------|
| Economy/Transactions | `bank.py` |
| Shops/Locations | `locations.py` |
| GPS Math | `geo_utils.py` |
| API Endpoints | `main.py` |
| Map Display | `frontend/src/MapComponent.js` |
| Database | `economy.db` (created when you run it) |

## Test Data Included

**7 Shops in Kathmandu:**
- Pilgrim Book House
- The Bhaktapur Kitchen
- Nirvana Garden Cafe
- Durbar Handicraft Co.
- Silver Market
- Swayambhu Bazaar
- Patan Trading House

**6 Points of Interest (POIs):**
- Kathmandu Durbar Square (landmark)
- Swayambhu Stupa (landmark)
- Boudhanath Stupa (landmark)
- Thamel Green Space (quest hub)
- Patan Durbar Square (landmark)
- Thamel Trading Arena (PvP arena)

## What You Can Do

✅ Walk around with GPS (or pretend to on map)
✅ See shops and landmarks nearby
✅ Buy from shops (pay with tokens)
✅ Drag a joystick to move around
✅ See real-time updates (WebSocket)
✅ Guaranteed no one cheats with fake money

## What's Missing (Can Build Later)

- Admin panel to add/edit shops
- Quest system (tasks at landmarks)
- Inventory/items to carry
- Multiplayer chat
- Real business data (Google Places)
- Delivery system
- Guilds/teams

---

**Next Step**: Read `START.md` to run this locally!
