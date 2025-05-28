from datetime import datetime

from app.models import Book, BorrowedBook, Reader


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
            year=2020 + i,
            isbn=f"000-{i}",
            copies=1,
        )
        db_session.add(book)
        db_session.commit()

        # Берем книгу
        response = auth_client.post(
            "/borrow", json={"book_id": book.id, "reader_id": reader_id}
        )
        assert response.status_code in (200, 201)

    # Создаем 4-ю книгу
    book4 = Book(
        title="Book 4", author="Author", year=2023, isbn="000-4", copies=1
    )
    db_session.add(book4)
    db_session.commit()

    # Пытаемся взять 4-ю книгу
    response = auth_client.post(
        "/borrow", json={"book_id": book4.id, "reader_id": reader_id}
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
        copies=0,
    )
    db_session.add(book)
    db_session.commit()

    # Пытаемся взять книгу
    response = auth_client.post(
        "/borrow", json={"book_id": book.id, "reader_id": reader_id}
    )
    assert response.status_code == (400)
    assert "No available copies of this book" in response.json()["detail"]


def test_return_nonexistent_borrow(auth_client):
    # Пытаемся вернуть книгу, для которой нет активной записи займа
    response = auth_client.post(
        "/borrow/return",
        json={
            "book_id": 99999,
            "reader_id": 99999,
        },  # Несуществующие book_id и reader_id
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "No active borrow record found for this book and reader"
    )


def test_return_existing_borrow(auth_client, db_session):
    # Создаём читателя
    reader = Reader(email="reader3@example.com", name="Test Reader")
    db_session.add(reader)
    db_session.commit()
    reader_id = reader.id

    # Создаём книгу с копиями
    book = Book(
        title="Returnable Book",
        author="Author",
        year=2023,
        isbn="123-456",
        copies=1,
    )
    db_session.add(book)
    db_session.commit()
    book_id = book.id

    # Создаём активную запись займа (без return_date)
    borrowed = BorrowedBook(
        book_id=book_id,
        reader_id=reader_id,
        borrow_date=datetime.utcnow(),
        return_date=None,
    )
    book.copies -= 1
    db_session.add(borrowed)
    db_session.commit()

    # Отправляем запрос на возврат книги
    response = auth_client.post(
        "/borrow/return", json={"book_id": book_id, "reader_id": reader_id}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Book successfully returned"}

    # Проверяем, что количество копий увеличилось
    db_session.refresh(book)
    assert book.copies == 1

    # Проверяем, что у записи займа появилась дата возврата
    db_session.refresh(borrowed)
    assert borrowed.return_date is not None
