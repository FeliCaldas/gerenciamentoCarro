import json
import os
from datetime import datetime, timedelta

CACHE_DIR = "cache"
VEHICLE_CACHE_DURATION = timedelta(days=60)  # Cache de veículos: 2 meses
FIPE_CACHE_DURATION = timedelta(hours=24)    # Cache FIPE: 24 horas

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
            
            # Define a duração do cache baseado no prefixo da chave
            if key.startswith('fipe_'):
                duration = FIPE_CACHE_DURATION
            else:
                duration = VEHICLE_CACHE_DURATION
                
            if datetime.now() - cache_time <= duration:
                return cache_data['data']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return None

def clear_cache():
    if os.path.exists(CACHE_DIR):
        for file in os.listdir(CACHE_DIR):
            if file.endswith('.json'):
                os.remove(os.path.join(CACHE_DIR, file))

def save_vehicles_to_cache(vehicles_data):
    """Salva veículos no cache"""
    save_to_cache('vehicles', vehicles_data)

def load_vehicles_from_cache():
    """Carrega veículos do cache"""
    return load_from_cache('vehicles')

def update_vehicle_in_cache(vehicle_id, vehicle_data):
    """Atualiza um veículo específico no cache"""
    vehicles = load_vehicles_from_cache()
    if vehicles:
        vehicles = [v for v in vehicles if v['id'] != vehicle_id]
        vehicles.append(vehicle_data)
        save_vehicles_to_cache(vehicles)

def delete_vehicle_from_cache(vehicle_id):
    """Remove um veículo do cache"""
    vehicles = load_vehicles_from_cache()
    if vehicles:
        vehicles = [v for v in vehicles if v['id'] != vehicle_id]
        save_vehicles_to_cache(vehicles)
