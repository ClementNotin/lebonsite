# -*- coding: utf-8 -*-

from flask import Flask, g, request, url_for, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, current_user
import re
from jinja2 import evalcontextfilter, Markup

app = Flask(__name__)
app.config.from_object('config')
app.config.from_object('secret')

db = SQLAlchemy(app)
from entities import *

db.create_all()

lm = LoginManager()
lm.init_app(app)

@lm.user_loader
def load_user(userid):
    return User.query.get(int(userid))


@app.before_request
def before_request():
    g.user = current_user


@app.before_request
def check_valid_login():
    if g.user is None or not g.user.is_authenticated():
        if request.endpoint  and 'static' not in request.endpoint and request.endpoint != "login":
            return redirect(url_for('login', next=request.path))

# This is a nl2br (newline to <BR>) filter. Inspired from http://flask.pocoo.org/snippets/28/
_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = re.sub(_paragraph_re, "<br/>", value)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

import views
# trick my IDE in believing that I need to import views, so it doesn't try to remove it, THANKS
views.app
