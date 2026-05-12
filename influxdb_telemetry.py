"""
=============================================================
  Ascendia IT Asset Management — InfluxDB Telemetry
  Stores: Device Health, Battery, CPU, Memory streams
=============================================================
  HOW TO USE:
  1. Make sure InfluxDB is running: brew services start influxdb
  2. Run:  python3 influxdb_telemetry.py
=============================================================
  WHAT THIS STORES IN INFLUXDB:
  - Battery health % per asset over time
  - CPU usage % per asset over time
  - Memory usage % per asset over time
  - Overall device health score
  - Maintenance risk alerts
=============================================================
"""

import os
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point

load_dotenv()

INFLUXDB_URL      = os.getenv("INFLUXDB_URL",      "http://localhost:8181")
INFLUXDB_TOKEN    = os.getenv("INFLUXDB_TOKEN",    "")
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE", "ascendia_telemetry")

# ── Connect to InfluxDB ───────────────────────────────────
client = InfluxDBClient3(
    host     = INFLUXDB_URL,
    token    = INFLUXDB_TOKEN,
    database = INFLUXDB_DATABASE,
)

print("\n" + "═" * 60)
print("  INFLUXDB TELEMETRY — Ascendia Academic Institution")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 60)
print(f"\n✅  Connected to InfluxDB")
print(f"    URL:      {INFLUXDB_URL}")
print(f"    Database: {INFLUXDB_DATABASE}\n")


# ── Asset list (matches your Snipe-IT assets) ─────────────
ASSETS = [
    {"id": 1, "tag": "AAI-2026-00001", "name": "Dell Latitude 5540",      "category": "Laptop"},
    {"id": 2, "tag": "AAI-2026-00002", "name": "Dell Latitude 5540",      "category": "Laptop"},
    {"id": 3, "tag": "AAI-2026-00003", "name": "Dell Latitude 5540",      "category": "Laptop"},
    {"id": 4, "tag": "AAI-2026-00004", "name": "Dell UltraSharp Monitor", "category": "Monitor"},
    {"id": 5, "tag": "AAI-2026-00005", "name": "Dell UltraSharp Monitor", "category": "Monitor"},
    {"id": 6, "tag": "AAI-2026-00006", "name": "MacBook Pro M3",          "category": "Laptop"},
    {"id": 7, "tag": "AAI-2026-00007", "name": "MacBook Pro M3",          "category": "Laptop"},
    {"id": 8, "tag": "AAI-2026-00008", "name": "Epson EB-X51 Projector",  "category": "Projector"},
    {"id": 9, "tag": "AAI-2026-00009", "name": "Epson EB-X51 Projector",  "category": "Projector"},
]


# ══════════════════════════════════════════════════════════
#  WRITE TELEMETRY
# ══════════════════════════════════════════════════════════

def write_device_telemetry(asset_tag: str, asset_name: str, category: str,
                            battery_pct: float, cpu_pct: float,
                            memory_pct: float, timestamp=None):
    """Write a single telemetry reading for a device."""
    if timestamp is None:
        timestamp = datetime.utcnow()

    # Calculate health score (simple weighted average)
    # Battery weight: 40%, CPU: 30%, Memory: 30%
    # Lower CPU/Memory = healthier, higher battery = healthier
    health_score = (
        (battery_pct * 0.4) +
        ((100 - cpu_pct) * 0.3) +
        ((100 - memory_pct) * 0.3)
    )

    point = (
        Point("device_telemetry")
        .tag("asset_tag",  asset_tag)
        .tag("asset_name", asset_name)
        .tag("category",   category)
        .field("battery_pct",  round(battery_pct, 1))
        .field("cpu_pct",      round(cpu_pct, 1))
        .field("memory_pct",   round(memory_pct, 1))
        .field("health_score", round(health_score, 1))
        .time(timestamp)
    )

    client.write(record=point)


def write_maintenance_alert(asset_tag: str, asset_name: str,
                             alert_type: str, severity: str, message: str):
    """Write a maintenance alert event to InfluxDB."""
    point = (
        Point("maintenance_alerts")
        .tag("asset_tag",  asset_tag)
        .tag("asset_name", asset_name)
        .tag("alert_type", alert_type)
        .tag("severity",   severity)
        .field("message",  message)
        .field("value",    1)
        .time(datetime.utcnow())
    )
    client.write(record=point)


# ══════════════════════════════════════════════════════════
#  SIMULATE TELEMETRY DATA
#  In production this comes from JAMF/Intune MDM
# ══════════════════════════════════════════════════════════

