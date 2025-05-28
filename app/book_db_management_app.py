from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import (  # get_current_user — зависимость для проверки JWT
    get_current_user,
    get_db,
)
from app.models import Book
from app.schemas import BookCreate, BookOut, BookUpdate

router = APIRouter(prefix="/books", tags=["books"])


# Создание книги (Create)
@router.post("", response_model=BookOut, status_code=200)
def add_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Проверка уникальности ISBN (если указан)
    if book.isbn:
        existing = db.query(Book).filter(Book.isbn == book.isbn).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Book with this ISBN already exists"
            )
    if book.copies is not None and book.copies < 0:
        raise HTTPException(status_code=400, detail="Copies must be >= 0")
    new_book = Book(
        title=book.title,
        author=book.author,
        year=book.year,
        isbn=book.isbn,
        copies=book.copies if book.copies is not None else 1,
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


# Получение списка книг (Read)
@router.get("", response_model=List[BookOut])
def get_books(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    books = db.query(Book).all()
    return books


# Получение одной книги (Read)
@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


# Обновление книги (Update)
@router.put("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book_data.copies is not None and book_data.copies < 0:
        raise HTTPException(status_code=400, detail="Copies must be >= 0")
    # Проверка уникальности ISBN при обновлении
    if book_data.isbn and book_data.isbn != book.isbn:
        existing = db.query(Book).filter(Book.isbn == book_data.isbn).first()
        if existing:
            raise HTTPException(
                status_code=400, detail="Book with this ISBN already exists"
            )
    for field, value in book_data.dict(exclude_unset=True).items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return book


# Удаление книги (Delete)
@router.delete("/{book_id}", status_code=204)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return None
