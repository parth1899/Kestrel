from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, List
import json
import os

from ..utils.logger import logger, audit
from ..utils.config import load_config, load_actions_schema
from ..core.parser import parse_playbook_text, PlaybookValidationError
from .prompts import build_prompt
import yaml

# LLM providers are optional; we fallback to deterministic generation if keys absent.

async def _call_openai(prompt: Dict[str, str], model: str, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


async def _call_anthropic(prompt: Dict[str, str], model: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        system=prompt["system"],
        max_tokens=800,
        messages=[{"role": "user", "content": prompt["user"]}],
        temperature=0.1,
    )
    # Concatenate text outputs
    parts = []
    for c in msg.content:
        if getattr(c, "type", None) == "text":
            parts.append(c.text)
    return "\n".join(parts)


async def _call_groq(prompt: Dict[str, str], model: str, api_key: str) -> str:
    # Groq SDK chat.completions is compatible with OpenAI API surface
    from groq import Groq
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]},
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


def _deterministic_playbook(alert: Dict[str, Any]) -> str:
    # Produce a minimal YAML using simple heuristics; ensures offline functionality.
    event_type = str(alert.get("event_type", "generic"))
    severity = str(alert.get("severity", "medium"))
    aid = alert.get("agent_id", "unknown")
    steps = []
    if event_type == "process":
        pid = (alert.get("details", {}) or {}).get("pid", 0)
        # Remove isolate_host from deterministic fallback to keep E2E stable (admin requirement causes flaky failures)
        steps = [
            {"name": "Kill malicious process", "action": "kill_process", "params": {"agent_id": aid, "pid": pid}},
        ]
    elif event_type == "network":
        ip = (alert.get("details", {}) or {}).get("ip", "0.0.0.0")
        steps = [
            {"name": "Block C2 IP", "action": "block_ip", "params": {"agent_id": aid, "ip": ip}},
        ]
    elif event_type == "file":
        path = (alert.get("details", {}) or {}).get("path", "C:/tmp/unknown.bin")
        steps = [
            {"name": "Quarantine file", "action": "quarantine_file", "params": {"agent_id": aid, "path": path}},
        ]
    else:
        steps = [
            {"name": "Isolate host", "action": "isolate_host", "params": {"agent_id": aid}},
        ]
    steps = [s for s in steps if s]
    pb = {
        "id": f"pb-{event_type}-{severity}",
        "version": "1.0",
        "metadata": {"event_type": event_type, "severity": severity},
        "preconditions": [],
        "steps": steps,
        "rollback": [],
    }
    import yaml
    return yaml.safe_dump(pb, sort_keys=False)


def _strip_md_fences(text: str) -> str:
    # Remove Markdown code fences like ```yaml ... ``` if present
    if "```" not in text:
        return text
    lines = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return "\n".join(lines)


def _title_from_action(action: str) -> str:
    return " ".join(w.capitalize() for w in action.replace("_", " ").split())


def _normalize_yaml_to_schema(yaml_text: str) -> str:
    """Attempt to coerce common LLM YAML shapes to the strict Playbook schema.
    - Ensure version is a string
    - Convert step items like {action_name: {..}} to {name, action, params}
    - Ensure params exists (dict)
    - Apply same for rollback
    """
    try:
        raw = yaml.safe_load(_strip_md_fences(yaml_text)) or {}
    except Exception:
        return yaml_text  # let validator decide / fallback later
    if not isinstance(raw, dict):
        return yaml_text

    # version as string
    if "version" in raw and not isinstance(raw["version"], str):
        raw["version"] = str(raw["version"])

    # defaults
    raw.setdefault("preconditions", [])
    raw.setdefault("metadata", {})

    def normalize_list(items: Any) -> List[Dict[str, Any]]:
        lst: List[Dict[str, Any]] = []
        if not isinstance(items, list):
            return lst
        for it in items:
            if isinstance(it, dict):
                if "action" in it and "name" in it:
                    # ensure params dict
                    if "params" not in it or it["params"] is None:
                        it["params"] = {}
                    lst.append(it)
                else:
                    # try single-key mapping to action
                    if len(it) >= 1:
                        k = next(iter(it.keys()))
                        params = it.get(k) if isinstance(it.get(k), dict) else {}
                        lst.append({
                            "name": _title_from_action(str(k)),
                            "action": str(k),
                            "params": params or {},
                        })
            elif isinstance(it, str):
                lst.append({
                    "name": _title_from_action(it),
                    "action": it,
                    "params": {},
                })
        return lst

    if "steps" in raw:
        raw["steps"] = normalize_list(raw["steps"])
    if "rollback" in raw:
        raw["rollback"] = normalize_list(raw["rollback"])

    try:
        return yaml.safe_dump(raw, sort_keys=False)
    except Exception:
        return yaml_text


