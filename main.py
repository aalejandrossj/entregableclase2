from tool import get_fn_signature
from tool import validate_arguments
from tool import tool
from agent import REACT_SYSTEM_PROMPT
from agent import MODEL
from agent import GROQ_CLIENT
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

print("Tool name: ", get_actual_data.name)
print("Tool signature: ", get_actual_data.fn_signature)

tools_signature = get_actual_data.fn_signature + ",\n" + get_historic_data.fn_signature + ",\n"

REACT_SYSTEM_PROMPT = REACT_SYSTEM_PROMPT % tools_signature

USER_QUESTION = "What was the price of solana on 21 January 2025"
chat_history = [
    {
        "role": "system",
        "content": REACT_SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": f"<question>{USER_QUESTION}</question>"
    }
]

output = GROQ_CLIENT.chat.completions.create(
    messages=chat_history,
    model=MODEL
).choices[0].message.content


chat_history.append(
    {
        "role": "assistant",
        "content": output
    }
)

tool_call = extract_tag_content(output, tag="tool_call")

print(tool_call)
