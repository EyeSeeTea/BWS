from rest_framework import serializers
from . import models


class TypeNestedSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AnnType
        fields = ['id', 'title', 'description']

class CategorySerializer(serializers.HyperlinkedModelSerializer):
    types = TypeNestedSerializer(many=True)

    class Meta:
        model = models.AnnCategory
        fields = ['id', 'title', 'description', 'created' ,'types']

class CategoryNestedSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.AnnCategory
        fields = ['id', 'title']


class TypeSerializer(serializers.ModelSerializer):
    category = CategoryNestedSerializer()

    class Meta:
        model = models.AnnType
        fields = ['id', 'title', 'description', 'created', 'category']


class DataFileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DataFile
        fields = ['filename', 'unique_id']

class EntrySerializer(serializers.ModelSerializer):
    files = DataFileNestedSerializer(many=True, read_only=True)

    class Meta:
        model = models.Entry
        fields = ['entryId', 'path', 'files', 'entryType']

class DataSetNestedSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    class Meta:
        model = models.DataSet
        fields = ['features',]

class DataFileSerializer(serializers.ModelSerializer):
    data = DataFileNestedSerializer(many=True, read_only=True)
    class Meta:
        model = models.DataFile
        fields = ['unique_id', 'path', 'filename', 'entry', 'data', 'fileType']


class DataSetSerializer(serializers.ModelSerializer):
    features = serializers.ListField(child=serializers.CharField())
    class Meta:
        model = models.DataSet
        fields = ['file', 'features']


class UniprotEntrySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.UniprotEntry
        fields = '__all__'


class TrackTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TrackType
        fields = '__all__'


class FeatureDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.TrackData
        fields = '__all__'


class XrefSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.featureId

    class Meta:
        model = models.Xref
        fields = ['id', 'name', 'url']


class FeatureDataDetailSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField('get_type')
    xrefs = XrefSerializer(many=True)

    def get_type(self, obj):
        return obj.f_track.track_type.name.upper()

    class Meta:
        model = models.TrackData
        fields = [
            'type',
            'mutationType',
            'sourceType',
            'mutationEffect',
            'begin', 'end',
            'wildType', 'alternativeSequence',
            'numberOfViruses',
            'reportedProtChange', 'genomicPosition', 'originalGenomic', 'newGenomic',
            'evidenceLevel',
            'xrefs']

class FeatureTrackSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.FeatureTrack
        fields = '__all__'


class TrackDetailSerializer(serializers.ModelSerializer):
    track_name = serializers.SerializerMethodField('get_track_name')
    accession = serializers.SerializerMethodField('get_acc')
    features = FeatureDataDetailSerializer(many=True)

    def get_track_name(self, obj):
        return obj.name

    def get_acc(self, obj):
        return obj.uniprot_entry.accession

    def get_features(self, obj):
        return obj.data

    class Meta:
        model = models.FeatureTrack
        fields = [
            'accession', 
            'sequence',
            'track_name', 'reference', 'fav_icon',
            'features'
        ]