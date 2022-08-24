import json
import logging
import os
import re
from subprocess import check_output
from api import models
from api.models import ENTRY_TYPES, FILE_TYPES
from django.core.exceptions import ValidationError
from api.dataPaths import (EMDB_BASEDIR, EMDB_DATA_DIR,
                           LOCAL_DATA_DIR, MODEL_AND_LIGAND_DIR,
                           MODIFIED_PDBS_ANN_DIR, THORN_DATA_DIR, IDR_DIR)
from api.study_parser import StudyParser


logger = logging.getLogger(__name__)

PDB_FOLDER_PATTERN = re.compile(".*/(\d\w{3})/.*\.pdb$")

REGEX_EMDB_ID = re.compile('^emd-\d{4,5}$')
REGEX_VOL_FILE = re.compile('^(emd)-\d{4,5}\.map$')
REGEX_PDB_FILE = re.compile('^(pdb)\d\w{3}\.ent$')
REGEX_LR_FILE = re.compile('^\d\w{3}\.(deepres|monores)\.pdb$')
REGEX_MAP2MODELQUALITY_FILE = re.compile('^\d\w{3}\.(mapq|fscq)\.pdb$')
REGEX_IDR_ID = re.compile('(idr\d{4})-.*-.*')


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


def findIDR(dirToLook=IDR_DIR):
    return findGeneric("*isolde/*pdb", dirToLook=dirToLook)

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

