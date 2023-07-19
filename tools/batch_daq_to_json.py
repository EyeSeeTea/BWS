#!/usr/bin/env python
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

# /data/daq/data_20230426/aa/a0
DATA_PATH = "/data/daq/data_20230426/aa"
JSON_DATA_PATH = "/data/daq/json"
JSON_DATA_PATH = "../data/daq/json"
# 2981_5a0q_a_v1-1_w9.pdb
MAPQ_FILE_PATTERN = "*.pdb"

RESOURCE = "EMV-DAQ-Scores"


def pdb2json(emdb_entry, pdb_entry, chainId, input_file):

    with open(input_file) as f:
        lines_data = f.readlines()

        # there is only one chain per file
        # save current chain
        chain_data = {}
        chain_data["name"] = chainId
        chain_data["seqData"] = []

        current_residue = 0
        for line in lines_data:
            if (line.startswith('ATOM') or line.startswith('HETATM')):
                # read fields
                # 0....v...10....v...20....v...30....v...40....v...50....v...60....v...70....v...80
                # 0....v....|....v....|....v....|....v....|....v....|....v....|....v....|....v....|
                # ATOM      1  N   ASN a   8      25.537   3.945 -10.152  1.00 -0.01           N
                # ATOM      2  CA  ASN a   8      26.474   5.086 -10.154  1.00 -0.01           C
                # ATOM      3  C   ASN a   8      26.925   5.322  -8.740  1.00 -0.01           C
                # ATOM      4  O   ASN a   8      26.182   5.070  -7.789  1.00 -0.01           O
                # ATOM      6  CG  ASN S  13      12.406  59.933  -5.158  1.00  0.40           C
                # ATOM      7  OD1 ASN S  13      12.478  58.711  -5.318  1.00  0.40           O
                # ATOM      8  ND2 ASN S  13      12.017  60.804  -6.138  1.00  0.40           N
                # ATOM      9  N   THR S  14      14.666  63.074  -4.407  1.00  0.18           N
                # ATOM     10  CA  THR S  14      15.054  64.129  -5.275  1.00  0.18           C
                group_PDB = line[:4]
                atom_id = line[5:11]
                atom_symbol = line[13:16]
                label_comp_id = line[17:20]
                label_asym_id = line[21:23]
                label_seq_id = line[23:26]
                Cartn_x = line[30:38]
                Cartn_y = line[38:46]
                Cartn_z = line[46:54]
                occupancy = line[54:60]
                daq_score = float(line[60:66])
                auth_atom_id = line[77:]

                # get data
                if current_residue != label_seq_id:
                    if current_residue:
                        # save current residue data
                        res_values.append(daq_score)
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
                    res_values.append(daq_score)
    return chain_data


def getEntryFiles(path):
    logger.info('Get DAQ files from %s' % (path, ))
    entry_data_list = []
    entry_list = []
    try:
        logger.info('Reading data folder:  %s %s' % (path, MAPQ_FILE_PATTERN))
        search_path = os.path.join(path, "**", MAPQ_FILE_PATTERN)
        logger.info('search_path  %s' % (search_path, ))
        data_files = glob.glob(search_path, recursive=True)

        for data_file in sorted(data_files):
            data_filename = os.path.basename(data_file)
            # 15086_8a1s_B_v1-2_w9.pdb
            logger.info('Found data file:  %s' % (data_filename))
            emdb_entry_num, pdb_entry, chainId, version, week = data_filename.split(
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


def saveEmvData(emdbId, pdbId, emv_data):

    # emd-23530_7lv9_emv_daq.json
    json_filename = emdbId + '_' + pdbId + '_emv_daq.json'
    dirPath = Path(JSON_DATA_PATH, pdbId[1:3])
    dirPath.mkdir(parents=True, exist_ok=True)
    json_file = dirPath.joinpath(json_filename)

    logger.info('Save EMV DAQ data %s %s %s %s' %
                (emdbId, pdbId, dirPath, json_filename))
    with open(str(json_file), "w+") as of:
        of.write(json.dumps(emv_data, indent=2))


def getEmvDataHeader(emdbId, pdbId, proc_date):
    logger.info('Get EMV DAQ data header %s %s' % (emdbId, pdbId))

    emv_data = {}
    emv_data["resource"] = RESOURCE
    entry_data = {
        "volume_map": emdbId,
        "atomic_model": pdbId,
        "date": proc_date
    }
    source_data = {
        "method": "DAQ-Score Database - Kihara Lab",
        "citation":
        "Nakamura, T., Wang, X., Terashi, G. et al. DAQ-Score Database: assessment of map-model compatibility for protein structure models from cryo-EM maps. Nat Methods 20, 775-776 (2023).",
        "doi": "https://doi.org/10.1038/s41592-023-01876-1",
        "source":
        "https://daqdb.kiharalab.org/search?query=%s" % emdbId.upper(),
    }
    entry_data["source"] = source_data
    emv_data["entry"] = entry_data
    emv_data["chains"] = []

    logger.debug('EMV DAQ data header %s %s %s' % (emdbId, pdbId, emv_data))
    return emv_data


def getChainsData(data_files):
    chains_data = []

    for data_file in data_files:
        # 2981_5a0q_a_v1-1_w9.pdb
        data_filename = os.path.basename(data_file)
        logger.info('Process DAQ data file %s ' % (data_filename))
        emdb_entry_num, pdb_entry, chainId, version, week = data_filename.split(
            "_")
        emdb_entry = "emd-" + emdb_entry_num
        logger.info('Processing %s %s %s %s' %
                    (emdb_entry, pdb_entry, chainId, data_file))

        chains_data.append(pdb2json(emdb_entry, pdb_entry, chainId, data_file))

    return chains_data


def main(argv):

    parser = argparse.ArgumentParser(
        description="Prepare DAQ data from pdb-atom file to JSON, batch mode")
    parser.add_argument("-i",
                        "--inputDir",
                        help="input data directory",
                        required=True)
    parser.add_argument(
        "-l",
        "--logFile",
        help=
        "log file. By default 'prepareJob.log' in a dedicated 'logs' folder.",
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

    inputDir = args.inputDir
    test_only = args.test
    if test_only:
        logger.warning(
            'Performing a trial run. No permanent changes will be made')

    logger.info('Reading DAQ scores from %s' % (inputDir, ))
    entry_list, entry_data_list = getEntryFiles(inputDir)
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
