from fastapi import HTTPException
from jose import jwt
import pytest

from app.config_app import ALGORITHM, SECRET_KEY
from app.dependencies import get_current_user
from app.models import User


def test_register(auth_client):
    response = auth_client.post(
        "/librarian/register",
        json={"email": "new_user@example.com", "password": "newpass"},
    )
    assert response.status_code == 200


def test_protected_route(auth_client):
    response = auth_client.get("/books")
    assert response.status_code == 200


def test_unauthenticated_access(client):
    response = client.get("/books")
    assert response.status_code == 401


# --- Тесты для get_current_user ---


def create_token(sub_value: str) -> str:
    return jwt.encode({"sub": sub_value}, SECRET_KEY, algorithm=ALGORITHM)


def test_get_current_user_success(db_session):
    user = User(
        email="test@example.com",
        password_hash="fakehashedpassword",
        is_librarian=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_token(str(user.id))
    result = get_current_user(db=db_session, token=token)
    assert result.id == user.id


def test_get_current_user_missing_sub(db_session):
    token = jwt.encode({}, SECRET_KEY, algorithm=ALGORITHM)  # Нет 'sub'
    user = User(
        email="test2@example.com",
        password_hash="fakehashedpassword",
        is_librarian=True,
    )
    db_session.add(user)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=db_session, token=token)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


def test_get_current_user_invalid_sub_value(db_session):
    user = User(
        email="test3@example.com",
        password_hash="fakehashedpassword",
        is_librarian=True,
    )
    db_session.add(user)
    db_session.commit()

    token = create_token("not_an_int")
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=db_session, token=token)
    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_token(db_session):
    user = User(
        email="test4@example.com",
        password_hash="fakehashedpassword",
        is_librarian=True,
    )
    db_session.add(user)
    db_session.commit()

    invalid_token = "this.is.not.a.valid.token"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=db_session, token=invalid_token)
    assert exc_info.value.status_code == 401


def test_get_current_user_not_found(db_session):
    token = create_token("999999")  # Предположим, такого пользователя нет
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(db=db_session, token=token)
    assert exc_info.value.status_code == 401
