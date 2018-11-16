__version__ = '0.4.0'
from flask import Flask     # pyre-ignore


# TODO handle settings correctly
def create_app(settings):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from .routes import health_api, karp_api
    app.register_blueprint(karp_api)
    app.register_blueprint(health_api)

    from . import models
    models.init_db(app, settings.get('setup_database', True))

    return app
