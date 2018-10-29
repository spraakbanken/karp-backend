import os
import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]
app.config['SQLALCHEMY_DATABASE_URI'] = \
  'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return "<Entry(value='%s')>" % self.value

    @property
    def serialize(self):
        return {
           'id': self.id,
           'value': self.value
        }


# temporary setup of tables
db.create_all()


@app.route("/entries", methods=['GET'])
def get_entries():
    entries = Entry.query.all()
    return flask.jsonify([entry.serialize for entry in entries])


@app.route("/entry/<value>", methods=['POST'])
def add_entry(value):
    entry = Entry(value=value)
    db.session.add(entry)
    db.session.commit()
    return flask.jsonify({'status': 'added'}), 201


@app.route("/entry/<value>", methods=['DELETE'])
def delete_entry(value):
    entry = Entry.query.filter(value=value).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    return flask.jsonify({'status': 'removed'})


@app.route("/entry/<value>", methods=['GET'])
def get_entry(value):
    entry = Entry.query.filter(value=value).first_or_404()
    return flask.jsonify(entry.serialize)
