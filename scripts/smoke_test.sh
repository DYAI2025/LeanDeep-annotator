#!/usr/bin/env bash
# Smoke test script for post-deploy verification.
# Usage: BASE_URL="https://your-service.up.railway.app" bash scripts/smoke_test.sh
#
# Exits non-zero on any failure.

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8420}"
PASS=0
FAIL=0

check() {
  local description="$1"
  local expected="$2"
  local actual="$3"

  if echo "$actual" | grep -q "$expected"; then
    echo "✅ PASS: $description"
    PASS=$((PASS + 1))
  else
    echo "❌ FAIL: $description"
    echo "   Expected: $expected"
    echo "   Got: ${actual:0:200}"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== LeanDeep Smoke Tests ==="
echo "Target: $BASE_URL"
echo ""

# 1. Health Check
echo "--- Health Check ---"
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/v1/health")
check "GET /v1/health returns 200" "200" "$HEALTH"

HEALTH_BODY=$(curl -s "$BASE_URL/v1/health")
check "Health response contains status:ok" '"ok"' "$HEALTH_BODY"

# 2. Engine Config
echo ""
echo "--- Engine Config ---"
CONFIG=$(curl -s "$BASE_URL/v1/engine/config")
CONFIG_MARKERS=$(echo "$CONFIG" | grep -o '"total_markers":[0-9]*' | cut -d: -f2)
if [ -n "$CONFIG_MARKERS" ] && [ "$CONFIG_MARKERS" -gt 0 ]; then
  echo "✅ PASS: Engine config has total_markers > 0 ($CONFIG_MARKERS)"
  PASS=$((PASS + 1))
else
  echo "❌ FAIL: Engine config has no markers (got: $CONFIG_MARKERS)"
  FAIL=$((FAIL + 1))
fi

# 3. Analyze Endpoint
echo ""
echo "--- Analyze Endpoint ---"
ANALYZE=$(curl -s -X POST "$BASE_URL/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test message.", "language": "en"}')
check "POST /v1/analyze returns markers key" '"markers"' "$ANALYZE"

# 4. Frontend (if deployed)
echo ""
echo "--- Frontend ---"
FRONTEND_HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$FRONTEND_HTTP" = "200" ]; then
  FRONTEND_BODY=$(curl -s "$BASE_URL/")
  check "GET / returns HTML" "<!doctype html>\|<html" "$FRONTEND_BODY"
else
  echo "⚠️  SKIP: Frontend not served (HTTP $FRONTEND_HTTP) — may be dev mode"
fi

# 5. Markers Endpoint
echo ""
echo "--- Markers Endpoint ---"
MARKERS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/v1/markers")
check "GET /v1/markers returns 200" "200" "$MARKERS"

# Summary
echo ""
echo "=== Summary ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Smoke tests FAILED ($FAIL failures)"
  exit 1
else
  echo "✅ All smoke tests PASSED"
  exit 0
fi
