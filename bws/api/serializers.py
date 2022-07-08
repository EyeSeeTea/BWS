from rest_framework import serializers
from api import models
from collections import OrderedDict

class DataFileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DataFile
        fields = ['filename', 'unique_id']


class EntrySerializer(serializers.ModelSerializer):
    files = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = models.Entry
        fields = ['entryId', 'path', 'files', 'entryType']


class DataFileSerializer(serializers.ModelSerializer):
    data = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = models.DataFile
        fields = ['unique_id', 'path', 'filename', 'entry', 'data', 'fileType']


# ========== ========== ========== ========== ========== ========== ==========

# class PdbToLigandSerializer(serializers.ModelSerializer):
 
#    #ligand = LigandEntitySerializer(read_only=True)
#    #pdbId = PdbEntrySerializer(read_only=True)
#    #imageData = WellEntitySerializer(read_only=True)
#    class Meta:
#        model = models.PdbToLigand
#        fields = ['quantity']


# class PdbToLigandListingField(serializers.RelatedField):
#     def to_representation(self, value):
#         return 'Ligand %s: %s' % (value.pdbId, value.quantity)

class WellEntitySerializer(serializers.ModelSerializer):
    
     class Meta:
        model = models.WellEntity
        fields =  ['dbId', 'imageThumbailLink', 'imagesIds', 'micromolarConcentration', 'cellLine', 'qualityControl', 'percentageInhibition', 'hitOver75Activity', 'numbeCells', 'phenotypeAnnotationLevel', 'channels']

class PlateEntitySerializer(serializers.ModelSerializer):
    wells = WellEntitySerializer(read_only=True, many=True)
    #wells = WellEntitySerializer(source='filtered_wells', many=True, read_only=True)
    class Meta:
       model = models.PlateEntity
       fields = ['dbId', 'wells']

class ScreenEntitySerializer(serializers.ModelSerializer):
    plates = PlateEntitySerializer(read_only=True, many=True)
    #plates = PlateEntitySerializer(source='filtered_plates', many=True, read_only=True)
    class Meta:
       model = models.ScreenEntity
       fields = ['dbId', 'name', 'type', 'technologyType', 'imagingMethod1', 'imagingMethod2', 'plateCount', 'dataDoi', 'plates']

class StudyEntitySerializer(serializers.ModelSerializer):
   screens = ScreenEntitySerializer(read_only=True, many=True)
   #screens = ScreenEntitySerializer(source='filtered_screens', many=True, read_only=True)
   class Meta:
       model = models.StudyEntity
       fields = ['dbId', 'name', 'description', 'sampleType', 'dataDoi', 'screens']
