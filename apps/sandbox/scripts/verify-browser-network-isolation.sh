#!/usr/bin/env bash
set -Eeuo pipefail

# Run from the repository root after:
# docker compose -f apps/sandbox/compose.browser.yml up -d
# Required: docker, curl, python3, jq. This script never prints credentials.
COMPOSE_FILE="${COMPOSE_FILE:-apps/sandbox/compose.browser.yml}"
BROWSER_SERVICE="${BROWSER_SERVICE:-browser-supervisor}"
PROXY_SERVICE="${PROXY_SERVICE:-browser-egress-proxy}"
ALLOWLIST_TEST_URL="${ALLOWLIST_TEST_URL:-https://example.com/}"
PRIVATE_TEST_IP="${PRIVATE_TEST_IP:-127.0.0.1}"
METADATA_TEST_IP="${METADATA_TEST_IP:-169.254.169.254}"
FAIL=0

pass(){ printf 'PASS %s\n' "$1"; }
fail(){ printf 'FAIL %s\n' "$1"; FAIL=1; }
need(){ command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 2; }; }
need docker; need curl; need python3; need jq

browser_id="$(docker compose -f "$COMPOSE_FILE" ps -q "$BROWSER_SERVICE")"
proxy_id="$(docker compose -f "$COMPOSE_FILE" ps -q "$PROXY_SERVICE")"
[[ -n "$browser_id" && -n "$proxy_id" ]] || { echo "Both browser and proxy containers must be running" >&2; exit 2; }

browser_networks="$(docker inspect "$browser_id" | jq -r '.[0].NetworkSettings.Networks | keys[]' | sort)"
proxy_networks="$(docker inspect "$proxy_id" | jq -r '.[0].NetworkSettings.Networks | keys[]' | sort)"
browser_network_count="$(printf '%s\n' "$browser_networks" | wc -l | tr -d ' ')"
proxy_network_count="$(printf '%s\n' "$proxy_networks" | wc -l | tr -d ' ')"
if [[ "$browser_network_count" == "1" ]] && grep -q 'browser_isolated' <<<"$browser_networks"; then pass "browser is attached only to internal browser_isolated network"; else fail "browser network attachment is not isolated: $browser_networks"; fi
if [[ "$proxy_network_count" == "2" ]] && grep -q 'browser_isolated' <<<"$proxy_networks" && grep -q 'browser_egress' <<<"$proxy_networks"; then pass "proxy is the only service bridging isolated and egress networks"; else fail "proxy network topology unexpected: $proxy_networks"; fi

network_name="$(docker compose -f "$COMPOSE_FILE" config --format json | jq -r '.networks.browser_isolated.name // empty')"
[[ -n "$network_name" ]] || network_name="${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}_browser_isolated"
internal="$(docker network inspect "$network_name" 2>/dev/null | jq -r '.[0].Internal' || true)"
if [[ "$internal" == "true" ]]; then pass "browser_isolated network has Docker Internal=true"; else fail "browser_isolated network is not internal"; fi

if docker exec "$browser_id" python -c 'import socket; s=socket.create_connection(("1.1.1.1",443),3); s.close()' >/dev/null 2>&1; then fail "direct IPv4 egress succeeded"; else pass "direct IPv4 egress is blocked"; fi
if docker exec "$browser_id" python -c 'import socket; s=socket.socket(socket.AF_INET6); s.settimeout(3); s.connect(("2606:4700:4700::1111",443)); s.close()' >/dev/null 2>&1; then fail "direct IPv6 egress succeeded"; else pass "direct IPv6 egress is blocked"; fi

proxy_token_present="$(docker exec "$proxy_id" sh -lc 'test -n "$MOREAI_BROWSER_PROXY_TOKEN" && echo yes || echo no')"
[[ "$proxy_token_present" == "yes" ]] || fail "proxy token is not configured"
# Verify the worker-facing supervisor readiness contract over the isolated service network.
ready_json="$(docker exec "$proxy_id" curl --fail --silent --show-error \
  -H "Authorization: Bearer ${MOREAI_BROWSER_SERVICE_TOKEN:?service token required}" \
  http://browser-supervisor:8080/ready)"
if jq -e '.status == "ready" and .egress_enforced == true and .proxy_reachable == true' <<<"$ready_json" >/dev/null; then
  pass "authenticated browser supervisor readiness confirms live proxy"
else
  fail "browser supervisor readiness did not confirm enforced egress"
fi

