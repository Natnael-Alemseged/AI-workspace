# app/services/memory_service.py

from supermemory import Supermemory
from datetime import datetime
from app.core.config import SUPERMEMORY_API_KEY

supermemory = Supermemory(api_key=SUPERMEMORY_API_KEY)

def add_memory(user_id: str, prompt: str, response: str):
    supermemory.memories.add(
        container_tag=user_id,
        content=f"User: {prompt}\nAssistant: {response}",
        metadata={"timestamp": datetime.utcnow().isoformat()}
    )

def get_relevant_memories(user_id: str, query: str, limit: int = 3):
    result = supermemory.search.memories(q=query, container_tag=user_id, limit=limit)
    return [m.memory for m in result.results] if result.results else []
