#! /usr/bin/env python3

## Not to be used as the external db dependant has changed

import json
import requests

from .models import InterproDatum
from django.http import HttpResponse

def _filter_downloaded_interpro(line):
    return "/interpro/popup/supermatch" in line


interpro_URL = "http://www.ebi.ac.uk/interpro/protein/{}"

def create_InterproDatum(id, data):
    pass

def read_InterproDatum(uniprotAc):
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
        query = InterproDatum.objects.filter(proteinId=uniprotAc)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{uniprotAc} not found in DB"}
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
    return  query

def download_from_interpro(uniprotAc):
    ### API changed and info is unavailable
    ###
    url = URL.format(uniprotAc)
    data = requests.get(url).text.split("\n")
    result = []
    for line in filter(_filter_downloaded_interpro, data):
        pass
    pass

def source_Interpro_from_Uniprot(request, uniprotAc):
    data = read_InterproDatum(uniprotAc)
    if data is None:
        data = download_from_interpro(uniprotAc)
        if len(data) > 0: 
            create_InterproDatum(uniprotAc, data)
    
    return HttpResponse(json.dumps(data), content_type='application/json')
