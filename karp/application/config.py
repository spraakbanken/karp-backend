import os
import logging
from distutils.util import strtobool

from sqlalchemy.engine.url import URL, make_url

from starlette.config import Config as StarletteConfig
from starlette.datastructures import CommaSeparatedStrings, Secret

config = StarletteConfig(".env")

DEBUG = config("DEBUG", cast=bool, default=False)
TESTING = config("TESTING", cast=bool, default=False)

DB_DRIVER = config("DB_DRIVER", default="mysql")
DB_HOST = config("DB_HOST", default=None)
DB_PORT = config("DB_PORT", cast=int, default=None)
DB_USER = config("DB_USER", default=None)
DB_PASSWORD = config("DB_PASSWORD", cast=Secret, default=None)
DB_DATABASE = config("DB_DATABASE", default=None)
if TESTING is True:
    DB_DATABASE = f"test_{DB_DATABASE}"
DB_URL = config(
    "DB_URL",
    cast=make_url,
    default=URL(
        drivername=DB_DRIVER,
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_DATABASE,
    ),
)

ELASTICSEARCH_HOST = config(
    "ELASTICSEARCH_HOST", cast=CommaSeparatedStrings, default=None
)
# MYSQL_FORMAT = "mysql://{user}:{passwd}@{dbhost}/{dbname}"


# class Config:
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     DEBUG = False
#     TESTING = False
#     SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
#     ELASTICSEARCH_HOST = (
#         os.environ["ELASTICSEARCH_HOST"].split(",")
#         if "ELASTICSEARCH_HOST" in os.environ
#         else None
#     )
#     ELASTICSEARCH_ENABLED = strtobool(os.environ.get("ELASTICSEARCH_ENABLED", "n"))
#     # CONSOLE_LOG_LEVEL = logging.getLevelName(
#     #     os.environ.get("CONSOLE_LOG_LEVEL", "INFO")
#     # )
#     CONSOLE_LOG_LEVEL = getattr(
#         logging, os.environ.get("CONSOLE_LOG_LEVEL", "INFO"), logging.INFO
#     )
#     LOG_TO_SLACK = strtobool(os.environ.get("LOG_TO_SLACK", "n"))
#     SLACK_SECRET = os.environ.get("SLACK_SECRET")
#     JWT_AUTH = strtobool(os.environ.get("JWT_AUTH", "n"))


# class ProductionConfig(Config):
#     def __init__(self):
#         self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
#             user=os.environ["MARIADB_USER"],
#             pwd=os.environ["MARIADB_PASSWORD"],
#             dbhost=os.environ["MARIADB_HOST"],
#             dbname=os.environ["MARIADB_DATABASE"],
#         )


# class DevelopmentConfig(Config):
#     DEBUG = True


# class TestingConfig(Config):
#     TESTING = True


# def get_config():
#     return Config()


# class MariaDBConfig(Config):
#     def __init__(
#         self, user=None, pwd=None, host=None, dbname=None, setup_database=False
#     ):
#         if not user:
#             user = os.environ["MARIADB_USER"]
#         if not pwd:
#             pwd = os.environ["MARIADB_PASSWORD"]
#         if not host:
#             host = os.environ["MARIADB_HOST"]
#         if not dbname:
#             dbname = os.environ["MARIADB_DATABASE"]

#         self.SETUP_DATABASE = setup_database
#         self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
#             user=user, passwd=pwd, dbhost=host, dbname=dbname
#         )


# def create_config() -> Config:
#     return Config()