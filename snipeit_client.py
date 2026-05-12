"""
=============================================================
  Ascendia IT Asset Management — Phase 1
  Snipe-IT API Client + Custom Fields Setup
=============================================================
  HOW TO USE:
  1. Install dependencies:  pip install requests python-dotenv
  2. Create a .env file in the same folder (see below)
  3. Run:  python snipeit_client.py
=============================================================
  .env file contents:
  SNIPEIT_URL=http://localhost:8000   (your Snipe-IT URL)
  SNIPEIT_TOKEN=your_api_token_here
=============================================================
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ─────────────────────────────────────────
SNIPEIT_URL   = os.getenv("SNIPEIT_URL", "http://localhost:8000")
SNIPEIT_TOKEN = os.getenv("SNIPEIT_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {SNIPEIT_TOKEN}",
    "Accept":        "application/json",
    "Content-Type":  "application/json",
}


# ══════════════════════════════════════════════════════════
#  CORE API CLIENT
# ══════════════════════════════════════════════════════════

class SnipeITClient:
    """Thin wrapper around the Snipe-IT REST API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session  = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept":        "application/json",
            "Content-Type":  "application/json",
        })

    # ── Internal helpers ──────────────────────────────────

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}/api/v1/{endpoint}"
        r   = self.session.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/api/v1/{endpoint}"
        r   = self.session.post(url, json=payload)
        r.raise_for_status()
        return r.json()

    def _patch(self, endpoint: str, payload: dict):
        url = f"{self.base_url}/api/v1/{endpoint}"
        r   = self.session.patch(url, json=payload)
        r.raise_for_status()
        return r.json()

    # ── Connection test ───────────────────────────────────

    def test_connection(self):
        """Ping Snipe-IT and return basic account info."""
        result = self._get("users/me")
        print("✅  Connected to Snipe-IT!")
        print(f"    Logged in as: {result.get('name')} ({result.get('username')})")
        return result

    # ══════════════════════════════════════════════════════
    #  ASSETS
    # ══════════════════════════════════════════════════════

    def list_assets(self, limit: int = 10, offset: int = 0):
        """Fetch a page of assets."""
        return self._get("hardware", params={"limit": limit, "offset": offset})

    def get_asset(self, asset_id: int):
        """Fetch a single asset by its ID."""
        return self._get(f"hardware/{asset_id}")

    def get_asset_by_tag(self, asset_tag: str):
        """Look up an asset by its physical tag (e.g. AAI-2026-00125)."""
        return self._get("hardware/bytag/{asset_tag}".replace("{asset_tag}", asset_tag))

    def create_asset(self, asset_tag: str, status_id: int, model_id: int,
                     name: str = None, serial: str = None,
                     location_id: int = None, notes: str = None,
                     custom_fields: dict = None):
        """
        Create a new asset in Snipe-IT.

        custom_fields example:
            {"_snipeit_ai_priority_1": "Low",
             "_snipeit_po_number_2":   "PO-00123"}
        """
        payload = {
            "asset_tag":  asset_tag,
            "status_id":  status_id,
            "model_id":   model_id,
        }
        if name:        payload["name"]        = name
        if serial:      payload["serial"]      = serial
        if location_id: payload["location_id"] = location_id
        if notes:       payload["notes"]       = notes
        if custom_fields:
            payload.update(custom_fields)

        result = self._post("hardware", payload)
        if result.get("status") == "success":
            print(f"✅  Asset created — ID: {result['payload']['id']}  Tag: {asset_tag}")
        else:
            print(f"❌  Asset creation failed: {result.get('messages')}")
        return result

    def update_asset(self, asset_id: int, fields: dict):
        """Partially update an existing asset."""
        result = self._patch(f"hardware/{asset_id}", fields)
        if result.get("status") == "success":
            print(f"✅  Asset {asset_id} updated.")
        else:
            print(f"❌  Update failed: {result.get('messages')}")
        return result

    def checkout_asset(self, asset_id: int, user_id: int, note: str = ""):
        """Check out an asset to a user."""
        payload = {
            "checkout_to_type": "user",
            "assigned_user":    user_id,
            "note":             note,
        }
        result = self._post(f"hardware/{asset_id}/checkout", payload)
        if result.get("status") == "success":
            print(f"✅  Asset {asset_id} checked out to user {user_id}.")
        else:
            print(f"❌  Checkout failed: {result.get('messages')}")
        return result

    def checkin_asset(self, asset_id: int, note: str = ""):
        """Check in (return) an asset."""
        result = self._post(f"hardware/{asset_id}/checkin", {"note": note})
        if result.get("status") == "success":
            print(f"✅  Asset {asset_id} checked in.")
        else:
            print(f"❌  Checkin failed: {result.get('messages')}")
        return result

    # ══════════════════════════════════════════════════════
    #  USERS
    # ══════════════════════════════════════════════════════

    def list_users(self, limit: int = 10):
        return self._get("users", params={"limit": limit})

    def get_user(self, user_id: int):
        return self._get(f"users/{user_id}")

    def create_user(self, first_name: str, last_name: str, username: str,
                    email: str, department_id: int, password: str,
                    employee_num: str = None):
        """
        Create a new user.
        NOTE: email must end in @ascendia.edu.ph per BR-Email rule.
        """
        if not email.endswith("@ascendia.edu.ph"):
            raise ValueError(f"Email must end in @ascendia.edu.ph — got: {email}")

        payload = {
            "first_name":     first_name,
            "last_name":      last_name,
            "username":       username,
            "email":          email,
            "department_id":  department_id,
            "password":       password,
            "password_confirmation": password,
            "activated":      True,
        }
        if employee_num:
            payload["employee_num"] = employee_num

        result = self._post("users", payload)
        if result.get("status") == "success":
            print(f"✅  User created — {first_name} {last_name} ({email})")
        else:
            print(f"❌  User creation failed: {result.get('messages')}")
        return result

    # ══════════════════════════════════════════════════════
    #  MAINTENANCE LOGS
    # ══════════════════════════════════════════════════════

    def list_maintenance_logs(self, asset_id: int = None):
        params = {}
        if asset_id:
            params["asset_id"] = asset_id
        return self._get("maintenances", params=params)

    def create_maintenance_log(self, asset_id: int, title: str,
                                maintenance_type: str, start_date: str,
                                notes: str = "", supplier_id: int = None,
                                completion_date: str = None):
        """
        Log a maintenance event for an asset.
        maintenance_type options: "Maintenance", "Repair", "Upgrade",
                                  "PAT Testing", "Calibration", "Software Support",
                                  "Hardware Support", "License Renewal", "Battery Replacement"
        start_date / completion_date format: "YYYY-MM-DD"
        """
        payload = {
            "asset_id":         asset_id,
            "title":            title,
            "maintenance_type": maintenance_type,
            "start_date":       start_date,
            "notes":            notes,
        }
        if supplier_id:      payload["supplier_id"]      = supplier_id
        if completion_date:  payload["completion_date"]  = completion_date

        result = self._post("maintenances", payload)
        if result.get("status") == "success":
            print(f"✅  Maintenance log created for asset {asset_id}.")
        else:
            print(f"❌  Maintenance log failed: {result.get('messages')}")
        return result

    # ══════════════════════════════════════════════════════
    #  DEPARTMENTS / LOCATIONS / CATEGORIES
    # ══════════════════════════════════════════════════════

    def list_departments(self):
        return self._get("departments")

    def list_locations(self):
        return self._get("locations")

    def list_categories(self):
        return self._get("categories")

    def list_status_labels(self):
        return self._get("statuslabels")

    def list_models(self):
        return self._get("models")


