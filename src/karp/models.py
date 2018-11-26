import json
import fastjsonschema  # pyre-ignore
from typing import BinaryIO, Tuple
import pkg_resources
from sqlalchemy.sql import func
from karp import db


def init_db(app):
    db.init_app(app)
    with app.app_context():
        if not db.engine.dialect.has_table(db.engine, 'resource'):
            Resource.__table__.create(db.engine)
        if app.config.get('SETUP_DATABASE', True):
            setup_resource_classes()


class Resource(db.Model):
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


def create_sqlalchemy_class(config, version):
    resource_id = config['resource_id']

    conf_fields = config['fields']
    fields = []
    for field_name, field_conf in conf_fields.items():
        field_type = field_conf["type"]
        collection = field_conf.get("collection", False)

        if field_type == 'object' or collection:
            column_type = db.Text
        elif field_type == 'number':
            column_type = db.Integer
        elif field_type == 'string':
            column_type = db.Text
        else:
            raise ValueError('Not implemented yet')

        kwargs = {}
        if 'required' in field_conf:
            kwargs['nullable'] = not field_conf['required']

        fields.append((field_name, db.Column(column_type, **kwargs)))

    def serialize(self):
        res = {
            'id': self.id
        }

        for field, _ in fields:
            res[field] = getattr(self, field)

        return res

    table_name = resource_id + '_' + str(version)
    if table_name in class_cache:
        return class_cache[table_name]
    else:
        attributes = {
            '__tablename__': table_name,
            'id': db.Column(db.Integer, primary_key=True),
            'serialize': serialize
        }
        if 'id' in config:
            constraints = (
                db.UniqueConstraint(config['id'], name='entry_id_unique_constraint'),
            )
            attributes['__table_args__'] = constraints

        for (field_name, field_column) in fields:
            attributes[field_name] = field_column

        def _repr(self):
            strs = ['id=%s' % self.id]
            for (key, _) in fields:
                strs.append('%s=%s' % (key, getattr(self, key)))
            return '<%s(' % table_name + ', '.join(strs) + ')>'
        attributes['__repr__'] = _repr

        sqlalchemy_class = type(resource_id, (db.Model,), attributes)
        class_cache[table_name] = sqlalchemy_class
        return sqlalchemy_class


class_cache = {}
resource_classes = {}


def get_available_resources():
    return Resource.query.filter_by(active=True)


def setup_resource_classes():
    for resource in get_available_resources():
        config = json.loads(resource.config_file)
        resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def setup_resource_class(resource_id, version=None):
    if version:
        resource = Resource.query.filter_by(resource_id=resource_id, version=version).first()
    else:
        resource = Resource.query.filter_by(resource_id=resource_id, active=True).first()
    config = json.loads(resource.config_file)
    resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def create_new_resource(config_file: BinaryIO) -> Tuple[str, int]:
    config = json.load(config_file)
    try:
        schema = (
            pkg_resources
                .resource_string(__name__,
                                 'schema/resourceconf.schema.json')
                .decode('utf-8')
        )
        validate_conf = fastjsonschema.compile(json.loads(schema))
        validate_conf(config)
    except fastjsonschema.JsonSchemaException as e:
        raise RuntimeError(e)

    resource_id = config['resource_id']

    latest_resource = (
        Resource.query
                .filter_by(resource_id=resource_id)
                .order_by(Resource.version.desc())
                .first()
    )
    if latest_resource:
        version = latest_resource.version + 1
    else:
        version = 1

    entry_json_schema = create_entry_json_schema(config)

    resource = {
        'resource_id': resource_id,
        'version': version,
        'config_file': json.dumps(config),
        'entry_json_schema': json.dumps(entry_json_schema)
    }

    new_resource = Resource(**resource)
    db.session.add(new_resource)
    db.session.commit()

    sqlalchemyclass = create_sqlalchemy_class(config, version)

    sqlalchemyclass.__table__.create(bind=db.engine)

    return resource['resource_id'], resource['version']


def publish_resource(resource_id, version):
    resource = Resource.query.filter_by(resource_id=resource_id, version=version).first()
    old_active = Resource.query.filter_by(resource_id=resource_id, version=version, active=True).first()
    if old_active:
        old_active.active = False
    resource.active = True
    db.session.commit()

    config = json.loads(resource.config_file)

    # this stuff doesn't matter right now since we are not modifying the state of the actual app, only the CLI
    resource_classes[config['resource_id']] = create_sqlalchemy_class(config, resource.version)


def unpublish_resource(resource_id):
    resource = Resource.query.filter_by(resource_id=resource_id, active=True).first()
    if resource:
        resource.active = False
        db.session.update(resource)
        db.session.commit()
    del resource_classes[resource_id]


def delete_resource(resource_id, version):
    resource = Resource.query.filter_by(resource_id=resource_id, version=version).first()
    resource.deleted = True
    resource.active = False
    db.session.update(resource)
    db.session.commit()


def create_entry_json_schema(config):
    json_schema = {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        'properties': {}
    }

    fields = config['fields']

    def recursive_field(parent_schema, parent_field_name, parent_field_def):
        if parent_field_def['type'] != 'object':
            # TODO this will not work when we have user defined types, s.a. saldoid
            result = {
                'type': parent_field_def['type']
            }
        else:
            result = {
                'type': 'object',
                'properties': {}
            }

            for child_field_name, child_field_def in parent_field_def['fields'].items():
                recursive_field(result, child_field_name, child_field_def)

        if parent_field_def.get('required', False):
            if 'required' not in parent_schema:
                parent_schema['required'] = []
            parent_schema['required'].append(parent_field_name)

        if parent_field_def.get('collection', False):
            result = {
                'type': 'array',
                'items': result
            }

        parent_schema['properties'][parent_field_name] = result

    for field_name, field_def in fields.items():
        recursive_field(json_schema, field_name, field_def)

    return json_schema
