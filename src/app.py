import os
from flask import Flask
from config import Config
from extensions import db, bcrypt, jwt
from init import register_routes

def read_db_path(filename='db_path.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read().strip()
    else:
        print("Файл с путём к базе данных не найден. Запустите сначала init_db.py")
        exit(1)

def create_app(db_path):
    app = Flask(__name__)
    app.config.from_object(Config(db_path))

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    register_routes(app)

    return app

if __name__ == '__main__':
    db_path = read_db_path()
    app = create_app(db_path)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
