from cmath import nan
import glob
import json
import logging
import os
import re
from subprocess import check_output
from django.core.exceptions import ValidationError
from api.study_parser import StudyParser
from .dataPaths import *
from .models import *
import requests
import fnmatch
from Bio.PDB import MMCIF2Dict
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
from django.db.models import Q
import numpy as np

STATUS = {"REL": "Released",
          "UNREL": "Unreleased",
          "HPUB": "Header released",
          "HOLD1": "1 year hold",
          "HOLD2": "2 year hold"}
FILE_EXT_PATTERN = '*.cif'

logger = logging.getLogger(__name__)

PDB_FOLDER_PATTERN = re.compile(r".*/(\d\w{3})/.*\.pdb$")
REGEX_EMDB_ID = re.compile(r'^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile(r'^(emd)-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile(r'^(pdb)\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile(r'^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAP2MODELQUALITY_FILE = re.compile(r'^\d\w{3}\.(mapq|fscq)\.pdb$')
REGEX_IDR_ID = re.compile(r'.*(idr\d{4})-.*-.*')
REGEX_TAXON_REF = re.compile(r'(ncbitaxon).*')
REGEX_SCREEN_NAME = re.compile(r'.*\/(screen)(.*)')
REGEX_ONTOLOGY_ID = re.compile(r'(\w*)_\d*')
PUBCHEM_WS_URL = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/'
OLS_WS_URL = 'https://www.ebi.ac.uk/ols/%s/ontologies/%s/terms?iri=%s%s'
HTTP_TIMEOUT = 15

# TODO: create a json to import this data?

nmrentity_list = [
    {
        'name': 'NSP1',
        'verbose_name': 'Non-structural protein 1',
        'start': 1,
        'end': 180,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP1 GD',
        'verbose_name': 'Globular domain of Non-structural protein 1',
        'start': 12,
        'end': 127,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP2',
        'verbose_name': 'Non-structural protein 2',
        'start': 181,
        'end': 818,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP2 CtDR',
        'verbose_name': 'C-terminal domain of Non-structural protein 2',
        'start': 690,
        'end': 818,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3',
        'verbose_name': 'Non-structural protein 3',
        'start': 819,
        'end': 2763,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 UBl1',
        'verbose_name': 'Ubiquitin-like domain 1 of Non-structural protein 3',
        'start': 821,
        'end': 929,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 MacroDomain',
        'verbose_name': 'MacroDomain I of Non-structural protein 3 (Mac1)',
        'start': 1025,
        'end': 1194,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 SUD-N',
        'verbose_name': 'SARS-unique domain N of Non-structural protein 3 (Mac2)',
        'start': 1231,
        'end': 1359,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 SUD-M',
        'verbose_name': 'SARS-unique domain M of Non-structural protein 3 (Mac3)',
        'start': 1367,
        'end': 1494,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 SUD-C',
        'verbose_name': 'SARS-unique domain C of Non-structural protein 3 (DPUP)',
        'start': 1496,
        'end': 1561,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 SUD-MC',
        'verbose_name': 'SARS-unique domain M and C of Non-structural protein 3 (Mac3 and DPUP)',
        'start': 1367,
        'end': 1561,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 Ubl2',
        'verbose_name': 'Ubiquitin-like domain 2 of Non-structural protein 3',
        'start': 1565,
        'end': 1620,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 PLPro',
        'verbose_name': 'Papain-like proteinase domain of Non-structural protein 3',
        'start': 1634,
        'end': 1898,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 NAB',
        'verbose_name': 'Nucleic acid binding domain of Non-structural protein 3',
        'start': 1911,
        'end': 2021,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP3 Y3',
        'verbose_name': 'Y3 domain of Non-structural protein 3',
        'start': 2660,
        'end': 2763,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP4',
        'verbose_name': 'Non-structural protein 4',
        'start': 2764,
        'end': 3263,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP5',
        'verbose_name': 'Non-structural protein 5',
        'start': 3264,
        'end': 3569,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP6',
        'verbose_name': 'Non-structural protein 6',
        'start': 3570,
        'end': 3859,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP7',
        'verbose_name': 'Non-structural protein 7',
        'start': 3860,
        'end': 3942,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP8',
        'verbose_name': 'Non-structural protein 8',
        'start': 3943,
        'end': 4140,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP9',
        'verbose_name': 'Non-structural protein 9',
        'start': 4141,
        'end': 4253,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP10',
        'verbose_name': 'Non-structural protein 10',
        'start': 4254,
        'end': 4392,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP11',
        'verbose_name': 'Non-structural protein 11',
        'start': 4393,
        'end': 4405,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP12',
        'verbose_name': 'Non-structural protein 12',
        'start': 4393,
        'end': 5324,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP13',
        'verbose_name': 'Non-structural protein 13',
        'start': 5325,
        'end': 5925,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP14',
        'verbose_name': 'Non-structural protein 14',
        'start': 5926,
        'end': 6452,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP15',
        'verbose_name': 'Non-structural protein 15',
        'start': 6453,
        'end': 6798,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'NSP16',
        'verbose_name': 'Non-structural protein 16',
        'start': 6799,
        'end': 7096,
        'uniprot_acc': 'P0DTD1',
    },

    {
        'name': 'Nucleoprotein IDR1-NTD-IDR2',
        'verbose_name': 'Intrinsically Disordered Region (IDR) of Nucleoprotein',
        'start': 1,
        'end': 248,
        'uniprot_acc': 'P0DTC9',
    },

    {
        'name': 'Nucleoprotein NTD-SR',
        'verbose_name': 'Rich Region (SR) of Nucleoprotein N-terminal domain',
        'start': 44,
        'end': 212,
        'uniprot_acc': 'P0DTC9',
    },

    {
        'name': 'Nucleoprotein NTD',
        'verbose_name': 'N-terminal domain of Nucleoprotein',
        'start': 44,
        'end': 180,
        'uniprot_acc': 'P0DTC9',
    },

    {
        'name': 'Nucleoprotein CTD',
        'verbose_name': 'C-terminal domain of Nucleoprotein',
        'start': 247,
        'end': 364,
        'uniprot_acc': 'P0DTC9',
    },

    {
        'name': 'ORF9b',
        'verbose_name': 'ORF9b protein',
        'start': 1,
        'end': 97,
        'uniprot_acc': 'P0DTD2',
    },
]


def findGeneric(pattern, dirToLook=THORN_DATA_DIR):
    data = {}
    cmd = ["find", os.path.join(dirToLook, "pdb"), "-wholename", pattern]
    logger.debug(" ".join(cmd))
    isoldesCandidates = check_output(cmd).decode()
    for candidate in isoldesCandidates.split("\n"):
        matchObj = re.match(PDB_FOLDER_PATTERN, candidate)
        if matchObj:
            pdbId = matchObj.group(1)
            try:
                data[pdbId].append(candidate)
            except KeyError:
                data[pdbId] = [candidate]
    return data


class PdbEntryAnnFromMapsUtils(object):

    def _getJsonFromFname(self, fneme, chain_id, minToFilter=-1):
        residues = []
        values = []
        with open(fneme) as f:
            for line in f:
                if not "CA" in line or not "ATOM" in line:
                    continue
                chainId = line[21]
                if chainId != chain_id:
                    continue
                resId = line[22:26].strip()
                bFactor = float(line[54:60].strip())
                residues.append({"begin": resId, "value": bFactor})
                values.append(bFactor)
        if len(residues) == 0:
            return None
        return {"chain": chain_id, "data": residues, "minVal": min([val for val in values if val > minToFilter]), "maxVal": max(values)}

    def _locateFname(self, targetFname, modifiedPdbType=None):

        try:
            logger.debug("Searching %s in DB", targetFname)
            fileRecord = DataFile.objects.get(
                filename__iexact=targetFname, fileType__iexact=ENTRY_TYPES[0])
            if fileRecord:
                return os.path.join(fileRecord.path, fileRecord.filename)
            else:
                logger.debug("Not found %s in DB", targetFname)
                return None
        except (ValueError, ValidationError, DataFile.DoesNotExist) as exc:
            logger.exception(exc)
            # check from disk
            logger.debug("Searching %s in Disk", targetFname)

            if modifiedPdbType is None:
                rootDir = EMDB_DATA_DIR
            else:
                rootDir = os.path.join(MODIFIED_PDBS_ANN_DIR, modifiedPdbType)
            for dirName in os.listdir(rootDir):
                for fname in os.listdir(os.path.join(rootDir, dirName)):
                    if fname == targetFname:
                        return os.path.join(rootDir, dirName, fname)
        return None

# ========== ========== ========== ========== ========== ========== ==========


def download_file(url, path):
    """
    Download the file from `url` and save it locally under `filename`:
    """
    local_filename = url.split('/')[-1]
    full_path = os.path.join(path, local_filename)
    logger.debug("- download file: %s %s",  url, full_path)
    print("- download file:", url, full_path)
    with requests.get(url, stream=True, timeout=HTTP_TIMEOUT) as r:
        r.raise_for_status()
        os.makedirs(path, exist_ok=True)
        with open(full_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return full_path


def save_json(data,  path, filename, createIfNotExist=True):
    """
    Save the data as json file
    """
    logger.debug("- save json: %s %s", path, filename)
    print("- save json:", path, filename)
    if path and createIfNotExist:
        os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    with open(full_path, 'w') as f:
        json.dump(data, f)
    return f.name


def save2file(data, path, filename, createIfNotExist=True, append=True):
    """
    Save data into a text file
    if data is a list of items, will be concatenated in a single string
    file will be created if not exists, by default
    data will be appended, by default
    """
    logger.debug("- save data: %s %s", path, filename)
    if path and createIfNotExist:
        os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, filename)
    strData = ''
    if isinstance(data, list):
        strData = ' '.join([str(item) for item in data if item])
        strData += '\n'
    if append:
        with open(full_path, 'a') as f:
            f.write(strData)
    else:
        with open(full_path, 'w') as f:
            f.write(strData)
    return f.name


def getGitHubFileList(url, ext=''):
    """
    Get the list of files from a GitHub repository
    """
    logger.debug("- get GitHub file list: %s %s", ext, url)
    print("- get GitHub file list:", ext, url)
    page = requests.get(url, timeout=HTTP_TIMEOUT).text
    soup = BeautifulSoup(page, 'html.parser')

    files = []
    for node in soup.find_all('a'):
        if node.get('href') and node.get('href').endswith(ext):
            files.append(node.get('href').split('/')[-1])
    return files

# ========== ========== ========== ========== ========== ========== ==========


def findPdbEntry(pdbId):
    obj = None
    try:
        obj = PdbEntry.objects.get(dbId=pdbId)
        logger.debug('Found: %s', obj)
        print('Found', obj)
    except Exception as exc:
        logger.exception(exc)
        print(pdbId, exc, os.strerror)
    return obj


def findRefinedModelSource(name):
    """
    Find a RefinedModelSource entry in the DB table
    """
    obj = None
    try:
        obj = RefinedModelSource.objects.get(name=name)
        logger.debug('Found: %s', obj)
        # print('Found', obj)
    except Exception as exc:
        logger.exception(exc)
        print(name, exc, os.strerror)
    return obj


def findRefinedModelMethod(name):
    """
    Find a RefinedModelMethod entry in the DB table
    """
    obj = None
    try:
        obj = RefinedModelMethod.objects.get(name=name)
        logger.debug('Found: %s', obj)
        # print('Found', obj)
    except Exception as exc:
        logger.exception(exc)
        print(name, exc, os.strerror)
    return obj


def updateRefinedModel(emdbObj, pdbObj, sourceObj, methodObj, filename, externalLink, queryLink, details):
    obj = None
    try:
        obj, created = RefinedModel.objects.update_or_create(
            emdbId=emdbObj,
            pdbId=pdbObj,
            source=sourceObj,
            method=methodObj,
            defaults={
                'filename': filename,
                'externalLink': externalLink,
                'queryLink': queryLink,
                'details': details,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated%s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def update_isolde_refinements(inputfile=None):
    """
    Update the isolde refinement models from GitHub
    """
    logger.debug("- update isolde refinements: %s", inputfile)
    # print("- update isolde refinements:", inputfile)
    if not inputfile:
        url = CSTF_GITHUB_RAW_URL + ISOLDE_REF_FNAME
        logger.debug("-- download Isolde entries list: %s", inputfile)
        # print("-- download Isolde entries list:", url)
        inputfile = download_file(url, CSTF_LOCAL_PATH)

    entries = []
    # print("- parse Isolde entry list:", inputfile)
    logger.debug("- parse Isolde entry list: %s", inputfile)
    parseIsoldeEntryList(inputfile, entries)

    # print("- get Isolde refinement data")
    logger.debug("- get Isolde refinement data")
    getIsoldeRefinementData(entries)

    # print("-- save Isolde data (JSON):", CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    logger.debug("-- save Isolde data (JSON): %s %s",
                 CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    save_json(entries, CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)

    # print("-- get Isolde refined model")
    logger.debug("-- get Isolde refined model")
    getIsoldeRefinedModel(entries)

    # print("-- get all files in Isolde data folder")
    logger.debug("-- get all files in Isolde data folder")
    getAllIsoldeDataFiles(entries, [".txt", ".mtz", ".cif"])

    # print("-- update DB Isolde data")
    logger.debug("-- update DB Isolde data")
    for entry in entries:
        if 'filename' in entry:
            for refModel in entry['refmodels']:
                pdbObj = findPdbEntry(entry['pdbId'].upper())
                if pdbObj:
                    updateRefinedModel(
                        emdbObj=None,
                        pdbObj=pdbObj,
                        sourceObj=findRefinedModelSource(refModel['source']),
                        methodObj=findRefinedModelMethod(refModel['method']),
                        filename=entry['filename'],
                        externalLink=refModel['externalLink'],
                        queryLink=refModel['queryLink'],
                        details=refModel['details'])


def parseIsoldeEntryList(inputfile, entries):
    """
    Parse the Isolde entries list file to get new entries
    """
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
        # print("-- found:", len(entries), "entries")
        logger.debug("-- found: %s entries", len(entries))


def getIsoldeRefinementData(entries):
    """
    Get the Isolde refinement data from GitHub
    """
    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        # print("-- get Isolde refinements for:", pdb_id, remote_path)
        logger.debug("-- get Isolde refinements for: %s %s",
                     pdb_id, remote_path)
        filenames = getGitHubFileList(url, ".pdb")
        if not filenames:
            filenames = getGitHubFileList(url, ".cif")
        for filename in filenames:
            if filename.startswith(pdb_id):
                filename = filenames[len(filenames)-1]
                # print("--- found:", len(filenames), "refinements ", filename)
                logger.debug("--- found: %s refinements %s",
                             len(filenames), filename)
                entry.update({"filename": filename})
                entry.update({"refmodels": [{
                    "source": "CSTF",
                    "method": "Isolde",
                    "externalLink": url,
                    "queryLink": "%s/%s/%s" % (URL_ISOLDE_QUERY, pdb_id, filename),
                    "details": "",
                }]})


def getIsoldeRefinedModel(entries):
    """
    Get the Isolde refined model file from GitHub
    """
    for entry in entries:
        if "filename" in entry:
            filename = entry["filename"]
            pdb_id = entry["pdbId"]
            url = os.path.join(CSTF_GITHUB_RAW_URL, entry["path"], filename)
            # print("--- dowload Isolde refinements for",
            #       pdb_id, entry["path"], filename)
            logger.debug("--- dowload Isolde refinements for %s %s %s",
                         pdb_id, entry["path"], filename)
            download_file(url, os.path.join(
                ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3], pdb_id))


def getAllIsoldeDataFiles(entries, exts=["txt"]):
    """
    Get all the files in the Isolde data folder from GitHub
    """
    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        url_raw = os.path.join(CSTF_GITHUB_RAW_URL, remote_path)
        # print("--- get all Isolde refinement files for", pdb_id, remote_path)
        logger.debug("--- get all Isolde refinement files for %s %s",
                     pdb_id, remote_path)
        for ext in [".txt", ".mtz", ".cif"]:
            filenames = getGitHubFileList(url, ext)
            for filename in filenames:
                download_file(os.path.join(url_raw, filename), os.path.join(
                    ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3], pdb_id))


def update_RefinedModel(refmodel):
    """
    Update a RefinedModel in the DB
    """
    emdb_id = refmodel["emdbId"]
    pdb_id = refmodel["pdbId"]
    source = findRefinedModelSource(refmodel["source"])
    method = findRefinedModelMethod(refmodel["method"])
    filename = refmodel["filename"]
    externalLink = refmodel["externalLink"]
    queryLink = refmodel["queryLink"]
    details = refmodel["details"]

    obj = None
    try:
        obj, created = RefinedModel.objects.update_or_create(
            emdbId=emdb_id,
            pdbId=pdb_id,
            source=source,
            method=method,
            defaults={
                'filename': filename if filename else '',
                'externalLink': externalLink if externalLink else '',
                'queryLink': queryLink if queryLink else '',
                'details': details[:200] if details else '',
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def init_base_tables():
    """
    Initialize some base tables
    """
    print('Initializing base tables', 'RefinedModelSources')
    initRefinedModelSources()
    print('Initializing base tables', 'RefinedModelMethods')
    initRefinedModelMethods()
    print('Initializing base tables', 'Topics')
    initTopics()


def initRefinedModelSources():
    """
    Initialize the RefinedModelSources table
    """
    print('Initializing Refined Model Source', 'PDB-REDO')
    source = updateRefinedModelSource(
        'PDB-REDO',
        'The PDB-REDO databank contains optimised versions of existing PDB entries with electron density maps, a description of model changes, and a wealth of model validation data.',
        URL_PDB_REDO)

    print('Initializing Refined Model Source', 'CSTF')
    source = updateRefinedModelSource(
        'CSTF',
        'The Coronavirus Structural Task Force (CSTF) serve as a public global resource for the macromolecular models for 17 of the 28 different SARS-CoV and SARS-CoV-2 proteins, as well as structures of the most important human coronavirus interaction partners. All structures have been evaluated and some have been reviewed manually, atom by atom.',
        URL_CSTF)

    print('Initializing Refined Model Source', 'CERES')
    source = updateRefinedModelSource(
        'CERES',
        'The Cryo-EM re-refinement system (CERES) provides automatically re-refined models deposited in the Protein Data Bank that have map resolutions better than 5Å, using the latest version of phenix.real_space_refine within the Phenix software package.',
        URL_PHENIX_CERES)


def initRefinedModelMethods():
    """
    Initialize the RefinedModelMethods table
    """
    print('Initializing Refined Model Method', 'PDB-Redo')
    method = updateRefinedModelMethod(
        RefinedModelSource.objects.get(name='PDB-REDO'),
        'PDB-Redo',
        'All the entries are treated with a consistent protocol that reduces the effects of differences in age, software, and depositors. This makes PDB-REDO a great datatset for large scale structure analysis studies.',
        URL_PDB_REDO)

    print('Initializing Refined Model Method', 'Isolde')
    method = updateRefinedModelMethod(
        RefinedModelSource.objects.get(name='CSTF'),
        'Isolde',
        'These are manual re-refinements from ISOLDE in ChimeraX, done by Tristan Croll. Structures were energy-minimised, visually checked residue-by-residue and, where necessary, rebuilt. Crystal structures were further refined with phenix.refine.',
        URL_CSTF)
    print('Initializing Refined Model Method', 'Isolde')
    method = updateRefinedModelMethod(
        RefinedModelSource.objects.get(name='CSTF'),
        'Refmac',
        'These are manual re-refinements from coot and REFMAC5 done by Dr. Sam Horrell. Structures were validated using inbuilt validation tools from coot in combination with validation through the molprobity server (Duke University School of Medicine).',
        URL_CSTF)

    print('Initializing Refined Model Method', 'PHENIX')
    method = updateRefinedModelMethod(
        RefinedModelSource.objects.get(name='CERES'),
        'PHENIX',
        'Re-refinements have been performed using the latest version of phenix.real_space_refine, a command-line tool inside the PHENIX software package for refinement of a model against a map. Models are taken from the Protein Data Bank and maps from the Electron Microscopy Data Bank, establishing a resolution cut-off of 5 Å because real_space_refine performs best for maps with resolutions better than 5 Å.',
        URL_PHENIX_CERES)


def initTopics():
    print('Initializing Topics')
    updateTopic(
        'COVID19', 'COVID-19, All SARS-CoV-2 virus and its proteins structures.')


# init_nmr_targets
def init_nmr_targets():
    """
    Initialize NMR Tagets table
    """
    print('Initializing base tables', 'NMRTargets')
    initNMRTargets()


def initNMRTargets():
    """
    Initialize the NMRTarget table
    """
    print('Initializing NMRTargets')
    for target in nmrentity_list:
        print(target['name'], target['verbose_name'], target['uniprot_acc'],
              target['start'], target['end'])
        uniprot_obj = getOrCreateUniProtEntry(target['uniprot_acc'], "")
        updateNMRTarget(target['name'], target['verbose_name'], uniprot_obj,
                        target['start'], target['end'])


def updateNMRTarget(name, verbose_name, uniprot_acc, start, end):
    obj = None
    try:
        obj, created = NMRTarget.objects.update_or_create(
            name=name,
            defaults={
                'verbose_name': verbose_name,
                'uniprot_acc': uniprot_acc,
                'start': start,
                'end': end,
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateNMRTargetToModelEntity(target, entity, start, end):
    obj = None
    try:
        obj, created = NMRTargetToModelEntity.objects.update_or_create(
            target=target,
            model_entity=entity,
            defaults={
                'start': start,
                'end': end,
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateTopic(name, description=''):
    obj = None
    try:
        obj, created = Topic.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateStructureTopic(structure, topic):
    obj = None
    try:
        obj, created = StructureTopic.objects.update_or_create(
            structure=structure,
            topic=topic,
            defaults={
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateRefinedModelSource(name, description='', url=''):
    """
    Update a RefinedModelSource in the DB
    """
    obj = None
    try:
        obj, created = RefinedModelSource.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'externalLink': url,
            }
        )
        if created:
            logger.debug('Created new %s: %s',
                         obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateRefinedModelMethod(source, name, description='', url=''):
    """
    Update a RefinedModelMethod in the DB
    """
    obj = None
    try:
        obj, created = RefinedModelMethod.objects.update_or_create(
            source=source,
            name=name,
            defaults={
                'description': description,
                'externalLink': url,
            })
        if created:
            logger.debug('Created new %s: %s',
                         obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


# ========== ========== ========== ========== ========== ========== ==========

def get_structures_from_path(path, start=0):
    """
    get_structures_from_path
    """
    logger.debug("Updating Structure entries from : %s", path)
    print("Updating Structure entries from", path)

    objs = []

    try:
        # Get files from path
        filenames = get_mmcif_files(path)

        # for filename in filenames:
        for idx, filename in enumerate(filenames):
            if idx < start:
                print("-> skipping ", idx)
                continue

            filename.replace(".cif", "")

            # Read mmCIF to dictionary
            mmcif_dict = convert_mmcif_to_dictionary(path, filename)

            print("->>> Entry:", idx + 1, "/", len(filenames))
            read_mmcif_file(mmcif_dict)
            # break

    except Exception as exc:
        logger.exception(exc)
        print(exc)
    return objs


def get_mmcif_files(path, pattern='*.cif'):
    fileList = []
    for root, dirs, files in os.walk(path):
        for filename in fnmatch.filter(files, pattern):
            fileList.append(filename)
    return fileList


def convert_mmcif_to_dictionary(path, filename):
    filepath = os.path.join(path, filename)
    # filepath = os.path.join(path, filename[1:3], filename)
    mmcif_dict = MMCIF2Dict.MMCIF2Dict(filepath)
    return mmcif_dict


def read_mmcif_file(mmCifDict):
    hybridmodelObj = None
    pdbobj = None

    # get PDB Entry
    pdbId = mmCifDict.get('_entry.id', '')[0]
    print('PDB file:', pdbId)
    if pdbId:
        pdbObj = updatePdbEntrymmCifFile(mmCifDict, pdbId)

    # Find associated EM volume
    emdbObj = None
    emdbId = ''
    related_db_name = mmCifDict.get('_pdbx_database_related.db_name', '')
    related_content_type = mmCifDict.get(
        '_pdbx_database_related.content_type', '')
    related_db_id = mmCifDict.get('_pdbx_database_related.db_id', '')

    for i, db in enumerate(related_db_name):
        if db == 'EMDB':
            if related_content_type[i] == 'associated EM volume':
                emdbId = related_db_id[i]

    # hybrid model
    if emdbId:
        emdbObj = updateEmdbEntrymmCifFile(emdbId, mmCifDict)

    hybridmodelObj = updateHybridModel(emdbObj, pdbObj)

    # get list of Polymer Entities (not ligands)
    entityList = getPdbToEntityListmmCifFile(mmCifDict, pdbObj)

    # get list of branched Ligands
    # branchedligandList = getPdbToLigandListmmCifFile(
    #     'branched', mmCifDict, pdbObj)

    # get list of non-polymers Ligands
    nonPolymerligandList = getPdbToLigandListmmCifFile(
        'non-polymer', mmCifDict, pdbObj)

    # get refined models
    # PDB-Redo
    refModel = getRefinedModelPDBRedo(pdbObj)

    # CERES
    if emdbObj:
        refModel = getRefinedModelCeres(pdbObj, emdbObj)

    # get submission authors
    submAuthors = getPdbEntryAuthors(mmCifDict, pdbObj)

    # Details
    entryDetails = updatePdbEntryDetails(mmCifDict, pdbObj)

    # get DB citation
    publications = getPublications(mmCifDict)
    entryDetails.refdoc.set(publications)

    return pdbObj


def updatePdbentry(entryId, title, status, releaseDate, method, keywords):
    obj = None
    try:
        obj, created = PdbEntry.objects.update_or_create(
            dbId=entryId,
            defaults={
                'title': title,
                'status': status,
                'relDate': releaseDate,
                'method': method,
                'keywords': keywords,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getCitationAuthors(mmCifDict, citation):
    auths = []
    # _citation_author.name
    # _citation_author.ordinal
    # _citation_author.identifier_ORCID
    names = mmCifDict.get('_citation_author.name', '')
    orcids = mmCifDict.get('_citation_author.identifier_ORCID', '')
    ordinals = mmCifDict.get('_citation_author.ordinal', '')
    for idx, name in enumerate(names):
        orcid = orcids[idx].replace('?', '') if orcids else ''
        ordinal = ordinals[idx].replace('?', '') if ordinals else ''
        authorObj = updatePublicationAuthor(name, orcid, ordinal, citation)
        auths.append(authorObj)
    return auths


def updatePublicationAuthor(name, orcid, ordinal, publication):
    obj = None
    author = updateAuthor(name, orcid)
    try:
        obj, created = PublicationAuthor.objects.update_or_create(
            publication=publication,
            author=author,
            defaults={
                'ordinal': ordinal,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updatePublication(title, journal, issn, issue, volume, firstPage, lastPage, year, doi, pubMedId, PMCId=''):
    obj = None
    try:
        obj, created = Publication.objects.update_or_create(
            title=title,
            defaults={
                'journal_abbrev': journal,
                'issn': issn,
                'issue': issue,
                'volume': volume,
                'page_first': firstPage,
                'page_last': lastPage,
                'year': year,
                'doi': doi,
                'pubMedId': pubMedId,
                'PMCId': PMCId,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getPublications(mmCifDict):
    objs = []
    titleList = mmCifDict.get('_citation.title', '')
    journalList = mmCifDict.get('_citation.journal_abbrev', '')
    issnList = mmCifDict.get('_citation.journal_id_ISSN', '')
    issueList = mmCifDict.get('_citation.journal_issue', '')
    volumeList = mmCifDict.get('_citation.journal_volume', '')
    firsPagetList = mmCifDict.get('_citation.page_first', '')
    lastPageList = mmCifDict.get('_citation.page_last', '')
    yearList = mmCifDict.get('_citation.year', '')
    doiList = mmCifDict.get('_citation.pdbx_database_id_DOI', '')
    pubMedList = mmCifDict.get('_citation.pdbx_database_id_PubMed', '')
    for idx, title in enumerate(titleList):
        journal = journalList[idx].replace('?', '') if journalList else ''
        issn = issnList[idx].replace('?', '') if issnList else ''
        issue = issueList[idx].replace('?', '') if issueList else ''
        volume = volumeList[idx].replace('?', '') if volumeList else ''
        firstPage = firsPagetList[idx].replace(
            '?', '') if firsPagetList else ''
        lastPage = lastPageList[idx].replace('?', '') if lastPageList else ''
        year = yearList[idx].replace('?', '') if yearList else ''
        doi = doiList[idx].replace('?', '') if doiList else ''
        pubMedId = pubMedList[idx].replace('?', '') if pubMedList else ''

        refObj = updatePublication(
            title, journal, issn, issue, volume, firstPage, lastPage, year, doi, pubMedId)
        objs.append(refObj)

        auths = getCitationAuthors(mmCifDict, refObj)
        # pubs = updateCitationToPdb(refObj, entryDetails)

    return objs


def updatePdbEntrymmCifFile(mmCifDict, entryId):
    obj = None
    title = mmCifDict.get('_struct.title', '')
    status = mmCifDict.get('_pdbx_database_status.status_code', '')[0]
    releaseDate = mmCifDict.get(
        '_pdbx_audit_revision_history.revision_date', '')
    method = mmCifDict.get('_exptl.method', '')
    keywords = mmCifDict.get('_struct_keywords.text', '')

    obj = updatePdbentry(entryId, title[0] if title else '',
                         STATUS[status] if status in STATUS else '',
                         releaseDate[0] if releaseDate else None,
                         method[0] if method else None,
                         keywords[0] if keywords else None)
    return obj


def updateEmdbEntry(emdbId, title, status, emMethod, resolution):
    obj = None
    try:
        obj, created = EmdbEntry.objects.update_or_create(
            dbId=emdbId,
            defaults={
                'title': title,
                'status': status,
                'emMethod': emMethod,
                'resolution': resolution,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateEmdbEntrymmCifFile(emdbId, mmCifDict):
    obj = None
    title = mmCifDict.get('_struct.title', '')
    status = mmCifDict.get('_pdbx_database_status.status_code', '')[0]
    em_method = mmCifDict.get('_em_experiment.reconstruction_method', '')
    resolution = mmCifDict.get('_em_3d_reconstruction.resolution', '')
    obj = updateEmdbEntry(emdbId,
                          title[0] if title else '',
                          STATUS[status] if status in STATUS else '',
                          em_method[0] if em_method else None,
                          resolution[0] if resolution else None)
    return obj


def updateHybridModel(emdbObj, pdbObj):
    obj = None
    try:
        obj, created = HybridModel.objects.update_or_create(
            emdbId=emdbObj,
            pdbId=pdbObj,
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getOrCreateUniProtEntry(db_accession, db_code):
    obj = None
    try:
        obj, created = UniProtEntry.objects.get_or_create(dbId=db_accession,
                                                          defaults={
                                                              'name':
                                                              db_code,
                                                              'externalLink':
                                                              URL_UNIPROT +
                                                              db_accession,
                                                          })
        if created:
            logger.debug(' %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateUniProtEntry(db_accession, db_code):
    obj = None
    try:
        obj, created = UniProtEntry.objects.update_or_create(
            dbId=db_accession,
            defaults={
                'name': db_code,
                'externalLink': URL_UNIPROT + db_accession,
            })
        if created:
            logger.debug(' %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateOrganism(taxonomy_id, scientific_name, common_name):
    obj = None
    try:
        obj, created = Organism.objects.update_or_create(
            ncbi_taxonomy_id=taxonomy_id,
            defaults={
                'scientific_name': scientific_name if scientific_name else '',
                'common_name': common_name.replace('?', '') if common_name else '',
                'externalLink': URL_NCBI_TAXONOMY + taxonomy_id,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getOrganismObjmmCifFile(indx, mmCifDict):
    entity_id = mmCifDict.get('_entity_src_gen.entity_id', '')
    common_name = mmCifDict.get('_entity_src_gen.gene_src_common_name', '')
    scientific_name = mmCifDict.get(
        '_entity_src_gen.pdbx_gene_src_scientific_name', '')
    ncbi_taxonomy_id = mmCifDict.get(
        '_entity_src_gen.pdbx_gene_src_ncbi_taxonomy_id', '')

    commonName = ''
    scientificName = ''
    ncbi_taxonomyId = ''
    for id, cname, sciname, taxid in zip(entity_id, common_name, scientific_name, ncbi_taxonomy_id):
        if int(id) == indx+1:
            commonName = cname
            scientificName = sciname
            ncbi_taxonomyId = taxid
    if ncbi_taxonomyId:
        organismObj = updateOrganism(
            ncbi_taxonomyId, scientificName, commonName)
        return organismObj


def updateEntitymmCifFile(indx, mmCifDict, uniprotObj=None, organismObj=None):
    entId = indx+1
    types = mmCifDict.get('_entity.type', '')
    names = mmCifDict.get('_entity.pdbx_description', '')
    quantity = mmCifDict.get('_entity.pdbx_number_of_molecules', '')
    mutations = mmCifDict.get('_entity.pdbx_mutation', '')
    details = mmCifDict.get('_entity.details', '')
    altNames = ''
    com_entity_ids = mmCifDict.get('_entity_name_com.entity_id', '')
    com_names = mmCifDict.get('_entity_name_com.name', '')
    for centId, cname in zip(com_entity_ids, com_names):
        if int(centId) == entId:
            altNames = cname
    obj = None
    try:
        obj, created = ModelEntity.objects.update_or_create(
            name=names[indx],
            defaults={
                'altNames': altNames if altNames else '',
                'type': types[indx] if types[indx] else '',
                'details': details[indx][:200].replace('?', '') if details[indx] else '',
                'mutation': mutations[indx][:200].replace('?', '') if mutations[indx] else '',
                'uniprotAcc': uniprotObj,
                'organism': organismObj,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj, quantity[indx]


def updatePdbToEntity(mmCifDict, entity_id, pdbObj, polymerObj, quantity=1):
    entity_src_entity_id = mmCifDict.get('_entity_src_gen.entity_id', '')
    entity_pdbx_beg_seq_num = mmCifDict.get('_entity_src_gen.pdbx_beg_seq_num',
                                            '')
    entity_pdbx_end_seq_num = mmCifDict.get('_entity_src_gen.pdbx_end_seq_num',
                                            '')
    pdbx_beg_seq_num = 0
    pdbx_end_seq_num = 0
    for (src_entity_id, entity_beg_seq_num,
         entity_end_seq_num) in zip(entity_src_entity_id,
                                    entity_pdbx_beg_seq_num,
                                    entity_pdbx_end_seq_num):
        if src_entity_id == entity_id:
            pdbx_beg_seq_num = int(entity_beg_seq_num.replace("?", "0"))
            pdbx_end_seq_num = int(entity_end_seq_num.replace("?", "0"))
            break

    entity_poly_entity_id = mmCifDict.get('_entity_poly.entity_id', '')
    entity_poly_pdbx_strand_id = mmCifDict.get('_entity_poly.pdbx_strand_id',
                                               '')
    struct_ref_seq_pdbx_strand_id = mmCifDict.get(
        '_struct_ref_seq.pdbx_strand_id', '')
    struct_ref_seq_seq_align_begin = mmCifDict.get(
        '_struct_ref_seq.seq_align_beg', '')
    struct_ref_seq_seq_align_end = mmCifDict.get(
        '_struct_ref_seq.seq_align_end', '')
    struct_ref_seq_db_align_begin = mmCifDict.get(
        '_struct_ref_seq.db_align_beg', '')
    struct_ref_seq_db_align_end = mmCifDict.get('_struct_ref_seq.db_align_end',
                                                '')
    struct_ref_seq_auth_seq_align_begin = mmCifDict.get(
        '_struct_ref_seq.pdbx_auth_seq_align_beg', '')
    struct_ref_seq_auth_seq_align_end = mmCifDict.get(
        '_struct_ref_seq.pdbx_auth_seq_align_end', '')

    chain_ids = ""
    for (poly_entity_id, poly_pdbx_strand_id) in zip(entity_poly_entity_id,
                                                     entity_poly_pdbx_strand_id):
        if poly_entity_id == entity_id:
            chain_ids = poly_pdbx_strand_id
            break
    objs = []
    for chain in chain_ids.split(','):
        obj = None
        seq_align_begin = 0
        seq_align_end = 0
        db_align_begin = 0
        db_align_end = 0
        auth_seq_align_begin = 0
        auth_seq_align_end = 0
        for (ref_seq_pdbx_strand_id, ref_seq_seq_align_begin,
             ref_seq_seq_align_end, ref_seq_db_align_begin,
             ref_seq_db_align_end, ref_seq_auth_seq_align_begin,
             ref_seq_auth_seq_align_end) in zip(
                 struct_ref_seq_pdbx_strand_id, struct_ref_seq_seq_align_begin,
                 struct_ref_seq_seq_align_end, struct_ref_seq_db_align_begin,
                 struct_ref_seq_db_align_end,
                 struct_ref_seq_auth_seq_align_begin,
                 struct_ref_seq_auth_seq_align_end):
            if ref_seq_pdbx_strand_id == chain:
                seq_align_begin = int(
                    ref_seq_seq_align_begin.replace("?", "0"))
                seq_align_end = int(ref_seq_seq_align_end.replace("?", "0"))
                db_align_begin = int(ref_seq_db_align_begin.replace("?", "0"))
                db_align_end = int(ref_seq_db_align_end.replace("?", "0"))
                auth_seq_align_begin = int(
                    ref_seq_auth_seq_align_begin.replace("?", "0"))
                auth_seq_align_end = int(
                    ref_seq_auth_seq_align_end.replace("?", "0"))
                break

        try:
            obj, created = PdbToEntity.objects.update_or_create(
                pdbId=pdbObj,
                entity=polymerObj,
                chain_id=chain,
                defaults={
                    'pdbx_beg_seq_num': pdbx_beg_seq_num,
                    'pdbx_end_seq_num': pdbx_end_seq_num,
                    'seq_align_begin': seq_align_begin,
                    'seq_align_end': seq_align_end,
                    'db_align_begin': db_align_begin,
                    'db_align_end': db_align_end,
                    'auth_seq_align_begin': auth_seq_align_begin,
                    'auth_seq_align_end': auth_seq_align_end,
                })
            if created:
                logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
                print('Created new', obj.__class__.__name__, obj)
            else:
                logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
                print('Updated', obj.__class__.__name__, obj)
        except Exception as exc:
            logger.exception(exc)
            print(exc, os.strerror)
        objs.append(obj)
    return objs


def getPdbToEntityListmmCifFile(mmCifDict, pdbObj):
    objList = []
    entity_types = mmCifDict.get('_entity.type', '')
    entity_ids = mmCifDict.get('_entity.id', '')
    struct_ref_db_name = mmCifDict.get('_struct_ref.db_name', '')
    struct_ref_db_code = mmCifDict.get('_struct_ref.db_code', '')
    struct_ref_db_accession = mmCifDict.get(
        '_struct_ref.pdbx_db_accession', '')
    for indx, entity_id in enumerate(entity_ids):
        if entity_types[indx] == 'polymer':
            # UniProt
            uniprotObj = None
            if struct_ref_db_name[indx] == 'UNP':
                db_accession = struct_ref_db_accession[indx]
                db_code = struct_ref_db_code[indx]
                uniprotObj = updateUniProtEntry(db_accession, db_code)

            # Organism
            organismObj = getOrganismObjmmCifFile(indx, mmCifDict)

            # Polymer Entity
            entityObj, quantity = updateEntitymmCifFile(
                indx, mmCifDict, uniprotObj, organismObj)

            # PDB-Polymer
            objList = updatePdbToEntity(
                mmCifDict, entity_id, pdbObj, entityObj, quantity)
            for pdbEntityOgj in objList:
                if pdbEntityOgj.entity.uniprotAcc:
                    uniprot_id = pdbEntityOgj.entity.uniprotAcc.dbId
                    entity_begin = pdbEntityOgj.pdbx_beg_seq_num
                    entity_end = pdbEntityOgj.pdbx_end_seq_num
                    targets = NMRTarget.objects.filter(uniprot_acc__dbId=uniprot_id,
                                                       start__lte=entity_end,
                                                       end__gte=entity_begin)
                    for target in targets:
                        updateNMRTargetToModelEntity(
                            target, entityObj, entity_begin, entity_end)
    return objList


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
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            jdata = resp.json()
            value = item_generator(jdata, jKey).__next__()
            if isinstance(value, list) and not returnList:
                value = value[0]
            if isinstance(value, int):
                value = str(value)
    except Exception as exc:
        logger.exception(exc)
        print('- >>>>',  exc, os.strerror)
    return value


def updateLigandEntity(inChIKey, ligandId, ligandType, ligandName, formula, formula_weight, details,
                       altNames, systematicNames, pubChemCompoundId, IUPACInChI, isomericSMILES, canonicalSMILES):
    obj = None
    try:
        obj, created = LigandEntity.objects.update_or_create(
            IUPACInChIkey=inChIKey,
            defaults={
                'dbId': ligandId if ligandId else '',
                'pubChemCompoundId': pubChemCompoundId if pubChemCompoundId else '',
                'ligandType': ligandType if ligandType else '',
                'name': ligandName if ligandName else '',
                'formula': formula if formula else '',
                'formula_weight': formula_weight if formula_weight else '',
                'details': details[:200] if details else '',
                'altNames': altNames if altNames else '',
                'systematicNames': systematicNames if systematicNames else '',
                'IUPACInChI': IUPACInChI if IUPACInChI else '',
                'isomericSMILES': isomericSMILES if isomericSMILES else '',
                'canonicalSMILES': canonicalSMILES if canonicalSMILES else '',
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateLigandEntitymmCifFile(lType, indx, entityId, mmCifDict):
    descriptions = mmCifDict.get('_entity.pdbx_description', '')
    formula_weights = mmCifDict.get('_entity.formula_weight', '')
    quantity = mmCifDict.get('_entity.pdbx_number_of_molecules', '')

    ligandType = ''
    ligandId = ''
    ligandName = ''
    if lType == 'branched':
        ltypes_entity_ids = mmCifDict.get('_pdbx_entity_branch.entity_id', '')
        ligandTypes = mmCifDict.get('_pdbx_entity_branch.type', '')
        for i, ltype in enumerate(ligandTypes):
            if ltypes_entity_ids[i] == entityId:
                ligandType = ltype

        branch_entity_ids = mmCifDict.get(
            '_pdbx_entity_branch_list.entity_id', '')
        comp_ids = mmCifDict.get('_pdbx_entity_branch_list.comp_id', '')
        ligandUnits = []
        for i, branch_entity_id in enumerate(branch_entity_ids):
            if branch_entity_id == entityId:
                ligandUnits.append(comp_ids[i])
        ligandId = "-".join(ligandUnits)

        bDescEntId = mmCifDict.get(
            '_pdbx_entity_branch_descriptor.entity_id', '')
        bDescriptors = mmCifDict.get(
            '_pdbx_entity_branch_descriptor.descriptor', '')
        bDescProgram = mmCifDict.get(
            '_pdbx_entity_branch_descriptor.program', '')
        for i, desc in enumerate(bDescriptors):
            if bDescEntId[i] == entityId and bDescProgram[i] == 'GMML':
                ligandName = desc

    elif lType == 'non-polymer':
        mdescEntId = mmCifDict.get(
            '_pdbx_entity_nonpoly.entity_id', '')
        mDescriptors = mmCifDict.get('_pdbx_entity_nonpoly.name', '')
        ligandId = mmCifDict.get('_pdbx_entity_nonpoly.comp_id', '')

        for (entId, desc, ligand) in zip(mdescEntId, mDescriptors, ligandId):
            if entId == entityId:
                ligandName = desc
                ligandId = ligand

    obj = getLigandEntity(ligandId, ligandType, ligandName, None, formula_weights[indx], descriptions[indx], None,
                          None, None, None, None, None, None)
    return obj, quantity[indx]


def getPubChemData(inChIKey, ligandId, ligandName):
    '''
    Get PuChem ID, inChIKey, inChI, isomericSMILES, canonicalSMILES, formula and formula_weight given ligand inChIKey, id or name by means of PuChem-WS
    '''

    # print('---> getPubChemData', inChIKey, ligandId, ligandName)
    pubChemCompoundId = ''
    if inChIKey:
        # print('----> searching by', inChIKey)
        pubChemCompoundId = getDataFromPubChem(
            url=PUBCHEM_WS_URL + 'inchikey/' + inChIKey + '/cids/JSON', jKey='CID')
    if (not pubChemCompoundId) and ligandId:
        # print('----> searching by', ligandId)
        pubChemCompoundId = getDataFromPubChem(
            url=PUBCHEM_WS_URL + 'xref/RegistryID/' + ligandId + '/cids/JSON', jKey='CID')
    if (not pubChemCompoundId) and ligandName:
        # clean the compound name a bit
        ligandName = ligandName.replace('(+/-)', ' ')
        ligandName = ligandName.replace('?', ' ')
        ligandName = ligandName.strip()
        # print('----> searching by', ligandName)
        pubChemCompoundId = getDataFromPubChem(
            url=PUBCHEM_WS_URL + 'name/' + ligandName + '/cids/JSON', jKey='CID')
    if isinstance(pubChemCompoundId, list):
        # print("----> CID:", pubChemCompoundId)
        pubChemCompoundId = pubChemCompoundId[0]

    # if Compound PubChem ID can not be found
    if not pubChemCompoundId:
        return None, None, None, None, None, None, None

    inChIKey = getDataFromPubChem(url=PUBCHEM_WS_URL +
                                  'cid/' + str(pubChemCompoundId) +
                                  '/property/InChIKey/json', jKey='InChIKey')
    inChI = getDataFromPubChem(url=PUBCHEM_WS_URL + 'cid/' + str(pubChemCompoundId) +
                               '/property/InChI/json', jKey='InChI')
    isomericSMILES = getDataFromPubChem(url=PUBCHEM_WS_URL + 'cid/' + str(pubChemCompoundId) +
                                        '/property/isomericSMILES/json', jKey='IsomericSMILES')
    canonicalSMILES = getDataFromPubChem(url=PUBCHEM_WS_URL + 'cid/' + str(pubChemCompoundId) +
                                         '/property/CanonicalSMILES/json', jKey='CanonicalSMILES')
    formula = getDataFromPubChem(url=PUBCHEM_WS_URL + 'cid/' + str(pubChemCompoundId) +
                                 '/property/MolecularFormula/json', jKey='MolecularFormula')
    formula_weight = getDataFromPubChem(url=PUBCHEM_WS_URL + 'cid/' + str(pubChemCompoundId) +
                                        '/property/MolecularWeight/json', jKey='MolecularWeight')

    return pubChemCompoundId, inChIKey, inChI, isomericSMILES, canonicalSMILES, formula, formula_weight


def updatePdbToLigand(pdbObj, ligandObj, quantity=1):
    obj = None
    try:
        obj, created = PdbToLigand.objects.update_or_create(
            pdbId=pdbObj,
            ligand=ligandObj,
            defaults={
                'quantity': quantity,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getPdbToLigandListmmCifFile(ligandType, mmCifDict, pdbObj):
    objList = []
    entityIds = mmCifDict.get('_entity.id', '')
    types = mmCifDict.get('_entity.type', '')

    for indx, entityId in enumerate(entityIds):
        if types[indx] == ligandType:
            ligandObj, quantity = updateLigandEntitymmCifFile(
                ligandType, indx, entityId, mmCifDict)
            # # PDB-Ligand
            pdbLigandOgj = updatePdbToLigand(pdbObj, ligandObj, quantity)
            objList.append(pdbLigandOgj)
        if types[indx] == 'non-polymer':
            pass
    return objList


def getRefinedModelPDBRedo(pdbObj):
    refModel = None
    entryId = pdbObj.dbId.lower()
    url = URL_PDB_REDO + 'db/' + entryId
    try:
        resp = requests.head(url, timeout=HTTP_TIMEOUT)
        print('Connecting', url)
        if resp.status_code == 200:
            # print('-->>> response', resp.status_code)
            refModelSource = RefinedModelSource.objects.get(name='PDB-REDO')
            refModelMethod = RefinedModelMethod.objects.get(
                source=refModelSource, name='PDB-Redo')
            refModel = updateRefinedModel(
                None, pdbObj, refModelSource, refModelMethod, entryId + '_final.pdb', url,
                URL_PDB_REDO_QUERY + entryId, '')
    except requests.ConnectionError:
        print("Can't find PDB-Redo model: failed to connect", url)
    return refModel


def getRefinedModelCeres(pdbObj, emdbObj):
    refModel = None
    pdbId = pdbObj.dbId.lower()
    emdbId = emdbObj.dbId.replace("EMD-", "")
    entry_date = datetime.today().strftime("%m_%Y")  # 0 padded, i.e.: 04_2022
    # entry_date = datetime.today().strftime("02_%Y")  # 0 padded, i.e.: 04_2022
    # https://cci.lbl.gov/ceres/goto_entry/7vdf_31916/04_2022
    url = URL_PHENIX_CERES + '/goto_entry/' + \
        pdbId + '_' + emdbId + '/' + entry_date
    try:
        print('Connecting', url)
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            # print('-->>> response', resp.status_code)
            if resp.text.find('Does not exist') == -1:
                # print('-->>> Found CERES refModel', pdbId, emdbId)
                refModelSource = RefinedModelSource.objects.get(name='Phenix')
                refModelMethod = RefinedModelMethod.objects.get(
                    source=refModelSource, name='CERES')
                refModel = updateRefinedModel(
                    emdbObj=emdbObj,
                    pdbObj=pdbObj,
                    sourceObj=refModelSource,
                    methodObj=refModelMethod,
                    filename=pdbId + '_' + emdbId + '_' + 'trim_real_space_refined_000.pdb',
                    externalLink=url,
                    queryLink=URL_PHENIX_CERES_QUERY,
                    details='')
            # else:
                # print('-->>> No entry found', )
    except requests.ConnectionError:
        print("Can't find PDB-Redo model: failed to connect", url)
    return refModel


def updateAuthor(name, orcid):
    obj = None
    try:
        obj, created = Author.objects.update_or_create(
            name=name,
            orcid=orcid,
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getPdbEntryAuthors(mmCifDict, pdbObj):
    auths = []
    # _audit_author.name
    # _audit_author.pdbx_ordinal
    # _audit_author.identifier_ORCID
    names = mmCifDict.get('_audit_author.name', '')
    orcids = mmCifDict.get('_audit_author.identifier_ORCID', '')
    ordinals = mmCifDict.get('_audit_author.pdbx_ordinal', '')
    for idx, name in enumerate(names):
        orcid = orcids[idx].replace('?', '') if orcids else ''
        ordinal = ordinals[idx].replace('?', '') if ordinals else ''
        # authorObj = updatePdbEntryAuthor(name, orcid, ordinal, pdbObj)
        authorObj = updateAuthor(name, orcid)
        pdbObj.dbauthors.add(authorObj)
        auths.append(authorObj)
    return auths


def updateSampleEntity(name, exprSystem,
                       assembly, ass_method, ass_details,
                       macromolecules, uniProts, genes,
                       bioFunction, bioProcess, cellComponent, domains):
    obj = None
    try:
        obj, created = SampleEntity.objects.update_or_create(
            name=name,
            exprSystem=exprSystem,
            assembly=assembly,
            ass_method=ass_method,
            ass_details=ass_details[:200],
            macromolecules=macromolecules,
            uniProts=uniProts,
            genes=genes,
            bioFunction=bioFunction,
            bioProcess=bioProcess,
            cellComponent=cellComponent,
            domains=domains,
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getSampleDetails(mmCifDict):

    exprSystem = mmCifDict.get(
        '_entity_src_gen.pdbx_host_org_scientific_name', '')
    assembly = mmCifDict.get('_pdbx_struct_assembly.details', '')
    ass_method = mmCifDict.get('_pdbx_struct_assembly.method_details', '')
    ass_details = mmCifDict.get('_pdbx_struct_assembly.oligomeric_details', '')
    genes = mmCifDict.get('_entity_src_gen.pdbx_gene_src_gene', '')
    name = mmCifDict.get('_entry.id', '')
    macromolecules = ''
    uniProts = ''
    bioFunction = ''
    bioProcess = ''
    cellComponent = ''
    domains = ''
    sampleObj = updateSampleEntity(
        name=name[0].replace('?', '') if name else '',
        exprSystem=exprSystem[0].replace('?', '') if exprSystem else '',
        assembly=assembly[0].replace('?', '') if exprSystem else '',
        ass_method=ass_method[0].replace('?', '') if exprSystem else '',
        ass_details=ass_details[0][:200].replace(
            '?', '') if exprSystem else '',
        macromolecules='',
        uniProts='',
        genes=''.join(genes).replace('?', ''),
        bioFunction='',
        bioProcess='',
        cellComponent='',
        domains='',)
    return sampleObj


def updatePdbEntryDetails(mmCifDict, pdbObj):
    obj = None
    # get Sample
    sample = getSampleDetails(mmCifDict)

    try:
        obj, created = PdbEntryDetails.objects.update_or_create(
            pdbentry=pdbObj,
            sample=sample,
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


# ========== ========== ========== ========== ========== ========== ==========


def updateFeatureType(name, description, dataSource, externalLink):
    """
    Update FeatureType entry
    """
    obj = None
    try:
        obj, created = FeatureType.objects.update_or_create(
            name=name,
            description=description,
            dataSource=dataSource,
            externalLink=externalLink)
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getOrganism(taxonomy_id, scientific_name='', common_name=''):
    """
    Get Organism entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = Organism.objects.get_or_create(
            ncbi_taxonomy_id=taxonomy_id,
            defaults={
                'scientific_name': scientific_name,
                'common_name': common_name,
                'externalLink': URL_NCBI_TAXONOMY + taxonomy_id,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)

    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getAuthor(name, email='', address='', orcid='', role=''):
    """
    Get Author entry or create in case it does not exist
    """
    obj = None

    if orcid != '':  # When orcid is specified
        try:
            obj, created = Author.objects.get_or_create(
                orcid=orcid,
                defaults={
                    'name': name,
                    'email': email,
                    'address': address,
                    'role': role
                }
            )
            if created:
                logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
                print('Created new', obj.__class__.__name__, obj)
            else:
                logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
                print('Updated', obj.__class__.__name__, obj)

        except Exception as exc:
            logger.exception(exc)
            print(exc, os.strerror)

    else:  # When orcid is not specified
        try:
            obj, created = Author.objects.get_or_create(
                name=name,
                defaults={
                    'orcid': orcid,
                    'email': email,
                    'address': address,
                    'role': role
                }
            )
            if created:
                logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
                print('Created new', obj.__class__.__name__, obj)
            else:
                logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
                print('Updated', obj.__class__.__name__, obj)

        except Exception as exc:
            logger.exception(exc)
            print(exc, os.strerror)

    return obj


def updateAuthorFromIDR(name, email='', address='', orcid='', role=''):
    """
    Update Author entry with Contact Details or create in case it does not exist
    """
    obj = None
    try:
        obj, created = Author.objects.update_or_create(
            name__contains=name,
            defaults={
                'email': email,
                'address': address,
                'orcid': orcid,
                'role': role}
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateAssayEntity(dbId, name, featureType, description, externalLink, details, screenCount, BIAId, releaseDate, dataDoi):
    """
    Update AssayEntity entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = AssayEntity.objects.update_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'featureType': featureType,
                'description': description,
                'externalLink': externalLink,
                'details': details[:200],
                'screenCount': screenCount,
                'BIAId': BIAId,
                'releaseDate': releaseDate,
                'dataDoi': dataDoi
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateScreenEntity(dbId, name, description, sampleType, plateCount, dataDoi, assay):
    """
    Update ScreenEntity entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = ScreenEntity.objects.update_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'description': description,
                'sampleType': sampleType,
                'plateCount': plateCount,
                'dataDoi': dataDoi,
                'assay': assay,
            }
        )
        if created:
            logger.debug(' %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def createHTTPSession():
    '''
    Create HTTP session with OMERO server for IDR queries
    '''

    with requests.Session() as session:
        request = requests.Request('GET', URL_IDR_INDEX_PAGE)
        prepped = session.prepare_request(request)
        response = session.send(prepped)
        if response.status_code != 200:
            response.raise_for_status()

    return session


def getScreenId(session, key, value, screenDir):
    '''
    Get screen ID using IDR Web API query
    '''

    # Set url variables
    qs = {'key': key, 'value': value}
    url = URL_SCREENS_PROJECTS.format(**qs)

    resp = session.get(url)
    if resp.status_code != 200:
        return None
    screens_projects_json = session.get(url).json()

    # Get screen ID given screen dir (e.g. idr0094-ellinger-sarscov2/screenA)
    for s in screens_projects_json['screens']:
        if screenDir in s['name']:
            return s['id']


def getScreenDataframe(session, screenId):
    '''
    Get screen dataframe including plate, ligand, and well data from OMERO webgateway
    '''

    # Set url variables
    qs = {'screenId': screenId}
    url = URL_SCREEN_TABLE.format(**qs)

    # Create a dataframe from "data" key in json output from url
    resp = session.get(url)
    if resp.status_code != 200:
        return None
    jsonData = session.get(url).json()
    columns = jsonData['data']['columns']
    data = jsonData['data']['rows']
    df = pd.DataFrame(data, columns=columns).convert_dtypes()

    # Get column names that could harbor float values (i.e. micromolecular concentration and percentage of inhibition)
    mc_colName = getColNameByKW(df.columns, 'micromolar', 'concentration')
    pi_colName = getColNameByKW(df.columns, 'percentage', 'inhibition')

    # Replace commans ',' with dots '.' to avoid string to float conversion issues
    df[pi_colName] = df[pi_colName].str.replace(',', '.')

    if mc_colName != None:
        df[mc_colName] = df[mc_colName].str.replace(',', '.')

    return df


def updatePlateEntity(dbId, name, screen):
    """
    Update PlateEntity entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = PlateEntity.objects.update_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'screen': screen
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)

    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateWellEntity(dbId, name, description, ligand, plate, externalLink, imageThumbailLink, imagesIds, cellLine, controlType, qualityControl, micromolarConcentration, percentageInhibition, hitOver75Activity, numberCells, phenotypeAnnotationLevel, channels):
    """
    Update WellEntity entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = WellEntity.objects.get_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'description': description,
                'ligand': ligand,
                'plate': plate,
                'externalLink': externalLink,
                'imageThumbailLink': imageThumbailLink,
                'imagesIds': imagesIds,
                'cellLine': cellLine,
                'controlType': controlType,
                'qualityControl': qualityControl,
                'micromolarConcentration': micromolarConcentration,
                'percentageInhibition': percentageInhibition,
                'hitOver75Activity': hitOver75Activity,
                'numberCells': numberCells,
                'phenotypeAnnotationLevel': phenotypeAnnotationLevel,
                'channels': channels
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
        logger.debug("Well not created or updated: %s", obj)
    return obj


def getImageIdsFromWellId(session, wellId):
    '''
    Get image IDs associated to a specific well using well ID through IDR Web API
    '''

    # Set url variables
    qs = {'key': 'well', 'keyId': wellId}
    url = URL_ATTR_KEY.format(**qs)
    well_attr_json = session.get(url).json()

    # Get screen ID given screen dir (e.g. idr0094-ellinger-sarscov2/screenA)
    imageIds = []
    for wellSample in well_attr_json['data']['WellSamples']:
        imageIds.append(wellSample['Image']['@id'])

    return imageIds


def getColNameByKW(colNames, keyword1, keyword2):
    '''
    Get the column name from a list of column names that match with 2 given keywords
    '''

    REGEX_KEYWORD = '(?=.*{keyword1})(?=.*{keyword2}).*$'.format(**
                                                                 {'keyword1': keyword1, 'keyword2': keyword2})

    for colName in colNames:
        if re.match(REGEX_KEYWORD, colName.lower()):
            return colName


def getLigandEntity(dbId, ligandType, name, formula, formula_weight, details, altNames,
                    pubChemCompoundId, systematicNames, IUPACInChI, IUPACInChIkey, isomericSMILES, canonicalSMILES):
    """
    Get LigandEntity entry given IUPAC InChIKey. 
    In case it does not exist, create it given ligand id (from ChEBI) or name by means of PubChem-WS.
    Export the names of the ligands whose InChIKey cannot be found using PubChem-WS.
    Returns LigandEntity entry.
    """

    obj = None
    try:
        # first look if the compound is already in the DB
        obj = LigandEntity.objects.get(pk=IUPACInChIkey)
        # print("Found in DB Compound ", obj)
    except LigandEntity.DoesNotExist:
        # get data from PubChem by ligandId or ligandName
        pubChemCompoundId, IUPACInChIkey, IUPACInChI, isomericSMILES, canonicalSMILES, formula, formula_weight = getPubChemData(
            IUPACInChIkey, dbId, name)
        if not IUPACInChIkey:
            print('---> NOT INCHIKEY FOUND IN PubChem-WS FOR COMPOUND:', dbId, name, pubChemCompoundId, IUPACInChIkey,
                  IUPACInChI, isomericSMILES, canonicalSMILES, formula, formula_weight)
            save2file(data=[dbId, name, pubChemCompoundId, IUPACInChIkey, IUPACInChI,
                      isomericSMILES, canonicalSMILES, formula, formula_weight],
                      path=os.path.join(PATH_DATA, 'IDR'), filename='ligands_not_found.txt')
            return None
        obj = updateLigandEntity(IUPACInChIkey, dbId, ligandType, name, formula,
                                 formula_weight, None, altNames, systematicNames, pubChemCompoundId, IUPACInChI, isomericSMILES, canonicalSMILES)
    return obj


def getAnalyses(name, relation, value, description, units, pvalue, dataComment, ligand, assay):
    """
    Get Analyses entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = Analyses.objects.get_or_create(
            name=name,
            relation=relation,
            value=value,
            description=description,
            units=units,
            pvalue=pvalue,
            dataComment=dataComment,
            ligand=ligand,
            assay=assay,
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)

    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def getOntology(dbId, name, description, externalLink, queryLink):
    """
    Get Ontology entry or create in case it does not exist
    """
    obj = None
    try:
        obj, created = Ontology.objects.get_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'description': description,
                'externalLink': externalLink,
                'queryLink': queryLink,
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateOntologyTerm(dbId, name, description, externalLink, source):
    """
    Update OntologyTerm entry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = OntologyTerm.objects.update_or_create(
            dbId=dbId,
            defaults={
                'name': name,
                'description': description,
                'externalLink': externalLink,
                'source': source,
            }
        )
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)

    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def detect_getOntologyByDbId(OntTermId):
    '''
    Detect the ontology depending on the OntologyTerm Id and get/create the Ontology entry.
    '''

    # Get Ontology ID
    matchObj = re.match(REGEX_ONTOLOGY_ID, OntTermId)
    if matchObj:
        dbId = matchObj.group(1)

    if 'efo' in dbId.lower():
        dbId = 'EFO'
        name = 'Experimental Factor Ontology'
        description = 'The Experimental Factor Ontology (EFO) provides a systematic description of many experimental variables available in EBI databases, and for external projects such as the NHGRI GWAS catalogue. It combines parts of several biological ontologies, such as anatomy, disease and chemical compounds. The scope of EFO is to support the annotation, analysis and visualization of data handled by many groups at the EBI and as the core ontology for OpenTargets.org'
        externalLink = 'http://www.ebi.ac.uk/efo/'
        queryLink = 'http://www.ebi.ac.uk/efo/'
    elif 'bao' in dbId.lower():
        dbId = 'BAO'
        name = 'BioAssay Ontology'
        description = 'The BioAssay Ontology (BAO) describes biological screening assays and their results including high-throughput screening (HTS) data for the purpose of categorizing assays and data analysis. BAO is an extensible, knowledge-based, highly expressive (currently SHOIQ(D)) description of biological assays making use of descriptive logic based features of the Web Ontology Language (OWL). BAO currently has over 700 classes and also makes use of several other ontologies. It describes several concepts related to biological screening, including Perturbagen, Format, Meta Target, Design, Detection Technology, and Endpoint. '
        externalLink = 'http://bioassayontology.org'
        queryLink = 'http://www.bioassayontology.org/bao%23'
    elif 'fbbi' in dbId.lower():
        dbId = 'FBbi'
        name = 'Biological Imaging Methods Ontology'
        description = 'A structured controlled vocabulary of sample preparation, visualization and imaging methods used in biomedical research'
        externalLink = 'http://cellimagelibrary.org/'
        queryLink = 'http://purl.obolibrary.org/obo/'
    elif 'uo' in dbId.lower():
        dbId = 'UO'
        name = 'Units of measurement ontology'
        description = 'A structured controlled vocabulary of sample preparation, visualization and imaging methods used in biomedical research'
        externalLink = 'http://cellimagelibrary.org/'
        queryLink = 'http://purl.obolibrary.org/obo/'
    else:
        print('Unkown ontology for %s' % (OntTermId))
        raise KeyError

    obj = getOntology(dbId, name, description, externalLink, queryLink)

    return obj


def getDataFromOLS(url, jKey, returnList=False):
    '''
    Get data specified for jkey in the JSON response for the OLS url.
    If value is a list and returnList is not True, it returns only the first item.
    If value is an integer, it returns a string. 
    '''
    jdata = ''
    try:
        resp = requests.get(url, timeout=HTTP_TIMEOUT)
        if resp.status_code == 200:
            jdata = resp.json()
            value = item_generator(jdata, jKey).__next__()
            if isinstance(value, list) and not returnList:
                # Check if value list is empty
                if value:
                    value = value[0]
                else:
                    value = ''
            if isinstance(value, int):
                value = str(value)
    except Exception as exc:
        logger.exception(exc)
        print('- >>>>',  exc, os.strerror)
    return value


def getOntologyTermDataBydbId(dbId):
    """
    Get OntologyTerm entry given database id. 
    In case it does not exist, create it by means of OLS-WS.
    Create related Ontology entry too if it does no exists.
    Returns OntologyTerm entry.
    """
    obj = None
    try:
        # first look if the OntologyTerm entry is already in the DB
        obj = OntologyTerm.objects.get(pk=dbId)
    except OntologyTerm.DoesNotExist:
        # Check Ontology entry is already in the DB
        try:
            OntologyEntry = detect_getOntologyByDbId(dbId)
        except KeyError:
            print('OntologyTerm %s cannot be created due to unkown Ontology' % (dbId))

        # Get data from OLS by dbId to create OntologyTerm entry
        url = OLS_WS_URL % ('api', OntologyEntry.dbId,
                            OntologyEntry.queryLink, dbId)

        name = getDataFromOLS(url, 'label')
        description = getDataFromOLS(url, 'description')
        externalLink = OLS_WS_URL % (
            'api', OntologyEntry.dbId, OntologyEntry.queryLink, dbId)

        obj = updateOntologyTerm(
            dbId, name, description, externalLink, OntologyEntry)

    return obj


def getListOfOntologyTerms(dbId_list):
    '''
    Given a list of OntologyTerm IDs, returns a list of OntologyTerm entries
    '''
    entry_list = []
    for dbId in dbId_list:
        entry = getOntologyTermDataBydbId(dbId)
        entry_list.append(entry)

    return entry_list


class IDRUtils(object):

    def _updateAssayDirs_fromGitHub(self):
        """
        Update Assay directories in IDR from GitHub repository
        """

        # TODO: crear aqui unas lineas para que se saque un registo.txt con la fecha y el nombre de los directorios de assays
        # (idrNNNN-lastname-example) que se vayan importando para saber cuales son los dirs que quedan por hacer updateLigandEntryFromIDRAssay()
        pass

    def _updateDB_fromNonHCSAssay(self, assayPath):
        pass

    def _updateDB_fromHCSAssay(self, assayPath):
        '''
         Create FeatureType, Organism, Author, Publication, AssayEntity, ScreenEntity, 
         PlateEntityentry, LigandEntity and WellEntity for HCS Assays in IDR
        '''

        # Create http session
        session = createHTTPSession()

        # Create FeatureType for HCS Assays in IDR
        name = 'High-Content Screening Assay'
        description = 'High throughput sample analysis of collections of compounds that provide '\
            'a variety of chemically diverse structures that can be used to identify structure types '\
            'that have affinity with pharmacological targets. (Source Accession: EFO_0007553)'
        dataSource = 'The Image Data Resource (IDR)'
        externalLink = 'https://idr.openmicroscopy.org/'

        FeatureTypeEntry = updateFeatureType(
            name, description, dataSource, externalLink)

        # Get ID and metadata file for IDR assay
        matchObj = re.match(REGEX_IDR_ID, assayPath)
        if matchObj:
            assayId = matchObj.group(1)
        metadataFileExtention = '-study.txt'
        metadataFile = assayId + metadataFileExtention

        # Get Analyses files
        # TODO: Change for other types of HCS assays that do not have .csv for addicional analyses
        analysesFilePattern = '*.csv'
        analysesPattern = os.path.join(
            assayPath, 'Analyses', analysesFilePattern)

        dfs = []
        for file in glob.glob(analysesPattern):
            dfs.append(pd.read_csv(file, sep=';'))
        if not dfs:
            # send exception
            print("ERROR: No files found", analysesPattern)
            exit(2)
        analysesDf = pd.concat(dfs)

        # Fix compound name
        analysesDf = analysesDf.replace(
            {
                np.nan: None,
                'THIOGUANINE': 'TIOGUANINE'  # TODO: solucionar esto
            }
        )

        # Get columns names in analyses dataframe
        n_colName = getColNameByKW(analysesDf.columns, 'standard', 'type')
        r_colName = getColNameByKW(analysesDf.columns, 'standard', 'relation')
        v_colName = getColNameByKW(analysesDf.columns, 'standard', 'value')
        u_colName = getColNameByKW(
            analysesDf.columns, 'uo', 'units')  # units ontology terms
        pv_colName = getColNameByKW(analysesDf.columns, 'pchembl', 'value')
        dc_colName = getColNameByKW(analysesDf.columns, 'data', 'comment')
        l_colName = getColNameByKW(analysesDf.columns, 'compound', 'key')

        # Remove single quotes from relation column
        analysesDf[r_colName] = analysesDf[r_colName].str.replace("'", "")

        # Parse metadata file using StudyParser
        MetadataFilePath = os.path.join(assayPath, metadataFile)
        studyParserObj = StudyParser(MetadataFilePath)

        # Get or Create Organism entries
        # TODO: create ontology term??
        organisms = [
            organism for organism in studyParserObj.study['Study Organism'].split("\t")]
        organismTermSources = [
            termSource for termSource in studyParserObj.study['Study Organism Term Source REF'].split("\t")]
        organismTermAccessions = [
            termAccession for termAccession in studyParserObj.study['Study Organism Term Accession'].split("\t")]
        organism_entry_list = []

        for organism in zip(organisms, organismTermSources, organismTermAccessions):

            # Check that the Study Organism Term Source REF is NCBI Taxonomy
            TaxonTermSource = organism[1]
            TaxonRefMatchObj = re.match(
                REGEX_TAXON_REF, TaxonTermSource.lower())

            if TaxonRefMatchObj:
                OrganismEntry = getOrganism(
                    taxonomy_id=organism[2], scientific_name=organism[0])
                organism_entry_list.append(OrganismEntry)
            else:
                print('Study Organism Term Source REF for "%s" different from NCBI Taxonomy: '
                      '\n\tStudy Organism Term Source REF: %s \n\tStudy Organism Term Accession: %s'
                      % (organism[0], TaxonTermSource, organism[2]))

        # Create Author and Publication entries
        publication_entry_list = []

        for publication in studyParserObj.study['Publications']:
            author_entry_list = []

            for author in publication['Author List'].split(", "):
                AuthorEntry = getAuthor(name=author)
                author_entry_list.append(AuthorEntry)

            PublicationEntry = updatePublication(
                title=publication['Title'],
                doi=publication['DOI'],
                pubMedId=publication['PubMed ID'],
                PMCId=publication['PMC ID'],
                journal='', issn='', issue='', volume='',
                firstPage='', lastPage='', year='')

            publication_entry_list.append(PublicationEntry)
            # Add already updated/created Author entries to Publicacion entry
            [PublicationEntry.authors.add(author)
             for author in author_entry_list]

        # Update Author entries with "Study Contacts" details if exist.
        authorLastNames = [
            authorLastName for authorLastName in studyParserObj.study['Study Person Last Name'].split("\t")]
        authorFirstNames = [
            authorFirstName for authorFirstName in studyParserObj.study['Study Person First Name'].split("\t")]
        authorEmails = [
            authorEmail for authorEmail in studyParserObj.study['Study Person Email'].split("\t")]
        authorAddresses = [
            authorAddress for authorAddress in studyParserObj.study['Study Person Address'].split("\t")]
        authorORCIDs = [
            authorORCID for authorORCID in studyParserObj.study['Study Person ORCID'].split("\t")]
        authorRoles = [
            authorRole for authorRole in studyParserObj.study['Study Person Roles'].split("\t")]

        for authorEntry in zip(authorLastNames, authorFirstNames, authorEmails, authorAddresses, authorORCIDs, authorRoles):

            # NOTE: pseudoName tries to mimic Author entry name from publication['Author List']
            # although middle names would be missing. E.g:
            # Carpenter AE (Author entry name from publication['Author List']);
            # Carpenter A (Author entry name from study['Study Person Last Name'] + study['Study Person First Name'])

            pseudoName = ' '.join([authorEntry[0], authorEntry[1][0]])

            AuthorEntry = updateAuthorFromIDR(
                name=pseudoName,
                email=authorEntry[2],
                address=authorEntry[3],
                orcid=authorEntry[4],
                role=authorEntry[5]
            )

        # Create Ontology, OntologyTerm entries for AssayEntity type
        assayTypes = getListOfOntologyTerms(
            studyParserObj.study['Study Type Term Accession'].split("\t"))

        # Create Assay entry
        AssayEntityEntry = updateAssayEntity(
            name=studyParserObj.study['Study Title'],
            featureType=FeatureTypeEntry,
            description=studyParserObj.study['Study Description'],
            externalLink='',
            details=studyParserObj.study['Study Key Words'],
            dbId=assayId,
            screenCount=studyParserObj.study['Study Screens Number'],
            BIAId=studyParserObj.study['Study BioImage Archive Accession'],
            releaseDate=studyParserObj.study['Study Public Release Date'],
            dataDoi=studyParserObj.study['Data DOI'],
        )

        # Add already updated/created Author Publicacion and OntologyTerm entries to AssayEntity entry
        [AssayEntityEntry.organisms.add(orgEnt)
         for orgEnt in organism_entry_list]
        [AssayEntityEntry.publications.add(pubEnt)
         for pubEnt in publication_entry_list]
        [AssayEntityEntry.assayTypes.add(type) for type in assayTypes]

        # Create ScreenEntity entries
        for screen in studyParserObj.components:

            # Get screen name
            screenDir = screen['Comment\\[IDR Screen Name\\]']
            screenNameMatchObj = re.match(REGEX_SCREEN_NAME, screenDir)
            screenName = ' '.join(
                [screenNameMatchObj.group(1), screenNameMatchObj.group(2)])

            # Get screen id
            screenId = getScreenId(
                session,
                key='organism',
                value='Severe acute respiratory syndrome coronavirus 2',
                screenDir=screenDir,
            )

            # Create Ontology, OntologyTerm entries for ScreenEntity imagingMethods, screenTypes and technologyTypes
            imagingMethods = getListOfOntologyTerms(
                screen['Screen Imaging Method Term Accession'].split("\t"))
            screenTypes = getListOfOntologyTerms(
                screen['Screen Type Term Accession'].split("\t"))
            technologyTypes = getListOfOntologyTerms(
                screen['Screen Technology Type Term Accession'].split("\t"))

            ScreenEntityEntry = updateScreenEntity(
                dbId=screenId,
                name=screenName,
                description=screen['Screen Description'],
                sampleType=screen['Screen Sample Type'],
                # plateCount=plateCount,
                plateCount=None,
                dataDoi=screen['Screen Data DOI'],
                assay=AssayEntityEntry,
            )

            # Add OntologyTerm entries to ScreenEntity
            if ScreenEntityEntry:
                if imagingMethods:
                    [ScreenEntityEntry.imagingMethods.add(
                        method) for method in imagingMethods]
                if screenTypes:
                    [ScreenEntityEntry.screenTypes.add(
                        type) for type in screenTypes]
                if technologyTypes:
                    [ScreenEntityEntry.technologyTypes.add(
                        techtype) for techtype in technologyTypes]

            # Create PlateEntity, LigandEntity and WellEntity entries
            screenDf = getScreenDataframe(session, screenId)
            if screenDf.empty:
                continue
            for index, row in screenDf.iterrows():
                PlateEntityEntry = updatePlateEntity(
                    dbId=row['Plate'],
                    name=row['Plate Name'],
                    screen=ScreenEntityEntry,
                )

                # Get well ID and image ID associated to it
                wellId = row['Well']
                wellImageIds = getImageIdsFromWellId(session, wellId)

                # Get column names in screen DF that harbor key well attributes
                cl_colName = getColNameByKW(
                    screenDf.columns, 'accession', '3')  # cellLine ontology terms
                ct_colName = getColNameByKW(
                    screenDf.columns, 'control', 'type')
                qc_colName = getColNameByKW(
                    screenDf.columns, 'control', 'quality')
                mc_colName = getColNameByKW(
                    screenDf.columns, 'micromolar', 'concentration')
                pi_colName = getColNameByKW(
                    screenDf.columns, 'percentage', 'inhibition')
                ho75a_colName = getColNameByKW(
                    screenDf.columns, 'hit', 'activity')
                nc_colName = getColNameByKW(screenDf.columns, 'number', 'cell')
                pal_colName = getColNameByKW(
                    screenDf.columns, 'phenotype', 'level')
                c_colName = getColNameByKW(screenDf.columns, 'channel', '')

                # Create Ontology, OntologyTerm entries for WellEntity cellLine
                cellLineEntry = getOntologyTermDataBydbId(row[cl_colName])

                # Create WellEntity entries for unkown wells (no ligand tested and no control)
                if row['Compound Name'] == '' and row['Control Type'] == '':

                    WellEntityEntry = updateWellEntity(
                        dbId=wellId,
                        name=row['Well Name'],
                        description='Unkown details',
                        ligand=None,
                        plate=PlateEntityEntry,
                        externalLink=URL_SHOW_KEY.format(
                            **{'key': 'well', 'keyId': wellId}),
                        imageThumbailLink=URL_THUMBNAIL.format(
                            **{'imageId': wellImageIds[0]}),
                        imagesIds=wellImageIds,
                        cellLine=cellLineEntry,
                        controlType=row[ct_colName],
                        qualityControl=row[qc_colName],
                        micromolarConcentration=None,
                        percentageInhibition=float(
                            row[pi_colName]) if row[pi_colName] != '' else None,
                        hitOver75Activity=row[ho75a_colName],
                        numberCells=row[nc_colName] if row[nc_colName] != '' else None,
                        phenotypeAnnotationLevel=row[pal_colName],
                        channels=row[c_colName]
                    )

                # Create WellEntity entries for positive controls
                elif row['Compound Name'] == '' and row['Control Type'] == 'positive':

                    WellEntityEntry = updateWellEntity(
                        dbId=wellId,
                        name=row['Well Name'],
                        description='virus-treated well (no compounds). Assigned as 0% inhibition of virus cytopathicity',
                        ligand=None,
                        plate=PlateEntityEntry,
                        externalLink=URL_SHOW_KEY.format(
                            **{'key': 'well', 'keyId': wellId}),
                        imageThumbailLink=URL_THUMBNAIL.format(
                            **{'imageId': wellImageIds[0]}),
                        imagesIds=wellImageIds,
                        cellLine=cellLineEntry,
                        controlType=row[ct_colName],
                        qualityControl=row[qc_colName],
                        micromolarConcentration=None,
                        percentageInhibition=float(
                            row[pi_colName]) if row[pi_colName] != '' else None,
                        hitOver75Activity=row[ho75a_colName],
                        numberCells=row[nc_colName] if row[nc_colName] != '' else None,
                        phenotypeAnnotationLevel=row[pal_colName],
                        channels=row[c_colName]
                    )

                # Create WellEntity entries for negative controls
                elif row['Compound Name'] == '' and row['Control Type'] == 'negative':

                    WellEntityEntry = updateWellEntity(
                        dbId=wellId,
                        name=row['Well Name'],
                        description='no-virus- and no-compounds-treated well. Assigned as 100% inhibition of virus cytopathicity',
                        ligand=None,
                        plate=PlateEntityEntry,
                        externalLink=URL_SHOW_KEY.format(
                            **{'key': 'well', 'keyId': wellId}),
                        imageThumbailLink=URL_THUMBNAIL.format(
                            **{'imageId': wellImageIds[0]}),
                        imagesIds=wellImageIds,
                        cellLine=cellLineEntry,
                        controlType=row[ct_colName],
                        qualityControl=row[qc_colName],
                        micromolarConcentration=None,
                        percentageInhibition=float(
                            row[pi_colName]) if row[pi_colName] != '' else None,
                        hitOver75Activity=row[ho75a_colName],
                        numberCells=row[nc_colName] if row[nc_colName] != '' else None,
                        phenotypeAnnotationLevel=row[pal_colName],
                        channels=row[c_colName]
                    )

                # Create WellEntity entries with ligand
                else:
                    # Get column names in screen DF that harbor key ligand attributes
                    ln_colName = getColNameByKW(
                        screenDf.columns, 'compound', 'name')
                    pci_colName = getColNameByKW(
                        screenDf.columns, 'pubchem', 'id')
                    icik_colName = getColNameByKW(
                        screenDf.columns, 'inchikey', '')
                    sm_colName = getColNameByKW(screenDf.columns, 'smiles', '')

                    # Create LigandEntity entry
                    LigandEntityEntry = getLigandEntity(
                        dbId=None,
                        ligandType=None,
                        name=row[ln_colName],
                        formula=None,
                        formula_weight=None,
                        details=None,
                        altNames=None,
                        pubChemCompoundId=row[pci_colName],
                        systematicNames=None,
                        IUPACInChI=None,
                        IUPACInChIkey=row[icik_colName],
                        isomericSMILES=None,
                        canonicalSMILES=row[sm_colName],
                    )

                    # Update or create WellEntity
                    WellEntityEntry = updateWellEntity(
                        dbId=wellId,
                        name=row['Well Name'],
                        description='well treated with virus and compound',
                        ligand=LigandEntityEntry,
                        plate=PlateEntityEntry,
                        externalLink=URL_SHOW_KEY.format(
                            **{'key': 'well', 'keyId': wellId}),
                        imageThumbailLink=URL_THUMBNAIL.format(
                            **{'imageId': wellImageIds[0]}),
                        imagesIds=wellImageIds,
                        cellLine=cellLineEntry,
                        controlType=row[ct_colName],
                        qualityControl=row[qc_colName],
                        micromolarConcentration=row[mc_colName] if mc_colName else (
                            10.0 if assayId == 'idr0094' else None),
                        percentageInhibition=float(
                            row[pi_colName]) if row[pi_colName] != '' else None,
                        hitOver75Activity=row[ho75a_colName],
                        numberCells=row[nc_colName] if row[nc_colName] != '' else None,
                        phenotypeAnnotationLevel=row[pal_colName],
                        channels=row[c_colName]
                    )

                    if LigandEntityEntry:
                        # Check if LigandEntityEntry is in analyses dataframe and get ligand indexes
                        indexes = [i for i, elem in enumerate(analysesDf[l_colName].tolist(
                        )) if elem.upper() == LigandEntityEntry.name.upper()]

                        # Set Analyses description attribute
                        if indexes:
                            for index, row in analysesDf.iloc[indexes].iterrows():
                                if row[n_colName].lower() == 'ic50':
                                    description = 'The half maximal inhibitory concentration (IC50) is a measure of the potency of a substance in inhibiting a specific biological or biochemical function.'
                                elif row[n_colName].lower() == 'cc50':
                                    description = 'The 50% cytotoxic concentration (CC50) is the concentration of test compound  that reduced the cell viability by 50% when compared to untreated controls'
                                elif row[n_colName].lower() == 'selectivity index':
                                    description = 'The selectivity index (SI) is defined as the ratio of cytotoxicity to biological activity, which means the ratio of the 50% cytotoxic concentration, CC50, to the 50% antiviral concentration, IC50, (CC50/IC50)'

                                # Create Ontology, OntologyTerm entries for Analyses units
                                if row[u_colName] is not None:
                                    unitsEntry = getOntologyTermDataBydbId(
                                        row[u_colName])
                                else:
                                    unitsEntry = None

                                # Create Analyses entry
                                getAnalyses(
                                    name=row[n_colName],
                                    relation=row[r_colName],
                                    value=row[v_colName],
                                    description=description,
                                    units=unitsEntry,
                                    pvalue=row[pv_colName],
                                    dataComment=row[dc_colName],
                                    ligand=LigandEntityEntry,
                                    assay=AssayEntityEntry,
                                )


# ========== ========== ========== ========== ========== ========== ==========

def readInputFile(filename):
    df = pd.read_csv(filename, sep=';')
    return df


def init_uniprot_entry(filepath):
    # Create dataframe from file
    df = readInputFile(filepath)

    # Create UniProtEntry for each row
    for index, row in df.iterrows():
        uniprotentry = updateUniProtEntry(
            db_accession=row['db_accession'],
            db_code=row['db_code'],
        )


def getUniProtEntry(db_accession, db_code):
    """
    Get UniProtEntry or create in case it does not exist
    """

    obj = None
    try:
        obj, created = UniProtEntry.objects.get_or_create(
            dbId=db_accession,
            defaults={
                'name': db_code,
                'externalLink': URL_UNIPROT + db_accession,
            })
        if created:
            logger.debug('Created new %s: %s', obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated %s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)

    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


# ========== ========== ========== ========== ========== ========== ==========

def findIndexInObjList(objList, key, value):
    '''
    Find index of a specific object in a list of objects given a key/value pair
    '''
    for obj in objList:
        if obj[key] == value:
            return objList.index(obj)


def preprocessColumnNames(df):
    df.rename(columns={
        'Nsp1': 'NSP1 GD',
        'Nsp2 CTD': 'NSP2 CtDR',
        'Nsp15his': 'NSP15',
        'Nsp5_Mpro': 'NSP5·GS',
        'Nsp5': 'NSP5·GHM',
        'Nsp3a': 'NSP3 UBl1',
        'Nsp3b_599': 'NSP3 MacroDomain',
        'Nsp3b+NoR': 'NSP3 MacroDomain·GS-441524',
        'Nsp3c SUD M C': 'NSP3 SUD-MC',
        'Nsp3c SUD N': 'NSP3 SUD-N',
        'nsp3d': 'NSP3 PLPro',
        'Nsp3e': 'NSP3 NAB',
        'Nsp3y': 'NSP3 Y3',
        'Nsp5 WT': 'NSP5',
        'Nsp7': 'NSP7',
        'Nsp8': 'NSP8',
        'Nsp9': 'NSP9',
        'Nsp10': 'NSP10',
        'Nsp10_Nsp16': 'NSP10·NSP16',
        'Nsp14_Nsp10': 'NSP10·NSP14',
        'ORF9a-CTD': 'Nucleoprotein CTD',
        'ORF9a-IDR-NRD-SR': 'Nucleoprotein IDR1-NTD-IDR2',
        'ORF9a-NTD': 'Nucleoprotein NTD',
        'ORF9a-NTD-SR': 'Nucleoprotein NTD-SR',
        'ORF9b': 'ORF9b',
    },
        inplace=True)

    return df


def updateFeatureModelEntity(name, featureType, description, pdbentry, uniprotentry, ligandentity, externalLink, details):
    obj = None
    try:
        obj, created = FeatureModelEntity.objects.update_or_create(
            name=name,
            featureType=featureType,
            description=description,
            defaults={
                'pdbentry': pdbentry,
                'uniprotentry': uniprotentry,
                'externalLink': externalLink,
                'ligandentity': ligandentity,
                'externalLink': externalLink,
                'details': details[:200],
            })
        if created:
            logger.debug('Created new %s: %s',
                         obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated%s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateFeatureRegionEntity(name, featureType, description, pdbentry, uniprotentry, ligandentity, externalLink, start, end, details):
    obj = None
    try:
        obj, created = FeatureRegionEntity.objects.update_or_create(
            name=name,
            featureType=featureType,
            description=description,
            defaults={
                'pdbentry': pdbentry,
                'uniprotentry': uniprotentry,
                'externalLink': externalLink,
                'ligandentity': ligandentity,
                'externalLink': externalLink,
                'start': start,
                'end': end,
                'details': details,
            })
        if created:
            logger.debug('Created new %s: %s',
                         obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated%s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updateNMRTargetToPoliprotein(uniprotentry, targetName, start, end):
    obj = None
    try:
        obj, created = NMRTargetToPoliprotein.objects.update_or_create(
            uniprotentry=uniprotentry,
            targetName=targetName,
            start=start,
            end=end
        )
        if created:
            logger.debug('Created new %s: %s',
                         obj.__class__.__name__, obj)
            print('Created new', obj.__class__.__name__, obj)
        else:
            logger.debug('Updated%s: %s', obj.__class__.__name__, obj)
            print('Updated', obj.__class__.__name__, obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def update_NMR_binding(filepath):
    """
    Update NMR data from local csv file containing all binding and not binding ligands to COVID-19 proteins.
    """
    # Create dataframe from file
    NMRdf = readInputFile(filepath)

    # Rename all column names to fit db names
    NMRdf = preprocessColumnNames(NMRdf)

    # Duplicate columns related to protein complexes and rename them
    NMRdf['NSP16·NSP10'] = NMRdf.loc[:, 'NSP10·NSP16']
    NMRdf['NSP14·NSP10'] = NMRdf.loc[:, 'NSP10·NSP14']

    # Drop ligands with no InChIKey
    NMRdf2 = NMRdf.dropna(axis=0).reset_index(drop=True)

    # Update or create FeatureType for binding and not binding results #TODO: pass this to a csv and create a custom command to import it
    featureType = updateFeatureType(
        name='NMR-based fragment screening',
        description='NMR-based screening using a well-defined fragment library for identifying hits against 25 SAR-CoV-2 proteins.',
        dataSource='The COVID19-NMR Consortium',
        externalLink='https://onlinelibrary.wiley.com/doi/10.1002/anie.202205858',
    )

    # Iterate through NMR dataframe and create LigandEntity and FeatureRegionEntity
    for column in NMRdf2.columns[8:]:  # columns for protein entities
        # rows equal binding or not binding results
        for index, row in NMRdf2[column].items():

            # Get or create LigandEntity entry
            ligandentity = getLigandEntity(
                dbId=None,
                ligandType=None,
                name=NMRdf2.iloc[index]['Ligand_ID'],
                formula=NMRdf2.iloc[index]['Formula'],
                formula_weight=None,
                details=None,
                altNames=None,
                pubChemCompoundId=NMRdf2.iloc[index]['PubChemID'],
                systematicNames=None,
                IUPACInChI=None,
                IUPACInChIkey=NMRdf2.iloc[index]['InChIKey'],
                isomericSMILES=None,
                canonicalSMILES=NMRdf2.iloc[index]['SMILES']
            )
            if not ligandentity:
                continue

            # Set FeatureRegionEntity name, description depending on column content
            if '·' in column:  # For protein complexes
                complex = column.split('·')
                item1 = complex[0]
                item2 = complex[1]

                # Find obj index in nmr list of objs given entity name and set name and description for complex-realted columns
                entityIndx = findIndexInObjList(nmrentity_list, 'name', item1)
                entity = '%s·%s' % (nmrentity_list[entityIndx]['name'], item2)

                # Set FeatureRegionEntity start and end
                start = nmrentity_list[entityIndx]['start']
                end = nmrentity_list[entityIndx]['end']
                # Get UniProt id from modelentity_list
                uniprot_acc = nmrentity_list[entityIndx]['uniprot_acc']

                name = '%s %s %s·%s' % (
                    ligandentity.name, row, nmrentity_list[entityIndx]['name'], item2)
                details = {
                    'type': row.replace(' ', '').lower(),
                    'entity': entity,
                    'start': start,
                    'end': end,
                    'uniprot_acc': uniprot_acc,
                }

                if item1 == 'NSP5':
                    description = 'NMR-based detection of fragment %s %s to target %s with additional amino acids %s in the N-terminus (monomeric version of %s in solution)' % (
                        ligandentity.name, row.lower(), nmrentity_list[entityIndx]['verbose_name'], item2, nmrentity_list[entityIndx]['name'])
                elif item1 == 'NSP3 MacroDomain':
                    description = 'NMR-based detection of fragment %s %s to target %s in complex with %s. (the active metabolite of the remdesivir)' % (
                        ligandentity.name, row.lower(), nmrentity_list[entityIndx]['verbose_name'], item2)
                else:
                    description = 'NMR-based detection of fragment %s %s to target %s in complex with %s.' % (
                        ligandentity.name, row.lower(), nmrentity_list[entityIndx]['verbose_name'], item2)

            else:
                # Find obj index in nmr list of objs given entity name and set name, description and details for non-complex-realted columns
                entityIndx = findIndexInObjList(nmrentity_list, 'name', column)
                entity = nmrentity_list[entityIndx]['name']

                # Set FeatureRegionEntity start and end
                start = nmrentity_list[entityIndx]['start']
                end = nmrentity_list[entityIndx]['end']

                # Get UniProt id from modelentity_list
                uniprot_acc = nmrentity_list[entityIndx]['uniprot_acc']

                name = '%s %s %s' % (ligandentity.name, row,
                                     nmrentity_list[entityIndx]['name'])
                description = 'NMR-based detection of fragment %s %s to target %s.' % (
                    ligandentity.name, row.lower(), nmrentity_list[entityIndx]['verbose_name'])
                details = {
                    'type': row.replace(' ', '').lower(),
                    'entity': entity,
                    'start': start,
                    'end': end,
                    'uniprot_acc': uniprot_acc,
                }

            # Get UniProtEntry given a uniprot_id
            uniprotentry = getUniProtEntry(uniprot_acc, '',)

            # Create NMRTargetToPoliprotein entry
            updateNMRTargetToPoliprotein(
                uniprotentry=uniprotentry,
                targetName=entity,
                start=start,
                end=end
            )

            # Create FeatureRegionEntity
            updateFeatureRegionEntity(
                name=name,
                featureType=featureType,
                description=description,
                pdbentry=None,
                uniprotentry=uniprotentry,
                ligandentity=ligandentity,
                externalLink='',
                start=start,
                end=end,
                details=details,
            )
