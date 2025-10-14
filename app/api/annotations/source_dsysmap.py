#! /usr/bin/env python3

import requests
import json
import datetime
import xml.etree.ElementTree as ET

from .models import dsysmapentries

from django.forms.models import model_to_dict
from django.http import HttpResponse

DsysmapURL = "https://dsysmap.irbbarcelona.org/api/getMutationsForProteins?protein_ids={}"
PATHOLOGY_TYPE = "Pathology and Biotech"

def _get_Dsys_data_fromDB(uniprotID):
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
        query = dsysmapentries.objects.filter(proteinID=uniprotID)
        print(query)
        query = [json.loads(model_to_dict(result)["data"]) for result in query]
	    # If no elements returned, then return None
        # None means no results, and downstream it will be handled
        # By connecting to the original database and caching the data locally
        if (len(query)) == 0: 
            query = {"error":f"{uniprotID} not found in DB"}
    except Exception as e:
        print(e)
        # Unexpected error while connecting to the cache DB 
        # Returning none to show no results could be retrieved
        query =  {"error":f"Error while connecting to DB"}
    finally:
        return query

def _save_Dsys_data_in_DB(uniprotID, data):
    Model = dsysmapentries()
    Model.proteinID = uniprotID
    Model.data = json.dumps(data)
    Model.created_at = datetime.datetime.now()
    Model.updated_at = datetime.datetime.now()
    Model.save()

def _get_Dsys_data_from_uniprot(uniprotID):
    """
        Dsysmap seems to have changed the API
    """
    url = DsysmapURL.format(uniprotID)
    response = requests.get(url) 
    rawdata = response.text
    code = response.status_code
    xml_data:ET = ET.fromstring(rawdata)
    if xml_data.find("error"):
        return xml_data, code
    return xml_data, code

def _process_xml_from_dsys_map(xml_data):
    results = []
    # Checking if needed subkey exist
    if ("results" in xml_data and 
        "mutations" in xml_data["results"] and
        "mutation" in xml_data["results"]["mutations"]):
        
        mutations = xml_data["results"]["mutations"]["mutation"]
        mutations = mutations if type(mutations) is list else [mutations]

        for mut in mutations:
            # Structures to store the data from parsing the result
            tmp = {}
            characters = []
            references = []
            # Check if each key exists. If it does, then save it into the tmp 
            if ("disease" in mut and "min" in mut): tmp["disease"] = {"text":mut["disease"], reference:mut["min"]}
            if ("phenotype" in mut): characters.append(f"Phenotype: {mut["phenotype"]}")
            if ("res_num" in mut):
                tmp["start"] = int(mut["res_num"])
                tmp["end"] = int(mut["res_num"])
                tmp["position"] = mut["res_num"]
            if ("res_orig" in mut): tmp["original"] = mut["res_orig"]
            if ("res_mut" in mut): tmp["variation"] = mut["res_mut"]
            if ("swissvar_id" in mut): references.append({"references":f"Swissvar:{mut["swissvar_id"]}"})
            if (references): tmp["evidence"] = references
            if (characters): tmp["description"] = ";;".join(characters)
            tmp["type"] = PATHOLOGY_TYPE
            results.append(tmp)
    return results
 
## API ENDPOINT
def source_Dsysmap_From_Uniprot(request, uniprotID):
    data = _get_Dsys_data_fromDB(uniprotID)
    if data is None:
        data, code = _get_Dsys_data_from_uniprot(uniprotID)
        print(data.text, code)
        # The API returns a XML with error if such things occur
        # Checking it to identify error
        #print(data.find("code").text)
        if data.tag == "error":
            print("error")
            return_data = {"code":data.find("code").text, "id":uniprotID, "message":f"Dsysmap API{data.find("message").text}" }
            data = json.dumps(return_data)
            return HttpResponse(data, 
                                content_type='application/json')
        else:
            # If no error, then we process it to get the desired data
            data = _process_xml_from_dsys_map(data)
        if len(data) > 0:
            _save_Dsys_data_in_DB(uniprotID, data)
    if ("error" in data):
        status_code = 404
    else:
        status_code = 200
        data = data[0] # Remove the root list because ids should be uniq in the table
    data = json.dumps(data) 
    return HttpResponse(data, content_type='application/json', status=status_code)