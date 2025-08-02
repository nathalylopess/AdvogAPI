from pydantic import BaseModel, Field
from typing import Dict, Optional

class ProcessosNaoJulgados(BaseModel):
    total: Optional[str] = Field(..., example="100", alias="Total")
    mais_60_dias: Optional[str] = Field(..., example="10", alias="+60 dias")
    mais_100_dias: Optional[str] = Field(..., example="5", alias="+100 dias")

    class Config:
            allow_population_by_field_name = True
            json_encoders = {
                "mais_60_dias": lambda v: str(v),
                "mais_100_dias": lambda v: str(v)
            }

class ProcessosTramitacao(BaseModel):
    total: str = Field(..., example="500", alias="Total")
    mais_60_dias: str = Field(..., example="50", alias="+60 dias")
    mais_100_dias: str = Field(..., example="25", alias="+100 dias")
    nao_julgados: Optional[ProcessosNaoJulgados] = Field(
        None, 
        alias="Não julgados",
        description="Dados dos processos não julgados"
    )

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            "mais_60_dias": lambda v: str(v),
            "mais_100_dias": lambda v: str(v)
        }

class ProcedimentoPeticao(BaseModel):
    total: str = Field(..., example="77", alias="Total")
    mais_60_dias: str = Field(..., example="6", alias="+60 dias")
    mais_100_dias: str = Field(..., example="0", alias="+100 dias")

    class Config:
        allow_population_by_field_name = True

class SuspensosArquivoProvisorioItem(BaseModel):
    total: str = Field(..., alias="Total", example="18")
    mais_60_dias: str = Field(..., alias="+60 dias", example="0")
    mais_100_dias: str = Field(..., alias="+100 dias", example="14")
    mais_730_dias: str = Field(..., alias="+730 dias", example="4")

    class Config:
        allow_population_by_field_name = True

class ProcessoConclusoPorTipo(BaseModel):
    total: str = Field(..., alias="Total", example="68")
    mais_60_dias: str = Field(..., alias="+60 dias", example="0")
    mais_100_dias: str = Field(..., alias="+100 dias", example="0")

    class Config:
        allow_population_by_field_name = True

class ControleDePrisoes(BaseModel):
    total: str = Field(..., alias="Total", example="6")

    class Config:
        allow_population_by_field_name = True

class ControleDeDiligenciasItem(BaseModel):
    total: str = Field(..., alias="Total", example="62")

    class Config:
        allow_population_by_field_name = True

class UnidadeData(BaseModel):
    id: int = Field(..., example=1)
    unidade: str = Field(..., example="1ª Vara Cível")
    acervo_total: str = Field(..., example="1500")
    processos_em_tramitacao: Dict[str, ProcessosTramitacao] = Field(
        ...,
        example={
            "CONHECIMENTO": {
                "Total": "800",
                "+60 dias": "80",
                "+100 dias": "40",
                "Não julgados": {
                    "Total": "600",
                    "+60 dias": "60",
                    "+100 dias": "30"
                }
            }
        }
    )
    procedimentos_e_peticoes_em_tramitacao: Optional[Dict[str, ProcedimentoPeticao]] = Field(
        None,
        alias="procedimentos_e_peticoes_em_tramitacao",
        description="Dados dos procedimentos e petições em tramitação"
    )
    suspensos_arquivo_provisorio: Optional[Dict[str, SuspensosArquivoProvisorioItem]] = Field(
        None,
        description="Dados da tabela de Suspensos / Arquivo provisório",
        example={
            "Recurso Especial Repetitivo": {
                "Total": "18",
                "+60 dias": "0",
                "+100 dias": "14",
                "+730 dias": "4"
            },
            "Outros Motivos": {
                "Total": "197",
                "+60 dias": "16",
                "+100 dias": "115",
                "+730 dias": "38"
            }
        }
    )

    processos_conclusos_por_tipo: Optional[Dict[str, ProcessoConclusoPorTipo]] = Field(
        None,
        description="Dados da tabela de Processos Conclusos por Tipo",
        example={
            "Decisão": {
                "Total": "68",
                "+60 dias": "0",
                "+100 dias": "0"
            },
            "Despacho": {
                "Total": "13",
                "+60 dias": "0",
                "+100 dias": "0"
            },
            "Sentença": {
                "Total": "21",
                "+60 dias": "1",
                "+100 dias": "0"
            },
            "Total de processos conclusos": {
                "Total": "102",
                "+60 dias": "1",
                "+100 dias": "0"
            }
        }
    )

    controle_de_prisoes: Optional[Dict[str, ControleDePrisoes]] = Field(
        None,
        description="Dados da tabela de Controle de Prisões",
        example={
            "Não identificada": {
                "Total": "6"
            },
            "Preventiva": {
                "Total": "12"
            },
            "Temporária": {
                "Total": "3"
            }
        }
    )

    controle_de_diligencias: Optional[Dict[str, ControleDeDiligenciasItem]] = Field(
        None,
        description="Dados da tabela de Controle de Diligências (PJe)",
        example={
            "Aguardando Perícia, Laudo Técnico ou Outros": {
                "Total": "62"
            },
            "COJUD": {
                "Total": "39"
            },
            "INQUÉRITO REMETIDO AO MP": {
                "Total": "7"
            }
        }
    )

    class Config:
        allow_population_by_field_name = True