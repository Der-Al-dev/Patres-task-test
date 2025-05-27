from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from models import Reader, Book, BorrowedBook
from schemas import BorrowRequest, ReturnRequest, BorrowedBookOut
from dependencies import get_db, get_current_user  # JWT-аутентификация

router = APIRouter(prefix="/borrow", tags=["borrow"])

# Эндпоинт выдачи книги читателю
@router.post("", response_model=BorrowedBookOut, status_code=201)
def borrow_book(
    borrow_data: BorrowRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    book = db.query(Book).get(borrow_data.book_id)
    reader = db.query(Reader).get(borrow_data.reader_id)

    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")

    # Проверка доступных экземпляров
    if book.copies <= 0:
        raise HTTPException(status_code=400, detail="No available copies of this book")

    # Проверка количества выданных книг у читателя (не более 3)
    active_borrows_count = (
        db.query(BorrowedBook)
        .filter(BorrowedBook.reader_id == borrow_data.reader_id, BorrowedBook.return_date == None)
        .count()
    )
    if active_borrows_count >= 3:
        raise HTTPException(status_code=400, detail="Reader already has 3 borrowed books")

    # Создаём запись о выдаче
    borrowed = BorrowedBook(book_id=borrow_data.book_id, reader_id=borrow_data.reader_id)
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
    current_user=Depends(get_current_user)
):
    borrowed: Optional[BorrowedBook] = (
        db.query(BorrowedBook)
        .filter(
            BorrowedBook.book_id == return_data.book_id,
            BorrowedBook.reader_id == return_data.reader_id,
            BorrowedBook.return_date == None
        )
        .first()
    )
    if not borrowed:
        raise HTTPException(status_code=400, detail="No active borrow record found for this book and reader")

    book = db.query(Book).get(return_data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    borrowed.return_date = datetime.utcnow()
    book.copies += 1
    db.commit()
    return {"msg": "Book successfully returned"}
