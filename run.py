import os
import sys
from gevent import monkey

monkey.patch_all()
from gevent.pywsgi import WSGIServer

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

from karp import create_app
from karp.config import MariaDBConfig


def usage():
    sys.exit(
        """Usage:
        {script} <port> - run in production mode on port <port>
        {script} dev    - run in development mode
        """.format(
            script=sys.argv[0]
        )
    )


USER = os.environ["MARIADB_USER"]
PASSWD = os.environ["MARIADB_PASSWORD"]
DBHOST = os.environ["MARIADB_HOST"]
DBNAME = os.environ["MARIADB_DATABASE"]

application = create_app(MariaDBConfig(USER, PASSWD, DBHOST, DBNAME, True))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
            WSGIServer(("0.0.0.0", PORT), application).serve_forever()
        except ValueError:
            if sys.argv[1].lower() == "dev":
                application.run(debug=True)
            else:
                usage()
    else:
        usage()

