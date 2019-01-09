import os
import pkg_resources
import json

from flask import Flask     # pyre-ignore

from karp.errors import KarpError

__version__ = '0.6.0'


# TODO handle settings correctly
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object('karp.config.DevelopmentConfig')
    if config_class:
        app.config.from_object(config_class)
    if os.getenv('KARP_CONFIG'):
        app.config.from_object(os.getenv('KARP_CONFIG'))

    from .api import health_api, edit_api, query_api, documentation
    app.register_blueprint(edit_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)
    app.register_blueprint(documentation)

    from .init import init_db
    init_db(app)

    if app.config['ELASTICSEARCH_ENABLED'] and app.config.get('ELASTICSEARCH_HOST', ''):
        from karp.elasticsearch import init_es
        init_es(app.config['ELASTICSEARCH_HOST'])
    else:
        # TODO if an elasticsearch test runs before a non elasticsearch test this
        # is needed to reset the index and search modules
        from karp.search import SearchInterface, search
        from karp.indexmgr.index import IndexInterface
        from karp.indexmgr import indexer
        search.init(SearchInterface())
        indexer.init(IndexInterface())

    @app.errorhandler(KarpError)
    def http_error_handler(error: KarpError):
        return json.dumps({'error': error.message}), 400

    return app


def get_version() -> str:
    return __version__


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string(__name__, name).decode('utf-8')
