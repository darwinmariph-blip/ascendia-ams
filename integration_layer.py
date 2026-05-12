"""
=============================================================
  Ascendia IT Asset Management — Complete Integration Layer
  Includes:
  1. Redis Cache Layer
  2. Audit Event Logger
  3. Smart Notification Engine
  4. License Management
  5. Disposal/Retirement Workflow
  6. FastAPI REST API Service
=============================================================
  HOW TO USE:
  pip3 install fastapi uvicorn redis pymongo
  python3 integration_layer.py
=============================================================
"""

import os
import json
import redis
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from snipeit_client import SnipeITClient

load_dotenv()

# ── Connections ───────────────────────────────────────────
snipe  = SnipeITClient(os.getenv("SNIPEIT_URL"), os.getenv("SNIPEIT_TOKEN"))
mongo  = MongoClient("mongodb://localhost:27017/")
db     = mongo["ascendia_ams"]
cache  = redis.Redis(host="localhost", port=6379, decode_responses=True)


# ══════════════════════════════════════════════════════════
#  1. REDIS CACHE LAYER
# ══════════════════════════════════════════════════════════

class CacheLayer:
    """Caches Snipe-IT API responses to reduce repeated calls."""

    def __init__(self, redis_client, ttl=300):
        self.r   = redis_client
        self.ttl = ttl  # seconds

    def get_assets(self):
        cached = self.r.get("cache:assets")
        if cached:
            print("  📦  Assets loaded from Redis cache")
            return json.loads(cached)
        print("  🌐  Fetching assets from Snipe-IT...")
        data = snipe.list_assets(limit=500)
        self.r.setex("cache:assets", self.ttl, json.dumps(data))
        return data

    def get_users(self):
        cached = self.r.get("cache:users")
        if cached:
            print("  👥  Users loaded from Redis cache")
            return json.loads(cached)
        print("  🌐  Fetching users from Snipe-IT...")
        data = snipe.list_users(limit=500)
        self.r.setex("cache:users", self.ttl, json.dumps(data))
        return data

    def invalidate(self, key=None):
        if key:
            self.r.delete(f"cache:{key}")
        else:
            for k in self.r.scan_iter("cache:*"):
                self.r.delete(k)
        print("  🗑️   Cache invalidated.")

    def store_session(self, user_id, session_data, ttl=3600):
        self.r.setex(f"session:{user_id}", ttl, json.dumps(session_data))

    def get_session(self, user_id):
        data = self.r.get(f"session:{user_id}")
        return json.loads(data) if data else None

    def stats(self):
        keys = list(self.r.scan_iter("cache:*"))
        print(f"  📊  Redis cache keys: {len(keys)}")
        for k in keys:
            ttl = self.r.ttl(k)
            print(f"    • {k} (expires in {ttl}s)")


# ══════════════════════════════════════════════════════════
#  2. AUDIT EVENT LOGGER
# ══════════════════════════════════════════════════════════

audit_col = db["audit_events"]

def log_audit_event(action, actor, asset_tag=None, asset_id=None,
                    before=None, after=None, process=None, notes=""):
    """
    Log every system change with full before/after trail.
    Implements the Audit Event Logger from the Business Architecture.
    """
    event = {
        "event_id":  f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
        "action":    action,
        "actor":     actor,
        "asset_tag": asset_tag,
        "asset_id":  asset_id,
        "before":    before,
        "after":     after,
        "process":   process,
        "notes":     notes,
        "timestamp": datetime.now(),
    }
    audit_col.insert_one(event)
    print(f"  📝  Audit logged — [{action}] by {actor}" + (f" on {asset_tag}" if asset_tag else ""))
    return event["event_id"]


def get_audit_trail(asset_tag=None, limit=20):
    """Get audit trail for an asset or the whole system."""
    query = {"asset_tag": asset_tag} if asset_tag else {}
    return list(audit_col.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))


# ══════════════════════════════════════════════════════════
#  3. SMART NOTIFICATION ENGINE
# ══════════════════════════════════════════════════════════

notifications_col = db["notifications"]

