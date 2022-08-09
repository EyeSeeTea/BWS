import re
import logging
import requests
from django.http import HttpResponse, HttpResponseNotFound
from api import models, serializers
from api.utils import PdbEntryAnnFromMapsUtils
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from api.dataPaths import (COMPUT_MODELS_DIR, LOCAL_DATA_DIR,
                           MODEL_AND_LIGAND_DIR,
                           EMV_WS_URL,
                           EMV_WS_PATH)
from django_filters import rest_framework as filters
from django.db.models import Prefetch


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
    queryset = models.Entry.objects.all()
    serializer_class = serializers.EntrySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class LigandToImageDataViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides list of all ligand entries and "imageData" associated to them.
    """
    queryset = models.LigandEntity.objects.prefetch_related("well__plate__screen__assay")
    serializer_class = serializers.LigandToImageDataSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]