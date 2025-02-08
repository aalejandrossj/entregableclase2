import json
from typing import Callable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

# --- Utilidades para definir herramientas (tools) ---

def get_fn_signature(fn: Callable) -> dict:
    """
    Genera la firma de una función, incluyendo nombre, descripción y tipos de parámetros.
    """
    fn_signature: dict = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "parameters": {"properties": {}},
    }
    schema = {
        k: {"type": v.__name__}
        for k, v in fn.__annotations__.items()
        if k != "return"
    }
    fn_signature["parameters"]["properties"] = schema
    return fn_signature

def validate_arguments(tool_call: dict, tool_signature: dict) -> dict:
    """
    Valida y convierte los argumentos para que coincidan con los tipos esperados según la firma.
    """
    properties = tool_signature["parameters"]["properties"]
    type_mapping = {
        "int": int,
        "str": str,
        "bool": bool,
        "float": float,
    }
    for arg_name, arg_value in tool_call["arguments"].items():
        expected_type = properties[arg_name].get("type")
        if not isinstance(arg_value, type_mapping[expected_type]):
            tool_call["arguments"][arg_name] = type_mapping[expected_type](arg_value)
    return tool_call

class Tool:
    """
    Representa una herramienta que envuelve una función y su firma.
    """
    def __init__(self, name: str, fn: Callable, fn_signature: str):
        self.name = name
        self.fn = fn
        self.fn_signature = fn_signature

    def __str__(self):
        return self.fn_signature

    def run(self, **kwargs):
        return self.fn(**kwargs)

def tool(fn: Callable):
    """
    Decorador que convierte una función en una herramienta (Tool).
    """
    def wrapper():
        fn_signature = get_fn_signature(fn)
        return Tool(
            name=fn_signature.get("name"),
            fn=fn,
            fn_signature=json.dumps(fn_signature)
        )
    return wrapper()

# --- Código de scraping (clases internas) ---

class BaseScraper:
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument("--headless")

    def abrir_driver(self):
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=self.options
        )

    def cerrar_driver(self, driver):
        driver.quit()

class GetActualData(BaseScraper):
    def __init__(self, moneda: str):
        super().__init__()
        self.moneda = moneda
        self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/"

    def obtener_precio(self) -> str:
        driver = self.abrir_driver()
        driver.get(self.url)
        try:
            # Se busca el elemento que contiene el precio
            span = driver.find_element(By.CLASS_NAME, "sc-65e7f566-0.WXGwg.base-text")
            resultado = span.text
        except Exception as e:
            resultado = f"Error: {str(e)}"
        self.cerrar_driver(driver)
        return resultado

class GetHistoricData(BaseScraper):
    def __init__(self, moneda: str, fecha: str):
        super().__init__()
        self.moneda = moneda
        self.fecha = fecha
        self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/historical-data/"

    def obtener_precio(self) -> dict:
        driver = self.abrir_driver()
        driver.get(self.url)
        wait = WebDriverWait(driver, 10)
        try:
            # Se localiza la fila con el <td> que contiene la fecha indicada
            fila = wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//tbody/tr[td[normalize-space(text())='{self.fecha}']]")
                )
            )
            columnas = fila.find_elements(By.TAG_NAME, "td")
            resultado = {
                "Apertura": columnas[1].text,
                "Alza": columnas[2].text,
                "Baja": columnas[3].text,
                "MarketCap": columnas[6].text
            }
        except Exception as e:
            resultado = {"error": str(e)}
        self.cerrar_driver(driver)
        return resultado

# --- Funciones expuestas como herramientas (@tool) ---

@tool
def get_actual_data(moneda: str) -> dict:
    """
    Obtiene el precio actual de una moneda en CoinMarketCap.
    
    Args:
        moneda (str): El nombre de la moneda (por ejemplo, "bitcoin").
        
    Returns:
        dict: Diccionario con el precio actual, ej. {"Precio": "$96,065.33"}.
    """
    scraper = GetActualData(moneda)
    precio = scraper.obtener_precio()
    if precio.startswith("Error:"):
        return {"error": precio}
    return {"Precio": precio}

@tool
def get_historic_data(moneda: str, fecha: str) -> dict:
    """
    Obtiene datos históricos (Apertura, Alza, Baja, MarketCap) de una moneda en una fecha específica.
    
    Args:
        moneda (str): El nombre de la moneda (por ejemplo, "bitcoin").
        fecha (str): La fecha en el formato exacto de la tabla (por ejemplo, "Feb 07, 2025").
        
    Returns:
        dict: Diccionario con los datos históricos, ej. {"Apertura": "$96,581.32", ...}.
    """
    scraper = GetHistoricData(moneda, fecha)
    datos = scraper.obtener_precio()
    return datos
