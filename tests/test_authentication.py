import pytest
from unittest.mock import MagicMock, patch
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from app.api.authentication import (
    hash_password,
    verify_password,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_active_user,
)
from app.models.user import Cliente

# Configurações do JWT
SECRET_KEY = "CAMANA2@22"
ALGORITHM = "HS256"


def test_hash_and_verify_password():
    password = "senha123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("outra", hashed) is False


def test_authenticate_user_success():
    session = MagicMock()
    user = Cliente(username="nome_de_usuario", hashed_password=hash_password("1234"))
    session.exec.return_value.first.return_value = user

    authenticated = authenticate_user("nome_de_usuario", "1234", session)
    assert authenticated == user


def test_authenticate_user_fail():
    session = MagicMock()
    user = Cliente(username="nome_de_usuario", hashed_password=hash_password("1234"))
    session.exec.return_value.first.return_value = user

    authenticated = authenticate_user("nome_de_usuario", "errado", session)
    assert authenticated is None


def test_create_access_token():
    data = {"sub": "nome_de_usuario"}
    token = create_access_token(data)
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "nome_de_usuario"
    assert "exp" in decoded


def test_get_current_user_valid():
    token_data = {"sub": "nome_de_usuario", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    session = MagicMock()
    user = Cliente(username="nome_de_usuario", hashed_password="abc")
    session.exec.return_value.first.return_value = user

    with patch("app.api.authentication.oauth2_scheme", return_value=token):
        user_out = get_current_user(token=token, session=session)
        assert user_out.username == "nome_de_usuario"


def test_get_current_user_invalid_token():
    session = MagicMock()
    invalid_token = "token.invalido"

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=invalid_token, session=session)
    assert exc.value.status_code == 401


def test_get_current_active_user_enabled():
    user = Cliente(username="nome_de_usuario", disabled=False)
    active_user = get_current_active_user(current_user=user)
    assert active_user.username == "nome_de_usuario"


def test_get_current_active_user_disabled():
    user = Cliente(username="nome_de_usuario", disabled=True)
    with pytest.raises(HTTPException) as exc:
        get_current_active_user(current_user=user)
    assert exc.value.detail == "Usuário inativo"
