import uuid
from django.db import models
from django.core.validators import RegexValidator
import re


ENTRY_TYPES = ["emdb", "pdbRemodel", "computationalModel", "modelAndLigand"]
FILE_TYPES = ["PDB_ANN_FROM_MAP", "ISOLDE",
              "COMPUTATIONAL_MODEL", "PDB_LIGAND_POCKET"]

EMDB_URL = "https://www.ebi.ac.uk/emdb"
BIONOTES_URL = "https://3dbionotes.cnb.csic.es"

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


class EmdbEntry(models.Model):
    dbId = models.CharField(max_length=10, blank=False,
                            default='', primary_key=True, validators=[
                                RegexValidator(
                                    regex='^EMD-[0-9]{4,5}$',
                                    message='dbID doesnt comply',
                                ),
                            ])
    title = models.CharField(max_length=255, blank=False, default='')
    emMethod = models.CharField(
        max_length=25, choices=EM_METHOD, default=SINGLE_PARTICLE)
    resolution = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=5, blank=False, default=UNREL)
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
        emdb = self.emdbId.dbId if self.emdbId else ''
        pdb = self.pdbId.dbId if self.pdbId else ''
        return '%s - %s' % (emdb, pdb)


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
    title = models.CharField(max_length=255, blank=False, default='')
    status = models.CharField(max_length=25, blank=False, default='')
    relDate = models.DateField(blank=True, null=True)
    method = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)
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
    scientific_name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200)
    externalLink = models.CharField(max_length=200)

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
    altNames = models.CharField(max_length=200)

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
    dbId = models.CharField(max_length=20, blank=False,
                            default='', primary_key=True)

    ligandType = models.CharField(max_length=25)
    name = models.CharField(max_length=200)
    formula = models.CharField(max_length=200)
    formula_weight = models.FloatField()
    details = models.CharField(max_length=200)
    altNames = models.CharField(max_length=200)
    imageLink = models.CharField(max_length=200)
    externalLink = models.CharField(max_length=200)

    def __str__(self):
        return '%s' % (self.dbId,)