def send_notification(recipient, role, subject, message, priority="normal",
                      asset_tag=None, action_required=None):
    """
    Smart notification engine — logs notifications and simulates sending.
    In production, replace print with SMTP/Teams/email API call.
    """
    notif = {
        "notif_id":        f"NTF-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
        "recipient":       recipient,
        "role":            role,
        "subject":         subject,
        "message":         message,
        "priority":        priority,
        "asset_tag":       asset_tag,
        "action_required": action_required,
        "sent_at":         datetime.now(),
        "status":          "sent",
    }
    notifications_col.insert_one(notif)

    icon = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🔔"
    print(f"  {icon}  Notification → {recipient} ({role})")
    print(f"      Subject: {subject}")
    if action_required:
        print(f"      Action:  {action_required}")
    return notif["notif_id"]


def notify_high_priority_maintenance(asset_tag, asset_name, issue_notes):
    """BR003 — notify IT Support Manager when AI score is High."""
    send_notification(
        recipient       = "Roberto Garcia",
        role            = "IT Asset Manager",
        subject         = f"[HIGH PRIORITY] Maintenance required — {asset_tag}",
        message         = f"Asset {asset_tag} ({asset_name}) has been flagged as HIGH priority.\nIssue: {issue_notes}",
        priority        = "high",
        asset_tag       = asset_tag,
        action_required = "Escalate to immediate repair queue.",
    )
    send_notification(
        recipient       = "Jose Reyes",
        role            = "IT Technician",
        subject         = f"[ACTION REQUIRED] Repair — {asset_tag}",
        message         = f"Please inspect {asset_tag} ({asset_name}) immediately.\nIssue: {issue_notes}",
        priority        = "high",
        asset_tag       = asset_tag,
        action_required = "Perform physical inspection and repair.",
    )


def notify_pending_return(user_name, asset_tag, asset_name):
    """Notify when an offboarded employee still has assets."""
    send_notification(
        recipient       = user_name,
        role            = "Employee",
        subject         = f"Asset Return Required — {asset_tag}",
        message         = f"Please return {asset_tag} ({asset_name}) to the IT office.",
        priority        = "high",
        asset_tag       = asset_tag,
        action_required = "Return asset within 48 hours.",
    )
    send_notification(
        recipient       = "Roberto Garcia",
        role            = "IT Asset Manager",
        subject         = f"Pending Return — {asset_tag} from {user_name}",
        message         = f"{user_name} has been offboarded. Asset {asset_tag} pending return.",
        priority        = "medium",
        asset_tag       = asset_tag,
        action_required = "Follow up with HR if not returned in 48 hours.",
    )


def notify_license_expiry(license_name, expiry_date, seats_used, seats_total):
    """Alert when a software license is expiring."""
    send_notification(
        recipient       = "Roberto Garcia",
        role            = "IT Asset Manager",
        subject         = f"License Expiring — {license_name}",
        message         = f"{license_name} expires on {expiry_date}. Usage: {seats_used}/{seats_total} seats.",
        priority        = "medium",
        action_required = "Renew or reclaim unused seats before expiry.",
    )


# ══════════════════════════════════════════════════════════
#  4. LICENSE MANAGEMENT
# ══════════════════════════════════════════════════════════

licenses_col = db["software_licenses"]

def create_license(name, vendor, product_key, seats_total,
                   purchase_date, expiry_date, cost, po_number):
    """Create a software license record."""
    lic = {
        "license_id":   f"LIC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "name":         name,
        "vendor":       vendor,
        "product_key":  product_key,
        "seats_total":  seats_total,
        "seats_used":   0,
        "seats_avail":  seats_total,
        "purchase_date": purchase_date,
        "expiry_date":  expiry_date,
        "cost":         cost,
        "po_number":    po_number,
        "assigned_to":  [],
        "status":       "Active",
        "created_at":   datetime.now(),
    }
    licenses_col.insert_one(lic)
    print(f"  📄  License created — {name} ({seats_total} seats, expires {expiry_date})")
    return lic["license_id"]


def assign_license(license_id, user_name, asset_tag=None):
    """Assign a license seat to a user/device."""
    lic = licenses_col.find_one({"license_id": license_id})
    if not lic:
        print(f"  ❌  License {license_id} not found.")
        return False
    if lic["seats_avail"] <= 0:
        print(f"  ❌  No seats available for {lic['name']}.")
        notify_license_expiry(lic["name"], lic["expiry_date"], lic["seats_used"], lic["seats_total"])
        return False
    licenses_col.update_one(
        {"license_id": license_id},
        {"$inc": {"seats_used": 1, "seats_avail": -1},
         "$push": {"assigned_to": {"user": user_name, "asset": asset_tag, "assigned_at": datetime.now()}}}
    )
    log_audit_event("LICENSE_ASSIGNED", "System", notes=f"{lic['name']} → {user_name}")
    print(f"  ✅  License '{lic['name']}' assigned to {user_name}")
    return True


