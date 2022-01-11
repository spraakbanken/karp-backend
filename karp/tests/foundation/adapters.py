class FakeUnitOfWork:
    def start(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def __enter__(self):
        self.was_committed = False
        self.was_rolled_back = False
        return self

    def _commit(self):
        self.was_committed = True

    def rollback(self):
        self.was_rolled_back = True
