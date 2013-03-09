# -*- coding: utf-8 -*-

from datetime import datetime
from hashlib import sha1

from lebonsite import db, app


class Appartement(db.Model):
    __tablename__ = 'appartements'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200))
    loyer = db.Column(db.Integer)
    ville = db.Column(db.String(50))
    cp = db.Column(db.Integer)
    pieces = db.Column(db.Integer)
    meuble = db.Column(db.Boolean)
    surface = db.Column(db.Integer)
    description = db.Column(db.String(5000))
    photos = db.relationship("Photo", order_by="Photo.id", backref="appartement")
    comments = db.relationship("Comment", order_by="Comment.id", backref="appartement")
    views = db.relationship("AppartementUser", order_by="AppartementUser.date_seen", backref="appartement")
    date = db.Column(db.DateTime)
    auteur = db.Column(db.String(100))
    source = db.Column(db.Enum("leboncoin", "foncia", "seloger"))
    url = db.Column(db.String(200))

    def __init__(self, id, titre, loyer, ville, cp, pieces, meuble, surface, description, photos, date, auteur, source,
                 url):
        self.id = id
        self.titre = unicode(titre)
        self.loyer = loyer
        self.ville = unicode(ville)
        self.cp = cp
        self.pieces = pieces
        self.meuble = meuble
        self.surface = surface
        self.description = unicode(description)
        self.date = date
        self.auteur = unicode(auteur)
        self.source = source
        self.url = url

        for photo in photos:
            self.photos.append(Photo(photo))

    def seen_by(self, user):
        #may already be seen! si on insert quand même on aura un primary key duplication error
        if not AppartementUser.query.get((self.id, user.id)):
            last_visit = AppartementUser(user, self)
            last_visit.date_seen = datetime.now()
            db.session.add(last_visit)
            db.session.commit()

    def __repr__(self):
        return u"<Appartement %d %r>" % (self.id, self.titre)


class Photo(db.Model):
    __tablename__ = 'photos'

    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.String(40), nullable=False)
    appartement_id = db.Column(db.Integer, db.ForeignKey('appartements.id'))

    def __init__(self, file):
        self.file = file.split('/')[-1]


    def __repr__(self):
        return "<Photo('%s')>" % self.file


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    pwdhash = db.Column(db.String(40), unique=True)
    comments = db.relationship("Comment", order_by="Comment.id", backref="user")
    views = db.relationship("AppartementUser", order_by="AppartementUser.date_seen", backref="user")
    views_comments = db.relationship("CommentUser", backref="user")

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


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    content = db.Column(db.String(5000))
    appartement_id = db.Column(db.Integer, db.ForeignKey("appartements.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    views = db.relationship("CommentUser", backref="comment")

    def __init__(self, content):
        self.content = content
        self.date = datetime.now()

    def seen_by(self, user):
        #return True if it was already seen, False otherwise

        #may already be seen! si on insert quand même on aura un primary key duplication error
        if not CommentUser.query.get((self.id, user.id)):
            db.session.add(CommentUser(self, user))
            db.session.commit()
            return False
        return True

    def __repr__(self):
        return '<Comment %r>' % self.content


class AppartementUser(db.Model):
    __tablename__ = 'appartements_users'

    appartement_id = db.Column(db.Integer, db.ForeignKey("appartements.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    date_seen = db.Column(db.DateTime)
    like = db.Column(db.SmallInteger, default=0)

    def __init__(self, user, appartement):
        self.user = user
        self.appartement = appartement

    def __repr__(self):
        return '<AppartementUser %r,%r,%r,%r>' % (self.user, self.appartement, self.date_seen, self.like)


class CommentUser(db.Model):
    __tablename__ = 'comments_users'

    comment_id = db.Column(db.Integer, db.ForeignKey("comments.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    def __init__(self, comment, user):
        self.comment = comment
        self.user = user

    def __repr__(self):
        return '<CommentUser %r,%r>' % (self.comment, self.user)
