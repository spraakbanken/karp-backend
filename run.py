import os
import sys
from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer

from karp import create_app
from karp.config import MariaDBConfig

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

try:
    port = int(sys.argv[1])
except (IndexError, ValueError):
    sys.exit("Usage %s <port>" % sys.argv[0])

application = create_app(MariaDBConfig(user, passwd, dbhost, dbname, True))

WSGIServer(('0.0.0.0', port), application).serve_forever()

