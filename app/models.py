import datetime
from sqlalchemy import Integer, CheckConstraint, ForeignKey, func
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
)
from sqlalchemy.types import String

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(nullable=False)
    is_librarian: Mapped[bool] = mapped_column(default=True)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(nullable=False)
    author: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=True)
    isbn: Mapped[str] = mapped_column(unique=True, nullable=True)
    copies: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("copies >= 0", name="check_copies_positive"),
    )


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)


class BorrowedBook(Base):
    __tablename__ = "borrowed_books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id"), nullable=False
    )
    reader_id: Mapped[int] = mapped_column(
        ForeignKey("readers.id"), nullable=False
    )
    borrow_date: Mapped[datetime.datetime | None] = mapped_column(
        default=func.now(), nullable=False
    )
    return_date: Mapped[datetime.datetime | None] = mapped_column(
        nullable=True
    )

    book: Mapped["Book"] = relationship("Book")
    reader: Mapped["Reader"] = relationship("Reader")
