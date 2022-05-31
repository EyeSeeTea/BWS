from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'datafiles', views.EntryViewSet)
router.register(r'LigandToImageData', views.LigandEntityViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # EM Validation annotations for 3DBionotes - Protvista 
    re_path(r'^pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/?(?P<modified_model>(pdb-redo|isolde))?/$', views.PdbEntryAllAnnFromMapView.as_view()),
]
