from datetime import datetime, timezone
from itertools import chain
from pathlib import Path
import glob
import re
import json
import csv
import logging
import requests
from django.http import HttpResponse, HttpResponseNotFound
from .serializers import *
from .models import *
from .utils import PdbEntryAnnFromMapsUtils
from rest_framework import status, viewsets, permissions, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from .dataPaths import *
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters import rest_framework as filters
from rest_framework.renderers import JSONRenderer
from datetime import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, Value, BooleanField
from haystack.query import SearchQuerySet
import time

logger = logging.getLogger(__name__)

REGEX_PDB_ID = re.compile('^\d\w{3}$')
DEEP_RES_FNAME_TEMPLATE = "%(pdb_id)s.deepres.aa.pdb"
MONORES_FNAME_TEMPLATE = "%(pdb_id)s.monores.aa.pdb"
BLOCRES_FNAME_TEMPLATE = "%(pdb_id)s.blocres.aa.pdb"
MAPQ_FNAME_TEMPLATE = "%(pdb_id)s.mapq.aa.pdb"
DAQ_FNAME_TEMPLATE = "%(pdb_id)s.daq.aa.pdb"
FSCQ_TEMPLATE = "%(pdb_id)s.fscq.aa.pdb"
LOCALRES_HISTORY_FILE = 'emv_localResolution_stats.csv'
ANN_TYPES_DICT = {
    "localResolution": {
        "deepres": DEEP_RES_FNAME_TEMPLATE,
        "monores": MONORES_FNAME_TEMPLATE,
        "blocres": BLOCRES_FNAME_TEMPLATE
    },
    "modelQuality": {
        "mapq": MAPQ_FNAME_TEMPLATE,
        "fscq": FSCQ_TEMPLATE,
        "daq": DAQ_FNAME_TEMPLATE
    }
}
ANN_TYPES_MIN_VAL = {
    "localResolution": {
        "deepres": 1.5,
        "monores": 1.5,
        "blocres": 1.5
    },
    "modelQuality": {
        "mapq": -1,
        "fscq": -3,
        "daq": -1
    }
}


def not_found_resp(query_id):
    logger.debug("Not found %s", query_id)
    content = {"request": query_id, "detail": "Entry Not Found"}
    return Response(content, status=status.HTTP_404_NOT_FOUND)


def bad_entry_request(query_id):
    logger.debug("Bad Request Entry ID: %s", query_id)
    content = {
        "request": query_id,
        "detail": "entryId _strictly_ must be in the form `emd-#####`"
    }
    return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PdbEntryAllAnnFromMapView(APIView, PdbEntryAnnFromMapsUtils):
    """
    Retrieve an annotation entry `details`.
    """

    def get(self, request, pdb_id, chain_id, modified_model=None, format=None):
        """
        Get all map derived annotations related to one pdb_id, chain_id
        """

        pdb_id = pdb_id.lower()
        if not re.search(REGEX_PDB_ID, pdb_id):
            logger.debug("Bad Request Entry ID: %s", pdb_id)
            content = {
                "request": pdb_id,
                "detail": "entryId _strictly_ must be in the form `####/#`"
            }

            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        responseData = []
        if modified_model is not None:
            pdb_id = pdb_id + "." + modified_model
        for algFamily in ANN_TYPES_DICT:
            for algoName in ANN_TYPES_DICT[algFamily]:
                modifiedPdbFname = ANN_TYPES_DICT[algFamily][algoName] % {
                    "pdb_id": pdb_id
                }
                modifiedPdbFname = self._locateFname(
                    modifiedPdbFname, modifiedPdbType=modified_model)
                if modifiedPdbFname is not None:
                    algoDataDict = self._getJsonFromFname(
                        modifiedPdbFname,
                        chain_id,
                        minToFilter=ANN_TYPES_MIN_VAL[algFamily][algoName])
                    if algoDataDict is not None:
                        algoDataDict["algorithm"] = algoName
                        algoDataDict["algoType"] = algFamily
                        responseData.append(algoDataDict)

        if len(responseData) == 0:
            logger.debug("Not found %s", pdb_id + "/" + chain_id)
            #   Request EMV WebService to calculate the EMV scores
            #   This is an asyncronous call for computation. User must query again in the future to get results
            q_path = EMV_WS_URL + "/" + EMV_WS_PATH + "/" + pdb_id + "/" + chain_id + "/"
            logger.debug(
                "Requesting EMV WebService to calculate the EMV scores %s",
                q_path)
            try:
                headers = {'accept': 'application/json'}
                resp = requests.get(q_path, headers=headers, timeout=(2, 5))

                logger.debug("EMV WS-query: %s", resp.url)
                logger.debug("WS-response: %s, %s", resp.status_code,
                             resp.json())
                if resp:
                    dresp = HttpResponse(
                        content=resp.content,
                        status=resp.status_code,
                        content_type=resp.headers['Content-Type'])
                    return dresp
            except Exception as exc:
                logger.exception(exc)

            return not_found_resp(pdb_id)

        return Response(responseData)


#  ######################################################################

class RefinedModelMethodViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = RefinedModelMethod.objects.all()
    serializer_class = RefinedModelMethodSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class RefinedModelSourceViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = RefinedModelSource.objects.all()
    serializer_class = RefinedModelSourceSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class RefinedModelViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    renderer_classes = [JSONRenderer]
    queryset = RefinedModel.objects.all()
    serializer_class = RefinedModelSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['method', 'emdbId', 'pdbId']
    ordering_fields = ['method', 'emdbId', 'pdbId']
    ordering = ['method']


class TopicViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'description']
    ordering = ['name']


class StructureToTopicViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = StructureTopic.objects.all()
    serializer_class = StructureTopicSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = [
        'topic__name', 'structure__pdbId__dbId', 'structure__emdbId__dbId'
    ]
    ordering_fields = [
        'topic__name', 'structure__pdbId', 'structure__emdbId__dbId'
    ]
    ordering = ['topic']


