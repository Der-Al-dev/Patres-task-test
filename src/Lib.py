import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta

BASE_DATA = "library_catalog.db"
KEY = "SECURE_SECRET_KEY"

# Сначала создаём экземпляр приложения
app = Flask(__name__)

# Теперь вычисляем путь к базе данных
db_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', BASE_DATA)
)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Инициализируем расширения после настройки конфигурации
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Модель пользователя (библиотекаря)
class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

with app.app_context():
    db.create_all()

# Эндпоинт регистрации библиотекаря
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    if Librarian.query.filter_by(email=email).first():
        return jsonify({'msg': 'User with this email already exists'}), 409

    new_user = Librarian(email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'msg': 'User registered successfully'}), 201

# Эндпоинт входа (логина)
@app.route('/login', methods=['POST'])
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

# Пример защищённого эндпоинта, доступного только с JWT
@app.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    current_user_id = get_jwt_identity()
    # Здесь должна быть логика получения книг, например из базы данных
    # Для примера вернём заглушку
    return jsonify({'msg': f'Access granted for librarian id {current_user_id}', 'books': []}), 200

if __name__ == '__main__':
    app.run(debug=True)
    