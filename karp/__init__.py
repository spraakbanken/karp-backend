import pkg_resources

# from flask import Flask  # pyre-ignore
# from flask_cors import CORS  # pyre-ignore
# from flask import request  # pyre-ignore
# import flask_reverse_proxy
# import werkzeug.exceptions


__version__ = "6.0.19"


# TODO handle settings correctly
# def create_app(config_class=None):
#     app = Flask(__name__)
#     app.config.from_object("karp.config.DevelopmentConfig")
#     if config_class:
#         app.config.from_object(config_class)
#     if os.getenv("KARP_CONFIG"):
#         app.config.from_object(os.getenv("KARP_CONFIG"))

#     logger = setup_logging(app)

#     from .api import (
#         health_api,
#         edit_api,
#         query_api,
#         conf_api,
#         documentation,
#         stats_api,
#         history_api,
#     )

#     app.register_blueprint(edit_api)
#     app.register_blueprint(health_api)
#     app.register_blueprint(query_api)
#     app.register_blueprint(conf_api)
#     app.register_blueprint(documentation)
#     app.register_blueprint(stats_api)
#     app.register_blueprint(history_api)

#     from .database import db

#     db.init_app(app)

#     if app.config.get("SETUP_DATABASE", True):
#         from .resourcemgr import setup_resource_classes

#         with app.app_context():
#             setup_resource_classes()

#     if app.config["ELASTICSEARCH_ENABLED"] and app.config.get("ELASTICSEARCH_HOST", ""):
#         from karp.elasticsearch import init_es

#         init_es(app.config["ELASTICSEARCH_HOST"])
#     else:
#         # TODO if an elasticsearch test runs before a non elasticsearch test this
#         # is needed to reset the index and search modules
#         from karp import search
#         from karp.indexmgr.index import IndexInterface
#         from karp.indexmgr import indexer

#         search.init(search.SearchInterface())
#         indexer.init(IndexInterface())

#     with app.app_context():
#         import karp.pluginmanager

#         karp.pluginmanager.init()

#     @app.errorhandler(Exception)
#     def http_error_handler(error: Exception):
#         error_str = "Exception on %s [%s]" % (request.path, request.method)
#         if isinstance(error, werkzeug.exceptions.NotFound):
#             logger.debug(error_str)
#             return "", 404

#         if isinstance(error, KarpError):
#             logger.debug(error_str)
#             logger.debug(error.message)
#             error_code = error.code if error.code else 0
#             return (
#                 json.dumps({"error": error.message, "errorCode": error_code}),
#                 error.http_return_code,
#             )
#         else:
#             if app.config["DEBUG"]:
#                 raise error
#             logger.error(error_str)
#             logger.exception("unhandled exception")
#             return json.dumps({"error": "unknown error", "errorCode": 0}), 400

#     import karp.auth.auth as auth

#     if app.config["JWT_AUTH"]:
#         from karp.auth.jwt_authenticator import JWTAuthenticator

#         auth.auth.set_authenticator(JWTAuthenticator())
#     else:
#         from karp.auth.authenticator import Authenticator

#         auth.auth.set_authenticator(Authenticator())

#     CORS(app)

#     app.wsgi_app = flask_reverse_proxy.ReverseProxied(app.wsgi_app)
#     return app


# def setup_logging(app):
#     logger = logging.getLogger("karp")
#     if app.config.get("LOG_TO_SLACK"):
#         slack_handler = slack_logging.get_slack_logging_handler(
#             app.config.get("SLACK_SECRET")
#         )
#         logger.addHandler(slack_handler)
#     console_handler = logging.StreamHandler()
#     formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
#     console_handler.setFormatter(formatter)
#     logger.setLevel(app.config["CONSOLE_LOG_LEVEL"])
#     logger.addHandler(console_handler)
#     return logger


def get_version() -> str:
    return __version__


def get_resource_string(name: str) -> str:
    return pkg_resources.resource_string(__name__, name).decode("utf-8")
