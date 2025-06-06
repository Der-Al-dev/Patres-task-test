from fastapi.testclient import TestClient
from passlib.hash import bcrypt
import pytest

# Фикстура для создания тестовой БД в памяти и добавления первого пользователя
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, User


@pytest.fixture(scope="module")
def db_engine():
    print("\n=== Запуск фикстуры db_engine ===")
    engine = create_engine("sqlite:///test.db")
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        print("Ошибка при создании таблиц:", repr(e))
        raise
    print("Таблицы созданы:", Base.metadata.tables.keys())
    inspector = inspect(engine)
    print("Таблицы в БД:", inspector.get_table_names())

    # Добавляем первого пользователя
    Session = sessionmaker(bind=engine)
    session = Session()
    password_hash = bcrypt.hash("qwe123")
    session.add(
        User(email="first_librarian@library.com", password_hash=password_hash)
    )
    session.commit()
    session.close()

    yield engine

    print("\n=== Завершение фикстуры db_engine ===")
    Base.metadata.drop_all(engine)


# Фикстура для тестовой сессии БД
@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


# Фикстура для тестового клиента FastAPI с переопределением get_db
@pytest.fixture
def client(db_engine):
    def override_get_db():
        try:
            Session = sessionmaker(bind=db_engine)
            session = Session()
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


# Фикстура для авторизованного клиента
@pytest.fixture
def auth_client(client):
    response = client.post(
        "/librarian/login",
        data={
            "username": "first_librarian@library.com",
            "password": "qwe123",
        },
    )
    assert response.status_code == 200, f"Failed to get token: {response.text}"
    token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


# Фикстуры для init_db
@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_db_path(temp_data_dir):
    return temp_data_dir / "library.db"
