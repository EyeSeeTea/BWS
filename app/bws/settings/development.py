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

DEBUG = True

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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "api/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch7_backend.Elasticsearch7SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
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
