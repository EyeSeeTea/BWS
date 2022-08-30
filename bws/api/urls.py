from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from api import views, models
from django.conf import settings
import debug_toolbar

router = DefaultRouter()
router.register(r'datafiles', views.EntryViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # EM Validation annotations for 3DBionotes - Protvista 
    re_path(r'^pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/?(?P<modified_model>(pdb-redo|isolde))?/$', views.PdbEntryAllAnnFromMapView.as_view()),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += path('__debug__/', include(debug_toolbar.urls)),
    SHOW_TOOLBAR_CALLBACK = True