class ImageDataFromIDRAssayUtils(object):

    
    def _updateAssayDirsFromIDR(self, dirToLook=IDR_DIR):
        #TODO: crear aqui unas lineas para que se saque un registo.txt con la fecha y el nombre de los directorios de assays 
        # (idrNNNN-lastname-example) que se vayan importando para saber cuales son los dirs que quedan por hacer updateLigandEntryFromIDRAssay()
        pass

    def _updateLigandEntryFromIDRAssay(self, assayName, dirToLook=IDR_DIR):
        print("updateLigandEntryFromIDRAssay")

        '''
         Create FeatureType entry
        '''
        name = 'High-Content Screening Assay'
        description = 'High throughput sample analysis of collections of compounds that provide '\
            'a variety of chemically diverse structures that can be used to identify structure types '\
            'that have affinity with pharmacological targets. (Source Accession: EFO_0007553)'
        dataSource = 'The Image Data Resource (IDR)'
        externalLink = 'https://idr.openmicroscopy.org/'

        try:
            # update or create FeatureType entry 
            FeatureTypeEntry, created = models.FeatureType.objects.update_or_create(
                name=name,
                description=description,
                dataSource=dataSource,
                externalLink=externalLink)
            if created:
                logger.debug('Created new entry: %s', FeatureTypeEntry)
                print('Created new entry: ', FeatureTypeEntry)
        except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
            logger.debug(exc)


        '''
         Create Organism, Author, Publication, AssayEntity and ScreenEntity entries
        '''

        # Get ID and metadata file for IDR assay
        matchObj = re.match(REGEX_IDR_ID, assayName)
        if matchObj:
            assayId = matchObj.group(1)
        metadataFileExtention = '-study.txt'
        metadataFile = assayId + metadataFileExtention

        # Parse metadata file using StudyParser
        studypath=os.path.join(dirToLook, assayName, metadataFile)
        studyParserObj = StudyParser(studypath)

        # Create Organism entries
        #TODO: Crear una try/except para los casos en que no exista studyParserObj.study['Study Organism'] OR ['Study Organism Term Source REF'] OR ['Study Organism Term Accession'] y por tanto no se puedan dar estas lineas?? Ten en cuenta que en study_parser.ỳ aparecen como opcionales las 3
        REGEX_TAXON_REF = re.compile('(ncbitaxon).*')
        organisms = [organism for organism in studyParserObj.study['Study Organism'].split("\t")]
        organismTermSources = [termSource for termSource in studyParserObj.study['Study Organism Term Source REF'].split("\t")]
        organismTermAccessions = [termAccession for termAccession in studyParserObj.study['Study Organism Term Accession'].split("\t")]
        organism_entry_list = []

        for organism in zip(organisms, organismTermSources, organismTermAccessions):
            scientific_name = organism[0]
            TaxonTermSource = organism[1]
            ncbi_taxonomy_id = organism[2]
            
            # Check that the Study Organism Term Source REF is NCBI Taxonomy
            TaxonRefMatchObj = re.match(REGEX_TAXON_REF, TaxonTermSource.lower())
            if TaxonRefMatchObj:                
                try:
                    # update or create Organism entries
                    OrganismEntry, created = models.Organism.objects.update_or_create(
                        ncbi_taxonomy_id=ncbi_taxonomy_id,
                        scientific_name=scientific_name,
                        externalLink='https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=%s&lvl=0' % (ncbi_taxonomy_id))
                    organism_entry_list.append(OrganismEntry)
                    if created:
                        logger.debug('Created new entry: %s', OrganismEntry)
                        print('Created new entry: ', OrganismEntry)
                except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
                    logger.debug(exc)
            else:
                print('Study Organism Term Source REF for "%s" different from NCBI Taxonomy: '\
                    '\n\tStudy Organism Term Source REF: %s \n\tStudy Organism Term Accession: %s' \
                    % (scientific_name, TaxonTermSource, ncbi_taxonomy_id))


        # Create Author and Publication entries
        publication_list = studyParserObj.study['Publications'] #TODO: quitar esta linea y poner el bucle for directamente? (for publication in studyParserObj.study['Publications']:)
        publication_entry_list = []

        for publication in publication_list:
            title = publication['Title']
            doi = publication['DOI']
            pubMedId = publication['PubMed ID']
            PMCId = publication['PMC ID']
            author_list = [author for author in publication['Author List'].split(", ")]
            author_entry_list = []

            for author in author_list: #TODO: incluir last name y first name en Author entries?? #TODO: quitar esta linea y poner el bucle for directamente? (for author in publication['Author List'].split(", "):)
                try:
                    # update or create Author entries
                    AuthorEntry, created = models.Author.objects.update_or_create(
                        name=author)
                    author_entry_list.append(AuthorEntry)
                    if created:
                        logger.debug('Created new entry: %s', AuthorEntry)
                        print('Created new entry: ', AuthorEntry)
                except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
                    logger.debug(exc)

            try:
                
                # update or create Publication entries
                PublicationEntry, created = models.Publication.objects.update_or_create(
                    title=title,
                    doi=doi,
                    pubMedId=pubMedId,
                    PMCId=PMCId,
                    )
                publication_entry_list.append(PublicationEntry)
                # Add already updated/created Author entries to Publicacion entry
                [PublicationEntry.authors.add(author) for author in author_entry_list]

                if created:
                    logger.debug('Created new entry: %s', PublicationEntry)
                    print('Created new entry: ', PublicationEntry)
            except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
                logger.debug(exc)

        # Update Author entries with "Study Contacts" details if exist.
        #TODO: Crear una try/except para los casos en que no exista studyParserObj.study['Study Person Last Name'] OR ['Study Person First Name'] OR ... y por tanto no se puedan dar estas lineas?? Ten en cuenta que en study_parser.ỳ aparecen como opcionales
        authorLastNames = [authorLastName for authorLastName in studyParserObj.study['Study Person Last Name'].split("\t")]
        authorFirstNames = [authorFirstName for authorFirstName in studyParserObj.study['Study Person First Name'].split("\t")]
        authorEmails = [authorEmail for authorEmail in studyParserObj.study['Study Person Email'].split("\t")]
        authorAddresses = [authorAddress for authorAddress in studyParserObj.study['Study Person Address'].split("\t")]
        authorORCIDs = [authorORCID for authorORCID in studyParserObj.study['Study Person ORCID'].split("\t")]
        authorRoles = [authorRole for authorRole in studyParserObj.study['Study Person Roles'].split("\t")]

        for authorEntry in zip(authorLastNames, authorFirstNames, authorEmails, authorAddresses, authorORCIDs, authorRoles):
            nonExactName = ' '.join([authorEntry[0], authorEntry[1][0]]) # Try to mimic Author entry name from publication['Author List'] although middle names would be missing. E.g: Carpenter AE (Author entry name from publication['Author List']); Carpenter A (Author entry name from study['Study Person Last Name'] + study['Study Person First Name']) #TODO: hacer mas corta esta linea??
            email = authorEntry[2]
            address = authorEntry[3]
            orcid = authorEntry[4]
            role = authorEntry[5]

            try:
                # update or create Author entries
                AuthorEntry, created = models.Author.objects.update_or_create(
                    name__contains=nonExactName,
                    defaults={'email': email,'address': address, 'orcid': orcid, 'role': role}
                )
                if created:
                    logger.debug('Created new entry: %s', AuthorEntry)
                    print('Created new entry: ', AuthorEntry)
            except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
                logger.debug(exc)

        # Create Assay entry
        assayTitle = studyParserObj.study['Study Title']
        assayDescription = studyParserObj.study['Study Description']
        #assayExternalLinks = [assayExternalLink for assayExternalLink in studyParserObj.study['Study External URL'].split("\t")] #TODO: en los study.txt que no aparece la key ['Study External URL'] esto falla (como en idr0094-ellinger-sarscov2) SOLUCIONALO
        assayDetails = studyParserObj.study['Study Key Words']
        assayTypes = [assayType for assayType in studyParserObj.study['Study Type'].split("\t")] 
        assayTypeTermAccessions = [assayTypeTermAccession for assayTypeTermAccession in studyParserObj.study['Study Type Term Accession'].split("\t")] 
        screenCount = studyParserObj.study['Study Screens Number']
        BIAId = studyParserObj.study['Study BioImage Archive Accession']
        releaseDate = studyParserObj.study['Study Public Release Date']
        dataDoi = studyParserObj.study['Data DOI']

        try:
            # update or create Assay entry
            AssayEntityEntry, created = models.AssayEntity.objects.update_or_create(
                name=assayTitle,
                featureType=FeatureTypeEntry,
                description=assayDescription,
                #externalLink='; '.join(assayExternalLinks),
                details=assayDetails,
                dbId=assayId,
                assayType='; '.join(assayTypes),
                assayTypeTermAccession='; '.join(assayTypeTermAccessions),
                screenCount=screenCount,
                BIAId=BIAId,
                releaseDate=releaseDate,
                dataDoi=dataDoi,                
            )
            # Add already updated/created Author entries and Publicacion entries to AssayEntity entry
            [AssayEntityEntry.organisms.add(orgEnt) for orgEnt in organism_entry_list]
            [AssayEntityEntry.publications.add(pubEnt) for pubEnt in publication_entry_list]

            if created:
                logger.debug('Created new entry: %s', AssayEntityEntry)
                print('Created new entry: ', AssayEntityEntry)
        except Exception as exc: #TODO: mira a ver si hay otro tipo de excepcion mas concreta que Exception
            logger.debug(exc)

        
        # Create Screen entries
        print(studyParserObj.components)






    def _PRUEBAS_STUDY_TXT(self, study_txt, dirToLook=IDR_DIR): #TODO: eliminar esta funcion
        studyParserObj = StudyParser(study_txt)
        print(studyParserObj.study)
        
