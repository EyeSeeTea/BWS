"""
Command for updating Additional Analyses data on HCS from IDR 
"""
from django.core.management.base import BaseCommand
from api.utils import IDRUtils



class Command(BaseCommand):
    """
    Command for updating Additional analyses performed on HCS data from IDR
    """

    help = "Update IDR data with Additional Analyses data from <analysesPath>"
    missing_args_message = "Too few arguments. Please, provide the path to the Analyses directory."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'analysesPath', nargs=1, type=str,
            help='<Required> Anayses dir path, i.e.: /data/Analyses/ChEMBL4303805.csv')
        parser.add_argument(
            'assayId', nargs=1, type=str,
            help='<Required> Assay id from IDR, i.e.: idr0094')

    def handle(self, *args, **options):
        analysesPath = options['analysesPath'][0]
        assayId = options['assayId'][0]
        print("Reading data for", analysesPath)
        IDRUtils()._update_AnalysesToAssay(analysesPath=analysesPath, assayId=assayId)

