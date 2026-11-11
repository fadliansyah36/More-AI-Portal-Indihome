from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.dependencies import current_user
from app.routers import agent_runs, artifacts, catalog, conversations, customer, partner, tool_approvals


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

app.include_router(conversations.router)
app.include_router(customer.router)
app.include_router(partner.router)
app.include_router(tool_approvals.router)
app.include_router(agent_runs.router)
app.include_router(catalog.router)
app.include_router(artifacts.router)


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
    auth_ready = settings.supabase_auth_ready
    data_ready = settings.supabase_data_ready
    runtime_enabled = settings.agent_execution_enabled
    ready = auth_ready and data_ready
    return {
        "status": "ready" if ready else "degraded",
        "dependencies": {
            "supabase_auth": auth_ready,
            "supabase_data": data_ready,
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
