#!/bin/bash
# E2E Test Runner - Cycle 01
# Usage: ./tests/e2e/cycle-01/run-all.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
EVIDENCE_DIR="$SCRIPT_DIR/evidence"

echo "========================================"
echo "E2E Tests - Cycle 01 (MVP)"
echo "========================================"
echo "Date: $(date)"
echo "Project: $PROJECT_ROOT"
echo ""

# Create evidence directory if not exists
mkdir -p "$EVIDENCE_DIR"

# Run tests and capture output
LOG_FILE="$EVIDENCE_DIR/last_run.log"

echo "Running E2E tests..."
echo ""

cd "$PROJECT_ROOT"
PYTHONPATH=src python3 -m pytest tests/e2e/cycle-01/ -v --tb=short 2>&1 | tee "$LOG_FILE"

# Check result
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ E2E Tests PASSED"
    echo "========================================"
    echo "Evidence saved to: $LOG_FILE"
    exit 0
else
    echo ""
    echo "========================================"
    echo "❌ E2E Tests FAILED"
    echo "========================================"
    echo "Check log: $LOG_FILE"
    exit 1
fi
