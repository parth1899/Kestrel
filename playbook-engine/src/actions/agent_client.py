"""
Deprecated: Agent HTTP client removed. Local mode executes actions on the host directly.

This module is intentionally left as a stub to avoid import errors in any stale environments.
Do not use.
"""

class AgentClient:  # pragma: no cover
    def __init__(self, *_, **__):
        raise ImportError("AgentClient has been removed. Actions run locally in 'local' mode.")
