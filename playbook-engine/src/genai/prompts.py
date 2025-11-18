# Prompt templates for LLM playbook generation. Kept simple and deterministic.

BASE_SYSTEM = (
    "You are a security automation architect. Generate a YAML playbook with keys: "
    "id, version, metadata, preconditions, steps, rollback. Steps must be concise."
)

PLAYBOOK_INSTRUCTIONS = (
    "Use only allowed actions from the provided catalog. Ensure required params exist. "
    "Prefer minimal steps that mitigate the threat."
)


def build_prompt(alert: dict, actions_catalog: dict) -> dict:
    # Returns dict with role/content entries for providers supporting chat format.
    actions_text = "\n".join(
        f"- {name}: required_params={info.get('params', [])}" for name, info in (actions_catalog.get("actions") or {}).items()
    )
    user = (
        "Alert summary:\n"
        f"event_type: {alert.get('event_type')}\n"
        f"severity: {alert.get('severity')}\n"
        f"agent_id: {alert.get('agent_id')}\n"
        f"details: {alert.get('details', {})}\n\n"
        "Allowed actions:\n" + actions_text + "\n\n"
        "Return ONLY YAML, no code fences."
    )
    return {
        "system": BASE_SYSTEM,
        "user": f"{PLAYBOOK_INSTRUCTIONS}\n\n{user}"
    }
