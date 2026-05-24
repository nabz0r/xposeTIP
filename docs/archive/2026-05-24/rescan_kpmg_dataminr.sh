#!/usr/bin/env bash
# Rescan 12 targets (3 kpmg + 9 dataminr) for BFP validation.
# Run directly in a terminal (NOT via Claude Code).
set -euo pipefail

API="http://localhost:8000/api/v1"
EMAIL="nabil@xpose.dev"
PASS="xpose2026"

KPMG_WS="ad96117e-ffff-487b-a05b-119f2cccc976"
DATAMINR_WS="2ec3c06a-c3f4-4ccd-9838-ebfc647dc220"

KPMG_TARGETS=(
  "fe57ce83-b79a-4731-97e4-28cfeb434ce2"
  "418b271f-cf63-459e-a0db-d90772384b56"
  "d9538ec7-3db3-4997-ab99-3b797d28dae9"
)

DATAMINR_TARGETS=(
  "e026e3fd-12d6-4e1b-b9ea-1095005f46ad"
  "3ffe6e0a-0110-4a93-bd5f-f0bf726981b5"
  "ab7c31e2-27c7-4250-8078-a30abcf9e4a2"
  "7bc91ca1-7cba-41fa-ba14-7728770064f3"
  "10713caa-2d4b-44d8-b100-ca867de41759"
  "0db56541-8edc-490d-a915-6dd02ab9cde2"
  "5f1ef9f7-3430-4761-bb78-41297a2d5d68"
  "f2b1edd9-d84b-4ed3-81b1-0472219f02cb"
  "921d7c14-6e68-4525-9393-6b6da7219dfa"
)

OUT=/tmp/rescan_scans.txt
LOG=/tmp/rescan_progress.log
: > "$OUT"
: > "$LOG"

log()   { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG"; }

get_token() {
  curl -s -m 10 -X POST "$API/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))"
}

switch_ws() {
  local tok=$1 ws=$2
  curl -s -m 10 -X POST "$API/auth/switch-workspace" \
    -H "Authorization: Bearer $tok" \
    -H "Content-Type: application/json" \
    -d "{\"workspace_id\":\"$ws\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))"
}

trigger() {
  local tok=$1 tid=$2 label=$3
  local resp sid
  resp=$(curl -s -m 30 -X POST "$API/scans" \
    -H "Authorization: Bearer $tok" \
    -H "Content-Type: application/json" \
    -d "{\"target_id\":\"$tid\"}")
  sid=$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
  if [[ -z "$sid" ]]; then
    log "$label FAIL $tid → $resp"
    return 1
  fi
  echo "$label|$tid|$sid" >> "$OUT"
  log "$label OK   $tid → $sid"
}

# ---------- KPMG ----------
log "=== KPMG workspace ==="
TOK=$(get_token);  [[ -n "$TOK" ]] || { log "login failed";       exit 1; }
TOK=$(switch_ws "$TOK" "$KPMG_WS"); [[ -n "$TOK" ]] || { log "switch kpmg failed"; exit 1; }
for tid in "${KPMG_TARGETS[@]}"; do
  trigger "$TOK" "$tid" "kpmg" || true
done

# ---------- DATAMINR ----------
log "=== DATAMINR workspace ==="
TOK=$(get_token);  [[ -n "$TOK" ]] || { log "login failed";          exit 1; }
TOK=$(switch_ws "$TOK" "$DATAMINR_WS"); [[ -n "$TOK" ]] || { log "switch dataminr failed"; exit 1; }
for tid in "${DATAMINR_TARGETS[@]}"; do
  trigger "$TOK" "$tid" "dataminr" || true
done

log "=== triggered $(wc -l < "$OUT") / 12 scans ==="
echo
cat "$OUT"
