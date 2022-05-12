import fnmatch
from Bio.PDB import MMCIF2Dict
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import json
import logging
import os
import re
from django.core.exceptions import ValidationError
from .dataPaths import *
from .models import *


STATUS = {"REL": "Released",
          "UNREL": "Unreleased",
          "HPUB": "Header released",
          "HOLD1": "1 year hold",
          "HOLD2": "2 year hold"}
FILE_EXT_PATTERN = '*.cif'


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

# ========== ========== ========== ========== ========== ========== ==========


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
        print('Found', obj)
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
        print('Found', obj)
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


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


# ========== ========== ========== ========== ========== ========== ==========

def getStructuresFromPath(path):

    logger.debug("Updating Structure entries from : %s", path)
    print("Updating Structure entries from", path)

    objs = []

    try:
        # Get files from path
        filenames = getCifFiles(path)

        for filename in filenames:
            entryId = filename.replace('.cif', '')

            # Read mmCIF to dictionary
            mmCifDict = fileCif2Json(path, filename)
            obj = readmmCifFile(mmCifDict)
            # break

    except Exception as exc:
        logger.exception(exc)
        print(exc)
    return objs


def getCifFiles(path, pattern='*.cif'):
    fileList = []
    for root, dirs, files in os.walk(path):
        for filename in fnmatch.filter(files, pattern):
            fileList.append(filename)
    return fileList


def fileCif2Json(path, filename):
    filepath = os.path.join(path, filename)
    # filepath = os.path.join(path, filename[1:3], filename)
    mmcif_dict = MMCIF2Dict.MMCIF2Dict(filepath)
    return mmcif_dict


def readmmCifFile(mmCifDict):
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
    branchedligandList = getPdbToLigandListmmCifFile(
        'branched', mmCifDict, pdbObj)

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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
                'details': details[indx].replace('?', '') if details[indx] else '',
                'mutation': mutations[indx].replace('?', '') if mutations[indx] else '',
                'uniprotAcc': uniprotObj,
                'organism': organismObj,
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
    return obj, quantity[indx]


