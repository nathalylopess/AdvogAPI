from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from rich.console import Console
from rich.progress import track
import json

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

console = Console()

class TJRNScraper:
    def __init__(self, headless=True):
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        if headless:
            self.options.add_argument('--headless=new')  # Nova sintaxe para headless
        self.driver = webdriver.Chrome(options=self.options)
        self.base_url = "https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php"
        self.wait = WebDriverWait(self.driver, 15) 

    def fetch_data(self, max_units=None):
            self.driver.get(self.base_url)
            self._wait_for_page_load()
            
            select_element = self.wait.until(
                EC.presence_of_element_located((By.ID, "unidade"))
            )
            select = Select(select_element)
            options = select.options
            
            data = []
            max_range = len(options) if max_units is None else min(max_units + 1, len(options))
            
            for index in track(range(1, max_range), description="📊 Coletando dados..."):
            #for index in track(range(1, 5), description="📊 Coletando dados..."): # Apenas 4 iterações para testar
                try:
                    unit_data = self._process_unit(index)
                    if unit_data:
                        data.append(unit_data)
                except Exception as e:
                    console.print(f"[bold red]❌ Erro ao processar a unidade {index}: {str(e)}[/]")
                    # Tenta recarregar a página se falhar
                    self.driver.get(self.base_url)
                    self._wait_for_page_load()
            
            self.driver.quit()
            return data
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
            acervo_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                "//h3[text()='Acervo']/following-sibling::div[@class='box-rounded']/a/div[@class='big']"))
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
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                "//h4[contains(text(), 'Processos em tramitação')]/following::table[1]"))
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