class FunPDBeEntryListView(APIView):
    """
    Retrieve a list of all FunPDBe entries.
    """

    def get(self, request, format=None):
        """
        Get a list of entries
        """
        path = FUNPDBE_DATA_PATH
        entries = []
        try:
            logger.debug("Reading data folder: %s", path)
            for root, dirs, data_files in os.walk(path):
                for file in data_files:
                    entries.append({
                        "entry": {
                            "pdb": os.path.basename(file).split(".", 1)[0][:4],
                            "filename": file
                        }
                    })

        except (Exception) as exc:
            logger.exception(exc)

        return Response(entries)


class FunPDBeEntryByPDBView(APIView):
    """
    Retrieve a FunPDBe JSON file for the PDB entry
    """

    def get(self, request, pdb_id, format=None):
        path = os.path.join(FUNPDBE_DATA_PATH, pdb_id[1:3])
        entries = []
        try:
            logger.debug("Reading data folder: %s", path)
            data_files = [
                x for x in os.listdir(path)
                if x.startswith(pdb_id) and x.endswith("-emv.json")
            ]

            if not data_files:
                return not_found_resp(pdb_id)

            for file in data_files:
                entries.append({
                    "entry": {
                        "pdb": os.path.basename(data_files[0]).split(".",
                                                                     1)[0],
                        "filename": file
                    }
                })

            with open(os.path.join(path, data_files[0])) as json_file:
                data = json.load(json_file)

        except (Exception) as exc:
            logger.exception(exc)
            return not_found_resp(pdb_id)

        return Response(data)


def getEmdbMappings(pdb_id):
    """
    Find all PDB models fitted in a volume map, by EMDB ID
    Use the 3DBionotes API:
        https://3dbionotes.cnb.csic.es/api/mappings/PDB/EMDB/7a02/
    """
    url = BIONOTES_URL + "/" + MAPPINGS_WS_PATH + "/PDB/EMDB/" + pdb_id
    logger.debug("Check Bionotes WS for EMDB mappings for %s", pdb_id)
    logger.debug("WS-qry: %s", url)
    try:
        headers = {'accept': 'application/json'}
        resp = requests.get(url, headers=headers, timeout=(2, 5), verify=False)
        jresp = resp.json()

        logger.debug("WS-response: %s, %s", resp.status_code, jresp)
        if not resp.status_code == 200:
            return []
        return jresp[pdb_id]

    except Exception as exc:
        logger.exception(exc)


def getPdbMappings(emdb_id):
    """
    Find all EMDB volume maps with fitted atomic models, by PDB ID
    Use the 3DBionotes API:
        https://3dbionotes.cnb.csic.es/api/mappings/EMDB/PDB/EMD-2810
    """
    url = BIONOTES_URL + "/" + MAPPINGS_WS_PATH + "/EMDB/PDB/" + emdb_id
    logger.debug("Check Bionotes WS for PDB mappings for %s", emdb_id)
    logger.debug("WS-qry: %s", url)
    try:
        headers = {'accept': 'application/json'}
        resp = requests.get(url, headers=headers, timeout=(2, 5))
        jresp = resp.json()

        logger.debug("WS-response: %s, %s", resp.status_code, jresp)
        if not resp.status_code == 200:
            return []
        return jresp[emdb_id]

    except Exception as exc:
        logger.exception(exc)


class FunPDBeEntryByPDBMethodView(APIView):
    """
    Retrieve a JSON file with EMV validation data for the PDB entry
    by validation method
    """

    def get(self, request, pdb_id, method, format=None):
        volmaps = getEmdbMappings(pdb_id)
        if volmaps:
            # there should be only one
            emdb_id = volmaps[0]
            path = os.path.join(EMDB_DATA_DIR, emdb_id.lower())
            try:
                logger.debug("Reading data folder: %s", path)
                # emd-31319_7ey8_emv_mapq.json
                data_files = [
                    x for x in os.listdir(path)
                    if x.startswith(emdb_id.lower() + '_' +
                                    pdb_id) and x.endswith(method + '.json')
                ]
                if data_files:
                    # there should be only one
                    filepath = os.path.join(path, data_files[0])
                    with open(filepath, 'r') as jfile:
                        data = jfile.read()
                    response = HttpResponse(content=data)
                    response['Content-Type'] = 'application/json'
                    return response
            except (Exception) as exc:
                logger.exception(exc)

        return Response(status=status.HTTP_404_NOT_FOUND)



class SampleEntitySet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    renderer_classes = [JSONRenderer]
    queryset = SampleEntity.objects.all()
    serializer_class = SampleEntitySerializer


