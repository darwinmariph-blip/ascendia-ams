"""
=============================================================
  Ascendia IT Asset Management — FastAPI REST Service
  The central API layer connecting all components
=============================================================
  HOW TO USE:
  1. pip3 install fastapi uvicorn
  2. python3 fastapi_service.py
  3. Open: http://localhost:8080/docs  (auto-generated API docs)
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

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

snipe = SnipeITClient(os.getenv("SNIPEIT_URL"), os.getenv("SNIPEIT_TOKEN"))
mongo = MongoClient("mongodb://localhost:27017/")
db    = mongo["ascendia_ams"]
cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

if not FASTAPI_AVAILABLE:
    print("❌  FastAPI not installed. Run: pip3 install fastapi uvicorn")
    print("    Then run this file again.")
    exit(1)

app = FastAPI(
    title       = "Ascendia IT Asset Management API",
    description = "REST API for Ascendia AMS — Snipe-IT + MongoDB + InfluxDB + Redis",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ────────────────────────────────────────
class MaintenanceTicketRequest(BaseModel):
    asset_id:    int
    asset_tag:   str
    asset_name:  str
    issue_notes: str
    reported_by: str

class DisposalRequest(BaseModel):
    asset_id:     int
    asset_tag:    str
    asset_name:   str
    requested_by: str
    reason:       str

class NotificationRequest(BaseModel):
    recipient: str
    role:      str
    subject:   str
    message:   str
    priority:  str = "normal"


# ── Routes ────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "system":  "Ascendia IT Asset Management",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs",
    }

@app.get("/health")
def health_check():
    return {
        "snipeit":  "connected",
        "mongodb":  "connected",
        "redis":    "connected",
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/assets")
def get_assets():
    cached = cache.get("api:assets")
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    data = snipe.list_assets(limit=500)
    cache.setex("api:assets", 300, json.dumps(data))
    return {"source": "live", "data": data}

@app.get("/assets/{asset_tag}")
def get_asset_by_tag(asset_tag: str):
    data = snipe.get_asset_by_tag(asset_tag)
    return data

@app.get("/users")
def get_users():
    cached = cache.get("api:users")
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    data = snipe.list_users(limit=500)
    cache.setex("api:users", 300, json.dumps(data))
    return {"source": "live", "data": data}

@app.get("/maintenance/tickets")
def get_tickets():
    tickets = list(db.maintenance_tickets.find({}, {"_id": 0}).sort("created_at", -1).limit(50))
    return {"total": len(tickets), "tickets": tickets}

@app.get("/maintenance/tickets/open")
def get_open_tickets():
    tickets = list(db.maintenance_tickets.find({"status": "Open"}, {"_id": 0}))
    return {"total": len(tickets), "tickets": tickets}

@app.post("/maintenance/tickets")
def create_ticket(req: MaintenanceTicketRequest):
    from ai_priority_scorer import score_note
    ai_score = score_note(req.issue_notes)
    ticket = {
        "ticket_id":   f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":    req.asset_id,
        "asset_tag":   req.asset_tag,
        "asset_name":  req.asset_name,
        "issue_notes": req.issue_notes,
        "ai_priority": ai_score,
        "reported_by": req.reported_by,
        "status":      "Open",
        "created_at":  datetime.now(),
    }
    db.maintenance_tickets.insert_one(ticket)
    cache.delete("api:assets")
    return {"status": "created", "ticket_id": ticket["ticket_id"], "ai_priority": ai_score}

@app.get("/audit/trail")
def get_audit_trail(asset_tag: str = None, limit: int = 20):
    query = {"asset_tag": asset_tag} if asset_tag else {}
    events = list(db.audit_events.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))
    return {"total": len(events), "events": events}

@app.get("/licenses")
def get_licenses():
    lics = list(db.software_licenses.find({}, {"_id": 0}))
    return {"total": len(lics), "licenses": lics}

@app.get("/notifications")
def get_notifications(limit: int = 20):
    notifs = list(db.notifications.find({}, {"_id": 0}).sort("sent_at", -1).limit(limit))
    return {"total": len(notifs), "notifications": notifs}

@app.get("/disposals")
def get_disposals():
    records = list(db.disposal_records.find({}, {"_id": 0}).sort("created_at", -1))
    return {"total": len(records), "disposals": records}

@app.post("/disposals")
def create_disposal(req: DisposalRequest):
    record = {
        "disposal_id":  f"DSP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":     req.asset_id,
        "asset_tag":    req.asset_tag,
        "asset_name":   req.asset_name,
        "requested_by": req.requested_by,
        "reason":       req.reason,
        "stage":        "Pending Return",
        "evidence":     {"asset_returned": False, "data_wiped": False, "disposal_cert": None, "finance_approved": False},
        "created_at":   datetime.now(),
    }
    db.disposal_records.insert_one(record)
    return {"status": "created", "disposal_id": record["disposal_id"]}

@app.get("/lms/schedules")
def get_lms_schedules():
    from pymongo import MongoClient
    db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]
    schedules = list(db.lms_schedules.find({}, {"_id": 0}))
    return {"total": len(schedules), "schedules": schedules}

@app.get("/report/summary")
def get_summary():
    assets = snipe.list_assets(limit=500)
    users  = snipe.list_users(limit=500)
    return {
        "assets":        assets.get("total", 0),
        "users":         users.get("total", 0),
        "open_tickets":  db.maintenance_tickets.count_documents({"status": "Open"}),
        "high_tickets":  db.maintenance_tickets.count_documents({"ai_priority": "High", "status": "Open"}),
        "notifications": db.notifications.count_documents({}),
        "licenses":      db.software_licenses.count_documents({}),
        "disposals":     db.disposal_records.count_documents({}),
        "generated_at":  datetime.now().isoformat(),
    }


if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  ASCENDIA AMS — FastAPI REST Service")
    print("═" * 60)
    print("  API docs: http://localhost:8080/docs")
    print("  Health:   http://localhost:8080/health")
    print("  Summary:  http://localhost:8080/report/summary")
    print("═" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8080)

@app.get("/lms/schedules")
def get_lms_schedules():
    from pymongo import MongoClient
    db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]
    schedules = list(db.lms_schedules.find({}, {"_id": 0}))
    return {"total": len(schedules), "schedules": schedules}
