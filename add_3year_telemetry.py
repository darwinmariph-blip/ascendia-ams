"""
Add 3 years of telemetry data to InfluxDB for all assets
Also adds 3 years of audit events and maintenance records to MongoDB
Run: python3 add_3year_telemetry.py
"""
import os, random, requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()

SNIPEIT_URL = os.getenv("SNIPEIT_URL", "http://snipe-it.test")
TOKEN = os.getenv("SNIPEIT_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8181")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_DB = os.getenv("INFLUXDB_DATABASE", "ascendia_telemetry")

print("\n" + "="*60)
print("  ASCENDIA AMS — 3 YEAR DATA GENERATOR")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# Get all assets
print("\n📦  Fetching all assets...")
r = requests.get(f"{SNIPEIT_URL}/api/v1/hardware?limit=500", headers=HEADERS, timeout=30)
assets = r.json().get("rows", [])
print(f"  ✅  {len(assets)} assets found")

# ── STEP 1: InfluxDB 3-year telemetry ────────────────────
print("\n📡  Step 1 — Writing 3 years of telemetry to InfluxDB...")
try:
    from influxdb_client_3 import InfluxDBClient3, Point
    influx = InfluxDBClient3(host=INFLUXDB_URL, token=INFLUXDB_TOKEN, database=INFLUXDB_DB)
    
    written = 0
    start_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 5, 27, tzinfo=timezone.utc)
    
    # Write monthly readings for each asset
    for asset in assets:
        tag = asset.get("asset_tag", "")
        name = asset.get("name", "")
        category = (asset.get("category") or {}).get("name", "Other")
        purchase_date_str = (asset.get("purchase_date") or {}).get("date", "2023-01-01")
        
        try:
            purchase_date = datetime.strptime(purchase_date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            purchase_date = start_date

        # Asset age in months affects health
        asset_start = max(start_date, purchase_date)
        current = asset_start
        
        # Base health depends on category
        if category in ["Network Equipment", "UPS", "Security Equipment"]:
            base_health = random.uniform(80, 95)
        elif category in ["Laptops", "Desktops"]:
            base_health = random.uniform(75, 92)
        else:
            base_health = random.uniform(82, 96)

        # Special case for critical asset
        is_critical = tag == "AAI-2026-00001"
        
        month_count = 0
        while current <= end_date:
            month_count += 1
            
            if is_critical:
                health = max(5, base_health - month_count * 3 + random.uniform(-3, 3))
                battery = max(5, 90 - month_count * 2.5 + random.uniform(-5, 5))
                cpu = min(98, 20 + month_count * 2.5 + random.uniform(-5, 10))
            else:
                # Gradual degradation over time
                degradation = month_count * random.uniform(0.1, 0.4)
                health = max(40, base_health - degradation + random.uniform(-5, 5))
                
                if category in ["Network Equipment", "UPS", "Security Equipment"]:
                    battery = 100.0
                    cpu = random.uniform(5, 25)
                else:
                    battery = max(40, 95 - degradation * 0.5 + random.uniform(-5, 5))
                    cpu = min(90, 15 + degradation * 0.3 + random.uniform(-5, 10))
                
                memory = random.uniform(20, 65)

            point = (
                Point("device_telemetry")
                .tag("asset_tag", tag)
                .tag("asset_name", name[:50])
                .tag("category", category)
                .field("battery_pct", round(min(100, max(0, battery)), 1))
                .field("cpu_pct", round(min(100, max(0, cpu)), 1))
                .field("memory_pct", round(random.uniform(20, 70), 1))
                .field("health_score", round(min(100, max(0, health)), 1))
                .time(current)
            )
            influx.write(record=point)
            written += 1
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+1)
        
        if written % 500 == 0:
            print(f"  📊  {written} telemetry points written...")

    print(f"  ✅  {written} telemetry points written to InfluxDB (3 years)")

except Exception as e:
    print(f"  ❌  InfluxDB error: {e}")

