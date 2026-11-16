from django.core.management import call_command
from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)


class Command(RunserverCommand):
    def handle(self, *args, **options):
        call_command("clear_imported_data")
        return super().handle(*args, **options)
