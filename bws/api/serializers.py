from rest_framework import serializers
from api import models


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


 
class IDRWellEntitySerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.IDRWellEntity
       fields = '__all__'

class FeatureTypeSerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.FeatureType
       fields = ['dataSource']
 
class FeatureHCSModelEntitySerializer(serializers.ModelSerializer):
 
   well = IDRWellEntitySerializer(read_only=True)
   featureType = FeatureTypeSerializer(read_only=True)
 
   class Meta:
      model = models.FeatureHCSModelEntity
      fields = ['featureType', 'name', 'description', 'screen_id', 'plate_id', 'well']