# ══════════════════════════════════════════════════════════
#  CUSTOM FIELDS SETUP
#  Run this ONCE after Snipe-IT is installed to create
#  the three custom fields defined in your architecture doc.
# ══════════════════════════════════════════════════════════

def setup_custom_fields(client: SnipeITClient):
    """
    Creates the custom fields required by Ascendia's data model.
    These must be created manually in the Snipe-IT UI (Settings →
    Custom Fields) OR via the API if your version supports it.

    This function prints exact instructions for each field.
    """

    print("\n" + "═" * 60)
    print("  CUSTOM FIELDS SETUP GUIDE")
    print("  Go to: Settings → Custom Fields → Create New Field")
    print("═" * 60)

    fields = [
        {
            "name":     "AI Priority",
            "type":     "text (dropdown)",
            "values":   "High, Med, Low",
            "applies":  "Assets (via Fieldset)",
            "rule":     "Required when maintenance log is created",
            "purpose":  "Records NLP urgency score from Hugging Face",
        },
        {
            "name":     "Last Audit Date",
            "type":     "date",
            "values":   "YYYY-MM-DD",
            "applies":  "Assets",
            "rule":     "Must be updated annually",
            "purpose":  "Tracks physical inventory audit cycles",
        },
        {
            "name":     "PO Number",
            "type":     "text",
            "values":   "Format: PO-#####  e.g. PO-00123",
            "applies":  "Assets",
            "rule":     "Populated during Procurement Intake",
            "purpose":  "Links each asset to its purchase order",
        },
    ]

    for i, f in enumerate(fields, 1):
        print(f"\n  [{i}] {f['name']}")
        print(f"      Type    : {f['type']}")
        print(f"      Values  : {f['values']}")
        print(f"      Applies : {f['applies']}")
        print(f"      Rule    : {f['rule']}")
        print(f"      Purpose : {f['purpose']}")

    print("\n" + "═" * 60)
    print("  After creating the fields, add them to a Fieldset")
    print("  called 'Ascendia Standard' and apply it to all")
    print("  hardware asset models.")
    print("═" * 60 + "\n")


