#! /usr/bin/env python3

import json

from django.http import HttpResponse
from django.forms.models import model_to_dict

from .models import dbptmentries

## Endpoints for the /api/annotation/Dbptm/Uniprot/<id>
## This funcion is called when the API endpoint is hit
def source_Dbptm_from_Uniprot(request, uniprot_id):
    query = None
    status_code = 200
    try:
        """
            Queries the database to get elements with the desired uniprotID
            Then turns it into a dict (to be able to be returned as json
            The behaviour varies depending on the query:
		    1 or more results -> returned in a dict
                - 0 results -> returns None
                - Error -> returns None and TODO: registers the error
	    """
        query = dbptmentries.objects.filter(proteinID=uniprot_id)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
        print(query)
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{uniprot_id} not found in DB"}
            status_code = 404
        else:
            query = query[0] # Remove root list because protein ID should be unique in this table
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
        status_code = 404
    finally:
        return HttpResponse(json.dumps(query),content_type='application/json', status=status_code)