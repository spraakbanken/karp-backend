import logging

from karp.search.application.repositories import (
    Index,
    IndexUnitOfWork,
)


logger = logging.getLogger("karp")


class NoOpIndex(Index):
    pass

    def create_index(self, *args, **kwargs):
        logger.debug("create_index called with args=%s, kwargs=%s", args, kwargs)

    def publish_index(self, *args, **kwargs):
        logger.debug("publish_index called with args=%s, kwargs=%s", args, kwargs)

    def add_entries(self, *args, **kwargs):
        logger.debug("add_entries called with args=%s, kwargs=%s", args, kwargs)

    def delete_entry(self, *args, **kwargs):
        logger.debug("delete_entry called with args=%s, kwargs=%s", args, kwargs)


class NoOpIndexUnitOfWork(IndexUnitOfWork):
    def __init__(self):
        self._repo = NoOpIndex()

    @property
    def repo(self):
        return self._repo

    def _commit(self, *args, **kwargs):
        logger.debug("_commit called with args=%s, kwargs=%s", args, kwargs)

    def _close(self, *args, **kwargs):
        logger.debug("_close called with args=%s, kwargs=%s", args, kwargs)

    def rollback(self, *args, **kwargs):
        logger.debug("rollback called with args=%s, kwargs=%s", args, kwargs)
