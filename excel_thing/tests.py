from datetime import date
from decimal import Decimal
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.middleware.csrf import get_token
from django.test import RequestFactory, TestCase
from django.urls import reverse
from openpyxl import Workbook

from .models import DemandRecord, Inventory, LegacyInventory
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


def zss_upload(rows, filename="zss.xlsx"):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["Supplier Demands"])
    worksheet.append([])
    worksheet.append(
        [
            "Material",
            "Description",
            "Unit of measure",
            "Calendar Day",
            "2026-02-03",
            "2026-02-04",
            "Overall Result",
        ]
    )
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

        self.assertIn('id="demandCenterFileInput"', content)
        self.assertIn('data-display-filename="demandCenterFileName"', content)
        self.assertIn('data-submit-on-change required', content)
        self.assertNotIn("ZSS Analysis", content)
        self.assertNotIn("zss_analysis_file", content)
        self.assertIn('id="inventoryFileInput"', content)
        self.assertEqual(content.count("data-submit-on-change"), 2)
        self.assertNotIn("Import both demand files", content)
        self.assertNotIn("Replace demand data", content)
        self.assertNotIn("Replace inventory data", content)
        self.assertNotIn("Stored demand rows", content)
        self.assertNotIn("Stored inventory materials", content)

    def test_demand_upload_replaces_demand_only(self):
        demand_upload = zss_upload(
            [
                [
                    "new-demand",
                    "New part",
                    "Piece",
                    "On-Hand\nStock",
                    5,
                    None,
                    5,
                ]
            ],
            filename="demand-by-work-center.xlsx",
        )

        response = self.client.post(
            reverse("upload_demand"),
            {"demand_center_file": demand_upload},
        )

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertFalse(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertEqual(DemandRecord.objects.count(), 1)
        self.assertEqual(
            set(DemandRecord.objects.values_list("material", flat=True)),
            {"new-demand"},
        )
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())

    def test_https_localhost_origin_can_submit_demand_upload(self):
        client = self.client_class(enforce_csrf_checks=True)
        host = "localhost:8000"
        csrf_token = get_token(RequestFactory().get("/"))
        client.cookies["csrftoken"] = csrf_token
        demand_upload = zss_upload(
            [
                [
                    "new-demand",
                    "New part",
                    "Piece",
                    "On-Hand\nStock",
                    5,
                    None,
                    5,
                ]
            ]
        )

        response = client.post(
            reverse("upload_demand"),
            {
                "demand_center_file": demand_upload,
                "csrfmiddlewaretoken": csrf_token,
            },
            secure=True,
            HTTP_HOST=host,
            HTTP_ORIGIN=f"https://{host}",
        )

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertEqual(
            set(DemandRecord.objects.values_list("material", flat=True)),
            {"new-demand"},
        )

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
        demand_upload = excel_upload(
            "bad-demand.xlsx", ["Material", "Quantity"], [["new", 2]]
        )

        response = self.client.post(
            reverse("upload_demand"),
            {"demand_center_file": demand_upload},
        )

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertTrue(Inventory.objects.filter(pk=self.inventory.pk).exists())

    def test_demand_import_includes_all_row_types_from_one_workbook(self):
        demand_upload = zss_upload(
            [
                [
                    "000541",
                    "CUSHION - CHAIR, LOUNGE",
                    "Piece",
                    "On-Hand\nStock",
                    90,
                    None,
                    90,
                ],
                [
                    "000541",
                    "CUSHION - CHAIR, LOUNGE",
                    "Piece",
                    "Actual\nRequirements",
                    -7,
                    -0.115,
                    -7.115,
                ],
                [
                    "000541",
                    "CUSHION - CHAIR, LOUNGE",
                    "Piece",
                    "Open\nOrders",
                    None,
                    36,
                    36,
                ],
            ]
        )

        response = self.client.post(
            reverse("upload_demand"),
            {"demand_center_file": demand_upload},
        )

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        imported = list(
            DemandRecord.objects.order_by("record_type", "calendar_day")
        )
        self.assertEqual(len(imported), 4)
        self.assertEqual(
            {
                (record.record_type, record.calendar_day, record.quantity)
                for record in imported
            },
            {
                ("On-Hand Stock", date(2026, 2, 3), Decimal("90.00")),
                ("Actual Requirements", date(2026, 2, 3), Decimal("-7.00")),
                ("Actual Requirements", date(2026, 2, 4), Decimal("-0.115")),
                ("Open Orders", date(2026, 2, 4), Decimal("36.00")),
            },
        )
        self.assertTrue(all(record.work_center == "A20" for record in imported))

    def test_invalid_demand_workbook_preserves_existing_demand_data(self):
        invalid_demand_upload = excel_upload(
            "invalid-demand.xlsx", ["Material", "Quantity"], [["new", 2]]
        )

        response = self.client.post(
            reverse("upload_demand"),
            {
                "demand_center_file": invalid_demand_upload,
            },
        )

        self.assertRedirects(
            response, reverse("index"), fetch_redirect_response=False
        )
        self.assertTrue(DemandRecord.objects.filter(pk=self.demand.pk).exists())
        self.assertEqual(DemandRecord.objects.count(), 1)

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


class ClearImportedDataCommandTests(TestCase):
    def test_command_clears_imported_tables_and_preserves_accounts(self):
        DemandRecord.objects.create(
            material="startup-demand-marker",
            record_type="Open Orders",
            calendar_day="2026-02-03",
            quantity=1,
        )
        Inventory.objects.create(
            item_class="FG",
            item_number="startup-inventory-marker",
            standard_cost=1,
            on_hand=1,
            non_conform=0,
        )
        LegacyInventory.objects.create(material="legacy", on_hand=1)
        user = get_user_model().objects.create_user(
            username="kept-user", password="unused"
        )
        output = StringIO()

        call_command("clear_imported_data", stdout=output)

        self.assertEqual(DemandRecord.objects.count(), 0)
        self.assertEqual(Inventory.objects.count(), 0)
        self.assertEqual(LegacyInventory.objects.count(), 0)
        self.assertTrue(get_user_model().objects.filter(pk=user.pk).exists())
        self.assertIn("Cleared 3 imported record(s).", output.getvalue())

        with patch("excel_thing.views.render") as render_mock:
            index_view(RequestFactory().get(reverse("index")))

        context = render_mock.call_args.args[2]
        self.assertEqual(list(context["demand_records"]), [])
        self.assertEqual(list(context["inventory_items"]), [])