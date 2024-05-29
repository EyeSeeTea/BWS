from django.core.management.base import BaseCommand
from api.utils import get_structures_from_path


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
        parser.add_argument('start_from', nargs='*', type=str, default='0',
            help='<optional> order num to begin with')

    def handle(self, *args, **options):
        path = options['path_name'][0]
        start = int(options['start_from'][0])
        print("Reading data from", path)
        if start:
            print("\tstarting from ", start)
        get_structures_from_path(path, start)
