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
   export MARIADB_PASSWORD=<user's password>
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

## Development

### Version handling

Version can be bumped with [`bumpversion`](https://pypi.org/project/bumpversion/).

Usage:
- Increase patch number `a.b.X => a.b.(X+1)`: `bumpversion patch`
- Increase minor number `a.X.c => a.(X+1).c`: `bumpversion minor`
- Increase major number `X.b.c => (X+1).b.c`: `bumpversion major`
- To custom version `a.b.c => X.Y.Z`: `bumpversion --new-version X.Y.Z`

`bumpversion` is configured in [`.bumpversion.cfg`](.bumpversion.cfg).

The version is changed in the following files:
- [`setup.py`](setup.py)
- [`src/karp/__init__.py`](src/karp/__init__.py)
- [`.bumpversion.cfg`](.bumpversion.cfg)
- [`doc/karp_api_spec.yaml`](doc/karp_api_spec.yaml)