class LigandEntityViewSet(viewsets.GenericViewSet, 
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    # queryset = LigandEntity.objects.all()
    queryset = LigandEntity.objects.prefetch_related(
        "well__plate__screen__assay")
    serializer_class = LigandEntitySerializer
    search_fields = [
        'dbId',
        'IUPACInChIkey',
        'ligandType',
        'name',
        'formula',
    ]
    ordering_fields = [
        'ligandType',
        'IUPACInChIkey',
        'dbId',
        'name',
    ]
    ordering = ['ligandType', 'IUPACInChIkey']


class PdbLigandViewSet(viewsets.GenericViewSet,
    mixins.ListModelMixin, mixins.RetrieveModelMixin
    ):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    renderer_classes = [JSONRenderer]
    queryset = PdbToLigand.objects.all()
    serializer_class = PdbLigandSerializer
    search_fields = ['pdbId', 'ligand', 'quantity']
    ordering_fields = ['pdbId', 'ligand', 'quantity']
    ordering = ['pdbId']

class PdbEntryFilter(filters.FilterSet):
    is_antibody = filters.BooleanFilter(method='filter_by_is_antibody', label='Is antibody')
    is_nanobody = filters.BooleanFilter(method='filter_by_is_nanobody', label='Is nanobody')
    is_sybody = filters.BooleanFilter(method='filter_by_is_sybody', label='Is sybody')
    is_idr = filters.BooleanFilter(method='filter_by_is_idr', label='Is IDR')
    is_pdb_redo = filters.BooleanFilter(method='filter_by_is_pdb_redo', label='Is PDB-REDO')
    is_nmr = filters.BooleanFilter(method='filter_by_is_nmr', label='Is NMR')

    class Meta:
        model = PdbEntry
        fields = ['is_antibody', 'is_nanobody', 'is_sybody', 'is_idr', 'is_pdb_redo', 'is_nmr']

    def filter_by_is_antibody(self, queryset, name, value):
        kwords = ['antibody', 'antibodies', 'fab', 'heavy', 'light']
        case_expression = self.create_case_expression(kwords)
        return queryset.annotate(is_antibody=case_expression).filter(is_antibody=value).distinct()

    def filter_by_is_nanobody(self, queryset, name, value):
        kwords = ['nanobody', 'nanobodies', 'nonobody']
        case_expression = self.create_case_expression(kwords)
        return queryset.annotate(is_nanobody=case_expression).filter(is_nanobody=value).distinct()

    def filter_by_is_sybody(self, queryset, name, value):
        kwords = ['synthetic nanobody', 'sybody', 'sybodies']
        case_expression = self.create_case_expression(kwords)
        return queryset.annotate(is_sybody=case_expression).filter(is_sybody=value).distinct()
    
    def filter_by_is_pdb_redo(self, queryset, name, value):
        pdb_redo_source = RefinedModelSource.objects.get(name='PDB-REDO')
        pdb_redo_models = RefinedModel.objects.filter(pdbId=models.OuterRef('pk'), source=pdb_redo_source)
        return queryset.annotate(has_pdb_redo=models.Exists(pdb_redo_models)).filter(has_pdb_redo=value)
    
    def filter_by_is_idr(self, queryset, name, value):
        ligand_well_exists = models.Exists(LigandEntity.objects.filter(pdbentry=models.OuterRef('pk'), well__isnull=False))
        return queryset.annotate(has_ligand_well=ligand_well_exists).filter(has_ligand_well=value)
        
    def filter_by_is_nmr(self, queryset, name, value):
        has_nmr = models.Exists(ModelEntity.objects.filter(pdbentry=models.OuterRef('pk'), uniprotAcc__featureregionentity_features__isnull=False))
        return queryset.annotate(is_nmr=has_nmr).filter(is_nmr=value).distinct()

    def create_case_expression(self, kwords):
        case_expression = Case(
            *[When(entities__name__icontains=word, then=Value(True)) for word in kwords],
            *[When(entities__details__icontains=word, then=Value(True)) for word in kwords],
            *[When(entities__altNames__icontains=word, then=Value(True)) for word in kwords],
            default=Value(False),
            output_field=BooleanField()
        )
        return case_expression

    

class PdbEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    serializer_class = PdbEntryExportSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = PdbEntryFilter
    filterset_fields = ['is_antibody', 'is_nanobody', 'is_sybody', 'is_idr', 'is_pdb_redo', 'is_nmr']
    ordering_fields = ['dbId', 'title', 'relDate', 'emdbs__dbId']
    ordering = ['-relDate']

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        if query:
            search_results = SearchQuerySet().models(PdbEntry).filter_and(content=query)
            return PdbEntry.objects.filter(dbId__in=[result.pk for result in search_results])
        else:
            return PdbEntry.objects.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, dbId__iexact=kwargs.get('pk'))
        serializer = self.get_serializer(obj)
        return Response(serializer.data)

class AutocompleteAPIView(APIView):
    """
    This view provides autocomplete functionality.
    """
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').lower()
        if query:
            search_results = SearchQuerySet().models(PdbEntry).autocomplete(text_auto=query)
            split_results = [list(filter(None, result.text_auto.lower().split(';;'))) for result in search_results]
            filtered_results = [[word for word in result if query in word] for result in split_results]
            flattened_results = list(chain(*filtered_results))
            regex_filtered_results = [re.sub('.*[\w\d-]'+query+'.*|.*('+query+'[\w\d-]*\s?[\w\d-]*)|.*', r'\1', string, flags=re.IGNORECASE) for string in flattened_results]
            unique_results = list(filter(None,dict.fromkeys(regex_filtered_results)))
            return Response({
                'results': unique_results
            })
        else:
            return Response({
                'results': []
            })

class LigandsSectionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LigandEntitySerializer

    def get_queryset(self, **kwargs):
        pdb_id = self.kwargs['pdb_id']

        # Case Insensitive search on PdbToLigand
        pdb_ligands = PdbToLigand.objects.filter(pdbId__dbId__iexact=pdb_id)

        # Use PdbToLigand entries to filter LigandEntity
        queryset = LigandEntity.objects.filter(pdbligands__in=pdb_ligands).prefetch_related(
            "well__plate__screen__assay"
        )

        return queryset


class EntitiesSectionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = EntityExportSerializer

    def get_queryset(self, **kwargs):
        pdb_id = self.kwargs['pdb_id']

        # Case Insensitive search on PdbToEntity
        pdb_entities = PdbToEntity.objects.filter(pdbId__dbId__iexact=pdb_id)

        # Use PdbToEntity entries to filter ModelEntity
        queryset = ModelEntity.objects.filter(pdbentities__in=pdb_entities)
        return queryset


def _getEmvDataFiles(path, pattern):
    data_files = []
    logger.debug("Reading data folder: %s", path)
    try:
        search_path = "%s/%s" % (path, pattern)
        data_files = glob.glob(search_path, recursive=True)
    except (Exception) as exc:
        logger.exception(exc)
    return data_files


