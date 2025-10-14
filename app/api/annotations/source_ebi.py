#! /usr/bin/env python3

import json
import requests
import datetime

from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

from .models import ebifeaturesentries

EBI_URL = "https://www.ebi.ac.uk/proteins/api/{}/{}"

def _load_EBI_from_DB(proteinid, type):
    query = None
    try:
        """
            Queries the database to get elements with the desired uniprotID
            Then turns it into a dict (to be able to be returned as json
            The behaviour varies depending on the query:
		    1 or more results -> returned in a dict
                - 0 results -> returns None
                - Error -> returns None and TODO: registers the error
	    """
        query = ebifeaturesentries.objects.filter(proteinID=proteinid)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{proteinid} not found in DB"}
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
    finally:
        return query

def _download_data_from_EBI(proteinid, type):
    url = EBI_URL.format(type, proteinid)
    response = requests.get(url)
    features = json.loads(response.text)
    if ("errorMessage" in features):
        return {"error": {"EBI_error":features["errorMessage"][0], "url": features["requestedURL"]}}
    return features

def _save_EBI_data(proteinid, type, data):
    element = ebifeaturesentries()
    element.proteinID = proteinid
    element.data = data
    element.created_at = datetime.datetime.now()
    element.updated_at = datetime.datetime.now()
    element.save()

def source_ebi_features(request, uniprotAc, type):
    print(uniprotAc, type)
    data = _load_EBI_from_DB(uniprotAc, type)
    print(data)
    status_code = 200
    if ("error" in data):
        data = _download_data_from_EBI(uniprotAc, type)
        if (not "error" in data): _save_EBI_data(uniprotAc, type, data)
        else: status_code = 404
    return HttpResponse(json.dumps(data), content_type='application/json', status=status_code)