import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from redis.asyncio import Redis
from .logger import logger

# Thin wrapper around redis lock/cooldown using SET NX with TTL.

_client: Optional[Redis] = None


def get_redis(url: str) -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(url, decode_responses=True)
    return _client


async def close_redis():
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@asynccontextmanager
async def acquire_lock(r: Redis, key: str, ttl: int):
    token = f"{asyncio.get_running_loop().time()}"
    try:
        ok = await r.set(name=f"lock:{key}", value=token, nx=True, ex=ttl)
    except Exception as e:
        # Graceful degrade: if Redis not available or auth fails, proceed without a distributed lock
        logger.warning(f"Redis lock unavailable ({e}); proceeding without lock for {key}")
        ok = True
    try:
        if not ok:
            yield False
            return
        yield True
    finally:
        # Best-effort release (no Lua check token for brevity)
        try:
            await r.delete(f"lock:{key}")
        except Exception:
            pass


async def check_and_set_cooldown(r: Redis, key: str, ttl: int) -> bool:
    # Returns False if under cooldown; True if cooldown set now
    try:
        setnx = await r.set(name=f"cooldown:{key}", value="1", nx=True, ex=ttl)
        return bool(setnx)
    except Exception as e:
        # Graceful degrade: if Redis fails, allow execution and log
        logger.warning(f"Redis cooldown unavailable ({e}); allowing execution for {key}")
        return True
