from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from .models import DemandRecord, Inventory


def excel_upload(filename, headers, rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)

    content = BytesIO()
    workbook.save(content)
    return SimpleUploadedFile(
        filename,
        content.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


class ExcelImportTests(TestCase):
    def setUp(self):
        self.demand = DemandRecord.objects.create(
            material="old-demand",
            record_type="old",
            calendar_day="2026-01-01",
            quantity=1,
        )
        self.inventory = Inventory.objects.create(material="old-inventory", on_hand=5)

    def test_demand_upload_replaces_demand_only(self):
        upload = excel_upload(
            "demand.xlsx",
            [
                "Material",
                "Description",
                "Unit",
                "Record Type",
                "Work Center",
                "Calendar Day",
                "Quantity",
            ],
            [["new-demand", "New part", "EA", "Planned", "WC1", "2026-02-03", 12.5]],
        )

        response = self.client.post(reverse("upload_demand"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertFalse(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertEqual(DemandRecord.objects.count(), 1)
        self.assertEqual(DemandRecord.objects.get().material, "new-demand")
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())

    def test_inventory_upload_replaces_inventory_only(self):
        upload = excel_upload(
            "inventory.xlsx",
            ["Material", "On Hand"],
            [["new-inventory", 42]],
        )

        response = self.client.post(reverse("upload_inventory"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertFalse(Inventory.objects.filter(pk=self.inventory.pk).exists())
        self.assertEqual(Inventory.objects.count(), 1)
        self.assertEqual(Inventory.objects.get().material, "new-inventory")
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())

    def test_invalid_demand_upload_preserves_existing_data(self):
        upload = excel_upload("bad-demand.xlsx", ["Material", "Quantity"], [["new", 2]])

        response = self.client.post(reverse("upload_demand"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())

    def test_invalid_inventory_upload_preserves_existing_data(self):
        upload = excel_upload(
            "duplicate-inventory.xlsx",
            ["Material", "OnHand"],
            [["duplicate", 2], ["duplicate", 3]],
        )

        response = self.client.post(reverse("upload_inventory"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())