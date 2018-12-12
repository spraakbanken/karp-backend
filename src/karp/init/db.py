from karp.database import db, ResourceDefinition
from karp.resourcemgr import setup_resource_classes


# TODO: Move this function to database
def init_db(app):
    db.init_app(app)
    with app.app_context():
        # TODO this must be here right now, even though alembic is in change of table creation
        # if removed, something complains about resource_definiton not existing, even though it does!
        if not db.engine.dialect.has_table(db.engine, 'resource_definition'):
            ResourceDefinition.__table__.create(db.engine)
        if app.config.get('SETUP_DATABASE', True):
            setup_resource_classes()
