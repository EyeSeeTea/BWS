"""
Command creating UniProt entries for each of the SARS-CoV-2 proteins in UniProtEntry table.
"""
from django.core.management.base import BaseCommand
from api.utils import initUniProtEntry


class Command(BaseCommand):
    """
    Command creating UniProt entries for each of the SARS-CoV-2 proteins in UniProtEntry table.
    """
    help = "Command creating UniProt entries for each of the SARS-CoV-2 proteins in UniProtEntry table."
    missing_args_message = "Too few arguments. Please, provide a filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path', nargs=1, type=str,
            help='<Required> CSV file path, i.e.: /data/SARS-CoV-2/UniProtEntry_covid19-proteome.csv')

    def handle(self, *args, **options):
        filepath = options['file_path'][0]
        print("Initializing UniProtEntry for SARS-CoV-2 data from ", filepath)
        initUniProtEntry(filepath)
        print("Done.")