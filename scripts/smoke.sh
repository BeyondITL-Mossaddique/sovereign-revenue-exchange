#!/usr/bin/env bash
# Smoke tests for the reference services.
#
# Default: hits the local docker-compose stack on its host-exposed ports.
# OpenChoreo: pass the gateway URL as $GATEWAY_URL to hit the project's
# OpenChoreo-managed endpoint (host ports 19080/19443 in the quick-start).
#
# Examples:
#   scripts/smoke.sh                                   # compose, ports 18000+
#   GATEWAY_URL=https://exchange.dev.localhost:19443 scripts/smoke.sh
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:18000}"
REGISTRY_URL="${REGISTRY_URL:-http://127.0.0.1:18001}"
RETURNS_URL="${RETURNS_URL:-http://127.0.0.1:18002}"
AGENCY="${REQUESTING_AGENCY:-customs}"
CURL_OPTS=(--fail-with-body --silent --show-error --max-time 10)

pass() { printf "  \033[32m✓\033[0m %s\n" "$1"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$1"; exit 1; }
say()  { printf "\n\033[1m%s\033[0m\n" "$1"; }

require_jq() {
  if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required to validate JSON responses. Install: brew install jq"
    exit 2
  fi
}

require_jq

say "1. healthz checks"
for url in "$GATEWAY_URL" "$REGISTRY_URL" "$RETURNS_URL"; do
  body=$(curl "${CURL_OPTS[@]}" "$url/healthz")
  status=$(echo "$body" | jq -r .status)
  service=$(echo "$body" | jq -r .service)
  [[ "$status" == "ok" ]] || fail "$url/healthz status was $status"
  pass "$service @ $url"
done

say "2. taxpayer-registry direct lookup"
body=$(curl "${CURL_OPTS[@]}" "$REGISTRY_URL/taxpayers/900000001")
tin=$(echo "$body" | jq -r .tin)
[[ "$tin" == "900000001" ]] || fail "expected tin 900000001, got $tin"
pass "GET /taxpayers/900000001 -> $tin"

say "3. taxpayer-registry NID lookup"
body=$(curl "${CURL_OPTS[@]}" "$REGISTRY_URL/taxpayers?nid=1000000003")
count=$(echo "$body" | jq 'length')
[[ "$count" == "1" ]] || fail "expected 1 row for nid, got $count"
pass "GET /taxpayers?nid=1000000003 -> $count row"

say "4. returns submission + retrieval"
sub_id=$(curl "${CURL_OPTS[@]}" -X POST "$RETURNS_URL/returns" \
  -H 'content-type: application/json' \
  -d '{
        "tin": "900000005",
        "period": "2023",
        "figures": {
          "gross_income": "450000.00",
          "deductions": "25000.00",
          "tax_payable": "42500.00",
          "currency": "BDT"
        }
      }' | jq -r .id)
[[ -n "$sub_id" && "$sub_id" != "null" ]] || fail "no return id returned"
pass "POST /returns -> $sub_id"
got_id=$(curl "${CURL_OPTS[@]}" "$RETURNS_URL/returns/$sub_id" | jq -r .id)
[[ "$got_id" == "$sub_id" ]] || fail "GET /returns/$sub_id mismatched"
pass "GET /returns/$sub_id"

say "5. exchange-gateway composed profile"
body=$(curl "${CURL_OPTS[@]}" -H "X-Requesting-Agency: $AGENCY" \
       "$GATEWAY_URL/exchange/taxpayer-profile/900000001")
tin=$(echo "$body" | jq -r .taxpayer.tin)
agency=$(echo "$body" | jq -r .served_to_agency)
returns_n=$(echo "$body" | jq '.returns | length')
[[ "$tin" == "900000001" ]] || fail "expected tin 900000001, got $tin"
[[ "$agency" == "$AGENCY" ]] || fail "expected agency $AGENCY, got $agency"
[[ "$returns_n" -ge 1 ]] || fail "expected >=1 returns, got $returns_n"
pass "GET /exchange/taxpayer-profile/900000001 -> tin=$tin agency=$agency returns=$returns_n"

say "6. exchange-gateway verify (match)"
body=$(curl "${CURL_OPTS[@]}" -X POST -H "X-Requesting-Agency: $AGENCY" \
       -H 'content-type: application/json' \
       "$GATEWAY_URL/exchange/verify" \
       -d '{"tin":"900000001","period":"2024","claimed_status":"accepted"}')
verified=$(echo "$body" | jq -r .verified)
[[ "$verified" == "true" ]] || fail "expected verified=true, got $verified"
pass "POST /exchange/verify (accepted) -> verified=true"

say "7. exchange-gateway verify (mismatch)"
body=$(curl "${CURL_OPTS[@]}" -X POST -H "X-Requesting-Agency: $AGENCY" \
       -H 'content-type: application/json' \
       "$GATEWAY_URL/exchange/verify" \
       -d '{"tin":"900000001","period":"2024","claimed_status":"rejected"}')
verified=$(echo "$body" | jq -r .verified)
actual=$(echo "$body" | jq -r .actual_status)
[[ "$verified" == "false" ]] || fail "expected verified=false, got $verified"
[[ "$actual" == "accepted" ]] || fail "expected actual=accepted, got $actual"
pass "POST /exchange/verify (rejected claim vs accepted actual) -> verified=false"

echo
echo "All smoke tests passed."
