#!/usr/bin/env bash
set -euo pipefail

QUERY="${1:-교통사고}"
PAGES="${2:-1}"
DISPLAY="${3:-10}"
SLEEP_SECONDS="${4:-0.2}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"

if [ ! -f "${BACKEND_DIR}/.env" ]; then
  echo "backend/.env 파일이 없습니다. DATABASE_URL과 LAW_OPEN_API_OC를 먼저 설정해 주세요." >&2
  exit 1
fi

cd "${BACKEND_DIR}"

PYTHON_BIN="python3"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

"${PYTHON_BIN}" -m pipelines.collector.collect_precedents \
  --query "${QUERY}" \
  --pages "${PAGES}" \
  --display "${DISPLAY}" \
  --sleep "${SLEEP_SECONDS}"
