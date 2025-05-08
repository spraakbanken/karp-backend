# Installation

Karp uses MariaDB for storage of data and Elasticsearch for searching. The generated Elasticserch
indices are transient and may be genererad from scratch if needed.

Running the Karp backend or CLI requires Python.

Follow the instructions in the backend's [README.md](https://github.com/spraakbanken/karp-backend) for a basic install.

### Production

Typically one will have a setup where the backend instance is kept alive using a process control system
such as Supervisor or system. Use this command to start:

`uvicorn --port 9093 --factory karp.api.main:create_app --workers 4`

`uvicorn` shoudl be available in the venv's bin-directory.

`--workers` is used two spawn multiple processes of the backend, which will speed up requests if there is a higher
load. Read Uvicorn's documentation to learn more, but a rule of thumb is to not spawn more processes than the number
of cores on the production machine.

If the application is running on a specific path, add the path using: `--root-path /karp/v7`

The application starts on localhost on HTTP and is not available from outside the machine. Setup your webserver to
forward to `localhost:9093` or consult Uvicorns documentation for more advanced setups.

## About the CLI

The CLI and backend lives in the same codebase and it can be a good idea to use the same venv when
running the CLI, as when running the backend, since there will be fewer essors due to dependency mismatches.
