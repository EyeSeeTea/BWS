from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from api import views, models
from django.conf import settings
import debug_toolbar

router = DefaultRouter()
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

    # Get version
    re_path(r'^version/$', views.GetApiVersion.as_view()),

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

    # DAQ scores
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/$', views.EmvDataByIdDaqView.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<fileformat>(json|pdb))/$', views.EmvDataByIdDaqView.as_view()),
    # TODO: add end-point for getting different versions
    # re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<version>)/$', views.EmvDataByIdDaqView.as_view()),
    # re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<version>)/(?P<fileformat>(json|pdb))/$', views.EmvDataByIdDaqView.as_view()),

    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/(?P<method>(stats|deepres|monores|blocres|mapq|fscq))/(?P<fileformat>(json|pdb|mmcif))/$', views.EmvSourceDataByIdMethodView.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/(?P<method>(stats|deepres|monores|blocres|mapq|fscq))/$', views.EmvDataByIdMethodView.as_view()),
    # Average Q-score and estimated resolution
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/mapq/averages/$', views.EmvMapQDataAveragesView.as_view()),

    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/consensus/$', views.EmvDataLocalresConsensus.as_view()),
    re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/rank/$', views.EmvDataLocalresRank.as_view()),

    # Ontology related endpoints
    re_path(r'^ontologies/$', views.OntologyViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/terms/$', views.AllOntologyTermViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/terms/(?P<term_id>\w[a-zA-Z]*_\d*)/$', views.AllOntologyTermViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/(?P<pk>\w[a-zA-Z]*)/$', views.OntologyViewSet.as_view({'get': 'retrieve'})),
    re_path(r'^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/$', views.OntologyTermViewSet.as_view({'get': 'list'})),
    re_path(r'^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/(?P<term_id>\w[a-zA-Z]*_\d*)$', views.OntologyTermViewSet.as_view({'get': 'list'})),

    # Organisms related endpoint
    re_path(r'^organisms/$', views.OrganismViewSet.as_view({'get': 'list'})),
    re_path(r'^organisms/(?P<ncbi_taxonomy_id>\d*)/$', views.OrganismViewSet.as_view({'get': 'list'})),


    # NMR annotations end-points
    re_path(r'^nmr/$', views.NMRViewSet.as_view({'get': 'list'})),
    re_path(r'^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/$', views.NMRViewSet.as_view({'get': 'list'})),
    re_path(r'^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/(?P<dataType>(binding|notbinding|docking))/$', views.NMRViewSet.as_view({'get': 'list'})),
    re_path(r'^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/(?P<dataType>(binding|notbinding|docking))/(?P<ligand_id>[0-9A-Z\-]+)/$', views.NMRViewSet.as_view({'get': 'list'})),

]


if settings.DEBUG:
    urlpatterns += path('__debug__/', include(debug_toolbar.urls)),
    SHOW_TOOLBAR_CALLBACK = True
