.DEFAULT: test

UV = uv run
UV_EXISTS := $(shell command -v uv 2>/dev/null)

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
	@echo "reload"
	@echo "   restart web server gracefully"
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

.PHONY: ensure-uv
ensure-uv:
ifeq ($(UV_EXISTS),)
	ifeq (${VIRTUAL_ENV},)
		@echo "Set up either uv or a virtual environment to install with this Makefile. See README.md"
		@false
	else
		pip install uv
		export UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
	endif
else
	@:
endif

# Make it possible to exclude the sentence_transformers library by setting NO_SENTENCE_TRANSFORMERS
SENTENCE_TRANSFORMERS = $(if $(filter 1,$(NO_SENTENCE_TRANSFORMERS)),,--group sentence_transformers)

install: ensure-uv
	uv sync --no-dev --group prod $(SENTENCE_TRANSFORMERS)

dev: install-dev
install-dev: ensure-uv
	uv sync --group prod $(SENTENCE_TRANSFORMERS)

init-db:
	${UV} alembic upgrade head

build-parser: src/karp/search/domain/query_dsl/karp_query_parser.py src/karp/search/domain/query_dsl/karp_query_model.py

src/karp/search/domain/query_dsl/karp_query_parser.py: grammars/query.ebnf
	${UV} tatsu $< > $@

src/karp/search/domain/query_dsl/karp_query_model.py: grammars/query.ebnf
	${UV} tatsu --object-model $< > $@

run:
	mkdir run

.PHONY: serve serve-w-reload

PORT ?= 8000
NUM_WORKERS ?= 1

GUNICORN_BASE = $(UV) gunicorn 'karp.api.main:create_app()' --control-socket run/gunicorn.ctl --worker-class asgi --workers $(NUM_WORKERS) --bind 127.0.0.1:$(PORT) --pid run/gunicorn.pid

serve: install-dev run
	$(GUNICORN_BASE) --preload

serve-w-reload: install-dev run
	$(GUNICORN_BASE) --reload --graceful-timeout 1

.PHONY: reload
reload: run/gunicorn.ctl
	$(UV) gunicornc -s run/gunicorn.ctl -c "reload"

run/gunicorn.ctl:
	@echo "Cannot find gunicorn control socket, have you run make serve(-w-reload)?"
	@exit 1

unit_test_dirs := tests/unit
e2e_test_dirs := tests/e2e
all_test_dirs := tests

tests := ${unit_test_dirs}
all_tests := ${all_test_dirs}

.PHONY: test
test: unit-tests

.PHONY: all-tests
all-tests: clean-pyc type-check
	${UV} pytest -vv tests

.PHONY: unit-tests
unit-tests:
	${UV} pytest -vv tests/unit

.PHONY: e2e-tests
e2e-tests: clean-pyc
	${UV} pytest -vv tests/e2e

.PHONY: integration-tests
integration-tests: clean-pyc
	${UV} pytest -vv tests/integration

.PHONY: lint
lint:
	${UV} ruff check ${flags} .

.PHONY: lint-fix
lint-fix:
	${UV} ruff check ${flags} . --fix

.PHONY: fmt
fmt:
	${UV} ruff format .

.PHONY: type-check
type-check:
	${UV} basedpyright

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
