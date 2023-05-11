from django.contrib import admin
from api import models

# Register your models here.

admin.site.register(models.FeatureType)
#admin.site.register(models.StudyToOrganism)
admin.site.register(models.AssayEntity)
admin.site.register(models.ScreenEntity)
admin.site.register(models.PlateEntity)
admin.site.register(models.WellEntity)
#admin.site.register(models.PublicationAuthor)
admin.site.register(models.Publication)
admin.site.register(models.Author)
admin.site.register(models.LigandEntity)
admin.site.register(models.PdbToLigand)
admin.site.register(models.Organism)
admin.site.register(models.PdbEntry)
admin.site.register(models.Analyses)
admin.site.register(models.Ontology)
admin.site.register(models.OntologyTerm)
# admin.site.register(models.PTMEntity)
# admin.site.register(models.DomainEntity)
admin.site.register(models.UniProtEntry)
admin.site.register(models.PdbToEntity)
admin.site.register(models.ModelEntity)
admin.site.register(models.FeatureRegionEntity)
admin.site.register(models.FeatureModelEntity)
