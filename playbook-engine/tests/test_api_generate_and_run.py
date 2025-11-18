import os
import sys
import json
import ctypes
import subprocess
from pathlib import Path

import asyncio
import pytest
from starlette.testclient import TestClient

# Make src importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.main import app  # noqa: E402
from src.utils.config import load_config  # noqa: E402


def _clear_config_cache():
    try:
        load_config.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass


def _is_admin_windows() -> bool:
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


@pytest.fixture(autouse=True)
def api_env(monkeypatch, tmp_path):
    # Keep tests fast and side-effect free
    monkeypatch.setenv("REDIS_COOLDOWN_ENABLED", "false")
    monkeypatch.setenv("EXECUTIONS_PERSIST", "false")
    monkeypatch.setenv("GENAI_PROVIDER", "stub")  # deterministic generator
    monkeypatch.setenv("ALLOW_ISOLATE_HOST", "false")

    # Avoid background RabbitMQ/file ingestion during app startup
    async def _noop(*args, **kwargs):
        return None
    monkeypatch.setattr("src.messaging.consumer.start_consumer", _noop, raising=False)
    monkeypatch.setattr("src.messaging.consumer.ingest_file_once", _noop, raising=False)

    _clear_config_cache()
    yield
    _clear_config_cache()


def test_api_generate_and_run_file(tmp_path):
    # Create a real temporary file to quarantine
    f = tmp_path / "api-e2e-mal.bin"
    f.write_text("malware")
    alert = {
        "event_type": "file",
        "severity": "medium",
        "agent_id": "api-e2e",
        "event_id": "api-file-1",
        "details": {"path": str(f).replace("\\", "/")},
    }

    with TestClient(app) as client:
        resp = client.post("/api/playbooks/generate-and-run", json=alert)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body.get("path"), body
        result = body.get("result", {})
        assert result.get("playbook_id") or body.get("playbook_id")
        assert result.get("success") is True
        # File should be moved to quarantine
        assert not f.exists()


def test_api_generate_and_run_process():
    if os.name != "nt":
        pytest.skip("Windows-only process action")
    # Launch a benign process to terminate
    exe = os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "notepad.exe")
    proc = subprocess.Popen([exe])
    pid = proc.pid

    alert = {
        "event_type": "process",
        "severity": "high",
        "agent_id": "api-e2e",
        "event_id": "api-proc-1",
        "details": {"pid": pid},
    }

    with TestClient(app) as client:
        resp = client.post("/api/playbooks/generate-and-run", json=alert)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        result = body.get("result", {})
        # Even if other optional steps are skipped, kill_process should succeed
        steps = result.get("steps", [])
        assert any(s.get("action") == "kill_process" and s.get("status") == "ok" for s in steps), steps
        # Verify process is terminated
        check = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
        assert str(pid) not in check.stdout


@pytest.mark.skipif(os.name == "nt" and not _is_admin_windows(), reason="Requires Administrator for firewall rule changes")
def test_api_generate_and_run_network():
    # Use a test/documentation IP
    test_ip = "203.0.113.10"
    alert = {
        "event_type": "network",
        "severity": "medium",
        "agent_id": "api-e2e",
        "event_id": "api-net-1",
        "details": {"ip": test_ip, "remote_port": 443},
    }

    with TestClient(app) as client:
        resp = client.post("/api/playbooks/generate-and-run", json=alert)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        result = body.get("result", {})
        assert result.get("success") is True, body

    # Cleanup firewall rules (best effort, Windows only)
    if os.name == "nt":
        for name in (f"Playbook-Block-IP-In-{test_ip}", f"Playbook-Block-IP-Out-{test_ip}"):
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"], capture_output=True)
