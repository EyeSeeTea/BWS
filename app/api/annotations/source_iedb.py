#! /usr/bin/env python3

###############################################
#                                             #
# Makes a SQL query directly to the database  #
# To get the joined data                      #
#                                             #
###############################################

import json

from django.db import connection
from django.http import HttpResponse

QUERY = "select distinct e.epitope_id, ee.linear_peptide_seq, o.starting_position, \
            o.ending_position from annotations_epitope ee, annotations_epitope_object e, \
            annotations_object o where ee.epitope_id=e.epitope_id and \
            e.object_id=o.object_id and e.source_antigen_accession in (\"{uniprotAc}\",\"{uniprotAc}.1\") and o.object_type = \"Fragment of a Natural Sequence Molecule\";"
    

def source_IEDB_from_DB(request, proteinID):
    data = list()
    with connection.cursor() as cursor:
        cursor.execute(QUERY.format(uniprotAc=proteinID))
        row = cursor.fetchall()
    for element in row:
        data.append({ 'start':row['starting_position'],'end':row['ending_position'],'type':'epitope','description':row['linear_peptide_seq'],'evidence':row['epitope_id']})
    status_code = 200 if (data) else 404
    return HttpResponse(json.dumps(data), content_type='application/json', status=status_code)
    