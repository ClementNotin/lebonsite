# -*- coding: utf-8 -*-

from flask import  render_template, request, url_for, g, redirect, session
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm.exc import NoResultFound
from forms import *
import json
from lebonsite import app, db
import config
from entities import *
from flask.ext.login import login_user, logout_user

@app.route('/')
def index():
    return render_template('index.html')


@app.route("/api/apparts/")
def api_apparts():
    datatable = DataTablesServer(request,
        ["titre", "photos", "loyer", "ville", "cp", "pieces", "meuble", "surface", "date"], Appartement)
    results = datatable.output_result()
    return json.dumps(results)


@app.route("/api/rate/<appart_id>", methods=["POST"])
def api_rate(appart_id=None):
    if appart_id and "note" in request.values:
        visit = AppartementUser.query.filter_by(user=g.user, appartement_id=appart_id).first()
        visit.note = int(request.values["note"])
        db.session.commit()

    return "ok"


@app.route("/apparts/")
def apparts():
    return render_template('apparts.html')


@app.route("/appart/<appart_id>")
def appart(appart_id=None):
    if appart_id:
        # add comment form
        form = AddCommentForm()
        form.appart_id.data = appart_id

        # get the appart
        appart = db.session.query(Appartement).filter_by(id=appart_id).first()

        # has the user already seen this appart? if not: add tracking
        last_visit = AppartementUser.query.filter_by(appartement=appart, user=g.user).first()
        if not last_visit:
            last_visit = AppartementUser(g.user, appart)
            last_visit.date_seen = datetime.now()
            db.session.add(last_visit)
            db.session.commit()

        # MAJ le fait que l'utilisateur a vu les commentaires
        for comment in appart.comments:
            comment.seen_by(g.user)

        #arrondissement depuis code postal
        ardt=None
        cp_str = str(appart.cp)
        if cp_str.startswith("75"):
            ardt=cp_str[-2:]

        return render_template('appart.html', BASE_PHOTOS_URL=config.BASE_PHOTOS_URL, appart=appart, arrondissement=ardt, form=form)
    else:
        return apparts()


@app.route("/comments/add", methods=["POST"])
def comments_add():
    form = AddCommentForm()
    if form.validate_on_submit():
        appart = db.session.query(Appartement).filter_by(id=form.appart_id.data).first()
        if appart:
            comment = Comment(form.content.data)
            comment.user = g.user
            comment.appartement = appart
            db.session.add(comment)
            db.session.commit()
    return redirect(request.referrer)


@app.route("/notifications")
def notifications():
    comments = Comment.query.outerjoin(CommentUser, Comment.id == CommentUser.comment_id).filter(
        CommentUser.user == None).order_by(desc(Comment.date)) # "== None" n'est pas une erreur, c'est sqlalchemy qui le veut comme ça

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
                        col = u'<a href="%s">'\
                              u'<img src="%s/%s"/ style="max-height: 10em; width:auto;">'\
                              u'</a>' % (url_for("appart", appart_id=row.id), config.BASE_PHOTOS_URL, col[0].file)
                    else:
                        col = ""
                elif col_name == "titre":
                    col = u'<a href="%s">%s</a>' % (url_for("appart", appart_id=row.id), col)
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
            query = query.outerjoin(AppartementUser, Appartement.id == AppartementUser.appartement_id).filter(
                AppartementUser.user == None) # "== None" n'est pas une erreur, c'est sqlalchemy qui le veut comme ça

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

