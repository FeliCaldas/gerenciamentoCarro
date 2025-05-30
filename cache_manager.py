from datetime import datetime, timedelta
import json
import os
from logger import setup_logger

# Configuração dos loggers
logger = setup_logger('cache_manager')

CACHE_DIR = "cache"
VEHICLE_CACHE_DURATION = timedelta(days=60)  # Cache de veículos: 2 meses
FIPE_CACHE_DURATION = timedelta(hours=24)    # Cache FIPE: 24 horas

# Adicionar constante para arquivo de backup
BACKUP_FILE = os.path.join(CACHE_DIR, 'persistent_data.json')

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
    """Limpa todo o cache"""
    try:
        if os.path.exists(CACHE_DIR):
            count = 0
            for file in os.listdir(CACHE_DIR):
                if file.endswith('.json'):
                    os.remove(os.path.join(CACHE_DIR, file))
                    count += 1
            logger.info(f"Cache limpo: {count} arquivo(s) removido(s)")
    except Exception as e:
        logger.error(f"Erro ao limpar cache: {e}")

def save_persistent_data(data):
    """Salva dados de forma persistente"""
    ensure_cache_dir()
    try:
        with open(BACKUP_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("Dados persistentes salvos com sucesso")
    except Exception as e:
        logger.error(f"Erro ao salvar dados persistentes: {e}")

def load_persistent_data():
    """Carrega dados persistentes"""
    try:
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'r') as f:
                data = json.load(f)
            logger.info("Dados persistentes carregados com sucesso")
            return data
    except Exception as e:
        logger.error(f"Erro ao carregar dados persistentes: {e}")
    return None

def save_vehicles_to_cache(vehicles_data):
    """Salva veículos no cache e no backup persistente"""
    try:
        save_to_cache('vehicles', vehicles_data)
        save_persistent_data({'vehicles': vehicles_data}) # Adiciona persistência
        logger.info(f"Cache e backup de veículos atualizados com {len(vehicles_data)} veículos")
    except Exception as e:
        logger.error(f"Erro ao salvar cache de veículos: {e}")

def load_vehicles_from_cache():
    """Carrega veículos do cache ou do backup persistente"""
    try:
        # Tenta carregar do cache primeiro
        data = load_from_cache('vehicles')
        if data is not None:
            logger.info("Cache de veículos carregado com sucesso")
            return data
            
        # Se não encontrar no cache, tenta carregar do backup
        persistent_data = load_persistent_data()
        if persistent_data and 'vehicles' in persistent_data:
            logger.info("Veículos carregados do backup persistente")
            return persistent_data['vehicles']
            
        logger.debug("Nenhum dado encontrado (cache ou persistente)")
        return None
    except Exception as e:
        logger.error(f"Erro ao carregar veículos: {e}")
        return None

def update_vehicle_in_cache(vehicle_id, vehicle_data):
    """Atualiza um veículo específico no cache"""
    try:
        vehicles = load_vehicles_from_cache()
        if vehicles:
            vehicles = [v for v in vehicles if v['id'] != vehicle_id]
            vehicles.append(vehicle_data)
            save_vehicles_to_cache(vehicles)
            logger.info(f"Veículo {vehicle_id} atualizado no cache")
    except Exception as e:
        logger.error(f"Erro ao atualizar veículo {vehicle_id} no cache: {e}")

def delete_vehicle_from_cache(vehicle_id):
    """Remove um veículo do cache"""
    try:
        vehicles = load_vehicles_from_cache()
        if vehicles:
            old_count = len(vehicles)
            vehicles = [v for v in vehicles if v['id'] != vehicle_id]
            save_vehicles_to_cache(vehicles)
            logger.info(f"Veículo {vehicle_id} removido do cache")
            logger.debug(f"Total de veículos no cache: {len(vehicles)} (antes: {old_count})")
    except Exception as e:
        logger.error(f"Erro ao remover veículo {vehicle_id} do cache: {e}")
