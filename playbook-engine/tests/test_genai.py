import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import asyncio
from src.genai.generator import generate_playbook, find_existing_playbook
from src.utils.config import load_config


def test_genai_generation(tmp_path, monkeypatch):
    # Force provider to stub via env; but our config loader caches, so rely on default 'stub'
    alert = {"event_type": "file", "severity": "medium", "agent_id": "a-2", "details": {"path": "C:/tmp/mal.doc"}}

    async def run():
        return await generate_playbook(alert)

    p = asyncio.get_event_loop().run_until_complete(run())
    assert p.exists()
    found = find_existing_playbook(alert)
    assert found is not None
