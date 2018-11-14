import json
import glob

from flask_sqlalchemy import SQLAlchemy     # pyre-ignore


db = SQLAlchemy()


def create_sqlalchemy_class(config):
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
        'id': db.Column(db.Integer, primary_key=True),
        'serialize': serialize
    }

    for (field_name, field_column) in fields:
        attributes[field_name] = field_column

    sqlalchemy_class = type(resource_id, (db.Model,), attributes)
    return sqlalchemy_class


resource_classes = {}


def setup_resource_classes():
    # Needs to be edited for tests to work
    for config_file in glob.glob('config/*'):
        config = json.load(open(config_file))
        resource_classes[config['resource_id']] = create_sqlalchemy_class(config)


setup_resource_classes()
