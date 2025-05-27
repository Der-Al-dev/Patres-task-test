from flask_jwt_extended import jwt_required
from flask import Blueprint, request, jsonify
from datetime import datetime
from classes import Reader, Book, BorrowedBook
from extensions import db

borrow_bp = Blueprint('borrow', __name__)

#  Эндпоинт выдачи книги читателю
@borrow_bp.route('/borrow', methods=['POST'])
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

    # Бизнес-логика 1: Проверка доступных экземпляров
    if book.copies <= 0:
        return jsonify({'msg': 'No available copies of this book'}), 400

    # Бизнес-логика 2: Проверка количества выданных книг у читателя (не более 3)
    active_borrows_count = BorrowedBook.query.filter_by(reader_id=reader_id, return_date=None).count()
    if active_borrows_count >= 3:
        return jsonify({'msg': 'Reader already has 3 borrowed books'}), 400

    # Создаём запись о выдаче
    borrowed = BorrowedBook(book_id=book_id, reader_id=reader_id)
    book.copies -= 1

    db.session.add(borrowed)
    db.session.commit()

    return jsonify({'msg': 'Book successfully borrowed', 'borrow_id': borrowed.id}), 201

# Эндпоинт возврата книги читателем
@borrow_bp.route('/return', methods=['POST'])
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

    book = Book.query.get(book_id)
    if not book:
        return jsonify({'msg': 'Book not found'}), 404  # Добавлена проверка

    borrowed.return_date = datetime.utcnow()
    book.copies += 1

    db.session.commit()

    return jsonify({'msg': 'Book successfully returned'}), 200