# ══════════════════════════════════════════════════════════
#  CUSTOM STATUS LABELS SETUP
# ══════════════════════════════════════════════════════════

def setup_status_labels(client: SnipeITClient):
    """
    Creates the custom status labels defined in your architecture.
    Snipe-IT's /api/v1/statuslabels endpoint supports POST.
    """

    labels = [
        {
            "name":  "Awaiting Pickup",
            "type":  "pending",   # deployable
            "notes": "Assigned but not yet physically handed to user.",
        },
        {
            "name":  "Maintenance - High",
            "type":  "undeployable",
            "notes": "Urgent repair triggered by AI Priority = High.",
        },
        {
            "name":  "Pending Return",
            "type":  "pending",
            "notes": "Employee offboarded; device awaiting collection.",
        },
    ]

    print("\n📋  Creating custom status labels...")
    for label in labels:
        try:
            result = client._post("statuslabels", label)
            if result.get("status") == "success":
                print(f"  ✅  '{label['name']}' created.")
            else:
                print(f"  ⚠️   '{label['name']}': {result.get('messages')}")
        except Exception as e:
            print(f"  ❌  '{label['name']}' error: {e}")


# ══════════════════════════════════════════════════════════
#  QUICK-TEST — runs when you execute this file directly
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":

    if not SNIPEIT_TOKEN:
        print("❌  No API token found.")
        print("    Create a .env file with:")
        print("    SNIPEIT_URL=http://localhost:8000")
        print("    SNIPEIT_TOKEN=your_token_here")
        exit(1)

    client = SnipeITClient(SNIPEIT_URL, SNIPEIT_TOKEN)

    # 1 — Test connection
    print("\n🔌  Testing Snipe-IT connection...")
    client.test_connection()

    # 2 — Print custom fields setup guide
    setup_custom_fields(client)

    # 3 — Create custom status labels
    setup_status_labels(client)

    # 4 — Quick read test: list first 5 assets
    print("📦  Fetching first 5 assets from Snipe-IT...")
    assets = client.list_assets(limit=5)
    total  = assets.get("total", 0)
    rows   = assets.get("rows", [])
    print(f"    Total assets in system: {total}")
    for a in rows:
        tag    = a.get("asset_tag", "—")
        name   = a.get("name", "—")
        status = a.get("status_label", {}).get("name", "—")
        print(f"    • [{tag}]  {name}  —  {status}")

    print("\n✅  Phase 1 complete! Your Snipe-IT client is ready.")
    print("    Next step → Phase 2a: HRIS User Sync")
