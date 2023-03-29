"""
Command creating DomainEntity entries for each of the domain or region of interest for a specific SARS-CoV-2 protein
"""
from django.core.management.base import BaseCommand
from api.utils import initDomainEntity


class Command(BaseCommand):
    """
    Command creating DomainEntity entries for each of the domain or region of interest for a specific SARS-CoV-2 protein
    """
    help = "Command creating DomainEntity entries for each of the domain or region of interest for a specific SARS-CoV-2 protein"
    missing_args_message = "Too few arguments. Please, provide a filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path', nargs=1, type=str,
            help='<Required> CSV file path, i.e.: /data/SARS-CoV-2/DomainEntity_covid19-proteome.csv')

    def handle(self, *args, **options):
        filepath = options['file_path'][0]
        print("Initializing DomainEntity table for SARS-CoV-2 data from ", filepath)
        initDomainEntity(filepath)
        print("Done.")