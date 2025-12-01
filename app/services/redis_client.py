import os
import redis
from urllib.parse import urlparse

from app.core.config import REDIS_URL


class RedisClient:
    def __init__(self, url: str | None = None, namespace: str = "app"):
        self.namespace = namespace
        self.url = url or REDIS_URL

        if not self.url:
            raise RuntimeError("❌ REDIS_URL missing from .env")

        parsed = urlparse(self.url)

        self.client = redis.Redis(
            host=parsed.hostname,
            port=parsed.port,
            password=parsed.password,
            username=parsed.username,
            db=int(parsed.path.replace("/", "")) if parsed.path else 0,
            decode_responses=True,
            ssl=self.url.startswith("rediss://")  # 🔥 auto SSL if needed
        )

    # -------------------------------------------------------------
    # Base namespaced key generator
    # -------------------------------------------------------------
    def key(self, name: str) -> str:
        return f"{self.namespace}:{name}"

    # -------------------------------------------------------------
    # Simple get/set
    # -------------------------------------------------------------
    def get(self, name: str):
        return self.client.get(self.key(name))

    def set(self, name: str, value: str, ttl: int | None = None):
        return self.client.set(self.key(name), value, ex=ttl)

    # -------------------------------------------------------------
    # JSON helpers
    # -------------------------------------------------------------
    def get_json(self, name: str):
        import json
        v = self.get(name)
        return json.loads(v) if v else None

    def set_json(self, name: str, data, ttl: int | None = None):
        import json
        return self.set(name, json.dumps(data), ttl)

    # hashing operations
    def hset(self, name: str, mapping: dict):
        return self.client.hset(self.key(name), mapping=mapping)

    def hgetall(self, name: str) -> dict:
        return self.client.hgetall(self.key(name))

    def delete(self, name: str):
        return self.client.delete(self.key(name))


# 🔥 Global client instance (fully reusable in ANY app)
redis_client = RedisClient(namespace="ordo")
