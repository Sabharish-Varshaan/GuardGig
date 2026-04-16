import os

import redis


def _build_redis_client() -> redis.Redis:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
            health_check_interval=30,
        )

    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=int(os.getenv("REDIS_DB", 0)),
        password=os.getenv("REDIS_PASSWORD") or None,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
        health_check_interval=30,
    )


redis_client = _build_redis_client()