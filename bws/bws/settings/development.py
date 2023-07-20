"""
Django settings for BWS project.

    *** DEVELOPMENT ONLY  SETTINGS ***
    Additional or overridden settings specific to the development environment.
    *** *** *** *** *** ***

"""

import os
from bws.settings import *
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'SECRET_KEY'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': os.environ['DB_NAME'],
#         'USER': os.environ['DB_USER_NAME'],
#         'PASSWORD': os.environ['DB_USER_PASSWD'],
#         'HOST': os.environ['DB_HOST'],
#         'PORT': os.environ['DB_PORT'],
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}