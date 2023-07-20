"""
Passing EM Validations to JSON Data Format
"""
import getopt
import os
import sys
import glob
from pathlib import Path
import time
import numpy
import json

DATA_PATH = "/data/q-score/emdb_qscores"
JSON_DATA_PATH = "/data/q-score/json"
MAPQ_FILE_PATTERN = "emd_*_pdb_*.cif"

RESOURCE = "EMV-MapQ-Scores"


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def cif2json(emdb_entry, pdb_entry, input_file):

    emv_data = {}
    proc_date = time.strftime('%Y-%m-%d',
                              time.gmtime(os.path.getmtime(input_file)))
    emv_data["resource"] = RESOURCE
    entry_data = {
        "volume_map": emdb_entry,
        "atomic_model": pdb_entry,
        "date": proc_date
    }
    source_data = {
        "method": "MapQ - Q-score - Grigore Pintilie",
        "citation": "Pintilie, G. & Chiu, W. (2021). Validation, analysis and annotation of cryo-EM structures. Acta Cryst. D77, 1142–1152.",
        "doi": "doi:10.1107/S2059798321006069"
    }
    entry_data["source"] = source_data
    emv_data["entry"] = entry_data
    emv_data["chains"] = []

    with open(input_file) as f:
        lines_data = f.readlines()

        current_chain = ""
        current_residue = 0
        for line in lines_data:
            if (line.startswith('ATOM') or line.startswith('HETATM')):
                # read fields
                # ATOM   1     N  N     . ARG A 1 28  ? 196.425 215.363 143.820 1.000 159.66 0.508586  ? 28  ARG A N     1
                group_PDB, id, type_symbol, label_atom_id, label_alt_id, label_comp_id, label_asym_id, label_entity_id, label_seq_id, pdbx_PDB_ins_code, Cartn_x, Cartn_y, Cartn_z, occupancy, B_iso_or_equiv, q_score, pdbx_formal_charge, auth_seq_id, auth_comp_id, auth_asym_id, auth_atom_id, pdbx_PDB_model_num = line.split(
                )
                if not is_number(q_score):
                    continue
                q_score = float(q_score) if is_number(q_score) else ""

                # get data
                if current_residue != label_seq_id:

                    if current_residue:
                        # save current residue data
                        res_values.append(q_score)
                        mean_score = numpy.mean(res_values)
                        residue_data["scoreValue"] = ' {0:.4f}'.format(
                            mean_score)
                        chain_data["seqData"].append(residue_data)

                    # start new residue data set
                    res_values = []
                    residue_data = {
                        "resSeqName": label_comp_id,
                        "resSeqNumber": label_seq_id,
                    }
                    current_residue = label_seq_id
                else:
                    res_values.append(q_score)

                # get chain
                if current_chain != label_asym_id or line == lines_data[-1]:
                    if current_chain:
                        # save current chain
                        emv_data["chains"].append(chain_data)

                    # start new chain data set
                    chain_data = {}
                    chain_data["name"] = label_asym_id
                    chain_data["seqData"] = []
                    current_chain = label_asym_id
    return emv_data


def read_em_validations(path):
    """
    Read EM Validations
    """
    print('-- Reading EM Validations from', path)

    try:
        print("--- Reading data folder: ", path, MAPQ_FILE_PATTERN)
        search_path = os.path.join(path, MAPQ_FILE_PATTERN)
        data_files = glob.glob(search_path, recursive=True)
    except (Exception) as exc:
        print("--- ERROR: ", exc)

    if data_files:
        for data_file in data_files:
            filename = Path(data_file).stem
            name_parts = filename.split("_")
            emdbId = name_parts[0].upper() + "-" + name_parts[1]
            pdbId = name_parts[3]
            path = os.path.dirname(data_file)
            print("---- Data-File:", path, filename)

            # emd-0001_6gh5_emv_mapq.json
            json_filename = filename + '_emv_mapq.json'
            dirPath = Path(JSON_DATA_PATH)
            dirPath.mkdir(parents=True, exist_ok=True)
            json_file = os.path.join(JSON_DATA_PATH, json_filename)
            print("---- JSON-File:", JSON_DATA_PATH, json_filename)

            jdata = cif2json(emdbId, pdbId, data_file)
            print("-- Writing", json_file)
            with open(json_file, "w+") as of:
                of.write(json.dumps(jdata, indent=2))


def main(argv):
    path = ''
    try:
        opts, args = getopt.getopt(argv, 'hp:', [
            'path=',
        ])
    except getopt.GetoptError:
        print(__name__, ' -p <path>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(__name__, ' -p <path>')
            sys.exit()
        elif opt in ('-p', '--path'):
            path = arg

    if not path:
        path = DATA_PATH

    print('Passing EM Validations to JSON Data Format')
    print("- Processing", path)
    read_em_validations(path)


if __name__ == '__main__':
    main(sys.argv[1:])
