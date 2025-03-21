import requests
import pandas as pd
from cache_manager import load_from_cache, save_to_cache
from logger import setup_logger

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"
logger = setup_logger('fipe_api')

def get_fipe_brands():
    logger.info("Buscando marcas FIPE")
    cached_data = load_from_cache('brands')
    if cached_data is not None:
        logger.debug("Dados de marcas encontrados no cache")
        return pd.DataFrame(cached_data)

    try:
        logger.debug("Fazendo requisição para API FIPE - marcas")
        response = requests.get(f"{BASE_URL}/marcas")
        response.raise_for_status()
        data = response.json()
        save_to_cache('brands', data)
        logger.info(f"Obtidas {len(data)} marcas da API FIPE")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Erro ao obter marcas: {str(e)}")
        raise Exception("Erro ao obter marcas da tabela FIPE")

def get_fipe_models(brand_code):
    logger.info(f"Buscando modelos para marca {brand_code}")
    cached_data = load_from_cache(f'models_{brand_code}')
    if cached_data is not None:
        logger.debug(f"Dados de modelos para marca {brand_code} encontrados no cache")
        return pd.DataFrame(cached_data)

    try:
        logger.debug(f"Fazendo requisição para API FIPE - modelos da marca {brand_code}")
        response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos")
        response.raise_for_status()
        data = response.json()['modelos']
        save_to_cache(f'models_{brand_code}', data)
        logger.info(f"Obtidos {len(data)} modelos para marca {brand_code}")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Erro ao obter modelos da marca {brand_code}: {str(e)}")
        raise Exception("Erro ao obter modelos da tabela FIPE")

def get_fipe_years(brand_code, model_code):
    logger.info(f"Buscando anos para marca {brand_code}, modelo {model_code}")
    cached_data = load_from_cache(f'years_{brand_code}_{model_code}')
    if cached_data is not None:
        logger.debug(f"Dados de anos encontrados no cache")
        return pd.DataFrame(cached_data)

    try:
        logger.debug(f"Fazendo requisição para API FIPE - anos")
        response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos")
        response.raise_for_status()
        data = response.json()
        save_to_cache(f'years_{brand_code}_{model_code}', data)
        logger.info(f"Obtidos {len(data)} anos para o modelo")
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Erro ao obter anos: {str(e)}")
        raise Exception("Erro ao obter anos da tabela FIPE")

def get_fipe_price(brand_code, model_code, year_code):
    logger.info(f"Buscando preço para marca {brand_code}, modelo {model_code}, ano {year_code}")
    cached_data = load_from_cache(f'price_{brand_code}_{model_code}_{year_code}')
    if cached_data is not None:
        logger.debug("Dados de preço encontrados no cache")
        return cached_data

    try:
        logger.debug("Fazendo requisição para API FIPE - preço")
        response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}")
        response.raise_for_status()
        data = response.json()
        save_to_cache(f'price_{brand_code}_{model_code}_{year_code}', data)
        logger.info(f"Preço obtido com sucesso: {data.get('Valor', 'N/A')}")
        return data
    except Exception as e:
        logger.error(f"Erro ao obter preço: {str(e)}")
        raise Exception("Erro ao obter preço da tabela FIPE")
