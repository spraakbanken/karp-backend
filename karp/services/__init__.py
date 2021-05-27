from karp.domain.commands import CreateResourceCommand
from karp.domain.model import Resource
# from karp.domain.model import Issue, IssueReporter
from karp.domain.ports import UnitOfWorkManager


class CreateResourceHandler:
    def __init__(self, uowm: UnitOfWorkManager):
        self.uowm = uowm

    def handle(self, cmd: CreateResourceCommand):
        # reporter = IssueReporter(cmd.reporter_name, cmd.reporter_email)
        resource = Resource(
            entity_id=cmd.id,
            resource_id=cmd.resource_id,
            name=cmd.name,
            config=cmd.config,
            message=cmd.message,
        )

        with self.uowm.start() as tx:
            tx.resources.add(resource)
            tx.commit()
