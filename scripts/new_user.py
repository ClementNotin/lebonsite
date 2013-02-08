# -*- coding: utf-8 -*-

import sys

sys.path.append("..")
from lebonsite import db
from entities import *
from passgen import hash

print "Go"

name = raw_input("Name? ")
pwd = raw_input("Pass? ")
user = User(name, hash(pwd))
db.session.add(user)
db.session.commit()

old_apparts = Appartement.query.all()
for appart in old_apparts:
    appart.seen_by(user)

old_comments = Comment.query.all()
for comment in old_comments:
    comment.seen_by(user)

db.session.commit()
print "End"
