from flask import Flask
from config import Config
from extensions import db, bcrypt, jwt
from init import register_routes
from librarian_db_management import start

def create_app(db_path):
    app = Flask(__name__)
    app.config.from_object(Config(db_path))

    # Инициализация расширений
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Регистрируем маршруты (blueprints)
    register_routes(app)

    # Создаем таблицы, если их нет
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    db_path = start()
    if db_path:
        app = create_app(db_path)
        app.run(debug=True)
    else:
        print("Запуск приложения отменён из-за отсутствия базы данных.")
