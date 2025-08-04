import pytest
from unittest.mock import MagicMock, patch
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from app.services.scraping_logic import (
    get_acervo, 
    wait_for_new_data, 
    get_processos_em_tramitacao, 
    get_procedimentos_e_peticoes_em_tramitacao, 
    get_suspensos_arquivo_provisorio,
    get_processos_conclusos_por_tipo,
    get_controle_de_prisoes,
    get_controle_de_diligencias,
    get_demonstrativo_de_distribuicoes,
    get_processos_baixados,
    get_atos_judiciais_proferidos
)

# Teste da função get_acervo
@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_acervo(mock_wait_for_selenium):
    mock_element = MagicMock()
    mock_element.text.strip.return_value = "1500"
    mock_wait_for_selenium.return_value = mock_element

    mock_scraper = MagicMock()
    acervo = get_acervo(mock_scraper)

    assert acervo == "1500"
    mock_wait_for_selenium.assert_called_once()

@patch("app.services.scraping_logic.console.print")
def test_get_acervo_error(mock_console_print):
    # Simula erro no wait_for_selenium
    with patch("app.services.scraping_logic.wait_for_selenium", side_effect=Exception("Elemento não encontrado")):
        mock_scraper = MagicMock()
        result = get_acervo(mock_scraper)

        assert result == "N/A"
        mock_console_print.assert_not_called()  # A função não imprime nada em caso de erro

# Teste da função wait_for_new_data
def test_wait_for_new_data_success():
    scraper = MagicMock()
    scraper.wait.until = MagicMock()

    old_element = MagicMock()
    wait_for_new_data(scraper, old_element)

    # Verifica se todas as condições foram chamadas
    assert scraper.wait.until.call_count == 3

@patch("app.services.scraping_logic.console.print")
def test_wait_for_new_data_timeout(mock_console_print):
    scraper = MagicMock()
    scraper.wait.until.side_effect = TimeoutException("timeout")

    old_element = MagicMock()

    wait_for_new_data(scraper, old_element)

    mock_console_print.assert_called_with("[bold yellow]⚠ Tempo de espera excedido, tentando continuar...[/]")

