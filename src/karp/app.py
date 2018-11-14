from flask import Flask     # pyre-ignore

from .web import karp_api
from karp.models import db
from karp.routes import karp_health_api


def create_app(settings):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.register_blueprint(karp_api)
    app.register_blueprint(karp_health_api)

    db.init_app(app)
    # temporary setup of tables
    db.create_all(app=app)

    return app
