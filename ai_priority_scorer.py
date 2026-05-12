"""
=============================================================
  Ascendia IT Asset Management — Phase 2c
  AI Priority Scorer — NLP scores maintenance notes
=============================================================
  HOW TO USE:
  1. Install:  pip3 install transformers torch
  2. Run:      python3 ai_priority_scorer.py
=============================================================
  WHAT THIS SCRIPT DOES:
  - Reads maintenance notes from Snipe-IT assets
  - Uses a lightweight NLP model to classify urgency
  - Scores each note as: High, Medium, Low, or Unscored
  - Updates the AI Priority Score custom field in Snipe-IT
  - If score is High → changes asset status to Maintenance-High
=============================================================
"""

import os
import re
from datetime import datetime
from dotenv import load_dotenv
from snipeit_client import SnipeITClient

load_dotenv()

client = SnipeITClient(
    base_url = os.getenv("SNIPEIT_URL", "http://snipe-it.test"),
    token    = os.getenv("SNIPEIT_TOKEN", ""),
)


# ══════════════════════════════════════════════════════════
#  RULE-BASED NLP SCORER
#  No API key needed. Works offline.
#  Uses keyword matching to classify urgency.
#  You can upgrade this to Hugging Face later.
# ══════════════════════════════════════════════════════════

HIGH_KEYWORDS = [
    "not working", "broken", "dead", "failed", "failure",
    "crashed", "won't turn on", "wont turn on", "no power",
    "screen cracked", "damaged", "urgent", "emergency",
    "data loss", "virus", "malware", "overheating", "smoke",
    "cannot boot", "blue screen", "bsod", "totally broken",
    "completely dead", "not booting", "won't start",
    "liquid damage", "water damage", "dropped", "physical damage",
    "hindi gumagana", "sira", "patay", "hindi na bumubukas",
]

MEDIUM_KEYWORDS = [
    "slow", "laggy", "freezing", "freezes", "hanging",
    "battery", "charging", "won't charge", "low battery",
    "keyboard", "trackpad", "mouse not working", "wifi issue",
    "audio", "speaker", "microphone", "webcam", "display issue",
    "blurry", "flickering", "dim screen", "partial damage",
    "needs repair", "needs replacement", "performance issue",
    "mabagal", "nagyeyelo", "hindi nag-charge",
]

LOW_KEYWORDS = [
    "software update", "update needed", "needs cleaning",
    "dust", "minor issue", "cosmetic", "scratch", "sticker",
    "password reset", "login issue", "account", "config",
    "setup", "install", "reinstall", "general maintenance",
    "scheduled", "routine", "for checking", "for inspection",
    "kailangan ng update", "linisin",
]


def score_note(note: str) -> str:
    """
    Classify a maintenance note as High, Medium, Low, or Unscored.
    Uses keyword matching with priority hierarchy.
    """
    if not note or len(note.strip()) < 3:
        return "Unscored"

    text = note.lower()

    # Check High first (most urgent wins)
    for keyword in HIGH_KEYWORDS:
        if keyword in text:
            return "High"

    for keyword in MEDIUM_KEYWORDS:
        if keyword in text:
            return "Medium"

    for keyword in LOW_KEYWORDS:
        if keyword in text:
            return "Low"

    # Has text but no keywords matched
    return "Unscored"


def explain_score(note: str, score: str) -> str:
    """Return which keyword triggered the score."""
    if score == "Unscored":
        return "No matching keywords found."

    text  = note.lower()
    lists = {
        "High":   HIGH_KEYWORDS,
        "Medium": MEDIUM_KEYWORDS,
        "Low":    LOW_KEYWORDS,
    }
    for keyword in lists.get(score, []):
        if keyword in text:
            return f"Matched keyword: '{keyword}'"
    return ""


# ══════════════════════════════════════════════════════════
#  GET CUSTOM FIELD KEY FOR "AI Priority Score"
# ══════════════════════════════════════════════════════════

def get_ai_priority_field_key() -> str:
    """Find the DB column name for AI Priority Score field."""
    try:
        data = client._get("fields")
        for f in data.get("rows", []):
            if "ai priority" in f["name"].lower():
                return f["db_column_name"]
    except Exception:
        pass
    return None


def get_maintenance_high_status_id() -> int:
    """Get the ID of 'Maintenance - High' status label."""
    data = client.list_status_labels()
    for s in data.get("rows", []):
        if "maintenance" in s["name"].lower() and "high" in s["name"].lower():
            return s["id"]
    return None


# ══════════════════════════════════════════════════════════
#  SCORE A SINGLE MAINTENANCE NOTE (manual input)
# ══════════════════════════════════════════════════════════

