"""Event handling."""
import abc

from karp.domain.common import _now
from karp.utility.time import monotonic_utc_now


class DomainEvent:
    def __init__(self, timestamp=_now, **kwargs):
        self.__dict__["timestamp"] = (
            monotonic_utc_now() if timestamp is _now else timestamp
        )
        self.__dict__.update(kwargs)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError(
                f"{self.__class__.__name__} attributes can be added but not modified."
                f" Attribute '{key!r}' already exists with value '{getattr(self,key)!r}'"
            )
        self.__dict__[key] = value

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        dict_str = ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items())
        return f"{self.__class__.__qualname__}({dict_str})"

    @abc.abstractmethod
    def mutate(self, obj):
        raise NotImplementedError()
