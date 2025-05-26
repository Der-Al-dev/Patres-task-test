import os
from datetime import timedelta

KEY = "SECURE_SECRET_KEY"

class Config:
    def __init__(self, db_path):
        self.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.JWT_SECRET_KEY = KEY
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(weeks=1)
