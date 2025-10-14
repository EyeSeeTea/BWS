#! /usr/bin/env python3

# Original Ruby script https://github.com/3dbionotes-community/3DBIONOTES/blob/master/app/lib/annotation_manager/source_protein_data/source_smart.rb
# Original author: 3DBionotes team
# Python refactoring author: Fabián Robledo -> fabian.robledo@csic.es

import json
import re
import requests
import logging

from django.http import HttpResponse
from django.forms.models import model_to_dict

from .models import SMARTentity


SMART_URL:str = "http://smart.embl.de/smart/batch.pl?TEXTONLY=1&INCLUDE_SIGNALP=1&IDS={}"
#logging.basicConfig(filename='/sys/stdout', level=logging.INFO)

def _create_instace_of_SMARTentity(data: dict) -> SMARTentity:
    """
        Creates an instance of the model to save in the database
        Only uses required fields for the db.
    """
    smart =  SMARTentity()
    smart.start = data["start"]
    smart.end = data["end"]
    smart.evalue = data["evalue"]
    smart.uniprotid = data["uniprotid"]
    smart.domain = data["domain"]
    smart.type = data["type"]
    return smart

### Api function for the /api/annotation/SMART endpoints
def _load_smart_from_db(uniprotAC:str) -> list[dict]:
    """
	Tries to load elements in the database associated with
        uniprotAC. Returns a List with all annotations fount

        Returns None if no elements found
    """
    query = []
    try:
        """
           Queries the database to get elements with the desired uniprotID
           Then turns it into a dict (to be able to be returned as json
           The behaviour varies depending on the query:
		- 1 or more results -> returned in a dict
                - 0 results -> returns None
                - Error -> returns None and TODO: registers the error
	"""
        query = SMARTentity.objects.filter(uniprotid=uniprotAC)
        query = [model_to_dict(result) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = None
    except Exception as e:
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query = None
    finally:
        return query

def download_smart_from_embl(uniprotAc:str) -> list:
    """
	Connects to SMART to get the data for the uniprotAC ID given

        Input:
         - uniprotAc: Protein ID from Uniprot
        Output:
         - out: A list containing the data, each element being on
    """
    sm_url:str = SMART_URL.format(uniprotAc)
    response = requests.get(sm_url)
    # if status == 200, ok, 
    ann = []
    if (response.status_code == 200):
        data = response.content.decode("utf-8").split("\n")
        # Data return contains "\n\n" pairs. Turning them into just "\n" to split and
        # leave no empty lines
        # Itering over the data
        domain = ""
        content = iter(data) # Turning it into an iterator to use next()
        for line in content:
            if line.startswith("DOMAIN"):
                registry = {}
                while(line):
                    # Results are separed by a blank line
                    # Therefore, when line is empty, it means a registry has finished
                    # Saving all elements parsed into a dict
                    elements = line.split("=")
                    registry[elements[0].lower()] = elements[1]
                    line = next(content)
                registry["uniprotid"] = uniprotAc # To be able to query it later
                # If status is not visible, then we don't register it
                # To Do: ask if someone knows why
                # (would not bet on in, the script is 7 years old)
                # Visible is represented as "visible|OK" so we need to split it by |
                if (registry["status"].split("|")[0] == "visible"):
                    ann.append(registry)
    return ann

def save_result_into_DB(out):
    """
	Saves the results gotten from the external DB into de cache DB using the SMARTentity model

    The data is cached once and then served to the user.
    """
    for element in out:
        smart = _create_instace_of_SMARTentity(element)
        smart.save()
    pass

def sourceSmartFromUniprot(request, uniprotAc):
   """
      This function is called when /api/annotation/SMART/Uniprot/:name is accessed

      Tries to load the data from the database. If not present, will download it from SMART EMBL website, 
      and then cache it in the database

      If there's data in either the db or the webpage.
      In either cases, data is returnd formatted in json. 
      Else, returns an json file with an empty array
   """
   out =  _load_smart_from_db(uniprotAc)
   # If no elements are cached in the DB, then connects to the original DB
   # and saves the values returned into de cache DB
   # Note that if for some reason could not connect to the cache DB for read
   # But then can connect for write, duplicate elements might be recorded
   # Generally, if cached, it will take the info and not connect remotely
   # If not cached, will get the info from the remote db
   if out is None:
      out = download_smart_from_embl(uniprotAc)
      save_result_into_DB(out)
   if len(out) == 0:
       # No data neither in database or in the service. Send nothing
       warn = []
       return HttpResponse(json.dumps(warn), content_type='application/json', status=404)
   return HttpResponse(json.dumps(out), 
                         content_type='application/json')
