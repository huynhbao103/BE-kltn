import uuid
import json
import time
from typing import Dict, Any

# Lưu session trong memory (tạm thời thay vì Redis)
session_store: Dict[str, Dict[str, Any]] = {}
session_timestamps: Dict[str, float] = {}

def save_state_to_redis(state: dict, ttl: int = 3600) -> str:
    session_id = str(uuid.uuid4())
    session_store[session_id] = state
    session_timestamps[session_id] = time.time() + ttl
    return session_id

def load_state_from_redis(session_id: str) -> dict:
    if session_id not in session_store:
        raise Exception("Session expired or not found")
    
    # Kiểm tra TTL
    if time.time() > session_timestamps.get(session_id, 0):
        # Xóa session hết hạn
        del session_store[session_id]
        if session_id in session_timestamps:
            del session_timestamps[session_id]
        raise Exception("Session expired")
    
    return session_store[session_id]

# Hàm cleanup để xóa session hết hạn (có thể gọi định kỳ)
def cleanup_expired_sessions():
    current_time = time.time()
    expired_sessions = [
        session_id for session_id, timestamp in session_timestamps.items()
        if current_time > timestamp
    ]
    for session_id in expired_sessions:
        if session_id in session_store:
            del session_store[session_id]
        if session_id in session_timestamps:
            del session_timestamps[session_id]