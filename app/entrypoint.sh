#!/bin/bash

echo 'Starting http server'
python manage.py makemigrations api && # Probably necessary to also add annotations also to makemigrations (as new line)
python manage.py migrate &&
python manage.py rebuild_index --noinput &&
uwsgi --module bws.wsgi:application --http :8000 --master --enable-threads