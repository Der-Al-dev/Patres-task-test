import os

from passlib.hash import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.init_db_app import (  # замените your_module на имя вашего модуля
    add_first_librarian_if_needed,
    ensure_db_exists,
)
from app.models import User


def test_ensure_db_exists_creates_file_and_dir(tmp_path):
    data_dir = tmp_path / "data"
    db_path = data_dir / "library.db"

    # Убедимся, что ничего нет
    assert not data_dir.exists()
    assert not db_path.exists()

    # Вызов функции
    returned_path = ensure_db_exists()

    # Проверяем, что папка и файл созданы
    assert os.path.isdir(os.path.dirname(returned_path))
    assert os.path.isfile(returned_path)


def test_add_first_librarian_if_needed_creates_user(temp_db_path):
    # Создаём пустую SQLite базу с таблицей users
    engine = create_engine(f"sqlite:///{temp_db_path}")
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                is_librarian BOOLEAN DEFAULT 0
            )
        """
            )
        )
        conn.commit()

    # Запускаем функцию добавления библиотекаря
    add_first_librarian_if_needed(str(temp_db_path))

    # Проверяем, что пользователь добавлен
    Session = sessionmaker(bind=engine)
    session = Session()
    user = (
        session.query(User)
        .filter_by(email="first_librarian@library.com")
        .first()
    )
    session.close()

    assert user is not None
    assert bcrypt.verify("qwe123", user.password_hash)


def test_add_first_librarian_if_needed_skips_if_users_exist(temp_db_path):
    # Создаём базу и таблицу
    engine = create_engine(f"sqlite:///{temp_db_path}")
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR NOT NULL,
                is_librarian BOOLEAN DEFAULT 0
            )
        """
            )
        )
        conn.commit()

    # Добавляем пользователя вручную
    Session = sessionmaker(bind=engine)
    session = Session()
    user = User(
        email="existing@library.com", password_hash=bcrypt.hash("password")
    )
    session.add(user)
    session.commit()

    # Запускаем функцию — библиотекарь не должен добавиться
    add_first_librarian_if_needed(str(temp_db_path))

    # Проверяем, что в базе ровно один пользователь
    users = session.query(User).all()
    session.close()

    assert len(users) == 1
    assert users[0].email == "existing@library.com"


def test_add_first_librarian_if_needed_no_users_table(temp_db_path, capsys):
    # Создаём пустую базу без таблиц
    create_engine(f"sqlite:///{temp_db_path}")

    # Запускаем функцию — должна вывести предупреждение
    add_first_librarian_if_needed(str(temp_db_path))

    captured = capsys.readouterr()
    assert "Таблица users не найдена" in captured.out
