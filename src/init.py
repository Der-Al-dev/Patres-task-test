from book_db_management import books_bp
from reader_db_management import readers_bp
from bookkeeping import borrow_bp
from librarian_db_management import librarian_bp

def register_routes(app):
    app.register_blueprint(librarian_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(readers_bp)
    app.register_blueprint(borrow_bp)
