import requests
import pandas as pd

BASE_URL = "https://parallelum.com.br/fipe/api/v1/carros"

def get_fipe_brands():
    response = requests.get(f"{BASE_URL}/marcas")
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    raise Exception("Erro ao obter marcas da tabela FIPE")

def get_fipe_models(brand_code):
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos")
    if response.status_code == 200:
        return pd.DataFrame(response.json()['modelos'])
    raise Exception("Erro ao obter modelos da tabela FIPE")

def get_fipe_years(brand_code, model_code):
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos")
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    raise Exception("Erro ao obter anos da tabela FIPE")

def get_fipe_price(brand_code, model_code, year_code):
    response = requests.get(f"{BASE_URL}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}")
    if response.status_code == 200:
        return response.json()
    raise Exception("Erro ao obter preço da tabela FIPE")
