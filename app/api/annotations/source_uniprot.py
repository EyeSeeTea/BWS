#! /usr/bin/env python3

import json
import requests

from django.http import HttpResponse

error = "The 'accession' value has invalid format. It should be a valid UniProtKB accession"
UNIPROT_URL:str = "https://rest.uniprot.org/uniprotkb/{}.fasta"
UNIPROT_URL_ID:str = "https://rest.uniprot.org/uniprotkb/{}"

def get_uniprot_sequence(uniprotAc):
    url = UNIPROT_URL.format(uniprotAc)
    data = requests.get(url).text
    data = data.split("\n")[1:] # Ignore header
    return "".join(data)

####################
#                  #
#   API ENDPOINTS  #
#                  #
####################

def get_uniprot_length(request, uniprotAc):
    seq = get_uniprot_sequence(uniprotAc)
    if (seq == error):
        toreturn = json.dumps([{"error": f"invalid accession number {uniprotAc}"}])
        status = 404
    else:
        toreturn = json.dumps([{"length": len(seq)}])
        status = 200
    return HttpResponse(toreturn, content_type='application/json', status_code=status)

def fetch_uniprot_multiple_sequences(request, uniprotAcs,sep=","):
    return_values = {}
    ids = uniprotAcs.split(sep)
    print(ids)
    for id in ids:
        url = UNIPROT_URL_ID.format(id)
        response = requests.get(url)
        if (response.status_code == 404):
            # Comentar en el informe 
            # Para ser coherente, si una proteina no es encontrada en uniprot, no la guarda
            # Si ninguna es válida, devuelve un [] con código 404
            continue
        data = json.loads(response.text)
        if ("sequence" in data and "length" in data["sequence"]):
            length = data["sequence"]["length"]
        else:
            length = 0
        if ("organism" in data and "scientificName" in data["organism"]):
            organism = data["organism"]["scientificName"]
        else:
            organism = "UNK ORG"
        if ("genes" in data):
            gene = data["genes"][0]["geneName"]["value"]
        else:
            gene = "N/A"
        if ("proteinDescription" in data and "recommendedName" in data["proteinDescription"]):
            name = data["proteinDescription"]["recommendedName"]["fullName"]["value"]
        else:
            name = "obsolete protein?"
        return_values[id] = [length, name, gene, organism]
    if (len(return_values)) == 0:
        return HttpResponse(json.dumps([]), content_type='application/json', status_code=404)    
    return HttpResponse(json.dumps(return_values), content_type='application/json')

