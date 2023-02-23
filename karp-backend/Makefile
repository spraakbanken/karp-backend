
ifeq (${VIRTUAL_ENV},)
  INVENV = poetry run
else
  INVENV =
endif

# setup development environment
dev: install-dev
install-dev:
	poetry install

# setup CI environment
install-ci: install-dev
	poetry install --only ci

default_cov := "--cov=src/karp"
cov_report := "term-missing"
cov := ${default_cov}

all_tests := src/karp/tests
tests := src/karp/tests/unit

# run tests with code coverage
.PHONY: test-w-coverage
test-w-coverage: clean-pyc
	${INVENV} pytest -vv ${cov} --cov-report=${cov_report} ${all_tests}

# run given test(s)
.PHONY: test
test:
	${INVENV} pytest -vv ${tests}

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
