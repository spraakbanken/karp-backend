import injector
from karp.foundation.commands import CommandBus, InjectorCommandBus


class CommandBusMod(injector.Module):
    @injector.provider
    def command_bus(self, inj: injector.Injector) -> CommandBus:
        return InjectorCommandBus(inj)
