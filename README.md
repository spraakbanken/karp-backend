<!-- @format -->

# Karp backend

This is the backend of Karp, SBX:s tool for managing lexical data and other 
structured data.

The basic structure in Karp is a resource, which is a collection of entries.
Each resource may  be configured according to the format of the data and other needs.

The backend consists of two parts. The command-line interface (CLI), used to 
manage resources and the web API for modifying and querying the data.

There is also a frontend, contact SBX for more information.

## Installation

Follow the steps in [getting started](#getting-started).

## CLI

Use the CLI to create or modify resources, publish resources and do bulk editing.
To view the CLI documentation, use:

`(uv run) karp-cli --help`

The resource configuration is documented [here](docs/resource-config.md).

There is also a tutorial describing [creation of a resource](docs/add-resource.md).

## Web API

The API documentation for the current version is available [here](https://ws.spraakbanken.gu.se/docs/karp).

### Editing

Using the API (with credentials) one can:
- add an entry to a resource
- modify existing entries
- delete an entry from a resource (discard, actual data is retained) 

All edits are stored, along with time and the editor. The history of an entry is
also available through the API.

### Searching

Searching is done with our [custom query language](https://ws.spraakbanken.gu.se/docs/karp#tag/Searching).

Searching supports sorting and pagination.

## Versions

This is the version 7 of Karp backend, [for the legacy version (v5)](https://github.com/spraakbanken/karp-backend-v5).

## Dependencies

We use [MariaDB](https://mariadb.org/) for storage and [Elasticsearch][es-download] for search.

## Development

This project uses [uv](https://docs.astral.sh/uv/).

A Makefile is provided to simplify tasks. 

If `uv` is pre-installed, `make` will assume that everything is setup as the user wants and just invoke `uv`.

If `uv` is *not* pre-installed, but the user has activated a virtualenv, `make`-invokations will:
- install `uv`
- if env. variable `UV_PROJECT_ENVIRONMENT` is not set, will be set to `$VIRTUAL_ENV`
And then proceed as normally.

If neither `uv` is available or a virtual environment activated, the user must set up either manually to be able to use `make`.

### Getting started

1. First clone this repo: `git clone` or `gh repo clone` (if using github-cli).

2. Either create and activate a virtual environment or rely on a globally installed uv. Then install dependencies:

  `make dev` (or `make install-dev`)

3. Install MariaDB and create a database

4. Setup environment variables (can be placed in a `.env` file in the root):
   ```
   export DB_DATABASE=<name of database>
   export DB_USER=<database user>
   export DB_PASSWORD=<user's password>
   export DB_HOST=localhost
   export AUTH_JWT_PUBKEY_PATH=/path/to/pubkey (only neded to support SB AUTH JWT in header)
   ```
5. Run `(uv run) karp-cli db up` to initialize database
6. Run `make serve` or `make serve-w-reload` or other method using the function `karp.api.main:create_app`.

7. To setup Elasticsearch, [download][es-download] Elasticsearch 8.x and run the
   following commands from the `elasticsearch-8.XXX` directory:
   ```
   bin/elasticsearch-plugin install analysis-icu
   ```
   Then run `bin/elasticsearch -Expack.security.enabled=false` to start it.
8. Add environment variables

```
export ELASTICSEARCH_HOST=http://localhost:9200
```

## Web server

The default web server, used in Makefile, is Gunicorn. It is started with the flag `--preload`.
This flag causes the master process to create the app before forking workers. This gives faster
reload times, but makes it so that the master must be restarted more often, for example on code changes.
It is especially important when using memory intensive resources, such as a language model (currently
only done in plugins).

The reason we want fast reload times is that the workers must be reloaded on every
`reindex` and `publish` to clear caches.

## Create test resources

1. `(uv run) karp-cli resource create assets/testing/config/places.yaml`
2. `(uv run) karp-cli entries add places assets/testing/data/places.jsonl`
3. Do the same for `municipalities`
4. `(uv run) karp-cli resource publish places 1`
5. `(uv run) karp-cli resource publish municipalities 1`

## Technologies

### Python

- Python
- FastAPI
- SQLAlchemy
- Typer
- Elasticsearch
- Elasticsearch DSL

### Databases

- MariaDB
- Elasticsearch

### Type checking

Run type checking with `make type-check` or just `basedpyright`.

We use [basedpyright](https://docs.basedpyright.com/), but [Pyright](https://microsoft.github.io/pyright/) should work.

Currently actual type checking is only done on selected files, but basedpyright provides "syntax and sematic errors" for all files.

### Testing

The tests are organized in unit, integration and end-to-end tests.

#### Unit tests

These test should have no infrastructure dependencies and should run fast.

Run them by: `make test` (or `make unit-tests`)

#### Integration tests

These test have some infrastructure dependencies and should run slower.

Run them by: `make integration-tests`

#### End-to-end tests

These test have all infrastructure dependencies and should run slowest.

Run them by: `make e2e-tests`

#### All tests

These test have all infrastructure dependencies and should run slowest. They 
also start with a type checking pass.

Run them by: `make all-tests`

### Linting and formatting

Linting and formatting is done by [`ruff`](https://beta.ruff.rs/docs/). Settings are in `ruff.toml`.

Run linter with `make lint`.

Run formatter with `make fmt`.

### Version handling

Update version in the following files:
- [`pyproj.toml`](pyproject.toml)
- [`karp.main.config`](src/karp/main/config.py)

[es-download]: https://www.elastic.co/downloads/elasticsearch
