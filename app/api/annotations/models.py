#! /usr/bin/env python3

# Database models for annotation

from django.db import models
from django.contrib import admin
from django.apps import apps

###########################################
# Database Models for annotation endpoints#
###########################################

# This section contains all "Entries" models
# They all store data in a similar way:
# A protein/gen ID, timestamps and the data as a json dump to a string

class biomutanentries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    resID = models.TextField(blank=True, default="")

    def __str__(self):
        return self.proteinID

class dbptmentries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

class dsysmapentries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID
        
class ebifeaturesentries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    features_type = models.CharField(max_length=255, blank=True, null=True, default="")

    def __str__(self):
        return self.geneID

class ElmdbData(models.Model):
    uniprotID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    features_type = models.CharField(max_length=255, blank=True, null=True, default="")

    def __str__(self):
        return self.uniprotID

class EnsemblAnnotationData(models.Model):
    geneName = models.CharField(max_length=30, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return f"{self.geneName}-{self.transcriptName}_{self.start}-{self.end}"

class EnsemblVariantEntry(models.Model):
    geneID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.geneID

class epitope(models.Model):
    epitope_id = models.DecimalField(max_digits=22, decimal_places=0)
    description = models.CharField(max_length=535, blank=True, null=True, default="")
    linear_peptide_seq = models.CharField(max_length=4000, blank=True, null=True, default="")
    linear_peptide_modified_seq = models.CharField(max_length=4000, blank=True, null=True, default="")
    linear_peptide_modification = models.CharField(max_length=85, blank=True, null=True, default="")
    non_aa_source_id = models.DecimalField(max_digits=22, decimal_places=0)
    disc_source_id = models.DecimalField(max_digits=22, decimal_places=0)
    disc_region = models.CharField(max_length=4000, blank=True, null=True, default="")
    disc_modification = models.CharField(max_length=85, blank=True, null=True, default="")
    mc_region = models.CharField(max_length=85, blank=True, null=True, default="")
    mc_mol1_source_id = models.DecimalField(max_digits=22, decimal_places=0)
    mc_mol1_modification = models.CharField(max_length=85, blank=True, null=True, default="")
    mc_mol2_source_id = models.DecimalField(max_digits=22, decimal_places=0)
    mc_mol2_modification = models.CharField(max_length=85, blank=True, null=True, default="")

    def __str__(self):
        return self.epitopte_id

class epitope_object(models.Model):
    epitope_id = models.DecimalField(max_digits=22, decimal_places=0)
    object_id = models.DecimalField(max_digits=22, decimal_places=0)
    source_antigen_accession = models.CharField(max_length=85, blank=True, null=True, default="")
    source_organism_org_id = models.DecimalField(max_digits=22, decimal_places=0)

    def __str__(self):
        return self.epitope_id

class intrproentries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

class object(models.Model):

    object_id = models.DecimalField(max_digits=22, decimal_places=0, primary_key=True)
    reference_id = models.DecimalField(max_digits=22, decimal_places=0)
    object_type = models.CharField(max_length=200)
    object_sub_type = models.CharField(max_length=200, blank=True, null=True)
    object_description = models.CharField(max_length=535, blank=True, null=True)
    derivative_type = models.CharField(max_length=500, blank=True, null=True)
    organism_id = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    organism2_id = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    region = models.CharField(max_length=1000, blank=True, null=True)
    starting_position = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    ending_position = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    cell_name = models.CharField(max_length=85, blank=True, null=True)
    cell_type = models.CharField(max_length=85, blank=True, null=True)
    tissue_type = models.CharField(max_length=85, blank=True, null=True)
    origin = models.CharField(max_length=85, blank=True, null=True)
    mol1_seq = models.CharField(max_length=4000, blank=True, null=True)
    mol1_modified_seq = models.CharField(max_length=4000, blank=True, null=True)
    mol1_modification = models.CharField(max_length=85, blank=True, null=True)
    mol1_source_id = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    mol2_modified_seq = models.CharField(max_length=4000, blank=True, null=True)
    mol2_modification = models.CharField(max_length=85, blank=True, null=True)
    mol2_source_id = models.DecimalField(max_digits=22, decimal_places=0, blank=True, null=True)
    mult_chain_mol_name = models.CharField(max_length=85, blank=True, null=True)

    def __str__(self):
        return self.object_id


class mobientries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

class molprobityentries(models.Model):
    PDBID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.PDBID

class PDBEntry(models.Model):
    PDBID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.PDBID

class PDBRedoEntry(models.Model):
    PDBID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.PDBID

class PdbDatum(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

class PFAMentity(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

class PhosphoEntries(models.Model):
    proteinID = models.CharField(max_length=255, blank=True, null=True, default="")
    data = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)
    updated_at = models.DateTimeField(auto_now=False, auto_now_add=False, default=None)

    def __str__(self):
        return self.proteinID

from django.db import models

class InterproDatum(models.Model):
    proteinId = models.CharField(max_length=255, null=True, blank=True)
    data = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=False)
    updated_at = models.DateTimeField(auto_now_add=False)

    class Meta:
        db_table = 'your_table_name'  # Replace with your actual table name

    def __str__(self):
        return f"{self.proteinId}"

# Model for SMART data
class SMARTentity(models.Model):
     uniprotid = models.CharField(max_length=30, blank=True, null=True, default="")
     domain = models.CharField(max_length=30, blank=True, null=True, default="")
     start = models.IntegerField(null=True, blank=True)
     end = models.IntegerField(null=True, blank=True)
     evalue = models.CharField(max_length=20, blank=True, null=True, default="1")
     type = models.CharField(max_length=30, blank=False, null=True, default="")

     def __str__(self):
         return self.uniprotid

class swissvarentries(models.Model):
     uniprotid = models.CharField(max_length=30, blank=True, null=True, default="")
     domain = models.CharField(max_length=30, blank=True, null=True, default="")
     start = models.IntegerField(null=True, blank=True)
     end = models.IntegerField(null=True, blank=True)
     evalue = models.CharField(max_length=20, blank=True, null=True, default="1")
     type = models.CharField(max_length=30, blank=False, null=True, default="")

     def __str__(self):
         return self.uniprotid

class uniprotmappingentries(models.Model):
     uniprotid = models.CharField(max_length=30, blank=True, null=True, default="")
     domain = models.CharField(max_length=30, blank=True, null=True, default="")
     gene = models.TextField(default=None, null=True)
     transcript = models.TextField(default=None, null=True)
     start = models.IntegerField(null=True, blank=True)
     end = models.IntegerField(null=True, blank=True)
     evalue = models.CharField(max_length=20, blank=True, null=True, default="1")
     type = models.CharField(max_length=30, blank=False, null=True, default="")

     def __str__(self):
         return self.uniprotid

admin.site.register(biomutanentries)
admin.site.register(dbptmentries)
admin.site.register(dsysmapentries)
admin.site.register(ebifeaturesentries)
admin.site.register(EnsemblAnnotationData)
admin.site.register(EnsemblVariantEntry)
admin.site.register(epitope)
admin.site.register(epitope_object)
admin.site.register(intrproentries)
admin.site.register(mobientries)
admin.site.register(molprobityentries)
admin.site.register(PDBEntry)
admin.site.register(PDBRedoEntry)
admin.site.register(PFAMentity)
admin.site.register(PhosphoEntries)
admin.site.register(SMARTentity)
admin.site.register(swissvarentries)
admin.site.register(uniprotmappingentries)

###########################
#     LRS MODELS          #
###########################

## Copied the models from LRS source code

import uuid

ENTRY_TYPES=["emdb", "pdbRemodel", "computationalModel", "modelAndLigand"]
FILE_TYPES=["PDB_ANN_FROM_MAP", "ISOLDE", "COMPUTATIONAL_MODEL", "PDB_LIGAND_POCKET"]

class AnnCategory(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()

    class Meta:
        ordering = ['created']

class AnnType(models.Model):
    category = models.ForeignKey(AnnCategory, related_name='types', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField()

class Entry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    entryId = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entryType = models.CharField(max_length=12, blank=True, default='')

class DataFile(models.Model):
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=50, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entry = models.ForeignKey(Entry, related_name='files', on_delete=models.CASCADE)
    fileType = models.CharField(max_length=12, blank=True, default='')
    method = models.CharField(max_length=12, blank=True, default='')


class Feature(models.Model):
    start = models.IntegerField()
    end = models.IntegerField()
    f_type = models.IntegerField()
    f_category = models.IntegerField()
    description = models.CharField(max_length=255, blank=True, default='')

class DataSet(models.Model):
    file = models.ForeignKey(Entry, related_name='data', on_delete=models.CASCADE)
    features = Feature()


#  ######################################################################
class UniprotEntry(models.Model):
    """
    UniprotEntry
    """
    accession = models.CharField(max_length=30, blank=False, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    description = models.CharField(max_length=255, blank=True, null=True, default='')


class TrackType(models.Model):
    trackTypeId = models.CharField(max_length=30, blank=False, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    description = models.CharField(max_length=255, blank=True, null=True, default='')


class FeatureTrack(models.Model):
    # acc
    uniprot_entry = models.ForeignKey(UniprotEntry, related_name='tracks', on_delete=models.CASCADE)
    # visualization_type
    track_type = models.ForeignKey(TrackType, related_name='tracks', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    reference = models.CharField(max_length=255, blank=True, null=True, default='')
    fav_icon = models.CharField(max_length=255, blank=True, null=True, default='')
    sequence = models.TextField(blank=True, null=True, default='')


class TrackData(models.Model):
    f_track = models.ForeignKey(FeatureTrack, related_name='features', on_delete=models.CASCADE)
    mutationType = models.CharField(max_length=255, blank=True, null=True, default='')
    sourceType = models.CharField(max_length=255, blank=True, null=True, default='')
    alternativeSequence = models.CharField(max_length=255, blank=True, null=True, default='')
    mutationEffect = models.CharField(max_length=255, blank=True, null=True, default='')
    begin = models.IntegerField()
    end = models.IntegerField()
    wildType = models.CharField(max_length=255, blank=True, null=True, default='')
    numberOfViruses = models.IntegerField()
    reportedProtChange = models.CharField(max_length=255, blank=True, null=True, default='')
    genomicPosition = models.IntegerField()
    originalGenomic = models.CharField(max_length=255, blank=True, null=True, default='')
    newGenomic = models.CharField(max_length=255, blank=True, null=True, default='')
    evidenceLevel = models.CharField(max_length=255, blank=True, null=True, default='')

class Xref(models.Model):
    feature = models.ForeignKey(TrackData, related_name='xrefs', on_delete=models.CASCADE)
    featureId = models.CharField(max_length=30, blank=True, null=True, default='')
    name = models.CharField(max_length=255, blank=True, null=True, default='')
    url = models.CharField(max_length=255, blank=True, null=True, default='')

admin.site.register(FeatureTrack)