# Mock da função parse_processos_data usada internamente
@pytest.fixture(autouse=True)
def mock_parse_processos_data():
    with patch("app.services.scraping_logic.parse_processos_data") as mock:
        mock.return_value = {"Total": "10", "+60 dias": "1", "+100 dias": "0"}
        yield mock

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_processos_em_tramitacao(mock_wait):
    table_mock = MagicMock()
    mock_wait.return_value = table_mock

    # Simula linhas da tabela
    row_mock = MagicMock()
    cell_mock = [MagicMock() for _ in range(4)]
    cell_mock[0].text.strip.side_effect = [
        "CONHECIMENTO", "Não julgados",
        "EXECUÇÃO", "EXECUÇÃO FISCAL", "Não julgados",
        "EXECUÇÃO CRIMINAL", "TOTAL"
    ]
    row_mock.find_elements.return_value = cell_mock
    table_mock.find_elements.return_value = [row_mock for _ in range(7)]

    scraper = MagicMock()
    result = get_processos_em_tramitacao(scraper)
    assert "CONHECIMENTO" in result
    assert result["CONHECIMENTO"]["Total"] == "10"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_procedimentos_e_peticoes_em_tramitacao(mock_wait):
    table_mock = MagicMock()
    row_mock = MagicMock()
    cells = [MagicMock() for _ in range(4)]
    cells[0].text.strip.return_value = "Nome Procedimento"
    cells[1].text.strip.return_value = "5"
    cells[2].text.strip.return_value = "2"
    cells[3].text.strip.return_value = "1"
    row_mock.find_elements.return_value = cells
    table_mock.find_elements.return_value = [row_mock]
    mock_wait.return_value = table_mock

    scraper = MagicMock()
    result = get_procedimentos_e_peticoes_em_tramitacao(scraper)
    assert result["Nome Procedimento"] == {"Total": "5", "+60 dias": "2", "+100 dias": "1"}

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_suspensos_arquivo_provisorio(mock_wait):
    table_mock = MagicMock()
    row_mock = MagicMock()
    cells = [MagicMock() for _ in range(5)]
    cells[0].text.strip.return_value = "Categoria X"
    cells[1].text.strip.return_value = "20"
    cells[2].text.strip.return_value = "5"
    cells[3].text.strip.return_value = "2"
    cells[4].text.strip.return_value = "1"
    row_mock.find_elements.return_value = cells
    table_mock.find_elements.return_value = [row_mock]
    mock_wait.return_value = table_mock

    scraper = MagicMock()
    result = get_suspensos_arquivo_provisorio(scraper)
    assert result["Categoria X"] == {
        "Total": "20",
        "+60 dias": "5",
        "+100 dias": "2",
        "+730 dias": "1"
    }

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_processos_conclusos_por_tipo(mock_wait):
    row = MagicMock()
    row.find_elements.return_value = [
        MagicMock(text="Decisão"),
        MagicMock(text="50"),
        MagicMock(text="5"),
        MagicMock(text="2")
    ]
    table = MagicMock()
    table.find_elements.return_value = [row]
    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_processos_conclusos_por_tipo(scraper)

    assert "Decisão" in result
    assert result["Decisão"]["Total"] == "50"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_controle_de_prisoes(mock_wait):
    row = MagicMock()
    row.find_elements.return_value = [
        MagicMock(text="Preventiva"),
        MagicMock(text="12")
    ]
    table = MagicMock()
    table.find_elements.return_value = [row]
    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_controle_de_prisoes(scraper)

    assert "Preventiva" in result
    assert result["Preventiva"] == "12"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_controle_de_diligencias(mock_wait):
    row = MagicMock()
    row.find_elements.return_value = [
        MagicMock(text="Grupo X"),
        MagicMock(text="7")
    ]
    table = MagicMock()
    table.find_elements.return_value = [row]
    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_controle_de_diligencias(scraper)

    assert "Grupo X" in result
    assert result["Grupo X"] == "7"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_demonstrativo_de_distribuicoes(mock_wait):
    row1 = MagicMock()
    row1.find_elements.return_value = [
        MagicMock(text="Mês"),
        MagicMock(text="Jan"),
        MagicMock(text="Fev"),
        MagicMock(text="Total")
    ]
    row2 = MagicMock()
    row2.find_elements.return_value = [
        MagicMock(text="Entradas"),
        MagicMock(text="5"),
        MagicMock(text="7"),
        MagicMock(text="12")
    ]
    row3 = MagicMock()
    row3.find_elements.return_value = [
        MagicMock(text="Saldo"),
        MagicMock(text="3"),
        MagicMock(text="2"),
        MagicMock(text="5")
    ]

    table = MagicMock()
    table.find_elements.return_value = [row1, row2, row3]
    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_demonstrativo_de_distribuicoes(scraper)

    assert "Entradas" in result
    assert result["Entradas"]["total"] == "12"
    assert "Saldo (entradas - saídas)" in result
    assert result["Saldo (entradas - saídas)"]["mensal"]["Fev"] == "2"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_processos_baixados(mock_wait):
    header = MagicMock()
    header.find_elements.return_value = [
        MagicMock(text=""),
        MagicMock(text="Jan"),
        MagicMock(text="Fev"),
        MagicMock(text="Total")
    ]
    row = MagicMock()
    row.find_elements.return_value = [
        MagicMock(text="Baixados"),
        MagicMock(text="5"),
        MagicMock(text="3"),
        MagicMock(text="8")
    ]
    tbody = MagicMock()
    tbody.find_elements.return_value = [row]
    table = MagicMock()
    table.find_element.side_effect = lambda by, value=None: header if value == "thead" else tbody
    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_processos_baixados(scraper)

    assert "Baixados" in result
    assert result["Baixados"]["mensal"]["Jan"] == "5"
    assert result["Baixados"]["total"] == "8"

@patch("app.services.scraping_logic.wait_for_selenium")
def test_get_atos_judiciais_proferidos(mock_wait):
    # Mock dos cabeçalhos da tabela (thead > tr > th)
    header_cells = [
        MagicMock(text="Tipo"),
        MagicMock(text="Jan"),
        MagicMock(text="Fev"),
        MagicMock(text="Total")
    ]

    # Mock da linha de dados (tbody > tr)
    row = MagicMock()
    # row.find_element(xpath="./td[1]") retorna o tipo (descrição)
    row.find_element.return_value = MagicMock(text="Sentença")
    # row.find_elements(xpath="./td[position() > 1]") retorna as células numéricas (jan, fev, total)
    row.find_elements.return_value = [
        MagicMock(text="10"),
        MagicMock(text="20"),
        MagicMock(text="30")
    ]

    # Mock da tabela
    table = MagicMock()

    # Função para simular table.find_elements com base em parâmetros
    def find_elements_mock(by=None, value=None):
        if by == "xpath" and value == ".//thead/tr/th":
            return header_cells
        elif by == "xpath" and value == ".//tbody/tr":
            return [row]
        else:
            return []

    # Configura o mock para chamar a função acima
    table.find_elements.side_effect = find_elements_mock

    mock_wait.return_value = table

    scraper = MagicMock()
    result = get_atos_judiciais_proferidos(scraper)

    assert "Sentença" in result
    assert result["Sentença"]["mensal"]["Fev"] == "20"
    assert result["Sentença"]["total"] == "30"