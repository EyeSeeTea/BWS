import getopt
import sys
import os
import csv
import requests
from datetime import datetime, timedelta
from rcsbsearch import rcsb_attributes as attrs

SCRIPT_NAME = os.path.basename(__file__)
WS_URL = "https://3dbionotes.cnb.csic.es/api/mappings/PDB/EMDB/"
PATH_DATA = "../data/updates"
FN_PDB_ENTRIES = "_new_PDB_entries_covid_noem.txt"
FN_EM_ENTRIES = "_new_PDB_entries_covid_em.txt"
FN_EMDB_PDB_ENTRIES = "_new_PDB_entries_covid_mappings.csv"
DAYS_INTERVAL = 7


def getCovidEntries(d1, interval, withEM=False):
    iso1 = d1.replace(microsecond=0).isoformat()

    d0 = d1 - timedelta(days=interval)
    iso0 = d0.replace(microsecond=0).isoformat()

    q1 = attrs.rcsb_entity_source_organism.taxonomy_lineage.name == "COVID-19 virus"
    q2 = attrs.rcsb_accession_info.initial_release_date >= str(iso0+'Z')
    q3 = attrs.rcsb_accession_info.initial_release_date <= str(iso1+'Z')
    q4 = attrs.rcsb_entry_info.experimental_method != "EM"
    q5 = attrs.rcsb_entry_info.experimental_method == "EM"
    query = q1 & q2 & q3
    if withEM:
        query = query & q5
    else:
        query = query & q4

    print(query)

    return list(query())


def save2file(list, filename):
    if list:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as filehandle:
            filehandle.writelines("%s\n" % entry for entry in list)


def save2csv(list, filename, delimiter='\t'):
    if list:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=delimiter)
            writer.writerows(list)


def getPdbMappings(entryList):
    emdbEntries = []
    for entry in entryList:
        response = requests.get(WS_URL + entry)
        if response.status_code == 200:
            jresp = response.json()
            emdbEntries.append((jresp[entry.lower()][0], entry.lower()))
    return emdbEntries


def main(argv):
    endDate = ''
    interval = ''
    try:
        opts, args = getopt.getopt(argv, 'hd:i:', ['endDate=', 'interval='])
    except getopt.GetoptError:
        print(SCRIPT_NAME, '-i <interval>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(SCRIPT_NAME, '-i <interval>')
            sys.exit()
        elif opt in ('-d', '--endDate'):
            endDate = datetime.strptime(arg, '%d/%m/%Y')
        elif opt in ('-i', '--interval'):
            interval = int(arg)

    if not endDate:
        endDate = datetime.today()
    if not interval:
        interval = DAYS_INTERVAL

    print('Get latest Covid Non EM-PDB Entries:', endDate, interval)
    noem_entries = getCovidEntries(endDate, interval, withEM=False)
    print("->", noem_entries)
    print(endDate.date().isoformat() + FN_PDB_ENTRIES)
    save2file(sorted(noem_entries), filename=os.path.join(
        PATH_DATA, endDate.date().isoformat() + FN_PDB_ENTRIES))

    print("Get latest Covid EM-PDB Entries",  endDate, interval)
    em_entries = getCovidEntries(endDate, interval, withEM=True)
    print("->", em_entries)
    save2file(sorted(em_entries), filename=os.path.join(
        PATH_DATA, endDate.date().isoformat() + FN_EM_ENTRIES))

    print("Get latest mappings EM-PDB",  endDate, interval)
    mappings = getPdbMappings(em_entries)
    print("", mappings)
    save2csv(mappings, filename=os.path.join(
        PATH_DATA, endDate.date().isoformat() + FN_EMDB_PDB_ENTRIES))


if __name__ == '__main__':
    main(sys.argv[1:])
