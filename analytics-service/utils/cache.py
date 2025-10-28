import redis
import os
import json
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.getenv("REDIS_PORT")), username=os.getenv("REDIS_USER"), password=os.getenv("REDIS_PASSWORD"), db=int(os.getenv("REDIS_DB", 0)), decode_responses=True, ssl=True)

def get_counter(agent_id: str, key: str):
    return int(redis_client.get(f"counter:{agent_id}:{key}") or 0)

def incr_counter(agent_id: str, key: str):
    return redis_client.incr(f"counter:{agent_id}:{key}")