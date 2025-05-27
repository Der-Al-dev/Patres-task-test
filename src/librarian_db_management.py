from classes import Librarian
from extensions import db
import os
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required


librarian_bp = Blueprint('login', __name__)

def start():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    os.makedirs(data_dir, exist_ok=True)

    choice = input("Подключиться к существующей библиотеке (0) или создать новую (1)?").strip()
    while choice not in ('0', '1'):
        choice = input("Пожалуйста, введите 0 (существующая) или 1 (новая): ").strip()

    if choice == '0':
        db_name = input("Введите название библиотеки: ").strip()
        db_path = os.path.join(data_dir, f"{db_name}.db")

        if os.path.isfile(db_path):
            print("Для управления библиотекой, пожалуйста, авторизуйтесь")
        else:
            print(f"Библиотека {db_name} не найдена")

    else:  # choice == '1'
        db_name = input("Введите название новой библиотеки: ").strip()
        db_path = os.path.join(data_dir, f"{db_name}.db")

        if os.path.exists(db_path):
            print(f"Файл {db_name}.db уже существует.")
        else:
            with open(db_path, 'w') as f:
                pass
            print(f"Создана библиотека: {db_path} для управления создайте логин и пароль")
    return db_path

def create_first_librarian():
    # Запрос логина и пароля
    while True:
        email = input("Введите логин (e-mail): ").strip()
        if not is_valid_email(email):
            print("Некорректный e-mail. Попробуйте ещё раз.")
            continue
        else:
            break
    password = input("Введите пароль: ").strip()
    print(f"Библиотекарь с {email} успешно зарегистрирован.")
    return email, password


def is_valid_email(email):
    # Простое регулярное выражение для проверки e-mail
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None
    
# Эндпоинт входа (логина)
@librarian_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    user = Librarian.query.filter_by(email=email).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'msg': 'Invalid email or password'}), 401
    
# Эндпоинт регистрации библиотекаря
@librarian_bp.route('/register', methods=['POST'])
@jwt_required()
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    if not is_valid_email(email):
        return jsonify({'msg': 'Invalid email format'}), 400

    existing_user = Librarian.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'msg': 'User with this email already exists'}), 409

    new_librarian = Librarian(email=email)
    new_librarian.set_password(password)

    try:
        db.session.add(new_librarian)
        db.session.commit()
        return jsonify({'msg': 'Librarian registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Error: {str(e)}'}), 500