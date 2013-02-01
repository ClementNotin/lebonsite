# coding=utf-8

from flask.ext.wtf import Form, StringField, BooleanField, PasswordField
from flask.ext.wtf import Required

class LoginForm(Form):
    login = StringField('login', validators = [Required()])
    password = PasswordField('password', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)
