from contextlib import asynccontextmanager
import logging
from uuid import UUID, uuid4
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger("moreai.api")

from app.config import Settings
from app.dependencies import current_user
from app.routers import admin, agent_runs, artifacts, catalog, conversations, customer, notifications, partner, tool_approvals, workspaces, learning, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.settings = Settings.from_env()
    async with httpx.AsyncClient() as client:
        app.state.http = client
        yield


app = FastAPI(
    title="MoreAI API",
    version="0.3.0",
    description="Trusted MoreAI business API. Browser Supabase access is Auth-only; application data and agent execution are mediated here.",
    lifespan=lifespan,
)

_cors_origins = [origin.strip().rstrip('/') for origin in os.getenv('MOREAI_CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Authorization', 'Content-Type', 'Accept', 'Idempotency-Key', 'X-Correlation-ID', 'If-Match', 'X-Workspace-Path', 'X-Filename', 'X-Artifact-Purpose', 'X-Conversation-Id', 'X-Agent-Run-Id'],
        expose_headers=['X-Correlation-ID', 'X-Next-Cursor', 'X-Pagination-Mode'],
        max_age=600,
    )

app.include_router(conversations.router)
app.include_router(customer.router)
app.include_router(workspaces.router)
app.include_router(partner.router)
app.include_router(admin.router)
app.include_router(tool_approvals.router)
app.include_router(agent_runs.router)
app.include_router(catalog.router)
app.include_router(artifacts.router)
app.include_router(notifications.router)
app.include_router(learning.router)
app.include_router(knowledge.router)


class ProfileRecordResponse(BaseModel):
    id: UUID
    display_name: str | None = None
    avatar_path: str | None = None
    locale: str | None = None
    timezone: str | None = None


class ProfileIdentityResponse(BaseModel):
    id: UUID
    email: str | None = None
    display_name: str | None = None


class MyProfileResponse(BaseModel):
    user: ProfileIdentityResponse
    profile: ProfileRecordResponse | None = None


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    avatar_path: str | None = Field(default=None, max_length=512)
    locale: str | None = Field(default=None, pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$", max_length=10)
    timezone: str | None = Field(default=None, max_length=64)

    def changes(self) -> dict[str, str | None]:
        return self.model_dump(exclude_unset=True)


@app.middleware("http")
async def correlation_id(request: Request, call_next):
    supplied = request.headers.get("x-correlation-id", "").strip()
    valid = supplied[:128] if supplied and all(c.isalnum() or c in "-_." for c in supplied) else str(uuid4())
    request.state.correlation_id = valid
    # Bearer-token APIs do not rely on ambient browser cookies. Reject cross-site
    # state-changing browser requests as defense in depth; CORS remains a separate gate.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        fetch_site = request.headers.get("sec-fetch-site", "").lower()
        if origin and origin.rstrip("/") not in _cors_origins:
            return JSONResponse(status_code=403, content={"error": {"code": "untrusted_origin", "message": "Request origin is not allowed", "correlation_id": valid}})
        if not origin and fetch_site == "cross-site":
            return JSONResponse(status_code=403, content={"error": {"code": "cross_site_request_denied", "message": "Cross-site mutation is not allowed", "correlation_id": valid}})

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = valid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/") else response.headers.get("Cache-Control", "no-cache")
    return response


def _error_response(request: Request, *, status_code: int, code: str, message: str, details: Any = None, headers: dict[str, str] | None = None):
    error = {
        "code": code,
        "message": message,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=headers,
    )


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict):
        code = str(detail.get("code") or "http_error")
        message = str(detail.get("message") or "The request could not be completed")
        details = detail.get("details")
    else:
        code = {
            400: "bad_request", 401: "unauthorized", 403: "forbidden",
            404: "not_found", 409: "conflict", 422: "validation_error",
            429: "rate_limited", 503: "service_unavailable",
        }.get(exc.status_code, "http_error")
        message = str(detail) if isinstance(detail, str) else "The request could not be completed"
        details = None
    return _error_response(
        request, status_code=exc.status_code, code=code,
        message=message, details=details, headers=exc.headers,
    )


