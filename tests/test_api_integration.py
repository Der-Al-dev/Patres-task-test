from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import Reader


def test_full_workflow(auth_client, db_session):
    # 1. Добавление книги (библиотекарь)
    response = auth_client.post(
        "/books",
        json={
            "title": "New Book",
            "author": "Author",
            "year": 2023,
            "isbn": "111-222",
            "copies": 1,
        },
    )
    print("Добавление книги:", response.json())
    assert response.status_code == 200
    book_id = response.json()["id"]

    # 2. Создаём читателя (если нет автоматической авторизации читателя)
    reader = Reader(email="reader@example.com", name="Test Reader")
    db_session.add(reader)
    db_session.commit()
    reader_id = reader.id

    # 3. Взятие книги (читатель)
    response = auth_client.post(
        "/borrow", json={"book_id": book_id, "reader_id": reader_id}
    )
    assert response.status_code == 200

    # 4. Проверка списка взятых книг
    response = auth_client.get("/borrow")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "New Book"

    # 5. Получение списка всех книг
    response = auth_client.get("/books")
    assert response.status_code == 200
    books = response.json()
    assert any(book["id"] == book_id for book in books)

    # 6. Получение одной книги по ID
    response = auth_client.get(f"/books/{book_id}")
    assert response.status_code == 200
    book = response.json()
    assert book["id"] == book_id
    assert book["title"] == "New Book"

    # 7. Обновление книги
    update_data = {
        "title": "Updated Book Title",
        "author": "Updated Author",
        "year": 2024,
        "copies": 5,
    }
    response = auth_client.put(f"/books/{book_id}", json=update_data)
    assert response.status_code == 200
    updated_book = response.json()
    assert updated_book["title"] == update_data["title"]
    assert updated_book["author"] == update_data["author"]
    assert updated_book["year"] == update_data["year"]
    assert updated_book["copies"] == update_data["copies"]

    # 8. Удаление книги
    response = auth_client.delete(f"/books/{book_id}")
    assert response.status_code == 204

    # 9. Проверка, что книга удалена (должен быть 404)
    response = auth_client.get(f"/books/{book_id}")
    assert response.status_code == 404


def test_get_db_coverage():
    gen = get_db()
    db = next(gen)  # Создаём сессию
    assert db is not None
    try:
        pass  # Можно выполнить дополнительные проверки с db
    finally:
        try:
            next(gen)  # Завершаем генератор, чтобы вызвать db.close()
        except StopIteration:
            pass


def test_unauthorized_access():
    # Создаём клиент без авторизации
    client = TestClient(app)

    # Пытаемся получить список книг без авторизации
    response = client.get("/books")
    assert (
        response.status_code == 401
    )  # Unauthorized или 403 Forbidden, зависит от настройки

    # Пытаемся добавить книгу без авторизации
    response = client.post(
        "/books",
        json={
            "title": "Unauthorized Book",
            "author": "No Author",
            "year": 2025,
            "isbn": "000-000",
            "copies": 1,
        },
    )
    assert response.status_code == 401  # Unauthorize


def test_create_reader_success(auth_client, db_session):
    # Успешное создание читателя
    response = auth_client.post(
        "/readers", json={"name": "John Doe", "email": "john@example.com"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"

    # Проверяем запись в базе
    reader = (
        db_session.query(Reader)
        .filter(Reader.email == "john@example.com")
        .first()
    )
    assert reader is not None
    assert reader.name == "John Doe"


def test_create_reader_duplicate_email(auth_client, db_session):
    # Создаем первого читателя
    auth_client.post(
        "/readers", json={"name": "Alice Smith", "email": "alice@example.com"}
    )

    # Пытаемся создать второго с тем же email
    response = auth_client.post(
        "/readers", json={"name": "Alice Brown", "email": "alice@example.com"}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

    # Проверяем что в базе только одна запись
    readers = (
        db_session.query(Reader)
        .filter(Reader.email == "alice@example.com")
        .all()
    )
    assert len(readers) == 1
    assert readers[0].name == "Alice Smith"


def test_update_reader_success(auth_client, db_session):
    # Создаём читателя для обновления
    reader = Reader(name="Original Name", email="original@example.com")
    db_session.add(reader)
    db_session.commit()
    db_session.refresh(reader)

    update_data = {"name": "Updated Name", "email": "updated@example.com"}

    response = auth_client.put(f"/readers/{reader.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["email"] == update_data["email"]

    # Проверяем, что данные обновились в базе
    db_session.refresh(reader)
    assert reader.name == update_data["name"]
    assert reader.email == update_data["email"]


def test_update_reader_not_found(auth_client):
    # Пытаемся обновить несуществующего читателя
    response = auth_client.put("/readers/999999", json={"name": "Name"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Reader not found"


def test_update_reader_email_conflict(auth_client, db_session):
    # Создаём двух читателей
    reader1 = Reader(name="Reader One", email="one@example.com")
    reader2 = Reader(name="Reader Two", email="two@example.com")
    db_session.add_all([reader1, reader2])
    db_session.commit()
    db_session.refresh(reader1)
    db_session.refresh(reader2)

    # Пытаемся обновить email второго читателя на email первого
    response = auth_client.put(
        f"/readers/{reader2.id}", json={"email": "one@example.com"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already in use"
