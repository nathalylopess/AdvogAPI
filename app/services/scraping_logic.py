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

        console.print("[green]✔ Chamando get_procedimentos_e_peticoes_em_tramitacao()[/]")
        procedimentos = get_procedimentos_e_peticoes_em_tramitacao(scraper)

        console.print("[green]✔ Chamando get_suspensos_arquivo_provisorio()[/]")
        suspensos_arquivo_provisorio = get_suspensos_arquivo_provisorio(scraper)

        console.print("[green]✔ Chamando get_processos_conclusos_por_tipo()[/]")
        conclusos = get_processos_conclusos_por_tipo(scraper)

        console.print("[green]✔ Chamando get_controle_de_prisoes()[/]")
        controle_prisoes = get_controle_de_prisoes(scraper)

        console.print("[green]✔ Chamando get_controle_de_diligencias()[/]")
        diligencias = get_controle_de_diligencias(scraper)

        console.print(f"[bold green]✔ Coletado:[/] [cyan]{unidade}[/] - [yellow]Acervo:[/] {acervo}")

        return {
            "id": index,
            "unidade": unidade,
            "acervo_total": acervo,
            "processos_em_tramitacao": processos,
            "procedimentos_e_peticoes_em_tramitacao": procedimentos,
            "suspensos_arquivo_provisorio": suspensos_arquivo_provisorio,
            "processos_conclusos_por_tipo": conclusos,
            "controle_de_prisoes": controle_prisoes,
            "controle_de_diligencias": diligencias
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

        # debug_log_table_html(table)

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

def get_procedimentos_e_peticoes_em_tramitacao(scraper) -> Dict:
    procedimentos = {}

    try:
        # Espera o elemento <h4> específico e captura a tabela logo após
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//h4[text()='Procedimentos e petições em tramitação']/following::table[1]"
            )),
            timeout=10,
            error_msg="Tabela de procedimentos e petições em tramitação não encontrada"
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        # Itera nas linhas, pulando o cabeçalho (thead) e rodapé (tfoot)
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")

            # As linhas de dados devem ter 4 células: nome + 3 valores
            if len(cells) == 4:
                nome = cells[0].text.strip()
                total = cells[1].text.strip()
                mais_60 = cells[2].text.strip()
                mais_100 = cells[3].text.strip()

                procedimentos[nome] = {
                    "Total": total,
                    "+60 dias": mais_60,
                    "+100 dias": mais_100
                }

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Não foi possível coletar dados de 'Procedimentos e petições em tramitação'. Erro: {str(e)}")

    return procedimentos

def get_suspensos_arquivo_provisorio(scraper) -> Dict:
    """
    Coleta os dados da tabela "Suspensos / Arquivo provisório".
    Retorna um dicionário com os dados categorizados.
    """
    dados = {}

    try:
        # Localiza a tabela com base no título anterior a ela
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//h4[contains(text(), 'Suspensos / Arquivo provisório')]/following::table[1]"
            )),
            timeout=10,
            error_msg="Tabela 'Suspensos / Arquivo provisório' não encontrada"
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 5:
                categoria = cells[0].text.strip()
                dados[categoria] = {
                    "Total": cells[1].text.strip(),
                    "+60 dias": cells[2].text.strip(),
                    "+100 dias": cells[3].text.strip(),
                    "+730 dias": cells[4].text.strip()
                }

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Não foi possível coletar dados de 'Suspensos / Arquivo provisório'. Erro: {str(e)}")

    return dados

def get_processos_conclusos_por_tipo(scraper) -> Dict[str, Dict[str, str]]:
    """
    Coleta os dados da tabela 'Processos Conclusos por Tipo'.

    Retorna um dicionário com os tipos (Decisão, Despacho, Sentença, Total de processos conclusos)
    e os respectivos totais por prazo.
    """
    conclusos = {}

    try:
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'table-data')]/div[contains(text(),'Processos Conclusos por Tipo')]/following-sibling::table"
            )),
            timeout=10,
            error_msg="Tabela de 'Processos Conclusos por Tipo' não encontrada"
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 4:
                tipo = cells[0].text.strip()
                conclusos[tipo] = {
                    "Total": cells[1].text.strip(),
                    "+60 dias": cells[2].text.strip(),
                    "+100 dias": cells[3].text.strip()
                }

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Erro ao coletar dados de 'Processos Conclusos por Tipo': {str(e)}")

    return conclusos

def get_controle_de_prisoes(scraper) -> Dict[str, str]:
    """
    Coleta os dados da tabela 'Controle de Prisões'.

    Retorna um dicionário com o tipo de prisão como chave e o total como valor.
    """
    prisoes = {}

    try:
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'table-data')]/div[contains(text(),'Controle de Prisões')]/following-sibling::table"
            )),
            timeout=10,
            error_msg="Tabela de 'Controle de Prisões' não encontrada"
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 2:
                tipo = cells[0].text.strip()
                total = cells[1].text.strip()
                prisoes[tipo] = total

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Erro ao coletar dados de 'Controle de Prisões': {str(e)}")

    return prisoes

def get_controle_de_diligencias(scraper) -> Dict[str, str]:
    """
    Coleta os dados da tabela 'Controle de Diligências (PJe)'.

    Retorna um dicionário com os grupos e seus respectivos totais.
    """
    diligencias = {}

    try:
        table = wait_for_selenium(
            scraper.driver,
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'table-data') and div[contains(text(),'Controle de Diligências (PJe)')]]/table"
            )),
            timeout=10,
            error_msg="Tabela de 'Controle de Diligências (PJe)' não encontrada"
        )

        rows = table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 2:
                grupo = cells[0].text.strip()
                total = cells[1].text.strip()
                diligencias[grupo] = total

    except Exception as e:
        console.print(f"[bold yellow]⚠ Aviso:[/] Erro ao coletar dados de 'Controle de Diligências (PJe)': {str(e)}")

    return diligencias

def parse_processos_data(cells) -> Dict:
    return {
        "Total": cells[1].text.strip(),
        "+60 dias": cells[2].text.strip(),
        "+100 dias": cells[3].text.strip()
    }
