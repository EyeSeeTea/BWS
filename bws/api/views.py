import re
import json
import logging
import requests
from django.http import HttpResponse, HttpResponseNotFound
from .serializers import *
from .models import *
from .utils import PdbEntryAnnFromMapsUtils
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .dataPaths import *
from django_filters import FilterSet, ModelChoiceFilter
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters import rest_framework as filters


logger = logging.getLogger(__name__)

REGEX_PDB_ID = re.compile('^\d\w{3}$')
DEEP_RES_FNAME_TEMPLATE = "%(pdb_id)s.deepres.aa.pdb"
MONORES_FNAME_TEMPLATE = "%(pdb_id)s.monores.aa.pdb"
MAPQ_FNAME_TEMPLATE = "%(pdb_id)s.mapq.aa.pdb"
FSCQ_TEMPLATE = "%(pdb_id)s.fscq.aa.pdb"
ANN_TYPES_DICT = {"localResolution": {"deepres": DEEP_RES_FNAME_TEMPLATE, "monores": MONORES_FNAME_TEMPLATE},
                  "modelQuality": {"mapq": MAPQ_FNAME_TEMPLATE, "fscq": FSCQ_TEMPLATE}}
ANN_TYPES_MIN_VAL = {"localResolution": {"deepres": 1.5,
                                         "monores": 1.5}, "modelQuality": {"mapq": -1, "fscq": -3}}


def not_found_resp(query_id):
    logger.debug("Not found %s", query_id)
    content = {"request": query_id,
               "detail": "Annotation Entry Not Found"}
    return Response(content, status=status.HTTP_404_NOT_FOUND)


def bad_entry_request(query_id):
    logger.debug("Bad Request Entry ID: %s", query_id)
    content = {"request": query_id,
               "detail": "entryId _strictly_ must be in the form `emd-#####`"}
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
            content = {"request": pdb_id,
                       "detail": "entryId _strictly_ must be in the form `####/#`"}

            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        responseData = []
        if modified_model is not None:
            pdb_id = pdb_id+"."+modified_model
        for algFamily in ANN_TYPES_DICT:
            for algoName in ANN_TYPES_DICT[algFamily]:
                modifiedPdbFname = ANN_TYPES_DICT[algFamily][algoName] % {
                    "pdb_id": pdb_id}
                modifiedPdbFname = self._locateFname(
                    modifiedPdbFname, modifiedPdbType=modified_model)
                if modifiedPdbFname is not None:
                    algoDataDict = self._getJsonFromFname(
                        modifiedPdbFname, chain_id, minToFilter=ANN_TYPES_MIN_VAL[algFamily][algoName])
                    if algoDataDict is not None:
                        algoDataDict["algorithm"] = algoName
                        algoDataDict["algoType"] = algFamily
                        responseData.append(algoDataDict)

        if len(responseData) == 0:
            logger.debug("Not found %s", pdb_id+"/"+chain_id)
        #   Request EMV WebService to calculate the EMV scores
        #   This is an asyncronous call for computation. User must query again in the future to get results
            q_path = EMV_WS_URL + "/" + EMV_WS_PATH + "/" + pdb_id + "/" + chain_id + "/"
            logger.debug(
                "Requesting EMV WebService to calculate the EMV scores %s", q_path)
            try:
                headers = {'accept': 'application/json'}
                resp = requests.get(q_path, headers=headers, timeout=(2, 5))

                logger.debug("EMV WS-query: %s", resp.url)
                logger.debug("WS-response: %s, %s",
                             resp.status_code, resp.json())
                if resp:
                    dresp = HttpResponse(
                        content=resp.content,
                        status=resp.status_code,
                        content_type=resp.headers['Content-Type']
                    )
                    return dresp
            except Exception as exc:
                logger.exception(exc)

            return not_found_resp(pdb_id)

        return Response(responseData)


#  ######################################################################
class EntryViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class RefinedModelMethodViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = RefinedModelMethod.objects.all()
    serializer_class = RefinedModelMethodSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class RefinedModelSourceViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = RefinedModelSource.objects.all()
    serializer_class = RefinedModelSourceSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class RefinedModelViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = RefinedModel.objects.all()
    serializer_class = RefinedModelSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    search_fields = ['method', 'emdbId',  'pdbId']
    ordering_fields = ['method', 'emdbId',  'pdbId']
    ordering = ['method']


class TopicViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class StructureToTopicViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = StructureTopic.objects.all()
    serializer_class = StructureTopicSerializer
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    search_fields = ['topic', 'structure']
    ordering_fields = ['topic', 'structure']
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
                    entries.append({"entry": {
                        "pdb": os.path.basename(file).split(".", 1)[0][:4],
                        "filename": file}
                    })

        except(Exception) as exc:
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
            data_files = [x for x in os.listdir(
                path) if x.startswith(pdb_id) and x.endswith("-emv.json")]

            if not data_files:
                return not_found_resp(pdb_id)

            for file in data_files:
                entries.append({"entry": {
                    "pdb": os.path.basename(data_files[0]).split(".", 1)[0],
                    "filename": file}
                })

            with open(os.path.join(path, data_files[0])) as json_file:
                data = json.load(json_file)

        except(Exception) as exc:
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
                data_files = [x for x in os.listdir(path) if x.startswith(emdb_id.lower() + '_' + pdb_id)
                              and x.endswith(method + '.json')]
                if data_files:
                    # there should be only one
                    filepath = os.path.join(path, data_files[0])
                    with open(filepath, 'r') as jfile:
                        data = jfile.read()
                    response = HttpResponse(content=data)
                    response['Content-Type'] = 'application/json'
                    return response
            except(Exception) as exc:
                logger.exception(exc)

        return Response(status=status.HTTP_404_NOT_FOUND)


class LigandToImageDataViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides list of all ligand entries and "imageData" associated to them.
    """
    queryset = LigandEntity.objects.prefetch_related("well__plate__screen__assay")
    serializer_class = LigandToImageDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
