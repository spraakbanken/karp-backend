from flask_sqlalchemy import SQLAlchemy     # pyre-ignore

db = SQLAlchemy()


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return "<Entry(value='%s')>" % self.value

    @property
    def serialize(self):
        return {
           'id': self.id,
           'value': self.value
        }
