from app.services.redis_client import redis_client

def persona_key(user, topic):
    return f"persona:{user}:{topic.lower().replace(' ', '_')}"

def get_persona(user, topic):
    return redis_client.get(persona_key(user, topic))

def set_persona(user, topic, persona):
    redis_client.set(persona_key(user, topic), persona)