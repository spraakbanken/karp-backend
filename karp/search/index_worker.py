import asyncio

from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session

from karp.lex.infrastructure import ResourceRepository
from karp.lex.infrastructure.sql.models import IndexJob
from karp.search.infrastructure import EsIndex, EsMappingRepository


async def start(elasticsearch_url, sqlalchemy_engine):
    es = Elasticsearch(elasticsearch_url)
    # TODO how to create a session here
    session = Session(bind=sqlalchemy_engine)
    resource_repo: ResourceRepository = ResourceRepository(session)
    mapping_repo = EsMappingRepository(es, resource_repo)
    indices = EsIndex(es, mapping_repo)
    while True:
        # TODO can we trigger it when something has happened in MariaDB instead of always sleeping and waking on a schedule

        # TODO how to create a session here
        session = Session(bind=sqlalchemy_engine)
        jobs = session.query(IndexJob).all()
        reindex = set()
        index = []
        for job in jobs:
            if job.op == "REINDEX":
                reindex.add(job.resource_id)
            else:
                index.append(job)

        # now we must check for dependencies, we must first update the resources that does not have any dependencies
        # Do we need to check really? MariaDB contains the truth and that's were we will be fetching the data
        # for links

        done_index = []
        for job in index:
            # only save index jobs that will not be reindexed anyway
            if job.resource_id not in reindex:
                # TODO for each job, check if there are dependencies, add dependencies to job table
                if job.op == "ADD":
                    doc = {
                        "_index": job.resource_id,
                        "_id": str(job.entry_id),
                        "_source": job.body,
                    }

                else:
                    doc = {
                        "_op_type": "delete",
                        "_index": job.resource_id,
                        "_id": str(job.entry_id),
                    }
                done_index.append(doc)

        try:
            indices.update_index(done_index)
        except Exception as e:  # noqa BLE001
            # TODO handle
            print(str(e))
            continue
        for row in index:
            session.delete(row)
        session.commit()

        await asyncio.sleep(1)
