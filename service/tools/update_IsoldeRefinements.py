import csv
import json
import sys
from utils import *

DATA_PATH = '../data'
TOOLS_PATH = 'tools'

# https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/nsp3/SARS-CoV-2/6vxs/isolde
CSTF_GITHUB_URL = "https://github.com/thorn-lab/coronavirus_structural_task_force/tree/master/pdb/"
# https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/isolde_refinements.txt
CSTF_GITHUB_RAW_URL = "https://raw.githubusercontent.com/thorn-lab/coronavirus_structural_task_force/master/pdb/"
ISOLDE_REF_FNAME = "isolde_refinements.txt"
ISOLDE_JSON_FNAME = "isolde_entries.json"
CSTF_LOCAL_PATH = DATA_PATH + "/" + "cstf"
ISOLDE_LOCAL_DATA_PATH = CSTF_LOCAL_PATH + "/" + "isolde"


def main(argv):

    url = CSTF_GITHUB_RAW_URL + ISOLDE_REF_FNAME
    print("- download Isolde entries list:", url)
    list_file = download_file(url, CSTF_LOCAL_PATH)

    entries = []
    print("- parse Isolde entries list:", list_file)
    with open(list_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            entries.append({"pdbId": line.split(
                '/')[-2], "path": line.removeprefix('./').strip()})
        print("-- found", len(entries), "entries")
        # print(json.dumps(entries, indent=2))

    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        print("-- get Isolde refinements for", pdb_id, remote_path)
        filenames = getRemoteFileList(url, ".pdb")
        if not filenames:
            filenames = getRemoteFileList(url, ".cif")
        for filename in filenames:
            if filename.startswith(pdb_id):
                filename = filenames[len(filenames)-1]
                print("--- found", len(filenames), "refinements: ", filename)
                entry.update({"filename": filename})
                entry.update({"refmodels": [{
                    "method": "Isolde",
                    "externalLink": url,
                    "queryLink": "https://3dbionotes.cnb.csic.es/isolde/%s/%s" % (pdb_id, filename)
                }]})

    print("-- save Isolde data (JSON):", CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    save_json(entries, CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)

    for entry in entries:
        if "filename" in entry:
            filename = entry["filename"]
            pdb_id = entry["pdbId"]
            url = os.path.join(CSTF_GITHUB_URL, entry["path"], filename)
            print("-- dowload Isolde refinements for",
                  pdb_id, entry["path"], filename)
            download_file(url, os.path.join(
                ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3]))


if __name__ == '__main__':
    main(sys.argv[1:])
