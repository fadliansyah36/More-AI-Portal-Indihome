# Phase 09 — Customer Speedtest Typed API Integration

Date: 2026-11-13
Target branch: `main`
Source commits:
- `1106499d1f374ca163392e4676fdc7b68e850139` — add typed FastAPI client methods for ping, download and upload.
- `bddf8142e15d2b3122ac9d95282bceb2385be3f4` — route the existing Speedtest screen through those methods.

## Scope

The existing Customer Speedtest screen already used authenticated FastAPI endpoints, but bypassed the typed Customer API surface and called the generic authenticated fetch helper directly. This increment moves those three operations into `customerApi` and keeps the view focused on measurement presentation.

## Contract mapping

- `customerApi.networkSpeedtestPing()` → `GET /api/v1/customer/network/speedtest/ping`
- `customerApi.networkSpeedtestDownload(sizeBytes)` → `GET /api/v1/customer/network/speedtest/download?size_bytes=...`, returning the authenticated raw `Response` for byte measurement.
- `customerApi.networkSpeedtestUpload(payload)` → `POST /api/v1/customer/network/speedtest/upload`, returning typed `received_bytes` and `duration_ms`.

The size bound in the client follows the existing API contract (64 KiB–8 MiB download). Upload continues to use the existing bounded 4 MiB payload and server-side byte acceptance check.

## Files changed

- `lib/api/client.ts`: added typed methods to the existing `customerApi` namespace.
- `components/views/speedtest-view.tsx`: replaced direct generic fetch calls with the typed methods. Existing measurements, copy, state handling and layout are unchanged.

## Architecture and security

The flow remains browser → authenticated Customer API client → FastAPI Customer router. Supabase is used only by the existing Auth token/session helper. No direct browser table, Storage, RPC or Realtime access was added. The FastAPI route retains `customer_principal` authorization.

The screen continues to describe this as device-to-MoreAI-API path measurement, not ISP/ONT/gateway throughput.

## Validation and deployment

Per product-owner instruction, no tests, lint, typecheck, build, browser checks, screenshots, API probes, staging, migrations or deployment were performed. Source-level changes only; runtime is unverified.

## Phase status and next work

Phase 09 remains **IN PROGRESS**. Continue the remaining Customer screen/action audit and close other provider-independent typed API gaps without changing protected UI. Gateway/OTP, media generation, payment settlement, authoritative EduTech catalog/video delivery and support remain blocked pending official provider contracts and secure configuration. Phase 10 is not accepted under the current no-testing instruction; Phase 11 remains blocked.
