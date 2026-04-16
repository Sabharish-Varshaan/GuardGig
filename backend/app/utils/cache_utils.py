import json

from app.core.redis_client import redis_client


CACHE_TTL = 900  # 15 minutes


def get_cache(key: str):
    try:
        data = redis_client.get(key)
        if data:
            print(f"[CACHE HIT] {key}")
            return json.loads(data)
        print(f"[CACHE MISS] {key}")
        return None
    except Exception as exc:
        print(f"[CACHE ERROR GET] {exc}")
        return None


def set_cache(key: str, value):
    try:
        redis_client.setex(
            key,
            CACHE_TTL,
            json.dumps(value),
        )
    except Exception as exc:
        print(f"[CACHE ERROR SET] {exc}")