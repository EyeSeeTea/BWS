#! /usr/bin/env python3

import json
import subprocess

from django.http import HttpResponse
from django.forms.models import model_to_dict

from .models import ElmdbData

ELM_SCRIPT = "/services/bionotes/apps/ELMDB/get_elm_data"

def _get_ELM_from_script(uniprotID):
    return subprocess.check_output([ELM_SCRIPT, uniprotID]).decode("utf-8")

def _load_ELM_from_DB(uniprotID):
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
        query = ElmdbData.objects.filter(uniprotID=uniprotID)
        if (not query): 
            query = {"error": f"{uniprotID} not found in DB"}
            return query
        query = [model_to_dict(result)["data"] for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally

    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
    finally:
        return query

def source_ELMDB(request, uniprotID):
    data = _load_ELM_from_DB(uniprotID)
    status = 200
    if ("error" in data):
        # Get the necessary data from the script
        # As is not available in DB
        try:
            scripted_data = _get_ELM_from_script(uniprotID)
        except FileNotFoundError as FNFE:
            # This endpoint depends on a script available in ELM_SCRIPT path
            scripted_data = {"error": "ELM script not found at {}".format(ELM_SCRIPT)}
            status = 404
        if (scripted_data and "error" not in scripted_data):
            data = json.dumps(scripted_data)
        if ("error" in data):
            status = 404
            print(scripted_data)
            data = json.dumps(scripted_data)
    return HttpResponse(data, 
                        content_type='application/json',
                        status=status)
