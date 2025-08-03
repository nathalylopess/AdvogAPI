from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from app.services.data_service import DataService
from app.models.schemas import UnidadeData
from typing import List, Dict
import logging

router = APIRouter(
    prefix="/api/v1",
    tags=["unidades"],
    responses={404: {"description": "Não encontrado"}}
)

logger = logging.getLogger(__name__)

def get_data_service():
    return DataService(auto_load=True)

def transform_process_data(data: Dict) -> Dict:
    def safe_str(value):
        return str(value) if value is not None else ""

    result = {
        "Total": safe_str(data.get("Total")),
        "+60 dias": safe_str(data.get("+60 dias")),
        "+100 dias": safe_str(data.get("+100 dias")),
    }

    if "Não julgados" in data:
        result["Não julgados"] = {
            "Total": safe_str(data["Não julgados"].get("Total")),
            "+60 dias": safe_str(data["Não julgados"].get("+60 dias")),
            "+100 dias": safe_str(data["Não julgados"].get("+100 dias")),
        }

    return result

def transform_unit_data(data: Dict) -> Dict:
    try:
        return {
            "id": data.get("id"),
            "unidade": data.get("unidade"),
            "acervo_total": data.get("acervo_total"),
            "processos_em_tramitacao": {
                k: transform_process_data(v)
                for k, v in data.get("processos_em_tramitacao", {}).items()
            }
        }
    except Exception as e:
        logger.error(f"Erro ao transformar dados da unidade: {str(e)}")
        raise HTTPException(500, f"Erro ao processar unidade ID {data.get('id')}")

def transform_controle_de_prisoes(data) -> Dict:
    def safe_str(value):
        return str(value) if value is not None else ""

    # Se já for string, retorna diretamente
    if isinstance(data, str):
        return {
            "Total": data
        }

    # Se for dict, transforma normalmente
    if isinstance(data, dict):
        return {
            "Total": safe_str(data.get("Total")),
        }
    
    # Caso seja None ou outro tipo, retorna vazio
    return {}

def find_unit_by_id(data: List[Dict], unit_id: int) -> Dict:
    unit = next((u for u in data if u.get("id") == unit_id), None)
    if not unit:
        raise HTTPException(404, f"Unidade com ID {unit_id} não encontrada")
    return unit

@router.get(
    "/unidades",
    response_model=List[UnidadeData],
    summary="Lista todas as unidades",
    description="Retorna todos os dados coletados das unidades judiciárias"
)
async def list_unidades(service: DataService = Depends(get_data_service)):
    service.debug_file_path()

    if not service.data:
        raise HTTPException(404, "Nenhum dado encontrado. Execute o scraper primeiro.")

    try:
        return [transform_unit_data(unit) for unit in service.data]
    except Exception as e:
        logger.error(f"Erro ao processar lista de unidades: {str(e)}")
        raise HTTPException(500, "Erro ao processar os dados das unidades")

