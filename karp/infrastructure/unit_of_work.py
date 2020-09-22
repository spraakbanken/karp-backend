"""Unit of Work"""
from functools import singledispatch
from typing import ContextManager


def unit_of_work(*, using, **kwargs) -> ContextManager:
    return create_unit_of_work(using, **kwargs)


@singledispatch
def create_unit_of_work(repo):
    class Dummy:
        def __enter__(self):
            raise NotImplementedError(f"Can't handle repository '{repo!r}'")

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    return Dummy()
