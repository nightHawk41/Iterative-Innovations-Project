#!/usr/bin/env bash
# =============================================================================
# run_demo_tests.sh
# Sprint 3 Backend Demo — Test & Verification Runner
#
# Must be run from the backend/ directory with the venv active:
#   source ../.venv/bin/activate
#   bash run_demo_tests.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

pass()   { echo -e "${GREEN}${BOLD}$*${RESET}"; }
fail()   { echo -e "${RED}${BOLD}$*${RESET}"; }
header() {
    echo ""
    echo -e "${CYAN}${BOLD}================================================================${RESET}"
    echo -e "${CYAN}${BOLD}  $*${RESET}"
    echo -e "${CYAN}${BOLD}================================================================${RESET}"
    echo ""
}

FAILURES=0

run_suite() {
    local label="$1"
    local cmd="$2"
    header "$label"
    if eval "$cmd"; then
        echo ""
        pass "  ✅  $label -- PASSED"
    else
        echo ""
        fail "  ❌  $label -- FAILED"
        FAILURES=$((FAILURES + 1))
    fi
}

echo ""
echo -e "${BOLD}================================================================${RESET}"
echo -e "${BOLD}  UMBC Vending Inventory System -- Sprint 3 Backend Demo${RESET}"
echo -e "${BOLD}  Running all test and verification suites...${RESET}"
echo -e "${BOLD}================================================================${RESET}"

run_suite \
    "SUITE 1 of 6 -- Unit Tests: ItemSlot Model" \
    "python -m pytest app/tests/test_item_slot.py --tb=short -v"

run_suite \
    "SUITE 2 of 6 -- Unit Tests: CBORD Transaction Builder" \
    "python -m pytest app/tests/test_cbord_transaction_builder.py --tb=short -v"

run_suite \
    "SUITE 3 of 6 -- Unit Tests: Mapping Service" \
    "python -m pytest app/tests/test_mapping_service.py --tb=short -v"

run_suite \
    "SUITE 4 of 6 -- API & Sales Report Tests (Sprint 3)" \
    "python -m pytest app/tests/test_api.py --tb=short -v"

run_suite \
    "SUITE 5 of 6 -- D-1: SQLAlchemy Schema & FK Verification" \
    "python -m app.tests.verify_schema"

run_suite \
    "SUITE 6 of 6 -- D-2: Pipeline Integration Tests" \
    "python -m app.tests.test_pipeline_integration"

echo ""
echo -e "${BOLD}================================================================${RESET}"
if [ "$FAILURES" -eq 0 ]; then
    pass "  ✅  ALL SUITES PASSED -- Sprint 3 Backend Complete"
else
    fail "  ❌  $FAILURES SUITE(S) FAILED"
fi
echo -e "${BOLD}================================================================${RESET}"
echo ""

exit "$FAILURES"