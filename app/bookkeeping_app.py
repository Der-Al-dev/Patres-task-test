from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, get_db  # JWT-аутентификация
from app.models import Book, BorrowedBook, Reader
from app.schemas import BorrowedBookOut, BorrowRequest, ReturnRequest, BorrowedBookWithTitleOut

router = APIRouter(prefix="/borrow", tags=["borrow"])

# Эндпоинт выдачи книги читателю
@router.post("", response_model=BorrowedBookOut, status_code=200)
def borrow_book(
    borrow_data: BorrowRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    book = db.query(Book).get(borrow_data.book_id)
    reader = db.query(Reader).get(borrow_data.reader_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    # Проверка доступных экземпляров
    if book.copies <= 0:
        raise HTTPException(
            status_code=400, detail="No available copies of this book"
        )

    # Проверка количества выданных книг у читателя (не более 3)
    active_borrows_count = (
        db.query(BorrowedBook)
        .filter(
            BorrowedBook.reader_id == borrow_data.reader_id,
            BorrowedBook.return_date.is_(None),
        )
        .count()
    )
    if active_borrows_count >= 3:
        raise HTTPException(
            status_code=400, detail="Reader already has 3 borrowed books"
        )

    # Создаём запись о выдаче
    borrowed = BorrowedBook(
        book_id=borrow_data.book_id, reader_id=borrow_data.reader_id
    )
    book.copies -= 1
    db.add(borrowed)
    db.commit()
    db.refresh(borrowed)
    return borrowed


# Эндпоинт возврата книги читателем
@router.post("/return", response_model=dict)
def return_book(
    return_data: ReturnRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    borrowed: Optional[BorrowedBook] = (
        db.query(BorrowedBook)
        .filter(
            BorrowedBook.book_id == return_data.book_id,
            BorrowedBook.reader_id == return_data.reader_id,
            BorrowedBook.return_date.is_(None),
        )
        .first()
    )
    if not borrowed:
        raise HTTPException(
            status_code=400,
            detail="No active borrow record found for this book and reader",
        )

    book = db.query(Book).get(return_data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    borrowed.return_date = datetime.utcnow()
    book.copies += 1
    db.commit()
    return {"msg": "Book successfully returned"}

# Эндпоинт для списка взятых читателем книг
@router.get("", response_model=List[BorrowedBookWithTitleOut])
def list_borrowed_books_with_title(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Получить список всех взятых книг с названиями."""
    borrowed_books = (
        db.query(BorrowedBook)
        .join(Book)
        .all()
    )
    return [
        {
            "id": borrowed.id,
            "book_id": borrowed.book_id,
            "reader_id": borrowed.reader_id,
            "borrow_date": borrowed.borrow_date,
            "return_date": borrowed.return_date,
            "title": borrowed.book.title,
            "author": borrowed.book.author
        }
        for borrowed in borrowed_books
    ]
