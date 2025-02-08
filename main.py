from tool import get_fn_signature
from tool import validate_arguments
from tool import tool
from agent import ReactAgent
from utils.extraction import extract_tag_content
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

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
    Gets the current price of a currency on CoinMarketCap.

    Args:
        moneda (str): The name of the currency (e.g., "bitcoin").
    
    Returns:
        dict: Dictionary with the current price, e.g., {"Precio": "$96,065.33"}.
    """
    scraper = GetActualData(moneda)
    precio = scraper.obtener_precio()
    if precio.startswith("Error:"):
        return {"error": precio}
    return {"Precio": precio}

@tool
def get_historic_data(moneda: str, fecha: str) -> dict:
    """
        Gets historical data (Open, High, Low, MarketCap) of a currency on a specific date.

    Args:
        moneda (str): The name of the currency (e.g., "bitcoin").
        fecha (str): The date in the exact format of the table (e.g., "Feb 07, 2025").

    Returns:
        dict: Dictionary with historical data, e.g., {"Open": "$96,581.32", ...}.
    """

    scraper = GetHistoricData(moneda, fecha)
    datos = scraper.obtener_precio()
    return datos

agent = ReactAgent(
    model="llama-3.3-70b-versatile",
    tools=[get_historic_data, get_actual_data]
    )

user_msg = "Dame datos de solana del dia 20 de enero de 2025"
agent.run(user_msg)