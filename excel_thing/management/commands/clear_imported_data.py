from django.core.management.base import BaseCommand
from django.db import transaction

from excel_thing.models import DemandRecord, Inventory, LegacyInventory


class Command(BaseCommand):
    help = "Remove imported demand and inventory data."

    def handle(self, *args, **options):
        with transaction.atomic():
            deleted_count = 0
            for model in (DemandRecord, Inventory, LegacyInventory):
                deleted, _ = model.objects.all().delete()
                deleted_count += deleted

        self.stdout.write(
            self.style.SUCCESS(
                f"Cleared {deleted_count} imported record(s)."
            )
        )
