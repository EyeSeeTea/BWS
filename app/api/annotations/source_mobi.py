#! /usr/bin/env python

import json

import requests

from django.http import HttpResponse
from django.forms.models import model_to_dict

from .models import mobientries

MOBI_URL:str = "http://mobidb.bio.unipd.it/ws/{}/consensus"

def _save_Mobi_on_DB(data, uniprotAc):
    pass

def _load_Mobi_from_DB(uniprotAc):
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
        query = mobientries.objects.filter(proteinID=uniprotAc)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{id} not found in DB"}
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
    return  query

def _process_downloaded_Mobi_data(uniprotAc, data):
    main_out = dict()
    disorder = {}
    flag = False
    if "mobidb_consensus" in data and "disorder" in data["mobidb_consensus"]:
        pass
    main_out["disorder"] = out
    lips = {}
    if "mobidb_consensus" in data and "lips" in data["mobidb_consensus"]:
        pass
    main_out["lips"] = lips
    if flag: _save_Mobi_on_DB(data, uniprotAc)
    to_return = json.dumps

def _download_Mobi_from_MobiDB(uniprotAc):
    url = MOBI_URL.format(uniprotAc)
    response = requests.get(url)
    if (not response == 200):
        return {"error":"MobiDB not available"}
    return _process_downloaded_Mobi_data(json.loads(response.text))


def source_Mobi(request, uniprotAc):
    method = {'full':'curated databases', 'missing_residues':'missing electron densities', 'bfactor':'high temperature residues', 'mobile':'backbone displacemen in NMR structures', 'mobi2':'Inferred from PDB structures' }
    source = {'db':'database','derived':'inferred'}
    data = _load_Mobi_from_DB(uniprotAc)
    # Remove unnecesary root list as ids must be unique in this table
    return HttpResponse(json.dumps(data[0]), content_type='application/json')