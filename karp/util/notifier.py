from typing import Any, Optional, Set

import attr


class Observer:
    def update(self, **kwargs):
        pass


@attr.s(auto_attribs=True)
class Notifier:
    observers: Set[Observer] = attr.Factory(set)

    def register(self, who: Observer):
        self.observers.add(who)

    def unregister(self, who: Observer):
        try:
            self.observers.remove(who)
        except KeyError:
            pass

    def notify(self, **kwargs):
        for observer in self.observers:
            observer.update(**kwargs)

