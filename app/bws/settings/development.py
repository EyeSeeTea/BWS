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


# Application definition
INSTALLED_APPS += [
    "debug_toolbar",
]

CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # debug_toolbar_force enable to show debug_toolbar in non- or partial-HTML views (APIs)
    "debug_toolbar_force.middleware.ForceDebugToolbarMiddleware",
]

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
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
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "bws.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 100,
}


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}
