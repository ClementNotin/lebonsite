# -*- coding: utf-8 -*-

from flask.ext.wtf import Form, StringField, BooleanField, PasswordField, TextAreaField, HiddenField
from flask.ext.wtf import Required


class LoginForm(Form):
    login = StringField('login', validators=[Required()])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('remember_me', default=False)


class AddCommentForm(Form):
    appart_id = HiddenField("appart_id", validators=[Required()])
    content = TextAreaField('content', validators=[Required()])
