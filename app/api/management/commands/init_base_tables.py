from django.core.management.base import BaseCommand
from api.utils import init_base_tables


class Command(BaseCommand):
    """
    Command to setup some base tables that need/may contain fixed data.
    """

    help = "Init base tables that need/may contain fixed data."
    requires_migrations_checks = True

    def handle(self, *args, **options):
        print(help)
        init_base_tables()
