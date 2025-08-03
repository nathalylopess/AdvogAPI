from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.services.data_service import DataService
from app.models.schemas import UnidadeData, Cliente, UserCreate, Token
from typing import List, Dict, Optional
import logging

from datetime import timedelta

from app.api.authentication import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    hash_password,
    clientes_db,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# Router principal - Rotas gerais
router = APIRouter(
    prefix="/api/v1",
    tags=["unidades"],
    responses={404: {"description": "Não encontrado"}}
)

# Router de autenticação
router_auth = APIRouter(
    prefix="/api/v1/auth",
    tags=["autenticação"],
    responses={404: {"description": "Não encontrado"}}
)

# Router específico - Rotas por unidade específica
router_unidade = APIRouter(
    prefix="/api/v1/unidades",
    tags=["unidade específica"],
    responses={404: {"description": "Unidade não encontrada"}}
)

logger = logging.getLogger(__name__)

# Rotas de Autenticação
@router_auth.post(
    "/token",
    response_model=Token,
    summary="Obter token de acesso",
    description="Autentica o usuário e retorna um token JWT para uso nas rotas protegidas"
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router_auth.post(
    "/usuarios",
    response_model=Cliente,
    summary="Criar novo usuário",
    description="Registra um novo usuário no sistema",
    status_code=status.HTTP_201_CREATED
)
async def criar_usuario(usuario: UserCreate):
    if usuario.username in clientes_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já existe"
        )

    db_usuario = Cliente(
        **usuario.dict(exclude={"password"}),
        hashed_password=hash_password(usuario.password),
        id=len(clientes_db) + 1
    )

    clientes_db[usuario.username] = db_usuario
    return db_usuario

@router_auth.get(
    "/usuarios/atual",
    response_model=Cliente,
    summary="Dados do usuário atual",
    description="Retorna os dados do usuário autenticado"

)
async def get_usuario_atual(current_user: Cliente = Depends(get_current_active_user)):
    return current_user

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

def transform_dict_with_total(data: Optional[Dict]) -> Optional[Dict[str, Dict[str, str]]]:
    if not isinstance(data, dict):
        return None
    return {
        k: {"Total": str(v)} if not isinstance(v, dict) else v
        for k, v in data.items()
    }

