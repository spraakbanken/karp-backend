import os
import flask
from flask import Flask

app = Flask(__name__)
user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

import karp.database as database


@app.route("/entries", methods=['GET'])
def get_entries():
    entries = database.get_entries()
    return flask.jsonify([entry.serialize for entry in entries])


@app.route("/entry/<value>", methods=['POST'])
def add_entry(value):
    database.add_entry(value)
    return flask.jsonify({'status': 'added'}), 201


@app.route("/entry/<value>", methods=['DELETE'])
def delete_entry(value):
    database.delete_entry(value)
    return flask.jsonify({'status': 'removed'})


@app.route("/entry/<value>", methods=['GET'])
def get_entry(value):
    entry = database.get_entry(value)
    return flask.jsonify(entry.serialize)
