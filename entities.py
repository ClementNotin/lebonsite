# coding=utf-8

from lebonsite import db, app
from hashlib import sha1

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    pwdhash = db.Column(db.String(40), unique=True)

    def __init__(self, username, pwdhash):
        self.username = username
        self.pwdhash = pwdhash

    def check_password(self, password):
        return sha1(app.config["PWD_SALT"] + password).hexdigest() == self.pwdhash

    # required by flask-login
    def is_authenticated(self):
        return True

    # required by flask-login
    def is_active(self):
        return True

    # required by flask-login
    def is_anonymous(self):
        return False

    # required by flask-login
    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % self.username

