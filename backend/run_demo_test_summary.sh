#!/usr/bin/env bash

# =============================================================================
# run_demo_test_summary.sh
# Sprint 3 Backend Demo — Summary Test Runner
#
# Runs the same demo suites with compact reporting suitable for screenshots.
# Must be run from the backend/ directory, or from anywhere with this script.
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -n "${PYTHON_BIN:-}" ]]; then
    PYTHON_CMD="$PYTHON_BIN"
elif [[ -x "$SCRIPT_DIR/../.venv/bin/python" ]]; then
    PYTHON_CMD="$SCRIPT_DIR/../.venv/bin/python"
else
    PYTHON_CMD="python"
fi

pass()   { echo -e "${GREEN}${BOLD}$*${RESET}"; }
fail()   { echo -e "${RED}${BOLD}$*${RESET}"; }
header() {
    echo ""
    echo -e "${CYAN}${BOLD}================================================================${RESET}"
    echo -e "${CYAN}${BOLD}  $*${RESET}"
    echo -e "${CYAN}${BOLD}================================================================${RESET}"
    echo ""
}

summary_line_from_pytest() {
    local output="$1"
    local summary

    summary=$(printf '%s\n' "$output" | grep -E '[0-9]+ .* in [0-9.]+s$' | tail -n 1 || true)
    if [[ -z "$summary" ]]; then
        summary=$(printf '%s\n' "$output" | awk 'NF { line=$0 } END { print line }')
    fi

    printf '%s\n' "$summary"
}

failure_lines_from_pytest() {
    local output="$1"

    printf '%s\n' "$output" | grep '^FAILED ' | head -n 5 || true
}

schema_summary_line() {
    local output="$1"
    local checks

    checks=$(printf '%s\n' "$output" | grep -c '^✔' || true)
    if printf '%s\n' "$output" | grep -q 'ALL D-1 CHECKS PASSED'; then
        printf '%s\n' "$checks schema checks passed"
    else
        printf '%s\n' "Schema verification did not report success"
    fi
}

schema_failure_lines() {
    local output="$1"

    printf '%s\n' "$output" | tail -n 10
}

run_pytest_suite() {
    local label="$1"
    local target="$2"
    local output
    local summary
    local failures

    header "$label"
    if output="$($PYTHON_CMD -m pytest "$target" --tb=short -q 2>&1)"; then
        summary=$(summary_line_from_pytest "$output")
        pass "  PASS  $summary"
    else
        summary=$(summary_line_from_pytest "$output")
        fail "  FAIL  $summary"
        failures=$(failure_lines_from_pytest "$output")
        if [[ -n "$failures" ]]; then
            printf '%s\n' "$failures"
        fi
        return 1
    fi
}

run_schema_suite() {
    local label="$1"
    local output
    local summary

    header "$label"
    if output="$($PYTHON_CMD -m app.tests.verify_schema 2>&1)"; then
        summary=$(schema_summary_line "$output")
        pass "  PASS  $summary"
    else
        summary=$(schema_summary_line "$output")
        fail "  FAIL  $summary"
        schema_failure_lines "$output"
        return 1
    fi
}

FAILURES=0

echo ""
echo -e "${BOLD}================================================================${RESET}"
echo -e "${BOLD}  UMBC Vending Inventory System -- Sprint 3 Summary Demo${RESET}"
echo -e "${BOLD}  Running compact backend test summaries...${RESET}"
echo -e "${BOLD}================================================================${RESET}"

run_pytest_suite "SUITE 1 of 6 -- Unit Tests: ItemSlot Model" "app/tests/test_item_slot.py" || FAILURES=$((FAILURES + 1))
run_pytest_suite "SUITE 2 of 6 -- Unit Tests: CBORD Transaction Builder" "app/tests/test_cbord_transaction_builder.py" || FAILURES=$((FAILURES + 1))
run_pytest_suite "SUITE 3 of 6 -- Unit Tests: Mapping Service" "app/tests/test_mapping_service.py" || FAILURES=$((FAILURES + 1))
run_pytest_suite "SUITE 4 of 6 -- API & Sales Report Tests (Sprint 3)" "app/tests/test_api.py" || FAILURES=$((FAILURES + 1))
run_schema_suite "SUITE 5 of 6 -- D-1: SQLAlchemy Schema & FK Verification" || FAILURES=$((FAILURES + 1))
run_pytest_suite "SUITE 6 of 6 -- D-2: Pipeline Integration Tests" "app/tests/test_pipeline_integration.py" || FAILURES=$((FAILURES + 1))

echo ""
echo -e "${BOLD}================================================================${RESET}"
if [[ "$FAILURES" -eq 0 ]]; then
    pass "  PASS  All 6 demo suites completed successfully"
else
    fail "  FAIL  $FAILURES suite(s) reported failures"
fi
echo -e "${BOLD}================================================================${RESET}"
echo ""

exit "$FAILURES"