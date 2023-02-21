import logging  # noqa: D100, I001

from karp.search.application.repositories import (
    Index,
    IndexUnitOfWork,
)


logger = logging.getLogger("karp")


class NoOpIndex(Index):  # noqa: D101
    pass

    def create_index(self, *args, **kwargs):  # noqa: ANN201, ANN003, ANN002, D102
        logger.debug("create_index called with args=%s, kwargs=%s", args, kwargs)

    def publish_index(self, *args, **kwargs):  # noqa: ANN201, ANN003, ANN002, D102
        logger.debug("publish_index called with args=%s, kwargs=%s", args, kwargs)

    def add_entries(self, *args, **kwargs):  # noqa: ANN201, ANN003, ANN002, D102
        logger.debug("add_entries called with args=%s, kwargs=%s", args, kwargs)

    def delete_entry(self, *args, **kwargs):  # noqa: ANN201, ANN003, ANN002, D102
        logger.debug("delete_entry called with args=%s, kwargs=%s", args, kwargs)


class NoOpIndexUnitOfWork(IndexUnitOfWork):  # noqa: D101
    def __init__(self):  # noqa: D107, ANN204
        self._repo = NoOpIndex()

    @property
    def repo(self):  # noqa: ANN201, D102
        return self._repo

    def _commit(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        logger.debug("_commit called with args=%s, kwargs=%s", args, kwargs)

    def _close(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        logger.debug("_close called with args=%s, kwargs=%s", args, kwargs)

    def rollback(self, *args, **kwargs):  # noqa: ANN201, ANN003, ANN002, D102
        logger.debug("rollback called with args=%s, kwargs=%s", args, kwargs)
