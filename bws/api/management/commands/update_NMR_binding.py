"""
Command updating the NMR data from local CSV file containing all binding and not binding ligands to COVID-19 proteins.
"""
from django.core.management.base import BaseCommand
from api.utils import update_NMR_binding


class Command(BaseCommand):
    """
    Command to update the NMR data from local "binding" CSV file
    """
    help = "Update NMR data from local csv file containing all binding and not binding ligands to COVID-19 proteins"
    missing_args_message = "Too few arguments. Please, provide a filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path', nargs=1, type=str,
            help='<Required> CSV file path, i.e.: /data/C19-NMR-C/C19-NMR-C_pre-processed_data.csv')

    def handle(self, *args, **options):
        filepath = options['file_path'][0]
        print("Reading NMR binding data from ", filepath)
        update_NMR_binding(filepath)
        print("Done.")