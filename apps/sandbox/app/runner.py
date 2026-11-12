from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import signal
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SandboxLimits:
    timeout_seconds: int = 30
    memory_mb: int = 512
    cpu_count: float = 1.0
    pids_limit: int = 32
    output_bytes: int = 64_000
    workspace_bytes: int = 2_000_000


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    workspace_files: dict[str, bytes]


class _OutputLimitExceeded(RuntimeError):
    pass


async def _read_bounded(stream: asyncio.StreamReader, limit: int) -> bytes:
    output = bytearray()
    while True:
        chunk = await stream.read(8192)
        if not chunk:
            return bytes(output)
        if len(output) + len(chunk) > limit:
            raise _OutputLimitExceeded()
        output.extend(chunk)


# The bootstrap runs outside the user process. User code receives only an ephemeral
# /tmp/workspace tree; it cannot access the supervisor filesystem or network.
_BOOTSTRAP = r"""
import base64, contextlib, io, json, os, pathlib, re, subprocess, sys
payload=json.loads(sys.stdin.read())
root=pathlib.Path('/tmp/workspace')
root.mkdir(mode=0o700, parents=True, exist_ok=True)
files=payload.get('workspace_files') or {}
total=0
for name, encoded in files.items():
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*',name) or any(x in ('','.','..') for x in name.split('/')):
        raise SystemExit('workspace_snapshot_path_invalid')
    raw=base64.b64decode(encoded, validate=True)
    total += len(raw)
    if total > 2000000: raise SystemExit('workspace_snapshot_limit_exceeded')
    target=root.joinpath(*name.split('/'))
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    target.write_bytes(raw)
source=payload.get('source')
language=payload.get('language')
if not isinstance(source,str) or language not in ('python','bash'): raise SystemExit('sandbox_payload_invalid')
try:
    with tempfile.TemporaryFile() as out_file, tempfile.TemporaryFile() as err_file:
        command = ([sys.executable,'-I','-c',source] if language == 'python'
                   else ['bash','--noprofile','--norc','-c',source])
        proc=subprocess.run(command, cwd=str(root), stdout=out_file, stderr=err_file, timeout=115)
        exit_code=proc.returncode
        out_file.seek(0); err_file.seek(0)
        stdout=out_file.read(65536).decode('utf-8','replace')
        stderr=err_file.read(65536).decode('utf-8','replace')
except subprocess.TimeoutExpired:
    exit_code=124
    stdout=''
    stderr='execution_timeout'
changed={}
total=0
for item in root.rglob('*'):
    if item.is_symlink(): raise SystemExit('workspace_symlink_not_supported')
    if not item.is_file(): continue
    rel=item.relative_to(root).as_posix()
    if not re.fullmatch(r'[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*',rel) or any(x in ('','.','..') for x in rel.split('/')): continue
    raw=item.read_bytes()
    total += len(raw)
    if total > 2000000: raise SystemExit('workspace_snapshot_limit_exceeded')
    if len(changed) >= 200: raise SystemExit('workspace_file_count_exceeded')
    changed[rel]=base64.b64encode(raw).decode('ascii')
sys.stdout.write(json.dumps({'exit_code':exit_code,'stdout':stdout,'stderr':stderr,'workspace_files':changed},separators=(',',':')))
"""
_PROTOCOL_BYTES = 4_000_000


