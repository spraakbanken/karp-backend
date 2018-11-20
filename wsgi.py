import os

from karp import create_app
from karp.config import BaseConfig

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]


class Config(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"mysql://{user}:{passwd}@{dbhost}/{dbname}"
    SETUP_DATABASE = False


application = create_app(Config)

if __name__ == "__main__":
    application.run(debug=True)
