#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

PROJECT_DIR="${PROJECT_DIR:-/var/www/estatecell}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/estatecell-backups}"
KEEP_BACKUPS="${KEEP_BACKUPS:-14}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
WORK_DIR=""
VERIFY_DB=""

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
LOG_FILE="$BACKUP_DIR/backup.log"
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"

log() { printf '[%s] %s\\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE"; }
die() { log "ERROR: $*"; exit 1; }
cleanup() {
    [[ -n "${VERIFY_DB:-}" && -f "$VERIFY_DB" ]] && rm -f "$VERIFY_DB"
    [[ -n "${WORK_DIR:-}" && -d "$WORK_DIR" ]] && rm -rf "$WORK_DIR"
}
trap cleanup EXIT
trap 'rc=$?; log "FAILED at line $LINENO (exit $rc)"; exit "$rc"' ERR

[[ -d "$PROJECT_DIR" ]] || die "Project directory not found: $PROJECT_DIR"
cd "$PROJECT_DIR"
[[ -f manage.py ]] || die "manage.py not found in $PROJECT_DIR"

# Read the configured DB and media paths from Django settings.
CONFIG_JSON="$("$PYTHON_BIN" manage.py shell -c '
import json
from django.conf import settings
db = settings.DATABASES["default"]
print(json.dumps({
    "engine": db.get("ENGINE", ""),
    "database": str(db.get("NAME", "")),
    "media_root": str(getattr(settings, "MEDIA_ROOT", "")),
    "debug": bool(getattr(settings, "DEBUG", False)),
}))
' 2>>"$LOG_FILE")" || die "Could not read Django settings. Activate the correct virtualenv or set PYTHON_BIN."

eval "$("$PYTHON_BIN" -c '
import json, shlex, sys
d=json.loads(sys.stdin.read())
for k,v in d.items():
    print(f"{k.upper()}={shlex.quote(str(v))}")
' <<< "$CONFIG_JSON")"

[[ "$ENGINE" == "django.db.backends.sqlite3" ]] || die "Configured database is $ENGINE, not SQLite."
[[ -f "$DATABASE" ]] || die "SQLite database not found: $DATABASE"

WORK_DIR="$(mktemp -d "$BACKUP_DIR/.estatecell-${TIMESTAMP}.XXXXXX")"
mkdir -p "$WORK_DIR/media"
log "Starting backup for $PROJECT_DIR"
log "Database: $DATABASE"

# Use SQLite's online backup API rather than copying a live database file.
"$PYTHON_BIN" - "$DATABASE" "$WORK_DIR/db.sqlite3" <<'PY' 2>>"$LOG_FILE"
import sqlite3, sys
with sqlite3.connect(sys.argv[1], timeout=30) as src:
    with sqlite3.connect(sys.argv[2]) as dst:
        src.backup(dst)
with sqlite3.connect(sys.argv[2]) as conn:
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
if result != "ok":
    raise SystemExit("SQLite backup integrity check failed: " + str(result))
print("Database backup integrity check: ok")
PY

if [[ -n "${MEDIA_ROOT:-}" && -d "$MEDIA_ROOT" ]]; then
    cp -a "$MEDIA_ROOT"/. "$WORK_DIR/media"/
    log "Uploaded media files backed up"
else
    log "WARNING: MEDIA_ROOT missing or directory not found; no media files copied"
fi

# Optional portable Django export; the SQLite file remains the primary backup.
if "$PYTHON_BIN" manage.py dumpdata --all --indent 2 \
    --exclude contenttypes --exclude auth.permission \
    > "$WORK_DIR/data.json" 2>>"$LOG_FILE"; then
    log "Django data export created"
else
    rm -f "$WORK_DIR/data.json"
    log "WARNING: dumpdata failed; database backup is still included"
fi

cat > "$WORK_DIR/backup-info.txt" <<EOF
EstateCell backup
Created: $(date --iso-8601=seconds)
Project directory: $PROJECT_DIR
Database engine: $ENGINE
Database path: $DATABASE
Media root: ${MEDIA_ROOT:-}
DEBUG: $DEBUG
EOF

{
    echo "Django version:"
    "$PYTHON_BIN" -m django --version 2>&1 || true
    echo
    echo "Python version:"
    "$PYTHON_BIN" --version 2>&1 || true
    echo
    echo "Git commit (if available):"
    git rev-parse --short HEAD 2>/dev/null || echo "not a git repository"
} > "$WORK_DIR/software-info.txt"

ARCHIVE="$BACKUP_DIR/estatecell_${TIMESTAMP}.tar.gz"
tar -czf "$ARCHIVE" -C "$WORK_DIR" .
chmod 600 "$ARCHIVE"
tar -tzf "$ARCHIVE" >/dev/null

# Verify the database inside the finished archive.
VERIFY_DB="$(mktemp "$BACKUP_DIR/.verify-db.XXXXXX")"
tar -xOzf "$ARCHIVE" ./db.sqlite3 > "$VERIFY_DB" 2>/dev/null || tar -xOzf "$ARCHIVE" db.sqlite3 > "$VERIFY_DB"
"$PYTHON_BIN" - "$VERIFY_DB" <<'PY' 2>>"$LOG_FILE"
import sqlite3, sys
with sqlite3.connect(sys.argv[1]) as conn:
    result = conn.execute("PRAGMA integrity_check").fetchone()[0]
if result != "ok":
    raise SystemExit("Archived database integrity check failed: " + str(result))
print("Archived database integrity check: ok")
PY
rm -f "$VERIFY_DB"
VERIFY_DB=""

# Retain only the newest KEEP_BACKUPS archives.
if [[ "$KEEP_BACKUPS" =~ ^[0-9]+$ ]] && (( KEEP_BACKUPS > 0 )); then
    mapfile -t OLD_ARCHIVES < <(
        find "$BACKUP_DIR" -maxdepth 1 -type f -name 'estatecell_*.tar.gz' -printf '%T@ %p\\n' |
        sort -nr | awk -v keep="$KEEP_BACKUPS" 'NR>keep {$1=""; sub(/^ /,""); print}'
    )
    for old in "${OLD_ARCHIVES[@]:-}"; do
        [[ -n "$old" && -f "$old" ]] && rm -f -- "$old"
    done
fi

log "SUCCESS: $ARCHIVE"
log "Archive size: $(du -h "$ARCHIVE" | awk '{print $1}')"
log "Completed successfully. Backup log: $LOG_FILE"
