from flask_jwt_extended import jwt_required
from flask import Blueprint, request, jsonify
from classes import Reader
from extensions import db

readers_bp = Blueprint('readers', __name__, url_prefix='/readers')

# Создание читателя (Create)
@readers_bp.route('/readers', methods=['POST'])
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
@readers_bp.route('/readers', methods=['GET'])
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
@readers_bp.route('/readers/<int:reader_id>', methods=['GET'])
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
@readers_bp.route('/readers/<int:reader_id>', methods=['PUT'])
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
@readers_bp.route('/readers/<int:reader_id>', methods=['DELETE'])
@jwt_required()
def delete_reader(reader_id):
    reader = Reader.query.get(reader_id)
    if not reader:
        return jsonify({'msg': 'Reader not found'}), 404

    db.session.delete(reader)
    db.session.commit()
    return jsonify({'msg': 'Reader deleted successfully'}), 200