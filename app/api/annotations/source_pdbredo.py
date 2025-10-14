#! /usr/bin/env python3

# This files contains the code for the PDB_REDO API entrypoint

import json
import re
import requests
import pdb

from collections import defaultdict
from django.http import HttpResponse

from .models import PDBRedoEntry, PdbDatum
from django.forms.models import model_to_dict


##############################
#       Constants            #
##############################

PDB_REDO_URL:str = "https://pdb-redo.eu/db/"
LOCALPATH:str = "/tmp"
EVIDENCES_TEMPLATE:str = "{'Imported information':[{url:'https://pdb-redo.eu/db/'+{pdbId}, 'id':{pdbId}, name:'Imported from PDB_REDO'}]}"
H_BOND_DESCRIPTION:str = "H-bond flip in PDB_REDO model"
ROTAMER_DESCRIPTION:str = "Rotamer changes in PDB_REDO model"
COMPLETED_DESCRIPTION:str = "Completed residue in PDB_REDO model"
COMPLETED_LOOP_DESCRIPTION:str = "Completed loop in PDB_REDO model"

##############################
# Routines to get/save info #
##############################

def _load_PDBRedo_from_DB(id):
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
        query = PDBRedoEntry.objects.filter(PDBID=id)
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


def _download_PDBRedo(id, PDBdata):
    url = f"{PDB_REDO_URL}{id.lower()}/{id.lower()}_final.py"
    try:
        session = requests.get(url)
        data = session.content.decode("utf-8")
    # TO DO: Handle network errors
    # For now, just ignore everything and return empty dict, just as if we could not get the data
    except Exception as e:
        print(e)
        print(f"Error downloading: {url}")
        return {}
    # The original code in ruby is:
    # data = data.chop.chop.chop.chop.chop.split("\n")
    # data.shift(3)
    # Which if I understand correctly is eliminate the last 5 characters, then split and keep only 
    # the first three elements
    # This can be summarized to this line. It needs review:
    pdb_py = data[:-5].split("\n")[4:]
    PDB = json.loads(f"[{"".join(pdb_py)}]")
    print(PDB)
    out = defaultdict(list) # if accessing with a key not present, by default it will be an empty list
    for line in PDB:
        print(line)
        x = line[0] 
        re_match_cond_1 = re.match(r'^(H\-bond\sflip)(\s+)(\w+)(\s+)(\w+)(\s+)(\w+)', x)
        re_match_cond_2 = re.match(r'^(Changed\srotamer)(\s+)(\w+)(\s+)(\w+)(\s+)(\w+)', x)
        re_match_cond_3 = re.match(r'^(Completed)(\s+)(\w+)(\s+)(\w+)(\s+)(\w+)',x)
        re_match_cond_4 = re.match(r'^(Added\sloop)(\s+)(\w+)(\s+)(\w+)(\s+)(\w+)(\s+\-)(\w+)(\s+)(\w+)(\s+)(\w+)',x)
        if (re_match_cond_1):
            #    Regular expressions 1 to 3 follow the same code and thus have been summarized into 
            #    the _parse_PDBredo_downloaded_file function
            if (re_match_cond_1.group(5) in PDBdata.keys()):
                pdbredo_results = _parse_PDBredo_downloaded_file(PDB,re_match_cond_1,  H_BOND_DESCRIPTION,'h_bond_flip', 
                                                                    EVIDENCES_TEMPLATE.format(pdbId=id))
                if (pdbredo_results['begin'] > 0):
                    out[ch].append(pdbredo_results)
        elif (re_match_cond_2):
            if (re_match_cond_2.group(5) in PDBdata.keys()):
                pdbredo_results = _parse_PDBredo_downloaded_file(PDB,re_match_cond_2,  ROTAMER_DESCRIPTION,'changed_rotamer', 
                                                                   EVIDENCES_TEMPLATE.format(pdbId=id))
                if (pdbredo_results['begin'] > 0):
                    out[ch].append(pdbredo_results)
        elif (re_match_cond_3):
            if (re_match_cond_3.group(5) in PDBdata.keys()):
                pdbredo_results =  _parse_PDBredo_downloaded_file(PDB,re_match_cond_3,  COMPLETED_DESCRIPTION,'completed_res', 
                                                                   EVIDENCES_TEMPLATE.format(pdbId=id))
                if (pdbredo_results['begin'] > 0):
                    out[ch].append(pdbredo_results)
        elif (re_match_cond_4):
            # This section may need to do some refactoring to improve readability
            # TO DO: Clean up nested elements
            if (re_match_cond_4.group(5) in PDBdata.keys()):
                ch_1 = re_match.group(5)
                ch_2 = re_match.group(11)
                acc = PDBdata[ch].keys()[0]
                start = PDBdata[ch_1][acc]['inverse'][str(int(re_match_cond_4.group(7))+1)]+1
                end = PDBdata[ch_1][acc]['inverse'][str(int(re_match_cond_4.group(13))+1)]+1
                if (ch_1 == ch_2) and (start > 0) and (end > 0):
                    out[ch_1].append({'begin':start, 'end': start, 'type': "completed_loop", 
                    'descrption':COMPLETED_LOOP_DESCRIPTION, 'evidences':EVIDENCES_TEMPLATE.format(id)})
        out = json.dumps(out)
    pass

