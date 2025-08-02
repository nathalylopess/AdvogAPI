from typing import Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from rich.console import Console

from app.services.utils import wait_for_selenium

console = Console()

def debug_log_table_html(table_element):
    """Função temporária para exibir o conteúdo HTML da tabela coletada e ajudar no debug."""
    try:
        console.rule("[bold blue]🔍 DEBUG: HTML da tabela de processos")
        html = table_element.get_attribute("outerHTML")
        console.print(html)

        rows = table_element.find_elements(By.TAG_NAME, "tr")
        console.print(f"[bold cyan]Número de linhas (tr):[/] {len(rows)}")

        if rows:
            first_row_cells = rows[0].find_elements(By.TAG_NAME, "td")
            console.print(f"[bold cyan]Número de colunas (td) na primeira linha:[/] {len(first_row_cells)}")
            console.rule()

    except Exception as e:
        console.print(f"[bold red]Erro ao inspecionar a tabela:[/] {str(e)}")

def process_unit(scraper, index: int) -> Dict:
    """Processa uma unidade judiciária específica."""
    try:
        select_element = scraper.wait.until(
            EC.presence_of_element_located((By.ID, "unidade"))
        )
        select = Select(select_element)
        select.select_by_index(index)

        wait_for_new_data(scraper, select_element)

        select = Select(scraper.driver.find_element(By.ID, "unidade"))
        unidade = select.first_selected_option.text.strip()

        console.print("[green]✔ Chamando get_acervo()[/]")
        acervo = get_acervo(scraper)

        console.print("[green]✔ Chamando get_processos_em_tramitacao()[/]")
        processos = get_processos_em_tramitacao(scraper)

        console.print(f"[bold green]✔ Coletado:[/] [cyan]{unidade}[/] - [yellow]Acervo:[/] {acervo}")

        return {
            "id": index,
            "unidade": unidade,
            "acervo_total": acervo,
            "processos_em_tramitacao": processos
        }

    except StaleElementReferenceException:
        return process_unit(scraper, index)
    except Exception as e:
        console.print(f"[bold yellow]⚠ Tentando recuperar após erro: {str(e)}[/]")
        raise


def wait_for_new_data(scraper, old_element):
    """Espera o carregamento dos dados após mudança de unidade."""
    try:
        scraper.wait.until(EC.staleness_of(old_element))
        scraper.wait.until(EC.presence_of_element_located((By.ID, "unidade")))
        scraper.wait.until(EC.presence_of_element_located((By.XPATH, "//h3[text()='Acervo']")))
    except TimeoutException:
        console.print("[bold yellow]⚠ Tempo de espera excedido, tentando continuar...[/]")


def get_acervo(scraper) -> str:
    try:
        acervo_element = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//h3[text()='Acervo']/following-sibling::div[@class='box-rounded']/a/div[@class='big']"
            )),
            timeout=10,
            error_msg="Elemento do acervo não encontrado"
        )
        return acervo_element.text.strip()
    except Exception:
        return "N/A"


def get_processos_em_tramitacao(scraper) -> Dict:
    processos = {
        "CONHECIMENTO": {},
        "EXECUÇÃO": {},
        "EXECUÇÃO FISCAL": {},
        "EXECUÇÃO CRIMINAL": {},
        "TOTAL": {}
    }

    try:
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//h4[contains(text(), 'Processos em tramitação')]/following::table[1]"
            )),
            timeout=10,
            error_msg="Tabela de processos em tramitação não encontrada"
        )

        debug_log_table_html(table)

        rows = table.find_elements(By.TAG_NAME, "tr")
        current_category = None

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            if len(cells) == 4:
                category = cells[0].text.strip()

                if "CONHECIMENTO" in category:
                    current_category = "CONHECIMENTO"
                    processos[current_category] = parse_processos_data(cells)
                    processos[current_category]["Não julgados"] = {}
                elif "EXECUÇÃO" in category and "FISCAL" not in category and "CRIMINAL" not in category:
                    current_category = "EXECUÇÃO"
                    processos[current_category] = parse_processos_data(cells)
                elif "EXECUÇÃO FISCAL" in category:
                    current_category = "EXECUÇÃO FISCAL"
                    processos[current_category] = parse_processos_data(cells)
                    processos[current_category]["Não julgados"] = {}
                elif "EXECUÇÃO CRIMINAL" in category:
                    current_category = "EXECUÇÃO CRIMINAL"
                    processos[current_category] = parse_processos_data(cells)
                elif "TOTAL" in category:
                    processos["TOTAL"] = parse_processos_data(cells)
                elif "Não julgados" in category:
                    if current_category in ["CONHECIMENTO", "EXECUÇÃO FISCAL"]:
                        processos[current_category]["Não julgados"] = parse_processos_data(cells)

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Não foi possível coletar dados de 'Processos em tramitação'. Erro: {str(e)}")

    return processos


def parse_processos_data(cells) -> Dict:
    return {
        "Total": cells[1].text.strip(),
        "+60 dias": cells[2].text.strip(),
        "+100 dias": cells[3].text.strip()
    }
