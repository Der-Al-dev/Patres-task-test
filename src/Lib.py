from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import timedelta, datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library_catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'  # Замените на свой секретный ключ
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(weeks=1)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# --------------------
# Модели
# --------------------

class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<Librarian id={self.id}, email="{self.email}">'

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

class BorrowedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('reader.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)

    book = db.relationship('Book', backref=db.backref('borrowed_records', lazy=True))
    reader = db.relationship('Reader', backref=db.backref('borrowed_books', lazy=True))

    def __repr__(self):
        return f'<BorrowedBook id={self.id}, book_id={self.book_id}, reader_id={self.reader_id}, returned={self.return_date is not None}>'

# --------------------
# Создание таблиц
# --------------------

with app.app_context():
    db.create_all()

# --------------------
# Регистрация и логин библиотекаря
# --------------------

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'msg': 'Email and password are required'}), 400

    if Librarian.query.filter_by(email=email).first():
        return jsonify({'msg': 'User already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    librarian = Librarian(email=email, password=hashed_password)
    db.session.add(librarian)
    db.session.commit()

    return jsonify({'msg': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    librarian = Librarian.query.filter_by(email=email).first()
    if not librarian or not bcrypt.check_password_hash(librarian.password, password):
        return jsonify({'msg': 'Bad email or password'}), 401

    access_token = create_access_token(identity=librarian.id)
    return jsonify({'access_token': access_token}), 200

# --------------------
# CRUD для книг
# --------------------

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

    if isbn and Book.query.filter_by(isbn=isbn).first():
        return jsonify({'msg': 'Book with this ISBN already exists'}), 409

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

@app.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    data = request.get_json()
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404

    if 'copies' in data and data['copies'] < 0:
        return jsonify({'msg': 'Copies must be >= 0'}), 400

    if 'isbn' in data:
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing and existing.id != book_id:
            return jsonify({'msg': 'ISBN already in use'}), 409

    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.year = data.get('year', book.year)
    book.isbn = data.get('isbn', book.isbn)
    book.copies = data.get('copies', book.copies)

    db.session.commit()
    return jsonify({'msg': 'Book updated successfully'}), 200

@app.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404

    db.session.delete(book)
    db.session.commit()
    return jsonify({'msg': 'Book deleted successfully'}), 200

# --------------------
# CRUD для читателей
# --------------------

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

@app.route('/readers/<int:reader_id>', methods=['PUT'])
@jwt_required()
def update_reader(reader_id):
    data = request.get_json()
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    if 'email' in data:
        existing = Reader.query.filter_by(email=data['email']).first()
        if existing and existing.id != reader_id:
            return jsonify({'msg': 'Email already in use'}), 409

    reader.name = data.get('name', reader.name)
    reader.email = data.get('email', reader.email)

    db.session.commit()
    return jsonify({'msg': 'Reader updated successfully'}), 200

@app.route('/readers/<int:reader_id>', methods=['DELETE'])
@jwt_required()
def delete_reader(reader_id):
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    db.session.delete(reader)
    db.session.commit()
    return jsonify({'msg': 'Reader deleted successfully'}), 200

# --------------------
# Выдача и возврат книг
# --------------------

@app.route('/borrow', methods=['POST'])
@jwt_required()
def borrow_book():
    data = request.get_json()
    book_id = data.get('book_id')
    reader_id = data.get('reader_id')

    if not book_id or not reader_id:
        return jsonify({'msg': 'book_id and reader_id are required'}), 400

    book = Book.query.get(book_id)
    reader = Reader.query.get(reader_id)

    if not book:
        return jsonify({'msg': 'Book not found'}), 404
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    if book.copies <= 0:
        return jsonify({'msg': 'No available copies of this book'}), 400

    active_borrows_count = BorrowedBook.query.filter_by(reader_id=reader_id, return_date=None).count()
    if active_borrows_count >= 3:
        return jsonify({'msg': 'Reader already has 3 borrowed books'}), 400

    borrowed = BorrowedBook(book_id=book_id, reader_id=reader_id)
    book.copies -= 1

    db.session.add(borrowed)
    db.session.commit()

    return jsonify({'msg': 'Book successfully borrowed', 'borrow_id': borrowed.id}), 201

@app.route('/return', methods=['POST'])
@jwt_required()
def return_book():
    data = request.get_json()
    book_id = data.get('book_id')
    reader_id = data.get('reader_id')

    if not book_id or not reader_id:
        return jsonify({'msg': 'book_id and reader_id are required'}), 400

    borrowed = BorrowedBook.query.filter_by(
        book_id=book_id,
        reader_id=reader_id,
        return_date=None
    ).first()

    if not borrowed:
        return jsonify({'msg': 'No active borrow record found for this book and reader'}), 400

    borrowed.return_date = datetime.utcnow()
    book = Book.query.get(book_id)
    book.copies += 1

    db.session.commit()

    return jsonify({'msg': 'Book successfully returned'}), 200

# --------------------
# Запуск приложения
# --------------------

if __name__ == '__main__':
    app.run(debug=True)
