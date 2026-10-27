#!/usr/bin/env bash
# Reproduce helper. Primary path = connect AMBER; also supports local_sim summarize.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  set -a; source .env; set +a
fi

DATA_DIR="${AMBER_DATA_DIR:-reference/fair_r2}"
BACKEND="${AMBER_BENCH_BACKEND:-amber}"

echo "== AMBER public bench harness =="
echo "ROOT=$ROOT"
echo "DATA_DIR=$DATA_DIR  BACKEND=$BACKEND"
echo "(This repo is a comparison harness, not the memory product source.)"
echo

echo ">>> summarize shipped/current raw (no API)"
python3 scripts/summarize.py --data-dir "$DATA_DIR"
echo

if [[ -z "${AMBER_API_KEY:-}" && "$BACKEND" == "amber" ]]; then
  echo "[hint] AMBER_API_KEY not set — cannot hit AMBER yet."
  echo "       1) cp .env.example .env  and fill AMBER_BASE_URL + AMBER_API_KEY"
  echo "       2) export AMBER_DATA_DIR=data/sample_minimal   # or your corpus"
  echo "       3) bash scripts/reproduce.sh"
  echo
  echo "To only recompute the published local_sim reference (needs upstream key):"
  echo "  export AMBER_BENCH_BACKEND=local_sim"
  echo "  export UPSTREAM_API_KEY=...   # or DEEPSEEK_API_KEY"
  echo "  # full fair_r2 re-run = 100 tasks × 3 arms × 3 = 900 calls"
  echo "  python3 scripts/run_bench.py --backend local_sim --data-dir reference/fair_r2"
  exit 0
fi

echo "[ok] credentials present for backend=$BACKEND"
echo "Full re-run example:"
echo "  python3 scripts/run_bench.py --backend $BACKEND --data-dir $DATA_DIR"
echo "  python3 scripts/summarize.py --data-dir $DATA_DIR"
echo
echo "fair_r2 full size ≈ 900 API calls; sample_minimal is a handful."
