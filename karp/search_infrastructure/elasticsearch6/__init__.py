# from elasticsearch import Elasticsearch  # pyre-ignore

# from karp.application import ctx
# from karp.infrastructure.elasticsearch6.es6_search_service import Es6SearchService


# def init_es(host):
#     print("Setting up ES with host={}".format(host))
#     es = Elasticsearch(
#         hosts=host,
#         sniff_on_start=True,
#         sniff_on_connection_fail=True,
#         sniffer_timeout=60,
#         sniff_timeout=10,
#     )
#     search_service = Es6SearchService(es)
#     ctx.search_service = search_service
