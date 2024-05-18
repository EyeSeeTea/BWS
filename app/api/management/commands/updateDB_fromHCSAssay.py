"""
Command for updating IDR data and the associated additional analyses
"""
from django.core.management.base import BaseCommand
from api.utils import IDRUtils



class Command(BaseCommand):
    """
    Command for updating HCS data from IDR and the associated additional analyses
    """

    help = "Update IDR data and the additional analyses from from <assayPath>"
    missing_args_message = "Too few arguments. Please, provide the path to the experiment directory."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'assayPath', nargs=1, type=str,
            help='<Required> Assay dir path, i.e.: /data/IDR/idr0094-ellinger-sarscov2')

    def handle(self, *args, **options):
        assayPath = options['assayPath'][0]
        print("Reading data for", assayPath)
        IDRUtils()._updateDB_fromHCSAssay(assayPath=assayPath)

