"""
=============================================================
  Ascendia IT Asset Management — Phase 2a
  HRIS User Sync — Auto-create/update users from HR data
=============================================================
  HOW TO USE:
  1. Make sure snipeit_client.py is in the same folder
  2. Edit the SAMPLE HR DATA section below with real staff
  3. Run:  python3 hris_sync.py
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
#  WHAT THIS SCRIPT DOES
#  1. Reads a list of employees (from HR CSV or dict below)
#  2. For each employee:
#     - If they don't exist in Snipe-IT → CREATE them
#     - If they exist but are terminated → DEACTIVATE them
#     - If they exist and are active → SKIP (already synced)
#  3. Logs everything it does
# ══════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════
#  STEP 1 — EDIT THIS: Your HR employee data
#  In real life this comes from your HR system export (CSV).
#  For now, add your actual staff here to test.
#
#  status: "active"     = currently employed
#          "terminated" = resigned / offboarded
# ══════════════════════════════════════════════════════════

HR_EMPLOYEES = [
    {
        "employee_num":  "EMP-00001",
        "first_name":    "Maria",
        "last_name":     "Santos",
        "username":      "msantos",
        "email":         "msantos@ascendia.edu.ph",
        "department":    "College of Computer Studies",
        "job_title":     "Faculty",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00002",
        "first_name":    "Jose",
        "last_name":     "Reyes",
        "username":      "jreyes",
        "email":         "jreyes@ascendia.edu.ph",
        "department":    "IT Support",
        "job_title":     "IT Technician",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00003",
        "first_name":    "Ana",
        "last_name":     "Cruz",
        "username":      "acruz",
        "email":         "acruz@ascendia.edu.ph",
        "department":    "Registrar's Office",
        "job_title":     "Registrar Staff",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00004",
        "first_name":    "Juan",
        "last_name":     "Dela Cruz",
        "username":      "jdelacruz",
        "email":         "jdelacruz@ascendia.edu.ph",
        "department":    "Finance",
        "job_title":     "Finance Officer",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00005",
        "first_name":    "Liza",
        "last_name":     "Mendoza",
        "username":      "lmendoza",
        "email":         "lmendoza@ascendia.edu.ph",
        "department":    "College of Computer Studies",
        "job_title":     "Faculty",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00006",
        "first_name":    "Roberto",
        "last_name":     "Garcia",
        "username":      "rgarcia",
        "email":         "rgarcia@ascendia.edu.ph",
        "department":    "IT Support",
        "job_title":     "IT Asset Manager",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00007",
        "first_name":    "Patricia",
        "last_name":     "Lim",
        "username":      "plim",
        "email":         "plim@ascendia.edu.ph",
        "department":    "Human Resources",
        "job_title":     "HR Officer",
        "status":        "active",
    },
    {
        "employee_num":  "EMP-00008",
        "first_name":    "Miguel",
        "last_name":     "Torres",
        "username":      "mtorres",
        "email":         "mtorres@ascendia.edu.ph",
        "department":    "College of Computer Studies",
        "job_title":     "Department Chair",
        "status":        "active",
    },
]
    # ── Add more staff here ──
    # {
    #     "employee_num":  "EMP-00004",
    #     "first_name":    "Juan",
    #     "last_name":     "Dela Cruz",
    #     "username":      "jdelacruz",
    #     "email":         "jdelacruz@ascendia.edu.ph",
    #     "department":    "Finance",
    #     "job_title":     "Finance Officer",
    #     "status":        "active",
    # },



# ══════════════════════════════════════════════════════════
#  STEP 2 — Department lookup
#  Maps department names to their Snipe-IT department IDs.
#  The script auto-fetches this from your Snipe-IT.
# ══════════════════════════════════════════════════════════

def get_department_map():
    """Returns { 'Department Name': id } from Snipe-IT."""
    data = client.list_departments()
    dept_map = {}
    for d in data.get("rows", []):
        dept_map[d["name"]] = d["id"]
    print(f"📂  Found {len(dept_map)} departments in Snipe-IT:")
    for name, dept_id in dept_map.items():
        print(f"    • [{dept_id}] {name}")
    return dept_map


# ══════════════════════════════════════════════════════════
#  STEP 3 — Existing user lookup
#  Fetches all current users so we don't create duplicates.
# ══════════════════════════════════════════════════════════

def get_existing_users():
    """Returns { 'username': user_dict } from Snipe-IT."""
    data   = client.list_users(limit=500)
    users  = {}
    for u in data.get("rows", []):
        users[u["username"]] = u
    print(f"\n👥  Found {len(users)} existing users in Snipe-IT.")
    return users


# ══════════════════════════════════════════════════════════
#  STEP 4 — The sync logic
# ══════════════════════════════════════════════════════════

def sync_users():
    print("\n" + "═" * 60)
    print("  HRIS USER SYNC — Ascendia Academic Institution")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    dept_map       = get_department_map()
    existing_users = get_existing_users()

    results = {
        "created":     [],
        "deactivated": [],
        "skipped":     [],
        "errors":      [],
    }

    print(f"\n🔄  Processing {len(HR_EMPLOYEES)} employees from HR...\n")

    for emp in HR_EMPLOYEES:
        username = emp["username"]
        email    = emp["email"]
        fullname = f"{emp['first_name']} {emp['last_name']}"

        # ── Business Rule: email must end in @ascendia.edu.ph ──
        if not email.endswith("@ascendia.edu.ph"):
            msg = f"❌  SKIPPED {fullname} — email '{email}' must end in @ascendia.edu.ph"
            print(msg)
            results["errors"].append({"name": fullname, "reason": msg})
            continue

        # ── Look up department ID ──
        dept_name = emp.get("department", "")
        dept_id   = dept_map.get(dept_name)
        if not dept_id:
            msg = f"⚠️   SKIPPED {fullname} — department '{dept_name}' not found in Snipe-IT"
            print(msg)
            results["errors"].append({"name": fullname, "reason": msg})
            continue

        # ── Check if user already exists ──
        if username in existing_users:
            existing = existing_users[username]

            # If terminated → deactivate in Snipe-IT
            if emp["status"] == "terminated":
                try:
                    client.update_asset  # reuse patch method
                    result = client._patch(f"users/{existing['id']}", {"activated": False})
                    print(f"🔴  DEACTIVATED {fullname} ({username}) — terminated in HR")
                    results["deactivated"].append(fullname)
                except Exception as e:
                    print(f"❌  ERROR deactivating {fullname}: {e}")
                    results["errors"].append({"name": fullname, "reason": str(e)})
            else:
                print(f"⏭️   SKIPPED {fullname} ({username}) — already exists")
                results["skipped"].append(fullname)
            continue

        # ── New employee → create in Snipe-IT ──
        if emp["status"] == "terminated":
            print(f"⏭️   SKIPPED {fullname} — terminated, no need to create")
            results["skipped"].append(fullname)
            continue

        try:
            result = client.create_user(
                first_name    = emp["first_name"],
                last_name     = emp["last_name"],
                username      = username,
                email         = email,
                department_id = dept_id,
                password      = "Ascendia@2026!",   # temp password — user should change
                employee_num  = emp.get("employee_num", ""),
            )
            if result.get("status") == "success":
                results["created"].append(fullname)
            else:
                msg = str(result.get("messages", "Unknown error"))
                print(f"❌  ERROR creating {fullname}: {msg}")
                results["errors"].append({"name": fullname, "reason": msg})

        except Exception as e:
            print(f"❌  ERROR creating {fullname}: {e}")
            results["errors"].append({"name": fullname, "reason": str(e)})

    # ── Summary ──
    print("\n" + "═" * 60)
    print("  SYNC COMPLETE — Summary")
    print("═" * 60)
    print(f"  ✅  Created     : {len(results['created'])}")
    print(f"  🔴  Deactivated : {len(results['deactivated'])}")
    print(f"  ⏭️   Skipped     : {len(results['skipped'])}")
    print(f"  ❌  Errors      : {len(results['errors'])}")

    if results["created"]:
        print(f"\n  New users added:")
        for name in results["created"]:
            print(f"    • {name}")

    if results["errors"]:
        print(f"\n  Errors to fix:")
        for e in results["errors"]:
            print(f"    • {e['name']}: {e['reason']}")

    print("═" * 60 + "\n")
    return results


# ══════════════════════════════════════════════════════════
#  LOAD FROM CSV (optional — for real HR export files)
#  If your HR team gives you a CSV file, use this instead
#  of the HR_EMPLOYEES list above.
#
#  CSV format expected:
#  employee_num,first_name,last_name,username,email,department,job_title,status
# ══════════════════════════════════════════════════════════

def load_from_csv(filepath: str):
    """Load employees from a CSV file instead of the hardcoded list."""
    import csv
    employees = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            employees.append(row)
    print(f"📄  Loaded {len(employees)} employees from {filepath}")
    return employees


# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    sync_users()

    # ── To use a CSV file instead, uncomment these lines: ──
    # global HR_EMPLOYEES
    # HR_EMPLOYEES = load_from_csv("hr_export.csv")
    # sync_users()
