import os
from classes import Librarian
from librarian_db_management import start, create_first_librarian

def save_db_path(db_path, filename='db_path.txt'):
    with open(filename, 'w') as f:
        f.write(db_path)

def load_db_path(filename='db_path.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read().strip()
    return None

if __name__ == '__main__':
    db_path = start()
    if db_path:
        save_db_path(db_path)
        from app import create_app
        from extensions import db
        from classes import Librarian
        app = create_app(db_path)
        with app.app_context():
            db.create_all()
            email, password = create_first_librarian()
            librarian = Librarian(email=email)
            librarian.set_password(password)
            db.session.add(librarian)
            db.session.commit()
            print(f"Библиотекарь с {email} успешно зарегистрирован.")
        print(f"Инициализация завершена. Путь к базе сохранён в db_path.txt")
    else:
        print("Инициализация отменена.")
