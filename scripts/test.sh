#!/bin/sh
# Menjalankan seluruh tes: ./scripts/test.sh [api|ui]
set -e
cd "$(dirname "$0")/.."
PY=${PY:-python3}
case "${1:-all}" in
  api) $PY -m pytest tests -q ;;
  ui) (cd tests/ui && node run.js) ;;
  *) $PY -m pytest tests -q; (cd tests/ui && node run.js) ;;
esac
