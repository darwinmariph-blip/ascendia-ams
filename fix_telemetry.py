import os, random, requests
from datetime import datetime, timezone
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))

from influxdb_client_3 import InfluxDBClient3, Point

SNIPEIT_URL = os.getenv("SNIPEIT_URL", "http://snipe-it.test")
TOKEN = os.getenv("SNIPEIT_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8181")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_DB = os.getenv("INFLUXDB_DATABASE", "ascendia_telemetry")

print(f"Snipe-IT: {SNIPEIT_URL}")
print(f"InfluxDB: {INFLUXDB_URL}")

influx = InfluxDBClient3(host=INFLUXDB_URL, token=INFLUXDB_TOKEN, database=INFLUXDB_DB)

print("Fetching all assets...")
all_assets = []
offset = 0
while True:
    r = requests.get(f"{SNIPEIT_URL}/api/v1/hardware?limit=100&offset={offset}", headers=HEADERS, timeout=30)
    data = r.json()
    rows = data.get("rows", [])
    total = data.get("total", 0)
    if not rows:
        break
    all_assets.extend(rows)
    offset += 100
    print(f"  Fetched {len(all_assets)}/{total}...")
    if offset >= total:
        break

print(f"✅ {len(all_assets)} assets found\n")

def next_month(dt):
    if dt.month == 12:
        return dt.replace(year=dt.year + 1, month=1, day=1)
    return dt.replace(month=dt.month + 1, day=1)

written = 0
errors = 0
start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
end_date = datetime(2026, 5, 27, tzinfo=timezone.utc)

for idx, asset in enumerate(all_assets):
    tag = asset.get("asset_tag", "")
    name = asset.get("name", "")
    category = (asset.get("category") or {}).get("name", "Other")
    purchase_date_str = (asset.get("purchase_date") or {}).get("date", "2023-01-01")
    try:
        purchase_date = datetime.strptime(purchase_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except:
        purchase_date = start_date

    asset_start = max(start_date, purchase_date)
    base_health = float(random.uniform(75.0, 92.0))
    is_critical = tag == "AAI-2026-00001"
    current = asset_start.replace(day=1)
    month_count = 0

    while current <= end_date:
        month_count += 1
        if is_critical:
            health  = float(max(5.0,  base_health - month_count * 3.0 + random.uniform(-3.0,  3.0)))
            battery = float(max(5.0,  90.0 - month_count * 2.5        + random.uniform(-5.0,  5.0)))
            cpu     = float(min(98.0, 20.0 + month_count * 2.5        + random.uniform(-5.0, 10.0)))
        else:
            degradation = float(month_count * random.uniform(0.1, 0.4))
            health  = float(max(40.0, base_health - degradation + random.uniform(-5.0, 5.0)))
            if category in ["Network Equipment", "UPS", "Security Equipment"]:
                battery = 100.0
                cpu     = float(random.uniform(5.0, 25.0))
            else:
                battery = float(max(40.0, 95.0 - degradation * 0.5 + random.uniform(-5.0,  5.0)))
                cpu     = float(min(90.0, 15.0 + degradation * 0.3 + random.uniform(-5.0, 10.0)))
        memory = float(random.uniform(20.0, 70.0))
        try:
            point = (
                Point("device_telemetry")
                .tag("asset_tag", tag)
                .tag("asset_name", name[:50])
                .tag("category", category)
                .field("battery_pct",  round(min(100.0, max(0.0, battery)), 2))
                .field("cpu_pct",      round(min(100.0, max(0.0, cpu)),     2))
                .field("memory_pct",   round(memory, 2))
                .field("health_score", round(min(100.0, max(0.0, health)),  2))
                .time(current)
            )
            influx.write(record=point)
            written += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  ❌ Write error: {e}")
        current = next_month(current)

    if (idx + 1) % 50 == 0:
        print(f"  Processed {idx+1}/{len(all_assets)} assets — {written} points written...")

print(f"\n{'='*50}")
print(f"  ✅ Done!")
print(f"  Assets processed : {len(all_assets)}")
print(f"  Points written   : {written}")
print(f"  Errors           : {errors}")
print(f"{'='*50}")
