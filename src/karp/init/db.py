from karp.database import db
from karp.resourcemgr import setup_resource_classes


# TODO: Move this function to database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        if app.config.get('SETUP_DATABASE', True):
            setup_resource_classes()
