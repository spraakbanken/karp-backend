default: tox

pytest: build
	pipenv run py.test tests

tox:
	tox

build:
	pipenv install

flaske8:
	flake8 src tests setup.py wsgi.py