def check_license_health():
    """Check all licenses for expiry or overuse."""
    print("\n  🔍  License health check...")
    for lic in licenses_col.find({"status": "Active"}):
        utilization = (lic["seats_used"] / lic["seats_total"] * 100) if lic["seats_total"] > 0 else 0
        expiry = datetime.strptime(lic["expiry_date"], "%Y-%m-%d")
        days_left = (expiry - datetime.now()).days
        icon = "🔴" if days_left < 30 or utilization > 90 else "🟡" if days_left < 90 else "🟢"
        print(f"  {icon}  {lic['name']} — {lic['seats_used']}/{lic['seats_total']} seats ({utilization:.0f}%) — expires in {days_left} days")
        if days_left < 30:
            notify_license_expiry(lic["name"], lic["expiry_date"], lic["seats_used"], lic["seats_total"])


# ══════════════════════════════════════════════════════════
#  5. DISPOSAL / RETIREMENT WORKFLOW
# ══════════════════════════════════════════════════════════

disposals_col = db["disposal_records"]

def initiate_disposal(asset_id, asset_tag, asset_name, requested_by, reason):
    """
    Start the disposal workflow.
    BR005: Retired assets must have a disposal note.
    Evidence gates must pass before final disposal.
    """
    record = {
        "disposal_id":     f"DSP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":        asset_id,
        "asset_tag":       asset_tag,
        "asset_name":      asset_name,
        "requested_by":    requested_by,
        "reason":          reason,
        "stage":           "Pending Return",
        "evidence": {
            "asset_returned":    False,
            "data_wiped":        False,
            "disposal_cert":     None,
            "finance_approved":  False,
        },
        "created_at":  datetime.now(),
        "completed_at": None,
        "notes":       [],
    }
    disposals_col.insert_one(record)

    # Update Snipe-IT status to Pending Return
    snipe.update_asset(asset_id, {"status_id": 5})  # adjust ID as needed
    log_audit_event("DISPOSAL_INITIATED", requested_by, asset_tag=asset_tag,
                    after={"stage": "Pending Return"}, process="Disposal Workflow")

    send_notification(
        recipient       = "Roberto Garcia",
        role            = "IT Asset Manager",
        subject         = f"Disposal Initiated — {asset_tag}",
        message         = f"Disposal workflow started for {asset_tag} ({asset_name}).\nReason: {reason}",
        priority        = "medium",
        asset_tag       = asset_tag,
        action_required = "Verify asset return and begin data wiping.",
    )
    print(f"  🗑️   Disposal initiated — {asset_tag} | Stage: Pending Return")
    return record["disposal_id"]


def advance_disposal(disposal_id, evidence_key, value, actor):
    """Advance disposal through evidence gates."""
    disposals_col.update_one(
        {"disposal_id": disposal_id},
        {"$set": {f"evidence.{evidence_key}": value}}
    )
    record = disposals_col.find_one({"disposal_id": disposal_id})
    ev = record["evidence"]

    # Check if all gates passed
    all_passed = all([
        ev["asset_returned"],
        ev["data_wiped"],
        ev["disposal_cert"],
        ev["finance_approved"],
    ])

    if all_passed:
        disposals_col.update_one(
            {"disposal_id": disposal_id},
            {"$set": {"stage": "Disposed", "completed_at": datetime.now()}}
        )
        log_audit_event("DISPOSAL_COMPLETED", actor,
                        asset_tag=record["asset_tag"],
                        after={"stage": "Disposed"}, process="Disposal Workflow")
        print(f"  ✅  Disposal {disposal_id} COMPLETED — all evidence gates passed!")
    else:
        remaining = [k for k, v in ev.items() if not v]
        print(f"  ⏳  Disposal {disposal_id} advancing — still needs: {remaining}")

    log_audit_event(f"DISPOSAL_{evidence_key.upper()}", actor,
                    asset_tag=record["asset_tag"],
                    after={evidence_key: value}, process="Disposal Workflow")


# ══════════════════════════════════════════════════════════
#  RUN DEMO
# ══════════════════════════════════════════════════════════

