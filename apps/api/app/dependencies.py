from typing import Annotated, Any
from fastapi import Depends, Header, HTTPException, Request, status


async def current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid bearer access token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = request.app.state.settings
    if not settings.supabase_auth_ready:
        raise HTTPException(status_code=503, detail="Authentication service is not configured")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")

    try:
        response = await request.app.state.http.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
            timeout=8.0,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc

    if response.status_code in (401, 403):
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Unexpected authentication response")

    user = response.json()
    if not isinstance(user, dict) or not user.get("id"):
        raise HTTPException(status_code=401, detail="Authentication response is invalid")

    # Supabase Auth metadata is the authoritative registration-time name fallback.
    # Expose only a normalized display name, never the raw metadata object.
    metadata = user.get("user_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    display_name = metadata.get("full_name") or metadata.get("name")
    if isinstance(display_name, str):
        display_name = " ".join(display_name.split())[:120] or None
    else:
        display_name = None
    return {"id": user["id"], "email": user.get("email"), "display_name": display_name}
