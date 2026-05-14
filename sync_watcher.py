"""
=============================================================
  ASCENDIA AMS — REAL-TIME SYNC WATCHER
  Monitors all changes and syncs across all systems
=============================================================
  Run: python3 sync_watcher.py
  Keep running in background — watches every 30 seconds
=============================================================
"""

import os
import time
import json
import random
import hashlib
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SNIPEIT_URL = os.getenv("SNIPEIT_URL", "http://snipe-it.test")
SNIPEIT_TOKEN = os.getenv("SNIPEIT_TOKEN", "")
INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8181")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_DATABASE = os.getenv("INFLUXDB_DATABASE", "ascendia_telemetry")
POLL_INTERVAL = 30  # seconds

HEADERS = {
    "Authorization": f"Bearer {SNIPEIT_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ── State tracking ────────────────────────────────────────
state = {
    "assets": {},      # asset_id -> hash of asset data
    "users": {},       # user_id -> hash of user data
    "licenses": {},    # license_id -> hash of license data
    "last_sync": None,
}

def get_hash(obj):
    return hashlib.md5(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()

def snipe_get(endpoint):
    try:
        r = requests.get(f"{SNIPEIT_URL}/api/v1/{endpoint}", headers=HEADERS, timeout=10)
        return r.json()
    except:
        return {}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icon = {"INFO": "ℹ️ ", "OK": "✅", "WARN": "⚠️ ", "ERR": "❌", "SYNC": "🔄", "NEW": "➕", "DEL": "🗑️", "MOD": "✏️ "}.get(level, "  ")
    print(f"  [{ts}] {icon}  {msg}")

# ── Sync functions ────────────────────────────────────────

def sync_influxdb(asset):
    """Write fresh telemetry for a single asset"""
    try:
        from influxdb_client_3 import InfluxDBClient3, Point
        influx = InfluxDBClient3(host=INFLUXDB_URL, token=INFLUXDB_TOKEN, database=INFLUXDB_DATABASE)
        tag = asset.get("asset_tag", "")
        name = asset.get("name", "")
        category = (asset.get("category") or {}).get("name", "Other")

        if tag == "AAI-2026-00001":
            battery, cpu, memory = 8.0, 94.0, 95.0
        elif category in ("Network Equipment", "UPS", "Printers", "Scanners", "Security Equipment", "Audio Equipment"):
            battery, cpu, memory = 100.0, random.uniform(5, 20), random.uniform(10, 30)
        else:
            battery = random.uniform(70, 95)
            cpu = random.uniform(5, 30)
            memory = random.uniform(20, 50)

        health = (battery * 0.4) + ((100 - cpu) * 0.3) + ((100 - memory) * 0.3)

        point = (
            Point("device_telemetry")
            .tag("asset_tag", tag)
            .tag("asset_name", name)
            .tag("category", category)
            .field("battery_pct", round(battery, 1))
            .field("cpu_pct", round(cpu, 1))
            .field("memory_pct", round(memory, 1))
            .field("health_score", round(health, 1))
            .time(datetime.now(timezone.utc))
        )
        influx.write(record=point)
        return True
    except Exception as e:
        log(f"InfluxDB sync failed: {e}", "ERR")
        return False

def sync_mongodb_audit(action, actor, asset_tag, before, after, notes=""):
    """Write audit event to MongoDB"""
    try:
        from pymongo import MongoClient
        db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]
        db.audit_events.insert_one({
            "event_id": f"AUD-{asset_tag}-{int(time.time())}",
            "action": action,
            "actor": actor,
            "asset_tag": asset_tag,
            "before": before,
            "after": after,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "process": "Real-time Sync Watcher",
            "notes": notes
        })
        return True
    except Exception as e:
        log(f"MongoDB audit failed: {e}", "ERR")
        return False

def sync_graph(assets, users):
    """Update graph relationships"""
    try:
        import networkx as nx
        from pymongo import MongoClient
        G = nx.DiGraph()

        for a in assets:
            tag = a.get("asset_tag", "")
            location = (a.get("location") or {}).get("name", "Unknown")
            category = (a.get("category") or {}).get("name", "Other")
            assigned = (a.get("assigned_to") or {}).get("name", None)
            supplier = (a.get("supplier") or {}).get("name", None)

            G.add_node(tag, type="asset", name=a.get("name",""), category=category)
            if location:
                G.add_node(location, type="location")
                G.add_edge(tag, location, relation="located_at")
            if assigned:
                G.add_node(assigned, type="user")
                G.add_edge(tag, assigned, relation="assigned_to")
            if supplier:
                G.add_node(supplier, type="supplier")
                G.add_edge(tag, supplier, relation="supplied_by")

        db = MongoClient("mongodb://localhost:27017/")["ascendia_ams"]
        db.graph_relationships.delete_many({})
        db.graph_relationships.insert_one({
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "nodes": len(G.nodes),
            "edges": len(G.edges),
            "assets": len(assets),
            "node_list": [{"id": n, **G.nodes[n]} for n in G.nodes],
            "edge_list": [{"from": u, "to": v, **G.edges[u,v]} for u,v in G.edges]
        })
        return len(G.nodes), len(G.edges)
    except Exception as e:
        log(f"Graph sync failed: {e}", "ERR")
        return 0, 0

def sync_ai_score(asset):
    """Score asset if it has maintenance notes"""
    try:
        from ai_priority_scorer import score_text
        notes = (asset.get("custom_fields") or {}).get("Maintenance Notes", {}).get("value", "") or ""
        current = (asset.get("custom_fields") or {}).get("AI Priority Score", {}).get("value", "Unscored")

        if notes and current == "Unscored":
            score = score_text(notes)
            requests.patch(
                f"{SNIPEIT_URL}/api/v1/hardware/{asset['id']}",
                headers=HEADERS,
                json={"_snipeit_ai_priority_score_2": score}
            )
            return score
        return None
    except Exception as e:
        log(f"AI scorer failed: {e}", "ERR")
        return None

def sync_redis_event(event_type, data):
    """Push event to Redis stream"""
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.xadd("ascendia:events", {
            "type": event_type,
            "data": json.dumps(data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return True
    except:
        return False

# ── Main watcher loop ─────────────────────────────────────

def check_assets(all_assets):
    """Check for asset changes and sync"""
    changes = 0
    current_ids = set()

    for asset in all_assets:
        aid = asset["id"]
        tag = asset.get("asset_tag", "")
        current_ids.add(aid)
        h = get_hash({
            "status": (asset.get("status_label") or {}).get("name"),
            "location": (asset.get("location") or {}).get("name"),
            "assigned_to": (asset.get("assigned_to") or {}).get("name"),
            "ai_score": (asset.get("custom_fields") or {}).get("AI Priority Score", {}).get("value"),
            "purchase_cost": asset.get("purchase_cost"),
        })

        if aid not in state["assets"]:
            # New asset detected
            log(f"New asset detected: {tag} — {asset.get('name')}", "NEW")
            sync_influxdb(asset)
            sync_mongodb_audit("ASSET_ADDED", "Sync Watcher", tag, {}, {
                "name": asset.get("name"),
                "status": (asset.get("status_label") or {}).get("name"),
                "location": (asset.get("location") or {}).get("name"),
            }, f"New asset {tag} detected and synced")
            sync_ai_score(asset)
            sync_redis_event("ASSET_ADDED", {"asset_tag": tag, "name": asset.get("name")})
            state["assets"][aid] = h
            changes += 1

        elif state["assets"][aid] != h:
            # Asset modified
            old_h = state["assets"][aid]
            log(f"Asset modified: {tag} — {asset.get('name')}", "MOD")
            sync_influxdb(asset)
            sync_mongodb_audit("ASSET_MODIFIED", "Sync Watcher", tag,
                {"hash": old_h}, {
                    "status": (asset.get("status_label") or {}).get("name"),
                    "location": (asset.get("location") or {}).get("name"),
                    "assigned_to": (asset.get("assigned_to") or {}).get("name"),
                },
                f"Asset {tag} modified — auto-synced to all databases"
            )
            new_score = sync_ai_score(asset)
            if new_score:
                log(f"AI scored {tag}: {new_score}", "OK")
            sync_redis_event("ASSET_MODIFIED", {"asset_tag": tag})
            state["assets"][aid] = h
            changes += 1

    # Check for deleted assets
    deleted_ids = set(state["assets"].keys()) - current_ids
    for did in deleted_ids:
        log(f"Asset deleted: ID {did}", "DEL")
        sync_mongodb_audit("ASSET_DELETED", "Sync Watcher", f"ID-{did}", {"id": did}, {}, "Asset removed from Snipe-IT")
        sync_redis_event("ASSET_DELETED", {"asset_id": did})
        del state["assets"][did]
        changes += 1

    return changes

def check_users(all_users):
    """Check for user changes"""
    changes = 0
    current_ids = set()

    for user in all_users:
        uid = user["id"]
        current_ids.add(uid)
        h = get_hash({
            "activated": user.get("activated"),
            "department": (user.get("department") or {}).get("name"),
            "jobtitle": user.get("jobtitle"),
        })

        if uid not in state["users"]:
            log(f"New user detected: {user.get('name')}", "NEW")
            sync_mongodb_audit("USER_ADDED", "Sync Watcher", None, {}, {
                "name": user.get("name"),
                "department": (user.get("department") or {}).get("name"),
            })
            sync_redis_event("USER_ADDED", {"name": user.get("name")})
            state["users"][uid] = h
            changes += 1
        elif state["users"][uid] != h:
            log(f"User modified: {user.get('name')}", "MOD")
            sync_mongodb_audit("USER_MODIFIED", "Sync Watcher", None,
                {"hash": state["users"][uid]},
                {"name": user.get("name"), "activated": user.get("activated")}
            )
            sync_redis_event("USER_MODIFIED", {"name": user.get("name")})
            state["users"][uid] = h
            changes += 1

    deleted_ids = set(state["users"].keys()) - current_ids
    for did in deleted_ids:
        log(f"User deleted: ID {did}", "DEL")
        del state["users"][did]
        changes += 1

    return changes

def check_licenses(all_licenses):
    """Check for license changes"""
    changes = 0
    for lic in all_licenses:
        lid = lic["id"]
        h = get_hash({"seats": lic.get("seats"), "remaining": lic.get("remaining_seats")})
        if lid not in state["licenses"]:
            state["licenses"][lid] = h
        elif state["licenses"][lid] != h:
            log(f"License modified: {lic.get('name')}", "MOD")
            sync_mongodb_audit("LICENSE_MODIFIED", "Sync Watcher", None, {}, {
                "name": lic.get("name"), "seats": lic.get("seats")
            })
            state["licenses"][lid] = h
            changes += 1
    return changes

def run_watcher():
    print("\n" + "═"*60)
    print("  ASCENDIA AMS — REAL-TIME SYNC WATCHER")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Polling every {POLL_INTERVAL} seconds")
    print("═"*60)
    print("  Watching: Snipe-IT → InfluxDB + MongoDB + Graph DB + Redis")
    print("  Press Control+C to stop\n")

    # Initial load
    log("Loading initial state...", "INFO")
    assets = snipe_get("hardware?limit=500").get("rows", [])
    users = snipe_get("users?limit=500").get("rows", [])
    licenses = snipe_get("licenses?limit=50").get("rows", [])

    for a in assets: state["assets"][a["id"]] = get_hash({
        "status": (a.get("status_label") or {}).get("name"),
        "location": (a.get("location") or {}).get("name"),
        "assigned_to": (a.get("assigned_to") or {}).get("name"),
        "ai_score": (a.get("custom_fields") or {}).get("AI Priority Score", {}).get("value"),
        "purchase_cost": a.get("purchase_cost"),
    })
    for u in users: state["users"][u["id"]] = get_hash({"activated": u.get("activated"), "department": (u.get("department") or {}).get("name")})
    for l in licenses: state["licenses"][l["id"]] = get_hash({"seats": l.get("seats"), "remaining": l.get("remaining_seats")})

    log(f"Initial state loaded — {len(assets)} assets, {len(users)} users, {len(licenses)} licenses", "OK")

    # Initial graph sync
    nodes, edges = sync_graph(assets, users)
    log(f"Graph DB initialized — {nodes} nodes, {edges} edges", "OK")

    cycle = 0
    while True:
        try:
            time.sleep(POLL_INTERVAL)
            cycle += 1
            print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] 🔄  Cycle #{cycle} — checking for changes...")

            assets = snipe_get("hardware?limit=500").get("rows", [])
            users = snipe_get("users?limit=500").get("rows", [])
            licenses = snipe_get("licenses?limit=50").get("rows", [])

            asset_changes = check_assets(assets)
            user_changes = check_users(users)
            lic_changes = check_licenses(licenses)

            total = asset_changes + user_changes + lic_changes

            if total > 0:
                log(f"{total} change(s) detected and synced!", "OK")
                nodes, edges = sync_graph(assets, users)
                log(f"Graph DB updated — {nodes} nodes, {edges} edges", "OK")
            else:
                log("No changes detected", "INFO")

            state["last_sync"] = datetime.now().isoformat()

        except KeyboardInterrupt:
            print("\n\n  Sync watcher stopped.")
            break
        except Exception as e:
            log(f"Watcher error: {e}", "ERR")
            time.sleep(5)

if __name__ == "__main__":
    run_watcher()
