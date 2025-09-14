from flask_sqlalchemy_lite import SQLAlchemy
from flask_alembic import Alembic
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Model(DeclarativeBase):
    pass

db = SQLAlchemy()
alembic = Alembic(metadatas=Model.metadata)
login_manager = LoginManager()