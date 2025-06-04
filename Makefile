.DEFAULT: test

ifeq (${VIRTUAL_ENV},)
  INVENV = poetry run
else
  INVENV =
endif

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
	@echo "serve | serve-w-reload"
	@echo "   start web server"
	@echo ""
	@echo "lint"
	@echo "   lint the code"
	@echo ""
	@echo "type-check"
	@echo "   check types"
	@echo ""
	@echo "fmt"
	@echo "   run formatter on all code"
	@echo ""
	@echo "tags"
	@echo "   generate tags file"

install:
	poetry install --only=main

dev: install-dev
install-dev:
	poetry install

init-db:
	${INVENV} alembic upgrade head

build-parser: karp/search/domain/query_dsl/karp_query_parser.py karp/search/domain/query_dsl/karp_query_model.py

karp/search/domain/query_dsl/karp_query_parser.py: grammars/query.ebnf
	${INVENV} tatsu $< > $@

karp/search/domain/query_dsl/karp_query_model.py: grammars/query.ebnf
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
all-tests: clean-pyc type-check
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
	${INVENV} ruff check ${flags} .

.PHONY: lint-fix
lint-fix:
	${INVENV} ruff check ${flags} . --fix

.PHONY: fmt
fmt:
	${INVENV} ruff format .

.PHONY: type-check
type-check:
	${INENV} basedpyright

.PHONY: tags
tags:
	ctags --languages=python -R --python-kinds=-i karp
	ctags --languages=python -R --python-kinds=-i -e karp

.PHONY: clean clean-pyc
clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