class DockerSandbox:
    """Fail-closed disposable runner with an ephemeral, network-disabled workspace snapshot."""

    def __init__(self, *, image: str | None = None, docker_binary: str = "docker"):
        self.image = image or os.getenv("MOREAI_SANDBOX_IMAGE", "")
        self.docker_binary = docker_binary

    def _validate(self) -> None:
        if not self.image or "@sha256:" not in self.image:
            raise RuntimeError("sandbox_image_must_be_digest_pinned")
        image, digest = self.image.rsplit("@sha256:", 1)
        if not image or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise RuntimeError("sandbox_image_digest_invalid")
        if any(c in self.image for c in "\\n\\r\\x00"):
            raise RuntimeError("invalid_sandbox_image")

    async def check_ready(self) -> None:
        self._validate()
        process = await asyncio.create_subprocess_exec(
            self.docker_binary, "info", "--format", "{{.ServerVersion}}",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            env={"PATH": os.getenv("PATH", "/usr/bin:/bin"), "DOCKER_HOST": os.getenv("DOCKER_HOST", "")},
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=3.0)
        except TimeoutError as exc:
            self._terminate(process)
            await process.wait()
            raise RuntimeError("sandbox_runtime_unavailable") from exc
        if process.returncode != 0 or not stdout.strip():
            raise RuntimeError("sandbox_runtime_unavailable")

    @staticmethod
    def _terminate(process: asyncio.subprocess.Process) -> None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    async def _remove_container(self, cidfile: str) -> None:
        try:
            container_id = Path(cidfile).read_text(encoding="ascii").strip()
        except (OSError, UnicodeError):
            container_id = ""
        finally:
            try: Path(cidfile).unlink(missing_ok=True)
            except OSError: pass
        if not re.fullmatch(r"[0-9a-fA-F]{12,64}", container_id): return
        cleanup = await asyncio.create_subprocess_exec(
            self.docker_binary, "rm", "--force", container_id,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
            env={"PATH": os.getenv("PATH", "/usr/bin:/bin"), "DOCKER_HOST": os.getenv("DOCKER_HOST", "")},
        )
        try: await asyncio.wait_for(cleanup.wait(), timeout=4.0)
        except TimeoutError:
            self._terminate(cleanup)
            await cleanup.wait()

    async def execute(
        self, source: str, *, language: Literal["python", "bash"],
        workspace_files: dict[str, bytes] | None = None,
        limits: SandboxLimits = SandboxLimits(),
    ) -> SandboxResult:
        self._validate()
        if not source or len(source.encode("utf-8")) > 8_000_000:
            raise ValueError("sandbox_source_size_invalid")
        if language not in ("python", "bash"): raise ValueError("sandbox_language_not_supported")
        workspace_files = workspace_files or {}
        encoded_files = {}
        total = 0
        for name, raw in workspace_files.items():
            if not re.fullmatch(r"[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*", name) or any(x in ("", ".", "..") for x in name.split("/")):
                raise ValueError("sandbox_workspace_path_invalid")
            if not isinstance(raw, bytes): raise ValueError("sandbox_workspace_file_invalid")
            total += len(raw)
            if total > limits.workspace_bytes: raise ValueError("sandbox_workspace_snapshot_too_large")
            encoded_files[name] = base64.b64encode(raw).decode("ascii")
        if (
            not 1 <= limits.timeout_seconds <= 120 or not 64 <= limits.memory_mb <= 2048
            or not 0 < limits.cpu_count <= 4 or not 1 <= limits.pids_limit <= 128
            or not 1 <= limits.output_bytes <= 1_000_000 or not 1 <= limits.workspace_bytes <= 2_000_000
        ): raise ValueError("sandbox_limits_out_of_range")

        payload = json.dumps({"source": source, "language": language, "workspace_files": encoded_files}, separators=(",", ":")).encode()
        cid_handle = tempfile.NamedTemporaryFile(prefix="moreai-sandbox-", suffix=".cid", delete=False)
        cidfile = cid_handle.name
        cid_handle.close()
        Path(cidfile).unlink(missing_ok=True)
        command = [
            self.docker_binary, "run", "--rm", "-i", "--cidfile", cidfile,
            "--network=none", "--read-only", "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true", "--security-opt=seccomp=default",
            "--pids-limit", str(limits.pids_limit), "--memory", f"{limits.memory_mb}m",
            "--cpus", str(limits.cpu_count), "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--workdir", "/tmp", self.image, "python", "-I", "-c", _BOOTSTRAP,
        ]
        process = await asyncio.create_subprocess_exec(
            *command, stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            env={"PATH": os.getenv("PATH", "/usr/bin:/bin"), "DOCKER_HOST": os.getenv("DOCKER_HOST", "")},
        )
        stdout_task = asyncio.create_task(_read_bounded(process.stdout, _PROTOCOL_BYTES))
        stderr_task = asyncio.create_task(_read_bounded(process.stderr, limits.output_bytes))
        try:
            if process.stdin is None: raise RuntimeError("sandbox_stdin_unavailable")
            process.stdin.write(payload)
            await process.stdin.drain()
            process.stdin.close()
            await process.stdin.wait_closed()
            stdout, stderr = await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task), timeout=limits.timeout_seconds,
            )
            await process.wait()
            if process.returncode != 0: raise RuntimeError("sandbox_runner_protocol_failed")
            try: envelope = json.loads(stdout)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise RuntimeError("sandbox_runner_protocol_invalid") from exc
            if not isinstance(envelope, dict) or not isinstance(envelope.get("workspace_files"), dict):
                raise RuntimeError("sandbox_runner_response_invalid")
            files = {}
            returned_total = 0
            for name, encoded in envelope["workspace_files"].items():
                if not isinstance(name, str) or not isinstance(encoded, str): raise RuntimeError("sandbox_runner_workspace_invalid")
                raw = base64.b64decode(encoded, validate=True)
                returned_total += len(raw)
                if returned_total > limits.workspace_bytes: raise RuntimeError("sandbox_runner_workspace_limit_exceeded")
                files[name] = raw
            return SandboxResult(
                exit_code=int(envelope.get("exit_code", -1)),
                stdout=str(envelope.get("stdout", ""))[:limits.output_bytes],
                stderr=str(envelope.get("stderr", ""))[:limits.output_bytes],
                timed_out=int(envelope.get("exit_code", -1)) == 124,
                workspace_files=files,
            )
        except (_OutputLimitExceeded, TimeoutError):
            self._terminate(process)
            await process.wait()
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            return SandboxResult(-1, "", "execution_timeout_or_output_limit", True, {})
        except BaseException:
            self._terminate(process)
            await process.wait()
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            raise
        finally:
            await self._remove_container(cidfile)
