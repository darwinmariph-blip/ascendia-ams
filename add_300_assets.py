"""
Add ~233 more assets to reach ~300 total
Run: python3 add_300_assets.py
"""
import os, random, requests, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

SNIPEIT_URL = os.getenv("SNIPEIT_URL", "http://snipe-it.test")
TOKEN = os.getenv("SNIPEIT_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json", "Content-Type": "application/json"}

def api_get(endpoint):
    time.sleep(0.3)
    r = requests.get(f"{SNIPEIT_URL}/api/v1/{endpoint}", headers=HEADERS, timeout=15)
    return r.json()

def api_post(endpoint, data, retry=True):
    time.sleep(0.5)
    r = requests.post(f"{SNIPEIT_URL}/api/v1/{endpoint}", headers=HEADERS, json=data, timeout=15)
    res = r.json()
    if "Too many requests" in str(res) and retry:
        print("  ⏳ Rate limited — waiting 25 seconds...")
        time.sleep(25)
        return api_post(endpoint, data, retry=False)
    return res

def api_patch(endpoint, data, retry=True):
    time.sleep(0.5)
    r = requests.patch(f"{SNIPEIT_URL}/api/v1/{endpoint}", headers=HEADERS, json=data, timeout=15)
    res = r.json()
    if "Too many requests" in str(res) and retry:
        time.sleep(25)
        return api_patch(endpoint, data, retry=False)
    return res

# Get existing data
cats = {c["name"]: c["id"] for c in api_get("categories?limit=50").get("rows", [])}
locs = {l["name"]: l["id"] for l in api_get("locations?limit=50").get("rows", [])}
sups = {s["name"]: s["id"] for s in api_get("suppliers?limit=50").get("rows", [])}
statuses = {s["name"]: s["id"] for s in api_get("statuslabels?limit=50").get("rows", [])}
sups["APC"] = sups.get("APC by Schneider Electric", sups.get("APC"))

existing_models = {}
for m in api_get("models?limit=200").get("rows", []):
    existing_models[m["name"].lower()] = m["id"]
print(f"Existing models: {len(existing_models)}")

def get_or_create_model(name, cat_id):
    key = name.lower()
    if key in existing_models:
        return existing_models[key]
    result = api_post("models", {"name": name, "category_id": cat_id})
    if result.get("status") == "success":
        mid = result["payload"]["id"]
        existing_models[key] = mid
        return mid
    print(f"    Model failed: {name} — {result.get('messages','')}")
    return None

def get_status_id(year):
    age = 2026 - year
    if age >= 3:
        name = random.choices(["Ready to Deploy","Maintenance - High","Pending Repair","Archived (End of Life)"],weights=[60,15,15,10])[0]
    elif age == 2:
        name = random.choices(["Ready to Deploy","Maintenance - High","Pending Repair"],weights=[75,15,10])[0]
    else:
        name = random.choices(["Ready to Deploy","Awaiting Pickup"],weights=[90,10])[0]
    return statuses.get(name, list(statuses.values())[0])

