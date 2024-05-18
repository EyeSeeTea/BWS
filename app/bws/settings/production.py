"""
Django settings for emvWS project.

    *** PRODUCTION ONLY  SETTINGS ***
    Additional or overridden settings specific to the production environment.
    *** *** *** *** *** ***

"""

import os
from bws.settings import *

# ALLOWED_HOSTS = ["app", "*"]
DEBUG = False
PRODUCTION = True
SECRET_KEY = os.environ.get("SECRET_KEY")

# Fix probelms with DebugToolbarMiddleware when running in PROD
# Need to remove from general settings:
#   debug_toolbar.middleware.DebugToolbarMiddleware
#   debug_toolbar_force.middleware.ForceDebugToolbarMiddleware
# if DEBUG is False:
#     del MIDDLEWARE[11]
#     del MIDDLEWARE[10]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER_NAME"],
        "PASSWORD": os.environ["DB_USER_PASSWD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ["DB_PORT"],
    }
}


RUNNING_ENVIRONMENT = "DEV" if DEBUG else "PROD"

REST_FRAMEWORK = {
    "DEFAULT_VERSION": ""
    + API_VERSION_MAJOR
    + "."
    + API_VERSION_MINOR
    + "."
    + API_VERSION_PATCH
    + "-"
    + RUNNING_ENVIRONMENT,
    # Only JSON format responses
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "bws.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 100,
}


# If you're behind a proxy, use the X-Forwarded-Host header
# See https://docs.djangoproject.com/en/1.8/ref/settings/#use-x-forwarded-host
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
