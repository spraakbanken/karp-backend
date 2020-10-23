import os
import logging
from distutils.util import strtobool

MYSQL_FORMAT = "mysql://{user}:{passwd}@{dbhost}/{dbname}"


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ELASTICSEARCH_HOST = (
        os.environ["ELASTICSEARCH_HOST"].split(",")
        if "ELASTICSEARCH_HOST" in os.environ
        else None
    )
    ELASTICSEARCH_ENABLED = strtobool(os.environ.get("ELASTICSEARCH_ENABLED", "n"))
    # CONSOLE_LOG_LEVEL = logging.getLevelName(
    #     os.environ.get("CONSOLE_LOG_LEVEL", "INFO")
    # )
    CONSOLE_LOG_LEVEL = getattr(
        logging, os.environ.get("CONSOLE_LOG_LEVEL", "INFO"), logging.INFO
    )
    LOG_TO_SLACK = strtobool(os.environ.get("LOG_TO_SLACK", "n"))
    SLACK_SECRET = os.environ.get("SLACK_SECRET")
    JWT_AUTH = strtobool(os.environ.get("JWT_AUTH", "n"))
    REVERSE_PROXY_PATH = os.environ.get("REVERSE_PROXY_PATH")


class ProductionConfig(Config):
    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=os.environ["MARIADB_USER"],
            pwd=os.environ["MARIADB_PASSWORD"],
            dbhost=os.environ["MARIADB_HOST"],
            dbname=os.environ["MARIADB_DATABASE"],
        )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


def get_config():
    return Config()


class MariaDBConfig(Config):
    def __init__(
        self, user=None, pwd=None, host=None, dbname=None, setup_database=False
    ):
        if not user:
            user = os.environ["MARIADB_USER"]
        if not pwd:
            pwd = os.environ["MARIADB_PASSWORD"]
        if not host:
            host = os.environ["MARIADB_HOST"]
        if not dbname:
            dbname = os.environ["MARIADB_DATABASE"]

        self.SETUP_DATABASE = setup_database
        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=user, passwd=pwd, dbhost=host, dbname=dbname
        )
