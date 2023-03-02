"""
Passing EM Validations to JSON Data Format
"""
import getopt
import os
import re
import sys
import argparse
import csv
import pandas as pd
import requests


DATA_PATH = "../data/emdbs"
FN_OUTPUT_DATA = "C19-NMR-C_pre-processed_data.csv"
MAPQ_FILE_REGEX = "[0-9][A-Za-z0-9]{3}.fscq.atom.pdb"
PUBCHEM_WS_URL = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/'


def readInputFile(filename):
    df = pd.read_csv(filename, sep=';')
    return df


def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)


def getDataFromPubChem(url, jKey, returnList=False):
    value = ''
    jdata = ''
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            jdata = resp.json()
            value = item_generator(jdata, jKey).__next__()
            if isinstance(value, list) and not returnList:
                value = value[0]
            if isinstance(value, int):
                value = str(value)
    except Exception as exc:
        print('- >>>>',  exc, os.strerror)
    return value


def main(argv):

    parser = argparse.ArgumentParser(description="Compute DeepRes")
    parser.add_argument("-i", "--inputFilename",
                        help="input filename (i..: Summary-ordered.csv)", required=True)
    parser.add_argument("-o", "--outputFilename",
                        help="input filename (i..: data.csv)", required=False)
    args = parser.parse_args()

    inFilename = args.inputFilename
    outputFilename = args.outputFilename or FN_OUTPUT_DATA

    print('Passing EM Validations to JSON Data Format')
    print("- Processing:", inFilename, outputFilename)

    df = readInputFile(inFilename)
    print(df.info())

    # update missing data from PubChem: PubChemID & InChIKey
    for index, row in df.iterrows():
        # some SMILES are not cannonical, so need replace some characters
        smilesId = row['SMILES'].replace('#', '%23')
        PubChemID = getDataFromPubChem(
            url=PUBCHEM_WS_URL + 'smiles/' + smilesId + '/cids/JSON', jKey='CID')
        InChIKey = getDataFromPubChem(
            url=PUBCHEM_WS_URL + 'cid/' + PubChemID + '/property/InChIKey/json', jKey='InChIKey')
        # row['InChIKey'] = [InChIKey]
        df.at[index, 'InChIKey'] = InChIKey
        # row['PubChemID'] = [PubChemID]
        df.at[index, 'PubChemID'] = PubChemID
        print(index, row['SMILES'], smilesId, InChIKey, PubChemID)

    # save results to output csv file
    df.to_csv(outputFilename, sep=';', encoding='utf-8', index=False)


if __name__ == '__main__':
    main(sys.argv[1:])
