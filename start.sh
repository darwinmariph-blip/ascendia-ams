#!/bin/bash
# =============================================================
#  Ascendia AMS — Automated Startup Script
#  Starts all services in the correct order
# =============================================================
#  HOW TO USE:
#  chmod +x start.sh
#  ./start.sh
# =============================================================

echo ""
echo "============================================================"
echo "  ASCENDIA AMS — STARTING ALL SERVICES"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

# ── 1. Start MySQL ────────────────────────────────────────────
echo "1️⃣   Starting MySQL..."
brew services start mysql > /dev/null 2>&1
sleep 1
if brew services list | grep mysql | grep -q "started"; then
    echo "  ✅  MySQL running"
else
    echo "  ❌  MySQL failed to start"
fi

# ── 2. Start MongoDB ──────────────────────────────────────────
echo "2️⃣   Starting MongoDB..."
brew services start mongodb-community > /dev/null 2>&1
sleep 1
if brew services list | grep mongodb | grep -q "started"; then
    echo "  ✅  MongoDB running"
else
    echo "  ❌  MongoDB failed to start"
fi

# ── 3. Start InfluxDB ─────────────────────────────────────────
echo "3️⃣   Starting InfluxDB..."
brew services start influxdb > /dev/null 2>&1
sleep 1
if brew services list | grep influxdb | grep -q "started"; then
    echo "  ✅  InfluxDB running"
else
    echo "  ❌  InfluxDB failed to start"
fi

# ── 4. Start Redis ────────────────────────────────────────────
echo "4️⃣   Starting Redis..."
brew services start redis > /dev/null 2>&1
sleep 1
if brew services list | grep redis | grep -q "started"; then
    echo "  ✅  Redis running"
else
    echo "  ❌  Redis failed to start"
fi

# ── 5. Start Valet (Snipe-IT) ─────────────────────────────────
echo "5️⃣   Starting Valet (Snipe-IT)..."
cd "$HOME/Sites/snipe-it" && valet start > /dev/null 2>&1
sleep 2
# Test Snipe-IT
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://snipe-it.test 2>/dev/null)
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "  ✅  Snipe-IT running at http://snipe-it.test"
else
    echo "  ⚠️   Snipe-IT may still be starting... check http://snipe-it.test"
fi

# ── 6. Summary ────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ALL SERVICES STARTED"
echo "============================================================"
echo ""
echo "  Now run in a new terminal tab:"
echo "  cd ~/ascendia-ams && python3 proxy.py"
echo ""
echo "  Then open:"
echo "  Dashboard  → http://localhost:8888/dashboard.html"
echo "  Snipe-IT   → http://snipe-it.test"
echo "  API docs   → http://localhost:8080/docs"
echo "  Mobile QR  → http://localhost:8888/mobile_qr.html"
echo ""
echo "  Other scripts:"
echo "  python3 reporting.py          # Full system report"
echo "  python3 ai_priority_scorer.py # Score all assets"
echo "  python3 hris_sync.py          # Sync staff"
echo "  python3 backup.sh             # Backup all data"
echo "============================================================"
echo ""
