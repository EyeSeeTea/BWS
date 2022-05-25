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


# ========== ========== ========== ========== ========== ========== ==========

class PublicationSerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.Publication
       fields = ['title', 'doi', 'pubMedId']

class AuthorSerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.Author
       fields = ['name']

class PublicationAuthorSerializer(serializers.ModelSerializer):
 
   publication = PublicationSerializer(read_only=True)
   author = AuthorSerializer(read_only=True)
   class Meta:
       model = models.PublicationAuthor
       fields = ['publication', 'author']

class IDRWellEntitySerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.IDRWellEntity
       fields = '__all__'

class FeatureTypeSerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.FeatureType
       fields = ['dataSource']
 

class LigandEntitySerializer(serializers.ModelSerializer):
 
   class Meta:
       model = models.LigandEntity
       fields = ['dbId']

class PdbToLigandSerializer(serializers.ModelSerializer):
 
   ligand = LigandEntitySerializer(read_only=True)
   class Meta:
       model = models.LigandEntity
       fields = ['ligand']

class FeatureHCSModelEntitySerializer(serializers.ModelSerializer):
 
   well = IDRWellEntitySerializer(read_only=True)
   featureType = FeatureTypeSerializer(read_only=True)
   publication = PublicationAuthorSerializer(read_only=True)
   ligand = PdbToLigandSerializer(read_only=True)
 
   class Meta:
      model = models.FeatureHCSModelEntity
      fields = ['ligand', 'ligand_name', 'featureType', 'name', 'description', 'publication', 'screen_id', 'plate_id', 'well']

