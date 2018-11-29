from flask_sqlalchemy import SQLAlchemy     # pyre-ignore
from sqlalchemy.sql import func  # pyre-ignore


db = SQLAlchemy()


class Resources(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.String(30), nullable=False)
    version = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False, server_default=func.now())
    config_file = db.Column(db.Text, nullable=False)
    entry_json_schema = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)
    __table_args__ = (
        db.UniqueConstraint('resource_id',
                            'version',
                            name='resource_version_unique_constraint'),
        # TODO only one resource can be active, but several can be inactive
        #    here is how to do it in MariaDB, unclear whether this is possible using SQLAlchemy
        #    `virtual_column` char(0) as (if(active,'', NULL)) persistent
        #    and
        #    UNIQUE KEY `resource_version_unique_active` (`resource_id`,`virtual_column`)
        #    this works because the tuple (saldo, NULL) is not equal to (saldo, NULL)
    )

    def __repr__(self):
        return """<Resource(resource_id='{}',
                            version='{}',
                            timestamp='{}',
                            active='{}',
                            deleted='{}')
                >""".format(self.resource_id,
                            self.version,
                            self.timestamp,
                            self.active,
                            self.deleted)


class_cache = {}


def create_sqlalchemy_class(config, version):
    resource_id = config['resource_id']
    table_name = resource_id + '_' + str(version)
    if table_name in class_cache:
        return class_cache[table_name]
    else:

        attributes = {
            '__tablename__': table_name,
            'id': db.Column(db.Integer, primary_key=True),
            'body': db.Column(db.Text, nullable=False)
        }

        if 'id' in config:
            id_field = config['id']
            field_type = config['fields'][id_field]['type']

            if field_type == 'number':
                column_type = db.Integer
            elif field_type == 'string':
                column_type = db.Text
            else:
                raise ValueError('Not implemented yet')
            constraints = (
                db.UniqueConstraint(id_field, name='entry_id_unique_constraint'),
            )
            attributes[id_field] = db.Column(column_type, nullable=False)
            attributes['__table_args__'] = constraints
        else:
            id_field = None

        def _repr(self):
            if id_field:
                return '<%s(id=%s,%s=%s)>' % (table_name, self.id, id_field, getattr(self, id_field))
            else:
                return '<%s(id=%s)>' % (table_name, self.id)
        attributes['__repr__'] = _repr

        sqlalchemy_class = type(resource_id, (db.Model,), attributes)
        class_cache[table_name] = sqlalchemy_class
        return sqlalchemy_class