def _get_PDBData(id):
    """
        Loads the Data for a given PDB from a file stored in local storage

        Which file is loaded depends on the ID of the PDB

        If starts with pdb_redo_ followed by a 3-letter string, then is {LOCALPATH}/{id}/alignment.json
        elif is 3-letter string followed by _final.pdb, then is {LOCALPATH}/pdb_redo_{id}/alignment.json
        elif is 3-letter string, then it gets the data from the DB
        Any other case returns None

    """
    PDBData = {}
    if (re.match(r'^(pdb_redo_)(\d\w{3})', id)):
        print("MATCHED: get_PDBData")
        filepath = f"{LOCALPATH}/{id}/alignment.json"
        if(os.path.exists(filepath)):
            with open(filepath) as fh:
                PDBData = json.load(fh)
                PDBData = PDBData[f'{id}_final.pdb']
    elif (re.match(r'(\d\w{3})(_final.pdb)', id)):
        filepath = f"{LOCALPATH}/pdb_redo_{id}/alignment.json"
        if(os.path.exists(filepath)):
            with open(filepath) as fh:
                PDBData = json.load(fh)
                PDBData = PDBData[f'{id}_final.pdb']
    elif (len(id) == 3):
        Datum = PdbDatum.objects.get(ProteinID = id)
        if (not Datum is None):
            PDBData = json.loads(Datum["data"])
    return PDBData

##############################
#     Helper functions       #
##############################

def _parse_PDBID(ID):
    """
        Parse the PDB ID given to remove the _final_dot_pdb and get the ID
        Using a regular expression to check:
            - That there is a 4-letter length word, followed by
            - _final_dot_pdb literal string
        Discard the literal string and keep the 4-letter ID
    """
    PDB_ID = ID
    pattern = r'(\w{4})(_final_dot_pdb)'
    re_match = re.match(pattern, ID)
    if (re_match):
        PDB_ID = re_match.group(1)
    return PDB_ID

def _parse_PDBredo_downloaded_file(pdb_data, re_match, description, 
                                    type, evidences) -> dict:
    ch = re_match.group(5)
    acc = PDBdata[ch].keys()[0]
    index = PDBdata[ch][acc]['inverse'][re_match.group(7)]
    return {'begin':index, 'end': index, 'type': type, 
                    'descrption':descrption, 'evidences':evidences}


###############################
#        API endpoint         #
###############################
def source_PDBredo(request, pdbID):
    # First, we have to clean the ID and get associated data
    # - Get the 4 letter ID from the pdbID in case the pdb holds more info
    # - Load data from DB if it exists (if not, it will be handled later)
    # Then we use that ID to get the PDBdata and PDBredo from DB
    PDB = _parse_PDBID(pdbID)
    print(PDB)
    out = _load_PDBRedo_from_DB(PDB)
    print(out)
    PDBdata = _get_PDBData(PDB)
    print(PDBdata)
    # This three elements (PDB, out and PDBdata) represent all the elements we need
    # to get the annotations from the local filesystem:
    #   - If out is None (meaning info is not cached), but PDBdata has info and the ID is 3 letter length
    #     we connect to an url to download the data using the PDBData and ID
    print(re.match(r'^(\d\w{3})$', PDB))
    if (out is None) and (PDBdata is None) and (re.match(r'^(\d\w{3})$', PDB)):
        out = _download_PDBRedo(PDB, PDBdata)
    #    - Else, if ID hast 4 letter length and out has info on it, then we use the out info
    elif (re.match(r'^(\w{4})', PDB)) and (not out is None):
        out = out
    #    - Else, we return empty data info
    else:
        out = {"error":f"{pdbID} not found in database"}
    status_code = 404 if "error" in out else 200
    return HttpResponse(json.dumps(out),content_type='application/json', status=status_code)