def transform_unit_data(data: Dict) -> Dict:
    try:
        return {
            "id": data.get("id"),
            "unidade": data.get("unidade"),
            "acervo_total": data.get("acervo_total"),
            "processos_em_tramitacao": {
                k: transform_process_data(v)
                for k, v in data.get("processos_em_tramitacao", {}).items()
            },
            "procedimentos_e_peticoes_em_tramitacao": data.get("procedimentos_e_peticoes_em_tramitacao"),
            "suspensos_arquivo_provisorio": data.get("suspensos_arquivo_provisorio"),
            "processos_conclusos_por_tipo": transform_dict_with_total(data.get("processos_conclusos_por_tipo")),
            "controle_de_prisoes": transform_dict_with_total(data.get("controle_de_prisoes")),
            "controle_de_diligencias": transform_dict_with_total(data.get("controle_de_diligencias")),
            "demonstrativo_de_distribuicoes": transform_dict_with_total(data.get("demonstrativo_de_distribuicoes")),
            "processos_baixados": transform_dict_with_total(data.get("processos_baixados")),
            "atos_judiciais_proferidos": transform_dict_with_total(data.get("atos_judiciais_proferidos")),
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
async def list_unidades(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    
    service.debug_file_path()

    if not service.data:
        raise HTTPException(404, "Nenhum dado encontrado. Execute o scraper primeiro.")

    try:
        return [transform_unit_data(unit) for unit in service.data]
    except Exception as e:
        logger.error(f"Erro ao processar lista de unidades: {str(e)}")
        raise HTTPException(500, "Erro ao processar os dados das unidades")

@router.get(
    "/unidades/processos",
    summary="Processos em tramitação de todas as unidades",
    description="Retorna os dados de processos em tramitação para todas as unidades"
)
async def get_processos(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            processos = {
                k: transform_process_data(v)
                for k, v in unit.get("processos_em_tramitacao", {}).items()
            }
            resultados.append({
                "id": unit.get("id"),
                "unidade": unit.get("unidade"),
                "processos_em_tramitacao": processos
            })

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar processos gerais: {str(e)}")
        raise HTTPException(500, "Erro ao processar dados de processos")

@router.get(
    "/unidades/procedimentos",
    summary="Procedimentos e petições em tramitação de todas as unidades",
    description="Retorna os dados de procedimentos e petições em tramitação para todas as unidades"
)
async def get_procedimentos(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            procedimentos = unit.get("procedimentos_e_peticoes_em_tramitacao")
            if procedimentos:  # filtra apenas os que têm dado
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "procedimentos_e_peticoes_em_tramitacao": procedimentos
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de procedimentos/petições encontrado em nenhuma unidade")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar procedimentos gerais: {str(e)}")
        raise HTTPException(500, "Erro ao processar dados de procedimentos/petições")

@router.get(
    "/unidades/suspensos",
    summary="Suspensos / Arquivo provisório de todas as unidades",
    description="Retorna os dados de processos suspensos ou em arquivo provisório para todas as unidades"
)
async def get_suspensos_arquivo_provisorio(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            suspensos = unit.get("suspensos_arquivo_provisorio")
            if suspensos:
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "suspensos_arquivo_provisorio": suspensos
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de suspensos/arquivo provisório encontrado em nenhuma unidade")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar dados de suspensos gerais: {str(e)}")
        raise HTTPException(500, "Erro ao processar dados de suspensos/arquivo provisório")

@router.get(
    "/unidades/processos_conclusos_por_tipo",
    summary="Processos conclusos por tipo de todas as unidades",
    description="Retorna os dados de processos conclusos por tipo para todas as unidades judiciárias"
)
async def get_processos_conclusos_por_tipo(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        def safe_str(value):
            return str(value) if value is not None else ""

        resultados = []

        for unit in service.data:
            conclusos = unit.get("processos_conclusos_por_tipo", {})
            if conclusos:
                dados_formatados = {
                    tipo: {
                        "Total": safe_str(d.get("Total")),
                        "+60 dias": safe_str(d.get("+60 dias")),
                        "+100 dias": safe_str(d.get("+100 dias")),
                    }
                    for tipo, d in conclusos.items()
                }

                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "processos_conclusos_por_tipo": dados_formatados
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de processos conclusos por tipo encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar processos conclusos gerais: {str(e)}")
        raise HTTPException(500, "Erro ao processar processos conclusos por tipo")

@router.get(
    "/unidades/controle_de_prisoes",
    summary="Controle de prisões de todas as unidades",
    description="Retorna os dados da tabela de Controle de Prisões de todas as unidades judiciárias"
)
async def get_controle_de_prisoes(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            controle = unit.get("controle_de_prisoes")
            if controle:
                controle_transformado = transform_controle_de_prisoes(controle)
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "controle_de_prisoes": controle_transformado
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de controle de prisões encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar controle de prisões geral: {str(e)}")
        raise HTTPException(500, "Erro ao processar controle de prisões")

@router.get(
    "/unidades/controle_de_diligencias",
    summary="Controle de diligências de todas as unidades",
    description="Retorna os dados da tabela de Controle de Diligências (PJe) de todas as unidades"
)
async def get_controle_de_diligencias(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            controle = unit.get("controle_de_diligencias")
            if controle:
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "controle_de_diligencias": controle
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de controle de diligências encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar controle de diligências geral: {str(e)}")
        raise HTTPException(500, "Erro ao processar controle de diligências")

@router.get(
    "/unidades/distribuicoes",
    summary="Demonstrativo de distribuições de todas as unidades",
    description="Retorna os dados do Demonstrativo de Distribuições (últimos 12 meses) de todas as unidades"
)
async def get_distribuicoes(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            distrib = unit.get("demonstrativo_de_distribuicoes")
            if distrib:
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "demonstrativo_de_distribuicoes": distrib
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de distribuições encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar demonstrativo de distribuições geral: {str(e)}")
        raise HTTPException(500, "Erro ao processar distribuições")

@router.get(
    "/unidades/processos_baixados",
    summary="Processos baixados de todas as unidades",
    description="Retorna os dados da tabela de processos baixados (últimos 12 meses) de todas as unidades"
)
async def get_processos_baixados(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            processos_baixados = unit.get("processos_baixados")
            if processos_baixados:
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "processos_baixados": processos_baixados
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de processos baixados encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar processos baixados geral: {str(e)}")
        raise HTTPException(500, "Erro ao processar processos baixados")

@router.get(
    "/unidades/atos_judiciais",
    summary="Atos judiciais proferidos de todas as unidades",
    description="Retorna os dados da tabela de atos judiciais proferidos (últimos 12 meses) de todas as unidades"
)
async def get_atos_judiciais_proferidos(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        resultados = []

        for unit in service.data:
            atos = unit.get("atos_judiciais_proferidos")
            if atos:
                resultados.append({
                    "id": unit.get("id"),
                    "unidade": unit.get("unidade"),
                    "atos_judiciais_proferidos": atos
                })

        if not resultados:
            raise HTTPException(404, "Nenhum dado de atos judiciais proferidos encontrado")

        return JSONResponse(content=resultados)

    except Exception as e:
        logger.error(f"Erro ao processar atos judiciais geral: {str(e)}")
        raise HTTPException(500, "Erro ao processar atos judiciais")

@router_unidade.get(
    "/unidades/{unit_id}",
    response_model=UnidadeData,
    summary="Obtém uma unidade específica"
)
async def get_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    try:
        unit = find_unit_by_id(service.data, unit_id)
        return transform_unit_data(unit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar unidade {unit_id}: {str(e)}")
        raise HTTPException(500, f"Erro ao processar unidade ID {unit_id}")

@router_unidade.get(
    "/unidades/{unit_id}/processos",
    summary="Processos em tramitação de uma unidade específica",
    description="Retorna apenas os dados de processos em tramitação"
)
async def get_processos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/procedimentos",
    summary="Procedimentos e petições em tramitação de uma unidade específica",
    description="Retorna apenas os dados de procedimentos e petições em tramitação"
)
async def get_procedimentos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/suspensos",
    summary="Suspensos / Arquivo provisório de uma unidade específica",
    description="Retorna os dados de processos suspensos ou em arquivo provisório de uma unidade judiciária"
)
async def get_suspensos_arquivo_provisorio_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/processos_conclusos_por_tipo",
    summary="Processos conclusos por tipo de uma unidade específica",
    description="Retorna os dados de processos conclusos por tipo para uma unidade judiciária específica"
)
async def get_processos_conclusos_por_tipo(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/controle_de_prisoes",
    summary="Controle de prisões de uma unidade específica",
    description="Retorna os dados da tabela de Controle de Prisões da unidade especificada"
)

async def get_controle_de_prisoes(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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
    
@router_unidade.get(
    "/unidades/{unit_id}/controle_de_diligencias",
    summary="Controle de diligências de uma unidade específica",
    description="Retorna os dados da tabela de Controle de Diligências (PJe) da unidade especificada"
)
async def get_controle_de_diligencias_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/distribuicoes",
    summary="Demonstrativo de distribuições da unidade",
    description="Retorna apenas os dados do Demonstrativo de Distribuições (últimos 12 meses)"
)
async def get_distribuicoes_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/processos_baixados",
    summary="Processos baixados de uma unidade específica",
    description="Retorna apenas os dados da tabela de processos baixados nos últimos 12 meses"
)
async def get_processos_baixados_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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

@router_unidade.get(
    "/unidades/{unit_id}/atos_judiciais",
    summary="Atos judiciais proferidos de uma unidade específica",
    description="Retorna apenas os dados da tabela de atos judiciais proferidos nos últimos 12 meses"
)
async def get_atos_judiciais_proferidos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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