from tool import tool
from agent import ReactAgent

@tool
def get_actual_data(moneda: str) -> dict:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager

    class Scraper:
        def __init__(self, moneda: str):
            self.moneda = moneda
            self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/"
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--headless")
        
        def run(self) -> str:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            driver.get(self.url)
            try:
                # Se busca el elemento que contiene el precio
                span = driver.find_element(By.CLASS_NAME, "sc-65e7f566-0.WXGwg.base-text")
                resultado = span.text
            except Exception as e:
                resultado = f"Error: {e}"
            driver.quit()
            return resultado

    resultado = Scraper(moneda).run()
    if resultado.startswith("Error:"):
        return {"error": resultado}
    return {"Precio": resultado}


@tool
def get_historic_data(moneda: str, fecha: str) -> dict:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager

    class Scraper:
        def __init__(self, moneda: str, fecha: str):
            self.moneda = moneda
            self.fecha = fecha
            self.url = f"https://coinmarketcap.com/es/currencies/{self.moneda}/historical-data/"
            self.options = webdriver.ChromeOptions()
            self.options.add_argument("--headless")
        
        def run(self) -> dict:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=self.options
            )
            driver.get(self.url)
            wait = WebDriverWait(driver, 10)
            try:
                # Se localiza la fila que contiene la fecha indicada
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
            driver.quit()
            return resultado

    return Scraper(moneda, fecha).run()


agent = ReactAgent(
    model="llama-3.3-70b-versatile",
    tools=[get_historic_data, get_actual_data]
)

if __name__ == "__main__":
    user_msg = input("¿Qué datos de crypto quieres? ")
    output = agent.run(user_msg)
    print(output)
