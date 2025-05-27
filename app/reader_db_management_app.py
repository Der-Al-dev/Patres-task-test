from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models import Reader
from schemas import ReaderCreate, ReaderUpdate, ReaderOut
from dependencies import get_db, get_current_user  # get_current_user — проверка JWT

router = APIRouter(
    prefix="/readers",
    tags=["readers"]
)

# Создание читателя (Create)
@router.post("", response_model=ReaderOut, status_code=201)
def add_reader(
    reader: ReaderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if db.query(Reader).filter(Reader.email == reader.email).first():
        raise HTTPException(status_code=409, detail="Reader with this email already exists")
    new_reader = Reader(name=reader.name, email=reader.email)
    db.add(new_reader)
    db.commit()
    db.refresh(new_reader)
    return new_reader

# Получение списка читателей (Read)
@router.get("", response_model=List[ReaderOut])
def get_readers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    readers = db.query(Reader).all()
    return readers

# Получение одного читателя (Read)
@router.get("/{reader_id}", response_model=ReaderOut)
def get_reader(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    reader = db.query(Reader).get(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader

# Обновление читателя (Update)
@router.put("/{reader_id}", response_model=ReaderOut)
def update_reader(
    reader_id: int,
    reader_update: ReaderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    reader = db.query(Reader).get(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    
    if reader_update.email:
        existing = db.query(Reader).filter(Reader.email == reader_update.email).first()
        if existing is not None and existing.id != reader_id:
            raise HTTPException(status_code=409, detail="Email already in use")
        reader.email = reader_update.email


    if reader_update.name:
        reader.name = reader_update.name

    db.commit()
    db.refresh(reader)
    return reader

# Удаление читателя (Delete)
@router.delete("/{reader_id}", status_code=204)
def delete_reader(
    reader_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    reader = db.query(Reader).get(reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail="Reader not found")
    db.delete(reader)
    db.commit()
    return None
