#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"
cd "$ROOT"

exec /usr/bin/flock -n "$LOG_DIR/monthly-unpublished-review.lock" \
  /usr/bin/python3 scripts/monthly_unpublished_review.py \
  >> "$LOG_DIR/monthly-unpublished-review.log" 2>&1
