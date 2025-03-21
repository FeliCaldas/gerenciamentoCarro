import json
import os
from datetime import datetime, timedelta

CACHE_DIR = "cache"
CACHE_DURATION = timedelta(hours=24)

def ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_path(key):
    ensure_cache_dir()
    return os.path.join(CACHE_DIR, f"{key}.json")

def save_to_cache(key, data):
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    with open(get_cache_path(key), 'w') as f:
        json.dump(cache_data, f)

def load_from_cache(key):
    try:
        with open(get_cache_path(key), 'r') as f:
            cache_data = json.load(f)
            cache_time = datetime.fromisoformat(cache_data['timestamp'])
            
            if datetime.now() - cache_time <= CACHE_DURATION:
                return cache_data['data']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None

def clear_cache():
    if os.path.exists(CACHE_DIR):
        for file in os.listdir(CACHE_DIR):
            if file.endswith('.json'):
                os.remove(os.path.join(CACHE_DIR, file))