ASSETS = [
  {"name":"Dell Latitude 5530","cat":"Laptops","sup":"Dell Philippines","loc":"QC-MAIN-IT_OFFICE","cost":85000,"year":2023,"count":8},
  {"name":"Acer Aspire TC-1750","cat":"Desktops","sup":"Acer Philippines","loc":"QC-MAIN-LAB1","cost":42000,"year":2023,"count":25},
  {"name":"HP EliteDesk 800 G9","cat":"Desktops","sup":"HP Philippines","loc":"QC-MAIN-LAB1","cost":55000,"year":2023,"count":10},
  {"name":"Epson EB-W51","cat":"Projectors","sup":"Epson Philippines","loc":"QC-MAIN-CLASS101","cost":35000,"year":2023,"count":4},
  {"name":"HP LaserJet Pro M404","cat":"Printers","sup":"HP Philippines","loc":"QC-MAIN-REGISTRAR","cost":22000,"year":2023,"count":3},
  {"name":"Cisco Catalyst 2960","cat":"Network Equipment","sup":"Cisco Philippines","loc":"QC-MAIN-IT_OFFICE","cost":75000,"year":2023,"count":3},
  {"name":"APC Smart-UPS 1500","cat":"UPS","sup":"APC","loc":"QC-MAIN-IT_OFFICE","cost":28000,"year":2023,"count":4},
  {"name":"Dell UltraSharp U2422H","cat":"Monitors","sup":"Dell Philippines","loc":"QC-MAIN-IT_OFFICE","cost":18000,"year":2023,"count":8},
  {"name":"Hikvision DS-2CD2143G2","cat":"Security Equipment","sup":"Hikvision Philippines","loc":"QC-MAIN","cost":12000,"year":2023,"count":5},
  {"name":"Canon imageRUNNER 2625","cat":"Printers","sup":"Canon Philippines","loc":"QC-MAIN-FINANCE","cost":45000,"year":2023,"count":2},
  {"name":"Dell Latitude 5540","cat":"Laptops","sup":"Dell Philippines","loc":"QC-MAIN-IT_OFFICE","cost":92000,"year":2024,"count":10},
  {"name":"MacBook Pro M3","cat":"Laptops","sup":"Apple Philippines","loc":"QC-MAIN-IT_OFFICE","cost":125000,"year":2024,"count":5},
  {"name":"Acer Aspire TC-1760","cat":"Desktops","sup":"Acer Philippines","loc":"QC-MAIN-LAB1","cost":45000,"year":2024,"count":30},
  {"name":"HP EliteDesk 805 G9","cat":"Desktops","sup":"HP Philippines","loc":"QC-MAIN-LAB1","cost":58000,"year":2024,"count":10},
  {"name":"Epson EB-X51 2024","cat":"Projectors","sup":"Epson Philippines","loc":"QC-MAIN-CLASS101","cost":32000,"year":2024,"count":5},
  {"name":"Cisco Catalyst 9200","cat":"Network Equipment","sup":"Cisco Philippines","loc":"QC-MAIN-IT_OFFICE","cost":120000,"year":2024,"count":2},
  {"name":"Ubiquiti UniFi AP-AC-Pro","cat":"Network Equipment","sup":"Ubiquiti Networks","loc":"QC-MAIN","cost":8500,"year":2024,"count":8},
  {"name":"APC Back-UPS Pro 1500","cat":"UPS","sup":"APC","loc":"QC-MAIN-IT_OFFICE","cost":15000,"year":2024,"count":5},
  {"name":"iPad Pro 12.9 2024","cat":"Tablets","sup":"Apple Philippines","loc":"QC-MAIN-IT_OFFICE","cost":72000,"year":2024,"count":6},
  {"name":"Logitech MeetUp","cat":"Audio Equipment","sup":"Logitech Philippines","loc":"QC-MAIN-CLASS101","cost":35000,"year":2024,"count":3},
  {"name":"Epson DS-870","cat":"Scanners","sup":"Epson Philippines","loc":"QC-MAIN-REGISTRAR","cost":28000,"year":2024,"count":2},
  {"name":"Dell UltraSharp U2723QE","cat":"Monitors","sup":"Dell Philippines","loc":"QC-MAIN-IT_OFFICE","cost":32000,"year":2024,"count":10},
  {"name":"Hikvision DS-2CD2T47G2","cat":"Security Equipment","sup":"Hikvision Philippines","loc":"QC-MAIN","cost":15000,"year":2024,"count":6},
  {"name":"Dell Latitude 5550","cat":"Laptops","sup":"Dell Philippines","loc":"QC-MAIN-IT_OFFICE","cost":98000,"year":2025,"count":8},
  {"name":"MacBook Air M3","cat":"Laptops","sup":"Apple Philippines","loc":"QC-MAIN-IT_OFFICE","cost":95000,"year":2025,"count":5},
  {"name":"Acer Aspire TC-1770","cat":"Desktops","sup":"Acer Philippines","loc":"QC-MAIN-LAB1","cost":48000,"year":2025,"count":20},
  {"name":"HP EliteDesk 810 G9","cat":"Desktops","sup":"HP Philippines","loc":"QC-MAIN-IT_OFFICE","cost":62000,"year":2025,"count":8},
  {"name":"Epson EB-L210W","cat":"Projectors","sup":"Epson Philippines","loc":"QC-MAIN-CLASS101","cost":65000,"year":2025,"count":4},
  {"name":"Cisco Catalyst 9300","cat":"Network Equipment","sup":"Cisco Philippines","loc":"QC-MAIN-IT_OFFICE","cost":185000,"year":2025,"count":1},
  {"name":"Ubiquiti Dream Machine Pro","cat":"Network Equipment","sup":"Ubiquiti Networks","loc":"QC-MAIN-IT_OFFICE","cost":45000,"year":2025,"count":1},
  {"name":"APC Smart-UPS 3000","cat":"UPS","sup":"APC","loc":"QC-MAIN-IT_OFFICE","cost":55000,"year":2025,"count":2},
  {"name":"Canon PIXMA G7070","cat":"Printers","sup":"Canon Philippines","loc":"QC-MAIN-REGISTRAR","cost":18000,"year":2025,"count":3},
  {"name":"iPad Air M2","cat":"Tablets","sup":"Apple Philippines","loc":"QC-MAIN-IT_OFFICE","cost":55000,"year":2025,"count":4},
  {"name":"Hikvision DS-2DE4A425IWG","cat":"Security Equipment","sup":"Hikvision Philippines","loc":"QC-MAIN","cost":22000,"year":2025,"count":4},
  {"name":"Wacom Cintiq 16","cat":"Tablets","sup":"Wacom Philippines","loc":"QC-MAIN-IT_OFFICE","cost":48000,"year":2025,"count":3},
]

