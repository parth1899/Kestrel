import os
import yaml
from pathlib import Path
from functools import lru_cache
from typing import Any, Dict

# Simple YAML-based config loader with env overrides.

BASE_DIR = Path(__file__).resolve().parents[2]
# print(BASE_DIR)
CONFIG_DIR = BASE_DIR / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
ACTIONS_SCHEMA_PATH = CONFIG_DIR / "actions.yaml"


def _read_yaml(p: Path) -> Dict[str, Any]:
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_config() -> Dict[str, Any]:
    cfg = {
        "data": {
            "base_dir": str(BASE_DIR / "data"),
            "playbooks_static": str(BASE_DIR / "data" / "playbooks" / "static"),
            # default generated playbooks under data/playbooks/playbooks_generated
            "playbooks_generated": str(BASE_DIR / "data" / "playbooks" / "playbooks_generated"),
            # default execution JSON artifacts under data/executions
            "executions": str(BASE_DIR / "data" / "executions"),
            "quarantine": str(BASE_DIR / "data" / "quarantine"),
        },
        "messaging": {
            "enabled": True,
            "rabbitmq_url": os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/"),
            "exchange": os.getenv("RABBITMQ_EXCHANGE", "alerts"),
            "routing_key": "alerts.*",
            "file_input": os.getenv("FILE_INPUT_PATH", ""),
        },
        "redis": {
            "url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "lock_ttl": 60,
            "cooldown_ttl": int(os.getenv("REDIS_COOLDOWN_TTL", "300")),
            "cooldown_enabled": os.getenv("REDIS_COOLDOWN_ENABLED", "true").lower() in ("1","true","yes"),
        },
        "genai": {
            "provider": os.getenv("GENAI_PROVIDER", "openai"),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "groq_api_key": os.getenv("GROQ_API_KEY", "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"),
            "model": os.getenv("GENAI_MODEL", "gpt-4o-mini"),
        },
        "execution": {
            "mode": os.getenv("EXECUTION_MODE", "local"),
            "allow_isolate_host": os.getenv("ALLOW_ISOLATE_HOST", "false").lower() in ("1","true","yes"),
            "quarantine_dir": os.getenv("QUARANTINE_DIR", str(BASE_DIR / "data" / "quarantine")),
            "persist": os.getenv("EXECUTIONS_PERSIST", "true").lower() in ("1","true","yes"),
        },
        "actions": {
            "mode": os.getenv("ACTIONS_MODE", "local"),
        },
    }
    file_cfg = _read_yaml(DEFAULT_CONFIG_PATH)
    # Merge shallowly (good enough for this app). File overrides defaults.
    for k, v in file_cfg.items():
        if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
            cfg[k].update(v)
        else:
            cfg[k] = v

    # Normalize any paths in cfg["data"]: if a file config left them empty or relative,
    # resolve them to sensible defaults under BASE_DIR. This prevents users placing
    # empty strings in config.yaml from causing writes into the repository root.
    default_data = {
        "base_dir": str(BASE_DIR / "data"),
        "playbooks_static": str(BASE_DIR / "data" / "playbooks" / "static"),
        "playbooks_generated": str(BASE_DIR / "data" / "pgptlaybooks" / "playbooks_generated"),
        "executions": str(BASE_DIR / "data" / "executions"),
        "quarantine": str(BASE_DIR / "data" / "quarantine"),
    }
    # Ensure section exists
    cfg.setdefault("data", {})
    for key, dflt in default_data.items():
        val = cfg["data"].get(key)
        # If user left an empty string or null in config.yaml, fallback to default
        if not val:
            cfg["data"][key] = dflt
            continue
        p = Path(str(val))
        # If path is not absolute, resolve relative to BASE_DIR
        if not p.is_absolute():
            p = (BASE_DIR / p).resolve()
        cfg["data"][key] = str(p)

    # Defensive: ensure required sections exist even if file overrides emptied them
    cfg.setdefault("execution", {
        "mode": "local",
        "allow_isolate_host": False,
        "quarantine_dir": str(BASE_DIR / "data" / "quarantine"),
        "persist": True,
    })

    # Ensure directories exist
    for dkey in ("base_dir", "playbooks_static", "playbooks_generated", "executions", "quarantine"):
        Path(cfg["data"][dkey]).mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "data" / "alerts_log.json").touch(exist_ok=True)
    return cfg


def load_actions_schema() -> Dict[str, Any]:
    """Load actions.yaml which declares available actions and required params."""
    return _read_yaml(ACTIONS_SCHEMA_PATH) or {"actions": {}}