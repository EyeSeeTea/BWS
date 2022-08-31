"""
Command for updating IDR data
"""
from django.core.management.base import BaseCommand
from api.utils import ImageDataFromIDRAssayUtils



class Command(BaseCommand):
    """
    Command for updating IDR data
    """

    help = "Update IDR data from <assayName>"
    missing_args_message = "Too few arguments. Please, provide an experiment name."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'assayName', nargs=1, type=str,
            help='<Required> Assay name, i.e.: idr0094-ellinger-sarscov2')

    def handle(self, *args, **options):
        assayName = options['assayName'][0]
        print("Reading data for ", assayName)
        ImageDataFromIDRAssayUtils()._updateLigandEntryFromIDRAssay(assayName=assayName)

