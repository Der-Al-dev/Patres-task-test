from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.config_app import ACCESS_TOKEN_EXPIRE_WEEKS, ALGORITHM, SECRET_KEY
from app.dependencies import get_current_user
from app.models import User
from app.schemas import Token, UserCreate
from app.database import get_db

router = APIRouter(prefix="/librarian", tags=["librarian"])

# def get_db():
#     from sqlalchemy import create_engine
#     from sqlalchemy.orm import sessionmaker

#     engine = create_engine("sqlite:///../data/library.db")
#     SessionLocal = sessionmaker(bind=engine)
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(weeks=ACCESS_TOKEN_EXPIRE_WEEKS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register", response_model=dict)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # <- Токен обязателен
):
    if get_user(db, user.email):
        raise HTTPException(
            status_code=400, detail="User with this email already exists"
        )
    hashed_password = bcrypt.hash(user.password)
    db_user = User(email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    return {"msg": "Librarian registered successfully"}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user(
        db, form_data.username
    )  # OAuth2PasswordRequestForm использует username вместо email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not bcrypt.verify(form_data.password, str(user.password_hash)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(weeks=ACCESS_TOKEN_EXPIRE_WEEKS)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


__all__ = ["router"]
