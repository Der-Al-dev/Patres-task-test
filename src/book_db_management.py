from flask_jwt_extended import jwt_required
from flask import Blueprint, request, jsonify
from classes import Book
from extensions import db

books_bp = Blueprint('books', __name__, url_prefix='/books')

# Создание книги (Create)
@books_bp.route('', methods=['POST'])
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
@books_bp.route('', methods=['GET'])
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
@books_bp.route('/<int:book_id>', methods=['GET'])
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
@books_bp.route('/<int:book_id>', methods=['PUT'])
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
@books_bp.route('/<int:book_id>', methods=['DELETE'])
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