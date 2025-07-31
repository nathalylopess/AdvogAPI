from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Annotated, Optional
from models import *
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = "CAMANA2@22" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

carros: List[Carro] = []
clientes_db: dict[str, Cliente] = {}  
reservas: List[Reserva] = []

def fake_hash_password(password: str):
    return "fakehashed_" + password

def get_user(username: str) -> Optional[Cliente]:
    if username in clientes_db:
        return clientes_db[username]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not user.hashed_password == fake_hash_password(password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[Cliente, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login(
    username: str = Form(...),
    password: str = Form(...),
    grant_type: str = Form(default="password", regex="^password$")
):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(
    current_user: Annotated[Cliente, Depends(get_current_active_user)]
):
    return current_user

@app.post("/clientes/", response_model=Cliente)
async def create_cliente(cliente: UserCreate):
    if cliente.username in clientes_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = fake_hash_password(cliente.password)
    db_cliente = Cliente(
        **cliente.dict(exclude={"password"}),
        hashed_password=hashed_password,
        id=len(clientes_db) + 1,  
        cpf=cliente.cpf if hasattr(cliente, 'cpf') else "",
        telefone=cliente.telefone if hasattr(cliente, 'telefone') else ""
    )
    clientes_db[cliente.username] = db_cliente
    return db_cliente

@app.post('/carros/', response_model=Carro)
def cadastrar_carros(carro: Carro, current_user: Annotated[Cliente, Depends(get_current_active_user)]):
    carros.append(carro)
    return carro

@app.get('/carros/', response_model=List[Carro])
def listar_carros(current_user: Annotated[Cliente, Depends(get_current_active_user)]):
    return carros

@app.get('/carros/disponiveis', response_model=List[Carro])
def listar_carros_disponiveis(current_user: Annotated[Cliente, Depends(get_current_active_user)]):
    carros_disponiveis = [carro for carro in carros if carro.disponivel]
    return carros_disponiveis

@app.put('/carros/{carro_id}', response_model=Carro)
def atualizar_carros(carro_id: int, carro: Carro, current_user: Annotated[Cliente, Depends(get_current_active_user)]):
    for index, c in enumerate(carros):
        if c.id == carro_id:
            carros[index] = carro
            return carro
    raise HTTPException(status_code=404, detail="Não localizado")

@app.delete('/carros/{id}', response_model=Carro)
def deletar_tarefa(id: int, current_user: Annotated[Cliente, Depends(get_current_active_user)]):
    for index, carro in enumerate(carros):
        if carro.id == id:
            removed_carro = carros.pop(index)
            return removed_carro
    raise HTTPException(status_code=404, detail="Carro não encontrado")