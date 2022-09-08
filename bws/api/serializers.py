from rest_framework import serializers
from collections import OrderedDict
from .models import *
from django.db.models import Q

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


class AnalysesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analyses
        fields = ['name', 'value', 'description', 'units', 'unitsTermAccession', 'pvalue', 'dataComment']

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
    controlWells = serializers.SerializerMethodField()

    class Meta:
        model = PlateEntity
        fields = ['dbId', 'name', 'wells', 'controlWells']

    def get_wells(self, obj):

        # Get ligand ID and list of IDs tuples from queryset context to pass it to WellEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')
        zip_list = self.context.get('zip_list')

        # Given the ligand ID, get the get list of WellEntities  associated to that ligand
        if ligand_entity:
            wellid_list = []
            for well in zip_list:
                if well[3] == obj.dbId: # tupl[3] = PlateEntity id 
                    wellid_list.append(well[4]) # tupl[4] = WellEntity id 

            # Given the list of Well IDs, get queryset including all WellEntity models and pass it to WellEntitySerializer
            well_qs = WellEntity.objects.filter(dbId__in=wellid_list)
            return WellEntitySerializer(many=True,  context=context).to_representation(well_qs)
    
    def get_controlWells(self, obj):

        # Given the plate id, get queryset including all control wells and pass it to WellEntitySerializer
        controls_qs = WellEntity.objects.filter(plate_id=obj.dbId).filter(
            Q(controlType='positive') | Q(controlType='negative')
            )
        return WellEntitySerializer(many=True).to_representation(controls_qs)
 

class ScreenEntitySerializer(serializers.ModelSerializer):
    plates = serializers.SerializerMethodField()

    class Meta:
        model = ScreenEntity
        fields = ['dbId', 'name', 'type', 'typeTermAccession', 'technologyType', 'technologyTypeTermAccession', 
        'imagingMethod', 'imagingMethodTermAccession', 'sampleType', 'dataDoi', 'plateCount', 'plates']

    def get_plates(self, obj):

        # Get ligand ID and list of IDs tuples from queryset context to pass it to PlateEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')
        zip_list = self.context.get('zip_list')

        # Given the ligand ID, get the list of PlateEntities that include well(s) associated to that ligand and get the unique list
        if ligand_entity:
            plateid_list = []
            for tupl in zip_list:
                if tupl[2] == obj.dbId: # tupl[2] = ScreenEntity id 
                    plateid_list.append(tupl[3]) # tupl[3] = PlateEntity id        

            unique_plateid_list = list(set(plateid_list))

            # Given the unique list of Plate IDs, get queryset including all PlateEntity models and pass it to PlateEntitySerializer
            plate_qs = PlateEntity.objects.filter(dbId__in=unique_plateid_list)
            return PlateEntitySerializer(many=True,  context=context).to_representation(plate_qs)

class AssayEntitySerializer(serializers.ModelSerializer):
    screens = serializers.SerializerMethodField()
    organisms = OrganismSerializer(read_only=True, many=True)
    publications = PublicationSerializer(read_only=True, many=True)
    additionalAnalyses = serializers.SerializerMethodField()
    

    class Meta:
        model = AssayEntity
        fields = ['dbId', 'name', 'description', 'assayType', 'assayTypeTermAccession', 'organisms', 
        'externalLink', 'releaseDate', 'publications', 'dataDoi', 'BIAId', 'screenCount', 'screens', 'additionalAnalyses']

    def get_screens(self, obj):

        # Get ligand ID and list of IDs tuples from queryset context to pass it to ScreenEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')
        zip_list = self.context.get('zip_list')

        # Given the ligand ID, get the list of ScreenEntities that include well(s) associated to that ligand and get the unique list
        if ligand_entity:
            screenid_list = []
            for tupl in zip_list:
                if tupl[1] == obj.dbId: # tupl[1] = AssayEntity id
                    screenid_list.append(tupl[2]) # tupl[2] = ScreenEntity id               

            unique_screenid_list = list(set(screenid_list))

            # Given the unique list of Screen IDs, get queryset including all ScreenEntity models and pass it to ScreenEntitySerializer
            screen_qs = ScreenEntity.objects.filter(dbId__in=unique_screenid_list)
            return ScreenEntitySerializer(many=True,  context=context).to_representation(screen_qs)

    def get_additionalAnalyses(self, obj):

        # Get ligand ID from queryset context
        context = self.context
        ligand_entity = self.context.get('ligand_entity')

        # Given the assay and the ligand id, get queryset including all control wells and pass it to WellEntitySerializer
        analyses_qs = Analyses.objects.filter(assay_id=obj.dbId).filter(ligand=ligand_entity)
        return AnalysesSerializer(many=True).to_representation(analyses_qs)
 

class FeatureTypeSerializer(serializers.ModelSerializer):
    assays = serializers.SerializerMethodField()

    class Meta:
        model = FeatureType
        fields = ['dataSource', 'name', 
        'description', 'externalLink', 'assays']

    def get_assays(self, obj):
        # Get ligand ID and list of IDs tuples from queryset context to pass it to AssayEntitySerializer
        context = self.context
        ligand_entity = self.context.get('ligand_entity')
        zip_list = self.context.get('zip_list')

        # Given the ligand ID, get the list of AssayEntities that include well(s) associated to that ligand and get the unique list
        if ligand_entity:
            assayid_list1 = []
            for tupl in zip_list:
                if tupl[0] == obj.id: # tupl[0] = FeatureType id
                    assayid_list1.append(tupl[1]) # tupl[1] = AssayEntity id

            unique_assayid_list = list(set(assayid_list1))

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

        # Given the wells associated to a specific ligand, get the tuple of all ids associated to each well (FeatureType, AssayEntity, ScreenEntity and PlateEntity ids)
        featureTypeId_list2, assayEntityId_list2, screenEntityId_list2, plateEntityId_list2, wellEntityId_list2  = [], [], [], [], []
        for well in obj.well.all():
            featureTypeId_list2.append(well.plate.screen.assay.featureType_id)
            assayEntityId_list2.append(well.plate.screen.assay_id)
            screenEntityId_list2.append(well.plate.screen_id)
            plateEntityId_list2.append(well.plate_id)
            wellEntityId_list2.append(well.dbId)

        zip_list = list(zip(
            featureTypeId_list2, 
            assayEntityId_list2, 
            screenEntityId_list2, 
            plateEntityId_list2, 
            wellEntityId_list2
            ))

        # Update the queryset context with the the list of tuples including ids associated to a ligand and pass it to the rest of serializers involved (FeatureTypeSerializer, AssayEntitySerializer, ScreenEntitySerializer, PlateEntitySerializer and WellEntitySerializer)
        context.update({
            'zip_list': zip_list
            })

        # Get the unique list of all FeatureType IDs associated to each LigandEntity
        featureTypeid_list = []
        for well in zip_list:
            featureTypeid_list.append(well[0])

        unique_featureTypeid_list = list(set(featureTypeid_list))

        # Given the unique list of FeatureType IDs, get queryset including all FeatureType models and pass it to FeatureTypeSerializer
        featureType_qs = FeatureType.objects.filter(pk__in=unique_featureTypeid_list)

        return FeatureTypeSerializer(many=True, context=context).to_representation(featureType_qs)

    # To avoid showing imageData field in final JSON file when there is no info associated to it (avoid "imgaData []")
    def to_representation(self, value):
        repr_dict = super(serializers.ModelSerializer, self).to_representation(value)
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
