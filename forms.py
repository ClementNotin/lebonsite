# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, HiddenField
from wtforms.validators import DataRequired as Required


class LoginForm(Form):
    login = StringField('login', validators=[Required()])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('remember_me', default=True)


class AddCommentForm(Form):
    appart_id = HiddenField("appart_id", validators=[Required()])
    content = TextAreaField('content', validators=[Required()])


class SentEmailForm(Form):
    sent_email = BooleanField('sent_email', default=False)
