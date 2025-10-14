from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter
from api import views
from django.conf import settings
from django.http import HttpResponse

### Endpoints calling function in this section
from api.annotations import source_pfam as Pfam
from api.annotations import source_smart as smart
from api.annotations import source_ensembl_annotation as ensembl_annotation
from api.annotations import source_ensembl_variations as ensembl_variations
from api.annotations import source_pdbredo as pdbredo
from api.annotations import source_phosfosite as phosfosite
from api.annotations import source_iedb as iedb
from api.annotations import source_elmdb as elmdb
from api.annotations import source_dbptm as dbtpm
from api.annotations import source_biomuta as biomuta
from api.annotations import source_dsysmap as dsysmap
from api.annotations import source_uniprot as uniprot
from api.annotations import source_ebi as ebi
from api.annotations import source_mobi as mobi
from api.annotations import source_Interpro as interpro
from api.annotations import lrs

import json
import debug_toolbar

router = DefaultRouter()
router.register(r"topics", views.TopicViewSet)
router.register(r"topicStructures", views.StructureToTopicViewSet)
router.register(r"refinedModelSources", views.RefinedModelSourceViewSet)
router.register(r"refinedModelMethods", views.RefinedModelMethodViewSet)
router.register(r"refinedModels", views.RefinedModelViewSet)
router.register(r"sampleEntities", views.SampleEntitySet)
router.register(r"ligands", views.LigandEntityViewSet)
router.register(r"pdbligands", views.PdbLigandViewSet)
router.register(r"modelentities", views.ModelEntityViewSet)


