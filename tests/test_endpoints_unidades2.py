import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.endpoints import get_data_service
from tests.test_endpoints_unidades import get_auth_token

mock_unit = {
    "id": 1,
    "unidade": "Unidade 1",
    "acervo_total": 100,
    "processos_em_tramitacao": {
        "CONHECIMENTO": {
            "Total": 10,
            "+60 dias": 3,
            "+100 dias": 1,
            "Não julgados": {
                "Total": 8,
                "+60 dias": 2,
                "+100 dias": 1
            }
        }
    },
    "procedimentos_e_peticoes_em_tramitacao": {"Petição Inicial": {"Total": 5}},
    "suspensos_arquivo_provisorio": {"Categoria A": {"Total": 2}},
    "processos_conclusos_por_tipo": {
        "Sentença": {
            "Total": 4,
            "+60 dias": 1,
            "+100 dias": 1
        }
    },
    "controle_de_prisoes": {"Preventiva": 2},
    "controle_de_diligencias": {"Grupo X": 7},
    "demonstrativo_de_distribuicoes": {"Entradas": {"Jan": 2, "Total": 2}},
    "processos_baixados": {"Baixados": {"Jan": 1, "Total": 1}},
    "atos_judiciais_proferidos": {"Sentença": {"Jan": 5, "Total": 5}}
}


@pytest.fixture
def client_with_override():
    mock_service = MagicMock()
    mock_service.data = [mock_unit]
    app.dependency_overrides[get_data_service] = lambda: mock_service
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}

@pytest.fixture
def client_with_custom_data():
    def _client(data):
        mock_service = MagicMock()
        mock_service.data = data
        app.dependency_overrides[get_data_service] = lambda: mock_service
        client = TestClient(app)
        return client
    yield _client
    app.dependency_overrides = {}


def test_get_suspensos_arquivo_provisorio(client_with_override):
    token = get_auth_token(client_with_override)
    headers = {"Authorization": f"Bearer {token}"}

    response = client_with_override.get("/api/v1/unidades/suspensos", headers=headers)
    assert response.status_code == 200
    assert response.json()[0]["suspensos_arquivo_provisorio"]["Categoria A"]["Total"] == 2


def test_get_suspensos_arquivo_provisorio_sem_dados(client_with_custom_data):
    unidade_sem_dado = mock_unit.copy()
    unidade_sem_dado["suspensos_arquivo_provisorio"] = {}

    client = client_with_custom_data([unidade_sem_dado])
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/unidades/suspensos", headers=headers)
    assert response.status_code == 404


def test_get_processos_conclusos_por_tipo(client_with_override):
    token = get_auth_token(client_with_override)
    headers = {"Authorization": f"Bearer {token}"}

    response = client_with_override.get("/api/v1/unidades/processos_conclusos_por_tipo", headers=headers)
    data = response.json()[0]["processos_conclusos_por_tipo"]

    assert data["Sentença"]["Total"] == "4"
    assert data["Sentença"]["+60 dias"] == "1"


def test_get_processos_conclusos_por_tipo_sem_dados(client_with_custom_data):
    unidade_sem_dado = mock_unit.copy()
    unidade_sem_dado["processos_conclusos_por_tipo"] = {}

    client = client_with_custom_data([unidade_sem_dado])
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/unidades/processos_conclusos_por_tipo", headers=headers)
    assert response.status_code == 404
