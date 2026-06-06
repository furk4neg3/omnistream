#!/usr/bin/env bash
set -euo pipefail

run_service_tests() {
  local service_path="$1"
  shift

  echo "==> ${service_path}"
  PYTHONPATH="${service_path}" python -m pytest -q "$@"
}

run_service_tests "services/indexer" "services/indexer/tests"
run_service_tests "services/producer" "services/producer/tests"
run_service_tests "services/processing-agent" "services/processing-agent/tests"
run_service_tests "services/query-api" "services/query-api/tests" "services/query-api/app/test_ingestion.py"
