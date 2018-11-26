import os


MYSQL_FORMAT = "mysql://{user}:{passwd}@{dbhost}/{dbname}"


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200').split(',')


class ProductionConfig(Config):
    def __init__(self):
        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=os.environ["MARIADB_USER"],
            pwd=os.environ["MARIADB_PASSWORD"],
            dbhost=os.environ["MARIADB_HOST"],
            dbname=os.environ["MARIADB_DATABASE"]
        )


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


def get_config():
    return Config()


class MariaDBConfig(Config):
    SETUP_DATABASE = False

    def __init__(self, user=None, pwd=None, host=None, dbname=None):
        if not user:
            user = os.environ["MARIADB_USER"]
        if not pwd:
            pwd = os.environ["MARIADB_PASSWORD"]
        if not host:
            host = os.environ["MARIADB_HOST"]
        if not dbname:
            dbname = os.environ["MARIADB_DATABASE"]

        self.SQLALCHEMY_DATABASE_URI = MYSQL_FORMAT.format(
            user=user,
            passwd=pwd,
            dbhost=host,
            dbname=dbname
        )
