from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
from urllib.parse import quote
from typing import Any

from apps.worker.app.client import WorkerRpcClient


class SupabaseWorkspaceTool:
    """Immutable-version workspace files with lease-fenced compare-and-swap metadata."""

    def __init__(self, client: WorkerRpcClient, *, bucket: str | None = None):
        self.client = client
        self.bucket = bucket or os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")

    @staticmethod
    def _safe_path(value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
            raise ValueError("workspace_path_invalid")
        parts=value.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise ValueError("workspace_path_traversal_denied")
        normalized=posixpath.normpath(value)
        if normalized in (".","..") or normalized.startswith("../") or normalized.startswith("/"):
            raise ValueError("workspace_path_traversal_denied")
        if not re.fullmatch(r"[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*",normalized):
            raise ValueError("workspace_path_characters_denied")
        return normalized

    def _object_url(self, storage_path: str) -> str:
        return f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/object/{quote(self.bucket,safe='')}/{quote(storage_path,safe='/')}"

    def _headers(self, content_type: str="application/octet-stream", upsert: bool=False) -> dict[str,str]:
        key=self.client.settings.service_role_key
        return {"apikey":key,"Authorization":f"Bearer {key}","Content-Type":content_type,"x-upsert":"true" if upsert else "false"}

    async def str_replace_editor(self, arguments: dict[str,Any], *, run_id: str, user_id: str, workspace_id: str|None=None) -> str:
        if not workspace_id: raise RuntimeError("persistent_workspace_requires_workspace_id")
        path=self._safe_path(arguments.get("path"))
        old,new=arguments.get("old_str"),arguments.get("new_str")
        if not isinstance(old,str) or not isinstance(new,str): raise ValueError("workspace_editor_text_required")
        if len(old.encode())>50000 or len(new.encode())>50000: raise ValueError("workspace_editor_patch_too_large")
        bucket=await self.client.client.get(f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket,safe='')}",headers=self._headers(),timeout=8.0)
        if bucket.status_code>=400 or bucket.json().get("public") is not False: raise RuntimeError("workspace_bucket_must_exist_and_be_private")

        current=await self.client.workspace_get_file(user_id,workspace_id,path)
        version=current.get("version")
        if isinstance(version,bool) or not isinstance(version,int): raise RuntimeError("workspace_version_invalid")
        expected=arguments.get("expected_version",version)
        if isinstance(expected,bool) or not isinstance(expected,int) or expected!=version: raise ValueError("workspace_version_conflict")
        storage_path=current.get("storage_path")
        if storage_path:
            response=await self.client.client.get(self._object_url(storage_path),headers=self._headers(),timeout=15.0)
            response.raise_for_status()
            if len(response.content)>2000000: raise ValueError("workspace_file_too_large")
            try: source=response.content.decode("utf-8")
            except UnicodeDecodeError as exc: raise ValueError("workspace_editor_only_supports_utf8_text") from exc
        else:
            source=""
        if storage_path and not old: raise ValueError("workspace_create_cannot_overwrite_existing_file")
        if not storage_path and old: raise ValueError("workspace_file_not_found")
        if old:
            if source.count(old)!=1: raise ValueError("workspace_edit_match_must_be_unique")
            updated=source.replace(old,new,1)
        else:
            updated=new
        raw=updated.encode("utf-8")
        if len(raw)>2000000: raise ValueError("workspace_file_too_large")
        reservation=await self.client.workspace_begin_write(run_id,user_id,workspace_id,path,version)
        token, next_version, object_path=reservation.get("token"),reservation.get("version"),reservation.get("storage_path")
        if not isinstance(token,str) or not isinstance(next_version,int) or not isinstance(object_path,str):
            raise RuntimeError("workspace_write_reservation_invalid")
        sha=hashlib.sha256(raw).hexdigest()
        committed=False
        try:
            upload=await self.client.client.post(self._object_url(object_path),content=raw,headers=self._headers("text/plain; charset=utf-8",False),timeout=20.0)
            upload.raise_for_status()
            result=await self.client.workspace_commit_write(run_id,user_id,workspace_id,path,token,next_version,object_path,sha,len(raw))
            committed=True
            return json.dumps({"workspace_id":workspace_id,"path":path,"version":result["version"],"bytes":len(raw),"sha256":sha,"status":"saved"},separators=(",",":"))
        finally:
            if not committed:
                await self.client.workspace_abort_write(run_id,user_id,workspace_id,path,token)
