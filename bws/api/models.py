import uuid
from django.db import models

ENTRY_TYPES = ["emdb", "pdbRemodel", "computationalModel", "modelAndLigand"]
FILE_TYPES = ["PDB_ANN_FROM_MAP", "ISOLDE",
              "COMPUTATIONAL_MODEL", "PDB_LIGAND_POCKET"]


class Entry(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    entryId = models.CharField(max_length=10, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entryType = models.CharField(max_length=12, blank=True, default='')


class DataFile(models.Model):
    unique_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=50, blank=True, default='')
    path = models.CharField(max_length=255, blank=True, default='')
    entry = models.ForeignKey(
        Entry, related_name='files', on_delete=models.CASCADE)
    fileType = models.CharField(max_length=12, blank=True, default='')
    method = models.CharField(max_length=12, blank=True, default='')
