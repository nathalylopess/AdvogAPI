from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.services.data_service import DataService
from app.models.schemas import UnidadeData, ProcessosTramitacao
from typing import List, Dict
import logging

router = APIRouter(
    prefix="/api/v1",
    tags=["unidades"],
    responses={404: {"description": "Não encontrado"}}
)

logger = logging.getLogger(__name__)

def get_data_service():
    return DataService()

def _transform_process_data(process_data: Dict) -> Dict:
    """Transforma os dados brutos dos processos para o formato do schema"""
    transformed = {
        "Total": process_data.get("Total"),
        "+60 dias": process_data.get("+60 dias"),
        "+100 dias": process_data.get("+100 dias")
    }
    
    if "Não julgados" in process_data:
        transformed["Não julgados"] = {
            "Total": process_data["Não julgados"].get("Total"),
            "+60 dias": process_data["Não julgados"].get("+60 dias"),
            "+100 dias": process_data["Não julgados"].get("+100 dias")
        }
    
    return transformed

def _transform_unit_data(unit_data: Dict) -> Dict:
    """Transforma os dados brutos da unidade para o formato do schema"""
    try:
        transformed = {
            "id": unit_data["id"],
            "unidade": unit_data["unidade"],
            "acervo_total": unit_data["acervo_total"],
            "processos_em_tramitacao": {
                key: _transform_process_data(value)
                for key, value in unit_data["processos_em_tramitacao"].items()
            }
        }
        return transformed
    except KeyError as e:
        logger.error(f"Erro ao transformar dados da unidade: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar dados da unidade {unit_data.get('id')}"
        )

@router.get(
    "/unidades",
    response_model=List[UnidadeData],
    summary="Lista todas as unidades",
    description="Retorna todos os dados coletados das unidades judiciárias"
)
async def list_unidades(service: DataService = Depends(get_data_service)):
    service.debug_file_path()
    if not service.data:
        raise HTTPException(
            status_code=404,
            detail="Nenhum dado encontrado. Execute o scraper primeiro."
        )
    
    try:
        # Transforma todos os dados para o formato do schema
        transformed_data = [
            _transform_unit_data(unit)
            for unit in service.data
        ]
        return transformed_data
    except Exception as e:
        logger.error(f"Erro ao processar lista de unidades: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Erro ao processar os dados das unidades"
        )

@router.get(
    "/unidades/{unit_id}",
    response_model=UnidadeData,
    summary="Obtém uma unidade específica",
    responses={
        200: {"description": "Dados da unidade retornados com sucesso"},
        404: {"description": "Unidade não encontrada"},
        500: {"description": "Erro ao processar dados da unidade"}
    }
)
async def get_unidade(
    unit_id: int, 
    service: DataService = Depends(get_data_service)
):
    unit = next((u for u in service.data if u["id"] == unit_id), None)
    if not unit:
        raise HTTPException(
            status_code=404,
            detail=f"Unidade com ID {unit_id} não encontrada"
        )
    
    try:
        return _transform_unit_data(unit)
    except Exception as e:
        logger.error(f"Erro ao processar unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar dados da unidade {unit_id}"
        )

@router.get(
    "/unidades/{unit_id}/processos",
    summary="Processos em tramitação de uma unidade específica",
    description="Retorna apenas os dados de processos em tramitação",
    responses={
        200: {"description": "Dados de processos retornados com sucesso"},
        404: {"description": "Unidade não encontrada"},
        500: {"description": "Erro ao processar dados de processos"}
    }
)
async def get_processos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    unit = next((u for u in service.data if u["id"] == unit_id), None)
    if not unit:
        raise HTTPException(status_code=404, detail="Unidade não encontrada")
    
    try:
        processos = {
            key: _transform_process_data(value)
            for key, value in unit["processos_em_tramitacao"].items()
        }
        return JSONResponse(content=processos)
    except Exception as e:
        logger.error(f"Erro ao processar processos da unidade {unit_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar processos da unidade {unit_id}"
        )