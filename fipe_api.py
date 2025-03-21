import requests
import pandas as pd
from cache_manager import load_from_cache, save_to_cache

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

def get_fipe_brands():
    # Tenta carregar do cache primeiro
    cached_data = load_from_cache('brands')
    if cached_data is not None:
        return pd.DataFrame(cached_data)

    # Se não estiver em cache, faz a requisição
    response = requests.get(f"{BASE_URL}/marcas")
    if response.status_code == 200:
        data = response.json()
        save_to_cache('brands', data)
        return pd.DataFrame(data)
    raise Exception("Erro ao obter marcas da tabela FIPE")

def get_fipe_models(brand_code):
    # Tenta carregar do cache primeiro
    cached_data = load_from_cache(f'models_{brand_code}')
    if cached_data is not None:
        return pd.DataFrame(cached_data)

    # Se não estiver em cache, faz a requisição
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos")
    if response.status_code == 200:
        data = response.json()['modelos']
        save_to_cache(f'models_{brand_code}', data)
        return pd.DataFrame(data)
    raise Exception("Erro ao obter modelos da tabela FIPE")

def get_fipe_years(brand_code, model_code):
    # Tenta carregar do cache primeiro
    cached_data = load_from_cache(f'years_{brand_code}_{model_code}')
    if cached_data is not None:
        return pd.DataFrame(cached_data)

    # Se não estiver em cache, faz a requisição
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos")
    if response.status_code == 200:
        data = response.json()
        save_to_cache(f'years_{brand_code}_{model_code}', data)
        return pd.DataFrame(data)
    raise Exception("Erro ao obter anos da tabela FIPE")

def get_fipe_price(brand_code, model_code, year_code):
    # Tenta carregar do cache primeiro
    cached_data = load_from_cache(f'price_{brand_code}_{model_code}_{year_code}')
    if cached_data is not None:
        return cached_data

    # Se não estiver em cache, faz a requisição
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}")
    if response.status_code == 200:
        data = response.json()
        save_to_cache(f'price_{brand_code}_{model_code}_{year_code}', data)
        return data
    raise Exception("Erro ao obter preço da tabela FIPE")
