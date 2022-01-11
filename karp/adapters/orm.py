import logging

import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.orm.exc
from sqlalchemy import (Column, Integer, MetaData, String, Table, Text,
                        create_engine)
from sqlalchemy.orm import composite, mapper, scoped_session, sessionmaker
from sqlalchemy_utils.functions import create_database, drop_database

from karp.domain.model import Resource, ResourceReporter
from karp.domain.ports import UnitOfWork, UnitOfWorkManager


class SqlAlchemyUnitOfWorkManager(UnitOfWorkManager):

    def __init__(self, session_maker):
        self.session_maker = session_maker

    def start(self):
        return SqlAlchemyUnitOfWork(self.session_maker)


class ResourceRepository:

    def __init__(self, session):
        self._session = session

    def add(self, resource: Resource) -> None:
        self._session.add(resource)


class SqlAlchemyUnitOfWork(UnitOfWork):

    def __init__(self, sessionfactory):
        self.sessionfactory = sessionfactory

    def __enter__(self):
        self.session = self.sessionfactory()
        return self

    def __exit__(self, type, value, traceback):
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    @property
    def resources(self):
        return ResourceRepository(self.session)


class SqlAlchemy:
    def __init__(self, uri):
        self.engine = create_engine(uri)
        self._session_maker = scoped_session(sessionmaker(self.engine))

    @property
    def unit_of_work_manager(self):
        return SqlAlchemyUnitOfWorkManager(self._session_maker)

    def get_session(self):
        return self._session_maker()

    def recreate_schema(self):
        drop_database(self.engine.url)
        create_database(self.engine.url)
        self.metadata.create_all()

    def configure_mappings(self):
        self.metadata = MetaData(self.engine)

        ResourceReporter.__composite_values__ = lambda i: (i.name, i.email)
        resources = Table(
            'resources', self.metadata,
                       Column('id', Integer, primary_key=True),
                       Column('reporter_name', String(50)),
                       Column('reporter_email', String(50)),
                       Column('description', Text))
        mapper(
            Resource,
            resources,
            properties={
                'id': resources.c.id,
                'description': resources.c.description,
                'reporter': composite(
                    ResourceReporter,
                    resources.c.reporter_name,
                    resources.c.reporter_email)
            },
        )
