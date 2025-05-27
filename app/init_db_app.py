import os
from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import sessionmaker
from passlib.hash import bcrypt

# Импортируем модели (из models.py)
from models import User

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, "library.db")

def ensure_db_exists():
    """Создает папку data и файл БД, если их нет."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w'):
            pass
        print(f"Создан файл базы данных: {DB_PATH}")
    return DB_PATH

def add_first_librarian_if_needed(db_path):
    """Добавляет первого библиотекаря, если таблица users пуста."""
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    # Проверяем существование таблицы users
    insp = inspect(engine)
    if "users" not in insp.get_table_names():
        session.close()
        print("Таблица users не найдена. Примените миграции Alembic!")
        return

    # Проверяем, есть ли хотя бы один пользователь
    stmt = select(User).limit(1)
    user_exists = session.execute(stmt).scalar()
    if not user_exists:
        # Добавляем первого библиотекаря
        email = "first_librarian@library.com"
        password = "qwe123"
        password_hash = bcrypt.hash(password)
        librarian = User(email=email, password_hash=password_hash)
        session.add(librarian)
        session.commit()
        print(f"Добавлен первый библиотекарь: {email}")
    else:
        print("Пользователи уже существуют в базе.")
    session.close()

def main():
    """Основная функция инициализации."""
    db_path = ensure_db_exists()
    add_first_librarian_if_needed(db_path)
    print(f"База данных готова: {db_path}")

if __name__ == "__main__":
    main()