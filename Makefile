.PHONY: test test-log pytest build-dev run-tests clean clean-pyc help lint lint-syntax-errors
.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}
INVENV_PATH = ${shell which invenv}



ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
  ${info invenv: ${INVENV_PATH}}
  ifeq (${INVENV_PATH},)
    INVENV = export VIRTUAL_ENV="${VENV_NAME}"; export PATH="${VENV_BIN}:${PATH}"; unset PYTHON_HOME;
  else
    INVENV = invenv -C ${VENV_NAME}
  endif
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

venv: ${VENV_NAME}/venv.created

install: venv ${VENV_NAME}/req.installed
install-dev: venv ${VENV_NAME}/req-dev.installed

${VENV_NAME}/venv.created:
	@python3 -c "import sys; assert sys.version_info >= (3, 6)" || echo "Python >= 3.6 is needed"
	test -d ${VENV_NAME} || python3 -m venv ${VENV_NAME}
	${INVENV} pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: deploy/requirements.txt
	${INVENV} pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py setup.cfg tools/pip-requires
	${INVENV} pip install -e .[dev]
	@touch $@

init-db:
	${INVENV} alembic upgrade head

run: install
	${INVENV} python run.py 8081

run-dev: install-dev
	${INVENV} python wsgi.py

lint-syntax-errors: install-dev
	${INVENV} flake8 karp tests setup.py run.py --count --select=E9,F63,F7,F82 --show-source --statistics ${FLAKE8_FLAGS}

test: install-dev clean-pyc
	${INVENV} pytest -vv tests/unit_tests

test-w-coverage: install-dev clean-pyc
	${INVENV} pytest -vv --cov-config=setup.cfg --cov=karp --cov-report=term-missing tests

test-log: install-dev clean-pyc lint-syntax-errors
	${INVENV} pytest -vv --cov-config=setup.cfg --cov=karp --cov-report=term-missing tests > pytest.log

prepare-release: venv setup.py tools/pip-requires setup.cfg
	${INVENV} pip-compile --output-file=deploy/requirements.txt setup.py

run-tests: lint type-check test

tox:
	tox

tox-to-log:
	tox > tox.log

lint: install-dev
	${INVENV} pylint --rcfile=.pylintrc --load-plugins "pylint_flask" karp tests setup.py run.py wsgi.py

lint-no-fail: install-dev
	${INVENV} pylint --rcfile=.pylintrc --load-plugins "pylint_flask" --exit-zero karp tests setup.py run.py wsgi.py

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