def score_single_note(note: str):
    """Score a single note and print the result."""
    score   = score_note(note)
    reason  = explain_score(note, score)

    colors = {
        "High":     "🔴",
        "Medium":   "🟡",
        "Low":      "🟢",
        "Unscored": "⚪",
    }

    print(f"\n  Note    : \"{note}\"")
    print(f"  Score   : {colors.get(score, '⚪')} {score}")
    print(f"  Reason  : {reason}")
    return score


# ══════════════════════════════════════════════════════════
#  PROCESS ALL ASSETS WITH MAINTENANCE NOTES
#  Reads Maintenance Notes field from every asset,
#  scores it, and updates AI Priority Score field.
# ══════════════════════════════════════════════════════════

def process_all_assets():
    print("\n" + "═" * 60)
    print("  AI PRIORITY SCORER — Ascendia Academic Institution")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60)

    # Get custom field key
    ai_field_key = get_ai_priority_field_key()
    if ai_field_key:
        print(f"\n🔑  AI Priority Score field key: {ai_field_key}")
    else:
        print("\n⚠️   Could not find AI Priority Score field key.")
        print("    Scores will be printed but NOT saved to Snipe-IT.")
        print("    Run print_custom_field_keys() to debug.\n")

    maintenance_high_id = get_maintenance_high_status_id()

    # Fetch all assets
    assets = client.list_assets(limit=500)
    rows   = assets.get("rows", [])
    print(f"\n📦  Found {len(rows)} assets to process...\n")

    results = {
        "High":     [],
        "Medium":   [],
        "Low":      [],
        "Unscored": [],
        "errors":   [],
    }

    for asset in rows:
        asset_id  = asset["id"]
        asset_tag = asset.get("asset_tag", "—")
        name      = asset.get("name", "—")

        # Get maintenance note from asset notes field
        note = asset.get("notes", "") or ""

        # Also check custom fields if available
        custom_fields = asset.get("custom_fields", {})
        for field_name, field_data in custom_fields.items():
            if "maintenance" in field_name.lower():
                note = field_data.get("value", "") or note

        score  = score_note(note)
        reason = explain_score(note, score)

        icons = {"High": "🔴", "Medium": "🟡", "Low": "🟢", "Unscored": "⚪"}
        print(f"  {icons.get(score,'⚪')} [{asset_tag}] {name}")
        if note:
            print(f"      Note  : \"{note[:80]}{'...' if len(note)>80 else ''}\"")
        print(f"      Score : {score}  ({reason})")

        results[score].append(asset_tag)

        # Update AI Priority Score field in Snipe-IT
        if ai_field_key:
            try:
                update_payload = {ai_field_key: score}

                # Business Rule BR003: If High → change status to Maintenance-High
                if score == "High" and maintenance_high_id:
                    update_payload["status_id"] = maintenance_high_id
                    print(f"      ⚡  Status → Maintenance-High (BR003)")

                client.update_asset(asset_id, update_payload)
            except Exception as e:
                print(f"      ❌  Could not update: {e}")
                results["errors"].append(asset_tag)

    # ── Summary ──────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  AI SCORING COMPLETE — Summary")
    print("═" * 60)
    print(f"  🔴  High     : {len(results['High'])}")
    print(f"  🟡  Medium   : {len(results['Medium'])}")
    print(f"  🟢  Low      : {len(results['Low'])}")
    print(f"  ⚪  Unscored : {len(results['Unscored'])}")
    print(f"  ❌  Errors   : {len(results['errors'])}")
    print("═" * 60 + "\n")

    return results


# ══════════════════════════════════════════════════════════
#  INTERACTIVE MODE
#  Type a maintenance note and get a score instantly.
#  Great for testing and demos.
# ══════════════════════════════════════════════════════════

def interactive_mode():
    print("\n" + "═" * 60)
    print("  AI PRIORITY SCORER — Interactive Test Mode")
    print("  Type a maintenance note to score it.")
    print("  Type 'quit' to exit.")
    print("═" * 60)

    test_notes = [
        "Screen cracked after being dropped",
        "Laptop is running slow and freezing often",
        "Needs software update and general cleaning",
        "Hindi na bumubukas ang laptop",
        "Battery drains quickly",
        "For routine inspection next week",
    ]

    print("\n📋  Sample notes from your architecture doc:\n")
    for note in test_notes:
        score_single_note(note)

    print("\n\n💬  Now try your own notes (or type 'quit'):\n")
    while True:
        note = input("  Enter maintenance note: ").strip()
        if note.lower() in ("quit", "exit", "q"):
            break
        if note:
            score_single_note(note)


# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\nWhat do you want to do?")
    print("  1 — Score all assets in Snipe-IT")
    print("  2 — Interactive test mode (type notes manually)")
    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        process_all_assets()
    else:
        interactive_mode()
