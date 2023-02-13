class InMemoryUnitOfWork:
    def __init__(self, **kwargs):
        self.was_committed = False
        self.was_rolled_back = False
        self.was_closed = False

    def start(self):
        self.was_committed = False
        self.was_rolled_back = False
        self.was_closed = False
        return self

    def __enter__(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def _commit(self):
        self.was_committed = True

    def rollback(self):
        self.was_rolled_back = True

    def _close(self):
        self.was_closed = True
