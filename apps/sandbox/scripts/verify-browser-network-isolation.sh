#!/usr/bin/env bash
set -Eeuo pipefail

# Run from the deployment host after docker compose -f apps/sandbox/docker-compose.browser.yml up -d.
# Required: docker, curl, python3, jq. This script never prints credentials.
COMPOSE_FILE="${COMPOSE_FILE:-apps/sandbox/docker-compose.browser.yml}"
BROWSER_SERVICE="${BROWSER_SERVICE:-browser-supervisor}"
PROXY_SERVICE="${PROXY_SERVICE:-egress-proxy}"
ALLOWLIST_TEST_URL="${ALLOWLIST_TEST_URL:-https://example.com/}"
ALLOWLIST_TEST_HOST="${ALLOWLIST_TEST_HOST:-example.com}"
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
if [[ "$browser_network_count" == "1" ]] && grep -q 'browser_private' <<<"$browser_networks"; then pass "browser is attached only to internal browser_private network"; else fail "browser network attachment is not isolated: $browser_networks"; fi
if [[ "$proxy_network_count" == "2" ]] && grep -q 'browser_private' <<<"$proxy_networks" && grep -q 'browser_egress' <<<"$proxy_networks"; then pass "proxy is the only service bridging private and egress networks"; else fail "proxy network topology unexpected: $proxy_networks"; fi

internal="$(docker network inspect "$(docker compose -f "$COMPOSE_FILE" config --format json | jq -r '.networks.browser_private.name // "')" 2>/dev/null | jq -r '.[0].Internal' || true)"
if [[ "$internal" == "true" ]]; then pass "browser_private network has Docker Internal=true"; else fail "browser_private network is not internal"; fi

# A browser-container connection to public IPv4/IPv6 must fail without proxy.
if docker exec "$browser_id" python -c 'import socket; s=socket.create_connection(("1.1.1.1",443),3); s.close()' >/dev/null 2>&1; then fail "direct IPv4 egress succeeded"; else pass "direct IPv4 egress is blocked"; fi
if docker exec "$browser_id" python -c 'import socket; s=socket.socket(socket.AF_INET6); s.settimeout(3); s.connect(("2606:4700:4700::1111",443)); s.close()' >/dev/null 2>&1; then fail "direct IPv6 egress succeeded"; else pass "direct IPv6 egress is blocked"; fi

# Browser -> proxy -> public allowlisted destination must succeed.
proxy_token_present="$(docker exec "$proxy_id" sh -lc 'test -n "$MOREAI_BROWSER_PROXY_TOKEN" && echo yes || echo no')"
[[ "$proxy_token_present" == "yes" ]] || { fail "proxy token is not configured"; }
if docker exec "$browser_id" sh -lc 'command -v curl >/dev/null 2>&1'; then
  if docker exec "$browser_id" sh -lc 'curl --fail --silent --show-error --max-time 15 --proxy "$MOREAI_BROWSER_PROXY_URL" --proxy-user "moreai:$MOREAI_BROWSER_PROXY_TOKEN" "$1" >/dev/null' sh "$ALLOWLIST_TEST_URL" 2>/dev/null; then pass "allowlisted HTTPS egress works through proxy"; else fail "allowlisted HTTPS proxy request failed"; fi
else
  fail "curl is unavailable in browser image; cannot verify proxy success"
fi

# Proxy must reject loopback, link-local metadata and non-allowlisted hosts.
for target in "https://$PRIVATE_TEST_IP/" "https://$METADATA_TEST_IP/" "https://not-allowlisted.invalid/"; do
  if docker exec "$browser_id" sh -lc 'curl --silent --max-time 8 --proxy "$MOREAI_BROWSER_PROXY_URL" --proxy-user "moreai:$MOREAI_BROWSER_PROXY_TOKEN" "$1" >/dev/null 2>&1' sh "$target"; then fail "proxy accepted forbidden target $target"; else pass "proxy rejected forbidden target $target"; fi
done

# Confirm browser container has no host-network mode or privileged setting.
host_mode="$(docker inspect "$browser_id" | jq -r '.[0].HostConfig.NetworkMode')"
privileged="$(docker inspect "$browser_id" | jq -r '.[0].HostConfig.Privileged')"
[[ "$host_mode" != "host" ]] && [[ "$privileged" == "false" ]] && pass "browser is not host-networked or privileged" || fail "browser container has unsafe host/privileged mode"

if [[ "$FAIL" -ne 0 ]]; then
  echo "BROWSER NETWORK ACCEPTANCE: FAILED"
  exit 1
fi
echo "BROWSER NETWORK ACCEPTANCE: PASSED"
