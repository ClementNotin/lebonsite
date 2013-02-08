# -*- coding: utf-8 -*-

import sys

sys.path.append("..")
from lebonsite import db
from entities import *
from datetime import datetime

print "Go"

users = User.query.all()
old_apparts = Appartement.query.filter(Appartement.date < datetime(2013, 02, 07, 21, 0)).order_by(Appartement.date)

for appart in old_apparts:
    for user in users:
        appart.seen_by(user)

db.session.commit()
print "End"
