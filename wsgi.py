from karp.app import create_app
import os

user = os.environ["MARIADB_USER"]
passwd = os.environ["MARIADB_PASSWORD"]
dbhost = os.environ["MARIADB_HOST"]
dbname = os.environ["MARIADB_DATABASE"]

application = create_app({
    'SQLALCHEMY_DATABASE_URI': 'mysql://%s:%s@%s/%s' % (user, passwd, dbhost, dbname)
})

if __name__ == "__main__":
    application.run(debug=True)