# ── STEP 2: MongoDB - 3 years of audit events ─────────────
print("\n📝  Step 2 — Adding 3 years of audit events to MongoDB...")
try:
    from pymongo import MongoClient
    db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]

    audit_events = []
    maintenance_tickets = []
    finance_records = []

    actions = ["ASSET_CHECKOUT", "ASSET_CHECKIN", "ASSET_MOVED", "MAINTENANCE_SCHEDULED",
               "ASSET_AUDITED", "STATUS_CHANGED", "ASSET_UPDATED"]
    
    departments = ["College of Computer Studies", "IT Support", "Finance", 
                   "Human Resources", "Registrar's Office", "Property Office"]
    
    staff = ["Maria Santos", "Jose Reyes", "Ana Cruz", "Juan Dela Cruz",
             "Roberto Garcia", "Patricia Lim", "Miguel Torres", "Elena Gomez"]

    for asset in assets[:100]:  # Generate events for first 100 assets
        tag = asset.get("asset_tag", "")
        name = asset.get("name", "")
        purchase_date_str = (asset.get("purchase_date") or {}).get("date", "2023-01-01")
        
        try:
            purchase_date = datetime.strptime(purchase_date_str[:10], "%Y-%m-%d")
        except:
            purchase_date = datetime(2023, 1, 1)

        # Generate 3-12 events per asset over its lifetime
        num_events = random.randint(3, 12)
        asset_start = max(purchase_date, datetime(2023, 1, 1))
        
        for _ in range(num_events):
            days_since = (datetime(2026, 5, 27) - asset_start).days
            if days_since <= 0:
                continue
            event_date = asset_start + timedelta(days=random.randint(0, days_since))
            action = random.choice(actions)
            actor = random.choice(staff)
            dept = random.choice(departments)

            audit_events.append({
                "event_id": f"AUD-{tag}-{int(event_date.timestamp())}",
                "action": action,
                "actor": actor,
                "asset_tag": tag,
                "department": dept,
                "before": {"status": "Ready to Deploy"},
                "after": {"status": "In Use" if "CHECKOUT" in action else "Ready to Deploy"},
                "timestamp": event_date.isoformat(),
                "process": "Operations",
                "notes": f"{action.replace('_',' ').title()} — {name}"
            })

        # Generate maintenance tickets for older/degraded assets
        purchase_year = purchase_date.year
        if purchase_year <= 2024 and random.random() < 0.4:
            ticket_date = purchase_date + timedelta(days=random.randint(180, 900))
            if ticket_date <= datetime(2026, 5, 27):
                severity = random.choice(["High", "Medium", "Low"])
                issues = {
                    "High": ["Fan failure detected", "Battery degraded below 20%", "Hard drive errors", "Overheating issues"],
                    "Medium": ["Slow performance", "Minor hardware issue", "Keyboard malfunction", "Screen flickering"],
                    "Low": ["Routine maintenance", "Software update needed", "Cleaning required", "Cable replacement"]
                }
                maintenance_tickets.append({
                    "ticket_id": f"MNT-{tag}-{int(ticket_date.timestamp())}",
                    "asset_tag": tag,
                    "asset_name": name,
                    "severity": severity,
                    "status": random.choice(["Open", "Resolved", "In Progress"]),
                    "issue": random.choice(issues[severity]),
                    "reported_by": random.choice(staff),
                    "date_reported": ticket_date.isoformat(),
                    "department": random.choice(departments),
                    "resolution_date": (ticket_date + timedelta(days=random.randint(1, 30))).isoformat() if random.random() > 0.3 else None
                })

    # Finance records per year
    for year in [2023, 2024, 2025, 2026]:
        year_assets = [a for a in assets if str(year) in str((a.get("purchase_date") or {}).get("date", ""))]
        if year_assets:
            total_cost = sum(float(str(a.get("purchase_cost") or "0").replace(",", "")) for a in year_assets)
            finance_records.append({
                "record_id": f"FIN-{year}-PROCUREMENT",
                "year": year,
                "quarter": "Annual",
                "transaction_type": "PROCUREMENT",
                "total_assets_acquired": len(year_assets),
                "total_cost": round(total_cost, 2),
                "budget_allocated": round(total_cost * 1.1, 2),
                "budget_utilized": round(total_cost, 2),
                "budget_remaining": round(total_cost * 0.1, 2),
                "department_breakdown": {dept: round(total_cost / len(departments), 2) for dept in departments},
                "date": f"{year}-12-31",
                "notes": f"Annual IT procurement report {year}"
            })

    # Insert to MongoDB
    if audit_events:
        db.audit_events.insert_many(audit_events)
        print(f"  ✅  {len(audit_events)} audit events added")
    
    if maintenance_tickets:
        db.maintenance_tickets.insert_many(maintenance_tickets)
        print(f"  ✅  {len(maintenance_tickets)} maintenance tickets added")
    
    if finance_records:
        db.finance_records.delete_many({})
        db.finance_records.insert_many(finance_records)
        print(f"  ✅  {len(finance_records)} finance records updated")

except Exception as e:
    print(f"  ❌  MongoDB error: {e}")

# ── STEP 3: Analytics KPIs ────────────────────────────────
print("\n📈  Step 3 — Updating analytics KPIs...")
try:
    from pymongo import MongoClient
    db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]
    
    total = requests.get(f"{SNIPEIT_URL}/api/v1/hardware?limit=1", headers=HEADERS).json().get("total", 0)
    
    db.analytics_kpis.delete_many({})
    db.analytics_kpis.insert_one({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_assets": total,
        "total_value": sum(float(str(a.get("purchase_cost") or "0").replace(",","")) for a in assets),
        "assets_by_year": {
            "2023": len([a for a in assets if "2023" in str((a.get("purchase_date") or {}).get("date",""))]),
            "2024": len([a for a in assets if "2024" in str((a.get("purchase_date") or {}).get("date",""))]),
            "2025": len([a for a in assets if "2025" in str((a.get("purchase_date") or {}).get("date",""))]),
            "2026": len([a for a in assets if "2026" in str((a.get("purchase_date") or {}).get("date",""))]),
        },
        "maintenance_rate": round(len(maintenance_tickets) / max(total, 1) * 100, 1),
        "data_years": 3
    })
    print(f"  ✅  Analytics KPIs updated")

except Exception as e:
    print(f"  ❌  KPI error: {e}")

print(f"\n{'='*60}")
print("  ALL DONE! 3 years of data generated.")
print(f"  Assets: {len(assets)}")
print(f"  Telemetry: monthly readings per asset since purchase")
print(f"  Audit events: {len(audit_events)}")
print(f"  Maintenance tickets: {len(maintenance_tickets)}")
print(f"  Finance records: {len(finance_records)}")
print(f"{'='*60}\n")
