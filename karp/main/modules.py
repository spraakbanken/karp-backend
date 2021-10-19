import injector
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
