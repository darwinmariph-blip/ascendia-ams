"""
=============================================================
  Ascendia IT Asset Management — MongoDB Integration
  Stores: Maintenance Documents & Assignment History
=============================================================
  HOW TO USE:
  1. Make sure MongoDB is running: brew services start mongodb-community
  2. Run:  python3 mongodb_integration.py
=============================================================
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from snipeit_client import SnipeITClient

load_dotenv()

snipe = SnipeITClient(
    base_url = os.getenv("SNIPEIT_URL", "http://snipe-it.test"),
    token    = os.getenv("SNIPEIT_TOKEN", ""),
)

mongo = MongoClient("mongodb://localhost:27017/")
db    = mongo["ascendia_ams"]

maintenance_col = db["maintenance_tickets"]
assignments_col = db["assignment_history"]
disposals_col   = db["disposal_records"]

print("\n" + "═" * 60)
print("  MONGODB INTEGRATION — Ascendia Academic Institution")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 60)
print(f"\n✅  Connected to MongoDB — database: ascendia_ams")
print(f"    Collections: maintenance_tickets, assignment_history, disposal_records\n")


def log_maintenance_ticket(asset_id, asset_tag, asset_name,
                            issue_notes, ai_priority, reported_by, technician=None):
    ticket = {
        "ticket_id":   f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":    asset_id,
        "asset_tag":   asset_tag,
        "asset_name":  asset_name,
        "issue_notes": issue_notes,
        "ai_priority": ai_priority,
        "reported_by": reported_by,
        "technician":  technician,
        "status":      "Open",
        "created_at":  datetime.now(),
        "updated_at":  datetime.now(),
        "resolved_at": None,
        "resolution":  None,
        "attachments": [],
    }
    maintenance_col.insert_one(ticket)
    print(f"  🔧  Ticket logged — {ticket['ticket_id']} [{asset_tag}] AI: {ai_priority}")
    return ticket["ticket_id"]


def resolve_maintenance_ticket(ticket_id, resolution, technician):
    maintenance_col.update_one(
        {"ticket_id": ticket_id},
        {"$set": {
            "status":      "Resolved",
            "resolution":  resolution,
            "technician":  technician,
            "resolved_at": datetime.now(),
            "updated_at":  datetime.now(),
        }}
    )
    print(f"  ✅  Ticket {ticket_id} resolved.")


def get_open_tickets():
    priority_order = {"High": 0, "Medium": 1, "Low": 2, "Unscored": 3}
    tickets = list(maintenance_col.find({"status": "Open"}))
    tickets.sort(key=lambda t: priority_order.get(t.get("ai_priority", "Unscored"), 3))
    return tickets


def log_assignment(asset_id, asset_tag, asset_name,
                   user_id, user_name, department, assigned_by, notes=""):
    record = {
        "event_id":    f"ASN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":    asset_id,
        "asset_tag":   asset_tag,
        "asset_name":  asset_name,
        "user_id":     user_id,
        "user_name":   user_name,
        "department":  department,
        "assigned_by": assigned_by,
        "assigned_at": datetime.now(),
        "returned_at": None,
        "status":      "Active",
        "notes":       notes,
    }
    assignments_col.insert_one(record)
    print(f"  📋  Assignment logged — {asset_tag} → {user_name} ({department})")
    return record["event_id"]


def log_return(asset_tag, user_name, notes=""):
    assignments_col.update_one(
        {"asset_tag": asset_tag, "user_name": user_name, "status": "Active"},
        {"$set": {
            "status":      "Returned",
            "returned_at": datetime.now(),
            "notes":       notes,
        }}
    )
    print(f"  🔄  Return logged — {asset_tag} from {user_name}")


def log_disposal(asset_id, asset_tag, asset_name,
                 disposal_method, disposed_by, cert_number=None, notes=""):
    record = {
        "disposal_id":     f"DSP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":        asset_id,
        "asset_tag":       asset_tag,
        "asset_name":      asset_name,
        "disposal_method": disposal_method,
        "disposed_by":     disposed_by,
        "cert_number":     cert_number,
        "notes":           notes,
        "disposed_at":     datetime.now(),
    }
    disposals_col.insert_one(record)
    print(f"  🗑️   Disposal logged — {asset_tag} via {disposal_method}")
    return record["disposal_id"]


def sync_maintenance_logs_from_snipeit():
    print("\n📥  Syncing maintenance logs from Snipe-IT → MongoDB...")
    data = snipe.list_maintenance_logs()
    logs = data.get("rows", [])
    synced = 0
    for log in logs:
        if maintenance_col.find_one({"snipeit_log_id": log["id"]}):
            continue
        doc = {
            "snipeit_log_id":   log["id"],
            "asset_id":         log.get("asset", {}).get("id"),
            "asset_tag":        log.get("asset", {}).get("asset_tag", "—"),
            "asset_name":       log.get("asset", {}).get("name", "—"),
            "title":            log.get("title", ""),
            "issue_notes":      log.get("notes", ""),
            "maintenance_type": log.get("maintenance_type", ""),
            "ai_priority":      "Unscored",
            "status":           "Synced",
            "start_date":       log.get("start_date", {}).get("date", ""),
            "created_at":       datetime.now(),
            "source":           "snipeit_sync",
        }
        maintenance_col.insert_one(doc)
        synced += 1
    print(f"    Synced {synced} new maintenance logs.")


def print_mongodb_summary():
    print("\n" + "═" * 60)
    print("  MONGODB SUMMARY")
    print("═" * 60)
    print(f"  🔧  Maintenance tickets : {maintenance_col.count_documents({})}")
    print(f"  📋  Assignment records  : {assignments_col.count_documents({})}")
    print(f"  🗑️   Disposal records    : {disposals_col.count_documents({})}")
    open_t = maintenance_col.count_documents({"status": "Open"})
    high_t = maintenance_col.count_documents({"ai_priority": "High", "status": "Open"})
    print(f"\n  Open tickets  : {open_t}")
    print(f"  High priority : {high_t}")
    if high_t > 0:
        print(f"\n  ⚠️  High priority tickets:")
        for t in maintenance_col.find({"ai_priority": "High", "status": "Open"}):
            print(f"    • [{t.get('asset_tag','—')}] {t.get('issue_notes','')[:60]}")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    print("🧪  Inserting sample records...\n")

    log_maintenance_ticket(
        asset_id=1, asset_tag="AAI-2026-00001", asset_name="Dell Latitude 5540",
        issue_notes="Unit fails to power on. No response upon pressing the power button. Possible hardware failure.",
        ai_priority="High", reported_by="Maria Santos", technician="Jose Reyes",
    )
    log_maintenance_ticket(
        asset_id=6, asset_tag="AAI-2026-00006", asset_name="MacBook Pro M3",
        issue_notes="Unit is running slow and battery drains quickly.",
        ai_priority="Medium", reported_by="Miguel Torres",
    )
    log_assignment(
        asset_id=2, asset_tag="AAI-2026-00002", asset_name="Dell Latitude 5540",
        user_id=1, user_name="Maria Santos", department="College of Computer Studies",
        assigned_by="Roberto Garcia", notes="Issued for AY 2026-2027.",
    )
    log_assignment(
        asset_id=6, asset_tag="AAI-2026-00006", asset_name="MacBook Pro M3",
        user_id=8, user_name="Miguel Torres", department="College of Computer Studies",
        assigned_by="Roberto Garcia", notes="Issued to department chair.",
    )

    sync_maintenance_logs_from_snipeit()
    print_mongodb_summary()

    print("📋  Open tickets by priority:")
    for t in get_open_tickets():
        print(f"  [{t.get('ai_priority','?')}] {t.get('asset_tag','—')} — {t.get('issue_notes','')[:60]}")
