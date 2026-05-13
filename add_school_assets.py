"""
=============================================================
  Ascendia AMS — Add Realistic School Assets
  Adds desktops, printers, tablets, network devices, etc.
=============================================================
  Run:  python3 add_school_assets.py
=============================================================
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from snipeit_client import SnipeITClient

load_dotenv()

client = SnipeITClient(
    base_url = os.getenv("SNIPEIT_URL", "http://snipe-it.test"),
    token    = os.getenv("SNIPEIT_TOKEN", ""),
)

# ── Get existing IDs ──────────────────────────────────────
def get_status_id(name):
    data = client.list_status_labels()
    for s in data.get("rows", []):
        if name.lower() in s["name"].lower():
            return s["id"]
    return 2  # default Ready to Deploy

def get_or_create_category(name):
    data = client.list_categories()
    for c in data.get("rows", []):
        if c["name"].lower() == name.lower():
            return c["id"]
    result = client._post("categories", {"name": name, "category_type": "asset"})
    if result.get("status") == "success":
        print(f"  📁  Created category: {name}")
        return result["payload"]["id"]
    return None

def get_or_create_model(name, category_id):
    data = client.list_models()
    for m in data.get("rows", []):
        if m["name"].lower() == name.lower():
            return m["id"]
    result = client._post("models", {"name": name, "category_id": category_id})
    if result.get("status") == "success":
        return result["payload"]["id"]
    return None

def get_location_map():
    data = client.list_locations()
    return {l["name"]: l["id"] for l in data.get("rows", [])}

def get_next_sequence():
    assets = client.list_assets(limit=500).get("rows", [])
    max_seq = 0
    for a in assets:
        tag = a.get("asset_tag", "")
        parts = tag.split("-")
        if len(parts) == 3 and parts[0] == "AAI":
            try:
                seq = int(parts[2])
                if seq > max_seq:
                    max_seq = seq
            except:
                pass
    return max_seq + 1

def tag(seq):
    return f"AAI-{datetime.now().year}-{seq:05d}"

# ── Asset definitions ─────────────────────────────────────
ASSETS_TO_ADD = [
    # ── Computer Lab 1 (30 student stations) ─────────────
    *[{"name": "Acer Aspire TC Desktop", "category": "Desktops", "location": "QC-MAIN-LAB1", "cost": 28000} for _ in range(30)],

    # ── IT Office ─────────────────────────────────────────
    {"name": "HP EliteDesk 800 Desktop", "category": "Desktops",  "location": "QC-MAIN-IT_OFFICE", "cost": 35000},
    {"name": "HP LaserJet Pro M404dn",   "category": "Printers",  "location": "QC-MAIN-IT_OFFICE", "cost": 18000},
    {"name": "Canon imageCLASS MF644Cdw","category": "Printers",  "location": "QC-MAIN-IT_OFFICE", "cost": 22000},
    {"name": "Cisco SG350-28 Switch",    "category": "Network Equipment", "location": "QC-MAIN-IT_OFFICE", "cost": 45000},
    {"name": "Cisco RV340 Router",       "category": "Network Equipment", "location": "QC-MAIN-IT_OFFICE", "cost": 28000},
    {"name": "APC UPS 1500VA",           "category": "UPS",       "location": "QC-MAIN-IT_OFFICE", "cost": 12000},

    # ── Registrar's Office ────────────────────────────────
    {"name": "HP EliteDesk 600 Desktop", "category": "Desktops",  "location": "QC-MAIN-REGISTRAR", "cost": 30000},
    {"name": "HP EliteDesk 600 Desktop", "category": "Desktops",  "location": "QC-MAIN-REGISTRAR", "cost": 30000},
    {"name": "Canon imageCLASS MF267dw", "category": "Printers",  "location": "QC-MAIN-REGISTRAR", "cost": 15000},
    {"name": "Epson DS-530 Scanner",     "category": "Scanners",  "location": "QC-MAIN-REGISTRAR", "cost": 18000},

    # ── Finance Office ────────────────────────────────────
    {"name": "HP EliteDesk 600 Desktop", "category": "Desktops",  "location": "QC-MAIN-FINANCE",   "cost": 30000},
    {"name": "HP EliteDesk 600 Desktop", "category": "Desktops",  "location": "QC-MAIN-FINANCE",   "cost": 30000},
    {"name": "HP LaserJet Pro M203dw",   "category": "Printers",  "location": "QC-MAIN-FINANCE",   "cost": 12000},
    {"name": "APC UPS 650VA",            "category": "UPS",       "location": "QC-MAIN-FINANCE",   "cost": 6000},

    # ── Classroom 101 ─────────────────────────────────────
    {"name": "Epson EB-X51 Projector",   "category": "Projectors","location": "QC-MAIN-CLASS101",  "cost": 35000},
    {"name": "Logitech Z623 Speakers",   "category": "Audio Equipment", "location": "QC-MAIN-CLASS101", "cost": 8000},
    {"name": "Wacom Intuos Tablet",      "category": "Tablets",   "location": "QC-MAIN-CLASS101",  "cost": 6500},

    # ── Faculty Tablets (for professors) ──────────────────
    {"name": "iPad 10th Gen",            "category": "Tablets",   "location": "QC-MAIN-IT_OFFICE", "cost": 32000},
    {"name": "iPad 10th Gen",            "category": "Tablets",   "location": "QC-MAIN-IT_OFFICE", "cost": 32000},
    {"name": "iPad 10th Gen",            "category": "Tablets",   "location": "QC-MAIN-IT_OFFICE", "cost": 32000},

    # ── Network Infrastructure ────────────────────────────
    {"name": "Ubiquiti UniFi AP AC Pro", "category": "Network Equipment", "location": "QC-MAIN",  "cost": 8500},
    {"name": "Ubiquiti UniFi AP AC Pro", "category": "Network Equipment", "location": "QC-MAIN",  "cost": 8500},
    {"name": "Ubiquiti UniFi AP AC Pro", "category": "Network Equipment", "location": "QC-MAIN",  "cost": 8500},
    {"name": "APC Smart-UPS 3000VA",     "category": "UPS",       "location": "QC-MAIN-IT_OFFICE", "cost": 35000},

    # ── Security / CCTV ───────────────────────────────────
    {"name": "Hikvision IP Camera",      "category": "Security Equipment", "location": "QC-MAIN", "cost": 5500},
    {"name": "Hikvision IP Camera",      "category": "Security Equipment", "location": "QC-MAIN", "cost": 5500},
    {"name": "Hikvision NVR DS-7608NI",  "category": "Security Equipment", "location": "QC-MAIN-IT_OFFICE", "cost": 18000},
]

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  ASCENDIA AMS — ADDING REALISTIC SCHOOL ASSETS")
    print(f"  Total assets to add: {len(ASSETS_TO_ADD)}")
    print("═" * 60)

    location_map   = get_location_map()
    category_cache = {}
    model_cache    = {}
    status_id      = get_status_id("ready")
    sequence       = get_next_sequence()

    print(f"\n  Starting at sequence: AAI-{datetime.now().year}-{sequence:05d}")
    print(f"  Status ID (Ready to Deploy): {status_id}\n")

    created = 0
    errors  = 0

    for asset in ASSETS_TO_ADD:
        name     = asset["name"]
        category = asset["category"]
        location = asset["location"]
        cost     = asset["cost"]

        # Get location ID
        loc_id = location_map.get(location)
        if not loc_id:
            print(f"  ❌  Location not found: {location}")
            errors += 1
            continue

        # Get or create category
        if category not in category_cache:
            cat_id = get_or_create_category(category)
            category_cache[category] = cat_id
        cat_id = category_cache[category]

        # Get or create model
        model_key = f"{name}_{cat_id}"
        if model_key not in model_cache:
            model_id = get_or_create_model(name, cat_id)
            model_cache[model_key] = model_id
        model_id = model_cache[model_key]

        # Create asset
        asset_tag = tag(sequence)
        sequence += 1

        try:
            result = client.create_asset(
                asset_tag=asset_tag,
                status_id=status_id,
                model_id=model_id,
                name=name,
                location_id=loc_id,
            )
            if result.get("status") == "success":
                aid = result["payload"]["id"]
                client.update_asset(aid, {"purchase_cost": str(cost), "purchase_date": "2026-01-01"})
            if result.get("status") == "success":
                print(f"  ✅  [{asset_tag}] {name} → {location}")
                created += 1
            else:
                print(f"  ❌  Failed: {name} — {result.get('messages')}")
                errors += 1
        except Exception as e:
            print(f"  ❌  Error: {e}")
            errors += 1

    print("\n" + "═" * 60)
    print(f"  DONE — {created} assets created, {errors} errors")
    print(f"  Total assets in system: {9 + created}")
    print(f"  Total inventory value added: ₱{sum(a['cost'] for a in ASSETS_TO_ADD):,}")
    print("═" * 60 + "\n")
