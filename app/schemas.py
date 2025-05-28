import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class BookBase(BaseModel):
    title: str = Field(..., description="Название книги")
    author: str = Field(..., description="Автор книги")
    year: Optional[int] = Field(None, description="Год публикации")
    isbn: Optional[str] = Field(None, description="ISBN книги")
    copies: Optional[int] = Field(
        1, ge=0, description="Количество экземпляров"
    )
    genre: Optional[str] = Field(None, description="Жанр")


class BookCreate(BookBase):
    title: str
    author: str


class BookUpdate(BookBase):
    pass


class BookOut(BookBase):
    id: int

    class Config:
        from_attributes = True


class ReaderBase(BaseModel):
    name: str = Field(..., description="Имя читателя")
    email: EmailStr = Field(..., description="Email читателя")


class ReaderCreate(ReaderBase):
    pass


class ReaderUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Имя читателя")
    email: Optional[EmailStr] = Field(None, description="Email читателя")


class ReaderOut(ReaderBase):
    id: int

    class Config:
        from_attributes = True


class BorrowRequest(BaseModel):
    book_id: int = Field(..., description="ID книги")
    reader_id: int = Field(..., description="ID читателя")


class ReturnRequest(BaseModel):
    book_id: int = Field(..., description="ID книги")
    reader_id: int = Field(..., description="ID читателя")


class BorrowedBookOut(BaseModel):
    id: int
    book_id: int
    reader_id: int
    borrow_date: Optional[datetime.datetime]
    return_date: Optional[datetime.datetime]

    class Config:
        from_attributes = True


class BorrowedBookWithTitleOut(BaseModel):
    id: int
    book_id: int
    reader_id: int
    borrow_date: Optional[datetime.datetime]
    return_date: Optional[datetime.datetime]
    title: str
    author: str

    class Config:
        from_attributes = True
