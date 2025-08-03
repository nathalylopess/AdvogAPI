from fastapi import FastAPI
from app.api.endpoints import router, router_auth, router_unidade
from app.services.data_service import DataService
from app.core.database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API de Dados do TJRN",
    description="API para acesso aos dados coletados do TJRN",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas da API
app.include_router(router_auth)
app.include_router(router)
app.include_router(router_unidade)

@app.on_event("startup")
async def startup_event():
    """Carrega os dados ao iniciar a aplicação"""
    service = DataService(auto_load=True)
    if not service.data:
        print("⚠ Nenhum dado encontrado. Execute o scraper primeiro.")
    create_db_and_tables()

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "API de Dados do TJRN - Acesse /docs para a documentação"}