from app.models import Reader

def test_full_workflow(auth_client, db_session):
    # 1. Добавление книги (библиотекарь)
    response = auth_client.post("/books", json={
        "title": "New Book",
        "author": "Author",
        "year": 2023,
        "isbn": "111-222",
        "copies": 1
    })
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
        "/borrow",
        json={"book_id": book_id, "reader_id": reader_id}
    )
    assert response.status_code == 200

    # 4. Проверка списка взятых книг
    response = auth_client.get("/borrow")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "New Book"
