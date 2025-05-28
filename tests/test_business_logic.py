from app.models import Book, Reader

def test_borrow_limit(auth_client, db_session):
    # Создаём читателя
    reader = Reader(email="reader1@example.com", name="Test Reader")
    db_session.add(reader)
    db_session.commit()
    reader_id = reader.id

    # Создаем 3 тестовые книги
    for i in range(3):
        book = Book(
            title=f"Book {i}",
            author="Author",
            year=2020+i,
            isbn=f"000-{i}",
            copies=1
        )
        db_session.add(book)
        db_session.commit()
        
        # Берем книгу
        response = auth_client.post(
            "/borrow",
            json={"book_id": book.id, "reader_id": reader_id}
        )
        assert response.status_code in (200, 201)
    
    # Создаем 4-ю книгу
    book4 = Book(
        title="Book 4",
        author="Author",
        year=2023,
        isbn="000-4",
        copies=1
    )
    db_session.add(book4)
    db_session.commit()
    
    # Пытаемся взять 4-ю книгу
    response = auth_client.post(
        "/borrow",
        json={"book_id": book4.id, "reader_id": reader_id}
    )
    assert response.status_code == 400
    assert "Reader already has 3 borrowed books" in response.json()["detail"]

def test_borrow_unavailable(auth_client, db_session):
    # Создаём читателя
    reader = Reader(email="reader2@example.com", name="Test Reader")
    db_session.add(reader)
    db_session.commit()
    reader_id = reader.id
    # Создаем книгу без копий
    book = Book(
        title="Unavailable Book",
        author="Author",
        year=2023,
        isbn="999-0",
        copies=0
    )
    db_session.add(book)
    db_session.commit()
    
    # Пытаемся взять книгу
    response = auth_client.post(
        "/borrow",
        json={"book_id": book.id, "reader_id": reader_id}
    )
    assert response.status_code == (400)
    assert "No available copies of this book" in response.json()["detail"]
