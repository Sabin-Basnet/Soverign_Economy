# START - Run The Game (10 Minutes)

**NO API KEY NEEDED!** We use Leaflet.js + OpenStreetMap (100% free)

Follow these steps in order. Copy/paste each command.

---

## Step 1: Create & Activate Python Environment (3 min)

**In PowerShell, go to project folder:**

```powershell
cd c:\Users\SABIN\Desktop\Soverign_Economy
python -m venv venv
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` at the start of your prompt.

**Then install dependencies:**

```powershell
pip install -r requirements.txt
```

Wait for it to finish installing.

---

## Step 2: Seed Test Data for Dharan (1 min)

**Still in same Terminal with (venv) active:**

```powershell
sqlite3 economy.db ".read seed_dharan.sql"
```

This loads 7 shops and 6 landmarks from Dharan (where you're presenting!).

**Verify it worked:**

```powershell
sqlite3 economy.db "SELECT COUNT(*) as shops FROM locations;"
```

Should show: `7`

---

## Step 3: Start Backend (1 min)

**Terminal 1** (you should still be here with (venv) active):

```powershell
python main.py
```

Wait for this message:
```
[SERVER] GeoLedger Protocol Engine initialized
```

**Leave this running!**

---

## Step 4: Start Frontend (2 min)

**Open a NEW PowerShell window** (Terminal 2):

```powershell
cd c:\Users\SABIN\Desktop\Soverign_Economy\frontend
npm start
```

Your browser should open automatically at `http://localhost:3000`

If not, manually go to: http://localhost:3000

---

## Step 5: Test It! (2 min)

When the page loads:

1. **Geolocation Prompt** → Click **"Enable GPS"** 
   - Or click **"Skip"** if you want to manually place yourself
   
2. **Map appears** with:
   - Blue dot = your player
   - Green markers = shops
   - Colored markers = POIs (landmarks, quests)

3. **Try these:**
   - Click a shop marker → see info
   - Drag the joystick (bottom-left) → your player moves
   - Click map to place yourself manually

---

## ✅ You're Running!

If you see the map with shops/landmarks, you're done! 🎉

---

## 🛠️ If Something Breaks

### "Leaflet is not defined" error
- The Leaflet library might not have loaded from CDN
- Hard refresh browser: `Ctrl + Shift + R`
- Check browser console (F12) for network errors
- Make sure `index.html` has Leaflet script tags

### "Cannot find module" error
- Run this in `frontend/` folder:
```powershell
npm install
npm start
```

### Backend won't start
- Is Python activated? Check for `(venv)` in prompt
- Kill any other Python: `taskkill /im python.exe /f`
- Then try `python main.py` again

### "Address already in use"
- Another process is using port 8000
- Try: `python main.py --port 8001`

### Map shows blank/gray
- OpenStreetMap tiles might be slow to load
- Wait 2-3 seconds
- Check your internet connection
- Try hard refresh: `Ctrl + Shift + R`

---

## 📊 Verify Data Was Loaded

**Open Terminal 3:**

```powershell
cd c:\Users\SABIN\Desktop\Soverign_Economy
sqlite3 economy.db "SELECT COUNT(*) as shops FROM locations;"
```

Should show: `7`

If shows `0`, the data wasn't seeded. Run:
```powershell
sqlite3 economy.db ".read seed_dharan.sql"
```

---

## 🎮 What To Try

Once running:

1. **Look at map** → Find green shop markers
2. **Click a shop** → See details (name, distance)
3. **Drag joystick** (bottom-left) → Your player moves
4. **Check sidebar** → See all nearby shops
5. **Manual placement** → Click map to place yourself

---

## 🛑 To Stop

- **Backend**: Press `Ctrl + C` in Terminal 1
- **Frontend**: Press `Ctrl + C` in Terminal 2
- **Next time**: Just repeat Step 4 & 5

---

## 📚 Want to Understand?

Read `OVERVIEW.md` (this folder) to learn what the project does.

---

**Done!** You should be seeing Dharan on a map with shops. 🗺️