def _getJsonEMVEntry(file):
    fname = os.path.basename(file)
    fnameparts = fname.split("_")
    emdb_id = fnameparts[0].upper()
    pdb_id = fnameparts[1].upper() if '_stats' not in fname else ""
    entryType = "EMV data" if '_stats' not in fname else "EMV Statistics"
    return {
        "EMVentry": {
            "emdb": emdb_id,
            "pdb": pdb_id,
            "type": entryType,
            "filename": fname,
        }
    }


class EmvDataView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a list of all EMV entries
        """
        data_files = []
        entries = []
        data_files = _getEmvDataFiles(path="%s/%s" % (EMDB_DATA_DIR, 'emd-*'),
                                      pattern='*emv_*.json')
        for file in data_files:
            entries.append(_getJsonEMVEntry(file))
        if entries:
            return Response(entries)
        else:
            return HttpResponseNotFound()


class EmvDataByMethodView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a list of all EMV entries by method
        method : deepres | monores | blocres | mapq | fscq | daq
        """
        data_files = []
        entries = []
        if 'method' in self.kwargs:
            method = self.kwargs['method']
        data_files = _getEmvDataFiles(path="%s/%s" % (EMDB_DATA_DIR, 'emd-*'),
                                      pattern="*emv_*%s.json" % (method, ))
        for file in data_files:
            entries.append(_getJsonEMVEntry(file))
        if entries:
            return Response(entries)
        else:
            content = {
                "request": "EMV: %s" % (method),
                "detail": "Entry not found"
            }
            return Response(content, status=status.HTTP_404_NOT_FOUND)


class EmvDataByIDView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a list of all EMV entries by DB ID
        db_id : PDB | EMDB
        """
        data_files = []
        entries = []
        if 'db_id' in self.kwargs:
            db_id = self.kwargs['db_id'].lower()
            if db_id.startswith('emd-'):
                path = "%s/%s" % (EMDB_DATA_DIR, db_id)
                pattern = "%s*_emv_*.json" % (db_id, )
            else:
                path = "%s/%s" % (EMDB_DATA_DIR, 'emd-*')
                pattern = "*%s_emv_*.json" % (db_id, )
        data_files = _getEmvDataFiles(path, pattern)
        for file in data_files:
            entries.append(_getJsonEMVEntry(file))
        if entries:
            return Response(entries)
        else:
            content = {
                "request": "EMV: %s" % (db_id),
                "detail": "Entry not found"
            }
            return Response(content, status=status.HTTP_404_NOT_FOUND)


class EmvDataByIdMethodView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a JSON file with EMV data for an entry by DB ID and method
        db_id : PDB | EMDB
        method : deepres | monores | blocres | mapq | fscq | daq
        """
        data_files = []
        if 'method' in self.kwargs:
            method = self.kwargs['method']
        if 'db_id' in self.kwargs:
            db_id = self.kwargs['db_id'].lower()
            if method == 'mapq':
                # data source: Grigore Pintilie
                path = os.path.join(LOCAL_DATA_DIR, 'q-score', 'json')
                if db_id.startswith('emd-'):
                    pattern = "%s*_emv_%s.json" % (
                        db_id.replace("emd-", "emd_"), method,)
                else:
                    pattern = "*%s_emv_%s.json" % (db_id, method,)
            elif method == 'daq':
                # data source: Daisuke Kihara
                path = os.path.join(LOCAL_DATA_DIR, 'daq', 'json', '**')
                if db_id.startswith('emd-'):
                    pattern = "%s*_emv_%s.json" % (db_id, method,)
                else:
                    pattern = "*%s_emv_%s.json" % (db_id, method,)
            else:
                if db_id.startswith('emd-'):
                    path = "%s/%s" % (EMDB_DATA_DIR, db_id)
                    pattern = "*%s.json" % (method, )
                else:
                    path = "%s/%s" % (EMDB_DATA_DIR, 'emd-*')
                    pattern = "*%s_emv_%s.json" % (db_id, method,)

        data_files = _getEmvDataFiles(path, pattern)
        # there should be only one file for entry/method
        if len(data_files) != 1:
            content = {
                "request": "EMV: %s/%s" % (db_id, method),
                "detail": "Entry not found"
            }
            return Response(content, status=status.HTTP_404_NOT_FOUND)
        fileName = data_files[0]
        # return JSON file
        with open(fileName, 'r') as jfile:
            resp = json.load(jfile)
        return Response(resp)


