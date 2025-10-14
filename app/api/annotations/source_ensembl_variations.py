#! /usr/bin/env python3

## Function for annotations for:
# /api/annotation/ensembl/variantion/:name

import json
import requests

from django.http import HttpResponse
from django.forms.models import model_to_dict

from .models import EnsemblVariantEntry

def _load_variants_from_DB(id):
    query = []
    try:
        """
            Queries the database to get elements with the desired uniprotID
            Then turns it into a dict (to be able to be returned as json
            The behaviour varies depending on the query:
		    1 or more results -> returned in a dict
                - 0 results -> returns None
                - Error -> returns None and TODO: registers the error
	    """
        query = EnsemblVariantEntry.objects.filter(geneID=id)
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
    finally:
        return query

def getENSEMBLvariations(request, ensemblid):
    variants = _load_variants_from_DB(ensemblid)
    status_code = 404 if variants is [] or "error" in variants else 200
    return HttpResponse(json.dumps(variants),content_type='application/json', status=status_code)