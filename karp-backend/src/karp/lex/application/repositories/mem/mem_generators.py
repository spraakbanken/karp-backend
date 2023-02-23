from karp.lex.application.repositories import GeneratorUnitOfWork


class InMemoryGeneratorUnitOfWork(GeneratorUnitOfWork):
    @property
    def repo(self):
        pass

    def _close(self):
        pass

    def _commit(self):
        pass

    def rollback(self):
        pass