# Exercise the browser process itself, not just curl through the proxy.
navigate_json="$(docker exec "$proxy_id" curl --fail --silent --show-error \
  -H "Authorization: Bearer $MOREAI_BROWSER_SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/","action":"navigate","run_id":"ci-browser-acceptance","user_id":"ci-browser-acceptance"}' \
  http://browser-supervisor:8080/v1/browser/actions)"
if jq -e '(.status == "navigated") and (.url | startswith("https://example.com"))' <<<"$navigate_json" >/dev/null; then
  pass "Playwright navigation succeeds through the enforced allowlist proxy"
else
  fail "Playwright allowlisted navigation failed"
fi

redirect_code="$(docker exec "$proxy_id" curl --silent --output /dev/null --write-out '%{http_code}' \
  --max-time 30 -H "Authorization: Bearer $MOREAI_BROWSER_SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://httpbin.org/redirect-to?url=https%3A%2F%2Fnot-allowlisted.invalid%2F","action":"navigate","run_id":"ci-browser-redirect","user_id":"ci-browser-acceptance"}' \
  http://browser-supervisor:8080/v1/browser/actions)"
if [[ "$redirect_code" != "200" ]]; then pass "redirect to a non-allowlisted host is denied"; else fail "redirect escaped the browser domain allowlist"; fi

download_code="$(docker exec "$proxy_id" curl --silent --output /dev/null --write-out '%{http_code}' \
  --max-time 30 -H "Authorization: Bearer $MOREAI_BROWSER_SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://httpbin.org/response-headers?Content-Disposition=attachment%3Bfilename%3Dpayload.txt","action":"navigate","run_id":"ci-browser-download","user_id":"ci-browser-acceptance"}' \
  http://browser-supervisor:8080/v1/browser/actions)"
if [[ "$download_code" != "200" ]]; then pass "browser download is denied while scanner-backed download handling is disabled"; else fail "browser download was accepted without scanner approval"; fi

if docker exec "$browser_id" sh -lc 'command -v curl >/dev/null 2>&1'; then
  if docker exec "$browser_id" sh -lc 'curl --fail --silent --show-error --max-time 15 --proxy "$MOREAI_BROWSER_PROXY_URL" --proxy-user "moreai:$MOREAI_BROWSER_PROXY_TOKEN" "$1" >/dev/null' sh "$ALLOWLIST_TEST_URL" 2>/dev/null; then pass "allowlisted HTTPS egress works through proxy"; else fail "allowlisted HTTPS proxy request failed"; fi
else
  fail "curl is unavailable in browser image; cannot verify proxy success"
fi

docker exec "$proxy_id" python - <<'PY'
import asyncio, socket
from app.browser_security import BrowserPolicy, BrowserPolicyError, BrowserRequestGuard

answers = ["93.184.216.34", "127.0.0.1"]
async def resolver(host, port, socktype):
    address = answers.pop(0)
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port))]

async def verify():
    guard = BrowserRequestGuard(BrowserPolicy(("trusted.example",)), resolver=resolver)
    await guard.validate_request("https://trusted.example/first")
    try:
        await guard.validate_request("https://trusted.example/second")
    except BrowserPolicyError as exc:
        if str(exc) not in {"browser_private_or_reserved_address_denied", "browser_dns_rebinding_detected"}:
            raise
        return
    raise SystemExit("DNS rebinding was not rejected")

asyncio.run(verify())
PY
pass "DNS rebinding from a public address to loopback is rejected by the proxy guard"

for target in "https://$PRIVATE_TEST_IP/" "https://$METADATA_TEST_IP/" "https://not-allowlisted.invalid/"; do
  if docker exec "$browser_id" sh -lc 'curl --silent --max-time 8 --proxy "$MOREAI_BROWSER_PROXY_URL" --proxy-user "moreai:$MOREAI_BROWSER_PROXY_TOKEN" "$1" >/dev/null 2>&1' sh "$target"; then fail "proxy accepted forbidden target $target"; else pass "proxy rejected forbidden target $target"; fi
done

host_mode="$(docker inspect "$browser_id" | jq -r '.[0].HostConfig.NetworkMode')"
privileged="$(docker inspect "$browser_id" | jq -r '.[0].HostConfig.Privileged')"
[[ "$host_mode" != "host" && "$privileged" == "false" ]] && pass "browser is not host-networked or privileged" || fail "browser container has unsafe host/privileged mode"

if [[ "$FAIL" -ne 0 ]]; then
  echo "BROWSER NETWORK ACCEPTANCE: FAILED"
  exit 1
fi
echo "BROWSER NETWORK ACCEPTANCE: PASSED"
