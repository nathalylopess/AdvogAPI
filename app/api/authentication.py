from fastapi import HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer
from app.services.data_service import DataService
from app.models.schemas import Cliente 
from typing import Dict, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
import logging

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