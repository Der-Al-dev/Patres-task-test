from fastapi import FastAPI

from app.book_db_management_app import router as book_router
from app.librarian_db_management_app import router as librarian_router
from app.reader_db_management_app import router as reader_router
from app.bookkeeping_app import router as borrow_router

app = FastAPI()

app.include_router(librarian_router)
app.include_router(book_router)
app.include_router(reader_router)
app.include_router(borrow_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
