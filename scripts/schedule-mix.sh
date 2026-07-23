#!/usr/bin/env bash
# ===========================================================================
# schedule-mix.sh — Cron-compatible scheduled mix generation for OpenMusic
# ===========================================================================
# Usage:
#   ./scripts/schedule-mix.sh [config.yaml]              # Run once
#   OPENMUSIC_NOTIFY_WEBHOOK=https://... ./schedule-mix.sh  # With webhook
#
# Cron example (daily at 6:00 UTC):
#   0 6 * * * cd /path/to/openmusic && ./scripts/schedule-mix.sh >> /var/log/openmusic/schedule.log 2>&1
# ===========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
CONFIG="${1:-${PROJECT_DIR}/examples/schedule.yaml}"

# Ensure log directory exists (keep last 20 runs)
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="${LOG_DIR}/schedule-${TIMESTAMP}.log"

# Rotate old logs: keep only the 20 most recent
cleanup_logs() {
  local log_count
  log_count=$(ls -1 "${LOG_DIR}"/schedule-*.log 2>/dev/null | wc -l)
  if [ "$log_count" -gt 20 ]; then
    ls -1t "${LOG_DIR}"/schedule-*.log | tail -n +21 | xargs -r rm --
  fi
}

# ---- Run -----------------------------------------------------------------
{
  echo "=========================================="
  echo "OpenMusic Scheduled Mix — $(date)"
  echo "Config: ${CONFIG}"
  echo "=========================================="

  # Activate venv (adjust path if different)
  if [ -f "${PROJECT_DIR}/ACE-Step-1.5/.venv/bin/activate" ]; then
    source "${PROJECT_DIR}/ACE-Step-1.5/.venv/bin/activate"
  elif [ -f "${PROJECT_DIR}/.venv/bin/activate" ]; then
    source "${PROJECT_DIR}/.venv/bin/activate"
  fi

  # Build notification flags from environment (optional)
  NOTIFY_FLAGS=""
  if [ -n "${OPENMUSIC_NOTIFY_WEBHOOK:-}" ]; then
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-webhook ${OPENMUSIC_NOTIFY_WEBHOOK}"
  fi
  if [ -n "${OPENMUSIC_NOTIFY_EMAIL:-}" ]; then
    NOTIFY_FLAGS="${NOTIFY_FLAGS} --notify-email ${OPENMUSIC_NOTIFY_EMAIL}"
  fi

  # Run the release pipeline
  cd "$PROJECT_DIR"

  # shellcheck disable=SC2086
  python -m openmusic.cli.main release \
    --config "${CONFIG}" \
    ${NOTIFY_FLAGS} \
    2>&1

  EXIT_CODE=$?
  echo ""
  echo "Exit code: ${EXIT_CODE}"
  echo "Finished:   $(date)"
  echo "=========================================="

  cleanup_logs
  exit $EXIT_CODE
} 2>&1 | tee "$LOG_FILE"
