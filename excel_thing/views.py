import re
import zipfile
from decimal import Decimal, InvalidOperation

import pandas as pd
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import DecimalField
from django.shortcuts import redirect, render
from openpyxl.utils.exceptions import InvalidFileException
from xlrd.biffh import XLRDError

from .forms import DemandUploadForm, InventoryUploadForm
from .models import DemandRecord, Inventory


class ImportValidationError(ValueError):
    pass


COLUMN_LABELS = {
    "material": "Material",
    "calendarday": "CalendarDay",
    "quantity": "Quantity",
    "class": "Class",
    "itemnumber": "Item Number",
    "rev": "Rev",
    "description": "Description",
    "standardcost": "StandardCost",
    "onhand": "OnHand",
    "nonconform": "Non Conform",
}
HEADER_ALIASES = {"revision": "rev"}


def _read_workbook(upload):
    try:
        return pd.read_excel(upload)
    except (
        ImportError,
        InvalidFileException,
        OSError,
        ValueError,
        XLRDError,
        zipfile.BadZipFile,
    ) as exc:
        raise ImportValidationError(
            "The file could not be read as an Excel workbook."
        ) from exc


def _normalized_columns(dataframe, required_columns):
    columns = {}
    for column in dataframe.columns:
        normalized = re.sub(r"[^a-z0-9]", "", str(column).casefold())
        normalized = HEADER_ALIASES.get(normalized, normalized)
        if normalized in columns:
            raise ImportValidationError(
                f"The workbook has duplicate column names: {column}."
            )
        columns[normalized] = column

    missing = [column for column in required_columns if column not in columns]
    if missing:
        names = ", ".join(COLUMN_LABELS.get(column, column) for column in missing)
        raise ImportValidationError(f"Required column(s) missing: {names}.")
    return columns


def _is_blank(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return bool(pd.isna(value))


def _text_value(value, field, row_number, max_length, required=False):
    if _is_blank(value):
        if required:
            raise ImportValidationError(
                f"Row {row_number}: {field} must not be blank."
            )
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        value = str(int(value))
    else:
        value = str(value).strip()
    if len(value) > max_length:
        raise ImportValidationError(
            f"Row {row_number}: {field} exceeds {max_length} characters."
        )
    return value


def _decimal_value(value, field, row_number, max_digits=12, decimal_places=2):
    if _is_blank(value):
        raise ImportValidationError(f"Row {row_number}: {field} must not be blank.")
    try:
        return DecimalField(
            max_digits=max_digits, decimal_places=decimal_places
        ).clean(value)
    except (InvalidOperation, TypeError, ValidationError, ValueError) as exc:
        raise ImportValidationError(
            f"Row {row_number}: {field} must be a number with at most "
            "10 integer digits and 2 decimal places."
        ) from exc


def _date_value(value, row_number):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ImportValidationError(
            f"Row {row_number}: CalendarDay must be a valid date."
        )
    return parsed.date()


def _demand_records(upload):
    dataframe = _read_workbook(upload)
    columns = _normalized_columns(
        dataframe, ("material", "calendarday", "quantity")
    )
    records = []

    for row_number, (_, row) in enumerate(dataframe.iterrows(), start=2):
        if all(_is_blank(value) for value in row):
            continue
        records.append(
            DemandRecord(
                material=_text_value(
                    row[columns["material"]],
                    "Material",
                    row_number,
                    50,
                    required=True,
                ),
                description=_text_value(
                    row[columns["description"]], "Description", row_number, 255
                )
                if "description" in columns
                else "",
                unit=_text_value(row[columns["unit"]], "Unit", row_number, 20)
                if "unit" in columns
                else "",
                record_type=_text_value(
                    row[columns["recordtype"]], "RecordType", row_number, 50
                )
                if "recordtype" in columns
                else "",
                work_center=_text_value(
                    row[columns["workcenter"]], "WorkCenter", row_number, 50
                )
                if "workcenter" in columns
                else "",
                calendar_day=_date_value(row[columns["calendarday"]], row_number),
                quantity=_decimal_value(
                    row[columns["quantity"]], "Quantity", row_number
                ),
            )
        )

    if not records:
        raise ImportValidationError(
            "The demand workbook must contain at least one data row."
        )
    return records


def _inventory_records(upload):
    dataframe = _read_workbook(upload)
    columns = _normalized_columns(
        dataframe,
        (
            "class",
            "itemnumber",
            "rev",
            "description",
            "standardcost",
            "onhand",
            "nonconform",
        ),
    )
    records = []

    for row_number, (_, row) in enumerate(dataframe.iterrows(), start=2):
        if all(_is_blank(value) for value in row):
            continue
        item_class = row[columns["class"]]
        if not _is_blank(item_class):
            class_label = str(item_class).strip()
            if (
                re.match(r"^total for class\b", class_label, re.IGNORECASE)
                or class_label.casefold() == "grand totals"
                or re.match(r"^[a-z]:[\\/]", class_label, re.IGNORECASE)
            ):
                continue

        records.append(
            Inventory(
                item_class=_text_value(
                    item_class, "Class", row_number, 50, required=True
                ),
                item_number=_text_value(
                    row[columns["itemnumber"]],
                    "Item Number",
                    row_number,
                    50,
                    required=True,
                ),
                revision=_text_value(row[columns["rev"]], "Rev", row_number, 50),
                description=_text_value(
                    row[columns["description"]], "Description", row_number, 255
                ),
                standard_cost=_decimal_value(
                    row[columns["standardcost"]],
                    "StandardCost",
                    row_number,
                    max_digits=24,
                    decimal_places=16,
                ),
                on_hand=_decimal_value(
                    row[columns["onhand"]],
                    "On Hand",
                    row_number,
                    max_digits=14,
                    decimal_places=2,
                ),
                non_conform=_decimal_value(
                    row[columns["nonconform"]],
                    "Non Conform",
                    row_number,
                    max_digits=14,
                    decimal_places=2,
                ),
            )
        )

    if not records:
        raise ImportValidationError(
            "The inventory workbook must contain at least one data row."
        )
    return records


def _replace_data(request, form_class, model, record_builder, label):
    form = form_class(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, f"{label} upload failed: {form.errors['excel_file'][0]}")
        return redirect("index")

    upload = form.cleaned_data["excel_file"]
    try:
        records = record_builder(upload)
    except ImportValidationError as exc:
        messages.error(request, f"{label} upload failed: {exc}")
        return redirect("index")

    with transaction.atomic():
        model.objects.all().delete()
        model.objects.bulk_create(records, batch_size=1000)

    row_word = "row" if len(records) == 1 else "rows"
    messages.success(
        request,
        f"{label} data replaced with {len(records)} {row_word} from {upload.name}.",
    )
    return redirect("index")


def upload_demand(request):
    return _replace_data(
        request, DemandUploadForm, DemandRecord, _demand_records, "Demand"
    )


def upload_inventory(request):
    return _replace_data(
        request, InventoryUploadForm, Inventory, _inventory_records, "Inventory"
    )


def index_view(request):
    return render(
        request,
        "excel_thing/index.html",
        {
            "demand_records": DemandRecord.objects.all()[:100],
            "inventory_items": Inventory.objects.all()[:100],
        },
    )
