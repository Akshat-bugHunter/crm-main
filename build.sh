#!/usr/bin/env bash

set -o errexit

cd crm-main

pip install -r requirements.txt

python manage.py collectstatic --noinput

python manage.py migrate
