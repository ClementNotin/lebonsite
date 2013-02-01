# coding=utf-8

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root@localhost/lebonscrap?use_unicode=1'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

lm=None
#lm = LoginManager()
#lm.setup_app(app)

import views
