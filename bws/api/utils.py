from bs4 import BeautifulSoup
import requests
import json
import logging
import os
import re
from django.core.exceptions import ValidationError
from .dataPaths import *
from .models import *

logger = logging.getLogger(__name__)

PDB_FOLDER_PATTERN = re.compile(".*/(\d\w{3})/.*\.pdb$")

REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile('^(emd)-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile('^(pdb)\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAP2MODELQUALITY_FILE = re.compile('^\d\w{3}\.(mapq|fscq)\.pdb$')

URL_PDB_REDO = 'https://pdb-redo.eu/'
URL_PDB_REDO_QUERY = 'http://3dbionotes.cnb.csic.es/pdb_redo/'
URL_CSTF = 'https://insidecorona.net/'
URL_PHENIX_CERES = 'https://cci.lbl.gov/ceres'


logger = logging.getLogger(__name__)


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
            fileRecord = models.DataFile.objects.get(
                filename__iexact=targetFname, fileType__iexact=ENTRY_TYPES[0])
            if fileRecord:
                return os.path.join(fileRecord.path, fileRecord.filename)
            else:
                logger.debug("Not found %s in DB", targetFname)
                return None
        except (ValueError, ValidationError, models.DataFile.DoesNotExist) as exc:
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


def download_file(url, path):
    """
    Download the file from `url` and save it locally under `filename`:
    """
    local_filename = url.split('/')[-1]
    full_path = os.path.join(path, local_filename)
    logger.debug("- download file: %s %s",  url, full_path)
    print("- download file:", url, full_path)
    with requests.get(url, stream=True) as r:
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


def getGitHubFileList(url, ext=''):
    """
    Get the list of files from a GitHub repository
    """
    logger.debug("- get GitHub file list: %s %s", ext, url)
    print("- get GitHub file list:",  ext, url)
    page = requests.get(url).text
    soup = BeautifulSoup(page, 'html.parser')
    files = [node.get('href').split('/')[-1]
             for node in soup.find_all('a') if node.get('href').endswith(ext)]
    return files

# ========== ========== ========== ========== ========== ========== ==========


def update_isolde_refinements(inputfile):
    """
    Update the isolde refinement models from GitHub
    """
    logger.debug("- update isolde refinements: %s", inputfile)
    print("- update isolde refinements:", inputfile)
    if not inputfile:
        url = CSTF_GITHUB_RAW_URL + ISOLDE_REF_FNAME
        logger.debug("-- download Isolde entries list: %s", inputfile)
        print("-- download Isolde entries list:", url)
        inputfile = download_file(url, CSTF_LOCAL_PATH)

    entries = []
    print("- parse Isolde entry list:", inputfile)
    logger.debug("- parse Isolde entry list: %s", inputfile)
    parseIsoldeEntryList(inputfile, entries)

    print("- get Isolde refinement data")
    logger.debug("- get Isolde refinement data")
    getIsoldeRefinementData(entries)

    print("-- save Isolde data (JSON):", CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    logger.debug("-- save Isolde data (JSON): %s %s",
                 CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)
    save_json(entries, CSTF_LOCAL_PATH, ISOLDE_JSON_FNAME)

    print("-- get Isolde refined model")
    logger.debug("-- get Isolde refined model")
    getIsoldeRefinedModel(entries)

    print("-- get all files in Isolde data folder")
    logger.debug("-- get all files in Isolde data folder")
    getAllIsoldeDataFiles(entries, [".txt", ".mtz", ".cif"])

    print("-- update DB Isolde data")
    logger.debug("-- update DB Isolde data")
    for entry in entries:
        update_RefinedModel(entry)


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
        print("-- found:", len(entries), "entries")
        logger.debug("-- found: %s entries", len(entries))


def getIsoldeRefinementData(entries):
    """
    Get the Isolde refinement data from GitHub
    """
    for entry in entries:
        pdb_id = entry["pdbId"]
        remote_path = entry["path"]
        url = os.path.join(CSTF_GITHUB_URL, remote_path)
        print("-- get Isolde refinements for:", pdb_id, remote_path)
        logger.debug("-- get Isolde refinements for: %s %s",
                     pdb_id, remote_path)
        filenames = getGitHubFileList(url, ".pdb")
        if not filenames:
            filenames = getGitHubFileList(url, ".cif")
        for filename in filenames:
            if filename.startswith(pdb_id):
                filename = filenames[len(filenames)-1]
                print("--- found:", len(filenames), "refinements ", filename)
                logger.debug("--- found: %s refinements %s",
                             len(filenames), filename)
                entry.update({"filename": filename})
                entry.update({"refmodels": [{
                    "method": "Isolde",
                    "externalLink": url,
                    "queryLink": "%s/%s/%s" % (BIONOTES_QUERY_URL, pdb_id, filename)
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
            print("--- dowload Isolde refinements for",
                  pdb_id, entry["path"], filename)
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
        print("--- get all Isolde refinement files for", pdb_id, remote_path)
        logger.debug("--- get all Isolde refinement files for %s %s",
                     pdb_id, remote_path)
        for ext in [".txt", ".mtz", ".cif"]:
            filenames = getGitHubFileList(url, ext)
            for filename in filenames:
                download_file(os.path.join(url_raw, filename), os.path.join(
                    ISOLDE_LOCAL_DATA_PATH, pdb_id[1:3], pdb_id))


def update_RefinedModelSource(name, description, externalLink):
    """
    Update a RefinedModelSource intry in the DB table
    """
    obj = None
    try:
        obj, created = RefinedModelSource.objects.update_or_create(
            name=name,
            defaults={
                'description': description if description else '',
                'externalLink': externalLink if externalLink else '',
            })
        if created:
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def findRefinedModelSource(name):
    """
    Find a RefinedModelSource entry in the DB table
    """
    obj = None
    try:
        obj = RefinedModelSource.objects.get(name=name)
        logger.debug('Found: %s', obj)
        print('Found', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def findRefinedModelMethod(name):
    """
    Find a RefinedModelMethod entry in the DB table
    """
    obj = None
    try:
        obj = RefinedModelMethod.objects.get(name=name)
        logger.debug('Found: %s', obj)
        print('Found', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


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
                'details': details if details else '',
            })
        if created:
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def initBaseTables():
    """
    Initialize some base tables
    """
    print('Initializing base tables', 'RefinedModelSources')
    initRefinedModelSources()
    initRefinedModelMethods()


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

    print('Initializing Refined Model Source', 'Phenix')
    source = updateRefinedModelSource(
        'Phenix',
        'Re-refined models deposited in the Protein Data Bank that have map resolutions better than 5Å automatically obtained using the latest version of phenix.real_space_refine within the Phenix software package.',
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

    print('Initializing Refined Model Method', 'CERES')
    method = updateRefinedModelMethod(
        RefinedModelSource.objects.get(name='Phenix'),
        'CERES',
        'CERES - the Cryo-EM re-refinement system provides automatically re-refined models deposited in the Protein Data Bank that have map resolutions better than 5Å, using the latest version of phenix.real_space_refine within the Phenix software package.',
        URL_PHENIX_CERES)


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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj
