import os
import sys
import json
import ctypes
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
import time
import pytest

from src.utils.config import load_config
from src.genai.generator import generate_playbook
from src.core.parser import parse_playbook_yaml
from src.core.executor import execute_playbook
from src.utils.logger import AUDIT_FILE


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
def e2e_env(monkeypatch, tmp_path):
    # Make tests fast and non-intrusive
    monkeypatch.setenv("REDIS_COOLDOWN_ENABLED", "false")
    monkeypatch.setenv("EXECUTIONS_PERSIST", "false")
    # Prefer groq if available, else skip in tests that require it
    monkeypatch.setenv("GENAI_PROVIDER", os.getenv("GENAI_PROVIDER", "groq"))
    # Ensure fresh config picks up env
    _clear_config_cache()
    yield
    _clear_config_cache()


def _read_audit_count() -> int:
    p = AUDIT_FILE
    if not Path(p).exists():
        return 0
    with open(p, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def _has_groq_key() -> bool:
    cfg = load_config()
    return bool(cfg.get("genai", {}).get("groq_api_key"))


@pytest.mark.skipif(not _has_groq_key(), reason="Groq key not found in config.yaml or env")
def test_e2e_file_quarantine(tmp_path):
    # Prepare a real file alert
    f = tmp_path / "e2e-mal.bin"
    f.write_text("malware")
    alert = {
        "event_type": "file",
        "severity": "medium",
        "agent_id": "e2e-agent",
        "event_id": "evt-file-e2e",
        "details": {"path": str(f).replace('\\','/')},
    }

    before = _read_audit_count()

    async def run():
        print("[FILE] Alert JSON:\n", json.dumps(alert, indent=2))
        pb_path = await generate_playbook(alert)
        print(f"[FILE] Generated playbook path: {pb_path}")
        with open(pb_path, 'r', encoding='utf-8') as yf:
            print("[FILE] Generated Playbook YAML:\n" + yf.read())
        pb = parse_playbook_yaml(pb_path)
        print("[FILE] Parsed Playbook Steps:")
        for s in pb.steps:
            print("   -", s.name, s.action, s.params)
        res = await execute_playbook(pb, alert)
        print("[FILE] Execution Result success=", res.success, "rolled_back=", res.rolled_back)
        for st in res.steps:
            print("   [STEP]", st)
        return res

    res = asyncio.get_event_loop().run_until_complete(run())
    assert res.success is True
    # File should be moved
    assert not f.exists()
    after = _read_audit_count()
    assert after >= before + 1


@pytest.mark.skipif(not _has_groq_key(), reason="Groq key not found in config.yaml or env")
def test_e2e_process_kill():
    # Launch a harmless process (notepad) and treat as malicious
    exe = os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32", "notepad.exe")
    proc = subprocess.Popen([exe])
    pid = proc.pid
    alert = {
        "event_type": "process",
        "severity": "high",
        "agent_id": "e2e-agent",
        "event_id": "evt-proc-e2e",
        "details": {"pid": pid},
    }
    before = _read_audit_count()

    async def run():
        print("[PROC] Alert JSON:\n", json.dumps(alert, indent=2))
        pb_path = await generate_playbook(alert)
        print(f"[PROC] Generated playbook path: {pb_path}")
        with open(pb_path, 'r', encoding='utf-8') as yf:
            print("[PROC] Generated Playbook YAML:\n" + yf.read())
        pb = parse_playbook_yaml(pb_path)
        print("[PROC] Parsed Playbook Steps:")
        for s in pb.steps:
            print("   -", s.name, s.action, s.params)
        res = await execute_playbook(pb, alert)
        print("[PROC] Execution Result success=", res.success, "rolled_back=", res.rolled_back)
        for st in res.steps:
            print("   [STEP]", st)
        return res

    res = asyncio.get_event_loop().run_until_complete(run())
    # Success may be False if an optional step fails; ensure kill_process step executed
    kill_steps = [s for s in res.steps if s.get("action") == "kill_process" and s.get("status") == "ok"]
    assert kill_steps, f"Kill process action did not succeed: {res.steps}"
    # Give the OS a moment to terminate
    time.sleep(0.5)
    check = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True)
    assert str(pid) not in check.stdout
    after = _read_audit_count()
    assert after >= before + 1


@pytest.mark.skipif(not _has_groq_key(), reason="Groq key not found in config.yaml or env")
@pytest.mark.skipif(os.name == "nt" and not _is_admin_windows(), reason="Requires Administrator for firewall rule changes")
def test_e2e_network_block_ip():
    # Use a documentation/test IP range
    test_ip = "203.0.113.10"
    alert = {
        "event_type": "network",
        "severity": "medium",
        "agent_id": "e2e-agent",
        "event_id": "evt-net-e2e",
        "details": {"ip": test_ip, "remote_port": 443},
    }
    before = _read_audit_count()

    async def run():
        print("[NET] Alert JSON:\n", json.dumps(alert, indent=2))
        pb_path = await generate_playbook(alert)
        print(f"[NET] Generated playbook path: {pb_path}")
        with open(pb_path, 'r', encoding='utf-8') as yf:
            print("[NET] Generated Playbook YAML:\n" + yf.read())
        pb = parse_playbook_yaml(pb_path)
        print("[NET] Parsed Playbook Steps:")
        for s in pb.steps:
            print("   -", s.name, s.action, s.params)
        res = await execute_playbook(pb, alert)
        print("[NET] Execution Result success=", res.success, "rolled_back=", res.rolled_back)
        for st in res.steps:
            print("   [STEP]", st)
        return res

    res = asyncio.get_event_loop().run_until_complete(run())
    assert res.success is True
    after = _read_audit_count()
    assert after >= before + 1
    # Cleanup firewall rules created by action (best effort)
    if os.name == "nt":
        for name in (f"Playbook-Block-IP-In-{test_ip}", f"Playbook-Block-IP-Out-{test_ip}"):
            subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"], capture_output=True)
