import elasticsearch
import injector
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import sessionmaker

from karp.foundation.commands import CommandBus, InjectorCommandBus
from karp.foundation.events import EventBus, InjectorEventBus


class CommandBusMod(injector.Module):
    @injector.provider
    def command_bus(self, inj: injector.Injector) -> CommandBus:
        return InjectorCommandBus(inj)


class EventBusMod(injector.Module):
    @injector.provider
    def event_bus(self, inj: injector.Injector) -> EventBus:
        return InjectorEventBus(inj)


class Db(injector.Module):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # @request
    @injector.provider
    def connection(self) -> Connection:
        return self._engine.connect()

    @injector.provider
    def session_factory(self) -> sessionmaker:
        return sessionmaker(bind=self._engine)


class ElasticSearchMod(injector.Module):
    def __init__(self, es_url: str) -> None:
        self._url = es_url

    @injector.provider
    @injector.singleton
    def es(self) -> elasticsearch.Elasticsearch:
        return elasticsearch.Elasticsearch(self._url)
