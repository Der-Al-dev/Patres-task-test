from extensions import db, bcrypt
from datetime import datetime

class Librarian(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, email):
        self.email = email

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

# Класс книга
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    copies = db.Column(db.Integer, default=1, nullable=False)
    
    def __init__(self, title, author, year=None, isbn=None, copies=1):
        self.title = title
        self.author = author
        self.year = year
        self.isbn = isbn
        self.copies = copies

    def __repr__(self):
        return f'<Book id={self.id}, title="{self.title}", author="{self.author}">'
    

# Класс читатель
class Reader(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<Reader id={self.id}, name="{self.name}", email="{self.email}">'

# Класс выданные книги
class BorrowedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    reader_id = db.Column(db.Integer, db.ForeignKey('reader.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    book = db.relationship('Book', backref=db.backref('borrowed_records', lazy=True))
    reader = db.relationship('Reader', backref=db.backref('borrowed_books', lazy=True))

    def __init__(self, book_id, reader_id, borrow_date=None, return_date=None):
        self.book_id = book_id
        self.reader_id = reader_id
        self.borrow_date = borrow_date if borrow_date else datetime.utcnow()
        self.return_date = return_date