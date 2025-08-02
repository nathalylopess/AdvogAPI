import atexit
from typing import List, Dict, Optional, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from rich.console import Console
from rich.progress import track

from app.services.driver_setup import setup_driver
from app.services.scraping_logic import process_unit
from app.services.utils import wait_for_page_load, recover_from_error

console = Console()

class TJRNScraper:
    def __init__(self, headless: bool = True) -> None:
        """
        Inicializa o scraper do TJRN.
        
        Args:
            headless (bool): Se True, executa o navegador em modo headless.
        """
        self.headless = headless
        self.driver, self.options, self.user_data_dir = setup_driver(self.headless)
        self.wait = WebDriverWait(self.driver, 15)
        self.base_url = "https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php"
        atexit.register(self.cleanup)

    def fetch_data(self, max_units: Optional[int] = None) -> List[Dict[str, Union[str, int]]]:
        """
        Coleta dados das unidades judiciais.
        
        Args:
            max_units (int, optional): Número máximo de unidades a serem processadas.
            
        Returns:
            List[Dict]: Lista contendo os dados coletados de cada unidade.
        """
        try:
            self.driver.get(self.base_url)
            wait_for_page_load(self.driver, self.wait)

            select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "unidade"))
            )
            select = Select(select_element)
            options = select.options

            data = []
            max_range = len(options) if max_units is None else min(max_units + 1, len(options))

            for index in track(range(1, 5), description="📊 Coletando dados..."):
            #for index in track(range(1, max_range), description="📊 Coletando dados..."):
                try:
                    unit_data = process_unit(self, index)
                    if unit_data:
                        data.append(unit_data)
                except Exception as e:
                    console.print(f"[bold red]❌ Erro ao processar a unidade {index}: {str(e)}[/]")
                    recover_from_error(self.driver, self.base_url, self.wait)

            return data

        finally:
            self.driver.quit()

    def cleanup(self) -> None:
        """Limpeza final do WebDriver e diretório temporário."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
        except Exception:
            pass

        try:
            if hasattr(self, 'user_data_dir'):
                import shutil
                shutil.rmtree(self.user_data_dir, ignore_errors=True)
        except Exception:
            pass
