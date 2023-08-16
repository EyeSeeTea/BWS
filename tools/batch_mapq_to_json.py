"""
Passing EM Validations to JSON Data Format
"""
import argparse
import getopt
import os
import sys
import glob
from pathlib import Path
import time
import numpy
import json
from utils import *

DATA_PATH = "/data/q-score/emdb_qscores"
JSON_DATA_PATH = "../data/q-score/json"
# emd_26003_pdb_7tmw.cif
MAPQ_FILE_PATTERN = "emd_*_pdb_*.cif"

RESOURCE = "EMV-MapQ-Scores"


def getEntryFiles(path, filename_pattern):
    logger.info('Get MapQ files from %s' % (path, ))
    entry_data_list = []
    entry_list = []
    try:
        logger.info('Reading data folder:  %s %s' % (path, filename_pattern))
        search_path = os.path.join(path, "**", filename_pattern)
        logger.info('search_path  %s' % (search_path, ))
        data_files = glob.glob(search_path, recursive=True)

        for data_file in sorted(data_files):
            data_filename = os.path.basename(data_file)
            logger.info('Found data file:  %s' % (data_filename))
            # emd_26003_pdb_7tmw.cif
            data_filename = getFilename(data_file, withExt=False)
            emdb_prefix, emdb_entry_num, pdb_prefix, pdb_entry = data_filename.split(
                "_")
            emdb_entry = "emd-" + emdb_entry_num

            if not emdb_entry_num in entry_list:
                entry_data = {
                    "emdbId": emdb_entry,
                    "pdbId": pdb_entry,
                    "files": []
                }
                entry_data_list.append(entry_data)
                entry_list.append(emdb_entry_num)

            entry_data["files"].append(data_file)

    except (Exception) as exc:
        logger.error("--- ERROR: ", exc)

    return entry_list, entry_data_list


