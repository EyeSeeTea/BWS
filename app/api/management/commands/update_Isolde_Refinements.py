"""
Command updating the Isolde data from GitHub:
https://github.com/thorn-lab/coronavirus_structural_task_force
"""
from django.core.management.base import BaseCommand
from api.utils import update_isolde_refinements


class Command(BaseCommand):
    """
    Command to update the Isolde data from GitHub:
    """
    help = "Update Isolde refinements from GitHub"
    requires_migrations_checks = True

    def handle(self, *args, **options):
        update_isolde_refinements()
        print("Done.")
