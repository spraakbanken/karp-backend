from karp.database import db
from karp.database import ResourceDefinition
from karp.resourcemgr import setup_resource_classes


def init_db(app):
    db.init_app(app)
    with app.app_context():
        if not db.engine.dialect.has_table(db.engine, 'resources'):
            ResourceDefinition.__table__.create(db.engine)
        if app.config.get('SETUP_DATABASE', True):
            setup_resource_classes()
