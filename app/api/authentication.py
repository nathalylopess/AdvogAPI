from fastapi import HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.services.data_service import DataService
from app.models.schemas import Cliente 
from typing import Dict, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# Configurações de autenticação
SECRET_KEY = "CAMANA2@22" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Inicializa o contexto de criptografia com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

clientes_db = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Criação e verificação de hash de senha
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> Optional[Cliente]:
    return clientes_db.get(username)

def authenticate_user(username: str, password: str) -> Optional[Cliente]:
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
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
    
    user = get_user(username)
    if not user:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Cliente = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

def get_data_service():
    return DataService(auto_load=True)