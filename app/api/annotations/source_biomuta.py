#! /usr/bin/env python3

import json

from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

from .models import biomutanentries


def source_Biomuta_from_uniprot(request, proteinID):
    query = None
    status = 200
    try:
        """
            Queries the database to get elements with the desired uniprotID
            Then turns it into a dict (to be able to be returned as json
            The behaviour varies depending on the query:
		    1 or more results -> returned in a dict
                - 0 results -> returns None
                - Error -> returns None and TODO: registers the error
	    """
        query = biomutanentries.objects.filter(proteinID=proteinID)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{proteinID} not found in DB"}
            status = 404
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
        status = 404
    #Returns a list of lists, as each id may have different hits in the db
    return  HttpResponse(json.dumps(query), content_type='application/json', status=status)