class EmvSourceDataByIdMethodView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a file with EMV source data for an entry by DB ID and method
        db_id : PDB | EMDB
        method : deepres | monores | blocres | mapq | fscq | daq
        format : json | pdb | cif
        """
        fileformat = self.kwargs['fileformat'] if 'fileformat' in self.kwargs else ""
        method = self.kwargs['method'] if 'method' in self.kwargs else ""
        db_id = self.kwargs['db_id'].lower() if 'db_id' in self.kwargs else ""

        path = os.path.join(LOCAL_DATA_DIR)
        pattern = "*"
        data_files = []

        if method == 'mapq':
            if fileformat == 'mmcif':
                # original data from Grigore Pintilie
                path = os.path.join(
                    LOCAL_DATA_DIR, 'q-score', 'emdb_qscores')
                if db_id.startswith('emd-'):
                    pattern = "%s*.cif" % db_id.replace("emd-", "emd_")
                else:
                    pattern = "*pdb_%s.cif" % db_id

            elif fileformat == 'json':
                # reformated data from Grigore Pintilie
                path = os.path.join(LOCAL_DATA_DIR, 'q-score', 'json')
                if db_id.startswith('emd-'):
                    pattern = "%s*_emv_%s.json" % (
                        db_id.replace("emd-", "emd_"), method,)
                else:
                    pattern = "*%s_emv_%s.json" % (db_id, method,)

        elif method == 'daq':
            if fileformat == 'pdb':
                # original data from Kihara Lab
                path = os.path.join(LOCAL_DATA_DIR, 'daq',
                                    'data_20230426', '**')
                if db_id.startswith('emd-'):
                    pattern = "%s*.pdb" % db_id.replace("emd-", "")
                else:
                    pattern = "*%s*.pdb" % db_id
            elif fileformat == 'json':
                # reformated data from Kihara Lab
                path = os.path.join(LOCAL_DATA_DIR, 'daq', 'json', '**')
                if db_id.startswith('emd-'):
                    pattern = "%s*_emv_%s.json" % (db_id, method,)
                else:
                    pattern = "*%s_emv_%s.json" % (db_id, method,)

        data_files = _getEmvDataFiles(path, pattern)
        content = ""
        data_files = [f for f in data_files if os.path.isfile(f)]
        for data_file in data_files:
            if data_file.endswith('json'):
                with open(data_file, 'r') as jfile:
                    resp = json.load(jfile)
                return Response(resp)
            else:
                with open(data_file, 'r') as tfile:
                    for line in tfile:
                        content += line

        if content:
            response = HttpResponse(content, content_type='text/plain')
            return response
        else:
            content = {
                "request": "EMV: %s" % (request.path,),
                "detail": "Entry not found",
            }
            return Response(content, status=status.HTTP_404_NOT_FOUND)


class EmvMapQDataAveragesView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get Average Q-score and Estimated Resolution for EMV MapQ source data for an entry by DB ID
        db_id : PDB | EMDB
        method : mapq
        """
        db_id = self.kwargs['db_id'].lower() if 'db_id' in self.kwargs else ""

        data_path = os.path.join(LOCAL_DATA_DIR, 'q-score')
        data_filename = "emd_qscores.txt"
        dataFile = os.path.join(data_path, data_filename)
        resource = "EMV-MapQ-Averages"
        method_type = "MapQ"
        software_version = getattr(settings, "APP_VERSION_MAJOR", "") + '.' + getattr(
            settings, "APP_VERSION_MINOR", "") + '.' + getattr(settings, "APP_VERSION_PATCH", "")
        proc_date = time.strftime(
            '%Y-%m-%d', time.gmtime(os.path.getmtime(dataFile)))
        source_data = {
            "method": "MapQ - Q-score - Grigore Pintilie",
            "citation": "Pintilie, G. & Chiu, W. (2021). Validation, analysis and annotation of cryo-EM structures. Acta Cryst. D77, 1142–1152.",
            "doi": "doi:10.1107/S2059798321006069"
        }
        content = None
        try:
            with open(dataFile) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter='\t')
                for row in csv_reader:
                    if db_id.startswith('emd'):
                        entry_id = row[0].lower().replace('emd_', '')
                    else:
                        entry_id = row[1]

                    if db_id.replace('emd-', '') == entry_id:
                        content = {
                            "resource": resource,
                            "methodType": method_type,
                            "softwareVersion": software_version,
                            "entry": {
                                "volumeMap": "EMD-%s" % row[0].replace('emd_', ''),
                                "atomicModel": row[1],
                                "date": proc_date,
                                "source": source_data
                            },
                            "data": {
                                "averageQScore": float(row[2]),
                                "estimatedResolution": float(row[3])
                            }
                        }
                        return Response(content, status=status.HTTP_200_OK)

        except (Exception) as exc:
            logger.exception(exc)

        content = {
            "request": "EMV: %s" % (request.path,),
            "detail": "Entry not found",
        }
        return Response(content, status=status.HTTP_404_NOT_FOUND)


def _getConsensusData(db_id):
    # <EMDB-ID>_emv_localresolution_stats.json
    fileName = os.path.join(
        EMDB_DATA_DIR, db_id, "%s_emv_%s.json" % (
            db_id,
            'localresolution_cons',
        ))
    try:
        with open(fileName, 'r') as jfile:
            jdata = json.load(jfile)
    except (Exception) as exc:
        logger.exception(exc)
        raise Exception(exc)
    return jdata


class EmvDataLocalresConsensus(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get the consensus of all EMV local resolution methods by DB ID
        db_id : PDB | EMDB
        """
        try:
            if 'db_id' in self.kwargs:
                db_id = self.kwargs['db_id'].lower()
            jdata = _getConsensusData(db_id)

            jout = {
                "resource": jdata['resource'],
                "method_type": jdata["method_type"],
                "software_version": jdata["software_version"],
                "entry": jdata["entry"],
                "data": {
                    "sampling": jdata["data"]["sampling"],
                    "threshold": 2,
                },
                "warnings": jdata["warnings"],
                "errors": jdata["errors"]
            }
            metrics = []
            for metric in jdata["data"]["metrics"]:
                metric["unit"] = "Angstrom"
                metrics.append(metric)
            jout["data"]["metrics"] = metrics

            return Response(jout, status=status.HTTP_200_OK)
        except (Exception) as exc:
            logger.exception(exc)
            return not_found_resp(db_id)


def _getLocalResDBRank(resolution):
    """
        Find the position (rank) in the local resolution stats file by resolution
    """
    dataFile = os.path.join(EMDB_DATA_DIR, 'statistics', LOCALRES_HISTORY_FILE)
    resolutionList = []
    try:
        with open(dataFile) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            for row in csv_reader:
                resolutionList.append(float(row[1]))
    except (Exception) as exc:
        logger.exception(exc)
        raise Exception("Could not find %s" % dataFile)

    resolutionList.sort()
    position = 0
    for item in resolutionList:
        if resolution < item:
            break
        else:
            position = position + 1
    return int(position / len(resolutionList) * 100)


class EmvDataLocalresRank(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get position of query entry respect all entries in DB ordered by the consensus of all localresolution EMV
        db_id : PDB | EMDB
        """
        try:
            if 'db_id' in self.kwargs:
                db_id = self.kwargs['db_id'].lower()
            jdata = _getConsensusData(db_id)
            for metric in jdata['data']['metrics']:
                if 'resolutionMedian' in metric:
                    resolution = metric['resolutionMedian']
                    rank = _getLocalResDBRank(resolution)
        except (Exception) as exc:
            logger.exception(exc)
            return (not_found_resp(db_id))

        content = {
            "resource": "EMV-LocalResolution-DB_Rank",
            "method_type": "Local Resolution",
            "software_version": "0.7.0",
            "entry": {
                "date": datetime.today().strftime("%Y-%m-%d"),
                "volume_map": "%s" % (db_id),
            },
            "data": {
                "resolution": resolution,
                "rank": rank
            }
        }
        return Response(content, status=status.HTTP_200_OK)


class OntologyViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Ontology.objects.all()
    serializer_class = OntologySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)


class OntologyTermViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OntologyTermSerializer

    def get_queryset(self, **kwargs):

        ont_id = self.kwargs['ont_id']

        # If term_id is specified in url, filter ontology terms
        try:
            term_id = self.kwargs['term_id']
            queryset = OntologyTerm.objects.filter(source__dbId=ont_id).filter(
                dbId=term_id)
            return queryset
        # If not, provide all ontology terms
        except KeyError:
            queryset = OntologyTerm.objects.filter(source__dbId=ont_id)
            return queryset


class AllOntologyTermViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OntologyTermSerializer

    def get_queryset(self, **kwargs):

        # If term_id is specified in url, filter ontology terms
        try:
            term_id = self.kwargs['term_id']
            queryset = OntologyTerm.objects.filter(dbId=term_id)
            return queryset
        # If not, provide all ontology terms
        except KeyError:
            queryset = OntologyTerm.objects.all()
            return queryset


class OrganismViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = OrganismSerializer

    def get_queryset(self, **kwargs):

        # If ncbi_taxonomy_id is specified in url, filter Organisms
        try:
            ncbi_taxonomy_id = self.kwargs['ncbi_taxonomy_id']
            queryset = Organism.objects.filter(
                ncbi_taxonomy_id=ncbi_taxonomy_id)
            return queryset
        # If not, provide all Organisms
        except KeyError:
            queryset = Organism.objects.all()
            return queryset


class GetApiVersion(APIView):
    """
    Get API version
    """

    def get(self, request, format=None):
        """
        Get full info on API version
        """
        appVersionMajor = getattr(settings, "API_VERSION_MAJOR", "")
        appVersionMinor = getattr(settings, "API_VERSION_MINOR", "")
        appVersionPatch = getattr(settings, "API_VERSION_PATCH", "")
        appEnvironment = getattr(settings, "RUNNING_ENVIRONMENT", "")
        resp = {
            'API_Version':
            appVersionMajor + '.' + appVersionMinor + '.' + appVersionPatch +
            '-' + appEnvironment,
            'Type':
            'Semantic Versioning 2.0.0',
            'Major':
            appVersionMajor,
            'Minor':
            appVersionMinor,
            'Patch':
            appVersionPatch,
            'Environment':
            appEnvironment
        }

        return Response(resp)


class NMRViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    serializer_class = FeatureRegionEntitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)

    def get_queryset(self, **kwargs):

        # Get URL parameters uniprot_id, dataType and ligand_id if they have been specified
        uniprot_id = self.kwargs.get('uniprot_id', None)
        dataType = self.kwargs.get('dataType', None)
        ligand_id = self.kwargs.get('ligand_id', None)

        # Get query parameters start and end
        start = self.request.query_params.get('start', None)
        end = self.request.query_params.get('end', None)
        target = self.request.query_params.get('target', None)

        # Get NMR queryset
        queryset = FeatureRegionEntity.objects.filter(
            featureType__dataSource__exact='The COVID19-NMR Consortium').order_by('details__type')

        # Filter queryset depending on URL parameters
        if uniprot_id:
            queryset = queryset.filter(uniprotentry=uniprot_id).order_by('details__type')
        if dataType:
            queryset = queryset.filter(details__type=dataType)
        if ligand_id:
            queryset = queryset.filter(ligandentity=ligand_id)

        if start and end:
            queryset = queryset.filter(start__lte=end, end__gte=start)
        if target:
            queryset = queryset.filter(details__entity=target)

        return queryset

class NMRTargetsViewSet(APIView):
    """
    This viewset automatically provides `list` and `detail` actions.
    """

    def get(self, request, uniprot_id=False):

        # Get NMR target queryset
        queryset = FeatureRegionEntity.objects.filter(
            featureType__dataSource__exact='The COVID19-NMR Consortium').order_by('id').values('details')
        
        # Get entry details for all NMR entries
        results = []
        for entry in queryset:
            entity = entry['details']['entity']
            start = entry['details']['start']
            end = entry['details']['end']
            uniprot_acc = entry['details']['uniprot_acc']

            targetDict = {
                'entity': entity,
                'start': start,
                'end': end,
                'uniprot_acc': uniprot_acc,
            }
            results.append(targetDict)

        # Filter unique entries depending on entity name
        unique_dict = {item['entity']: item for item in results}

        # Get unique entry list
        unique_results = list(unique_dict.values())

        # Filter unique entry list if uniprot id is provided
        if uniprot_id:
            unique_results = [dic for dic in unique_results if dic.get('uniprot_acc') == uniprot_id]

        count = len(unique_results)

        return Response({'count': count, 'results': unique_results})


class NMRSourceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    serializer_class = FeatureTypeNMRSerializer
    queryset = FeatureType.objects.filter(
            name__exact='NMR-based fragment screening')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)


# -----
# DAQ
# https://daqdb.kiharalab.org/download/current/entry_ids.txt
# https://daqdb.kiharalab.org/data/aa/js/22458_7jsn_B_v1-1_w9.pdb
WEEK = "w9"


