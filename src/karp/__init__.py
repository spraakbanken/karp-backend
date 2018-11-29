import os
import pkg_resources

from flask import Flask     # pyre-ignore


__version__ = '0.4.7'


# TODO handle settings correctly
def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object('karp.config.DevelopmentConfig')
    if config_class:
        app.config.from_object(config_class)
    if os.getenv('KARP_CONFIG'):
        app.config.from_object(os.getenv('KARP_CONFIG'))

    from .api import health_api, crud_api, query_api, documentation
    app.register_blueprint(crud_api)
    app.register_blueprint(health_api)
    app.register_blueprint(query_api)
    app.register_blueprint(documentation)

    from .init import init_db
    init_db(app)

    from .search import init_search
    init_search(app)

    return app


def get_version() -> str:
    return __version__


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string(__name__, name).decode('utf-8')
