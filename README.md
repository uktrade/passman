# Passman

[![uktrade](https://circleci.com/gh/uktrade/passman.svg?style=svg)](https://app.circleci.com/pipelines/github/uktrade/passman) [![codecov](https://codecov.io/gh/uktrade/passman/branch/master/graph/badge.svg)](https://codecov.io/gh/uktrade/passman)

Passman is a simple hosted password manager built to replace Rattic (https://github.com/tildaslash/RatticWeb).

The application should be hosted in a secure environment, preferably behind a VPN, using an encrypted database and end-to-end encryption.

# Key features

- Allows the creation of passwords/secure details which can then be assigned to users and groups
- It is integrated with DIT's staff-sso app 
- An additional 2FA check is required to view secrets
- Passwords are encrypted using https://github.com/georgemarshall/django-cryptography
- detailed auditing

# Dependencies 

- Python 3.8+ 
- Postgres 10
- Zbar
- Staff-sso [this a DIT specific component]

# Set-up local environment

1. Clone the repository 

2. Run: `make setup-project`
  This will:
  - create and activate a virtualenv
  - install pip-tools
  - install dependencies
  - install a github precommit hook
  - create a new .env file
  - create a database (this requires a local postgres instance) 

3. Put relevant settings into your .env file. Specifically the `AUTHBROKER_*` env vars will need some settings. Speak to webops.

4. Apply django migrations and run the server - here's a shortcut: `make runserver` 

# Set-up local environment /w Poetry

1. Clone the repository 

2. Install poetry, via `pip install -U pip poetry`

3. Install the dependencies:

    ```
    poetry env use <python install>
    poetry install --with dev
    poetry shell
    ```

#. For MacOS users, `pyzbar` package will required `brew install zbar` and then add DYLD_LIBRARY_PATH added to your `~/.bash_profile`/`~/.zshrc`:
    `export DYLD_LIBRARY_PATH=$(brew --prefix zbar)/lib:$DYLD_LIBRARY_PATH`

If that does not work: 
  ```
  $ mkdir ~/lib
  $ ln -s $(brew --prefix zbar)/lib/libzbar.dylib ~/lib/libzbar.dylib
  ```

4. Create an ``.env`` file (it’s gitignored by default):
    cp sample.env .env

    Authobroker variable values are available in staff-sso admin, Oauth providers search for Passman

5. Create the db:

    ```
    psql -p5432
    create database passman;
    ```

6. Run `poetry shell` to activate local shell, then run: 
  ./manage.py migrate

7. To create a superuser, enter ``./manage.py shell`` and execute the following:

    ```
    from user.models import User
    u = User()
    u.email = "first.name-00000000@id.trade.gov.uk" #You will need to use your email_user_id email here.
    u.first_name = ""
    u.last_name = ""
    u.is_active=True
    u.is_staff=True
    u.is_superuser=True
    u.set_password("letmein")
    u.save()
    ```

8. Start the passman localhost server, run: 
	./manage.py runserver
