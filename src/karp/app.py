from flask import Flask     # pyre-ignore

from .web import karp_api
from .routes import health_api
from .models import db, setup_resource_classes


def create_app(settings):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings['SQLALCHEMY_DATABASE_URI']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.register_blueprint(karp_api)
    app.register_blueprint(health_api)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        if settings.get('setup_database', True):
            setup_resource_classes()

    return app
