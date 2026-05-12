"""
=============================================================
  Ascendia IT Asset Management — Phase 2b
  Procurement Intake — Auto-create assets from Purchase Orders
=============================================================
  HOW TO USE:
  1. Make sure snipeit_client.py is in the same folder
  2. Run:  python3 procurement_intake.py
=============================================================
  WHAT THIS SCRIPT DOES:
  - Reads Purchase Order (PO) data
  - For each item in the PO, auto-creates an asset in Snipe-IT
  - Tags each asset with: PO Number, category, location, status
  - Follows Ascendia asset tag format: AAI-{YEAR}-{SEQUENCE}
  - Skips duplicate PO numbers already in Snipe-IT
=============================================================
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from snipeit_client import SnipeITClient

load_dotenv()

client = SnipeITClient(
    base_url = os.getenv("SNIPEIT_URL", "http://snipe-it.test"),
    token    = os.getenv("SNIPEIT_TOKEN", ""),
)

# ══════════════════════════════════════════════════════════
#  SAMPLE PURCHASE ORDER DATA
#  In real life this comes from your Procurement System.
#  Each PO can have multiple line items (assets).
#
#  Fields:
#  - po_number:    Format PO-##### (from Procurement System)
#  - vendor:       Supplier name
#  - items:        List of assets being procured
#    - model_name: Hardware model
#    - category:   Must match a category in Snipe-IT
#    - quantity:   How many units
#    - location:   Must match a location name in Snipe-IT
#    - unit_cost:  Cost per unit in PHP
# ══════════════════════════════════════════════════════════

PURCHASE_ORDERS = [
    {
        "po_number":   "PO-00001",
        "vendor":      "Dell Philippines",
        "order_date":  "2026-05-11",
        "items": [
            {
                "model_name": "Dell Latitude 5540",
                "category":   "Laptops",
                "quantity":   3,
                "location":   "QC-MAIN-IT_OFFICE",
                "unit_cost":  65000,
            },
            {
                "model_name": "Dell UltraSharp Monitor",
                "category":   "Monitors",
                "quantity":   2,
                "location":   "QC-MAIN-IT_OFFICE",
                "unit_cost":  18000,
            },
        ],
    },
    {
        "po_number":   "PO-00002",
        "vendor":      "Apple Philippines",
        "order_date":  "2026-05-11",
        "items": [
            {
                "model_name": "MacBook Pro M3",
                "category":   "Laptops",
                "quantity":   2,
                "location":   "QC-MAIN-LAB1",
                "unit_cost":  120000,
            },
        ],
    },
    {
        "po_number":   "PO-00003",
        "vendor":      "Epson Philippines",
        "order_date":  "2026-05-11",
        "items": [
            {
                "model_name": "Epson EB-X51 Projector",
                "category":   "Projectors",
                "quantity":   2,
                "location":   "QC-MAIN-CLASS101",
                "unit_cost":  35000,
            },
        ],
    },
]


# ══════════════════════════════════════════════════════════
#  HELPER: Get or create a category in Snipe-IT
# ══════════════════════════════════════════════════════════

def get_or_create_category(name: str, category_cache: dict) -> int:
    if name in category_cache:
        return category_cache[name]

    # Try to find it
    data = client.list_categories()
    for cat in data.get("rows", []):
        if cat["name"].lower() == name.lower():
            category_cache[name] = cat["id"]
            return cat["id"]

    # Create it if not found
    result = client._post("categories", {
        "name":          name,
        "category_type": "asset",
    })
    if result.get("status") == "success":
        new_id = result["payload"]["id"]
        category_cache[name] = new_id
        print(f"  📁  Created category: {name}")
        return new_id

    raise Exception(f"Could not create category: {name}")


# ══════════════════════════════════════════════════════════
#  HELPER: Get or create a model in Snipe-IT
# ══════════════════════════════════════════════════════════

def get_or_create_model(model_name: str, category_id: int, model_cache: dict) -> int:
    if model_name in model_cache:
        return model_cache[model_name]

    # Try to find it
    data = client.list_models()
    for m in data.get("rows", []):
        if m["name"].lower() == model_name.lower():
            model_cache[model_name] = m["id"]
            return m["id"]

    # Create it if not found
    result = client._post("models", {
        "name":        model_name,
        "category_id": category_id,
    })
    if result.get("status") == "success":
        new_id = result["payload"]["id"]
        model_cache[model_name] = new_id
        print(f"  🖥️   Created model: {model_name}")
        return new_id

    raise Exception(f"Could not create model: {model_name}")


# ══════════════════════════════════════════════════════════
#  HELPER: Get location ID by name
# ══════════════════════════════════════════════════════════

def get_location_map() -> dict:
    data = client.list_locations()
    loc_map = {}
    for loc in data.get("rows", []):
        loc_map[loc["name"]] = loc["id"]
    return loc_map


# ══════════════════════════════════════════════════════════
#  HELPER: Get "Ready to Deploy" status ID
# ══════════════════════════════════════════════════════════

def get_ready_status_id() -> int:
    data = client.list_status_labels()
    for s in data.get("rows", []):
        if "ready" in s["name"].lower() or s.get("type") == "deployable":
            return s["id"]
    # fallback: return first deployable
    for s in data.get("rows", []):
        if s.get("type") == "deployable":
            return s["id"]
    raise Exception("No deployable status found. Create a 'Ready to Deploy' status in Snipe-IT.")


# ══════════════════════════════════════════════════════════
#  HELPER: Generate next asset tag
#  Format: AAI-{YEAR}-{5-digit sequence}
# ══════════════════════════════════════════════════════════

def generate_asset_tag(sequence: int) -> str:
    year = datetime.now().year
    return f"AAI-{year}-{sequence:05d}"


def get_next_sequence() -> int:
    """Find the highest existing sequence number and return next."""
    data   = client.list_assets(limit=500)
    assets = data.get("rows", [])
    max_seq = 0
    for a in assets:
        tag = a.get("asset_tag", "")
        parts = tag.split("-")
        if len(parts) == 3 and parts[0] == "AAI":
            try:
                seq = int(parts[2])
                if seq > max_seq:
                    max_seq = seq
            except ValueError:
                pass
    return max_seq + 1


# ══════════════════════════════════════════════════════════
#  MAIN: Process all Purchase Orders
# ══════════════════════════════════════════════════════════

def process_purchase_orders():
    print("\n" + "═" * 60)
    print("  PROCUREMENT INTAKE — Ascendia Academic Institution")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    location_map   = get_location_map()
    category_cache = {}
    model_cache    = {}
    status_id      = get_ready_status_id()
    sequence       = get_next_sequence()

    print(f"\n📍  Locations available: {list(location_map.keys())}")
    print(f"🏷️   Starting asset tag sequence: AAI-{datetime.now().year}-{sequence:05d}")
    print(f"✅  Status ID for 'Ready to Deploy': {status_id}\n")

    results = {
        "created": [],
        "skipped": [],
        "errors":  [],
    }

    for po in PURCHASE_ORDERS:
        po_number  = po["po_number"]
        vendor     = po["vendor"]
        order_date = po["order_date"]

        print(f"\n📦  Processing {po_number} — {vendor} ({order_date})")
        print(f"    {len(po['items'])} line item(s)")

        for item in po["items"]:
            model_name  = item["model_name"]
            category    = item["category"]
            quantity    = item["quantity"]
            location_nm = item["location"]
            unit_cost   = item["unit_cost"]

            # Validate location
            location_id = location_map.get(location_nm)
            if not location_id:
                msg = f"Location '{location_nm}' not found in Snipe-IT"
                print(f"  ❌  SKIPPED {model_name} — {msg}")
                results["errors"].append({"item": model_name, "reason": msg})
                continue

            # Get or create category and model
            try:
                category_id = get_or_create_category(category, category_cache)
                model_id    = get_or_create_model(model_name, category_id, model_cache)
            except Exception as e:
                print(f"  ❌  ERROR setting up {model_name}: {e}")
                results["errors"].append({"item": model_name, "reason": str(e)})
                continue

            # Create one asset per unit
            for unit in range(quantity):
                asset_tag = generate_asset_tag(sequence)
                sequence += 1

                try:
                    result = client.create_asset(
                        asset_tag   = asset_tag,
                        status_id   = status_id,
                        model_id    = model_id,
                        name        = f"{model_name}",
                        location_id = location_id,
                        notes       = f"Procured via {po_number} from {vendor} on {order_date}.",
                        custom_fields = {
                            # Update these keys after checking Settings → Custom Fields
                            # The key format is: _snipeit_{field_name_lowercase_with_underscores}_{id}
                            # Run print_custom_field_keys() below to find your exact keys
                        }
                    )

                    if result.get("status") == "success":
                        print(f"  ✅  [{asset_tag}] {model_name} → {location_nm}")
                        results["created"].append({
                            "tag":      asset_tag,
                            "model":    model_name,
                            "po":       po_number,
                            "location": location_nm,
                            "cost":     unit_cost,
                        })
                    else:
                        msg = str(result.get("messages", "Unknown error"))
                        print(f"  ❌  ERROR creating {model_name}: {msg}")
                        results["errors"].append({"item": model_name, "reason": msg})

                except Exception as e:
                    print(f"  ❌  ERROR: {e}")
                    results["errors"].append({"item": model_name, "reason": str(e)})

    # ── Summary ──────────────────────────────────────────
    total_cost = sum(a["cost"] for a in results["created"])

    print("\n" + "═" * 60)
    print("  PROCUREMENT INTAKE COMPLETE — Summary")
    print("═" * 60)
    print(f"  ✅  Assets created : {len(results['created'])}")
    print(f"  ❌  Errors         : {len(results['errors'])}")
    print(f"  💰  Total value    : PHP {total_cost:,.2f}")

    if results["created"]:
        print(f"\n  Assets added:")
        for a in results["created"]:
            print(f"    • [{a['tag']}] {a['model']} — {a['location']} ({a['po']})")

    if results["errors"]:
        print(f"\n  Errors to fix:")
        for e in results["errors"]:
            print(f"    • {e['item']}: {e['reason']}")

    print("═" * 60 + "\n")
    return results


# ══════════════════════════════════════════════════════════
#  UTILITY: Print your custom field DB keys
#  Run this once to find the exact key names for PO Number
#  so you can add them to create_asset() above.
# ══════════════════════════════════════════════════════════

def print_custom_field_keys():
    print("\n🔑  Your Snipe-IT custom field keys:")
    data = client._get("fields")
    for f in data.get("rows", []):
        print(f"  Field: '{f['name']}' → DB key: '{f['db_column_name']}'")


# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Uncomment this to find your custom field keys first:
    # print_custom_field_keys()

    process_purchase_orders()
