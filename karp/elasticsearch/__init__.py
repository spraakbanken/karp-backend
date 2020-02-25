from elasticsearch import Elasticsearch  # pyre-ignore
from .index import EsIndex
from .search import EsSearch
from karp import search
from karp.indexmgr import indexer


def init_es(host):
    print("Setting up ES with host={}".format(host))
    es = Elasticsearch(
        hosts=host,
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60,
        sniff_timeout=10,
    )
    index_module = EsIndex(es)
    search_module = EsSearch(es)
    search.init(search_module)
    indexer.init(index_module)
