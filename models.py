from pydantic import BaseModel
from datetime import date
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class Carro(BaseModel):
    id: int
    modelo: str
    marca: str
    ano: int
    disponivel: bool

class Cliente(UserInDB):
    id: int
    cpf: str
    telefone: str

class Reserva(BaseModel):
    id: int
    cliente_id: int
    carro_id: int
    data_inicio: date
    data_fim: date