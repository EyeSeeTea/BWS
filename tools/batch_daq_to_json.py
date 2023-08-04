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
                # ATOM      1  N   LYS a   3     137.151 284.625 191.025  1.00 -0.15           N  
                # ATOM      2  CA  LYS a   3     137.054 283.137 191.000  1.00 -0.15           C  
                # ATOM      3  C   LYS a   3     136.248 282.626 192.185  1.00 -0.15           C  
                # ATOM      4  O   LYS a   3     135.725 281.512 192.154  1.00 -0.15           O  
                # ATOM      5  CB  LYS a   3     138.450 282.511 191.066  1.00 -0.15           C  
                # ATOM      6  CG  LYS a   3     139.408 283.009 190.010  1.00 -0.15           C  
                # ATOM      7  CD  LYS a   3     139.016 282.529 188.633  1.00 -0.15           C  
                # ATOM      8  CE  LYS a   3     139.452 283.537 187.603  1.00 -0.15           C  
                # ATOM      9  NZ  LYS a   3     138.766 284.840 187.834  1.00 -0.15           N  
                # ATOM     10  N   LEU a   4     136.140 283.444 193.226  1.00 -0.14           N  
                # ATOM     11  CA  LEU a   4     135.431 283.021 194.422  1.00 -0.14           C  
                # ATOM     12  C   LEU a   4     134.113 283.719 194.744  1.00 -0.14           C  
                # ATOM     13  O   LEU a   4     133.072 283.068 194.814  1.00 -0.14           O  
                # ATOM     14  CB  LEU a   4     136.364 283.126 195.631  1.00 -0.14           C  
                # ATOM     15  CG  LEU a   4     137.712 282.402 195.524  1.00 -0.14           C  
                # ATOM     16  CD1 LEU a   4     138.450 282.507 196.850  1.00 -0.14           C  
                # ATOM     17  CD2 LEU a   4     137.498 280.941 195.148  1.00 -0.14           C  
                # ATOM     18  N   THR a   5     134.143 285.032 194.945  1.00 -0.09           N  
                # ATOM     19  CA  THR a   5     132.918 285.739 195.298  1.00 -0.09           C  
                # ATOM     20  C   THR a   5     132.340 286.698 194.266  1.00 -0.09           C  
                # ATOM     21  O   THR a   5     132.643 287.892 194.248  1.00 -0.09           O  
                # ATOM     22  CB  THR a   5     133.091 286.495 196.624  1.00 -0.09           C  
                # ATOM     23  OG1 THR a   5     134.251 287.331 196.544  1.00 -0.09           O  
                # ATOM     24  CG2 THR a   5     133.244 285.512 197.776  1.00 -0.09           C  

                group_PDB = line[:4]
                atom_id = line[5:11]
                atom_symbol = line[13:16]
                label_comp_id = line[17:20] # residue name
                label_asym_id = line[21:23] # chain name (provided by the author)
                label_seq_id = line[23:26] # residue seq number (provided by the author)
                Cartn_x = line[30:38]
                Cartn_y = line[38:46]
                Cartn_z = line[46:54]
                occupancy = line[54:60]
                daq_score = line[60:66] # DAQ score mean value for the whole residue
                auth_atom_id = line[77:]

                # skip data for atoms in the same residue
                if current_residue == label_seq_id:
                    continue

                residue_data = {
                    "resSeqName": label_comp_id,
                    "resSeqNumber": label_seq_id,
                }
                residue_data["scoreValue"] = daq_score
                chain_data["seqData"].append(residue_data)
                # use the name provided by the author for the chain
                if chain_data["name"] != label_asym_id:
                    chain_data["name"] = label_asym_id
                current_residue = label_seq_id

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
