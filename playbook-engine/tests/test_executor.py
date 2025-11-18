import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
from src.core.parser import parse_playbook_text
from src.core.executor import execute_playbook


def test_execute_quarantine(tmp_path):
    # Create a sample file to quarantine
    f = tmp_path / "malicious.bin"
    f.write_text("dummy")
    # Normalize path once to avoid complex escaping in f-string
    path_str = str(f).replace('\\', '/')
    pb_text = f"""
id: pb-test
version: "1.0"
metadata: {{event_type: file, severity: high}}
preconditions: []
steps:
  - name: Quarantine
    action: quarantine_file
    params: {{path: "{path_str}"}}
rollback: []
"""
    pb = parse_playbook_text(pb_text)
    alert = {"event_type": "file", "severity": "high", "event_id": "e-1"}

    async def run():
        return await execute_playbook(pb, alert)

    res = asyncio.get_event_loop().run_until_complete(run())
    assert res.success is True
    assert any(s.get("status") == "ok" for s in res.steps)
