#!/bin/bash
# =============================================================
#  Ascendia AMS — Automated Backup Script
#  Backs up MySQL, MongoDB, and all project files
# =============================================================
#  HOW TO USE:
#  chmod +x backup.sh
#  ./backup.sh
#  Or schedule with cron: 0 2 * * * /Users/darwinmari/ascendia-ams/backup.sh
# =============================================================

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$HOME/ascendia-ams/backups/$TIMESTAMP"
PROJECT_DIR="$HOME/ascendia-ams"
SNIPEIT_DIR="$HOME/Sites/snipe-it"

echo ""
echo "============================================================"
echo "  ASCENDIA AMS — AUTOMATED BACKUP"
echo "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo ""
echo "📁  Backup directory: $BACKUP_DIR"

# ── 1. MySQL backup (Snipe-IT database) ──────────────────────
echo ""
echo "1️⃣   Backing up MySQL (Snipe-IT)..."
mysqldump -u root -psnipeit snipeit > "$BACKUP_DIR/snipeit_mysql_$TIMESTAMP.sql" 2>/dev/null
if [ $? -eq 0 ]; then
    SIZE=$(du -sh "$BACKUP_DIR/snipeit_mysql_$TIMESTAMP.sql" | cut -f1)
    echo "  ✅  MySQL backup complete — $SIZE"
else
    echo "  ❌  MySQL backup failed"
fi

# ── 2. MongoDB backup ─────────────────────────────────────────
echo ""
echo "2️⃣   Backing up MongoDB (ascendia_ams)..."
mongodump --db ascendia_ams --out "$BACKUP_DIR/mongodb" --quiet 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅  MongoDB backup complete"
else
    echo "  ❌  MongoDB backup failed (is MongoDB running?)"
fi

# ── 3. Project files backup ───────────────────────────────────
echo ""
echo "3️⃣   Backing up project files..."
cp "$PROJECT_DIR"/*.py "$BACKUP_DIR/" 2>/dev/null
cp "$PROJECT_DIR"/*.html "$BACKUP_DIR/" 2>/dev/null
cp "$PROJECT_DIR"/.env "$BACKUP_DIR/env_backup" 2>/dev/null
echo "  ✅  Project files backed up"

# ── 4. Snipe-IT .env backup ───────────────────────────────────
echo ""
echo "4️⃣   Backing up Snipe-IT config..."
cp "$SNIPEIT_DIR/.env" "$BACKUP_DIR/snipeit_env_backup" 2>/dev/null
echo "  ✅  Snipe-IT config backed up"

# ── 5. Cleanup old backups (keep last 7) ─────────────────────
echo ""
echo "5️⃣   Cleaning old backups (keeping last 7)..."
ls -dt "$PROJECT_DIR/backups"/*/ 2>/dev/null | tail -n +8 | xargs rm -rf 2>/dev/null
BACKUP_COUNT=$(ls "$PROJECT_DIR/backups" 2>/dev/null | wc -l | tr -d ' ')
echo "  ✅  $BACKUP_COUNT backup(s) retained"

# ── Summary ───────────────────────────────────────────────────
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo ""
echo "============================================================"
echo "  BACKUP COMPLETE"
echo "  Location : $BACKUP_DIR"
echo "  Size     : $TOTAL_SIZE"
echo "  Time     : $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""