# Get current highest tag number
all_assets = api_get("hardware?limit=500").get("rows", [])
tag_num = 200
for a in all_assets:
    try:
        n = int(a.get("asset_tag","0").split("-")[-1])
        if n >= tag_num:
            tag_num = n + 1
    except:
        pass
print(f"Starting tag number: {tag_num}")
print(f"Current total: {len(all_assets)}\n")

added = 0
errors = 0
skipped = 0

for batch in ASSETS:
    cat_id = cats.get(batch["cat"])
    loc_id = locs.get(batch["loc"])
    sup_id = sups.get(batch["sup"])

    if not cat_id:
        skipped += batch["count"]
        continue

    model_id = get_or_create_model(batch["name"], cat_id)
    if not model_id:
        skipped += batch["count"]
        continue

    print(f"  Adding {batch['count']}x {batch['name']} ({batch['year']})...")

    for i in range(batch["count"]):
        year = batch["year"]
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
        purchase_date = start + timedelta(days=random.randint(0, (end-start).days))
        status_id = get_status_id(year)
        tag = f"AAI-{year}-{tag_num:05d}"
        name = f"{batch['name']} #{i+1:03d}"

        payload = {
            "name": name,
            "asset_tag": tag,
            "status_id": status_id,
            "model_id": model_id,
            "purchase_date": purchase_date.strftime("%Y-%m-%d"),
            "purchase_cost": str(batch["cost"] + random.randint(-2000, 5000)),
            "notes": f"Acquired {year} — Batch procurement",
        }
        if loc_id:
            payload["location_id"] = loc_id
        if sup_id:
            payload["supplier_id"] = sup_id

        result = api_post("hardware", payload)
        if result.get("status") == "success":
            added += 1
            asset_id = result["payload"]["id"]
            ai = "High" if year <= 2023 else ("Medium" if year == 2024 else "Low")
            api_patch(f"hardware/{asset_id}", {
                "_snipeit_ai_priority_score_2": ai,
                "_snipeit_last_audit_date_5": f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            })
        else:
            errors += 1
            if errors <= 3:
                print(f"  ❌  {name}: {result.get('messages','')}")
        tag_num += 1

    print(f"    Done batch. Total added so far: {added}")

total = api_get("hardware?limit=1").get("total", 0)
print(f"\n{'='*50}")
print(f"  Added: {added} | Errors: {errors} | Skipped: {skipped}")
print(f"  Total assets now: {total}")
print(f"{'='*50}")
