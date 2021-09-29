from karp import create_app
from karp.config import MariaDBConfig
from karp.database import ResourceDefinition

app = create_app(MariaDBConfig(setup_database=False))

with app.app_context():
    try:
        entry_tables = [
            resource.resource_id + "_" + str(resource.version)
            for resource in ResourceDefinition.query.all()
        ]
        history_tables = [table_name + "_history" for table_name in entry_tables]
    except Exception:
        entry_tables = []
        history_tables = []

database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
