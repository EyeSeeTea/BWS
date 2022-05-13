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
        fields = ['source', 'method',
                  'filename',
                  'externalLink',
                  'details']


class StructureMinimalSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField('get_title')
    emdb = serializers.StringRelatedField(source='emdbId')
    pdb = serializers.StringRelatedField(source='pdbId')

    class Meta:
        model = HybridModel
        fields = [
            'title',
            'emdb',
            'pdb',
        ]

    def get_title(self, obj):
        return obj.emdbId.title if obj.emdbId else obj.pdbId.title if obj.pdbId else ''


class StructureToTopicSerializer(serializers.ModelSerializer):
    Structure = StructureMinimalSerializer(source='structure')

    class Meta:
        model = StructureTopic
        fields = ['Structure']


class TopicSerializer(serializers.ModelSerializer):
    structures = StructureToTopicSerializer(many=True)

    class Meta:
        model = Topic
        fields = ['name', 'description', 'structures']


class StructureTopicSerializer(serializers.ModelSerializer):
    topic = serializers.StringRelatedField()
    Structure = StructureMinimalSerializer(source='structure')

    class Meta:
        model = StructureTopic
        fields = ['topic', 'Structure']
