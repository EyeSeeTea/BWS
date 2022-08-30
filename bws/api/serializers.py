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


class RefinedModelSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefinedModelSource
        fields = ['name', 'description', 'externalLink']

            # Given the unique list of Screen IDs, get queryset including all ScreenEntity models and pass it to ScreenEntitySerializer
                #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Assay queryset)
            screen_qs = models.ScreenEntity.objects.filter(dbId__in=unique_screenid_list)
            return ScreenEntitySerializer(many=True,  context=context).to_representation(screen_qs)

        #NOTE: is this line useful? (adapted from https://stackoverflow.com/questions/35878235/django-rest-framework-filter-related-data-based-on-parent-object)
        #return ScreenEntitySerializer(many=True).to_representation(obj.files.all())

class FeatureTypeSerializer(serializers.ModelSerializer):
    assays = serializers.SerializerMethodField()
    class Meta:
        model = models.FeatureType
        fields = ['dataSource', 'name', 'description', 'externalLink', 'assays']

    def get_assays(self, obj):
        # Get ligand ID from queryset context to pass it to AssayEntitySerializer
        context = self.context
        ligand_id = self.context.get('ligand_id')

        # Given the ligand ID, check which of the screens inside obj (Assay obj) include well(s) associated to that ligand and get the unique list
        if ligand_id:

            assayid_list = []
            for st in obj.assayentity_features.all():
                for s in st.screens.all():
                    for p in s.plates.all():
                        for w in p.wells.all():
                            if w.ligand_id == ligand_id:
                                assayid_list.append(st.dbId)
            
            unique_assayid_list = list(set(assayid_list))

            # Given the unique list of Assay IDs, get queryset including all AssayEntity models and pass it to AssayEntitySerializer
                #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (FeatureType queryset)
            assay_qs = models.AssayEntity.objects.filter(dbId__in=unique_assayid_list)
            return AssayEntitySerializer(many=True,  context=context).to_representation(assay_qs)

class LigandToImageDataSerializer(serializers.ModelSerializer):
    
    imageData = serializers.SerializerMethodField()
    class Meta:
        model = RefinedModel
        fields = ['source', 'method',
                  'filename',
                  'externalLink', 'queryLink',
                  'details']
