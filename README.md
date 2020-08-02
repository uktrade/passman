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

