"""
=============================================================
  Ascendia IT Asset Management — Graph Database (D4)
  Network/Department Relationship Maps
=============================================================
  HOW TO USE:
  Run:  python3 graph_db.py
=============================================================
  WHAT THIS MODELS:
  - User → owns/uses → Asset
  - Asset → located_in → Room
  - Room → part_of → Department
  - Department → managed_by → Manager
  - Asset → connected_to → Network Switch
  Supports impact analysis: if a room/switch fails,
  which users and assets are affected?
=============================================================
"""

import os
import json
import networkx as nx
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from snipeit_client import SnipeITClient

load_dotenv()

snipe = SnipeITClient(os.getenv("SNIPEIT_URL"), os.getenv("SNIPEIT_TOKEN"))
mongo = MongoClient("mongodb://localhost:27017/")
db    = mongo["ascendia_ams"]

# ── Graph store in MongoDB ────────────────────────────────
graph_col = db["graph_relationships"]

print("\n" + "═" * 60)
print("  GRAPH DATABASE (D4) — Ascendia Academic Institution")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("═" * 60)


# ══════════════════════════════════════════════════════════
#  BUILD THE GRAPH
# ══════════════════════════════════════════════════════════

def build_graph():
    """
    Build a directed graph from Snipe-IT data.
    Nodes: Users, Assets, Locations, Departments
    Edges: owns, located_in, part_of, managed_by
    """
    G = nx.DiGraph()

    # ── Fetch live data from Snipe-IT ─────────────────────
    assets = snipe.list_assets(limit=500).get("rows", [])
    users  = snipe.list_users(limit=500).get("rows", [])

    print(f"\n📊  Building graph from {len(assets)} assets and {len(users)} users...")

    # ── Add department nodes ───────────────────────────────
    depts = snipe.list_departments().get("rows", [])
    for d in depts:
        G.add_node(f"dept:{d['id']}", type="department",
                   name=d["name"], label=d["name"])

    # ── Add location nodes ─────────────────────────────────
    locations = snipe.list_locations().get("rows", [])
    for loc in locations:
        G.add_node(f"loc:{loc['id']}", type="location",
                   name=loc["name"], label=loc["name"])
        # Room → part_of → Parent location
        if loc.get("parent_id"):
            G.add_edge(f"loc:{loc['id']}", f"loc:{loc['parent_id']}",
                       relation="part_of")

    # ── Add user nodes ─────────────────────────────────────
    for u in users:
        uid = f"user:{u['id']}"
        G.add_node(uid, type="user",
                   name=u.get("name", "—"),
                   username=u.get("username", "—"),
                   department=u.get("department", {}).get("name", "—") if u.get("department") else "—",
                   label=u.get("name", "—"))
        # User → member_of → Department
        dept_id = u.get("department", {}).get("id") if u.get("department") else None
        if dept_id:
            G.add_edge(uid, f"dept:{dept_id}", relation="member_of")

    # ── Add asset nodes ────────────────────────────────────
    for a in assets:
        aid = f"asset:{a['id']}"
        cf  = a.get("custom_fields", {})
        ai  = cf.get("AI Priority Score", {}).get("value", "Unscored") if cf else "Unscored"

        G.add_node(aid, type="asset",
                   tag=a.get("asset_tag", "—"),
                   name=a.get("name", "—"),
                   category=a.get("category", {}).get("name", "—") if a.get("category") else "—",
                   status=a.get("status_label", {}).get("name", "—") if a.get("status_label") else "—",
                   ai_priority=ai,
                   label=a.get("asset_tag", "—"))

        # Asset → located_in → Location
        loc_id = a.get("location", {}).get("id") if a.get("location") else None
        if loc_id:
            G.add_edge(aid, f"loc:{loc_id}", relation="located_in")

        # User → owns → Asset (if checked out)
        assigned = a.get("assigned_to")
        if assigned and assigned.get("type") == "user":
            user_id = assigned.get("id")
            if user_id:
                G.add_edge(f"user:{user_id}", aid, relation="owns")

    print(f"  ✅  Graph built:")
    print(f"      Nodes : {G.number_of_nodes()}")
    print(f"      Edges : {G.number_of_edges()}")
    print(f"      Types : {set(nx.get_node_attributes(G, 'type').values())}")

    return G


# ══════════════════════════════════════════════════════════
#  SAVE GRAPH TO MONGODB
# ══════════════════════════════════════════════════════════

def save_graph(G):
    """Persist graph nodes and edges to MongoDB."""
    graph_col.delete_many({})  # clear old graph

    nodes = [{"node_id": n, **d} for n, d in G.nodes(data=True)]
    edges = [{"source": u, "target": v, **d} for u, v, d in G.edges(data=True)]

    if nodes:
        graph_col.insert_many(nodes + [
            {"_type": "edge", "source": e["source"], "target": e["target"],
             "relation": e.get("relation", "—")} for e in edges
        ])
    print(f"\n  💾  Graph saved to MongoDB — {len(nodes)} nodes, {len(edges)} edges")


