"""
Command for updating IDR data
"""
from django.core.management.base import BaseCommand
from api.utils import ImageDataFromIDRAssayUtils



class Command(BaseCommand):
    """
    Command for updating IDR data
    """

    help = "Update IDR data from <assayPath>"
    missing_args_message = "Too few arguments. Please, provide the path to the experiment directory."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'assayPath', nargs=1, type=str,
            help='<Required> Assay dir path, i.e.: /data/IDR/idr0094-ellinger-sarscov2')

    def handle(self, *args, **options):
        assayPath = options['assayPath'][0]
        print("Reading data for ", assayPath)
        ImageDataFromIDRAssayUtils()._updateLigandEntryFromIDRAssay(assayPath=assayPath)