def run_full_demo():
    print("\n" + "═" * 60)
    print("  ASCENDIA AMS — FULL INTEGRATION LAYER DEMO")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # 1. Redis Cache
    print("\n\n1️⃣   REDIS CACHE LAYER")
    print("─" * 40)
    c = CacheLayer(cache)
    assets = c.get_assets()
    users  = c.get_users()
    assets2 = c.get_assets()  # should hit cache
    c.stats()
    c.store_session("darwin.admin", {"role": "IT Admin", "login_time": str(datetime.now())})
    print(f"  💾  Session stored for darwin.admin")

    # 2. Audit Logger
    print("\n\n2️⃣   AUDIT EVENT LOGGER")
    print("─" * 40)
    log_audit_event("ASSET_CHECKOUT", "Roberto Garcia",
                    asset_tag="AAI-2026-00002", asset_id=2,
                    before={"status": "Ready to Deploy"},
                    after={"status": "Deployed", "assigned_to": "Maria Santos"},
                    process="Asset Assignment")
    log_audit_event("AI_SCORE_UPDATED", "AI Scorer",
                    asset_tag="AAI-2026-00001", asset_id=1,
                    before={"ai_priority": "Unscored"},
                    after={"ai_priority": "High", "status": "Maintenance-High"},
                    process="Maintenance Processing")
    log_audit_event("USER_SYNCED", "HRIS Integration",
                    notes="8 users synced from HR system", process="User Sync")

    # 3. Notifications
    print("\n\n3️⃣   SMART NOTIFICATION ENGINE")
    print("─" * 40)
    notify_high_priority_maintenance(
        asset_tag   = "AAI-2026-00001",
        asset_name  = "Dell Latitude 5540",
        issue_notes = "Unit fails to power on. Hardware failure detected.",
    )
    notify_pending_return("Ana Cruz", "AAI-2026-00003", "Dell Latitude 5540")

    # 4. Licenses
    print("\n\n4️⃣   LICENSE MANAGEMENT")
    print("─" * 40)
    lic1 = create_license(
        name="Microsoft Office 365",
        vendor="Microsoft Philippines",
        product_key="XXXXX-XXXXX-XXXXX",
        seats_total=20,
        purchase_date="2026-01-01",
        expiry_date="2027-01-01",
        cost=45000,
        po_number="PO-00004",
    )
    lic2 = create_license(
        name="Adobe Creative Cloud",
        vendor="Adobe Philippines",
        product_key="YYYYY-YYYYY-YYYYY",
        seats_total=5,
        purchase_date="2026-01-01",
        expiry_date="2026-06-01",
        cost=30000,
        po_number="PO-00005",
    )
    assign_license(lic1, "Maria Santos",  "AAI-2026-00002")
    assign_license(lic1, "Miguel Torres", "AAI-2026-00006")
    assign_license(lic2, "Liza Mendoza",  "AAI-2026-00003")
    check_license_health()

    # 5. Disposal Workflow
    print("\n\n5️⃣   DISPOSAL / RETIREMENT WORKFLOW")
    print("─" * 40)
    d1 = initiate_disposal(
        asset_id     = 1,
        asset_tag    = "AAI-2026-00001",
        asset_name   = "Dell Latitude 5540",
        requested_by = "Roberto Garcia",
        reason       = "Hardware failure — beyond economical repair.",
    )
    print("\n  Advancing through evidence gates...")
    advance_disposal(d1, "asset_returned",   True,           "Jose Reyes")
    advance_disposal(d1, "data_wiped",       True,           "Jose Reyes")
    advance_disposal(d1, "disposal_cert",    "CERT-2026-001","Jose Reyes")
    advance_disposal(d1, "finance_approved", True,           "Juan Dela Cruz")

    # 6. Summary
    print("\n\n" + "═" * 60)
    print("  INTEGRATION LAYER SUMMARY")
    print("═" * 60)
    print(f"  📦  Redis cache keys   : {len(list(cache.scan_iter('cache:*')))}")
    print(f"  📝  Audit events       : {audit_col.count_documents({})}")
    print(f"  🔔  Notifications sent : {notifications_col.count_documents({})}")
    print(f"  📄  Licenses tracked   : {licenses_col.count_documents({})}")
    print(f"  🗑️   Disposal records   : {disposals_col.count_documents({})}")
    print("═" * 60 + "\n")
    print("✅  All 5 integration components running!")
    print("    Next: run fastapi_service.py for the REST API layer\n")


if __name__ == "__main__":
    run_full_demo()
