"""Start the LiteLLM proxy for integration tests, and read its streamed answers (issues #9, #12)."""

from __future__ import annotations

import json
import os
import secrets
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT_S = 90


@dataclass(frozen=True)
class RunningProxy:
    """A started proxy: where to reach it, its master key, and the mock LLM's record file."""

    base_url: str
    master_key: str
    record_file: Path

    @property
    def auth(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.master_key}"}

    def clear_record(self) -> Path:
        """Empty the record file (one proxy serves several tests) and return its path."""
        self.record_file.write_text("", encoding="utf-8")
        return self.record_file


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@contextmanager
def start_proxy(config: Path, work_dir: Path) -> Iterator[RunningProxy]:
    """Start the proxy from the project root with ``config``, on a free port, with a random
    master key used only by this run and mock LLM recording on (the record file and the proxy
    log are written to ``work_dir``). Stop it on exit."""
    port = _free_port()
    master_key = "sk-" + secrets.token_hex(32)
    record_file = work_dir / "mock_llm_record.jsonl"
    log_path = work_dir / "proxy.log"
    env = {
        **os.environ,
        "LITELLM_MASTER_KEY": master_key,
        "LEAKGUARD_MOCK_LLM__RECORD_FILE": str(record_file),
        # LiteLLM's start-up banner cannot be written in Windows' default encoding.
        "PYTHONUTF8": "1",
    }
    base_url = f"http://127.0.0.1:{port}"

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "litellm.proxy.proxy_cli",
             "--config", str(config), "--host", "127.0.0.1", "--port", str(port)],
            cwd=PROJECT_ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + STARTUP_TIMEOUT_S
            while True:
                if process.poll() is not None:
                    pytest.fail("LiteLLM proxy exited during start-up:\n"
                                + log_path.read_text(encoding="utf-8")[-3000:])
                try:
                    if httpx.get(f"{base_url}/health/liveliness", timeout=2).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    pytest.fail(f"LiteLLM proxy did not start within {STARTUP_TIMEOUT_S} s")
                time.sleep(1)

            yield RunningProxy(base_url, master_key, record_file)
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()


def stream_content(response: httpx.Response) -> str:
    """Join the ``delta.content`` pieces of a streamed chat answer (its ``data:`` lines)."""
    pieces = []
    for line in response.text.splitlines():
        if not line.startswith("data: ") or line == "data: [DONE]":
            continue
        for choice in json.loads(line.removeprefix("data: ")).get("choices", []):
            content = choice.get("delta", {}).get("content")
            if content:
                pieces.append(content)
    return "".join(pieces)
