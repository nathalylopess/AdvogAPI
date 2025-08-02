# from fastapi import APIRouter, HTTPException, Depends
# from fastapi.responses import JSONResponse
# from app.services.data_service import DataService
# from app.models.schemas import UnidadeData
# from typing import List, Dict
# import logging

# router = APIRouter(
#     prefix="/api/v1",
#     tags=["unidades"],
#     responses={404: {"description": "Não encontrado"}}
# )

# logger = logging.getLogger(__name__)

# def get_data_service():
#     return DataService(auto_load=True)

# def transform_process_data(data: Dict) -> Dict:
#     return {
#         "Total": data.get("Total"),
#         "+60 dias": data.get("+60 dias"),
#         "+100 dias": data.get("+100 dias"),
#         **({
#             "Não julgados": {
#                 "Total": data["Não julgados"].get("Total"),
#                 "+60 dias": data["Não julgados"].get("+60 dias"),
#                 "+100 dias": data["Não julgados"].get("+100 dias")
#             }
#         } if "Não julgados" in data else {})
#     }

# def transform_unit_data(data: Dict) -> Dict:
#     try:
#         return {
#             "id": data.get("id"),
#             "unidade": data.get("unidade"),
#             "acervo_total": data.get("acervo_total"),
#             "processos_em_tramitacao": {
#                 k: transform_process_data(v)
#                 for k, v in data.get("processos_em_tramitacao", {}).items()
#             }
#         }
#     except Exception as e:
#         logger.error(f"Erro ao transformar dados da unidade: {str(e)}")
#         raise HTTPException(500, f"Erro ao processar unidade ID {data.get('id')}")

# def find_unit_by_id(data: List[Dict], unit_id: int) -> Dict:
#     unit = next((u for u in data if u.get("id") == unit_id), None)
#     if not unit:
#         raise HTTPException(404, f"Unidade com ID {unit_id} não encontrada")
#     return unit

# @router.get(
#     "/unidades",
#     response_model=List[UnidadeData],
#     summary="Lista todas as unidades",
#     description="Retorna todos os dados coletados das unidades judiciárias"
# )
# async def list_unidades(service: DataService = Depends(get_data_service)):
#     service.debug_file_path()

#     if not service.data:
#         raise HTTPException(404, "Nenhum dado encontrado. Execute o scraper primeiro.")

#     try:
#         return [transform_unit_data(unit) for unit in service.data]
#     except Exception as e:
#         logger.error(f"Erro ao processar lista de unidades: {str(e)}")
#         raise HTTPException(500, "Erro ao processar os dados das unidades")

# @router.get(
#     "/unidades/{unit_id}",
#     response_model=UnidadeData,
#     summary="Obtém uma unidade específica"
# )
# async def get_unidade(
#     unit_id: int,
#     service: DataService = Depends(get_data_service)
# ):
#     try:
#         unit = find_unit_by_id(service.data, unit_id)
#         return transform_unit_data(unit)
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erro ao processar unidade {unit_id}: {str(e)}")
#         raise HTTPException(500, f"Erro ao processar unidade ID {unit_id}")

# @router.get(
#     "/unidades/{unit_id}/processos",
#     summary="Processos em tramitação de uma unidade específica",
#     description="Retorna apenas os dados de processos em tramitação"
# )
# async def get_processos_unidade(
#     unit_id: int,
#     service: DataService = Depends(get_data_service)
# ):
#     try:
#         unit = find_unit_by_id(service.data, unit_id)
#         processos = {
#             k: transform_process_data(v)
#             for k, v in unit.get("processos_em_tramitacao", {}).items()
#         }
#         return JSONResponse(content=processos)
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Erro ao processar processos da unidade {unit_id}: {str(e)}")
#         raise HTTPException(500, f"Erro ao processar processos da unidade {unit_id}")
