from fastapi import APIRouter, HTTPException, Depends, status, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from app.services.data_service import DataService
from app.models.schemas import UnidadeData, ProcessosTramitacao, Cliente, UserCreate, Token
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt

router = APIRouter(
    prefix="/api/v1",
    tags=["unidades"],
    responses={404: {"description": "Não encontrado"}}
)

logger = logging.getLogger(__name__)

# Configurações de autenticação
SECRET_KEY = "CAMANA2@22" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

clientes_db = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

def fake_hash_password(password: str):
    return "fakehashedCAMANA2@22_364736473" + password  

def get_user(username: str) -> Optional[Cliente]:
    return clientes_db.get(username)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or not user.hashed_password == fake_hash_password(password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if (user := get_user(username)) is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Cliente = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

def get_data_service():
    return DataService(auto_load=True)

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

# Rotas de Autenticação

@router.post(
    "/token",
    response_model=Token,
    summary="Obter token de acesso",
    description="Autentica o usuário e retorna um token JWT para uso nas rotas protegidas"
)
async def login(
    username: str = Form(..., description="Nome de usuário"),
    password: str = Form(..., description="Senha"),
    grant_type: str = Form(default="password", regex="^password$")
):
    user = authenticate_user(username, password)
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

@router.post(
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
        hashed_password=fake_hash_password(usuario.password),
        id=len(clientes_db) + 1,
        cpf=usuario.cpf if hasattr(usuario, 'cpf') else "",
        telefone=usuario.telefone if hasattr(usuario, 'telefone') else ""
    )
    clientes_db[usuario.username] = db_usuario
    return db_usuario

@router.get(
    "/usuarios/atual",
    response_model=Cliente,
    summary="Dados do usuário atual",
    description="Retorna os dados do usuário autenticado"

)
async def get_usuario_atual(current_user: Cliente = Depends(get_current_active_user)):
    return current_user


# Rotas de Unidades agora protegidas

@router.get(
    "/unidades",
    response_model=List[UnidadeData],
    summary="Listar todas as unidades",
    description="Retorna todos os dados coletados das unidades judiciárias",
    responses={
        200: {"description": "Dados retornados com sucesso"},
        404: {"description": "Nenhum dado encontrado"},
        500: {"description": "Erro ao processar dados"}
    }
)
async def list_unidades(
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
):
    service.debug_file_path()
    if not service.data:
        raise HTTPException(
            status_code=404,
            detail="Nenhum dado encontrado. Execute o scraper primeiro."
        )
    
    try:
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
    summary="Obter unidade específica",
    description="Retorna os dados de uma unidade judiciária específica",
    responses={
        200: {"description": "Dados da unidade retornados com sucesso"},
        404: {"description": "Unidade não encontrada"},
        500: {"description": "Erro ao processar dados da unidade"}
    }
)
async def get_unidade(
    unit_id: int, 
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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
    summary="Processos em tramitação",
    description="Retorna os processos em tramitação de uma unidade específica",
    responses={
        200: {"description": "Dados de processos retornados com sucesso"},
        404: {"description": "Unidade não encontrada"},
        500: {"description": "Erro ao processar dados de processos"}
    }
)
async def get_processos_unidade(
    unit_id: int,
    service: DataService = Depends(get_data_service),
    current_user: Cliente = Depends(get_current_active_user)
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