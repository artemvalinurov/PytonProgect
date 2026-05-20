import datetime as dt
import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase

class Mem(SqlAlchemyBase):
    __tablename__ = 'mems'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    description = sa.Column(sa.String)
    image = sa.Column(sa.String)
    created = sa.Column(sa.DateTime, default=dt.datetime.now)
    creator = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    user = orm.relationship('User', back_populates='mems')