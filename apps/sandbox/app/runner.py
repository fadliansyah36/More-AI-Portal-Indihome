from __future__ import annotations

import asyncio
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
    workspace_bytes: int = 8_000_000


@dataclass(frozen=True)
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool


class _OutputLimitExceeded(RuntimeError):
    pass


async def _read_bounded(stream: asyncio.StreamReader, limit: int) -> bytes:
    output = bytearray()
    total = 0
    while True:
        chunk = await stream.read(8192)
        if not chunk:
            return bytes(output)
        total += len(chunk)
        if total > limit:
            raise _OutputLimitExceeded()
        output.extend(chunk)


class DockerSandbox:
    """Fail-closed disposable runner with immutable image and bounded process I/O."""

    def __init__(self, *, image: str | None = None, docker_binary: str = "docker"):
        self.image = image or os.getenv("MOREAI_SANDBOX_IMAGE", "")
        self.docker_binary = docker_binary

    def _validate(self) -> None:
        if not self.image or "@sha256:" not in self.image:
            raise RuntimeError("sandbox_image_must_be_digest_pinned")
        image, digest = self.image.rsplit("@sha256:", 1)
        if not image or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise RuntimeError("sandbox_image_digest_invalid")
        if any(c in self.image for c in "\n\r\x00"):
            raise RuntimeError("invalid_sandbox_image")

    async def check_ready(self) -> None:
        """Require the configured Docker daemon/socket proxy to be reachable."""
        self._validate()
        process = await asyncio.create_subprocess_exec(
            self.docker_binary, "info", "--format", "{{.ServerVersion}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            env={
                "PATH": os.getenv("PATH", "/usr/bin:/bin"),
                "DOCKER_HOST": os.getenv("DOCKER_HOST", ""),
            },
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
        """Remove the daemon-side container even if the docker CLI was cancelled."""
        try:
            container_id = Path(cidfile).read_text(encoding="ascii").strip()
        except (OSError, UnicodeError):
            container_id = ""
        finally:
            try:
                Path(cidfile).unlink(missing_ok=True)
            except OSError:
                pass
        if not re.fullmatch(r"[0-9a-fA-F]{12,64}", container_id):
            return
        cleanup = await asyncio.create_subprocess_exec(
            self.docker_binary, "rm", "--force", container_id,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
            env={"PATH": os.getenv("PATH", "/usr/bin:/bin"), "DOCKER_HOST": os.getenv("DOCKER_HOST", "")},
        )
        try:
            await asyncio.wait_for(cleanup.wait(), timeout=4.0)
        except TimeoutError:
            self._terminate(cleanup)
            await cleanup.wait()

    async def execute(
        self, source: str, *,
        language: Literal["python", "bash"],
        limits: SandboxLimits = SandboxLimits(),
    ) -> SandboxResult:
        self._validate()
        if not source or len(source.encode("utf-8")) > limits.workspace_bytes:
            raise ValueError("sandbox_source_size_invalid")
        if language not in ("python", "bash"):
            raise ValueError("sandbox_language_not_supported")
        if (
            not 1 <= limits.timeout_seconds <= 120
            or not 64 <= limits.memory_mb <= 2048
            or not 0 < limits.cpu_count <= 4
            or not 1 <= limits.pids_limit <= 128
            or not 1 <= limits.output_bytes <= 1_000_000
            or not 1 <= limits.workspace_bytes <= 20_000_000
        ):
            raise ValueError("sandbox_limits_out_of_range")

        cid_handle = tempfile.NamedTemporaryFile(prefix="moreai-sandbox-", suffix=".cid", delete=False)
        cidfile = cid_handle.name
        cid_handle.close()
        Path(cidfile).unlink(missing_ok=True)
        command = [
            self.docker_binary, "run", "--rm", "-i", "--cidfile", cidfile,
            "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges:true",
            "--security-opt=seccomp=default",
            "--pids-limit", str(limits.pids_limit),
            "--memory", f"{limits.memory_mb}m",
            "--cpus", str(limits.cpu_count),
            "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
            "--workdir", "/tmp", self.image,
            *( ["python", "-I", "-"] if language == "python" else ["bash", "--noprofile", "--norc"] ),
        ]
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
            env={"PATH": os.getenv("PATH", "/usr/bin:/bin"), "DOCKER_HOST": os.getenv("DOCKER_HOST", "")},
        )
        stdout_task = asyncio.create_task(_read_bounded(process.stdout, limits.output_bytes))
        stderr_task = asyncio.create_task(_read_bounded(process.stderr, limits.output_bytes))
        try:
            if process.stdin is None:
                raise RuntimeError("sandbox_stdin_unavailable")
            process.stdin.write(source.encode("utf-8"))
            await process.stdin.drain()
            process.stdin.close()
            await process.stdin.wait_closed()
            stdout, stderr = await asyncio.wait_for(
                asyncio.gather(stdout_task, stderr_task),
                timeout=limits.timeout_seconds,
            )
            await process.wait()
            return SandboxResult(
                exit_code=process.returncode if process.returncode is not None else -1,
                stdout=stdout.decode("utf-8", "replace"),
                stderr=stderr.decode("utf-8", "replace"),
                timed_out=False,
            )
        except _OutputLimitExceeded:
            self._terminate(process)
            await process.wait()
            await self._remove_container(cidfile)
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            return SandboxResult(-1, "", "output_limit_exceeded", False)
        except TimeoutError:
            self._terminate(process)
            await process.wait()
            await self._remove_container(cidfile)
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            return SandboxResult(-1, "", "execution_timeout", True)
        except BaseException:
            self._terminate(process)
            await process.wait()
            await self._remove_container(cidfile)
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            raise
        else:
            await self._remove_container(cidfile)
