import uuid
from django.db import models
from django.core.validators import RegexValidator
import re


ENTRY_TYPES = ["emdb", "pdbRemodel", "computationalModel", "modelAndLigand"]
FILE_TYPES = ["PDB_ANN_FROM_MAP", "ISOLDE",
              "COMPUTATIONAL_MODEL", "PDB_LIGAND_POCKET"]

EMDB_URL = "https://www.ebi.ac.uk/emdb"
BIONOTES_URL = "https://3dbionotes.cnb.csic.es"
PUBCHE_URL="https://pubchem.ncbi.nlm.nih.gov"

SINGLE_PARTICLE = "Single Particle"
HELICAL = "Shelical"
EM_CRYSTAL = "Electron Crystallography"
TOMOGRAPHY = "tomography"
SUBTOMOAVRG = "subtomogram averaging"
EM_METHOD = [
    (SINGLE_PARTICLE, "Single Particle"),
    (HELICAL, "Shelical"),
    (EM_CRYSTAL, "Electron Crystallography"),
    (TOMOGRAPHY, "tomography"),
    (SUBTOMOAVRG, "subtomogram averaging"),
]

REL = "Released"
UNREL = "Unreleased"
HPUB = "Header released"
HOLD1 = "1 year hold"
HOLD2 = "2 year hold"
EMDB_STATUS = [
    (REL, "Released"),
    (UNREL, "Unreleased"),
    (HPUB, "Header released"),
    (HOLD1, "1 year hold"),
    (HOLD2, "2 year hold"),
]

PDB_REDO = "PDB-Redo"
ISOLDE = "Isolde"
REFMAC = "RefMac"
PHENIX_CERES = "Cerex"
REF_METHOD = [
    (PDB_REDO, "PDB-Redo"),
    (ISOLDE, "Isolde"),
    (REFMAC, "RefMac"),
    (PHENIX_CERES, "Cerex"),
]


class Entry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    entryId = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entryType = models.CharField(max_length=12, blank=True, default='')


class DataFile(models.Model):
    unique_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=50, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entry = models.ForeignKey(
        Entry, related_name='files', on_delete=models.CASCADE)
    fileType = models.CharField(max_length=12, blank=True, default='')
    method = models.CharField(max_length=12, blank=True, default='')

# ========== ========== ========== ========== ========== ========== ==========

class Ontology(models.Model):
    '''
    Ontology.
    '''
    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False,
                            null=False, default='')
    description = models.CharField(max_length=900, blank=False,
                            null=False, default='')
    externalLink = models.URLField(max_length=200, default='', blank=True)
    queryLink = models.URLField(max_length=200, default='', blank=True) # Link that OLS API uses to access ontology data
    
    def __str__(self):
        return '%s' % (self.name)
    
class OntologyTerm(models.Model):
    '''
    Ontology term.
    '''
    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False,
                            null=False, default='')
    description = models.CharField(max_length=900, blank=False,
                            null=False, default='')
    externalLink = models.URLField(max_length=200, default='', blank=True)
    source = models.ForeignKey(Ontology, related_name = 'terms', on_delete=models.CASCADE)
    
    def __str__(self):
        return '%s' % (self.name)
    
class EmdbEntry(models.Model):
    dbId = models.CharField(max_length=10, blank=False,
                            default='', primary_key=True, validators=[
                                RegexValidator(
                                    regex='^EMD-[0-9]{4,5}$',
                                    message='dbID doesnt comply',
                                ),
                            ])
    title = models.CharField(max_length=500, blank=False, default='')
    emMethod = models.CharField(
        max_length=25, choices=EM_METHOD, default=SINGLE_PARTICLE)
    resolution = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=50, blank=False, default=UNREL)
    details = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    pdbIds = models.ManyToManyField('PdbEntry', through='HybridModel')

    def imageLink(self):
        # https://www.ebi.ac.uk/emdb/images/entry/{emdbId}/400_{id}.gif
        return '%s/images/entry/%s/400_%s.gif' % (EMDB_URL, self.dbId, re.sub('EMD-', '', self.dbId))

    def externalLink(self):
        # https://www.ebi.ac.uk/emdb/{emdbId}
        return '%s/entry/%s' % (EMDB_URL, self.dbId,)

    def queryLink(self):
        return '%s/?queryId=%s' % (BIONOTES_URL, self.dbId, )

    def __str__(self):
        return '%s' % (self.dbId,)


