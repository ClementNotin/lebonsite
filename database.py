from sqlalchemy import create_engine, func, desc, asc, or_
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import url_for

engine = create_engine('mysql+mysqldb://root@localhost/lebonscrap?use_unicode=1', convert_unicode=True, echo=True)
session = scoped_session(sessionmaker(autocommit=False,
    autoflush=False,
    bind=engine))

# import all modules here that might define models so that
# they will be registered properly on the metadata.  Otherwise
# you will have to import them first before calling init_db()
import sys

sys.path.append('../lebonscrap/')
from Entities import Appartement, Photo
#Base.metadata.create_all(bind=engine)


class DataTablesServer:
    def __init__(self, request, columns, collection):
        self.columns = columns
        self.collection = collection

        # values specified by the datatable for filtering, sorting, paging
        self.request_values = request.values

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
                              u'<img src="http://localhost:5001/photos/%s"/ style="max-height: 10em; width:auto;">'\
                              u'</a>' % (url_for("appart", appart_id=row.id), col[0].file)
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
        query = session.query(self.collection)

        query = self.sorting(query)

        # the term you entered into the datatable search
        query = self.filtering(query)

        query = self.paging(query)

        # get result from db
        self.result_data = query.all()

        self.cardinality_filtered = self.filtering(session.query(func.count(self.collection.id))).scalar()
        self.cardinality = session.query(func.count(self.collection.id)).scalar()


    def filtering(self, query):
        if (self.request_values.has_key('sSearch') ) and ( self.request_values['sSearch'] != ""):
            search_string = u"%%%s%%" % self.request_values['sSearch']

            query = query.filter(
                or_(Appartement.titre.like(search_string), Appartement.description.like(search_string)))

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
