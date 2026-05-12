"""
=============================================================
  Ascendia IT Asset Management — Reporting Module
  Combines: Snipe-IT + MongoDB + InfluxDB into one report
=============================================================
  HOW TO USE:
  Run:  python3 reporting.py
=============================================================
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from influxdb_client_3 import InfluxDBClient3
from snipeit_client import SnipeITClient

load_dotenv()

snipe = SnipeITClient(
    base_url = os.getenv("SNIPEIT_URL", "http://snipe-it.test"),
    token    = os.getenv("SNIPEIT_TOKEN", ""),
)

mongo  = MongoClient("mongodb://localhost:27017/")
db     = mongo["ascendia_ams"]

influx = InfluxDBClient3(
    host     = os.getenv("INFLUXDB_URL",      "http://localhost:8181"),
    token    = os.getenv("INFLUXDB_TOKEN",    ""),
    database = os.getenv("INFLUXDB_DATABASE", "ascendia_telemetry"),
)

def generate_full_report():
    print("\n" + "═" * 60)
    print("  ASCENDIA AMS — FULL SYSTEM REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # ── 1. Snipe-IT Summary ──────────────────────────────
    print("\n📦  ASSET INVENTORY (Snipe-IT)")
    print("─" * 40)
    assets = snipe.list_assets(limit=500).get("rows", [])
    users  = snipe.list_users(limit=500).get("rows", [])

    cats = {}
    high_assets = []
    total_value = 0
    for a in assets:
        cat = a.get("category", {}).get("name", "Other")
        cats[cat] = cats.get(cat, 0) + 1
        cost = float(str(a.get("purchase_cost") or 0).replace(',', ''))
        total_value += cost
        cf = a.get("custom_fields", {})
        ai = cf.get("AI Priority Score", {}).get("value", "Unscored")
        if ai == "High":
            high_assets.append(a.get("asset_tag", "—"))

    print(f"  Total assets  : {len(assets)}")
    print(f"  Total staff   : {len(users)}")
    print(f"  Total value   : ₱{total_value:,.2f}")
    print(f"  By category   :")
    for cat, count in cats.items():
        print(f"    • {cat}: {count}")
    print(f"  AI High alerts: {len(high_assets)} — {', '.join(high_assets) or 'None'}")

    # ── 2. MongoDB Summary ───────────────────────────────
    print("\n🔧  MAINTENANCE (MongoDB)")
    print("─" * 40)
    total_tickets  = db.maintenance_tickets.count_documents({})
    open_tickets   = db.maintenance_tickets.count_documents({"status": "Open"})
    high_tickets   = db.maintenance_tickets.count_documents({"ai_priority": "High", "status": "Open"})
    total_assign   = db.assignment_history.count_documents({})
    active_assign  = db.assignment_history.count_documents({"status": "Active"})

    print(f"  Total tickets  : {total_tickets}")
    print(f"  Open tickets   : {open_tickets}")
    print(f"  High priority  : {high_tickets}")
    print(f"  Assignments    : {total_assign} total, {active_assign} active")

    if high_tickets > 0:
        print(f"\n  ⚠️  Open High priority tickets:")
        for t in db.maintenance_tickets.find({"ai_priority": "High", "status": "Open"}):
            print(f"    • [{t.get('asset_tag','—')}] {t.get('issue_notes','')[:55]}...")

    # ── 3. InfluxDB Summary ──────────────────────────────
    print("\n📡  DEVICE TELEMETRY (InfluxDB)")
    print("─" * 40)
    try:
        query = """
            SELECT asset_tag, health_score, battery_pct, cpu_pct
            FROM device_telemetry
            WHERE time >= now() - INTERVAL '1 hour'
            ORDER BY time DESC
        """
        result = influx.query(query=query, language="sql")
        df = result.to_pandas()
        if not df.empty:
            latest = df.groupby("asset_tag").first().reset_index()
            critical = latest[latest["health_score"] < 40]
            warning  = latest[(latest["health_score"] >= 40) & (latest["health_score"] < 65)]
            healthy  = latest[latest["health_score"] >= 65]
            print(f"  🔴 Critical  : {len(critical)}")
            print(f"  🟡 Warning   : {len(warning)}")
            print(f"  🟢 Healthy   : {len(healthy)}")
            avg_health = latest["health_score"].mean()
            print(f"  Avg health  : {avg_health:.0f}%")
            print(f"\n  Per-asset health:")
            for _, row in latest.sort_values("health_score").iterrows():
                score = row["health_score"]
                icon  = "🔴" if score < 40 else "🟡" if score < 65 else "🟢"
                print(f"    {icon} [{row['asset_tag']}] {score:.0f}%  Battery:{row['battery_pct']:.0f}%  CPU:{row['cpu_pct']:.0f}%")
        else:
            print("  No recent telemetry data.")
    except Exception as e:
        print(f"  Telemetry query error: {e}")

    # ── 4. Overall System Health ─────────────────────────
    print("\n" + "═" * 60)
    print("  OVERALL SYSTEM HEALTH")
    print("═" * 60)
    issues = []
    if high_tickets > 0:
        issues.append(f"⚠️  {high_tickets} high-priority maintenance ticket(s) open")
    if len(high_assets) > 0:
        issues.append(f"⚠️  {len(high_assets)} asset(s) AI-flagged as High priority")

    if issues:
        print("\n  Action required:")
        for issue in issues:
            print(f"    {issue}")
    else:
        print("\n  ✅ No critical issues detected.")

    print(f"\n  Report complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    generate_full_report()
