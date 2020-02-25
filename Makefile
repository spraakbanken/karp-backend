.PHONY: test test-log pytest build-dev run-tests clean clean-pyc help lint lint-syntax-errors
.DEFAULT: test

PYTHON = python3
PLATFORM := ${shell uname -o}

ifeq (${VIRTUAL_ENV},)
  VENV_NAME = .venv
else
  VENV_NAME = ${VIRTUAL_ENV}
endif
${info Using ${VENV_NAME}}

VENV_BIN = ${VENV_NAME}/bin

ifeq (${VIRTUAL_ENV},)
  VENV_ACTIVATE = . ${VENV_BIN}/activate
else
  VENV_ACTIVATE = true
endif

ifeq (${PLATFORM}, Android)
  FLAKE8_FLAGS = --jobs=1
else
  FLAKE8_FLAGS = --jobs=auto
endif

help:
	echo "Available commands:"

venv: ${VENV_NAME}/venv.created

install: venv ${VENV_NAME}/req.installed
install-dev: venv ${VENV_NAME}/req-dev.installed

${VENV_NAME}/venv.created:
	@python3 -c "import sys; assert sys.version_info >= (3, 6)" || echo "Python >= 3.6 is needed"
	test -d ${VENV_NAME} || python3 -m venv ${VENV_NAME}
	${VENV_ACTIVATE}; pip install pip-tools
	@touch $@

${VENV_NAME}/req.installed: deploy/requirements.txt
	${VENV_ACTIVATE}; pip install -Ur $<
	@touch $@

${VENV_NAME}/req-dev.installed: setup.py setup.cfg tools/pip-requires
	${VENV_ACTIVATE}; pip install -e .[dev]
	@touch $@

init-db:
	${VENV_ACTIVATE}; alembic upgrade head

run: install
	${VENV_ACTIVATE}; python run.py 8081

run-dev: install-dev
	${VENV_ACTIVATE}; python wsgi.py

lint-syntax-errors: install-dev
	${VENV_ACTIVATE}; flake8 karp tests setup.py run.py cli.py --count --select=E9,F63,F7,F82 --show-source --statistics ${FLAKE8_FLAGS}

test: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest -vv tests

test-w-coverage: install-dev clean-pyc
	${VENV_ACTIVATE}; pytest -vv --cov-config=setup.cfg --cov=karp --cov-report=term-missing tests

test-log: install-dev clean-pyc lint-syntax-errors
	${VENV_ACTIVATE}; pytest -vv --cov-config=setup.cfg --cov=karp --cov-report=term-missing tests > pytest.log

prepare-release: venv setup.py
	${VENV_ACTIVATE}; pip-compile --output-file=deploy/requirements.txt setup.py

bump-version-patch:
	bumpversion patch
	make prepare-release

bump-version-minor:
	bumpversion minor
	make prepare-release

bump-version-major:
	bumpversion major
	make prepare-release

run-tests: lint type-check test

tox:
	tox

tox-to-log:
	tox > tox.log

lint: install-dev
	${VENV_ACTIVATE}; pylint --rcfile=.pylintrc --load-plugins "pylint_flask" src tests setup.py run.py wsgi.py

type-check:
	pyre check

docs/openapi.html: doc/karp_api_spec.yaml
	@echo "Skipping 'redoc-cli bundle --output $@ $<'"
	touch $@

bumpversion-patch:
	bumpversion patch

bumpversion-minor:
	bumpversion minor

bumpversion-major:
	bumpversion major

mkrelease-patch: bumpversion-patch prepare-release docs/openapi.html
mkrelease-minor: bumpversion-minor prepare-release docs/openapi.html
mkrelease-major: bumpversion-major prepare-release docs/openapi.html

clean: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
