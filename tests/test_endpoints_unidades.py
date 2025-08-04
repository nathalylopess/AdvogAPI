import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.api.endpoints import get_data_service
from app.main import app

# Remove essa linha — não use instância global do TestClient
# client = TestClient(app)

def mock_unit():
    return {
        "id": 1,
        "unidade": "1ª Vara",
        "acervo_total": 100,
        "processos_em_tramitacao": {
            "CONHECIMENTO": {
                "Total": 10,
                "+60 dias": 2,
                "+100 dias": 1,
                "Não julgados": {
                    "Total": 8,
                    "+60 dias": 1,
                    "+100 dias": 0
                }
            }
        },
        "procedimentos_e_peticoes_em_tramitacao": {"Pedido A": {"Total": 5}},
        "suspensos_arquivo_provisorio": {},
        "processos_conclusos_por_tipo": {"Sentença": 3},
        "controle_de_prisoes": {"Preventiva": 2},
        "controle_de_diligencias": {"Grupo X": 4},
        "demonstrativo_de_distribuicoes": {"Entradas": {"mensal": {"Jan": "3"}, "total": "3"}},
        "processos_baixados": {"Baixados": {"mensal": {"Jan": "1"}, "total": "1"}},
        "atos_judiciais_proferidos": {"Despacho": {"mensal": {"Jan": "2"}, "total": "2"}}
    }

@pytest.fixture
def client_with_override():
    mock_service = MagicMock()
    mock_service.data = [mock_unit()]
    mock_service.debug_file_path.return_value = None
    app.dependency_overrides[get_data_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides = {}

def get_auth_token(client: TestClient, username="cami", password="123") -> str:
    response = client.post(
        "/api/v1/auth/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    token = response.json().get("access_token")
    assert token is not None
    return token

# def test_list_unidades(client_with_override):
#     token = get_auth_token(client_with_override)
#     headers = {"Authorization": f"Bearer {token}"}

#     response = client_with_override.get("/api/v1/unidades", headers=headers)
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert response.json()[0]["unidade"] == "1ª Vara"

# def test_get_processos(client_with_override):
#     token = get_auth_token(client_with_override)
#     headers = {"Authorization": f"Bearer {token}"}

#     response = client_with_override.get("/api/v1/unidades/processos", headers=headers)
#     assert response.status_code == 200
#     assert response.json()[0]["unidade"] == "1ª Vara"
#     assert "CONHECIMENTO" in response.json()[0]["processos_em_tramitacao"]

# def test_get_procedimentos(client_with_override):
#     token = get_auth_token(client_with_override)
#     headers = {"Authorization": f"Bearer {token}"}

#     response = client_with_override.get("/api/v1/unidades/procedimentos", headers=headers)
#     assert response.status_code == 200
#     assert response.json()[0]["procedimentos_e_peticoes_em_tramitacao"]["Pedido A"]["Total"] == 5

# def test_get_procedimentos_empty():
#     mock_service = MagicMock()
#     mock_service.data = [{"id": 2, "unidade": "2ª Vara"}]
#     app.dependency_overrides[get_data_service] = lambda: mock_service

#     client = TestClient(app)  # cria cliente **após** override
#     token = get_auth_token(client)
#     headers = {"Authorization": f"Bearer {token}"}

#     response = client.get("/api/v1/unidades/procedimentos", headers=headers)
#     app.dependency_overrides = {}

#     assert response.status_code == 404
#     assert "Nenhum dado de procedimentos" in response.text