def simulate_telemetry():
    """
    Generate realistic telemetry data for all assets.
    Asset AAI-2026-00001 is intentionally unhealthy (it has Maintenance-High status).
    """
    print("📡  Writing telemetry data for all assets...\n")

    # Simulate 7 days of hourly readings
    now = datetime.utcnow()
    readings_written = 0

    for asset in ASSETS:
        tag      = asset["tag"]
        name     = asset["name"]
        category = asset["category"]

        # Asset 1 is unhealthy (matches our Maintenance-High status)
        is_unhealthy = (asset["id"] == 1)

        for hours_ago in range(168, 0, -6):  # every 6 hours for 7 days
            ts = now - timedelta(hours=hours_ago)

            if is_unhealthy:
                # Degrading battery, high CPU — simulates failing hardware
                battery = max(5,  20  - (hours_ago * 0.05) + random.uniform(-3, 3))
                cpu     = min(98, 85  + (hours_ago * 0.02) + random.uniform(-5, 5))
                memory  = min(95, 80  + (hours_ago * 0.01) + random.uniform(-3, 3))
            elif category == "Monitor" or category == "Projector":
                # Non-laptop devices have no battery
                battery = 100.0
                cpu     = random.uniform(5, 25)
                memory  = random.uniform(10, 40)
            else:
                # Healthy laptops
                battery = random.uniform(60, 95)
                cpu     = random.uniform(10, 45)
                memory  = random.uniform(30, 65)

            write_device_telemetry(tag, name, category, battery, cpu, memory, ts)
            readings_written += 1

        # Write current reading
        if is_unhealthy:
            write_device_telemetry(tag, name, category, 8.0, 94.0, 88.0)
            write_maintenance_alert(tag, name, "battery_critical", "High",
                                    "Battery at 8% — critical failure imminent")
            write_maintenance_alert(tag, name, "cpu_overload", "High",
                                    "CPU at 94% sustained — hardware investigation needed")
        else:
            battery = random.uniform(65, 95) if category == "Laptop" else 100.0
            cpu     = random.uniform(10, 40)
            memory  = random.uniform(30, 60)
            write_device_telemetry(tag, name, category, battery, cpu, memory)

        print(f"  ✅  {tag} — {168//6} readings written {'⚠️  UNHEALTHY' if is_unhealthy else ''}")

    print(f"\n  Total readings written: {readings_written + len(ASSETS)}")
    return readings_written


# ══════════════════════════════════════════════════════════
#  QUERY TELEMETRY
# ══════════════════════════════════════════════════════════

def get_latest_health_scores():
    """Get the most recent health score for each asset."""
    print("\n📊  Latest device health scores:\n")
    query = """
        SELECT asset_tag, asset_name, health_score, battery_pct, cpu_pct, memory_pct
        FROM device_telemetry
        WHERE time >= now() - INTERVAL '1 hour'
        ORDER BY time DESC
    """
    try:
        result = client.query(query=query, language="sql")
        df = result.to_pandas()
        if df.empty:
            print("  No recent telemetry data found.")
            return

        # Show latest per asset
        latest = df.groupby("asset_tag").first().reset_index()
        for _, row in latest.iterrows():
            score   = row.get("health_score", 0)
            battery = row.get("battery_pct", 0)
            cpu     = row.get("cpu_pct", 0)
            icon    = "🔴" if score < 40 else "🟡" if score < 65 else "🟢"
            print(f"  {icon} [{row['asset_tag']}] Health: {score:.0f}%  Battery: {battery:.0f}%  CPU: {cpu:.0f}%")
    except Exception as e:
        print(f"  Query error: {e}")


def get_alerts():
    """Get recent maintenance alerts."""
    print("\n⚠️   Recent maintenance alerts:\n")
    query = """
        SELECT asset_tag, alert_type, severity, message
        FROM maintenance_alerts
        WHERE time >= now() - INTERVAL '24 hours'
        ORDER BY time DESC
    """
    try:
        result = client.query(query=query, language="sql")
        df = result.to_pandas()
        if df.empty:
            print("  No recent alerts.")
            return
        for _, row in df.iterrows():
            icon = "🔴" if row["severity"] == "High" else "🟡"
            print(f"  {icon} [{row['asset_tag']}] {row['alert_type']}: {row['message']}")
    except Exception as e:
        print(f"  Query error: {e}")


def print_influxdb_summary():
    print("\n" + "═" * 60)
    print("  INFLUXDB SUMMARY")
    print("═" * 60)
    print(f"  Database  : {INFLUXDB_DATABASE}")
    print(f"  Assets    : {len(ASSETS)}")
    print(f"  Measurements: device_telemetry, maintenance_alerts")
    print("═" * 60)


if __name__ == "__main__":
    # Write simulated telemetry
    simulate_telemetry()

    # Small pause to let InfluxDB index
    print("\n  ⏳  Waiting 2 seconds for InfluxDB to index...")
    time.sleep(2)

    # Query results
    get_latest_health_scores()
    get_alerts()
    print_influxdb_summary()

    print("\n✅  InfluxDB telemetry integration complete!")
    print("    Next step → Build the full reporting dashboard\n")
