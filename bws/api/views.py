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
from rest_framework import status, viewsets, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .dataPaths import *
from django_filters import FilterSet, ModelChoiceFilter
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters import rest_framework as filters
from rest_framework.renderers import JSONRenderer
from datetime import datetime

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
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['name', 'details']
    ordering_fields = ['name', 'details']
    ordering = ['name']


class RefinedModelSourceViewSet(viewsets.ModelViewSet):
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


class RefinedModelViewSet(viewsets.ModelViewSet):
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


class TopicViewSet(viewsets.ModelViewSet):
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


class StructureToTopicViewSet(viewsets.ModelViewSet):
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


class LigandToImageDataViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides list of all ligand entries and "imageData" associated to them.
    """
    queryset = LigandEntity.objects.prefetch_related(
        "well__plate__screen__assay")
    serializer_class = LigandToImageDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SampleEntitySet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    renderer_classes = [JSONRenderer]
    queryset = SampleEntity.objects.all()
    serializer_class = SampleEntitySerializer


class LigandEntityViewSet(viewsets.ModelViewSet):
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


class PdbLigandViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    renderer_classes = [JSONRenderer]
    queryset = PdbToLigand.objects.all()
    serializer_class = PdbLigandSerializer
    search_fields = ['pdbId', 'ligand', 'quantity']
    ordering_fields = ['pdbId', 'ligand', 'quantity']
    ordering = ['pdbId']


class PdbEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = PdbEntry.objects.all()
    serializer_class = PdbEntryExportSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter,
                       OrderingFilter)
    search_fields = ['dbId', 'title', 'keywords', 'method']
    ordering_fields = [
        'dbId', 'title', 'status', 'relDate', 'method', 'resolution'
    ]
    ordering = ['-relDate']


class LigandsSectionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = LigandEntitySerializer

    def get_queryset(self, **kwargs):
        pdb_id = self.kwargs['pdb_id']
        queryset = LigandEntity.objects.filter(
            pdbligands__pdbId=pdb_id).prefetch_related(
                "well__plate__screen__assay")
        return queryset


class EntitiesSectionViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = EntityExportSerializer

    def get_queryset(self, **kwargs):
        pdb_id = self.kwargs['pdb_id']
        queryset = ModelEntity.objects.filter(pdbentities__pdbId=pdb_id)
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
            if db_id.startswith('emd-'):
                path = "%s/%s" % (EMDB_DATA_DIR, db_id)
                pattern = "*%s.json" % (method, )
            else:
                path = "%s/%s" % (EMDB_DATA_DIR, 'emd-*')
                pattern = "*%s_emv_%s.json" % (
                    db_id,
                    method,
                )
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


def _getConsensusData(db_id):
    # <EMDB-ID>_emv_localresolution_stats.json
    fileName = os.path.join(
        EMDB_DATA_DIR, db_id, "%s_emv_%s.json" % (
            db_id,
            'localresolution_stats',
        ))
    try:
        with open(fileName, 'r') as jfile:
            jdata = json.load(jfile)
    except (Exception) as exc:
        logger.exception(exc)
        raise Exception(exc)
    return jdata


class EmvDataLocalresConsensus(APIView):

    def get(self, request, **kwargs):
        """
        Get the consensus of all EMV local resolution methods by DB ID
        db_id : PDB | EMDB
        """
        try:
            if 'db_id' in self.kwargs:
                db_id = self.kwargs['db_id'].lower()
            jdata = _getConsensusData(db_id)
            return Response(jdata, status=status.HTTP_200_OK)
        except (Exception) as exc:
            logger.exception(exc)
            return not_found_resp(db_id)


def _getLocalResDBRank(resolution):
    """
        Find the position (rank) in the local resolution stats file by resolution
    """
    dataFile = os.path.join(EMDB_DATA_DIR, 'statistics',
                            LOCALRES_HISTORY_FILE)
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

    def get(self, request, **kwargs):
        """
        Get position of query entry respect all entries in DB ordered by the consensus of all localresolution EMV
        db_id : PDB | EMDB
        """
        try:
            if 'db_id' in self.kwargs:
                db_id = self.kwargs['db_id'].lower()
            jdata = _getConsensusData(db_id)
            resolution = jdata['data']['metrics']['resolutionMedian']
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
            queryset = OntologyTerm.objects.filter(
                source__dbId=ont_id).filter(dbId=term_id)
            return queryset
        # If not, provide all ontology terms
        except KeyError:
            queryset = OntologyTerm.objects.filter(
                source__dbId=ont_id)
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
        appVersionMajor = getattr(settings, "APP_VERSION_MAJOR", "")
        appVersionMinor = getattr(settings, "APP_VERSION_MINOR", "")
        appVersionPatch = getattr(settings, "APP_VERSION_PATCH", "")
        appEnvironment = getattr(settings, "ENVIRONMENT", "")
        resp = {
            'API_Version': appVersionMajor + '.' + appVersionMinor + '.' + appVersionPatch + '-' + appEnvironment,
            'Type': 'Semantic Versioning 2.0.0',
            'Major': appVersionMajor,
            'Minor': appVersionMinor,
            'Patch': appVersionPatch,
            'Environment': appEnvironment
        }

        return Response(resp)
