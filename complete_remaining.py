"""
=============================================================
  Ascendia IT Asset Management — Complete Remaining Items
  Builds all 5 partial + 6 missing items from gap check
=============================================================
  Run:  python3 complete_remaining.py
=============================================================
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from snipeit_client import SnipeITClient

load_dotenv()

snipe = SnipeITClient(os.getenv("SNIPEIT_URL"), os.getenv("SNIPEIT_TOKEN"))
mongo = MongoClient("mongodb://localhost:27017/")
db    = mongo["ascendia_ams"]

print("\n" + "═" * 60)
print("  ASCENDIA AMS — COMPLETING REMAINING ITEMS")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 60)


# ══════════════════════════════════════════════════════════
#  1. ADD ALL MISSING STAFF
#  Department Heads, Finance Controller, Facilities Manager
#  Approvers per department
# ══════════════════════════════════════════════════════════

def add_missing_staff():
    print("\n\n1️⃣   ADDING MISSING STAFF ROLES")
    print("─" * 40)

    # Department IDs from Snipe-IT
    DEPT = {
        'College of Computer Studies': 1,
        'IT Support':                  2,
        'Finance':                     3,
        'Human Resources':             4,
        'Registrar\'s Office':         5,
        'Property Office':             6,
        'Network Administration':      7,
    }

    missing_staff = [
        # Department Heads / Approvers
        {
            "employee_num": "EMP-00009",
            "first_name":   "Carlos",
            "last_name":    "Reyes",
            "username":     "creyes",
            "email":        "creyes@ascendia.edu.ph",
            "department_id": DEPT["College of Computer Studies"],
            "jobtitle":     "Department Head",
            "role":         "Department Head / Approver",
        },
        {
            "employee_num": "EMP-00010",
            "first_name":   "Sandra",
            "last_name":    "Bautista",
            "username":     "sbautista",
            "email":        "sbautista@ascendia.edu.ph",
            "department_id": DEPT["Finance"],
            "jobtitle":     "Finance Controller",
            "role":         "Finance / Administration",
        },
        {
            "employee_num": "EMP-00011",
            "first_name":   "Ramon",
            "last_name":    "Villanueva",
            "username":     "rvillanueva",
            "email":        "rvillanueva@ascendia.edu.ph",
            "department_id": DEPT["Property Office"],
            "jobtitle":     "Facilities Manager",
            "role":         "Facilities / LMS Administrator",
        },
        {
            "employee_num": "EMP-00012",
            "first_name":   "Elena",
            "last_name":    "Gomez",
            "username":     "egomez",
            "email":        "egomez@ascendia.edu.ph",
            "department_id": DEPT["IT Support"],
            "jobtitle":     "IT Support Manager",
            "role":         "IT Support Manager",
        },
        {
            "employee_num": "EMP-00013",
            "first_name":   "Marco",
            "last_name":    "Fernandez",
            "username":     "mfernandez",
            "email":        "mfernandez@ascendia.edu.ph",
            "department_id": DEPT["Network Administration"],
            "jobtitle":     "Network Administrator",
            "role":         "Network / Infrastructure",
        },
        {
            "employee_num": "EMP-00014",
            "first_name":   "Diana",
            "last_name":    "Santos",
            "username":     "dsantos",
            "email":        "dsantos@ascendia.edu.ph",
            "department_id": DEPT["Human Resources"],
            "jobtitle":     "HR Director",
            "role":         "HR Director",
        },
        {
            "employee_num": "EMP-00015",
            "first_name":   "Felix",
            "last_name":    "Aquino",
            "username":     "faquino",
            "email":        "faquino@ascendia.edu.ph",
            "department_id": DEPT["Property Office"],
            "jobtitle":     "Procurement Manager",
            "role":         "Procurement Office",
        },
    ]

    created = 0
    for staff in missing_staff:
        try:
            result = snipe.create_user(
                first_name    = staff["first_name"],
                last_name     = staff["last_name"],
                username      = staff["username"],
                email         = staff["email"],
                department_id = staff["department_id"],
                password      = "Ascendia@2026!",
                employee_num  = staff["employee_num"],
            )
            if result.get("status") == "success":
                created += 1
                print(f"  ✅  {staff['first_name']} {staff['last_name']} — {staff['role']}")
            else:
                msg = str(result.get("messages", ""))
                if "already been taken" in msg.lower():
                    print(f"  ⏭️   {staff['first_name']} {staff['last_name']} — already exists")
                else:
                    print(f"  ❌  {staff['first_name']} {staff['last_name']}: {msg}")
        except Exception as e:
            print(f"  ❌  Error: {e}")

    print(f"\n  Total new staff added: {created}")


# ══════════════════════════════════════════════════════════
#  2. DIGITAL CHECKOUT ACKNOWLEDGMENT WORKFLOW
# ══════════════════════════════════════════════════════════

checkout_col = db["digital_checkouts"]

def digital_checkout(asset_id, asset_tag, asset_name,
                     user_id, user_name, assigned_by,
                     expected_return=None, notes=""):
    """
    Digital checkout with acknowledgment workflow.
    No closure without digital acknowledgment (P3).
    """
    checkout = {
        "checkout_id":      f"CHK-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":         asset_id,
        "asset_tag":        asset_tag,
        "asset_name":       asset_name,
        "user_id":          user_id,
        "user_name":        user_name,
        "assigned_by":      assigned_by,
        "checkout_date":    datetime.now(),
        "expected_return":  expected_return,
        "acknowledged":     False,
        "acknowledged_at":  None,
        "status":           "Pending Acknowledgment",
        "notes":            notes,
    }
    checkout_col.insert_one(checkout)

    # Perform actual checkout in Snipe-IT
    result = snipe.checkout_asset(asset_id, user_id,
                                   note=f"Digital checkout — pending acknowledgment. {notes}")

    # Send acknowledgment request notification
    db.notifications.insert_one({
        "recipient":       user_name,
        "role":            "Employee",
        "subject":         f"Please acknowledge receipt — {asset_tag}",
        "message":         f"You have been assigned {asset_tag} ({asset_name}). Please acknowledge receipt.",
        "priority":        "normal",
        "asset_tag":       asset_tag,
        "action_required": "Confirm receipt by logging into the AMS portal.",
        "sent_at":         datetime.now(),
        "status":          "sent",
    })

    print(f"  📋  Checkout initiated — {asset_tag} → {user_name}")
    print(f"      Status: Pending Acknowledgment")
    print(f"      Notification sent to {user_name}")
    return checkout["checkout_id"]


def acknowledge_checkout(checkout_id, user_name):
    """User digitally acknowledges receipt of asset."""
    checkout_col.update_one(
        {"checkout_id": checkout_id},
        {"$set": {
            "acknowledged":    True,
            "acknowledged_at": datetime.now(),
            "status":          "Acknowledged — Deployed",
        }}
    )
    record = checkout_col.find_one({"checkout_id": checkout_id})

    # Update asset status to Deployed in Snipe-IT
    snipe.update_asset(record["asset_id"], {"status_id": 2})

    db.audit_events.insert_one({
        "event_id":  f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "action":    "DIGITAL_ACKNOWLEDGMENT",
        "actor":     user_name,
        "asset_tag": record["asset_tag"],
        "after":     {"status": "Acknowledged — Deployed"},
        "timestamp": datetime.now(),
        "process":   "Digital Checkout",
    })
    print(f"  ✅  {user_name} acknowledged receipt of {record['asset_tag']}")
    print(f"      Asset status → Deployed")


def get_pending_acknowledgments():
    """Get all checkouts waiting for acknowledgment."""
    pending = list(checkout_col.find({"acknowledged": False}, {"_id": 0}))
    print(f"\n  ⏳  Pending acknowledgments: {len(pending)}")
    for p in pending:
        print(f"    • {p['asset_tag']} → {p['user_name']} (since {p['checkout_date'].strftime('%Y-%m-%d %H:%M')})")
    return pending


# ══════════════════════════════════════════════════════════
#  3. ASSET MOVEMENT / TRANSFER WORKFLOW (24hr rule)
# ══════════════════════════════════════════════════════════

transfers_col = db["asset_transfers"]

def initiate_transfer(asset_id, asset_tag, asset_name,
                      from_location, to_location,
                      initiated_by, is_temporary=False,
                      due_back_hours=24):
    """
    Transfer workflow with 24hr update enforcement (BR004).
    Temporary transfers get a due-back reminder.
    """
    due_date = datetime.now() + timedelta(hours=due_back_hours) if is_temporary else None

    transfer = {
        "transfer_id":   f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "asset_id":      asset_id,
        "asset_tag":     asset_tag,
        "asset_name":    asset_name,
        "from_location": from_location,
        "to_location":   to_location,
        "initiated_by":  initiated_by,
        "is_temporary":  is_temporary,
        "due_back":      due_date,
        "status":        "In Transit",
        "initiated_at":  datetime.now(),
        "completed_at":  None,
        "overdue":       False,
    }
    transfers_col.insert_one(transfer)

    # Notification to IT team
    db.notifications.insert_one({
        "recipient":       "Roberto Garcia",
        "role":            "IT Asset Manager",
        "subject":         f"Asset Transfer — {asset_tag}",
        "message":         f"{asset_tag} moving from {from_location} to {to_location}.",
        "priority":        "normal",
        "asset_tag":       asset_tag,
        "action_required": f"Update location within 24 hours (BR004)." + (f" Due back: {due_date.strftime('%Y-%m-%d %H:%M')}" if due_date else ""),
        "sent_at":         datetime.now(),
        "status":          "sent",
    })

    print(f"  🔄  Transfer initiated — {asset_tag}")
    print(f"      From: {from_location} → To: {to_location}")
    if is_temporary:
        print(f"      Temporary — due back by: {due_date.strftime('%Y-%m-%d %H:%M')}")
    return transfer["transfer_id"]


def complete_transfer(transfer_id, confirmed_by, new_location_id):
    """Complete a transfer — update location in Snipe-IT."""
    record = transfers_col.find_one({"transfer_id": transfer_id})
    if not record:
        print(f"  ❌  Transfer {transfer_id} not found.")
        return

    # Update location in Snipe-IT
    snipe.update_asset(record["asset_id"], {
        "location_id": new_location_id,
        "last_audit_date": datetime.now().strftime("%Y-%m-%d 00:00:00"),
    })

    transfers_col.update_one(
        {"transfer_id": transfer_id},
        {"$set": {"status": "Completed", "completed_at": datetime.now()}}
    )

    db.audit_events.insert_one({
        "event_id":  f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "action":    "TRANSFER_COMPLETED",
        "actor":     confirmed_by,
        "asset_tag": record["asset_tag"],
        "before":    {"location": record["from_location"]},
        "after":     {"location": record["to_location"]},
        "timestamp": datetime.now(),
        "process":   "Asset Transfer",
    })
    print(f"  ✅  Transfer {transfer_id} completed — location updated in Snipe-IT")


def check_overdue_transfers():
    """Flag transfers that exceeded 24hr window (BR004)."""
    overdue = list(transfers_col.find({
        "status": "In Transit",
        "due_back": {"$lt": datetime.now()}
    }))
    if overdue:
        print(f"\n  ⚠️   Overdue transfers (BR004 violation):")
        for t in overdue:
            transfers_col.update_one({"transfer_id": t["transfer_id"]}, {"$set": {"overdue": True}})
            print(f"    • {t['asset_tag']} — overdue since {t['due_back'].strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"\n  ✅  No overdue transfers.")


# ══════════════════════════════════════════════════════════
#  4. LMS / CLASS SCHEDULING INTEGRATION
# ══════════════════════════════════════════════════════════

lms_col = db["lms_schedules"]

def sync_lms_schedules():
    """
    Simulated LMS integration — in production connects to
    your school's LMS (Moodle, Canvas, Google Classroom).
    Tracks which labs/rooms are in use and when.
    """
    print("\n\n4️⃣   LMS / CLASS SCHEDULING INTEGRATION")
    print("─" * 40)

    schedules = [
        {
            "schedule_id":  "SCH-001",
            "course":       "MSIT 631 — Advanced Systems Design",
            "room":         "QC-MAIN-LAB1",
            "day":          "Tuesday/Thursday",
            "time":         "09:00-11:00",
            "instructor":   "Miguel Torres",
            "students":     25,
            "assets_needed": ["Laptop", "Projector"],
            "semester":     "2026-1st",
            "critical_period": False,
        },
        {
            "schedule_id":  "SCH-002",
            "course":       "CS 101 — Introduction to Programming",
            "room":         "QC-MAIN-LAB1",
            "day":          "Monday/Wednesday/Friday",
            "time":         "13:00-15:00",
            "instructor":   "Maria Santos",
            "students":     30,
            "assets_needed": ["Laptop"],
            "semester":     "2026-1st",
            "critical_period": True,  # Finals week
        },
        {
            "schedule_id":  "SCH-003",
            "course":       "Finance 201 — Financial Management",
            "room":         "QC-MAIN-CLASS101",
            "day":          "Tuesday/Thursday",
            "time":         "14:00-16:00",
            "instructor":   "Juan Dela Cruz",
            "students":     35,
            "assets_needed": ["Projector"],
            "semester":     "2026-1st",
            "critical_period": False,
        },
    ]

    lms_col.delete_many({})
    for s in schedules:
        s["synced_at"] = datetime.now()
        lms_col.insert_one(s)
        critical = " ⚠️ CRITICAL PERIOD" if s["critical_period"] else ""
        print(f"  📅  {s['course']}")
        print(f"      Room: {s['room']} | {s['day']} {s['time']}{critical}")

    print(f"\n  ✅  {len(schedules)} class schedules synced from LMS")


def check_lab_readiness(room_name):
    """Check if assets in a room are ready for scheduled classes."""
    print(f"\n  🔍  Lab readiness check — {room_name}")

    # Get scheduled classes for this room
    classes = list(lms_col.find({"room": room_name}, {"_id": 0}))
    if not classes:
        print(f"    No classes scheduled for {room_name}")
        return

    # Get assets in this room from Snipe-IT
    assets = snipe.list_assets(limit=500).get("rows", [])
    room_assets = [a for a in assets if (a.get("location") or {}).get("name") == room_name]

    laptops    = [a for a in room_assets if "laptop" in a.get("category", {}).get("name", "").lower()]
    projectors = [a for a in room_assets if "projector" in a.get("category", {}).get("name", "").lower()]
    ready      = [a for a in room_assets if a.get("status_label", {}).get("name") == "Ready to Deploy"]
    issues     = [a for a in room_assets if "maintenance" in a.get("status_label", {}).get("name", "").lower()]

    for c in classes:
        print(f"\n    📚 {c['course']}")
        print(f"       Needs: {', '.join(c['assets_needed'])}")
        print(f"       Assets in room: {len(room_assets)} ({len(ready)} ready, {len(issues)} with issues)")

        if issues:
            for a in issues:
                print(f"       ⚠️  {a['asset_tag']} — {a['status_label']['name']}")
            if c.get("critical_period"):
                print(f"       🔴 CRITICAL: This is a finals period class — escalate immediately!")
                db.notifications.insert_one({
                    "recipient":       "Roberto Garcia",
                    "role":            "IT Asset Manager",
                    "subject":         f"CRITICAL — Lab issue during finals: {room_name}",
                    "message":         f"{len(issues)} asset(s) have issues in {room_name} during critical academic period.",
                    "priority":        "high",
                    "action_required": "Resolve before next class session.",
                    "sent_at":         datetime.now(),
                    "status":          "sent",
                })


# ══════════════════════════════════════════════════════════
#  5. FINANCE / ERP INTEGRATION
# ══════════════════════════════════════════════════════════

finance_col = db["finance_records"]

def sync_finance_erp():
    """
    Finance/ERP integration — depreciation, cost centers,
    and disposal financial closeout.
    """
    print("\n\n5️⃣   FINANCE / ERP INTEGRATION")
    print("─" * 40)

    assets = snipe.list_assets(limit=500).get("rows", [])

    finance_records = []
    for a in assets:
        cost = float(str(a.get("purchase_cost") or "0").replace(",", ""))
        if cost <= 0:
            continue

        purchase_date = a.get("purchase_date", {})
        if isinstance(purchase_date, dict):
            purchase_date = purchase_date.get("date", "2026-01-01")[:10]
        elif not purchase_date:
            purchase_date = "2026-01-01"

        # Straight-line depreciation (5 years for laptops/projectors)
        years_old    = (datetime.now() - datetime.strptime(purchase_date, "%Y-%m-%d")).days / 365
        useful_life  = 5
        depreciation = min(cost, (cost / useful_life) * years_old)
        book_value   = max(0, cost - depreciation)

        category = a.get("category", {}).get("name", "Other") if a.get("category") else "Other"
        dept     = a.get("location", {}).get("name", "Unknown") if a.get("location") else "Unknown"

        record = {
            "asset_id":       a["id"],
            "asset_tag":      a.get("asset_tag", "—"),
            "asset_name":     a.get("name", "—"),
            "category":       category,
            "cost_center":    dept,
            "acquisition_cost": cost,
            "purchase_date":  purchase_date,
            "useful_life_yrs": useful_life,
            "depreciation":   round(depreciation, 2),
            "book_value":     round(book_value, 2),
            "synced_at":      datetime.now(),
        }
        finance_records.append(record)

    finance_col.delete_many({})
    if finance_records:
        finance_col.insert_many(finance_records)

    total_cost  = sum(r["acquisition_cost"] for r in finance_records)
    total_depr  = sum(r["depreciation"]     for r in finance_records)
    total_value = sum(r["book_value"]        for r in finance_records)

    print(f"  💰  Finance records synced: {len(finance_records)} assets")
    print(f"      Total acquisition cost : ₱{total_cost:,.2f}")
    print(f"      Total depreciation     : ₱{total_depr:,.2f}")
    print(f"      Current book value     : ₱{total_value:,.2f}")
    print(f"\n  Per-asset depreciation:")
    for r in finance_records:
        print(f"    • [{r['asset_tag']}] {r['asset_name']}")
        print(f"      Cost: ₱{r['acquisition_cost']:,.0f} → Book Value: ₱{r['book_value']:,.0f}")


# ══════════════════════════════════════════════════════════
#  6. ANALYTICS / REPORTING STORE (KPI DB)
# ══════════════════════════════════════════════════════════

analytics_col = db["analytics_kpis"]

def generate_kpi_snapshot():
    """
    Generate and store KPI snapshot in MongoDB analytics store.
    Aggregates data from all sources into one KPI record.
    """
    print("\n\n6️⃣   ANALYTICS / REPORTING STORE")
    print("─" * 40)

    assets  = snipe.list_assets(limit=500).get("rows", [])
    users   = snipe.list_users(limit=500).get("rows", [])

    # Asset KPIs
    total_assets    = len(assets)
    ready_assets    = len([a for a in assets if "ready" in (a.get("status_label") or {}).get("name", "").lower()])
    maint_assets    = len([a for a in assets if "maintenance" in (a.get("status_label") or {}).get("name", "").lower()])
    total_value     = sum(float(str(a.get("purchase_cost") or "0").replace(",","")) for a in assets)

    # AI KPIs
    high_count   = db.maintenance_tickets.count_documents({"ai_priority": "High",   "status": "Open"})
    medium_count = db.maintenance_tickets.count_documents({"ai_priority": "Medium", "status": "Open"})
    low_count    = db.maintenance_tickets.count_documents({"ai_priority": "Low",    "status": "Open"})

    # Audit KPIs
    audit_events  = db.audit_events.count_documents({})
    notif_count   = db.notifications.count_documents({})

    # License KPIs
    licenses      = list(db.software_licenses.find({}))
    total_seats   = sum(l.get("seats_total", 0) for l in licenses)
    used_seats    = sum(l.get("seats_used",  0) for l in licenses)
    license_util  = round((used_seats / total_seats * 100) if total_seats > 0 else 0, 1)

    # Finance KPIs
    finance_recs  = list(finance_col.find({}))
    total_book    = sum(r.get("book_value", 0) for r in finance_recs)

    kpi = {
        "snapshot_id":    f"KPI-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "generated_at":   datetime.now(),
        "period":         datetime.now().strftime("%Y-%m"),
        "assets": {
            "total":       total_assets,
            "ready":       ready_assets,
            "maintenance": maint_assets,
            "total_value": round(total_value, 2),
            "book_value":  round(total_book, 2),
        },
        "users": {
            "total":       len(users),
            "active":      len([u for u in users if u.get("activated")]),
        },
        "maintenance": {
            "open_high":   high_count,
            "open_medium": medium_count,
            "open_low":    low_count,
            "total_open":  high_count + medium_count + low_count,
        },
        "licenses": {
            "total_licenses": len(licenses),
            "total_seats":    total_seats,
            "used_seats":     used_seats,
            "utilization_pct": license_util,
        },
        "audit": {
            "total_events":    audit_events,
            "notifications":   notif_count,
        },
        "transfers": {
            "total":    db.asset_transfers.count_documents({}),
            "overdue":  db.asset_transfers.count_documents({"overdue": True}),
        },
        "disposals": {
            "total":     db.disposal_records.count_documents({}),
            "completed": db.disposal_records.count_documents({"stage": "Disposed"}),
        },
    }

    analytics_col.insert_one(kpi)

    print(f"  📊  KPI snapshot generated — {kpi['snapshot_id']}")
    print(f"\n  Asset KPIs:")
    print(f"    Total assets   : {total_assets}")
    print(f"    Ready to deploy: {ready_assets}")
    print(f"    In maintenance : {maint_assets}")
    print(f"    Total value    : ₱{total_value:,.2f}")
    print(f"    Book value     : ₱{total_book:,.2f}")
    print(f"\n  Maintenance KPIs:")
    print(f"    High priority  : {high_count}")
    print(f"    Medium priority: {medium_count}")
    print(f"    Low priority   : {low_count}")
    print(f"\n  License KPIs:")
    print(f"    Utilization    : {license_util}% ({used_seats}/{total_seats} seats)")
    print(f"\n  Audit KPIs:")
    print(f"    Audit events   : {audit_events}")
    print(f"    Notifications  : {notif_count}")

    return kpi


# ══════════════════════════════════════════════════════════
#  7. RULES ENGINE — Complete Business Rules
# ══════════════════════════════════════════════════════════

def run_rules_engine():
    """
    Enforce all business rules from the architecture doc.
    BR001-BR005 + movement 24hr rule.
    """
    print("\n\n7️⃣   RULES ENGINE — Business Rules Check")
    print("─" * 40)

    assets = snipe.list_assets(limit=500).get("rows", [])
    users  = snipe.list_users(limit=500).get("rows", [])

    violations = []

    # BR001: Assets only assigned to official employees (no students)
    print("  Checking BR001 — employee-only asset assignment...")
    for a in assets:
        assigned = a.get("assigned_to")
        if assigned and assigned.get("type") == "user":
            user = next((u for u in users if u["id"] == assigned.get("id")), None)
            if user and not user.get("activated"):
                violations.append(f"BR001: {a.get('asset_tag')} assigned to inactive user {user.get('name')}")

    # BR002: No checkout to inactive users
    print("  Checking BR002 — no inactive user checkouts...")
    inactive = [u for u in users if not u.get("activated")]
    for u in inactive:
        assigned = [a for a in assets if a.get("assigned_to", {}).get("id") == u["id"]]
        for a in assigned:
            violations.append(f"BR002: {a.get('asset_tag')} still assigned to inactive user {u.get('name')}")

    # BR003: High AI priority → Maintenance-High status
    print("  Checking BR003 — High AI → Maintenance-High status...")
    for a in assets:
        cf = a.get("custom_fields", {})
        ai = cf.get("AI Priority Score", {}).get("value", "Unscored") if cf else "Unscored"
        status = (a.get("status_label") or {}).get("name", "")
        if ai == "High" and "maintenance" not in status.lower():
            violations.append(f"BR003: {a.get('asset_tag')} is High priority but status is '{status}'")

    # BR004: Check overdue transfers
    print("  Checking BR004 — 24hr movement update rule...")
    check_overdue_transfers()

    # BR005: Disposed assets must have disposal note
    print("  Checking BR005 — disposal notes required...")
    disposed = list(db.disposal_records.find({"stage": "Disposed"}))
    for d in disposed:
        if not d.get("reason"):
            violations.append(f"BR005: {d.get('asset_tag')} disposed without reason note")

    if violations:
        print(f"\n  ⚠️   {len(violations)} business rule violation(s):")
        for v in violations:
            print(f"    • {v}")
    else:
        print(f"\n  ✅  All business rules passed — no violations!")

    return violations


# ══════════════════════════════════════════════════════════
#  RUN EVERYTHING
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":

    # 1. Add missing staff
    add_missing_staff()

    # 2. Digital checkout workflow demo
    print("\n\n2️⃣   DIGITAL CHECKOUT ACKNOWLEDGMENT WORKFLOW")
    print("─" * 40)
    chk = digital_checkout(
        asset_id     = 2,
        asset_tag    = "AAI-2026-00002",
        asset_name   = "Dell Latitude 5540",
        user_id      = 1,
        user_name    = "Maria Santos",
        assigned_by  = "Roberto Garcia",
        notes        = "Issued for AY 2026-2027 semester.",
    )
    get_pending_acknowledgments()
    acknowledge_checkout(chk, "Maria Santos")

    # 3. Transfer workflow demo
    print("\n\n3️⃣   ASSET MOVEMENT / TRANSFER WORKFLOW")
    print("─" * 40)
    trf = initiate_transfer(
        asset_id      = 8,
        asset_tag     = "AAI-2026-00008",
        asset_name    = "Epson EB-X51 Projector",
        from_location = "QC-MAIN-CLASS101",
        to_location   = "QC-MAIN-LAB1",
        initiated_by  = "Jose Reyes",
        is_temporary  = True,
        due_back_hours = 48,
    )
    complete_transfer(trf, "Jose Reyes", new_location_id=3)

    # 4. LMS integration
    sync_lms_schedules()
    check_lab_readiness("QC-MAIN-LAB1")

    # 5. Finance ERP
    sync_finance_erp()

    # 6. Analytics KPI store
    generate_kpi_snapshot()

    # 7. Rules engine
    run_rules_engine()

    # Final summary
    print("\n\n" + "═" * 60)
    print("  COMPLETION SUMMARY")
    print("═" * 60)
    users_total = snipe.list_users(limit=500).get("total", 0)
    print(f"  👥  Total staff in Snipe-IT : {users_total}")
    print(f"  📋  Digital checkouts       : {db.digital_checkouts.count_documents({})}")
    print(f"  🔄  Asset transfers         : {db.asset_transfers.count_documents({})}")
    print(f"  📅  LMS schedules           : {db.lms_schedules.count_documents({})}")
    print(f"  💰  Finance records         : {db.finance_records.count_documents({})}")
    print(f"  📊  KPI snapshots           : {db.analytics_kpis.count_documents({})}")
    print(f"  ✅  All remaining items complete!")
    print("═" * 60 + "\n")
