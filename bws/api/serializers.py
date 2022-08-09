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

class WellEntitySerializer(serializers.ModelSerializer):
    
     class Meta:
        model = models.WellEntity
        fields =  ['dbId', 'imageThumbailLink', 'imagesIds', 'micromolarConcentration', 'cellLine', 'qualityControl', 'percentageInhibition', 'hitOver75Activity', 'numbeCells', 'phenotypeAnnotationLevel', 'channels']


class PlateEntitySerializer(serializers.ModelSerializer):
    wells = serializers.SerializerMethodField()

    class Meta:
       model = models.PlateEntity
       fields = ['dbId', 'wells']

    def get_wells(self, obj):

        # Get ligand ID from queryset context to pass it to WellEntitySerializer
        context = self.context
        ligand_id = self.context.get('ligand_id')

        # Given the ligand ID, check which of the wells inside obj (Plate obj) are associated to that ligand
        if ligand_id:
            wellid_list = []

            for w in obj.wells.all():
                if w.ligand_id == ligand_id:
                    wellid_list.append(w.dbId)

            # Given the unique list of Well IDs, get queryset including all WellEntity models and pass it to WellEntitySerializer
                #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Plate queryset)
            well_qs = models.WellEntity.objects.filter(dbId__in=wellid_list)
            return WellEntitySerializer(many=True,  context=context).to_representation(well_qs)

        #NOTE: is this line useful? (adapted from https://stackoverflow.com/questions/35878235/django-rest-framework-filter-related-data-based-on-parent-object)
        #return WellEntitySerializer(many=True).to_representation(obj.wells.all())


class ScreenEntitySerializer(serializers.ModelSerializer):
    plates = serializers.SerializerMethodField()
    class Meta:
       model = models.ScreenEntity
       fields = ['dbId', 'name', 'type', 'technologyType', 'imagingMethod1', 'imagingMethod2', 'plateCount', 'dataDoi', 'plates']

    def get_plates(self, obj):

        # Get ligand ID from queryset context to pass it to PlateEntitySerializer
        context = self.context
        ligand_id = self.context.get('ligand_id')

        # Given the ligand ID, check which of the plates inside obj (Screen obj) include well(s) associated to that ligand and get the unique list
        if ligand_id:

            plateid_list = []
            for p in obj.plates.all():
                for w in p.wells.all():
                    if w.ligand_id == ligand_id:
                        plateid_list.append(p.dbId)

            unique_plateid_list = list(set(plateid_list))

            # Given the unique list of Plate IDs, get queryset including all PlateEntity models and pass it to PlateEntitySerializer
                #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Screen queryset)
            plate_qs = models.PlateEntity.objects.filter(dbId__in=unique_plateid_list)
            return PlateEntitySerializer(many=True,  context=context).to_representation(plate_qs)

        #NOTE: is this line useful? (adapted from https://stackoverflow.com/questions/35878235/django-rest-framework-filter-related-data-based-on-parent-object)
        #return PlateEntitySerializer(many=True).to_representation(obj.files.all())

class StudyEntitySerializer(serializers.ModelSerializer):
    screens = serializers.SerializerMethodField()
    class Meta:
        model = models.StudyEntity
        fields = ['dbId', 'name', 'description', 'sampleType', 'dataDoi', 'screens']

    def get_screens(self, obj):

        # Get ligand ID from queryset context to pass it to ScreenEntitySerializer
        context = self.context
        ligand_id = self.context.get('ligand_id')

        # Given the ligand ID, check which of the screens inside obj (Assay obj) include well(s) associated to that ligand and get the unique list
        if ligand_id:

            screenid_list = []
            for s in obj.screens.all():
                for p in s.plates.all():
                    for w in p.wells.all():
                        if w.ligand_id == ligand_id:
                            screenid_list.append(s.dbId)
            
            unique_screenid_list = list(set(screenid_list))

            # Given the unique list of Screen IDs, get queryset including all ScreenEntity models and pass it to ScreenEntitySerializer
                #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Assay queryset)
            screen_qs = models.ScreenEntity.objects.filter(dbId__in=unique_screenid_list)
            return ScreenEntitySerializer(many=True,  context=context).to_representation(screen_qs)

        #NOTE: is this line useful? (adapted from https://stackoverflow.com/questions/35878235/django-rest-framework-filter-related-data-based-on-parent-object)
        #return ScreenEntitySerializer(many=True).to_representation(obj.files.all())

class LigandToImageDataSerializer(serializers.ModelSerializer):
    
    imageData = serializers.SerializerMethodField()
    class Meta:
        model = models.LigandEntity
        fields = ['dbId', 'name', 'details', 'imageLink', 'externalLink', 'IUPACInChIkey', 'pubChemCompoundId', 'imageData']
        depth = 6

    def get_imageData(self, obj):

        # Update the queryset context with the ligand ID to pass it to the rest of serializers involved (StudyEntitySerializer, ScreenEntitySerializer, PlateEntitySerializer and WellEntitySerializer)
        context = self.context
        context.update({'ligand_id': obj.dbId})

        # Given all wells associated to a specific ligand, get the unique list of all Assay IDs associated to it (assays in which the ligand has been proved)
        studyid_list = []
        for well in obj.well.all():
            studyid_list.append(well.plate.screen.assay.dbId)
        unique_studyid_list = list(set(studyid_list))

        # Given the unique list of Assay IDs, get queryset including all AssayEntity models and pass it to AssayEntitySerializer
            #TODO: Optimize to avoid querying the database. Instead, try to get the same info from the obj (Ligand queryset)
        study_qs = models.StudyEntity.objects.filter(dbId__in=unique_studyid_list)
        return StudyEntitySerializer(many=True, context=context).to_representation(study_qs)
        
    # To avoid showing imageData field in final JSON file when there is no info associated to it (avoid "imgaData []")
    def to_representation(self, value):
        repr_dict = super(serializers.ModelSerializer, self).to_representation(value)
        return OrderedDict((k, v) for k, v in repr_dict.items() 
                           if v not in [None, [], '', {}])