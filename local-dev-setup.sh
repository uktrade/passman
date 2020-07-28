#!/usr/bin/env bash

# initial local dev setup
#
# 1. set up and activate a virtualenv
# 2. install pip-tools and the current dev requirements
# 3. create a postgres DB 

if [ ! -f '.env']; then
    cp sample_env .env
fi

echo "edit .env and add required credentials"

virtualenv --python=python3 venv
source venv/bin/activate
pip install pip-tools

pip-sync requirements-dev.txt

# this will only work if postgres is installed locally and allows passwordless access 
createdb secrets

echo 'done.'
