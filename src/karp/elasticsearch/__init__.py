from elasticsearch import Elasticsearch
from .index import EsIndex
from .search import EsSearch
import karp.search.search
from karp.resourcemgr.index import index_mgr


def init_es(host):
    es = Elasticsearch(hosts=host)
    index_module = EsIndex(es)
    search_module = EsSearch(es)
    karp.search.search.init(search_module)
    index_mgr.init(index_module)
