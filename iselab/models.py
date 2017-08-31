import datetime
import random

from passlib.hash import sha512_crypt
from peewee import Model, OperationalError, CharField, DateTimeField, BooleanField

from iselab.settings import db


def db_init():
    db.connect()
    try:
        db.create_tables([User, ])
        print('Creating tables...')
    except OperationalError:
        pass
    db.close()


class BaseModel(Model):
    class Meta:
        database = db


def tmppass() -> str:
    chars = "abcdefghijklmnopqrstuvwxyziABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890^?!?$%&/()=?`+#*~;:_,.-<>|"
    password = ""
    while not len(password) == 35:
        password += random.choice(chars)
    return password


class User(BaseModel):
    netid = CharField(unique=True)
    password = CharField(null=True)
    created_date = DateTimeField(default=datetime.datetime.now)
    last_login = DateTimeField(default=None, null=True)
    locked = BooleanField(default=False)

    def verify_password(self, password: str) -> bool:
        return sha512_crypt.verify(password, self.password)

    def set_password(self, password: str) -> None:
        self.password = sha512_crypt.hash(password)
