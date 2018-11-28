import os

from flask import Flask     # pyre-ignore
from flask_sqlalchemy import SQLAlchemy     # pyre-ignore


__version__ = '0.4.6'

db = SQLAlchemy()


# TODO handle settings correctly
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object('karp.config.DevelopmentConfig')
    if config_class:
        app.config.from_object(config_class)
    if os.getenv('KARP_CONFIG'):
        app.config.from_object(os.getenv('KARP_CONFIG'))

    from .api import health_api, crud_api, query_api, documentation
    app.register_blueprint(crud_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)
    app.register_blueprint(documentation)

    from . import models
    models.init_db(app)

    return app