class HybridModel(models.Model):
    emdbId = models.ForeignKey(EmdbEntry, related_name='hybridmodels',
                               null=True, on_delete=models.CASCADE)
    pdbId = models.ForeignKey('PdbEntry', related_name='hybridmodels',
                              null=True, on_delete=models.CASCADE)

    def __str__(self):
        return '%s(%s)' % (self.pdbId.dbId if self.pdbId else '', self.emdbId.dbId if self.emdbId else '')


class UniProtEntry(models.Model):
    dbId = models.CharField(max_length=20, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=200)
    externalLink = models.CharField(max_length=200)

    def __str__(self):
        return '%s(%s)' % (self.dbId, self.name)


class PdbEntry(models.Model):
    dbId = models.CharField(max_length=4, blank=False,
                            default='', primary_key=True, validators=[
                                RegexValidator(
                                    regex='^[0-9][a-zA-Z_0-9]{3}$',
                                    message='dbID doesnt comply',
                                ),
                            ])
    title = models.CharField(max_length=500, blank=False, default='')
    status = models.CharField(max_length=50, blank=False, default='')
    relDate = models.DateField(blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.CharField(max_length=5000, blank=True, null=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    entities = models.ManyToManyField('ModelEntity', through='PdbToEntity')
    ligands = models.ManyToManyField('LigandEntity', through='PdbToLigand')
    dbauthors = models.ManyToManyField('Author')

    def imageLink(self):
        return 'https://www.ebi.ac.uk/pdbe/static/entry/%s_deposited_chain_front_image-200x200.png' % (self.dbId.lower(), )

    def externalLink(self):
        return 'https://www.ebi.ac.uk/pdbe/entry/pdb/%s' % (self.dbId.lower(),)

    def queryLink(self):
        return 'https://3dbionotes.cnb.csic.es/?queryId=%s' % (self.dbId.lower(),)

    def __str__(self):
        return '%s' % (self.dbId,)


class PdbToEntity(models.Model):
    pdbId = models.ForeignKey(PdbEntry,
                              related_name='pdbentities', on_delete=models.CASCADE)
    entity = models.ForeignKey('ModelEntity',
                               related_name='pdbentities', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return '(%s) %s' % (self.pdbId.dbId, self.entity.name)


class Organism(models.Model):
    ncbi_taxonomy_id = models.CharField(max_length=10, blank=False,
                                        default='', primary_key=True)
    scientific_name = models.CharField(max_length=200, blank=False)
    common_name = models.CharField(max_length=200, blank=True)
    externalLink = models.URLField(max_length=200, blank=True)

    def __str__(self):
        return '(%s) %s' % (self.ncbi_taxonomy_id, self.scientific_name)


class ModelEntity(models.Model):
    uniprotAcc = models.ForeignKey(UniProtEntry,
                                   blank=True, null=True,
                                   related_name='modelEntities', on_delete=models.CASCADE)
    organism = models.ForeignKey(Organism,
                                 blank=True, null=True,
                                 related_name='modelEntities', on_delete=models.CASCADE)
    type = models.CharField(max_length=25)
    src_method = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    mutation = models.CharField(max_length=200)
    details = models.CharField(max_length=200)
    altNames = models.CharField(max_length=1024)

    @property
    def isAntibody(self):
        found = False
        kwords = ['antibody', 'antibodies', 'fab', 'heavy', 'light']
        for word in kwords:
            if word in self.name.lower() or word in self.details.lower() or word in self.altNames.lower():
                found = True
                break
        return found

    @property
    def isNanobody(self):
        found = False
        kwords = ['nanobody', 'nanobodies', 'nonobody']
        for word in kwords:
            if word in self.name.lower() or word in self.details.lower() or word in self.altNames.lower():
                found = True
                break
        return found

    @ property
    def isSybody(self):
        found = False
        kwords = ['synthetic nanobody', 'sybody', 'sybodies']
        for word in kwords:
            if word in self.name.lower() or word in self.details.lower() or word in self.altNames.lower():
                found = True
                break
        return found

    def __str__(self):
        return '%s-%s' % (self.name, self.type)


class PdbToLigand(models.Model):
    pdbId = models.ForeignKey(PdbEntry,
                              related_name='pdbligands', on_delete=models.CASCADE)
    ligand = models.ForeignKey('LigandEntity',
                               related_name='pdbligands', on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return '(%s) %s' % (self.pdbId.dbId, self.ligand.name)


class LigandEntity(models.Model):
    IUPACInChIkey = models.CharField(max_length=27, primary_key=True, default='')
    dbId = models.CharField(max_length=20, null=True, blank=True)
    pubChemCompoundId = models.CharField(max_length=250,  null=True, blank=True)
    ligandType = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    formula = models.CharField(max_length=255, null=True, blank=True)
    formula_weight = models.FloatField(null=True, blank=True)
    details = models.CharField(max_length=2000, null=True, blank=True)
    altNames = models.CharField(max_length=5000, null=True, blank=True)
    systematicNames = models.CharField(max_length=2000, null=True, blank=True)
    IUPACInChI = models.CharField(max_length=2000, null=True, blank=True)
    isomericSMILES = models.CharField(max_length=2000, null=True, blank=True)
    canonicalSMILES = models.CharField(max_length=2000, null=True, blank=True)

    def imageLink(self):
        # https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/RZJQGNCSTQAWON-UHFFFAOYSA-N/PNG
        return '%s/rest/pug/compound/inchikey/%s/PNG' % (PUBCHE_URL, self.IUPACInChIkey,)

    def externalLink(self):
        # https://pubchem.ncbi.nlm.nih.gov/compound/63253327
        return '%s/compound/%s' % (PUBCHE_URL, self.pubChemCompoundId,)

    def __str__(self):
        return '%s (LigandEntity)' % (self.IUPACInChIkey,)



class RefinedModelSource(models.Model):
    # name of the data source, e.g. 'PDB-REDO', 'CSTF (Coronavirus Structural TaskForce)', etc
    name = models.CharField(max_length=255, unique=True)
    # description of the data source
    description = models.CharField(max_length=5000, blank=True, null=True)
    # link to the data source
    externalLink = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return '%s' % (self.name,)


class RefinedModelMethod(models.Model):
    source = models.ForeignKey(
        RefinedModelSource, on_delete=models.CASCADE)  # Data source
    # name of the refinement method, e.g. 'PDB-REDO', 'Isolde', etc
    name = models.CharField(max_length=255, unique=True)
    # description of the refinement method
    description = models.CharField(max_length=5000, blank=True, null=True)
    # link to the refinement method
    externalLink = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return '%s' % (self.name,)


class RefinedModel(models.Model):
    emdbId = models.ForeignKey(EmdbEntry, related_name='refMaps',
                               null=True, on_delete=models.CASCADE)  # EMDB entry
    pdbId = models.ForeignKey(PdbEntry, related_name='refModels',
                              null=True, on_delete=models.CASCADE)  # PDB entry
    source = models.ForeignKey(
        RefinedModelSource, on_delete=models.CASCADE)  # Data source
    method = models.ForeignKey(
        RefinedModelMethod, on_delete=models.CASCADE)  # Refinement method
    # filename of the refined model
    filename = models.CharField(max_length=255)
    # link to the refined model
    externalLink = models.CharField(max_length=255, blank=True, null=True)
    # link to the query used to display the refined model in 3DBionotes
    queryLink = models.CharField(max_length=255, blank=True, null=True)
    # description of the refined model, notes, etc.
    details = models.CharField(max_length=5000, blank=True, null=True)

    def __str__(self):
        return '%s' % (self.filename,)


class SampleModel(models.Model):
    method = models.CharField(
        max_length=25, choices=REF_METHOD, default=PDB_REDO)

    emdbId = models.ForeignKey(EmdbEntry, related_name='samples',
                               null=True, on_delete=models.CASCADE)
    pdbId = models.ForeignKey(PdbEntry, related_name='samples',
                              null=True, on_delete=models.CASCADE)


class Author(models.Model):
    name = models.CharField(max_length=255, blank=False, default='')
    email = models.EmailField(max_length=255, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    orcid = models.CharField(max_length=25, blank=True, default='')
    role = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        if self.orcid:
            return '%s (%s)' % (self.name, self.orcid)
        else:
            return '%s' % (self.name)


class PdbEntryAuthor(models.Model):
    '''
        _audit_author
        Author submitting to DB
    '''
    pdbId = models.ForeignKey(PdbEntry,
                              related_name='pdbauthors', on_delete=models.CASCADE)
    author = models.ForeignKey(Author,
                               related_name='pdbmodels', on_delete=models.CASCADE)
    ordinal = models.IntegerField()

    def __str__(self):
        return '(%s) %s - %s' % (self.ordinal, self.author.orcid, self.author.name)


class Publication(models.Model):
    '''
        Publication
    '''
    title = models.CharField(max_length=500, blank=False, default='')
    journal_abbrev = models.CharField(max_length=255, blank=True, default='')
    issn = models.CharField(max_length=255, blank=True, default='')
    issue = models.CharField(max_length=255, blank=True, default='')
    volume = models.CharField(max_length=255, blank=True, default='')
    page_first = models.CharField(max_length=255, blank=True, default='')
    page_last = models.CharField(max_length=255, blank=True, default='')
    year = models.CharField(max_length=255, blank=True, default='')
    doi = models.CharField(max_length=255, blank=False, default='')
    pubMedId = models.CharField(max_length=255, blank=False, default='')
    PMCId = models.CharField(max_length=255, blank=False, default='')
    abstract = models.CharField(max_length=5000, blank=True, null=True)

    authors = models.ManyToManyField(Author)

    def __str__(self):
        return '(%s) %s - %s' % (self.year, self.issn, self.title)


class PublicationAuthor(models.Model):
    '''
        Author in a Publication
    '''
    author = models.ForeignKey(Author,
                               related_name='pubauthors', on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication,
                                    related_name='pubauthors', on_delete=models.CASCADE)
    ordinal = models.IntegerField()

    def __str__(self):
        return '(%s) %s - %s' % (self.ordinal, self.author.orcid, self.author.name)


class SampleEntity(models.Model):
    '''
        Sample details
    '''
    name = models.CharField(max_length=255, blank=False, default='')
    exprSystem = models.CharField(max_length=255, blank=False, default='')
    assembly = models.CharField(max_length=255, blank=False, default='')
    ass_method = models.CharField(max_length=255, blank=False, default='')
    ass_details = models.CharField(max_length=255, blank=False, default='')
    macromolecules = models.CharField(max_length=255, blank=False, default='')
    uniProts = models.CharField(max_length=255, blank=False, default='')
    genes = models.CharField(max_length=255, blank=False, default='')
    bioFunction = models.CharField(max_length=255, blank=False, default='')
    bioProcess = models.CharField(max_length=255, blank=False, default='')
    cellComponent = models.CharField(max_length=255, blank=False, default='')
    domains = models.CharField(max_length=255, blank=False, default='')


class PdbEntryDetails(models.Model):
    '''
        Details of PDB entry
    '''
    pdbentry = models.ForeignKey(PdbEntry,
                                 related_name='details', on_delete=models.CASCADE)
    sample = models.ForeignKey(SampleEntity,
                               related_name='details', on_delete=models.CASCADE)

    refdoc = models.ManyToManyField(Publication)


class FeatureType(models.Model):
    '''
        Feature type
    '''
    name = models.CharField(max_length=255, blank=False, default='')
    description = models.CharField(max_length=255, blank=False, default='')
    dataSource = models.CharField(max_length=255, blank=False, default='')
    externalLink = models.CharField(max_length=200)

    def __str__(self):
        return '%s - %s (FeatureType)' % (self.name, self.dataSource)


class FeatureEntity(models.Model):
    '''
        Feature details
    '''
    name = models.CharField(max_length=255, blank=False, default='')
    featureType = models.ForeignKey(FeatureType,
                                    related_name='%(class)s_features', null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=5000, blank=True, null=True)
    pdbentry = models.ForeignKey(PdbEntry,
                                 related_name='%(class)s_features', null=True, blank=True, on_delete=models.CASCADE)
    externalLink = models.URLField(max_length=200, default='', blank=True)

    class Meta:
        abstract = True


class FeatureModelEntity(FeatureEntity):
    '''
        Feature that is associated with the whole Model
    '''
    details = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        abstract = True


class FeatureRegionEntity(FeatureEntity):
    '''
        Feature that is associated with a region in a Model
    '''
    start = models.IntegerField()
    end = models.IntegerField()


class AssayEntity(FeatureModelEntity):

    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    types = models.ManyToManyField(OntologyTerm, related_name='type_term_assays')
    organisms = models.ManyToManyField(Organism)
    publications = models.ManyToManyField(Publication)
    screenCount = models.IntegerField(blank=True, null=True)
    BIAId = models.CharField(max_length=255, blank=True, default='')
    releaseDate = models.DateField(
        max_length=255, blank=True, null=True, default='')
    dataDoi = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s - %s (AssayEntity)' % (self.dbId, self.name)


class ScreenEntity(models.Model):

    assay = models.ForeignKey(AssayEntity,
                              related_name='screens', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False, default='')
    description = models.CharField(max_length=255, blank=True, default='')
    types = models.ManyToManyField(OntologyTerm, related_name='type_term_screens')
    technologyTypes = models.ManyToManyField(OntologyTerm, related_name='technology_term_screens')
    imagingMethods = models.ManyToManyField(OntologyTerm, related_name='imaging_term_screens')
    sampleType = models.CharField(max_length=255, blank=True, default='')
    plateCount = models.IntegerField(blank=True, null=True)
    dataDoi = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s (ScreenEntity)' % (self.dbId)


class PlateEntity(models.Model):

    screen = models.ForeignKey(ScreenEntity,
                               related_name='plates', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s (PlateEntity)' % (self.dbId)


class WellEntity(models.Model):
    '''
        Well details
    '''
    dbId = models.CharField(max_length=50, blank=False,
                            default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False, default='')
    description = models.CharField(max_length=5000, blank=True, default='')
    ligand = models.ForeignKey(LigandEntity,
                               related_name='well', null=True, blank=True, default='', on_delete=models.CASCADE)

    plate = models.ForeignKey(PlateEntity,
                              related_name='wells', default='', on_delete=models.CASCADE)

    externalLink = models.URLField(max_length=200, blank=True)
    imageThumbailLink = models.URLField(max_length=200, blank=True)
    imagesIds = models.CharField(max_length=255, blank=True, default='')
    cellLine = models.ForeignKey(OntologyTerm, default='',
                                 related_name='cell_term_wells', on_delete=models.CASCADE)
    controlType = models.CharField(max_length=255, blank=True, default='')
    qualityControl = models.CharField(max_length=255, blank=True, default='')
    micromolarConcentration = models.FloatField(
        null=True, blank=True)
    percentageInhibition = models.FloatField(null=True, blank=True)
    hitOver75Activity = models.CharField(
        max_length=255, blank=True, default='')
    numberCells = models.IntegerField(null=True, blank=True)
    phenotypeAnnotationLevel = models.CharField(
        max_length=255, blank=True, default='')
    channels = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '%s (WellEntity)' % (self.dbId)


class Topic(models.Model):
    '''
        Main Topics to organize the structures in the database
    '''
    name = models.CharField(max_length=255, blank=False, default='')
    description = models.CharField(max_length=255, blank=False, default='')

    def __str__(self):
        return '%s' % (self.name,)


class StructureTopic(models.Model):
    '''
        Structure to Topic relationship
    '''
    structure = models.ForeignKey(HybridModel,
                                  related_name='topics', on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic,
                              related_name='structures', on_delete=models.CASCADE)

    def __str__(self):
        return '%s: %s(%s)' % (self.topic.name, self.structure.pdbId if self.structure.pdbId else '', self.structure.emdbId if self.structure.emdbId else '')


class Analyses(models.Model):
    '''
    Additional Analyses on HCS Assay results to describe a ligand effects.
    '''
    name = models.CharField(max_length=255, blank=False,
                            null=False, default='')
    relation = models.CharField(max_length=10, blank=True, null=True, default='=')
    value = models.FloatField(null=False, blank=False, default=0)
    description = models.CharField(
        max_length=255, blank=True, null=True, default='')
    units = models.ForeignKey(OntologyTerm, default='',
                              related_name='unit_term_analyses', on_delete=models.CASCADE)
    pvalue = models.FloatField(null=True, blank=True)
    dataComment = models.CharField(
        max_length=255, blank=True, null=True, default='')

    ligand = models.ForeignKey(LigandEntity,
                               related_name='%(class)s_analyses', on_delete=models.CASCADE)
    assay = models.ForeignKey(AssayEntity,
                              related_name='%(class)s_analyses', on_delete=models.CASCADE)

    def __str__(self):
        return '%s (%s)' % (self.name, self.ligand)