class RefinedModel(models.Model):
    URL_QUERYLINK = 'https://3dbionotes.cnb.csic.es/'

    method = models.CharField(
        max_length=25, choices=REF_METHOD, default=PDB_REDO)

    emdbId = models.ForeignKey(EmdbEntry, related_name='%(class)s_refMaps',
                               null=True, on_delete=models.CASCADE)
    pdbId = models.ForeignKey('PdbEntry', related_name='%(class)s_refModels',
                              null=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class RefinedPdbRedoModel(RefinedModel):
    # https://pdb-redo.eu/db/6lxt
    URL_EXTERNAL = 'https://pdb-redo.eu/db/'

    def externalLink(self):
        return "{0}{1}".format(self.URL_EXTERNAL, self.pdbId.dbId.lower())

    def queryLink(self):
        # https://3dbionotes.cnb.csic.es/pdb_redo/6lxt
        return "{0}{1}{2}".format(self.URL_QUERYLINK, 'pdb_redo/', self.pdbId.dbId.lower())


class RefinedIsoldeRedoModel(RefinedModel):
    # https://insidecorona.net/our-database/
    URL_EXTERNAL = 'https://insidecorona.net/our-database/'

    filename = models.CharField(max_length=255, blank=False, default='')

    def externalLink(self):
        return "{0}".format(self.URL_EXTERNAL,)

    def queryLink(self):
        # https://3dbionotes.cnb.csic.es/isolde/6w9c/6w9c_refine_15
        return "{0}{1}{2}{3}".format(self.URL_QUERYLINK, 'isolde/', self.pdbId.dbId.lower(), self.filename)


class SampleModel(models.Model):
    method = models.CharField(
        max_length=25, choices=REF_METHOD, default=PDB_REDO)

    emdbId = models.ForeignKey(EmdbEntry, related_name='samples',
                               null=True, on_delete=models.CASCADE)
    pdbId = models.ForeignKey(PdbEntry, related_name='samples',
                              null=True, on_delete=models.CASCADE)


class Author(models.Model):
    name = models.CharField(max_length=255, blank=False, default='')
    orcid = models.CharField(max_length=25, blank=False, default='')

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
    title = models.CharField(max_length=255, blank=False, default='')
    journal_abbrev = models.CharField(max_length=255, blank=False, default='')
    issn = models.CharField(max_length=255, blank=False, default='')
    issue = models.CharField(max_length=255, blank=False, default='')
    volume = models.CharField(max_length=255, blank=False, default='')
    page_first = models.CharField(max_length=255, blank=False, default='')
    page_last = models.CharField(max_length=255, blank=False, default='')
    year = models.CharField(max_length=255, blank=False, default='')
    doi = models.CharField(max_length=255, blank=False, default='')
    pubMedId = models.CharField(max_length=255, blank=False, default='')
    abstract = models.CharField(max_length=255, blank=False, default='')

    authors = models.ManyToManyField(Author, through='PublicationAuthor')

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


class FeatureEntity(models.Model):
    '''
        Feature details
    '''
    name = models.CharField(max_length=255, blank=False, default='')
    featureType = models.ForeignKey(FeatureType,
                                    related_name='%(class)s_features', null=True, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=False, default='')
    pdbentry = models.ForeignKey(PdbEntry,
                                 related_name='%(class)s_features', null=True, on_delete=models.CASCADE)
    externalLink = models.CharField(max_length=200, default='')
    class Meta:
            abstract = True



class FeatureModelEntity(FeatureEntity):
    '''
        Feature that is associated with the whole Model
    '''
    details = models.CharField(max_length=255, blank=False, default='')
    class Meta:
            abstract = True


class FeatureRegionEntity(FeatureEntity):
    '''
        Feature that is associated with a region in a Model
    '''
    start = models.IntegerField()
    end = models.IntegerField()


class StudyToOrganism(models.Model):
   study = models.ForeignKey('StudyEntity',
                             related_name='studyorganisms', on_delete=models.CASCADE)
   organism = models.ForeignKey(Organism,
                              related_name='studyorganisms', on_delete=models.CASCADE)
 
   def __str__(self):
       return '(%s) %s' % (self.study.dbId, self.organism.ncbi_taxonomy_id)


class StudyEntity(models.Model):

    organisms = models.ManyToManyField(Organism, through=StudyToOrganism)
    publicationAuthor = models.ForeignKey(PublicationAuthor,
                                 related_name='studies', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False, default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False, default='')
    description = models.CharField(max_length=255, blank=False, default='')
    sampleType = models.CharField(max_length=255, blank=False, default='')
    dataDoi = models.CharField(max_length=255, blank=False, default='')

class ScreenEntity(models.Model):

    assay = models.ForeignKey(StudyEntity,
                                 related_name='screens', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False, default='', primary_key=True)
    name = models.CharField(max_length=255, blank=False, default='')
    type = models.CharField(max_length=255, blank=False, default='')
    technologyType = models.CharField(max_length=255, blank=False, default='')
    imagingMethod1 = models.CharField(max_length=255, blank=False, default='')
    imagingMethod2 = models.CharField(max_length=255, null=True, blank=False, default='')
    plateCount = models.CharField(max_length=255, blank=False, default='')
    dataDoi = models.CharField(max_length=255, blank=False, default='')


class PlateEntity(models.Model):

    screen = models.ForeignKey(ScreenEntity,
                                 related_name='plates', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False, default='', primary_key=True)
    creationDate = models.CharField(max_length=255, blank=False, default='')


class WellEntity(FeatureModelEntity):
    '''
        Well details
    '''

    ligand = models.ForeignKey(PdbToLigand,
                                 related_name='wells', default='', on_delete=models.CASCADE)
    
    plate = models.ForeignKey(PlateEntity,
                                 related_name='wells', default='', on_delete=models.CASCADE)

    dbId = models.CharField(max_length=50, blank=False, default='', primary_key=True)
    imageThumbailLink = models.URLField(max_length=200)
    imagesIds = models.CharField(max_length=255, blank=False, default='')
    micromolarConcentration = models.CharField(max_length=255, null=True, blank=False, default='')
    cellLine = models.CharField(max_length=255, blank=False, default='')
    qualityControl = models.CharField(max_length=255, blank=False, default='')
    percentageInhibition = models.CharField(max_length=255, blank=False, default='')
    hitOver75Activity = models.CharField(max_length=255, blank=False, default='')
    numbeCells = models.CharField(max_length=255, blank=False, default='')
    phenotypeAnnotationLevel = models.CharField(max_length=255, blank=False, default='')
    channels = models.CharField(max_length=255, blank=False, default='')
