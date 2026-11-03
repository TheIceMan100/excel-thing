from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse
from openpyxl import Workbook

from .models import DemandRecord, Inventory
from .views import index_view


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
        self.inventory = Inventory.objects.create(
            item_class="OLD",
            item_number="old-inventory",
            revision="",
            description="Old inventory row",
            standard_cost="1.25",
            on_hand=5,
            non_conform=0,
        )

    @patch("excel_thing.views.render")
    def test_dashboard_view_provides_current_data_for_display(self, render_mock):
        request = RequestFactory().get(reverse("index"))

        index_view(request)

        context = render_mock.call_args.args[2]
        self.assertEqual(list(context["demand_records"]), [self.demand])
        self.assertEqual(list(context["inventory_items"]), [self.inventory])

    def test_dashboard_uploads_submit_on_file_selection_without_extra_controls(self):
        template_path = (
            Path(__file__).parent
            / "templates"
            / "excel_thing"
            / "index.html"
        )
        content = template_path.read_text()

        self.assertIn('id="demandFileInput"', content)
        self.assertIn('id="inventoryFileInput"', content)
        self.assertEqual(content.count("data-submit-on-change"), 2)
        self.assertNotIn("Replace demand data", content)
        self.assertNotIn("Replace inventory data", content)
        self.assertNotIn("Stored demand rows", content)
        self.assertNotIn("Stored inventory materials", content)

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
            [
                "Class",
                "Item Number",
                "Revision",
                "Description",
                "StandardCost",
                "On Hand",
                "Non Conform",
            ],
            [
                ["BL", "PART-1", None, "Part 1", 1.362287, 10, 0],
                ["FG", "PART-1", "A", "Part 1 revision A", 2.5, 20, 1],
                ["Total for Class BL", 30, 1, None, None, None, None],
                ["Grand Totals", 30, None, None, None, None, None],
                [r"Q:\IQWin32\Reports\Inv_Level.rpt", None, None, None, None, None, None],
                [None, None, None, None, None, None, None],
            ],
        )

        response = self.client.post(reverse("upload_inventory"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertFalse(Inventory.objects.filter(pk=self.inventory.pk).exists())
        self.assertEqual(Inventory.objects.count(), 2)
        imported = list(
            Inventory.objects.order_by("item_class", "revision")
        )
        self.assertEqual(
            [(item.item_class, item.item_number, item.revision) for item in imported],
            [("BL", "PART-1", ""), ("FG", "PART-1", "A")],
        )
        self.assertEqual(imported[0].standard_cost, Decimal("1.362287"))
        self.assertEqual(imported[0].description, "Part 1")
        self.assertEqual(imported[1].non_conform, Decimal("1.00"))
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())

    def test_invalid_demand_upload_preserves_existing_data(self):
        upload = excel_upload("bad-demand.xlsx", ["Material", "Quantity"], [["new", 2]])

        response = self.client.post(reverse("upload_demand"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())

    def test_inventory_upload_missing_required_column_preserves_existing_data(self):
        upload = excel_upload(
            "incomplete-inventory.xlsx",
            [
                "Class",
                "Item Number",
                "Rev",
                "Description",
                "Standard Cost",
                "On Hand",
            ],
            [["NEW", "new", "", "New item", 2, 2]],
        )

        response = self.client.post(reverse("upload_inventory"), {"excel_file": upload})

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())