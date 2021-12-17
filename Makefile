.PHONY: test test-log pytest build-dev run-tests clean clean-pyc help lint lint-syntax-errors run-all-tests-w-coverage run-unit-tests run-unit-tests-w-coverage run-integration-tests run-integration-tests-w-coverage run-all-tests run-all-tests-w-coverage
.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}
# INVENV_PATH = ${shell which invenv}



ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
  INVENV = poetry run
#   ${info invenv: ${INVENV_PATH}}
#   ifeq (${INVENV_PATH},)
#     INVENV = export VIRTUAL_ENV="${VENV_NAME}"; export PATH="${VENV_BIN}:${PATH}"; unset PYTHON_HOME;
#   else
#     INVENV = invenv -C ${VENV_NAME}
#   endif
else
  VENV_NAME = ${VIRTUAL_ENV}
  INVENV =
endif

${info Platform: ${PLATFORM}}
${info Using virtual environment: ${VENV_NAME}}

VENV_BIN = ${VENV_NAME}/bin



ifeq (${PLATFORM}, Android)
  FLAKE8_FLAGS = --jobs=1
else
  FLAKE8_FLAGS = --jobs=auto
endif

help:
	@echo "Available commands:"

install:
	poetry install --no-dev

dev: install-dev
install-dev: karp/search/domain/query_dsl/karp_query_v6_parser.py karp/search/domain/query_dsl/karp_query_v6_model.py
	poetry install

install-mysql:
	poetry install -E mysql --no-dev

install-dev-mysql:
	poetry install -E mysql

install-elasticsearch6:
	poetry install --no-dev -E elasticsearch6

install-elasticsearch7:
	poetry install --no-dev -E elasticsearch7

init-db:
	${INVENV} alembic upgrade head

karp/search/domain/query_dsl/karp_query_v6_parser.py: grammars/query_v6.ebnf
	${INVENV} tatsu $< > $@

karp/search/domain/query_dsl/karp_query_v6_model.py: grammars/query_v6.ebnf
	${INVENV} tatsu --object-model $< > $@

run: install
	${INVENV} python run.py 8081

.PHONY: serve
serve: install-dev
	${INVENV} uvicorn asgi:app

.PHONY: serve-w-reload
serve-w-reload: install-dev
	${INVENV} uvicorn --reload asgi:app

lint-syntax-errors: install-dev
	${INVENV} flake8 karp karp/tests setup.py run.py --count --select=E9,F63,F7,F82 --show-source --statistics ${FLAKE8_FLAGS}

check-security-issues: install-dev
	${INVENV} bandit -r -ll karp

test: unit-tests
run-all-tests: unit-tests run-integration-tests
run-all-tests-w-coverage: run-unit-tests-w-coverage run-integration-tests-w-coverage run-e2e-tests-w-coverage

.PHONY: unit-tests
unit-tests:
	${INVENV} pytest -vv karp/tests/unit

.PHONY: e2e-tests
e2e-tests:
	${INVENV} pytest -vv karp/tests/e2e

.PHONY: run-e2e-tests-w-coverage
run-e2e-tests-w-coverage: install-dev clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=term-missing karp/tests/e2e

.PHONY: integration-tests
integration-tests: install-dev clean-pyc
	${INVENV} pytest -vv karp/tests/integration

run-slow-tests: install-dev clean-pyc
	${INVENV} pytest -vv karp/tests/quick_tests karp/tests/slow_tests

run-unit-tests-w-coverage: install-dev clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=term-missing karp/tests/unit

run-integration-tests: install-dev clean-pyc
	${INVENV} pytest -vv karp/tests/integration

run-integration-tests-w-coverage: install-dev clean-pyc
	${INVENV} pytest -vv --cov=karp --cov-report=term-missing karp/tests/integration

test-log: install-dev clean-pyc lint-syntax-errors
	${INVENV} pytest -vv --cov=karp --cov-report=term-missing karp/tests > pytest.log

prepare-release: venv setup.py requirements.txt setup.cfg
	${INVENV} pip-compile --output-file=deploy/requirements.txt setup.py

tox:
	tox

tox-to-log:
	tox > tox.log

lint: install-dev
	${INVENV} pylint --rcfile=pylintrc karp karp/tests setup.py run.py wsgi.py

lint-no-fail: install-dev
	${INVENV} pylint --rcfile=pylintrc --exit-zero karp karp/tests setup.py run.py wsgi.py

check-pylint: install-dev
	${INVENV} pylint --rcfile=pylintrc  karp

check-mypy: install-dev
	${INVENV} mypy karp wsgi.py run.py

check-pylint-refactorings: install-dev
	${INVENV} pylint --disable=C,W,E --enable=R karp

type-check:
	pyre check

docs/openapi.html: doc/karp_api_spec.yaml
	@echo "Skipping 'redoc-cli bundle --output $@ $<'"
	touch $@

bumpversion-patch: install-dev
	${INVENV} bump2version patch

bumpversion-minor: install-dev
	${INVENV} bump2version minor

bumpversion-major: install-dev
	${INVENV} bump2version major

mkrelease-patch: bumpversion-patch prepare-release docs/openapi.html
mkrelease-minor: bumpversion-minor prepare-release docs/openapi.html
mkrelease-major: bumpversion-major prepare-release docs/openapi.html

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
