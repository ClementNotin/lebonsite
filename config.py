# coding=utf-8
import secret


# database
SQLALCHEMY_DATABASE_URI = u'mysql+mysqldb://%s@localhost/lebonscrap?charset=utf8' % secret.DB_AUTH
SQLALCHEMY_ECHO = True

# WTF forms
CSRF_ENABLED = True

BASE_PHOTOS_URL = u"http://localhost:5001/photos/"
