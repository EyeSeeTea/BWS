"""
    Get PDB entry files for a list read from a file
    Saves all files (mmCiff by default) to a given dir

"""
import getopt
import getopt
import sys
import os
import urllib
from Bio.PDB import *


SCRIPT_NAME = os.path.basename(__file__)
WS_PDB_FITTING_URL = "https://3dbionotes.cnb.csic.es/api/mappings/PDB/EMDB/"
WS_EMDB_FITTING_URL = "https://3dbionotes.cnb.csic.es/api/mappings/EMDB/PDB/"
URL_PDBE = "https://www.ebi.ac.uk/pdbe/entry-files/download/"
URL_RCSB = "https://files.rcsb.org/download/"


def readIdsFromFile(filename):
    ids = []
    with open(filename, 'r') as fh:
        for line in fh:
            ids.append(line.strip())
    return ids


def downloadFile(pdbcode, datadir, file_format="pdb"):
    """
    Downloads a PDB file from the Internet and saves it in a data directory.
    :param pdbcode: The standard PDB ID e.g. '3ICB' or '3icb'
    :param datadir: The directory where the downloaded file will be saved
    :param downloadurl: The base PDB download URL, cf.
        `https://www.rcsb.org/pages/download/http#structures` for details
    :return: the full path to the downloaded PDB file or None if something went wrong
    """

    if file_format == "pdb":
        urlPath = URL_RCSB
        pdbfn = pdbcode + ".pdb"
    elif file_format == "cif":
        urlPath = URL_RCSB
        pdbfn = pdbcode + ".cif"
    elif file_format == "ent":
        urlPath = URL_PDBE
        pdbfn = "pdb" + pdbcode + ".ent"

    os.makedirs(datadir, exist_ok=True)
    outfnm = os.path.join(datadir, pdbfn)
    if os.path.isfile(outfnm):
        print("Skip", pdbcode, "Found", outfnm)
        return

    url = urlPath + pdbfn
    print('Downloading', pdbfn, url, outfnm)
    try:
        urllib.request.urlretrieve(url, outfnm)
        return outfnm
    except Exception as err:
        print(str(err), file=sys.stderr)
        return None


def getFiles(pdbIds, outputdir):
    for pdbId in pdbIds:
        pdbId = pdbId.lower()
        datadir = os.path.join(outputdir)
        # datadir = os.path.join(outputdir, pdbId[1:3])
        # downloadFile(pdbId, datadir, file_format="cif")
        # if not downloadFile(pdbId, datadir, file_format="ent"):
        #     downloadFile(pdbId, datadir, file_format="pdb")

        pdbl = PDBList()
        pdbl.retrieve_pdb_file(pdb_code=pdbId, pdir=datadir)
        # break


def main(argv):
    inputfile = ''
    outputdir = ''
    helpmsg = '-i <inputfile>, -o <outputdir>'
    examplemsg = '-i 2022-02-15_new_PDB_entries_covid_noem.txt -o -o ../data/covid'
    try:
        opts, args = getopt.getopt(argv, 'hi:o:', ['inputfile=', 'outputdir='])
    except getopt.GetoptError:
        print(SCRIPT_NAME, helpmsg)
        sys.exit(1)
    for opt, arg in opts:
        if opt == '-h':
            print(SCRIPT_NAME, helpmsg)
            print(SCRIPT_NAME, examplemsg)
            sys.exit()
        elif opt in ('-i', '--inputfile'):
            inputfile = arg
        elif opt in ('-o', '--outputdir'):
            outputdir = arg

    if not inputfile:
        print(SCRIPT_NAME, helpmsg)
        print(SCRIPT_NAME, examplemsg)
        sys.exit(2)
    if not outputdir:
        print(SCRIPT_NAME, helpmsg)
        print(SCRIPT_NAME, examplemsg)
        sys.exit(2)

    pdbIds = readIdsFromFile(filename=inputfile)
    print("All Id's")
    print(pdbIds, len(pdbIds))

    getFiles(pdbIds, outputdir)


if __name__ == '__main__':
    main(sys.argv[1:])
