from django.core.management.base import BaseCommand
from api.utils import getStructuresFromPath


class Command(BaseCommand):
    """
    Command for updating PDB Entries
    """

    help = "Update PDB Entries <path_name>"
    missing_args_message = "Too few arguments. Please, provide a dir name."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'path_name', nargs=1, type=str,
            help='<Required> path to DataFiles')

    def handle(self, *args, **options):
        path = options['path_name'][0]
        print("Reading data from", path)
        getStructuresFromPath(path)
