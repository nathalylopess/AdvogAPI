from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.services.data_service import DataService
from app.models.user import Cliente
from app.core.database import get_session
from typing import Optional
from datetime import datetime, timedelta, timezone
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

# OAuth2 token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Hash e verificação de senhas
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Busca usuário por username
def get_user(username: str, session: Session) -> Optional[Cliente]:
    statement = select(Cliente).where(Cliente.username == username)
    return session.exec(statement).first()

# Autenticação de usuário
def authenticate_user(username: str, password: str, session: Session) -> Optional[Cliente]:
    user = get_user(username, session)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Criação de token JWT
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Recupera o usuário autenticado com base no token
def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
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

    user = get_user(username, session)
    if not user:
        raise credentials_exception
    return user

# Verifica se o usuário está ativo
def get_current_active_user(current_user: Cliente = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    return current_user

# Dependência do serviço de dados
def get_data_service():
    return DataService(auto_load=True)
