from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from rich import print
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()

# Configuração do Selenium
options = webdriver.ChromeOptions()

driver = webdriver.Chrome(options=options)
driver.get("https://gpsjus.tjrn.jus.br/1grau_gerencial_publico.php")

# Aguarda o carregamento do select
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "unidade")))

data = []

# Obtém todas as opções disponíveis no select
select_element = driver.find_element(By.ID, "unidade")
select = Select(select_element)
options = select.options

# Mensagem inicial
console.print("\n[bold cyan]🔍 Iniciando coleta de dados...[/]\n")

# Percorre todas as unidades disponíveis (ignorando a primeira opção "Selecione uma opção")
#for index in track(range(1, len(options)), description="📊 Coletando dados..."):
for index in track(range(1, 5), description="📊 Coletando dados..."):
    try:
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "unidade"))
        )
        select = Select(select_element)
        select.select_by_index(index)
        WebDriverWait(driver, 10).until(EC.staleness_of(select_element))
        
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "unidade"))
        )
        select = Select(select_element)
        unidade = select.first_selected_option.text.strip() # Aqui já coletará o valor que ficará em "unidade"
        
        acervo = "N/A" # Aqui coletará já o valor que ficará em "acervo"
        try:
            acervo_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[text()='Acervo']/following-sibling::div[@class='box-rounded']/a/div[@class='big']"))
            )
            acervo = acervo_element.text.strip()
        except:
            pass
        
        # Coleta dos dados da tabela "Processos em tramitação"
        processos = {
            "CONHECIMENTO": {},
            "EXECUÇÃO": {},
            "EXECUÇÃO FISCAL": {},
            "EXECUÇÃO CRIMINAL": {},
            "TOTAL": {}
        }
        
        try:
            # Localiza a tabela "Processos em tramitação"
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h4[contains(text(), 'Processos em tramitação')]/following::table[1]"))
            )
            
            # Coleta os dados das linhas
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            current_category = None
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) == 4:
                    category = cells[0].text.strip()
                    
                    if "CONHECIMENTO" in category:
                        current_category = "CONHECIMENTO"
                        processos[current_category] = {
                            "Total": cells[1].text.strip(),
                            "+60 dias": cells[2].text.strip(),
                            "+100 dias": cells[3].text.strip(),
                            "Não julgados": {}
                        }
                    elif "EXECUÇÃO" in category and "FISCAL" not in category and "CRIMINAL" not in category:
                        current_category = "EXECUÇÃO"
                        processos[current_category] = {
                            "Total": cells[1].text.strip(),
                            "+60 dias": cells[2].text.strip(),
                            "+100 dias": cells[3].text.strip()
                        }
                    elif "EXECUÇÃO FISCAL" in category:
                        current_category = "EXECUÇÃO FISCAL"
                        processos[current_category] = {
                            "Total": cells[1].text.strip(),
                            "+60 dias": cells[2].text.strip(),
                            "+100 dias": cells[3].text.strip(),
                            "Não julgados": {}
                        }
                    elif "EXECUÇÃO CRIMINAL" in category:
                        current_category = "EXECUÇÃO CRIMINAL"
                        processos[current_category] = {
                            "Total": cells[1].text.strip(),
                            "+60 dias": cells[2].text.strip(),
                            "+100 dias": cells[3].text.strip()
                        }
                    elif "TOTAL" in category:
                        processos["TOTAL"] = {
                            "Total": cells[1].text.strip(),
                            "+60 dias": cells[2].text.strip(),
                            "+100 dias": cells[3].text.strip()
                        }
                    elif "Não julgados" in category:
                        if current_category in ["CONHECIMENTO", "EXECUÇÃO FISCAL"]:
                            processos[current_category]["Não julgados"] = {
                                "Total": cells[1].text.strip(),
                                "+60 dias": cells[2].text.strip(),
                                "+100 dias": cells[3].text.strip()
                            }
        
        except Exception as e:
            console.print(f"[bold yellow]⚠ Aviso:[/] Não foi possível coletar dados de 'Processos em tramitação' para {unidade}. Erro: {str(e)}")
        
        data.append({
            "id": index,
            "unidade": unidade,
            "acervo_total": acervo,
            "processos_em_tramitacao": processos
        })
        
        console.print(f"[bold green]✔ Coletado:[/] [cyan]{unidade}[/] - [yellow]Acervo:[/] {acervo}")
    
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao processar a unidade {index}: {str(e)}[/]")

driver.quit()

# Exibe os resultados em uma tabela
table = Table(title="📊 Resultados da Coleta")
table.add_column("ID", justify="right")
table.add_column("Unidade", justify="left")
table.add_column("Acervo Total", justify="right")
table.add_column("Processos em Tramitação", justify="left")

for item in data:
    table.add_row(
        str(item["id"]),
        item["unidade"],
        item["acervo_total"],
        json.dumps(item["processos_em_tramitacao"], ensure_ascii=False)
    )

console.print(table)

# Salva os dados em formato JSON
with open('dados_tjrn.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

console.print("\n[bold magenta]✅ Coleta finalizada. Dados salvos em 'dados_tjrn.json'.[/]\n")