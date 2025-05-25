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

    class Config:
        allow_population_by_field_name = True