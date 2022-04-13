"""
Command updating the Isolde data from GitHub:
https://github.com/thorn-lab/coronavirus_structural_task_force
"""
from django.core.management.base import BaseCommand
from api.utils import update_isolde_refinements


class Command(BaseCommand):
    """
    Convert EM Validations to FunPDBe Data Exchange Format (JSON)
    """

    help = "Convert EM Validations to FunPDBe Data Exchange Format (JSON) from <path>"
    missing_args_message = "Too few arguments. Please, provide a folder name for the data files."
    requires_migrations_checks = True

    help = "Update Isolde refinements from GitHub"
    missing_args_message = "Too few arguments. Please, provide a filename."
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            'file_name', nargs=1, type=str,
            help='<Required> JSON file name')

    def handle(self, *args, **options):
        filename = options['file_name'][0]
        print("Reading data from ", filename)
        update_isolde_refinements(filename)
        print("Done.")
