from sqlmodel import SQLModel, Field
from typing import Dict, Optional

# Usado para entrada e leitura (sem table=True)
class UserBase(SQLModel):
    username: str
    disabled: Optional[bool] = False

class UserCreate(UserBase):
    password: str

# Usado para persistência no banco
class Cliente(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None