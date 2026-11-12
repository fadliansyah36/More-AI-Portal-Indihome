from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import JSONResponse

from app.config import Settings
from app.dependencies import current_user
from app.routers import admin, agent_runs, artifacts, catalog, conversations, customer, notifications, partner, tool_approvals, workspaces, learning


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
        allow_headers=['Authorization', 'Content-Type', 'Accept', 'Idempotency-Key', 'X-Correlation-ID'],
        expose_headers=['X-Correlation-ID'],
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
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = valid
    return response


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected server error occurred",
                "correlation_id": getattr(request.state, "correlation_id", None),
            }
        },
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
@app.get("/api/v1/me", tags=["identity"])
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
        return JSONResponse(status_code=503, content={"detail": "Profile service unavailable"})
    if response.status_code != 200:
        return JSONResponse(status_code=502, content={"detail": "Profile service returned an unexpected response"})
    rows = response.json()
    return {"user": user, "profile": rows[0] if rows else None}


@app.patch("/api/v1/me/profile", tags=["identity"])
async def update_my_profile(body: ProfileUpdate, request: Request, user=Depends(current_user)):
    changes = body.changes()
    if not changes:
        return await get_me(request, user)
    if "display_name" in changes and changes["display_name"] is not None:
        changes["display_name"] = changes["display_name"].strip()
        if not changes["display_name"]:
            return JSONResponse(status_code=422, content={"detail": "Display name cannot be empty"})
    if "avatar_path" in changes and changes["avatar_path"] is not None:
        path = changes["avatar_path"]
        if path.startswith(("http://", "https://", "/")) or ".." in path.split("/") or not path.startswith(f"{user['id']}/"):
            return JSONResponse(status_code=422, content={"detail": "Avatar path must be owner-scoped"})
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
        return JSONResponse(status_code=503, content={"detail": "Profile service unavailable"})
    if response.status_code >= 400:
        return JSONResponse(status_code=422, content={"detail": "Profile update was rejected by the profile policy"})
    rows = response.json()
    if not rows:
        return JSONResponse(status_code=404, content={"detail": "Profile not found or not editable"})
    return {"user": user, "profile": rows[0]}
