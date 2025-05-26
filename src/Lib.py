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
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(weeks=1)

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

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    copies = db.Column(db.Integer, default=1, nullable=False)

    def __repr__(self):
        return f'<Book id={self.id}, title="{self.title}", author="{self.author}">'

class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<Reader id={self.id}, name="{self.name}", email="{self.email}">'


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

# Создание книги (Create)
@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    year = data.get('year')
    isbn = data.get('isbn')
    copies = data.get('copies', 1)

    if not title or not author:
        return jsonify({'msg': 'Title and author are required'}), 400
    if copies is not None and copies < 0:
        return jsonify({'msg': 'Copies must be >= 0'}), 400

    try:
        new_book = Book(
            title=title,
            author=author,
            year=year,
            isbn=isbn,
            copies=copies
        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'msg': 'Book added successfully', 'id': new_book.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 400


# Получение списка книг (Read)
@app.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    books = Book.query.all()
    books_list = []
    for book in books:
        books_list.append({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'year': book.year,
            'isbn': book.isbn,
            'copies': book.copies
        })
    return jsonify({'books': books_list}), 200

# Получение одной книги (Read)
@app.route('/books/<int:book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404
    return jsonify({
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'year': book.year,
        'isbn': book.isbn,
        'copies': book.copies
    }), 200

# Обновление книги (Update)
@app.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    data = request.get_json()
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404

    if 'copies' in data and data['copies'] < 0:
        return jsonify({'msg': 'Copies must be >= 0'}), 400

    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.year = data.get('year', book.year)
    book.isbn = data.get('isbn', book.isbn)
    book.copies = data.get('copies', book.copies)

    try:
        db.session.commit()
        return jsonify({'msg': 'Book updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 400
    
# Удаление книги (Delete)
@app.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404

    try:
        db.session.delete(book)
        db.session.commit()
        return jsonify({'msg': 'Book deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': str(e)}), 400

# Создание читателя (Create)
@app.route('/readers', methods=['POST'])
@jwt_required()
def add_reader():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({'msg': 'Name and email are required'}), 400

    if Reader.query.filter_by(email=email).first():
        return jsonify({'msg': 'Reader with this email already exists'}), 409

    new_reader = Reader(name=name, email=email)
    db.session.add(new_reader)
    db.session.commit()

    return jsonify({'msg': 'Reader added successfully', 'id': new_reader.id}), 201

# Получение списка читателей (Read)
@app.route('/readers', methods=['GET'])
@jwt_required()
def get_readers():
    readers = Reader.query.all()
    readers_list = []
    for reader in readers:
        readers_list.append({
            'id': reader.id,
            'name': reader.name,
            'email': reader.email
        })
    return jsonify({'readers': readers_list}), 200

# Получение одного читателя (Read)
@app.route('/readers/<int:reader_id>', methods=['GET'])
@jwt_required()
def get_reader(reader_id):
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404
    return jsonify({
        'id': reader.id,
        'name': reader.name,
        'email': reader.email
    }), 200

# Обновление читателя (Update)
@app.route('/readers/<int:reader_id>', methods=['PUT'])
@jwt_required()
def update_reader(reader_id):
    data = request.get_json()
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    name = data.get('name')
    email = data.get('email')

    if name:
        reader.name = name
    if email:
        # Проверяем уникальность email
        existing = Reader.query.filter_by(email=email).first()
        if existing and existing.id != reader_id:
            return jsonify({'msg': 'Email already in use'}), 409
        reader.email = email

    db.session.commit()
    return jsonify({'msg': 'Reader updated successfully'}), 200

# Удаление читателя (Delete)
@app.route('/readers/<int:reader_id>', methods=['DELETE'])
@jwt_required()
def delete_reader(reader_id):
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    db.session.delete(reader)
    db.session.commit()
    return jsonify({'msg': 'Reader deleted successfully'}), 200



if __name__ == '__main__':
    app.run(debug=True)
