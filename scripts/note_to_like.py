# -*- coding: utf-8 -*-

import sys

sys.path.append("..")
from lebonsite import db
from entities import *

print "Go"

db.session.execute("ALTER TABLE `lebonscrap`.`appartements_users` "
                   "CHANGE COLUMN `note` `like` SMALLINT(6) NULL DEFAULT NULL;")
db.session.execute("UPDATE `lebonscrap`.`appartements_users` SET `like`=0;")
db.session.commit()

print "End"
