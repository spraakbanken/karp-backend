# Karp TNG backend

This in the next version of Karp backend

## Setup

This project uses [pipenv](https://pipenv.readthedocs.io/) and
[MariaDB](https://mariadb.org/).

1. Install pipenv
2. Run `pipenv install --dev` (skip --dev if deploying)
3. Install MariaDB and create a database
4. Setup environment variables:
   ```
   export MARIADB_DATABASE=<name of database>
   export MARIADB_USER=<database user>
   export MARIADB_PASSWORD=<usser's password>
   export MARIADB_HOST=localhost
   ```
5. Run `pipenv run python wsgi.py` to start development server

    or `pipenv shell` when `python wsgi.py`


The database setup is done automatically when running `wsgi.py`.

## Technologies

### Python

- Pipenv
- Flask
- SQLAlchemy
- Click
- Elasticsearch
- Elasticsearch DSL

### Databases

- MariaDB
- Elasticsearch

