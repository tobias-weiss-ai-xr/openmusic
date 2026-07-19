#!/usr/bin/env bash
# ============================================================================
# OpenMusic Schedule Mix — Cron-friendly automated mix generation
# ============================================================================
# Usage:
#   ./scripts/schedule-mix.sh [--dry-run] [--config schedule.yaml]
#
# Designed to be called from cron. Generates a mix using the release pipeline
# and optionally uploads to YouTube. All output is logged for later inspection.
#
# Cron example (runs every Saturday at 2am):
#   0 2 * * 6 /path/to/openmusic/scripts/schedule-mix.sh \
#     --config /path/to/schedule.yaml >> /var/log/openmusic/schedule.log 2>&1
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Defaults ---
CONFIG="${PROJECT_DIR}/examples/schedule.yaml"
VENV_DIR="${PROJECT_DIR}/packages/core/.venv"
LOG_DIR="${PROJECT_DIR}/.cache/schedule-logs"
DRY_RUN=false
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    --venv) VENV_DIR="$2"; shift 2 ;;
    --log-dir) LOG_DIR="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --help|-h)
      echo "Usage: $0 [--config path] [--venv path] [--log-dir path] [--dry-run]"
      echo ""
      echo "Options:"
      echo "  --config PATH   Path to schedule YAML (default: examples/schedule.yaml)"
      echo "  --venv DIR      Python venv directory (default: packages/core/.venv)"
      echo "  --log-dir DIR   Output log directory (default: .cache/schedule-logs)"
      echo "  --dry-run       Print what would be done without executing"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Validate config ---
if [ ! -f "$CONFIG" ]; then
  echo "[ERROR] Schedule config not found: $CONFIG"
  exit 1
fi

# --- Ensure log directory ---
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/schedule-${TIMESTAMP}.log"

# --- Activate Python venv ---
if [ -f "${VENV_DIR}/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"
elif [ -f "${VENV_DIR}/Scripts/activate" ]; then
  # Windows fallback
  # shellcheck disable=SC1091
  source "${VENV_DIR}/Scripts/activate"
else
  echo "[WARN] No venv found at ${VENV_DIR}; trying system Python"
fi

# --- Python command ---
PYTHON_CMD="python3"
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
fi

# --- Parse config with Python ---
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Reading config: ${CONFIG}" | tee -a "$LOG_FILE"

parse_config() {
  "${PYTHON_CMD}" -c "
import yaml, sys
with open('${CONFIG}') as f:
    cfg = yaml.safe_load(f)
if not cfg:
    sys.exit(1)
# Flatten fields
print(cfg.get('length', '2h'))
print(cfg.get('bpm', 125))
print(cfg.get('key', 'Dm'))
print(cfg.get('output_path', 'mix.flac'))
print(cfg.get('title', ''))
print(cfg.get('description', ''))
print(cfg.get('tags', ''))
print(cfg.get('privacy', 'unlisted'))
print(cfg.get('playlist', 'dub odyssee'))
print(cfg.get('schedule_datetime', ''))
print(cfg.get('model', 'ace-step'))
print(cfg.get('no_effects', False))
" 2>>"$LOG_FILE"
}

# shellcheck disable=SC2046,SC2034
IFS=$'\n' read -r -d '' LENGTH BPM KEY OUTPUT TITLE DESCRIPTION TAGS PRIVACY PLAYLIST SCHEDULE_DT MODEL NO_EFFECTS <<<$(parse_config; printf '\0')

if [ -z "$LENGTH" ]; then
  echo "[ERROR] Failed to parse config: ${CONFIG}" | tee -a "$LOG_FILE"
  exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Schedule: ${LENGTH} @${BPM}BPM ${KEY} → ${OUTPUT}" | tee -a "$LOG_FILE"

# --- Build the release command ---
RELEASE_CMD=("${PYTHON_CMD}" -m openmusic.cli.main release)
RELEASE_CMD+=(--length "$LENGTH")
RELEASE_CMD+=(--bpm "$BPM")
RELEASE_CMD+=(--key "$KEY")
RELEASE_CMD+=(--output "$OUTPUT")
RELEASE_CMD+=(--title "$TITLE")
RELEASE_CMD+=(--privacy "$PRIVACY")

if [ -n "$DESCRIPTION" ]; then
  RELEASE_CMD+=(--description "$DESCRIPTION")
fi
if [ -n "$TAGS" ]; then
  RELEASE_CMD+=(--tags "$TAGS")
fi
if [ -n "$PLAYLIST" ]; then
  RELEASE_CMD+=(--playlist "$PLAYLIST")
fi
if [ -n "$SCHEDULE_DT" ]; then
  RELEASE_CMD+=(--schedule "$SCHEDULE_DT")
fi
if [ "$NO_EFFECTS" = "True" ]; then
  RELEASE_CMD+=(--no-effects)
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Command: ${RELEASE_CMD[*]}" | tee -a "$LOG_FILE"

# --- Execute or dry-run ---
if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] Would execute: ${RELEASE_CMD[*]}" | tee -a "$LOG_FILE"
  echo "[DRY-RUN] Log: ${LOG_FILE}" | tee -a "$LOG_FILE"
  echo "[DRY-RUN] Done — no changes made." | tee -a "$LOG_FILE"
  exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting mix generation..." | tee -a "$LOG_FILE"

# Run the release command
set +e
"${RELEASE_CMD[@]}" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -eq 0 ]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: Mix generated and uploaded" | tee -a "$LOG_FILE"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] FAILED: Exit code ${EXIT_CODE}" | tee -a "$LOG_FILE"
fi

# Rotate logs: keep last 20
find "$LOG_DIR" -name 'schedule-*.log' -type f | sort | head -n -20 | xargs -r rm -f

exit $EXIT_CODE
