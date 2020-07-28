# Passman

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

2. Run: `setup-local-env.sh`

Then you can either run the app with docker-compose:

    `docker-compose up`
    
Or without docker:

    `./manage.py runserver`

NOTES:

`setup-local-env.sh` assumes that postgres is accessible locally without a password; if this is not the case then you will need to create a database and ensure the correct connection string is set for `DATABASE_URL` in `.env`   
