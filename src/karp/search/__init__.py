from karp.search.search import KarpSearch, SearchInterface
from karp.search.essearch import EsSearch

search = KarpSearch()


def init_search(app):
    """
    TODO in the future we will implement an alternative search, s.a. MySQL for simple resources
    """
    if app.config['ELASTICSEARCH_ENABLED'] and app.config.get('ELASTICSEARCH_HOST', ''):
        search.init(EsSearch(app.config['ELASTICSEARCH_HOST']))
    else:
        search.init(SearchInterface())
