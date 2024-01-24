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

    Authobroker variable values are available in staff-sso admin, Oauth providers search for Passman:
      AUTHBROKER_URL
      AUTHBROKER_CLIENT_ID
      AUTHBROKER_CLIENT_SECRET

5. Create the db:

    ```
    psql -p5432
    create database passman;
    ```

#. If running pytest locally is required, you will need to create a 'postgres' superuser within passman database if it does not already exist:

    CREATE USER postgres SUPERUSER;

6. Run `poetry shell` to activate local shell, then to populate passman database run: 
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



# Deploy to Staging

1. Push local branch changes to PR in GitHub, this will automatically trigger a Docker image to be built here: 

    https://console.cloud.google.com/gcr/images/sre-docker-registry/global/github.com/uktrade/passman?project=sre-docker-registry

2. Setup Pritunl staging VPN:
    - Go to Passman (Prod) and search for vpn.staging-ci.uktrade.digital.
    - Navigate to https://vpn.staging-ci.uktrade.digital/
    - Use the username & password given in Passman
    - In Pritunl admin page, go to Users tab and 'Add User'
    - Give name as: firstname.lastname
    - Give your @digital.trade.gov.uk as email, then click Save
    - Find your new user in the list, on the right hit the 'Click to download profile' button
    - Open Pritunl app, import downloaded profile
    - Connect to both prod/staging VPN at the same time

3. Configure AWS command line session
    - Go to AWS account list, click on 'dev' and click 'Command line or programmatic access'
    - Follow the steps in the 'Get credentials' popup window
    - Select 'dev' from the available AWS accounts list in command line

4. Update K8s config using kubectl: 

    `aws eks update-kubeconfig --name staging-ci-uktrade-digital --region eu-west-2 --profile <Use the profile given in step 2 here>`

5. Checks K8S pods to see if passman-staging is running: 

    `kubectl get pods -n tools`

6. Clone eks-services repo from Gitlab: https://gitlab.ci.uktrade.digital/webops/eks-services

7. Edit passman-stg.yaml file to use your branch's Docker image
    - Edit config/passman-stg.yaml
    - Go to image and change tag to you branch's image tag: 

```
      containers:
        - name: passman
          image: gcr.io/sre-docker-registry/github.com/uktrade/passman:latest
```
    
  to 

```
      containers:
        - name: passman
          image: gcr.io/sre-docker-registry/github.com/uktrade/passman:<branch_name>
```  

8. In the EKS repo terminal, apply changes using kubectl:

    `kubectl apply -f <path_to_file>/passman-stg.yaml`

    Note: May need to do: 

    `kubectl config set-context --current --namespace=tools`