def getEmvDataHeader(emdbId, pdbId, proc_date):
    logger.info('Get EMV MapQ data header %s %s' % (emdbId, pdbId))

    emv_data = {}
    emv_data["resource"] = RESOURCE
    entry_data = {
        "atomicModel": emdbId,
        "atomicModel": pdbId,
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

    logger.debug('EMV MapQ data header %s %s %s' % (emdbId, pdbId, emv_data))
    return emv_data


def pdb2json(emdb_entry, pdb_entry, data_file):
    logger.info('Process data file %s ' % data_file)
    chains_data = []
    with open(data_file) as f:
        lines_data = f.readlines()

        chain_data = {}
        current_chain = ""
        chain_data["seqData"] = []
        current_residue = 0
        for line in lines_data:
            if (line.startswith('ATOM') or line.startswith('HETATM')):
                # read fields
                # 0....v...10....v...20....v...30....v...40....v...50....v...60....v...70....v...80
                # 0....v....|....v....|....v....|....v....|....v....|....v....|....v....|....v....|
                # ATOM 1    N N   . GLU A 1 399 ? 179.919 136.739 117.419 1.000 88.14  0.752039  0  400  GLU R N   1
                # ATOM 9    O OE2 . GLU A 1 399 ? 180.178 135.042 112.367 1.000 88.14  -0.139837 -1 400  GLU R OE2 1
                # ATOM 10   N N   . ASN A 1 400 ? 178.077 138.636 117.924 1.000 84.67  0.402624  0  401  ASN R N   1
                group_PDB, id, type_symbol, label_atom_id, label_alt_id, \
                    label_comp_id, label_asym_id, label_entity_id, \
                    label_seq_id, pdbx_PDB_ins_code, Cartn_x, Cartn_y, Cartn_z, occupancy, B_iso_or_equiv, \
                    score, pdbx_formal_charge, auth_seq_id, auth_comp_id, \
                    auth_asym_id, auth_atom_id, pdbx_PDB_model_num = line.split()

                # skip data for atoms in the same residue
                if current_residue == auth_seq_id:
                    continue

                residue_data = {
                    "resSeqName": auth_comp_id,
                    "resSeqNumber": auth_seq_id,
                    "scoreValue": score
                }
                chain_data["seqData"].append(residue_data)
                current_residue = auth_seq_id


                if current_chain != auth_asym_id:
                    if current_chain:
                        # save current chain data
                        chains_data.append(chain_data)

                    # start new chain data set
                    chain_data = {}
                    chain_data["name"] = auth_asym_id
                    chain_data["seqData"] = []
                    residue_data = {
                        "resSeqName": auth_comp_id,
                        "resSeqNumber": auth_seq_id,
                        "scoreValue": score
                    }
                    chain_data["seqData"].append(residue_data)
                    current_chain = auth_asym_id
        chains_data.append(chain_data)
    return chains_data


def getChainsData(data_files):
    chains_data = []

    for data_file in data_files:
        # emd_26003_pdb_7tmw.cif
        data_filename = os.path.basename(data_file)
        logger.info('Process MapQ data file %s ' % (data_filename))
        print('-- Process MapQ data file %s ' % (data_filename))
        emdb_prefix, emdb_entry_num, pdb_prefix, pdb_entry = data_filename.split(
            "_")
        emdb_entry = "emd-" + emdb_entry_num
        logger.info('Processing %s %s %s' %
                    (emdb_entry, pdb_entry, data_file))

        chains_data.append(pdb2json(emdb_entry, pdb_entry, data_file))

    return chains_data


def saveEmvData(emdbId, pdbId, emv_data):

    # emd-23530_7lv9_emv_aapq.json
    json_filename = emdbId.replace('-','_') + '_' + pdbId.lower() + '_emv_mapq.json'
    dirPath = Path(JSON_DATA_PATH)
    dirPath.mkdir(parents=True, exist_ok=True)
    json_file = dirPath.joinpath(json_filename)

    logger.info('Save EMV MapQ data %s %s %s %s' %
                (emdbId, pdbId, dirPath, json_filename))
    with open(str(json_file), "w+") as of:
        of.write(json.dumps(emv_data, indent=2))


def main(argv):

    parser = argparse.ArgumentParser(
        description="Prepare MapQ data from mmCiff file to JSON, batch mode")
    parser.add_argument("-i",
                        "--inputDir",
                        help="input data directory",
                        required=True)
    parser.add_argument(
        "-l",
        "--logFile",
        help="log file. By default 'prepareJob.log' in a dedicated 'logs' folder.",
        required=False)
    parser.add_argument("-t",
                        "--test",
                        help="perform a trial run with no changes made",
                        required=False,
                        action='store_true')
    args = parser.parse_args()
    if args.logFile:
        logFile = args.logFile
        logsDir = os.path.dirname(logFile)
        logFilename = os.path.basename(logFile)
    else:
        logsDir = PATH_TOOLS_DIR.joinpath(DIR_TOOLS_LOGS)
        logFilename = logsDir.joinpath(
            os.path.splitext(Path(__file__).name)[0] + '.log')
    logger = logSetup(__name__, logsDir, logFilename)
    test_only = args.test
    if test_only:
        logger.warning(
            'Performing a trial run. No permanent changes will be made')

    inputDir = args.inputDir

    logger.info('Reading MapQ scores from %s' % (inputDir, ))
    print('- Reading MapQ scores from %s' % (inputDir, ))
    entry_list, entry_data_list = getEntryFiles(inputDir, MAPQ_FILE_PATTERN)
    for entry in entry_data_list:
        emdbId = entry["emdbId"]
        pdbId = entry["pdbId"]
        files = entry["files"]

        proc_date = time.strftime('%Y-%m-%d',
                                  time.gmtime(os.path.getmtime(files[0])))

        emv_data = getEmvDataHeader(emdbId, pdbId, proc_date)

        chains_data = getChainsData(files)
        emv_data["chains"] = chains_data

        saveEmvData(emdbId, pdbId, emv_data)


if __name__ == '__main__':
    main(sys.argv[1:])