@router.get(
    "/unidades/{unit_id}",
    response_model=UnidadeData,
    summary="Obtém uma unidade específica"
)
async def get_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        return transform_unit_data(unit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar unidade ID {unit_id}")

@router.get(
    "/unidades/{unit_id}/processos",
    summary="Processos em tramitação de uma unidade específica",
    description="Retorna apenas os dados de processos em tramitação"
)
async def get_processos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        processos = {
            k: transform_process_data(v)
            for k, v in unit.get("processos_em_tramitacao", {}).items()
        }
        return JSONResponse(content=processos)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar processos da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar processos da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/procedimentos",
    summary="Procedimentos e petições em tramitação de uma unidade específica",
    description="Retorna apenas os dados de procedimentos e petições em tramitação"
)
async def get_procedimentos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)

        procedimentos = unit.get("procedimentos_e_peticoes_em_tramitacao", None)
        if procedimentos is None:
            raise HTTPException(404, f"Nenhum dado de procedimentos/petições encontrado para a unidade {unit_id}")

        return JSONResponse(content=procedimentos)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar procedimentos da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar procedimentos da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/suspensos",
    summary="Suspensos / Arquivo provisório de uma unidade específica",
    description="Retorna os dados de processos suspensos ou em arquivo provisório de uma unidade judiciária"
)
async def get_suspensos_arquivo_provisorio_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)

        suspensos = unit.get("suspensos_arquivo_provisorio")
        if suspensos is None:
            raise HTTPException(404, f"Nenhum dado de suspensos/arquivo provisório encontrado para a unidade {unit_id}")

        return JSONResponse(content=suspensos)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar dados de suspensos da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar dados de suspensos da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/processos_conclusos_por_tipo",
    summary="Processos conclusos por tipo de uma unidade específica",
    description="Retorna os dados de processos conclusos por tipo para uma unidade judiciária específica"
)
async def get_processos_conclusos_por_tipo(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        conclusos = unit.get("processos_conclusos_por_tipo", {})

        if not conclusos:
            raise HTTPException(404, f"Dados de 'processos_conclusos_por_tipo' não encontrados para unidade ID {unit_id}")

        def safe_str(value):
            return str(value) if value is not None else ""

        result = {
            tipo: {
                "Total": safe_str(dados.get("Total")),
                "+60 dias": safe_str(dados.get("+60 dias")),
                "+100 dias": safe_str(dados.get("+100 dias")),
            }
            for tipo, dados in conclusos.items()
        }

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar processos conclusos da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar processos conclusos da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/controle_de_prisoes",
    summary="Controle de prisões de uma unidade específica",
    description="Retorna os dados da tabela de Controle de Prisões da unidade especificada"
)

async def get_controle_de_prisoes(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        controle = unit.get("controle_de_prisoes")
        if controle is None:
            raise HTTPException(404, f"Controle de prisões da unidade {unit_id} não encontrado")

        controle_transformado = transform_controle_de_prisoes(controle)
        return JSONResponse(content=controle_transformado)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar controle de prisões da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar controle de prisões da unidade {unit_id}")
    
@router.get(
    "/unidades/{unit_id}/controle_de_diligencias",
    summary="Controle de diligências de uma unidade específica",
    description="Retorna os dados da tabela de Controle de Diligências (PJe) da unidade especificada"
)
async def get_controle_de_diligencias_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        controle = unit.get("controle_de_diligencias")

        if controle is None:
            raise HTTPException(404, f"Controle de diligências não encontrado para a unidade {unit_id}")

        return JSONResponse(content=controle)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar controle de diligências da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar controle de diligências da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/distribuicoes",
    summary="Demonstrativo de distribuições da unidade",
    description="Retorna apenas os dados do Demonstrativo de Distribuições (últimos 12 meses)"
)
async def get_distribuicoes_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        distrib = unit.get("demonstrativo_de_distribuicoes")

        if distrib is None:
            raise HTTPException(404, f"Dados de demonstrativo de distribuições não encontrados para a unidade {unit_id}")

        return JSONResponse(content=distrib)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar distribuições da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar distribuições da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/processos_baixados",
    summary="Processos baixados de uma unidade específica",
    description="Retorna apenas os dados da tabela de processos baixados nos últimos 12 meses"
)
async def get_processos_baixados_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)

        processos_baixados = unit.get("processos_baixados")
        if not processos_baixados:
            raise HTTPException(404, f"Dados de 'processos baixados' não encontrados para a unidade {unit_id}")

        return JSONResponse(content=processos_baixados)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar processos baixados da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar processos baixados da unidade {unit_id}")

@router.get(
    "/unidades/{unit_id}/atos-judiciais",
    summary="Atos judiciais proferidos de uma unidade específica",
    description="Retorna apenas os dados da tabela de atos judiciais proferidos nos últimos 12 meses"
)
async def get_atos_judiciais_proferidos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        atos = unit.get("atos_judiciais_proferidos")

        if atos is None:
            raise HTTPException(404, f"A unidade {unit_id} não possui dados de atos judiciais proferidos")

        return JSONResponse(content=atos)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar atos judiciais da unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar atos judiciais da unidade {unit_id}")