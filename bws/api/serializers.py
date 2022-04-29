from rest_framework import serializers
from .models import *   # import all models


class DataFileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataFile
        fields = ['filename', 'unique_id']


class EntrySerializer(serializers.ModelSerializer):
    files = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Entry
        fields = ['entryId', 'path', 'files', 'entryType']


class DataFileSerializer(serializers.ModelSerializer):
    data = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = DataFile
        fields = ['unique_id', 'path', 'filename', 'entry', 'data', 'fileType']


class RefinedModelSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefinedModelSource
        fields = ['name', 'description', 'externalLink']


class RefinedModelMethodSerializer(serializers.ModelSerializer):
    source = serializers.StringRelatedField()

    class Meta:
        model = RefinedModelMethod
        fields = ['source', 'name', 'description', 'externalLink']


class RefinedModelSerializer(serializers.ModelSerializer):
    source = serializers.StringRelatedField()
    method = serializers.StringRelatedField()

    class Meta:
        model = RefinedModel
        fields = ['filename', 'details',  'source',
                  'method', 'externalLink', 'queryLink']