# ══════════════════════════════════════════════════════════
#  QUERIES
# ══════════════════════════════════════════════════════════

def get_assets_for_user(G, user_name):
    """Find all assets owned by a user."""
    print(f"\n🔍  Assets owned by: {user_name}")
    for node, data in G.nodes(data=True):
        if data.get("type") == "user" and data.get("name") == user_name:
            owned = [G.nodes[n]["tag"] for n in G.successors(node)
                     if G.nodes[n].get("type") == "asset"]
            if owned:
                for tag in owned:
                    print(f"    • {tag}")
            else:
                print(f"    No assets currently assigned.")
            return
    print(f"    User '{user_name}' not found in graph.")


def get_assets_in_location(G, location_name):
    """Find all assets in a location."""
    print(f"\n🔍  Assets in location: {location_name}")
    found = []
    for node, data in G.nodes(data=True):
        if data.get("type") == "asset":
            for neighbor in G.successors(node):
                if G.nodes[neighbor].get("name") == location_name:
                    found.append(f"    • [{data['tag']}] {data['name']} — {data['status']}")
    if found:
        for f in found:
            print(f)
    else:
        print(f"    No assets found in '{location_name}'.")


def impact_analysis(G, location_name):
    """
    Impact analysis: if this location goes down,
    which users and assets are affected?
    """
    print(f"\n⚡  Impact analysis — if '{location_name}' goes offline:")
    affected_assets = []
    affected_users  = []

    for node, data in G.nodes(data=True):
        if data.get("type") == "asset":
            for neighbor in G.successors(node):
                if G.nodes[neighbor].get("name") == location_name:
                    affected_assets.append(data)
                    # Find who owns this asset
                    for user_node, u_data in G.nodes(data=True):
                        if u_data.get("type") == "user":
                            if node in G.successors(user_node):
                                if u_data["name"] not in affected_users:
                                    affected_users.append(u_data["name"])

    print(f"  Assets affected : {len(affected_assets)}")
    for a in affected_assets:
        icon = "🔴" if a.get("ai_priority") == "High" else "🟢"
        print(f"    {icon} [{a['tag']}] {a['name']} — AI: {a.get('ai_priority','Unscored')}")

    print(f"  Users affected  : {len(affected_users)}")
    for u in affected_users:
        print(f"    • {u}")

    if not affected_assets:
        print("    No assets currently assigned to this location.")


def department_asset_map(G):
    """Show which departments own which assets (via users)."""
    print(f"\n🏢  Department → User → Asset map:")
    dept_map = {}
    for node, data in G.nodes(data=True):
        if data.get("type") == "user":
            dept = data.get("department", "Unknown")
            owned = [G.nodes[n]["tag"] for n in G.successors(node)
                     if G.nodes[n].get("type") == "asset"]
            if dept not in dept_map:
                dept_map[dept] = []
            if owned:
                dept_map[dept].append(f"{data['name']}: {', '.join(owned)}")

    for dept, entries in sorted(dept_map.items()):
        if entries:
            print(f"\n  📁 {dept}")
            for e in entries:
                print(f"    • {e}")


def print_graph_summary(G):
    print("\n" + "═" * 60)
    print("  GRAPH DATABASE SUMMARY")
    print("═" * 60)
    type_counts = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, count in type_counts.items():
        print(f"  {t:<15}: {count} nodes")

    edge_counts = {}
    for _, _, data in G.edges(data=True):
        r = data.get("relation", "unknown")
        edge_counts[r] = edge_counts.get(r, 0) + 1
    print()
    for r, count in edge_counts.items():
        print(f"  {r:<15}: {count} edges")
    print("═" * 60 + "\n")


if __name__ == "__main__":
    # Build graph from live Snipe-IT data
    G = build_graph()

    # Save to MongoDB
    save_graph(G)

    # Run queries
    get_assets_for_user(G, "Maria Santos")
    get_assets_for_user(G, "Miguel Torres")
    get_assets_in_location(G, "QC-MAIN-IT_OFFICE")
    get_assets_in_location(G, "QC-MAIN-LAB1")
    impact_analysis(G, "QC-MAIN-LAB1")
    department_asset_map(G)
    print_graph_summary(G)

    print("✅  Graph database (D4) complete!")
    print("    All 4 polyglot data stores are now implemented:\n")
    print("    D1 SQL        → Snipe-IT MySQL")
    print("    D2 NoSQL      → MongoDB")
    print("    D3 Time-Series → InfluxDB")
    print("    D4 Graph      → NetworkX + MongoDB\n")
