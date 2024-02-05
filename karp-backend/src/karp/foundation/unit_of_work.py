import abc  # noqa: D100, I001
import logging


logger = logging.getLogger(__name__)


class UnitOfWork(abc.ABC):
    def __enter__(self):  # noqa: ANN204, D105
        return self.begin()

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN204, D105
        self.rollback()
        self.close()

    def begin(self):  # noqa: ANN201, D102
        return self

    def commit(self):  # noqa: ANN201, D102
        logger.debug("called commit")
        self._commit()

    @abc.abstractmethod
    def _commit(self):  # noqa: ANN202
        raise NotImplementedError()

    @abc.abstractmethod
    def rollback(self):  # noqa: ANN201, D102
        pass

    @property
    @abc.abstractmethod
    def repo(self):  # noqa: D102
        pass

    @abc.abstractmethod
    def _close(self):  # noqa: ANN202
        pass

    def close(self):  # noqa: ANN201, D102
        self._close()
