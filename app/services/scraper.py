import json
import os
import shutil
import tempfile
import atexit
from typing import List, Dict, Optional, Union

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (StaleElementReferenceException, 
                                      TimeoutException,
                                      WebDriverException)
from selenium.webdriver import Remote
from rich.console import Console
from rich.progress import track

console = Console()

class TJRNScraper:
    def __init__(self, headless: bool = True) -> None:
        """
        Inicializa o scraper do TJRN.
        
        Args:
            headless (bool): Se True, executa o navegador em modo headless.
        """
        self.headless = headless
        self._setup_driver()
        if not hasattr(self, 'driver') or self.driver is None:
            raise RuntimeError("❌ Falha ao inicializar o WebDriver.")
        self.base_url = "https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php"
        atexit.register(self.cleanup)

    def _setup_driver(self) -> None:
        """Configura o WebDriver do Chrome."""
        self._setup_chrome_options()
        self._setup_temp_directory()
        self._initialize_driver()
        self.wait = WebDriverWait(self.driver, 15)

    def _setup_chrome_options(self) -> None:
        """Configura as opções do Chrome."""
        self.options = webdriver.ChromeOptions()
        
        # Configurações básicas
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        
        if self.headless:
            self.options.add_argument('--headless=new')
        
        # Configurações para evitar detecção como bot
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # Configurações de desempenho
        self.options.add_argument('--disable-application-cache')
        self.options.add_argument('--disable-extensions')
        self.options.add_argument('--disable-infobars')
        self.options.add_argument('--remote-debugging-port=9222')

    def _setup_temp_directory(self) -> None:
        """Configura o diretório temporário para o perfil do Chrome."""
        self.user_data_dir = os.path.join(tempfile.gettempdir(), f'chrome_{os.getpid()}')
        self._cleanup_old_sessions()
        self.options.add_argument(f'--user-data-dir={self.user_data_dir}')

    def _cleanup_old_sessions(self) -> None:
        """Limpa sessões antigas do Chrome."""
        try:
            # Para sistemas Unix/Linux
            os.system("pkill -f chrome")
            os.system("pkill -f chromedriver")

            # Limpa diretórios temporários antigos
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                if item.startswith('chrome_'):
                    try:
                        shutil.rmtree(os.path.join(temp_dir, item))
                    except Exception as e:
                        console.print(f"[yellow]⚠️ Falha ao limpar {item}: {str(e)}[/]")
        except Exception as e:
            console.print(f"[red]❌ Erro durante a limpeza de sessões antigas: {str(e)}[/]")

    def _initialize_driver(self) -> None:
        """Inicializa o WebDriver."""
        try:
            self.driver = Remote(
            command_executor=os.getenv("SELENIUM_REMOTE_URL", "http://chrome:4444/wd/hub"),
            options=self.options
)
            self.driver.set_page_load_timeout(30)
        except WebDriverException as e:
            console.print(f"[bold red]❌ Falha ao iniciar o WebDriver: {str(e)}[/]")
            raise e  

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
            self._wait_for_page_load()
            
            select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "unidade"))
            )
            select = Select(select_element)
            options = select.options
            
            data = []
            max_range = len(options) if max_units is None else min(max_units + 1, len(options))

            #for index in track(range(1, 4), description="📊 Coletando dados..."): # teste            
            for index in track(range(1, max_range), description="📊 Coletando dados..."):
                try:
                    unit_data = self._process_unit(index)
                    if unit_data:
                        data.append(unit_data)
                except Exception as e:
                    console.print(f"[bold red]❌ Erro ao processar a unidade {index}: {str(e)}[/]")
                    self._recover_from_error()
            
            return data
        
        finally:
            self.driver.quit()

    def _wait_for_page_load(self):
        """Espera até que a página tenha terminado de carregar completamente"""
        self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')

    def _process_unit(self, index):
        """Processa uma unidade judiciária específica"""
        try:
            # Localiza o elemento select novamente a cada iteração
            select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "unidade"))  # Fechando os parênteses corretamente
            )
            select = Select(select_element)
            
            # Seleciona a opção pelo índice
            select.select_by_index(index)
            
            # Espera até que os dados da nova unidade tenham carregado
            self._wait_for_new_data(select_element)
            
            # Obtém os dados da unidade
            select = Select(self.driver.find_element(By.ID, "unidade"))
            unidade = select.first_selected_option.text.strip()
            
            acervo = self._get_acervo()
            processos = self._get_processos_em_tramitacao()
            
            console.print(f"[bold green]✔ Coletado:[/] [cyan]{unidade}[/] - [yellow]Acervo:[/] {acervo}")
            
            return {
                "id": index,
                "unidade": unidade,
                "acervo_total": acervo,
                "processos_em_tramitacao": processos
            }
            
        except StaleElementReferenceException:
            # Se o elemento ficar obsoleto, tenta novamente
            return self._process_unit(index)
        except Exception as e:
            console.print(f"[bold yellow]⚠ Tentando recuperar após erro: {str(e)}[/]")
            raise
    
    def _wait_for_new_data(self, old_element):
        """Espera até que os novos dados tenham carregado após selecionar uma unidade"""
        try:
            # Espera até que o elemento antigo se torne obsoleto (indicando que a página está atualizando)
            self.wait.until(EC.staleness_of(old_element))
            
            # Espera até que o novo select esteja disponível
            self.wait.until(
                EC.presence_of_element_located((By.ID, "unidade"))
            )
            
            # Espera adicional para os dados serem carregados
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[text()='Acervo']"))
            )  # Fechando todos os parênteses corretamente
            
        except TimeoutException:
            console.print("[bold yellow]⚠ Tempo de espera excedido, tentando continuar...[/]")

    def _get_acervo(self):
        try:
            acervo_element = self.wait_for_selenium(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//h3[text()='Acervo']/following-sibling::div[@class='box-rounded']/a/div[@class='big']"
                )),
                timeout=10,
                error_msg="Elemento do acervo não encontrado"
            )
            return acervo_element.text.strip()
        except:
            return "N/A"
    
    def _get_processos_em_tramitacao(self):
        processos = {
            "CONHECIMENTO": {},
            "EXECUÇÃO": {},
            "EXECUÇÃO FISCAL": {},
            "EXECUÇÃO CRIMINAL": {},
            "TOTAL": {}
        }
        
        try:
            table = self.wait_for_selenium(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//h4[contains(text(), 'Processos em tramitação')]/following::table[1]"
                )),
                timeout=10,
                error_msg="Tabela de processos em tramitação não encontrada"
            )

            rows = table.find_elements(By.TAG_NAME, "tr")
            current_category = None
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) == 4:
                    category = cells[0].text.strip()
                    
                    if "CONHECIMENTO" in category:
                        current_category = "CONHECIMENTO"
                        processos[current_category] = self._parse_processos_data(cells)
                        processos[current_category]["Não julgados"] = {}
                    elif "EXECUÇÃO" in category and "FISCAL" not in category and "CRIMINAL" not in category:
                        current_category = "EXECUÇÃO"
                        processos[current_category] = self._parse_processos_data(cells)
                    elif "EXECUÇÃO FISCAL" in category:
                        current_category = "EXECUÇÃO FISCAL"
                        processos[current_category] = self._parse_processos_data(cells)
                        processos[current_category]["Não julgados"] = {}
                    elif "EXECUÇÃO CRIMINAL" in category:
                        current_category = "EXECUÇÃO CRIMINAL"
                        processos[current_category] = self._parse_processos_data(cells)
                    elif "TOTAL" in category:
                        processos["TOTAL"] = self._parse_processos_data(cells)
                    elif "Não julgados" in category:
                        if current_category in ["CONHECIMENTO", "EXECUÇÃO FISCAL"]:
                            processos[current_category]["Não julgados"] = self._parse_processos_data(cells)
        
        except Exception as e:
            console.print(f"[bold yellow]⚠ Aviso:[/] Não foi possível coletar dados de 'Processos em tramitação'. Erro: {str(e)}")
        
        return processos
    
    def _parse_processos_data(self, cells):
        return {
            "Total": cells[1].text.strip(),
            "+60 dias": cells[2].text.strip(),
            "+100 dias": cells[3].text.strip()
        }
    
    def save_to_json(self, data, filename='dados_tjrn.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[bold magenta]✅ Dados salvos em '{filename}'.[/]\n")

    def cleanup(self) -> None:
        """Limpeza final."""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
        except:
            pass
        
        try:
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
        except:
            pass

    def _recover_from_error(self) -> None:
        """Tenta recuperar de um erro."""
        try:
            self.driver.refresh()
            self._wait_for_page_load()
        except:
            try:
                self.driver.get(self.base_url)
                self._wait_for_page_load()
            except Exception as e:
                console.print(f"[red]❌ Falha na recuperação: {str(e)}[/]")
                raise

    def wait_for_selenium(self, condition, timeout=10, error_msg="Timeout waiting for condition"):
        """
        Aguarda uma condição do Selenium com tratamento de exceções.
        
        Args:
            condition: Condição do WebDriverWait (ex: EC.presence_of_element_located).
            timeout (int): Tempo máximo de espera em segundos.
            error_msg (str): Mensagem de erro em caso de falha.
        Returns:
            O resultado da condição esperada, ou levanta TimeoutException.
        """
        try:
            return WebDriverWait(self.driver, timeout).until(condition)
        except TimeoutException:
            console.print(f"[bold yellow]⚠ {error_msg}[/]")
            raise
