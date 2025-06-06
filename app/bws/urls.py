"""
    bws URL Configuration
"""
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from bws.settings import *

if DEBUG:
    from bws.settings.development import REST_FRAMEWORK
else:
    from bws.settings.production import REST_FRAMEWORK


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()


schema_view = get_schema_view(
    openapi.Info(
        title="3DBionotes-WS API",
        default_version=REST_FRAMEWORK["DEFAULT_VERSION"],
        description="API documentation for the Bionotes Structural HUB WebServices",
        contact=openapi.Contact(email="3dbionotes@cnb.csic.es"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Swagger documentation
    re_path(
        r"^api/swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^api/swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    # ReDoc documentation
    path("api/redoc/",
         schema_view.with_ui("redoc", cache_timeout=0),
         name="schema-redoc"),
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls",
                              namespace="rest_framework")),
    path("admin/", admin.site.urls),
    path("", include(router.urls)),
]