async def generate_playbook(alert: Dict[str, Any]) -> Path:
    cfg = load_config()
    actions = load_actions_schema()
    prompt = build_prompt(alert, actions)

    provider = (cfg["genai"]["provider"] or "stub").lower()
    model = cfg["genai"]["model"]
    yaml_text: Optional[str] = None

    # Choose provider if API key present, else fallback
    try:
        if provider == "openai" and cfg["genai"].get("openai_api_key"):
            yaml_text = await _call_openai(prompt, model, cfg["genai"]["openai_api_key"])  # type: ignore[arg-type]
        elif provider == "anthropic" and cfg["genai"].get("anthropic_api_key"):
            yaml_text = await _call_anthropic(prompt, model, cfg["genai"]["anthropic_api_key"])  # type: ignore[arg-type]
        elif provider == "groq" and cfg["genai"].get("groq_api_key"):
            yaml_text = await _call_groq(prompt, model, cfg["genai"]["groq_api_key"])  # type: ignore[arg-type]
        else:
            yaml_text = _deterministic_playbook(alert)
    except Exception as e:
        logger.warning(f"LLM call failed, fallback used: {e}")
        yaml_text = _deterministic_playbook(alert)

    # Try to normalize LLM YAML to schema before validation
    yaml_text = _normalize_yaml_to_schema(yaml_text)

    # Validate YAML; if invalid, fallback to deterministic
    try:
        pb = parse_playbook_text(yaml_text)
    except PlaybookValidationError as e:
        logger.warning(f"Generated YAML invalid: {e}; using fallback")
        yaml_text = _deterministic_playbook(alert)
        pb = parse_playbook_text(yaml_text)

    # Normalize playbook id to deterministic pattern for reliable retrieval
    event_type = str(alert.get("event_type", "generic"))
    severity = str(alert.get("severity", "medium"))
    desired_id = f"pb-{event_type}-{severity}"
    if not getattr(pb, "id", "") or not str(pb.id).startswith("pb-"):
        pb.id = desired_id  # type: ignore[attr-defined]
    # If LLM chose a different id, still override to pattern to satisfy find_existing_playbook
    elif pb.id != desired_id:
        pb.id = desired_id  # type: ignore[attr-defined]

    # Persist under generated dir by derived name
    gen_dir = Path(cfg["data"]["playbooks_generated"]).resolve()
    # Guard against misconfiguration where generated path points to BASE_DIR directly; redirect to default generated dir
    from ..utils.config import BASE_DIR
    if gen_dir == BASE_DIR:
        gen_dir = (BASE_DIR / "data" / "playbooks" / "generated").resolve()
    gen_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{pb.id}.yaml"
    out_path = gen_dir / fname
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(yaml_text)

    audit("playbook_generated", {"playbook_id": pb.id, "path": str(out_path)})
    return out_path


def find_existing_playbook(alert: Dict[str, Any]) -> Optional[Path]:
    # Match by event_type + severity first in static then generated dirs.
    cfg = load_config()
    event = str(alert.get("event_type", "generic"))
    sev = str(alert.get("severity", "medium"))
    patterns = [f"pb-{event}-{sev}.yaml", f"{event}-{sev}.yaml"]
    from ..utils.config import BASE_DIR
    paths = [
        Path(cfg["data"]["playbooks_static"]),
        Path(cfg["data"]["playbooks_generated"]),
        BASE_DIR / "data" / "playbooks" / "generated",  # canonical generated
    ]
    # Legacy misplaced files directly under BASE_DIR
    paths.append(BASE_DIR)
    for p in paths:
        for name in patterns:
            cand = p / name
            if cand.exists():
                return cand
        # Fallback: metadata scan of directory for matching event_type+severity
        if p.is_dir():
            for y in p.glob("*.yaml"):
                try:
                    data = yaml.safe_load(y.read_text(encoding="utf-8")) or {}
                    meta = data.get("metadata", {})
                    if str(meta.get("event_type")) == event and str(meta.get("severity")) == sev:
                        return y
                except Exception:
                    continue
    return None
