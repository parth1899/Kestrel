from __future__ import annotations
from typing import Any, Dict, List

# Tiny precondition evaluator. Supports simple equals/contains expressions.

class Preconditions:
    @staticmethod
    def evaluate(preconditions: List[Dict[str, Any]], context: Dict[str, Any]) -> bool:
        # Each precondition is a dict like { equals: {path: "payload.severity", value: "high"} }
        for cond in preconditions:
            if not isinstance(cond, dict):
                return False
            if "equals" in cond:
                path = cond["equals"].get("path")
                val = cond["equals"].get("value")
                if Preconditions._get(context, path) != val:
                    return False
                continue
            if "contains" in cond:
                path = cond["contains"].get("path")
                val = cond["contains"].get("value")
                container = Preconditions._get(context, path)
                try:
                    if val not in container:
                        return False
                except Exception:
                    return False
                continue
            # Fallback: treat plain key:value pairs as equality against alert root fields
            alert_ctx = context.get("alert", {}) if isinstance(context.get("alert"), dict) else {}
            for k, v in cond.items():
                if alert_ctx.get(k) != v:
                    return False
        return True

    @staticmethod
    def _get(obj: Dict[str, Any], dotted: str) -> Any:
        cur: Any = obj
        for part in dotted.split("."):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                return None
        return cur
