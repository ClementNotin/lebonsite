from flask import Flask, render_template, request
from database import session

import sys

sys.path.append("/home/clem/PycharmProjects/lebonscrap")
from Entities import Appartement, Photo

app = Flask(__name__)

@app.teardown_request
def shutdown_session(exception=None):
    session.remove()


@app.route('/')
def hello_world():
    return 'Blah blah World!'


@app.route("/apparts/")
def apparts():
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page=1

    apparts = session.query(Appartement).order_by("date").slice(0,34)
    return render_template('apparts.html', apparts=apparts)


@app.route("/appart/<appart_id>")
def appart(appart_id=None):
    if appart_id:
        appart = session.query(Appartement).filter_by(id=appart_id).first()
        return render_template('appart.html', appart=appart)
    else:
        return apparts()


if __name__ == '__main__':
    app.run(debug=True)

