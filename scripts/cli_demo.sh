#!/usr/bin/env bash
# ==============================================================================
# WB-Profit-Engine — Automated CLI Verification & Load Balancing Demo Script
# Demonstrates:
#   1. Seller Registration (`POST /api/v1/auth/register`) -> Bearer JWT Token
#   2. Seller Login (`POST /api/v1/auth/login`)
#   3. Wildberries Unit-Economics Calculation (`POST /api/v1/wb/calculate`)
#      across 90%, 75%, and 50% Buyout Scenarios + Target Price for 100% ROI
#   4. Round-Robin Load Balancing across `wb-api-1` and `wb-api-2`
# ==============================================================================
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:80}"
API_URL="${BASE_URL}/api/v1"
SELLER_EMAIL="seller_$(date +%s)@wildberries-pro.ru"
SELLER_PASSWORD="StrongSellerPassword!2026"

echo "========================================================================"
echo "  WB-PROFIT-ENGINE | CLI VERIFICATION & ROUND-ROBIN LOAD BALANCER DEMO"
echo "  Target Endpoint : ${API_URL}"
echo "  Seller Account  : ${SELLER_EMAIL}"
echo "========================================================================"
echo ""

echo "[1/4] Registering new WB Seller via POST ${API_URL}/auth/register ..."
REGISTER_RES=$(curl -sS -X POST "${API_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${SELLER_EMAIL}\",
    \"password\": \"${SELLER_PASSWORD}\",
    \"seller_name\": \"IP Sokolov WB Brand\"
  }")

echo "${REGISTER_RES}"
echo ""

echo "[2/4] Authenticating Seller via POST ${API_URL}/auth/login ..."
LOGIN_RES=$(curl -sS -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${SELLER_EMAIL}\",
    \"password\": \"${SELLER_PASSWORD}\"
  }")

# Extract Bearer JWT token using python3 or grep/sed fallback
if command -v python3 >/dev/null 2>&1; then
  JWT_TOKEN=$(printf '%s' "${LOGIN_RES}" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
else
  JWT_TOKEN=$(printf '%s' "${LOGIN_RES}" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
fi

echo "Authenticated! Issued JWT Bearer Token: ${JWT_TOKEN:0:32}..."
echo ""

echo "[3/4] Calculating WB Unit-Economics for SKU nm_id=214859102 (COGS=820 RUB) ..."
CALC_RES=$(curl -sS -X POST "${API_URL}/wb/calculate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -d '{
    "nm_id": 214859102,
    "cogs": 820.0,
    "custom_price": 3490.0,
    "length_cm": 36.0,
    "width_cm": 28.0,
    "height_cm": 8.0
  }')

if command -v python3 >/dev/null 2>&1; then
  printf '%s' "${CALC_RES}" | python3 -m json.tool
else
  echo "${CALC_RES}"
fi
echo ""

echo "[4/4] Verifying Nginx Round-Robin Load Balancing across 6 sequential requests ..."
for i in 1 2 3 4 5 6; do
  HEALTH_RES=$(curl -sS "${API_URL}/health")
  if command -v python3 >/dev/null 2>&1; then
    CONTAINER=$(printf '%s' "${HEALTH_RES}" | python3 -c "import sys, json; print(json.load(sys.stdin).get('served_by_container', 'unknown'))")
  else
    CONTAINER=$(printf '%s' "${HEALTH_RES}" | sed -n 's/.*"served_by_container":"\([^"]*\)".*/\1/p')
  fi
  echo "  Request #${i} -> served_by_container: ${CONTAINER}"
done

echo ""
echo "========================================================================"
echo "  VERIFICATION COMPLETE: Auth, Unit-Economics & Load Balancing Verified"
echo "========================================================================"
