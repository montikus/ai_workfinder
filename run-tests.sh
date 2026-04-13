#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/job-agent-frontend"
BACKEND_REPORTS_DIR="$BACKEND_DIR/reports/tests"
FRONTEND_RUN_ID="$(date +%Y%m%d-%H%M%S)"
FRONTEND_RUN_DIR="$FRONTEND_DIR/reports/test-runs/$FRONTEND_RUN_ID"
FRONTEND_TEST_REPORTS_DIR="$FRONTEND_RUN_DIR/tests"
FRONTEND_COVERAGE_REPORTS_DIR="$FRONTEND_RUN_DIR/coverage"
FRONTEND_COVERAGE_TMP_DIR="$FRONTEND_DIR/coverage"

mkdir -p "$BACKEND_REPORTS_DIR" "$FRONTEND_TEST_REPORTS_DIR" "$FRONTEND_COVERAGE_REPORTS_DIR"

overall_status=0
last_step_status=0
declare -a failed_steps=()

run_logged_step() {
  local label="$1"
  local workdir="$2"
  local logfile="$3"
  shift 3

  mkdir -p "$(dirname "$logfile")"

  echo
  echo "==> $label"
  (
    cd "$workdir" &&
    "$@"
  ) 2>&1 | tee "$logfile"

  local step_status=${PIPESTATUS[0]}
  last_step_status=$step_status

  if (( step_status != 0 )); then
    overall_status=1
    failed_steps+=("$label (exit code: $step_status)")
  fi

  return 0
}

copy_frontend_coverage() {
  local label="$1"
  local destination="$2"

  echo
  echo "==> Saving frontend coverage snapshot: $label"

  if (( last_step_status != 0 )); then
    echo "Skipping coverage snapshot because the previous coverage command failed."
    return 0
  fi

  if [[ ! -d "$FRONTEND_COVERAGE_TMP_DIR" ]]; then
    echo "Coverage directory not found: $FRONTEND_COVERAGE_TMP_DIR"
    overall_status=1
    failed_steps+=("$label coverage snapshot missing")
    return 0
  fi

  mkdir -p "$destination"
  cp -R "$FRONTEND_COVERAGE_TMP_DIR"/. "$destination"/
}

print_reports() {
  local title="$1"
  shift

  echo
  echo "$title"
  for path in "$@"; do
    if [[ -e "$path" ]]; then
      echo " - $path"
    fi
  done
}

echo "Repository root: $REPO_ROOT"
echo "Frontend report run id: $FRONTEND_RUN_ID"

if [[ -f "$BACKEND_DIR/venv/bin/activate" ]]; then
  echo "Backend virtualenv detected: $BACKEND_DIR/venv/bin/activate"
  echo "The backend commands below still follow TESTING.md from the repository root."
fi

run_logged_step \
  "Backend test dependencies" \
  "$REPO_ROOT" \
  "$BACKEND_REPORTS_DIR/backend-test-deps-install.txt" \
  python -m pip install -r backend/requirements-test.txt

run_logged_step \
  "Backend pytest with terminal coverage" \
  "$REPO_ROOT" \
  "$BACKEND_REPORTS_DIR/backend-pytest-term.txt" \
  pytest backend/tests --cov=app --cov-report=term-missing

run_logged_step \
  "Backend HTML/XML report generation" \
  "$REPO_ROOT" \
  "$BACKEND_REPORTS_DIR/backend-report-generation.txt" \
  python backend/scripts/generate_backend_test_reports.py

run_logged_step \
  "Frontend npm install" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-npm-install.txt" \
  npm install

run_logged_step \
  "Frontend Node/API tests" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test.txt" \
  npm run test

run_logged_step \
  "Frontend Node/API coverage" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-coverage.txt" \
  npm run test:coverage
copy_frontend_coverage "frontend api" "$FRONTEND_COVERAGE_REPORTS_DIR/api"

run_logged_step \
  "Frontend DOM tests" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-dom.txt" \
  npm run test:dom

run_logged_step \
  "Frontend DOM coverage" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-dom-coverage.txt" \
  npm run test:dom:coverage
copy_frontend_coverage "frontend dom" "$FRONTEND_COVERAGE_REPORTS_DIR/dom"

run_logged_step \
  "Frontend production build" \
  "$FRONTEND_DIR" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-build.txt" \
  npm run build

print_reports \
  "Backend reports:" \
  "$BACKEND_REPORTS_DIR/backend-pytest-term.txt" \
  "$BACKEND_REPORTS_DIR/backend-report-generation.txt" \
  "$BACKEND_REPORTS_DIR/backend-tests.html" \
  "$BACKEND_REPORTS_DIR/backend-tests.xml" \
  "$BACKEND_REPORTS_DIR/backend-tests.txt" \
  "$BACKEND_DIR/reports/coverage/index.html"

print_reports \
  "Frontend reports:" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-npm-install.txt" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test.txt" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-coverage.txt" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-dom.txt" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-test-dom-coverage.txt" \
  "$FRONTEND_TEST_REPORTS_DIR/frontend-build.txt" \
  "$FRONTEND_COVERAGE_REPORTS_DIR/api/index.html" \
  "$FRONTEND_COVERAGE_REPORTS_DIR/api/coverage-summary.json" \
  "$FRONTEND_COVERAGE_REPORTS_DIR/dom/index.html" \
  "$FRONTEND_COVERAGE_REPORTS_DIR/dom/coverage-summary.json"

if (( ${#failed_steps[@]} > 0 )); then
  echo
  echo "Failed steps:"
  for step in "${failed_steps[@]}"; do
    echo " - $step"
  done
fi

exit "$overall_status"