@app.exception_handler(httpx.TimeoutException)
async def upstream_timeout_error(request: Request, exc: httpx.TimeoutException):
    logger.warning(
        "Upstream dependency timeout",
        extra={
            "correlation_id": getattr(request.state, "correlation_id", None),
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )
    return _error_response(
        request, status_code=504, code="upstream_timeout",
        message="A required upstream service did not respond in time",
    )


@app.exception_handler(httpx.HTTPError)
async def upstream_transport_error(request: Request, exc: httpx.HTTPError):
    logger.warning(
        "Upstream dependency transport failure",
        extra={
            "correlation_id": getattr(request.state, "correlation_id", None),
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )
    return _error_response(
        request, status_code=503, code="upstream_unavailable",
        message="A required upstream service is temporarily unavailable",
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error(request: Request, exc: RequestValidationError):
    safe_errors = [
        {
            "location": [str(part) for part in item.get("loc", ())],
            "type": str(item.get("type", "invalid")),
            "message": str(item.get("msg", "Invalid value")),
        }
        for item in exc.errors()
    ]
    return _error_response(
        request, status_code=422, code="validation_error",
        message="One or more request fields are invalid",
        details={"fields": safe_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    # Log correlation and classification metadata only. Exception messages and
    # tracebacks may contain prompts, credentials, provider payloads or user data.
    logger.error(
        "Unhandled API exception",
        extra={
            "correlation_id": getattr(request.state, "correlation_id", None),
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )
    return _error_response(
        request, status_code=500, code="internal_error",
        message="An unexpected server error occurred",
    )


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "moreai-api"}


@app.get("/ready", tags=["system"])
async def readiness(request: Request):
    settings = request.app.state.settings
    auth_configured = settings.supabase_auth_ready
    data_configured = settings.supabase_data_ready
    auth_reachable = False
    data_reachable = False

    if auth_configured:
        try:
            response = await request.app.state.http.get(
                f"{settings.supabase_url}/auth/v1/settings",
                headers={"apikey": settings.supabase_anon_key},
                timeout=3.0,
            )
            auth_reachable = response.status_code < 500
        except Exception:
            auth_reachable = False

    if data_configured:
        try:
            response = await request.app.state.http.get(
                f"{settings.supabase_url}/rest/v1/roles",
                params={"select": "id", "limit": "1"},
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {settings.supabase_service_role_key}",
                },
                timeout=3.0,
            )
            data_reachable = response.status_code == 200
        except Exception:
            data_reachable = False

    runtime_enabled = settings.agent_execution_enabled
    ready = auth_configured and data_configured and auth_reachable and data_reachable
    return {
        "status": "ready" if ready else "degraded",
        "dependencies": {
            "supabase_auth": auth_configured,
            "supabase_data": data_configured,
            "supabase_auth_configured": auth_configured,
            "supabase_auth_reachable": auth_reachable,
            "supabase_data_configured": data_configured,
            "supabase_data_reachable": data_reachable,
            "agent_execution_enabled": runtime_enabled,
        },
    }


@app.get("/v1/me", tags=["identity"], include_in_schema=False)
@app.get("/api/v1/me", tags=["identity"], response_model=MyProfileResponse)
async def get_me(request: Request, user=Depends(current_user)):
    settings = request.app.state.settings
    token = request.headers["authorization"].removeprefix("Bearer ").strip()
    response = await request.app.state.http.get(
        f"{settings.supabase_url}/rest/v1/profiles",
        params={"id": f"eq.{user['id']}", "select": "id,display_name,avatar_path,locale,timezone"},
        headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
        timeout=8.0,
    )
    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail={"code": "profile_service_unavailable", "message": "Profile service is temporarily unavailable"})
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail={"code": "profile_service_error", "message": "Profile service returned an unexpected response"})
    rows = response.json()
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail={"code": "profile_response_invalid", "message": "Profile service returned an invalid response"})
    return {"user": user, "profile": rows[0] if rows else None}


@app.patch("/api/v1/me/profile", tags=["identity"], response_model=MyProfileResponse)
async def update_my_profile(body: ProfileUpdate, request: Request, user=Depends(current_user)):
    changes = body.changes()
    if not changes:
        return await get_me(request, user)
    if "display_name" in changes and changes["display_name"] is not None:
        changes["display_name"] = changes["display_name"].strip()
        if not changes["display_name"]:
            raise HTTPException(status_code=422, detail={"code": "invalid_display_name", "message": "Display name cannot be empty"})
    if "avatar_path" in changes and changes["avatar_path"] is not None:
        path = changes["avatar_path"]
        if path.startswith(("http://", "https://", "/")) or ".." in path.split("/") or not path.startswith(f"{user['id']}/"):
            raise HTTPException(status_code=422, detail={"code": "invalid_avatar_path", "message": "Avatar path must be owner-scoped"})
    settings = request.app.state.settings
    token = request.headers["authorization"].removeprefix("Bearer ").strip()
    response = await request.app.state.http.patch(
        f"{settings.supabase_url}/rest/v1/profiles",
        params={"id": f"eq.{user['id']}", "select": "id,display_name,avatar_path,locale,timezone"},
        json=changes,
        headers={
            "apikey": settings.supabase_anon_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        timeout=8.0,
    )
    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail={"code": "profile_service_unavailable", "message": "Profile service is temporarily unavailable"})
    if response.status_code >= 400:
        raise HTTPException(status_code=422, detail={"code": "profile_update_rejected", "message": "Profile update was rejected by the profile policy"})
    rows = response.json()
    if not isinstance(rows, list):
        raise HTTPException(status_code=502, detail={"code": "profile_response_invalid", "message": "Profile service returned an invalid response"})
    if not rows:
        raise HTTPException(status_code=404, detail={"code": "profile_not_found", "message": "Profile not found or not editable"})
    return {"user": user, "profile": rows[0]}


def _moreai_openapi():
    """Publish the actual FastAPI contracts with explicit bearer and correlation headers."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    components = schema.setdefault("components", {})
    components.setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
        "description": "Supabase Auth access token. Roles and tenant scope are resolved server-side.",
    }
    for path, path_item in schema.get("paths", {}).items():
        if not path.startswith("/api/v1/"):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"} or not isinstance(operation, dict):
                continue
            operation.setdefault("security", [{"BearerAuth": []}])
            params = operation.setdefault("parameters", [])
            if not any(isinstance(item, dict) and item.get("name") == "X-Correlation-ID" for item in params):
                params.append({"name": "X-Correlation-ID", "in": "header", "required": False, "description": "Optional trace ID; generated by the API when omitted.", "schema": {"type": "string", "maxLength": 128}})
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = _moreai_openapi
