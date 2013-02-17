# -*- coding: utf-8 -*-

import json
import re
from flask import render_template, request, url_for, g, redirect, session

from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm.exc import NoResultFound
from flask.ext.login import login_user, logout_user

from forms import *

from lebonsite import app, db
import config
from entities import *

user_re = re.compile("user(\d)")


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/api/apparts/")
def api_apparts():
    datatable = DataTablesServer(request,
                                 ["titre", "photos", "loyer", "ville", "cp", "pieces", "meuble", "surface", "date"],
                                 Appartement)
    results = datatable.output_result()
    return json.dumps(results)


@app.route("/api/rate/<int:appart_id>", methods=["POST"])
def api_rate(appart_id=None):
    if appart_id and "note" in request.values:
        visit = AppartementUser.query.get_or_404((appart_id, g.user.id))
        visit.note = int(request.values["note"])
        db.session.commit()

    return "ok"


@app.route("/apparts/")
def apparts():
    return render_template('apparts.html')


@app.route("/appart/<int:appart_id>")
def appart(appart_id=None):
    if appart_id:
        # get the appart
        appart = Appartement.query.get_or_404(appart_id)

        # add comment form
        form = AddCommentForm()
        form.appart_id.data = appart_id

        # has the user already seen this appart? if not: add tracking
        appart.seen_by(g.user)

        # MAJ le fait que l'utilisateur a vu les commentaires
        for comment in appart.comments:
            comment.seen_by(g.user)

        #arrondissement depuis code postal
        ardt = None
        cp_str = str(appart.cp)
        if cp_str.startswith("75"):
            ardt = cp_str[-2:]

        return render_template('appart.html', BASE_PHOTOS_URL=config.BASE_PHOTOS_URL, appart=appart,
                               arrondissement=ardt, form=form)
    else:
        return apparts()


@app.route("/comments/add", methods=["POST"])
def comments_add():
    form = AddCommentForm()
    if form.validate_on_submit():
        appart = Appartement.query.get_or_404(form.appart_id.data)
        if appart:
            comment = Comment(form.content.data)
            comment.user = g.user
            comment.appartement = appart
            db.session.add(comment)
            db.session.commit()

    #fait scroller en bas de page pour voir si ya pas eu des nouveaux commentaires pendant l'écriture de celui-ci
    return redirect(request.referrer + "#commentForm")


@app.route("/comments")
def comments():
    users = User.query.all()

    shown = []
    for arg in request.args:
        id = re.search(user_re, arg).group(1)
        shown.append(int(id))
    empty_shown = (len(shown) == 0)

    if empty_shown:
        comments = Comment.query.order_by(desc(Comment.date))
    else:
        comments = Comment.query.filter(Comment.user_id.in_(shown)).order_by(desc(Comment.date))
    return render_template("comments.html", shown=shown, users=users, comments=comments,empty_shown=empty_shown)


@app.route("/notifications")
def notifications():
    comments = Comment.query.filter(
        ~Comment.id.in_(db.session.query(CommentUser.comment_id).filter_by(user=g.user))).order_by(desc(Comment.date))
    return render_template("notifications.html", comments=comments)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        try:
            user = User.query.filter(User.username == form.login.data).one()
        except NoResultFound:
            print "bad login"

        if user and user.check_password(form.password.data):
            session['remember_me'] = form.remember_me.data
            login_user(user)
            if "next" in request.values and request.values["next"] != "/":
                return redirect(request.values["next"])
            else:
                return redirect(url_for("apparts"))

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if g.user is not None and g.user.is_authenticated():
        logout_user()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))


class DataTablesServer:
    def __init__(self, request, columns, collection):
        self.columns = columns
        self.collection = collection

        # values specified by the datatable for filtering, sorting, paging
        self.request_values = request.values

        self.only_news = False
        if "only_news" in self.request_values:
            self.only_news = self.request_values["only_news"].lower() == "true"

        # results from the db
        self.result_data = None

        # total in the table after filtering
        self.cardinality_filtered = 0

        # total in the table unfiltered
        self.cadinality = 0

        self.run_queries()

    def output_result(self):
        output = {'sEcho': str(int(self.request_values['sEcho'])),
                  'iTotalRecords': str(self.cardinality),
                  'iTotalDisplayRecords': str(self.cardinality_filtered)}
        aaData_rows = []

        for row in self.result_data:
            aaData_row = []
            for col_name in self.columns:
                #aaData_row.append(row[self.columns[i]].replace('"', '\\"'))
                col = getattr(row, col_name, "Column not found")

                if col_name == "photos":
                    if len(col) > 0:
                        col = u'<a href="%s">' \
                              u'<img src="%s/%s"/ style="max-height: 10em; width:auto;">' \
                              u'</a>' % (url_for("appart", appart_id=row.id), config.BASE_PHOTOS_URL, col[0].file)
                    else:
                        col = ""
                elif col_name == "titre":
                    col = u'<a href="%s">%s</a>' % (url_for("appart", appart_id=row.id), col)
                elif col_name == "meuble":
                    if row.meuble is None:
                        col = "N/A"
                    elif row.meuble:
                        col = "Oui"
                    else:
                        col = "Non"
                else:
                    col = unicode(col).replace('"', '\\"')

                aaData_row.append(col)

            aaData_rows.append(aaData_row)

        output['aaData'] = aaData_rows

        return output


    def run_queries(self):
        query = db.session.query(self.collection)

        query = self.sorting(query)

        # the term you entered into the datatable search, and only new apparts (or not)
        query = self.filtering(query)

        query = self.paging(query)

        # get result from db
        self.result_data = query.all()

        self.cardinality_filtered = self.filtering(db.session.query(func.count(self.collection.id))).scalar()
        self.cardinality = db.session.query(func.count(self.collection.id)).scalar()


    def filtering(self, query):
        if (self.request_values.has_key('sSearch') ) and ( self.request_values['sSearch'] != ""):
            search_string = u"%%%s%%" % self.request_values['sSearch']

            query = query.filter(
                or_(Appartement.titre.like(search_string), Appartement.description.like(search_string)))

        #show only news ?
        if self.only_news:
            query = query.filter(
                ~Appartement.id.in_(db.session.query(AppartementUser.appartement_id).filter_by(user=g.user)))

        return query


    def sorting(self, query):
        if ( self.request_values['iSortCol_0'] != "" ) and ( self.request_values['iSortingCols'] > 0 ):
            for i in range(int(self.request_values['iSortingCols'])):
                if self.request_values['sSortDir_' + str(i)] == "asc":
                    direction = asc
                else:
                    direction = desc

                query = query.order_by(direction(self.columns[int(self.request_values['iSortCol_' + str(i)])]))
        return query


    def paging(self, query):
        if (self.request_values['iDisplayStart'] != "" ) and (self.request_values['iDisplayLength'] != -1 ):
            start = int(self.request_values['iDisplayStart'])
            length = int(self.request_values['iDisplayLength'])

            query = query.slice(start, start + length)
        return query

