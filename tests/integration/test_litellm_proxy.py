"""End-to-end check: the real LiteLLM proxy starts from config/litellm.yaml with the
LeakGuard guardrail and approves a request to the mock model (issue #9)."""

from __future__ import annotations

import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

pytest.importorskip("litellm")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTUP_TIMEOUT_S = 90
CHAT_REQUEST = {
    "model": "leakguard-mock",
    "messages": [{"role": "user", "content": "hello LeakGuard"}],
}
MOCK_ANSWER = "Mock answer from the LeakGuard test model."


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def proxy(tmp_path_factory):
    """Start the proxy on a free port with a random master key used only by this run."""
    port = _free_port()
    master_key = "sk-" + secrets.token_hex(32)
    log_path = tmp_path_factory.mktemp("litellm") / "proxy.log"
    # PYTHONUTF8: LiteLLM's start-up banner cannot be written in Windows' default encoding.
    env = {**os.environ, "LITELLM_MASTER_KEY": master_key, "PYTHONUTF8": "1"}
    base_url = f"http://127.0.0.1:{port}"

    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "litellm.proxy.proxy_cli",
             "--config", "config/litellm.yaml", "--host", "127.0.0.1", "--port", str(port)],
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

            yield base_url, master_key
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()


def test_request_without_master_key_is_rejected(proxy):
    base_url, _ = proxy
    response = httpx.post(f"{base_url}/v1/chat/completions", json=CHAT_REQUEST, timeout=30)
    # LiteLLM 1.108.20 answers 500 here (its auth error handler needs the optional `prisma`
    # package); what matters is that the request is rejected and never reaches the model.
    assert response.status_code >= 400
    assert MOCK_ANSWER not in response.text


def test_leakguard_guardrail_is_registered(proxy):
    base_url, master_key = proxy
    response = httpx.get(f"{base_url}/guardrails/list",
                         headers={"Authorization": f"Bearer {master_key}"}, timeout=30)
    assert response.status_code == 200
    assert "leakguard" in [g["guardrail_name"] for g in response.json()["guardrails"]]


def test_request_with_master_key_is_approved(proxy):
    base_url, master_key = proxy
    response = httpx.post(f"{base_url}/v1/chat/completions", json=CHAT_REQUEST,
                          headers={"Authorization": f"Bearer {master_key}"}, timeout=30)
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == MOCK_ANSWER
