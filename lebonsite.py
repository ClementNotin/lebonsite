from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Blah blah World!'

@app.route("/apparts/")
@app.route("/apparts/<appart_id>")
def apparts(appart_id=None):
    if appart_id:
        return "hello appart %s"% appart_id
    else:
        return "hello all appart"
    

if __name__ == '__main__':
    app.run(debug=True)

