from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from api import views, models
from django.conf import settings
import debug_toolbar

router = DefaultRouter()
# router.register(r'datafiles', views.EntryViewSet)
router.register(r'ligandToImageData',
                views.LigandToImageDataViewSet, basename=models.LigandEntity)
router.register(r'topics', views.TopicViewSet)
router.register(r'topicStructures', views.StructureToTopicViewSet)
router.register(r'refinedModelSources', views.RefinedModelSourceViewSet)
router.register(r'refinedModelMethods', views.RefinedModelMethodViewSet)
router.register(r'refinedModels', views.RefinedModelViewSet)
router.register(r'sampleEntities', views.SampleEntitySet)
router.register(r'ligands', views.LigandEntityViewSet)
router.register(r'pdbligands', views.PdbLigandViewSet)


urlpatterns = [
    path('', include(router.urls)),

    # EM Validation annotations for 3DBionotes - Protvista
    re_path(r'^pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/?(?P<modified_model>(pdb-redo|isolde))?/$',
            views.PdbEntryAllAnnFromMapView.as_view()),

    # Validation annotations for FunPDBe
    re_path(r'^funpdbe/$', views.FunPDBeEntryListView.as_view()),
    re_path(r'^funpdbe/(?P<pdb_id>\d[a-zA-Z]\w{2})/$', views.FunPDBeEntryByPDBView.as_view()),
    re_path(r'^funpdbe/(?P<pdb_id>\d[a-zA-Z]\w{2})/(?P<method>(deepres|monores|blocres|mapq|fscq))/$',
            views.FunPDBeEntryByPDBMethodView.as_view()),

    # PDB Entry related end-points
    # get a list of all PDB entries in the DB
    re_path(r'^pdbentry/$', views.PdbEntryViewSet.as_view({'get': 'list'})),
    # get a PDB Entry by pdb_id
    re_path(r'^pdbentry/(?P<pk>\d[a-zA-Z]\w{2})/$', views.PdbEntryViewSet.as_view({'get': 'retrieve'})),
    re_path(r'^pdbentry/(?P<pdb_id>\d[a-zA-Z]\w{2})/ligands/$', views.LigandsSectionViewSet.as_view({'get': 'list'})),
    re_path(r'^pdbentry/(?P<pdb_id>\d[a-zA-Z]\w{2})/entities/$', views.EntitiesSectionViewSet.as_view({'get': 'list'})),

    # EM Validation annotations statistics
    re_path(r'^emv/$', views.EmvDataView.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/$', views.EmvDataByIDView.as_view()),


    re_path(r'^emv/(?P<method>(stats|deepres|monores|blocres|mapq|fscq|daq))/$', views.EmvDataByMethodView.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/(?P<method>(stats|deepres|monores|blocres|mapq|fscq|daq))/$', views.EmvDataByIdMethodView.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/consensus/$', views.EmvDataLocalresConsensus.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/rank/$', views.EmvDataLocalresRank.as_view()),

    # Ontology related end-points
    re_path(r'^ontologies/$', views.OntologyViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/(?P<pk>\w[a-zA-Z]*)/$', views.OntologyViewSet.as_view({'get': 'retrieve'})),
    re_path(r'^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/$', views.OntologyTermViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/(?P<term_id>\w[a-zA-Z]*_\d*)$', views.OntologyTermViewSet.as_view({'get': 'list'})),
]


if settings.DEBUG:
    urlpatterns += path('__debug__/', include(debug_toolbar.urls)),
    SHOW_TOOLBAR_CALLBACK = True