urlpatterns = [
    path("annotations/Pfam/Uniprot/<str:uniprotID>", Pfam.source_PFAM),
    path("annotations/SMART/Uniprot/<str:uniprotAc>", smart.sourceSmartFromUniprot),
    path("annotations/PDB_REDO/<str:pdbID>", pdbredo.source_PDBredo),
    path("annotations/Phosphosite/Uniprot/<str:proteinID>", phosfosite.get_phosphositeFromUniprot),
    path("annotations/IEDB/Uniprot/<str:proteinID>", iedb.source_IEDB_from_DB),
    path("annotations/dbptm/Uniprot/<str:uniprot_id>", dbtpm.source_Dbptm_from_Uniprot),
    path("annotations/biomuta/Uniprot/<str:proteinID>", biomuta.source_Biomuta_from_uniprot),
    path("annotations/dsysmap/Uniprot/<str:uniprotID>", dsysmap.source_Dsysmap_From_Uniprot),
    path("annotations/elmdb/Uniprot/<str:uniprotID>", elmdb.source_ELMDB),
    path("annotations/ENSEMBL/variation/<str:ensemblid>", ensembl_variations.getENSEMBLvariations),
    path("annotations/ENSEMBL/annotation/<str:ensemblid>", ensembl_annotation.getENSEMBLannotations),
    path("lengths/Uniprot/<str:uniprotAc>", uniprot.get_uniprot_length),
    path("lengths/UniprotMulti/<str:uniprotAcs>", uniprot.fetch_uniprot_multiple_sequences),
    path("annotations/EBI/<str:type>/<str:uniprotAc>", ebi.source_ebi_features),
    #path("annotations/mobi/Uniprot/<str:uniprotAc>", mobi.source_Mobi), # ONLY READY FOR DATA ALREADY IN LOCAL DB
    #path("annotations/interpro/Uniprot/<str:uniprotAc>", interpro.source_Interpro_from_Uniprot), # NOT READY to use
    re_path('features/variants/Genomic_Variants_CNCB/(?P<uniprot_entry>[^/.]+)/$', lrs.TrackDetailView.as_view()),
    path("", include(router.urls)),
    path('complete/search', views.AutocompleteAPIView.as_view()),
    # Get version
    re_path(r"^version/$", views.GetApiVersion.as_view()),
    # EM Validation annotations for 3DBionotes - Protvista
    re_path(
        r"^pdbAnnotFromMap/all/(?P<pdb_id>\d\w{3})/(?P<chain_id>\w{1})/?(?P<modified_model>(pdb-redo|isolde))?/$",
        views.PdbEntryAllAnnFromMapView.as_view(),
    ),
    # Validation annotations for FunPDBe
    re_path(r"^funpdbe/$", views.FunPDBeEntryListView.as_view()),
    re_path(
        r"^funpdbe/(?P<pdb_id>\d[a-zA-Z]\w{2})/$", views.FunPDBeEntryByPDBView.as_view()
    ),
    re_path(
        r"^funpdbe/(?P<pdb_id>\d[a-zA-Z]\w{2})/(?P<method>(deepres|monores|blocres|mapq|fscq))/$",
        views.FunPDBeEntryByPDBMethodView.as_view(),
    ),
    # PDB Entry related end-points
    # get a list of all PDB entries in the DB
    re_path(r"^pdbentry/$", views.PdbEntryViewSet.as_view({"get": "list"})),
    # get a PDB Entry by pdb_id
    re_path(
        r"^pdbentry/(?P<pk>\d[a-zA-Z]\w{2})/$",
        views.PdbEntryViewSet.as_view({"get": "retrieve"}),
    ),
    re_path(
        r"^pdbentry/(?P<pdb_id>\d[a-zA-Z]\w{2})/ligands/$",
        views.LigandsSectionViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^pdbentry/(?P<pdb_id>\d[a-zA-Z]\w{2})/entities/$",
        views.EntitiesSectionViewSet.as_view({"get": "list"}),
    ),
    # EM Validation annotations statistics
    re_path(r"^emv/$", views.EmvDataView.as_view()),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/$",
        views.EmvDataByIDView.as_view(),
    ),
    re_path(
        r"^emv/(?P<method>(stats|deepres|monores|blocres|mapq|fscq|daq))/$",
        views.EmvDataByMethodView.as_view(),
    ),
    # DAQ scores
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/$",
        views.EmvDataByIdDaqView.as_view(),
    ),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<fileformat>(json|pdb|mmcif))/$",
        views.EmvDataByIdDaqView.as_view(),
    ),
    # TODO: add end-point for getting different versions
    # re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<version>)/$',
    #  views.EmvDataByIdDaqView.as_view()),
    # re_path(r'^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/daq/(?P<version>)/(?P<fileformat>(json|pdb))/$',
    #  views.EmvDataByIdDaqView.as_view()),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/(?P<method>(stats|deepres|monores|blocres|mapq|fscq))/(?P<fileformat>(json|pdb|mmcif))/$",
        views.EmvSourceDataByIdMethodView.as_view(),
    ),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/(?P<method>(stats|deepres|monores|blocres|mapq|fscq))/$",
        views.EmvDataByIdMethodView.as_view(),
    ),
    # Average Q-score and estimated resolution
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/mapq/averages/$",
        views.EmvMapQDataAveragesView.as_view(),
    ),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/consensus/$",
        views.EmvDataLocalresConsensus.as_view(),
    ),
    re_path(
        r"^emv/(?P<db_id>(\d[a-zA-Z]\w{2}|[EMD]*[emd]*-\d{4,5}))/localresolution/rank/$",
        views.EmvDataLocalresRank.as_view(),
    ),
    # Ontology related endpoints
    re_path(r"^ontologies/$", views.OntologyViewSet.as_view({"get": "list"})),
    re_path(r"^ontologies/terms/$",
            views.AllOntologyTermViewSet.as_view({"get": "list"})),
    re_path(
        r"^ontologies/terms/(?P<term_id>\w[a-zA-Z]*_\d*)/$",
        views.AllOntologyTermViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^ontologies/(?P<pk>\w[a-zA-Z]*)/$",
        views.OntologyViewSet.as_view({"get": "retrieve"}),
    ),
    re_path(
        r"^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/$",
        views.OntologyTermViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^ontologies/(?P<ont_id>\w[a-zA-Z]*)/terms/(?P<term_id>\w[a-zA-Z]*_\d*)$",
        views.OntologyTermViewSet.as_view({"get": "list"}),
    ),
    # Organisms related endpoint
    re_path(r"^organisms/$", views.OrganismViewSet.as_view({"get": "list"})),
    re_path(
        r"^organisms/(?P<ncbi_taxonomy_id>\d*)/$",
        views.OrganismViewSet.as_view({"get": "list"}),
    ),
    # NMR annotations end-points
    re_path(r"^nmr/$", views.NMRViewSet.as_view({"get": "list"})),
    re_path(r"^nmr/source/$", views.NMRSourceViewSet.as_view({"get": "list"})),
    re_path(r"^nmr/targets/$", views.NMRTargetsViewSet.as_view()),
    re_path(
        r"^nmr/targets/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/$",
        views.NMRTargetsViewSet.as_view(),
    ),
    re_path(
        r"^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/$",
        views.NMRViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/(?P<dataType>(binding|notbinding|docking))/$",
        views.NMRViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^nmr/(?P<uniprot_id>[OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})/(?P<dataType>(binding|notbinding|docking))/(?P<ligand_id>[0-9A-Z\-]+)/$",
        views.NMRViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^nmr/(?P<pdb_id>\d[a-zA-Z]\w{2})/$",
        views.NMRViewSetByPDB.as_view({"get": "list"}),
    ),
]


if settings.DEBUG:
    urlpatterns += path('__debug__/', include(debug_toolbar.urls)),
    SHOW_TOOLBAR_CALLBACK = True
