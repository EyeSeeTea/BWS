import getopt
from importlib.resources import path
import sys
from utils import *

DATA_PATH = '../data'
TOOLS_PATH = 'tools'

BIONOTES_QUERY_URL = "https://3dbionotes.cnb.csic.es/isolde"
# https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/nsp3/SARS-CoV-2/6vxs/isolde
CSTF_GITHUB_URL = "https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/"
# https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/isolde_refinements.txt
CSTF_GITHUB_RAW_URL = "https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/"
ISOLDE_REF_FNAME = "isolde_refinements.txt"
ISOLDE_JSON_FNAME = "isolde_entries.json"
CSTF_LOCAL_PATH = DATA_PATH + "/" + "cstf"
ISOLDE_LOCAL_DATA_PATH = CSTF_LOCAL_PATH + "/" + "isolde"


def main(argv):
    scriptname = os.path.basename(sys.argv[0])
    inputfile = ''
    try:
        opts, args = getopt.getopt(
            argv, 'hi:', ['inputfile=', ])
    except getopt.GetoptError:
        print(scriptname, '-i <inputfile>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(scriptname, '-i <inputfile>')
            sys.exit()
        elif opt in ('-i', '--inputfile'):
            inputfile = arg

    if not inputfile:
        url = CSTF_GITHUB_RAW_URL + ISOLDE_REF_FNAME
        print("- download Isolde entries list:", url)
        inputfile = download_file(url, CSTF_LOCAL_PATH)

    entries = []
    print("- parse Isolde entry list:", inputfile)
    parseIsoldeEntryList(inputfile, entries)

    print("- get Isolde refinement data")
    getIsoldeRefinementData(entries)

    print("-- save Isolde data (JSON):", CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    save_json(entries, CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)

    print("-- get Isolde refined model")
    getIsoldeRefinedModel(entries)

    print("-- get all files in Isolde data folder")
    getAllIsoldeDataFiles(entries, [".txt", ".mtz", ".cif"])


def parseIsoldeEntryList(inputfile, entries):
    with open(inputfile, 'r') as f:
        lines = f.readlines()
        for line in lines:
            # skip empty lines
            line = line.strip()
            # skip ./ at the begining of the line
            line = line.removeprefix('./')
            # skip pdb/ at the begining of the line
            line = line.removeprefix('pdb/')
            entries.append({"pdbId": line.split('/')[-2],
                            "path": line})
        print("-- found", len(entries), "entries")


def getIsoldeRefinedModel(entries):
    for entry in entries:
        if "filename" in entry:
            filename = entry["filename"]
            pdb_id = entry["pdbId"]
            url = os.path.join(CSTF_GITHUB_RAW_URL, entry["path"], filename)
            print("--- dowload Isolde refinements for",
                  pdb_id, entry["path"], filename)
            download_file(url, os.path.join(
                ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3], pdb_id))


def getIsoldeRefinementData(entries):
    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        print("-- get Isolde refinements for", pdb_id, remote_path)
        filenames = getGitHubFileList(url, ".pdb")
        if not filenames:
            filenames = getGitHubFileList(url, ".cif")
        for filename in filenames:
            if filename.startswith(pdb_id):
                filename = filenames[len(filenames)-1]
                print("--- found", len(filenames), "refinements: ", filename)
                entry.update({"filename": filename})
                entry.update({"refmodels": [{
                    "method": "Isolde",
                    "externalLink": url,
                    "queryLink": "%s/%s/%s" % (BIONOTES_QUERY_URL, pdb_id, filename)
                }]})


def getAllIsoldeDataFiles(entries, exts=["txt"]):
    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        url_raw = os.path.join(CSTF_GITHUB_RAW_URL, remote_path)
        print("--- get all Isolde refinement files for", pdb_id, remote_path)
        for ext in [".txt", ".mtz", ".cif"]:
            filenames = getGitHubFileList(url, ext)
            for filename in filenames:
                download_file(os.path.join(url_raw, filename), os.path.join(
                    ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3], pdb_id))


if __name__ == '__main__':
    main(sys.argv[1:])
