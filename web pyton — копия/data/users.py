import datetime as dt
import sqlalchemy as sa
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import sqlalchemy.orm as orm

class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    nickname = sa.Column(sa.String, unique=True, index=True)
    hashed_password = sa.Column(sa.String)
    email = sa.Column(sa.String, unique=True)
    about = sa.Column(sa.String)
    created_date = sa.Column(sa.DateTime, default=dt.datetime.now)
    mems = orm.relationship('Mem', back_populates='user')
    role = sa.Column(sa.String, default='edit')
    
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)