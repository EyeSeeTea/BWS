from rest_framework import serializers
from collections import OrderedDict
from .models import *


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


# ========== ========== ========== ========== ========== ========== ==========

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['name', 'email', 'address', 'orcid', 'role']


class PublicationSerializer(serializers.ModelSerializer):
    authors = AuthorSerializer(read_only=True, many=True)

    class Meta:
        model = Publication
        fields = ['title', 'journal_abbrev', 'issn', 'issue', 'volume', 'page_first',
                  'page_last', 'year', 'doi', 'pubMedId', 'PMCId', 'abstract', 'authors']


class OrganismSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organism
        fields = ['ncbi_taxonomy_id', 'scientific_name',
                  'common_name', 'externalLink']


class WellEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = WellEntity
        fields = ['dbId', 'name', 'externalLink', 'imagesIds', 'imageThumbailLink', 'cellLine', 'cellLineTermAccession', 'controlType', 'qualityControl',
                  'micromolarConcentration', 'percentageInhibition', 'hitOver75Activity', 'numberCells', 'phenotypeAnnotationLevel', 'channels']


class PlateEntitySerializer(serializers.ModelSerializer):
    wells = serializers.SerializerMethodField()

    class Meta:
        model = PlateEntity
        fields = ['dbId', 'name', 'wells']

    def get_wells(self, obj):

        # Get ligand ID from queryset context to pass it to WellEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')

        # Given the ligand ID, check which of the wells inside obj (Plate obj) are associated to that ligand
        if ligand_entity:
            wellid_list = []

            for w in obj.wells.all():
                if w.ligand == ligand_entity:
                    wellid_list.append(w.dbId)

            # Given the unique list of Well IDs, get queryset including all WellEntity models and pass it to WellEntitySerializer
            well_qs = WellEntity.objects.filter(dbId__in=wellid_list)
            return WellEntitySerializer(many=True,  context=context).to_representation(well_qs)


class ScreenEntitySerializer(serializers.ModelSerializer):
    plates = serializers.SerializerMethodField()

    class Meta:
        model = ScreenEntity
        fields = ['dbId', 'name', 'type', 'typeTermAccession', 'technologyType', 'technologyTypeTermAccession',
                  'imagingMethod', 'imagingMethodTermAccession', 'sampleType', 'dataDoi', 'plateCount', 'plates']

    def get_plates(self, obj):

        # Get ligand ID from queryset context to pass it to PlateEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')

        # Given the ligand ID, check which of the plates inside obj (Screen obj) include well(s) associated to that ligand and get the unique list
        if ligand_entity:

            plateid_list = []
            for p in obj.plates.all():
                for w in p.wells.all():
                    if w.ligand == ligand_entity:
                        plateid_list.append(p.dbId)

            unique_plateid_list = list(set(plateid_list))

            # Given the unique list of Plate IDs, get queryset including all PlateEntity models and pass it to PlateEntitySerializer
            plate_qs = PlateEntity.objects.filter(dbId__in=unique_plateid_list)
            return PlateEntitySerializer(many=True,  context=context).to_representation(plate_qs)

class AssayEntitySerializer(serializers.ModelSerializer):
    screens = serializers.SerializerMethodField()
    organisms = OrganismSerializer(read_only=True, many=True)
    publications = PublicationSerializer(read_only=True, many=True)

    class Meta:
        model = AssayEntity
        fields = ['dbId', 'name', 'description', 'assayType', 'assayTypeTermAccession', 'organisms',
                  'externalLink', 'releaseDate', 'publications', 'dataDoi', 'BIAId', 'screenCount', 'screens']

    def get_screens(self, obj):

        # Get ligand ID from queryset context to pass it to ScreenEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')

        # Given the ligand ID, check which of the screens inside obj (Assay obj) include well(s) associated to that ligand and get the unique list
        if ligand_entity:

            screenid_list = []
            for s in obj.screens.all():
                for p in s.plates.all():
                    for w in p.wells.all():
                        if w.ligand == ligand_entity:
                            screenid_list.append(s.dbId)

            unique_screenid_list = list(set(screenid_list))

            # Given the unique list of Screen IDs, get queryset including all ScreenEntity models and pass it to ScreenEntitySerializer

            screen_qs = ScreenEntity.objects.filter(dbId__in=unique_screenid_list)

            # TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Assay queryset)
            screen_qs = ScreenEntity.objects.filter(
                dbId__in=unique_screenid_list)
            return ScreenEntitySerializer(many=True,  context=context).to_representation(screen_qs)

 

class FeatureTypeSerializer(serializers.ModelSerializer):
    assays = serializers.SerializerMethodField()

    class Meta:
        model = FeatureType
        fields = ['dataSource', 'name',
                  'description', 'externalLink', 'assays']

    def get_assays(self, obj):
        # Get ligand ID from queryset context to pass it to AssayEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')

        # Given the ligand ID, check which of the screens inside obj (Assay obj) include well(s) associated to that ligand and get the unique list
        if ligand_entity:

            assayid_list = []

            for st in obj.assayentity_features.all():
                for s in st.screens.all():
                    for p in s.plates.all():
                        for w in p.wells.all():
                            if w.ligand == ligand_entity:
                                assayid_list.append(st.dbId)

            unique_assayid_list = list(set(assayid_list))

            # Given the unique list of Assay IDs, get queryset including all AssayEntity models and pass it to AssayEntitySerializer
            assay_qs = AssayEntity.objects.filter(dbId__in=unique_assayid_list)
            return AssayEntitySerializer(many=True,  context=context).to_representation(assay_qs)


class LigandToImageDataSerializer(serializers.ModelSerializer):

    imageData = serializers.SerializerMethodField()

    class Meta:
        model = LigandEntity
        fields = ['dbId', 'name', 'ligandType', 'formula', 'formula_weight', 'details', 'altNames',
                  'IUPACInChIkey', 'pubChemCompoundId', 'imageLink', 'externalLink', 'imageData']
        depth = 6

    def get_imageData(self, obj):

        # Update the queryset context with the ligand ID to pass it to the rest of serializers involved (FeatureTypeSerializer, AssayEntitySerializer, ScreenEntitySerializer, PlateEntitySerializer and WellEntitySerializer)
        context = self.context
        context.update({'ligand_entity': obj})

        # Given all wells associated to a specific ligand, get the unique list of all FeatureType IDs associated to it (type os assays (e.g. High-ContentScreening Assay) in which the ligand has been proved)
        featureTypeId_list = []
        for well in obj.well.all():
            featureTypeId_list.append(well.plate.screen.assay.featureType_id)
        unique_featureTypeId_list = list(set(featureTypeId_list))

        # Given the unique list of FeatureType IDs, get queryset including all FeatureType models and pass it to FeatureTypeSerializer
        featureType_qs = FeatureType.objects.filter(pk__in=unique_featureTypeId_list)
        # TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Ligand queryset)
        featureType_qs = FeatureType.objects.filter(
            pk__in=unique_featureTypeId_list)
        return FeatureTypeSerializer(many=True, context=context).to_representation(featureType_qs)

    # To avoid showing imageData field in final JSON file when there is no info associated to it (avoid "imgaData []")
    def to_representation(self, value):
        repr_dict = super(serializers.ModelSerializer,
                          self).to_representation(value)
        return OrderedDict((k, v) for k, v in repr_dict.items()
                           if v not in [None, [], '', {}])


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


class RefinedModelSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefinedModelSource
        fields = ['name', 'description', 'externalLink']


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


class SampleEntitySerializer(serializers.ModelSerializer):

    class Meta:
        model = SampleEntity
        fields = '__all__'
