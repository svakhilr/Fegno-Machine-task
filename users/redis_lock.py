import uuid
from contextlib import contextmanager
import redis
from django.conf import settings

# Redis client (redis-py handles connection pooling automatically)
r = redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)


def get_redis_client():
    return r


def _slot_key(resource_id, date, start_time):
    return f"lock:slot:{resource_id}:{date}:{start_time}"


def acquire_slot_lock(resource_id, date, start_time, user_id=None, expire_seconds=180):
    """Atomically acquire slot lock. Returns (True, token) or (False, None)."""
    key = _slot_key(resource_id, date, start_time)
    token = f"{user_id or 'anon'}:{uuid.uuid4().hex}"
    acquired = r.set(key, token, nx=True, ex=expire_seconds)
    return (True, token) if acquired else (False, None)


def release_slot_lock(resource_id, date, start_time, token):
    """Release slot lock only if the token matches."""
    key = _slot_key(resource_id, date, start_time)
    if token and r.get(key) == str(token):
        return bool(r.delete(key))
    return False


def is_slot_locked(resource_id, date, start_time):
    """Check if slot is currently locked."""
    return bool(r.exists(_slot_key(resource_id, date, start_time)))


@contextmanager
def slot_lock(resource_id, date, start_time, user_id=None, expire_seconds=10):
    """Context manager for acquiring and safely releasing a slot lock."""
    acquired, token = acquire_slot_lock(resource_id, date, start_time, user_id, expire_seconds)
    try:
        yield acquired
    finally:
        if acquired and token:
            release_slot_lock(resource_id, date, start_time, token)
