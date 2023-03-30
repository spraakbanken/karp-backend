
ifeq (${VIRTUAL_ENV},)
  INVENV = poetry run
else
  INVENV =
endif

# setup development environment
dev: install-dev
install-dev:
	poetry install

# lint the code
.PHONY: lint
lint:
	${INVENV} ruff ${flags} src

# type-check the code
.PHONY: type-check
type-check:
	${INVENV} mypy --config-file mypy.ini -p karp

# run formatter
fmt:
	${INVENV} black .

# test if code is formatted
.PHONY: check-fmt
check-fmt:
	${INVENV} black . --check

# build the project
build:
	poetry build

part := "patch"
# bump given part of version
bumpversion:
	${INVENV} bump2version ${part}

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
