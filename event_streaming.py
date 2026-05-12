"""
=============================================================
  Ascendia IT Asset Management — Event Streaming
  Redis Streams as event bus (Kafka substitute)
=============================================================
  Run:  python3 event_streaming.py
=============================================================
"""

import os
import json
import redis
import time
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

r     = redis.Redis(host="localhost", port=6379, decode_responses=True)
mongo = MongoClient("mongodb://localhost:27017/")
db    = mongo["ascendia_ams"]

STREAM = "ascendia:events"

print("\n" + "═" * 60)
print("  ASCENDIA AMS — REDIS EVENT STREAMING")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 60)


def publish_event(event_type, payload):
    msg_id = r.xadd(STREAM, {
        "event_type": event_type,
        "payload":    json.dumps(payload),
        "timestamp":  datetime.now().isoformat(),
    })
    print(f"  📤  Published [{event_type}] → {msg_id}")
    return msg_id


def on_asset_moved(asset_tag, from_loc, to_loc, scanned_by):
    publish_event("ASSET_MOVED", {"asset_tag": asset_tag, "from": from_loc, "to": to_loc, "scanned_by": scanned_by})


def on_maintenance_filed(asset_tag, issue_notes, reported_by):
    publish_event("MAINTENANCE_FILED", {"asset_tag": asset_tag, "issue_notes": issue_notes, "reported_by": reported_by})


def on_user_synced(employee_num, user_name, action):
    publish_event("USER_SYNCED", {"employee_num": employee_num, "user_name": user_name, "action": action})


def on_qr_audit_scan(asset_tag, location, scanned_by):
    publish_event("QR_AUDIT_SCAN", {"asset_tag": asset_tag, "location": location, "scanned_by": scanned_by, "scan_time": datetime.now().isoformat()})


def on_procurement_received(po_number, asset_tags, vendor):
    publish_event("PROCUREMENT_RECEIVED", {"po_number": po_number, "asset_tags": asset_tags, "vendor": vendor})


def process_event(event_type, payload):
    if event_type == "ASSET_MOVED":
        db.audit_events.insert_one({
            "event_id": f"AUD-EVT-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
            "action": "ASSET_MOVED_VIA_QR", "actor": payload.get("scanned_by"),
            "asset_tag": payload.get("asset_tag"),
            "before": {"location": payload.get("from")}, "after": {"location": payload.get("to")},
            "timestamp": datetime.now(), "process": "QR Movement Trigger",
        })
        print(f"    → Audit logged for movement")

    elif event_type == "MAINTENANCE_FILED":
        from ai_priority_scorer import score_note
        score = score_note(payload.get("issue_notes", ""))
        db.maintenance_tickets.insert_one({
            "ticket_id": f"TKT-EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "asset_tag": payload.get("asset_tag"), "issue_notes": payload.get("issue_notes"),
            "ai_priority": score, "reported_by": payload.get("reported_by"),
            "status": "Open", "created_at": datetime.now(), "source": "event_stream",
        })
        print(f"    → Maintenance ticket created — AI: {score}")

    elif event_type in ("USER_SYNCED", "QR_AUDIT_SCAN", "PROCUREMENT_RECEIVED"):
        db.audit_events.insert_one({
            "event_id": f"AUD-EVT-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:18]}",
            "action": event_type, "actor": "Event Stream",
            "notes": json.dumps(payload), "timestamp": datetime.now(), "process": "Event Trigger",
        })
        print(f"    → {event_type} audit logged")


def consume_events(count=20):
    print(f"\n📥  Consuming events from stream...")
    messages = r.xrange(STREAM, count=count)
    processed = 0
    for msg_id, fields in messages:
        event_type = fields.get("event_type")
        payload    = json.loads(fields.get("payload", "{}"))
        print(f"\n  📨  [{event_type}] @ {fields.get('timestamp','')[:19]}")
        process_event(event_type, payload)
        processed += 1
    print(f"\n  ✅  Processed {processed} events")
    return processed


if __name__ == "__main__":
    print("\n📤  PUBLISHING EVENTS")
    print("─" * 40)
    on_asset_moved("AAI-2026-00008", "QC-MAIN-CLASS101", "QC-MAIN-LAB1", "Jose Reyes")
    on_maintenance_filed("AAI-2026-00003", "Laptop is running slow and freezing often", "Liza Mendoza")
    on_user_synced("EMP-00016", "New Faculty Member", "created")
    on_qr_audit_scan("AAI-2026-00006", "QC-MAIN-LAB1", "Jose Reyes")
    on_procurement_received("PO-00004", ["AAI-2026-00010", "AAI-2026-00011"], "Dell Philippines")

    time.sleep(0.5)

    print("\n📥  CONSUMING & PROCESSING EVENTS")
    print("─" * 40)
    consume_events()

    print(f"\n  📊  Stream length: {r.xlen(STREAM)} total events")
    print("\n✅  Redis Streams event bus complete!")
    print("    Replaces Kafka at Ascendia's institutional scale.\n")
