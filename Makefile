.DEFAULT: test

PLATFORM := ${shell uname -o}


ifeq (${VIRTUAL_ENV},)
  INVENV = poetry run
else
  INVENV =
endif

${info Platform: ${PLATFORM}}


.PHONY: help
help:
	@echo "usage:"
	@echo ""
	@echo "install"
	@echo "   setup production environment"
	@echo ""
	@echo "dev | install-dev"
	@echo "   setup development environment"
	@echo ""
	@echo "all-tests"
	@echo "   run all tests"
	@echo ""
	@echo "lint"
	@echo "   lint the code"
	@echo ""
	@echo "type-check"
	@echo "   check types"
	@echo ""
	@echo "fmt"
	@echo "   run formatter on all code"

install:
	poetry install --only=main

dev: install-dev
install-dev:
	poetry install

init-db:
	${INVENV} alembic upgrade head

build-parser: karp/search/domain/query_dsl/karp_query_v6_parser.py karp/search/domain/query_dsl/karp_query_v6_model.py

karp/search/domain/query_dsl/karp_query_v6_parser.py: grammars/query_v6.ebnf
	${INVENV} tatsu $< > $@

karp/search/domain/query_dsl/karp_query_v6_model.py: grammars/query_v6.ebnf
	${INVENV} tatsu --object-model $< > $@

.PHONY: serve
serve: install-dev
	${INVENV} uvicorn --factory karp.api.main:create_app

.PHONY: serve-w-reload
serve-w-reload: install-dev
	${INVENV} uvicorn --reload --factory karp.api.main:create_app

unit_test_dirs := tests/unit
e2e_test_dirs := tests/e2e
all_test_dirs := tests

tests := ${unit_test_dirs}
all_tests := ${all_test_dirs}

.PHONY: test
test: unit-tests

.PHONY: all-tests
all-tests: clean-pyc
	${INVENV} pytest -vv tests

.PHONY: unit-tests
unit-tests:
	${INVENV} pytest -vv tests/unit

.PHONY: e2e-tests
e2e-tests: clean-pyc
	${INVENV} pytest -vv tests/e2e

.PHONY: integration-tests
integration-tests: clean-pyc
	${INVENV} pytest -vv tests/integration

.PHONY: lint
lint:
	${INVENV} ruff check ${flags} karp

.PHONY: lint-fix
lint-fix:
	${INVENV} ruff check ${flags} karp --fix

.PHONY: fmt
fmt:
	${INVENV} ruff format .

.PHONY: type-check
type-check:
	${INVENV} mypy --config-file mypy.ini -p karp


.PHONY: clean clean-pyc
clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
