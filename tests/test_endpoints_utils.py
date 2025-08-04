import pytest
from fastapi import HTTPException
from app.api.endpoints import (
    transform_process_data,
    transform_dict_with_total,
    transform_unit_data,
    transform_controle_de_prisoes,
    find_unit_by_id
)

# --------- transform_process_data ---------
def test_transform_process_data_completo():
    entrada = {
        "Total": 10,
        "+60 dias": 3,
        "+100 dias": 2,
        "Não julgados": {
            "Total": 5,
            "+60 dias": 2,
            "+100 dias": 1
        }
    }
    esperado = {
        "Total": "10",
        "+60 dias": "3",
        "+100 dias": "2",
        "Não julgados": {
            "Total": "5",
            "+60 dias": "2",
            "+100 dias": "1"
        }
    }
    assert transform_process_data(entrada) == esperado

def test_transform_process_data_sem_nao_julgados():
    entrada = {"Total": 8, "+60 dias": 1, "+100 dias": 0}
    resultado = transform_process_data(entrada)
    assert resultado == {"Total": "8", "+60 dias": "1", "+100 dias": "0"}

# --------- transform_dict_with_total ---------
def test_transform_dict_with_total_valido():
    entrada = {"Grupo A": 5, "Grupo B": {"Total": "3"}}
    esperado = {"Grupo A": {"Total": "5"}, "Grupo B": {"Total": "3"}}
    assert transform_dict_with_total(entrada) == esperado

def test_transform_dict_with_total_none():
    assert transform_dict_with_total(None) is None

def test_transform_dict_with_total_nao_dict():
    assert transform_dict_with_total([1, 2, 3]) is None

# --------- transform_controle_de_prisoes ---------
def test_transform_controle_de_prisoes_str():
    assert transform_controle_de_prisoes("12") == {"Total": "12"}

def test_transform_controle_de_prisoes_dict():
    entrada = {"Total": 7}
    assert transform_controle_de_prisoes(entrada) == {"Total": "7"}

def test_transform_controle_de_prisoes_none():
    assert transform_controle_de_prisoes(None) == {}

# --------- transform_unit_data ---------
def test_transform_unit_data_valido():
    dados = {
        "id": 1,
        "unidade": "TJRN",
        "acervo_total": 100,
        "processos_em_tramitacao": {
            "CONHECIMENTO": {
                "Total": 20,
                "+60 dias": 5,
                "+100 dias": 3,
                "Não julgados": {
                    "Total": 10,
                    "+60 dias": 2,
                    "+100 dias": 1
                }
            }
        },
        "procedimentos_e_peticoes_em_tramitacao": {},
        "suspensos_arquivo_provisorio": {},
        "processos_conclusos_por_tipo": {"Decisão": {"Total": "5"}},
        "controle_de_prisoes": {"Preventiva": 2},
        "controle_de_diligencias": {"Grupo X": 4},
        "demonstrativo_de_distribuicoes": {"Entradas": {"Total": "12"}},
        "processos_baixados": {"Baixados": {"Total": "6"}},
        "atos_judiciais_proferidos": {"Sentenças": {"Total": "15"}}
    }
    resultado = transform_unit_data(dados)
    assert resultado["id"] == 1
    assert resultado["unidade"] == "TJRN"
    assert resultado["processos_em_tramitacao"]["CONHECIMENTO"]["+60 dias"] == "5"
    assert resultado["controle_de_prisoes"]["Preventiva"]["Total"] == "2"

# --------- find_unit_by_id ---------
def test_find_unit_by_id_encontrado():
    unidades = [{"id": 1, "unidade": "A"}, {"id": 2, "unidade": "B"}]
    unidade = find_unit_by_id(unidades, 2)
    assert unidade["unidade"] == "B"

def test_find_unit_by_id_nao_encontrado():
    unidades = [{"id": 1}, {"id": 2}]
    with pytest.raises(HTTPException) as exc:
        find_unit_by_id(unidades, 3)
    assert exc.value.status_code == 404