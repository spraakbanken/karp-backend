import json
from flask_sqlalchemy import SQLAlchemy     # pyre-ignore
import datetime

db = SQLAlchemy()


class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.String(30), nullable=False)
    version = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    config_file = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=False)
    deleted = db.Column(db.Boolean, default=False)

    # TODO skapa constraint på resource_id och active = true
    # TODO skapa constraint på resource_id och version

    def __repr__(self):
        return "<Resource(resource_id='%s', version='%s', timestamp='%s', active='%s', deleted='%s')>" % \
               (self.resource_id, self.version, self.timestamp, self.active, self.deleted)


def create_sqlalchemy_class(config, version):
    resource_id = config['resource_id']

    conf_fields = config['fields']
    fields = []
    for field_name, field_conf in conf_fields.items():
        field_type = field_conf["type"]
        if field_type == 'object':
            pass
        elif field_type == 'array':
            pass
        elif field_type == 'link':
            pass
        else:
            if field_type == 'number':
                column_type = db.Integer
            elif field_type == 'string':
                column_type = db.String(30)
            else:
                raise ValueError('Not implemented yet')

            kwargs = {}  # not implemented yet

            fields.append((field_name, db.Column(column_type, **kwargs)))

    def serialize(self):
        res = {
            'id': self.id
        }

        for field, _ in fields:
            res[field] = getattr(self, field)

        return res

    attributes = {
        '__tablename__': resource_id + '_' + str(version),
        'id': db.Column(db.Integer, primary_key=True),
        'serialize': serialize
    }

    for (field_name, field_column) in fields:
        attributes[field_name] = field_column

    sqlalchemy_class = type(resource_id, (db.Model,), attributes)
    return sqlalchemy_class


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


def create_new_resource(config_file):
    config = json.load(open(config_file))
    resource_id = config['resource_id']

    latest_resource = Resource.query.filter_by(resource_id=resource_id).order_by('version').first()
    if latest_resource:
        version = latest_resource.version + 1
    else:
        version = 1

    resource = {
        'resource_id': resource_id,
        'version': version,
        'config_file': json.dumps(config)
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
        # db.session.update(old_active)
    resource.active = True
    # db.session.update(resource)
    db.session.commit()

    config = json.loads(resource.config_file)

    # this stuff doesn't matter right now since we are not modifying the state of the actual app
    # only the CLI
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