def updatePdbToEntity(pdbObj, polymerObj, quantity=1):
    obj = None
    try:
        obj, created = PdbToEntity.objects.update_or_create(
            pdbId=pdbObj,
            entity=polymerObj,
            defaults={
                'quantity': quantity,
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


def getPdbToEntityListmmCifFile(mmCifDict, pdbObj):
    objList = []
    types = mmCifDict.get('_entity.type', '')
    entity_ids = mmCifDict.get('_entity.id', '')
    unp_db_names = mmCifDict.get('_struct_ref.db_name', '')
    unp_db_codes = mmCifDict.get('_struct_ref.db_code', '')
    unp_db_accessions = mmCifDict.get('_struct_ref.pdbx_db_accession', '')

    for indx, entity_id in enumerate(entity_ids):
        if types[indx] == 'polymer':
            # UniProt
            uniprotObj = None
            if unp_db_names[indx] == 'UNP':
                db_accession = unp_db_accessions[indx]
                db_code = unp_db_codes[indx]
                uniprotObj = updateUniProtEntry(db_accession, db_code)

            # Organism
            organismObj = getOrganismObjmmCifFile(indx, mmCifDict)

            # Polymer Entity
            entityObj, quantity = updateEntitymmCifFile(
                indx, mmCifDict, uniprotObj, organismObj)

            # PDB-Polymer
            pdbEntityOgj = updatePdbToEntity(pdbObj, entityObj, quantity)
            objList.append(pdbEntityOgj)
    return objList


def geDataFromPubChem(url, jKey):

    jValue = ''
    try:
        resp = requests.get(url)
        if jKey in resp:
            jvalue = resp[jKey]
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return jValue


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

    # get data from PubChem
    cid = geDataFromPubChem(url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/' + ligandName + '/cids/JSON',jKey='CID')
    inChIKey = geDataFromPubChem(url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + cid + '/property/InChIKey/json', jKey='InChIKey')
    inChI = geDataFromPubChem(url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + cid + '/property/InChI/json', jKey='InChI')
    isomericSMILES = geDataFromPubChem(url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + cid + '/property/isomericSMILES/json', jKey='isomericSMILES')
    canonicalSMILES = geDataFromPubChem(url='https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/' + cid + '/property/CanonicalSMILES/json', jKey='CanonicalSMILES')

    obj = None
    try:
        obj, created = LigandEntity.objects.update_or_create(
            dbId=ligandId,
            defaults={
                'ligandType': ligandType if ligandType else '',
                'name': ligandName if ligandName else '',

                'formula_weight': formula_weights[indx] if formula_weights[indx] else '',
                'details': descriptions[indx] if descriptions[indx] else '',
                'imageLink': "" if lType == 'branched' else URL_LIGAND_IMAGE_EBI + ligandId + "_400.svg",
                'externalLink': "" if lType == 'branched' else URL_LIGAND_EBI + ligandId,
                'pubChemCompoundId': cid if cid else '',
                'IUPACInChIkey': inChIKey if inChIKey else '',
                'IUPACInChI': inChI if inChI else '',
                'isomericSMILES': isomericSMILES if isomericSMILES else '',
                'canonicalSMILES': canonicalSMILES if canonicalSMILES else '',
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
    return obj, quantity[indx]


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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
        resp = requests.head(url)
        print('Connecting', url)
        if resp.status_code == 200:
            print('-->>> response', resp.status_code)
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
        resp = requests.get(url)
        if resp.status_code == 200:
            print('-->>> response', resp.status_code)
            if resp.text.find('Does not exist') == -1:
                print('-->>> Found CERES refModel', pdbId, emdbId)
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
            else:
                print('-->>> No entry found', )
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
            ass_details=ass_details,
            macromolecules=macromolecules,
            uniProts=uniProts,
            genes=genes,
            bioFunction=bioFunction,
            bioProcess=bioProcess,
            cellComponent=cellComponent,
            domains=domains,
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


def getSampleDetails(mmCifDict):

    exprSystem = mmCifDict.get(
        '_entity_src_gen.pdbx_host_org_scientific_name', '')
    assembly = mmCifDict.get('_pdbx_struct_assembly.details', '')
    ass_method = mmCifDict.get('_pdbx_struct_assembly.method_details', '')
    ass_details = mmCifDict.get('_pdbx_struct_assembly.oligomeric_details', '')
    genes = mmCifDict.get('_entity_src_gen.pdbx_gene_src_gene', '')
    name = ''
    macromolecules = ''
    uniProts = ''
    bioFunction = ''
    bioProcess = ''
    cellComponent = ''
    domains = ''
    sampleObj = updateSampleEntity(
        name='',
        exprSystem=exprSystem[0].replace('?', '') if exprSystem else '',
        assembly=assembly[0].replace('?', '') if exprSystem else '',
        ass_method=ass_method[0].replace('?', '') if exprSystem else '',
        ass_details=ass_details[0].replace('?', '') if exprSystem else '',
        macromolecules='',
        uniProts='',
        genes=''.join([str(item.replace('?', '') for item in genes)]),
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
    except Exception as exc:
        logger.exception(exc)
        print(exc, os.strerror)
    return obj


def updatePublication(title, journal, issn, issue, volume, firstPage, lastPage, year, doi, pubMedId, abstract):
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
                'abstract': abstract
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
            logger.debug('Created new: %s', obj)
            print('Created new', obj)
        else:
            logger.debug('Updated: %s', obj)
            print('Updated', obj)
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
    abstractList = mmCifDict.get('_citation.abstract', '')
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
        abstract = abstractList[idx].replace('?', '') if abstractList else ''

        refObj = updatePublication(
            title, journal, issn, issue, volume, firstPage, lastPage, year, doi, pubMedId, abstract)
        objs.append(refObj)

        auths = getCitationAuthors(mmCifDict, refObj)
        # pubs = updateCitationToPdb(refObj, entryDetails)

    return objs
