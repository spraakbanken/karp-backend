__version__ = '0.4.0'
from flask import Flask     # pyre-ignore
from flask_sqlalchemy import SQLAlchemy     # pyre-ignore

db = SQLAlchemy()


# TODO handle settings correctly
def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from .routes import health_api, karp_api, query_api
    app.register_blueprint(karp_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)

    from . import models
    models.init_db(app)

    return app
