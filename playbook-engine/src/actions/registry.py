from __future__ import annotations
import asyncio
import ctypes
import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Awaitable, Callable

from ..utils.logger import logger
from ..utils.config import load_config

# Registry of available actions. Functions are async and accept (params) only.

ActionFunc = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]

_actions: Dict[str, ActionFunc] = {}
_rollbacks: Dict[str, ActionFunc] = {}


def register(name: str, func: ActionFunc, rollback: ActionFunc | None = None) -> None:
    _actions[name] = func
    if rollback:
        _rollbacks[name] = rollback


def get_action(name: str) -> ActionFunc:
    if name not in _actions:
        raise KeyError(f"Action not registered: {name}")
    return _actions[name]


def get_rollback(name: str) -> ActionFunc | None:
    return _rollbacks.get(name)


# ---- helpers ----
def _is_windows() -> bool:
    return os.name == "nt"


def _is_admin_windows() -> bool:
    if not _is_windows():
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


async def _run_exec(*args: str) -> Dict[str, Any]:
    """Run a subprocess and return code/stdout/stderr; raise on non-zero code."""
    logger.info(f"Executing command: {' '.join(args)}")
    try:
        # Use sync subprocess.run in executor to avoid Windows asyncio issues
        import subprocess
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False
            )
        )
        logger.info(f"Process completed")
        code = result.returncode
        out = result.stdout.strip() if result.stdout else ""
        err = result.stderr.strip() if result.stderr else ""
        logger.info(f"Command completed: code={code}, stdout={repr(out)}, stderr={repr(err)}")
        if code != 0:
            error_msg = f"command failed (code={code}): {' '.join(args)} | stdout: {out} | stderr: {err}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        return {"code": code, "stdout": out, "stderr": err}
    except Exception as e:
        logger.error(f"Exception in _run_exec: {type(e).__name__}: {e}")
        raise


def _quarantine_dir() -> Path:
    cfg = load_config()
    q = cfg.get("data", {}).get("quarantine") or str(Path(cfg["data"]["base_dir"]) / "quarantine")
    p = Path(q)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _quarantine_path(orig: str) -> Path:
    o = Path(orig)
    h = hashlib.sha1(str(o).encode("utf-8")).hexdigest()[:8]
    return _quarantine_dir() / f"{o.name}.{h}.quar"


# --- Concrete local action implementations (Windows-first) ---

async def action_isolate_host(params: Dict[str, Any]) -> Dict[str, Any]:
    if not _is_windows():
        raise NotImplementedError("isolate_host is implemented for Windows only in local mode")
    if not _is_admin_windows():
        raise PermissionError("Administrator privileges required for isolate_host")
    # Make idempotent by deleting existing rules first
    try:
        await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", "name=Playbook-Isolate-In")
    except Exception:
        pass
    try:
        await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", "name=Playbook-Isolate-Out")
    except Exception:
        pass
    add_in = await _run_exec(
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=Playbook-Isolate-In", "dir=in", "action=block", "protocol=any"
    )
    add_out = await _run_exec(
        "netsh", "advfirewall", "firewall", "add", "rule",
        "name=Playbook-Isolate-Out", "dir=out", "action=block", "protocol=any"
    )
    return {"in": add_in, "out": add_out}


async def rollback_isolate_host(params: Dict[str, Any]) -> Dict[str, Any]:
    if not _is_windows():
        return {"status": "skipped", "reason": "non-windows"}
    if not _is_admin_windows():
        raise PermissionError("Administrator privileges required for rollback isolate_host")
    r1 = await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", "name=Playbook-Isolate-In")
    r2 = await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", "name=Playbook-Isolate-Out")
    return {"deleted": [r1, r2]}


async def action_kill_process(params: Dict[str, Any]) -> Dict[str, Any]:
    if not _is_windows():
        raise NotImplementedError("kill_process is implemented for Windows only in local mode")
    pid = int(params["pid"])
    logger.info(f"Attempting to kill process PID={pid}")
    # Force terminate the PID; treat 'not found' as already terminated (idempotent)
    try:
        res = await _run_exec("taskkill", "/PID", str(pid), "/F")
        logger.info(f"Successfully killed process PID={pid}")
        return {"status": "killed", "pid": pid, **res}
    except RuntimeError as e:
        msg = str(e).lower()
        logger.warning(f"RuntimeError killing PID {pid}: {msg}")
        if "not found" in msg or "process \"" in msg:
            logger.info(f"Process {pid} already terminated")
            return {"status": "already_terminated", "pid": pid}
        raise
    except Exception as e:
        logger.error(f"Unexpected error killing PID {pid}: {type(e).__name__}: {e}")
        raise


async def rollback_kill_process(params: Dict[str, Any]) -> Dict[str, Any]:
    # No rollback possible for a killed process
    return {"status": "noop", "note": "cannot rollback kill_process"}


async def action_block_ip(params: Dict[str, Any]) -> Dict[str, Any]:
    if not _is_windows():
        raise NotImplementedError("block_ip is implemented for Windows only in local mode")
    if not _is_admin_windows():
        raise PermissionError("Administrator privileges required for block_ip")
    ip = str(params["ip"]).strip()
    name_in = f"Playbook-Block-IP-In-{ip}"
    name_out = f"Playbook-Block-IP-Out-{ip}"
    # Delete if exists to be idempotent
    for n in (name_in, name_out):
        try:
            await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", f"name={n}")
        except Exception:
            pass
    r_in = await _run_exec(
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={name_in}", "dir=in", "action=block", f"remoteip={ip}", "protocol=any"
    )
    r_out = await _run_exec(
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={name_out}", "dir=out", "action=block", f"remoteip={ip}", "protocol=any"
    )
    return {"in": r_in, "out": r_out}


async def rollback_block_ip(params: Dict[str, Any]) -> Dict[str, Any]:
    if not _is_windows():
        return {"status": "skipped", "reason": "non-windows"}
    if not _is_admin_windows():
        raise PermissionError("Administrator privileges required for rollback block_ip")
    ip = str(params["ip"]).strip()
    name_in = f"Playbook-Block-IP-In-{ip}"
    name_out = f"Playbook-Block-IP-Out-{ip}"
    r1 = await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", f"name={name_in}")
    r2 = await _run_exec("netsh", "advfirewall", "firewall", "delete", "rule", f"name={name_out}")
    return {"deleted": [r1, r2]}


async def action_quarantine_file(params: Dict[str, Any]) -> Dict[str, Any]:
    src = Path(str(params["path"]))
    if not src.exists():
        raise FileNotFoundError(f"file not found: {src}")
    dst = _quarantine_path(str(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    return {"quarantined_to": str(dst)}


async def rollback_quarantine_file(params: Dict[str, Any]) -> Dict[str, Any]:
    orig = Path(str(params["path"]))
    q = _quarantine_path(str(orig))
    if not q.exists():
        return {"status": "skipped", "reason": "not_in_quarantine"}
    orig.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(q), str(orig))
    return {"restored": str(orig)}


# Register actions at import time
register("isolate_host", action_isolate_host, rollback_isolate_host)
register("kill_process", action_kill_process, rollback_kill_process)
register("block_ip", action_block_ip, rollback_block_ip)
register("quarantine_file", action_quarantine_file, rollback_quarantine_file)
