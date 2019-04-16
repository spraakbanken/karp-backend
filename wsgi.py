import os

from karp import create_app
from karp.config import MariaDBConfig

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

application = create_app(MariaDBConfig(user, passwd, dbhost, dbname, True))

if __name__ == "__main__":
    application.run(debug=True)

