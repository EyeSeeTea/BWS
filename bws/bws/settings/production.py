"""
Django settings for emvWS project.

    *** PRODUCTION ONLY  SETTINGS ***
    Additional or overridden settings specific to the production environment.
    *** *** *** *** *** ***

"""

import os
from bws.settings import *

ALLOWED_HOSTS = ['app']
DEBUG = False
PRODUCTION = True
SECRET_KEY = os.environ.get('SECRET_KEY')

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER_NAME'],
        'PASSWORD': os.environ['DB_USER_PASSWD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

REST_FRAMEWORK = {
    # un-commnet for JSON format responses
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer', ],
}

# If you're behind a proxy, use the X-Forwarded-Host header
# See https://docs.djangoproject.com/en/1.8/ref/settings/#use-x-forwarded-host
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
