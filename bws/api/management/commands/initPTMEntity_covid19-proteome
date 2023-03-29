"""
Command creating PTMEntity entries for each of the SARS-CoV-2 proteins derived from 
other proteins' post-translational modifications (PTMs) and/or processing events.
"""
from django.core.management.base import BaseCommand
from api.utils import initPTMEntity


class Command(BaseCommand):
    """
    Command creating PTMEntity entries for each of the SARS-CoV-2 proteins derived from 
    other proteins' post-translational modifications (PTMs) and/or processing events.
    """
    help = "Command creating PTMEntity entries for each of the SARS-CoV-2 proteins derived from other proteins' post-translational modifications (PTMs) and/or processing events"
    missing_args_message = "Too few arguments. Please, provide a filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'file_name', nargs=1, type=str,
            help='<Required> CSV file path, i.e.: /data/SARS-CoV-2/PTMEntity_covid19-proteome.csv')

    def handle(self, *args, **options):
        filepath = options['file_path'][0]
        print("Initializing PTMEntity table for SARS-CoV-2 data from ", filepath)
        initPTMEntity(filepath)
        print("Done.")