class EmvDataByIdDaqView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, **kwargs):
        """
        Get a file with EMV source data for an entry by DB ID and method
        db_id : PDB | EMDB
        method : daq
        format : json
        """
        fileformat = self.kwargs['fileformat'] if 'fileformat' in self.kwargs else ""
        db_id = self.kwargs['db_id'].lower() if 'db_id' in self.kwargs else ""
        method = 'daq'
        data_files = []
        # get the list of entries
        # 22458_7jsn_A_v1-1
        # 22458_7jsn_A_v2-0
        # 22458_7jsn_B_v1-1
        # 22458_7jsn_B_v2-0
        # 22458_7jsn_C_v1-1
        # 22458_7jsn_C_v2-0
        # 22458_7jsn_D_v1-1
        # 22458_7jsn_D_v2-0
        # 22458_7jsn_E_v1-1
        # 22458_7jsn_E_v2-0
        # 22458_7jsn_F_v1-1
        # 22458_7jsn_F_v2-0
        entry_list = self.getDaqEntryList()
        # search db_id in the index
        entries = self.searchDbId(
            db_id, entry_list, sort=False, reversed=False)
        if entries:
            emdb_id = 'EMD-' + entries[0][1][0]
            pdb_id = entries[0][1][1]
            # get all versions
            versions = []
            for entry in entries:
                version = entry[1][3].replace('v', '').replace('-', '.')
                if version not in versions:
                    versions.append(version)
            # get latest version
            latest_version = max(versions)
            # get files of the latest version only
            # TODO: cache these files to optimize performance
            data_files = []
            for entry in entries:
                version = entry[1][3].replace('v', '').replace('-', '.')
                filename = entry[0]
                if version == latest_version:
                    data_files.append(filename)
            # get url to download data
            # https://daqdb.kiharalab.org/data/aa/js/22458_7jsn_B_v2-0_w9.pdb
            urls = []
            for data_file in data_files:
                two_letter_hash = pdb_id[1:3]
                urls.append("https://daqdb.kiharalab.org/data/aa/%s/%s_%s.pdb" %
                            (two_letter_hash, data_file, WEEK,))

            if fileformat == 'pdb':
                # original data from Kihara Lab
                pdb_data = self.getSourceData(urls, format='pdb')
                return HttpResponse(pdb_data, content_type='text/plain')
            elif fileformat == 'mmcif':
                # reformated data from Kihara Lab
                # get mmCif format
                pdb_data = self.getSourceData(urls, format='pdb')
                cif_header = self.getCifHeader(pdb_id)
                cif_data = cif_header + '\n' + pdb_data + '\n' + '#'
                return HttpResponse(cif_data, content_type='text/plain')
            else:
                # reformated data from Kihara Lab
                # get JSON format
                emv_data = {}
                emdb_entry_num, pdb_entry, chainId, version = data_files[0].split(
                    "_")
                emv_data = self.getEmvDataHeader(
                    'emd-' + emdb_entry_num, pdb_entry, latest_version, versions, datetime.today().strftime("%m_%Y"))

                # get data from source
                chains_data = self.getSourceData(urls, format='json')
                emv_data["chains"] = chains_data

                if emv_data:
                    return Response(emv_data)

        content = {
            "request": "EMV: %s" % (request.path,),
            "detail": "Entry not found",
        }
        return Response(content, status=status.HTTP_404_NOT_FOUND)

    def getSourceData(self, urls, format="json"):
        pdb_data = ""
        chains_data = []
        for url in urls:
            try:
                resp = requests.get(url)
                if resp.status_code == 200:
                    if format == 'pdb':
                        pdb_data += resp.text + '\n'
                    if format == 'json':
                        chains_data.append(self.pdb2json(resp.text))
            except Exception as exc:
                logger.exception(exc)

        return pdb_data if pdb_data else chains_data

    def getDaqEntryList(self):

        url = "https://daqdb.kiharalab.org/download/current/entry_ids.txt"
        cache_path = "/tmp/bws/daq"
        cache_filename = "entry_ids.txt.cache"
        business_days = 7
        ndays = datetime.now().timestamp() - business_days * 86400
        # check recent cached file exists
        cache_file = Path(cache_path, cache_filename)
        try:
            logger.debug("Get the cache file %s" + str(cache_file))
            if cache_file.exists():
                logger.debug("Found the cache file %s" + str(cache_file))
                stat_result = cache_file.stat()
                modified = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
                logger.debug("The cache file is newer than %s days: %s" % (str(business_days), modified))
                if ndays < stat_result.st_mtime:
                    logger.debug("Read cache file")
                    with cache_file.open() as cf:
                        text_content = cf.readlines()
                    return text_content
                logger.debug("The cache file is older than %s days: %s" % (str(business_days), modified))
        except Exception as exc:
            logger.exception(exc)

        # get the list from source
        try:
            resp = requests.get(url)
            if not resp.status_code == 200:
                return []
            text_content = resp.text.splitlines()
            # save a cache
            logger.debug("Create cache path if not exists %s" % str(cache_path))
            Path(cache_path).mkdir(parents=True, exist_ok=True)
            logger.debug("Save the cache file %s" % cache_file)
            with cache_file.open( mode='w') as cf:
                for line in text_content:
                    cf.write(line + os.linesep)
            return text_content
        except Exception as exc:
            logger.exception(exc)

    def searchDbId(self, db_id, entry_list, sort=True, reversed=True):
        entries = []
        for entry in entry_list:
            entry = entry.replace(os.linesep, '')
            if db_id.replace('emd-', '') in entry.strip():
                entries.append([entry, entry.split('_')])
        # return entries
        if sort:
            return sorted(entries, key=lambda entry: entry[1][3], reverse=reversed)
        else:
            return entries

    def pdb2json(self, input_data=""):

        chain_data = {}
        chain_data["name"] = ""
        chain_data["seqData"] = []
        current_residue = 0
        for line in input_data.splitlines():
            if (line.startswith('ATOM') or line.startswith('HETATM')):
                # read fields
                # 0....v...10....v...20....v...30....v...40....v...50....v...60....v...70....v...80
                # 0....v....|....v....|....v....|....v....|....v....|....v....|....v....|....v....|
                # ATOM      1  N   LYS a   3     137.151 284.625 191.025  1.00 -0.15           N
                # ATOM      2  CA  LYS a   3     137.054 283.137 191.000  1.00 -0.15           C
                # ATOM      3  C   LYS a   3     136.248 282.626 192.185  1.00 -0.15           C
                # ATOM      4  O   LYS a   3     135.725 281.512 192.154  1.00 -0.15           O
                # ATOM      5  CB  LYS a   3     138.450 282.511 191.066  1.00 -0.15           C
                # ATOM      6  CG  LYS a   3     139.408 283.009 190.010  1.00 -0.15           C
                # ATOM      7  CD  LYS a   3     139.016 282.529 188.633  1.00 -0.15           C
                # ATOM      8  CE  LYS a   3     139.452 283.537 187.603  1.00 -0.15           C
                # ATOM      9  NZ  LYS a   3     138.766 284.840 187.834  1.00 -0.15           N
                # ATOM     10  N   LEU a   4     136.140 283.444 193.226  1.00 -0.14           N
                # ATOM     11  CA  LEU a   4     135.431 283.021 194.422  1.00 -0.14           C
                # ATOM     12  C   LEU a   4     134.113 283.719 194.744  1.00 -0.14           C
                # ATOM     13  O   LEU a   4     133.072 283.068 194.814  1.00 -0.14           O
                # ATOM     14  CB  LEU a   4     136.364 283.126 195.631  1.00 -0.14           C
                # ATOM     15  CG  LEU a   4     137.712 282.402 195.524  1.00 -0.14           C
                # ATOM     16  CD1 LEU a   4     138.450 282.507 196.850  1.00 -0.14           C
                # ATOM     17  CD2 LEU a   4     137.498 280.941 195.148  1.00 -0.14           C
                # ATOM     18  N   THR a   5     134.143 285.032 194.945  1.00 -0.09           N
                # ATOM     19  CA  THR a   5     132.918 285.739 195.298  1.00 -0.09           C
                # ATOM     20  C   THR a   5     132.340 286.698 194.266  1.00 -0.09           C
                # ATOM     21  O   THR a   5     132.643 287.892 194.248  1.00 -0.09           O
                # ATOM     22  CB  THR a   5     133.091 286.495 196.624  1.00 -0.09           C
                # ATOM     23  OG1 THR a   5     134.251 287.331 196.544  1.00 -0.09           O
                # ATOM     24  CG2 THR a   5     133.244 285.512 197.776  1.00 -0.09           C

                # Split the line
                group_PDB = line[:6]
                atom_id = line[6:11]
                atom_symbol = line[12:16]
                # residue name (DAQ is using the ones provided by the author)
                label_comp_id = line[17:20]
                # chain name (DAQ is using the ones provided by the author)
                label_asym_id = line[21]
                # residue seq number (DAQ is using the ones provided by the author)
                label_seq_id = line[22:26]
                Cartn_x = line[30:38]
                Cartn_y = line[38:46]
                Cartn_z = line[46:54]
                occupancy = line[54:60]
                # DAQ score mean value for the whole residue
                daq_score = line[60:66]
                auth_atom_id = line[77:]

                # skip data for atoms in the same residue
                if current_residue == label_seq_id:
                    continue

                residue_data = {
                    "resSeqName": label_comp_id,
                    "resSeqNumber": label_seq_id,
                }
                residue_data["scoreValue"] = daq_score
                chain_data["seqData"].append(residue_data)
                # use the name provided by the author for the chain
                chain_data["name"] = label_asym_id
                current_residue = label_seq_id
        return chain_data

    def getEmvDataHeader(self, emdb_id, pdb_id, pdb_version, pdb_versions,  proc_date):
        emv_data = {}
        emv_data["resource"] = "EMV-DAQ-Scores"
        entry_data = {
            "volumeMap": emdb_id,
            "atomicModel": pdb_id,
            "pdbVersion": {"current": pdb_version,
                           "available": pdb_versions},
            "date": proc_date
        }
        source_data = {
            "method": "DAQ-Score Database - Kihara Lab",
            "citation":
            "Nakamura, T., Wang, X., Terashi, G. et al. DAQ-Score Database: assessment of map-model compatibility for protein structure models from cryo-EM maps. Nat Methods 20, 775-776 (2023).",
            "doi": "https://doi.org/10.1038/s41592-023-01876-1",
            "source":
            "https://daqdb.kiharalab.org/search?query=%s" % emdb_id.upper(),
        }
        entry_data["source"] = source_data
        emv_data["entry"] = entry_data
        emv_data["chains"] = []

        logger.debug('EMV DAQ data header %s %s %s' %
                     (emdb_id, pdb_id, emv_data))
        return emv_data

    def getCifHeader(self, pdb_id):
        """
        Not completly standar header
        just the definition of the fields available in DAQ files
        """
        header = 'data_' + pdb_id
        header += '\n' + '#'
        header += '\n' + '_entry.id ' + pdb_id
        header += '\n' + '#'

        loop = 'loop_'
        loop += '\n' + '_atom_site.group_PDB'
        loop += '\n' + '_atom_site.id'
        loop += '\n' + '_atom_site.label_atom_id'
        loop += '\n' + '_atom_site.label_comp_id'
        loop += '\n' + '_atom_site.label_asym_id'
        loop += '\n' + '_atom_site.label_seq_id'
        loop += '\n' + '_atom_site.Cartn_x'
        loop += '\n' + '_atom_site.Cartn_y'
        loop += '\n' + '_atom_site.Cartn_z'
        loop += '\n' + '_atom_site.occupancy'
        loop += '\n' + '_atom_site.Q-score'
        loop += '\n' + '_atom_site.type_symbol'

        header += '\n' + loop
        return header
