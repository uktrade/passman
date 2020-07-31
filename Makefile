SHELL := /bin/bash


install-setup-deps:
	pip install pip-tools

make-virtualenv:
	virtualenv --python=python3 venv

compile-requirements:
	pip-compile -o requirements.txt requirements.in
	pip-compile -o requirements-dev.txt requirements-dev.in

install-requirements:
	pip-sync requirements-dev.txt

install-git-hooks:
	pre-commit install

create-env-file:
	@if [ ! -f ".env" ]; then \
	  cp sample_env .env; \
        else \
          echo ".env file already exists"; \
	fi

create-db:
	createdb -U postgres secrets
	
setup-project: install-setup-deps make-virtualenv activate-ve install-requirements create-env-file install-git-hooks create-db 

activate-ve:
	source venv/bin/activate

runserver:
	./manage.py migrate
	./manage.py runserver


.PHONY: install-setup-deps make-virtualenv compile-requirements install-requirements install-git-hooks create-env-file create-db setup-project activate-ve runserver
uONESHELL: create-env-file
