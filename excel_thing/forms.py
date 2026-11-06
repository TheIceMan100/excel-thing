from django import forms
from django.core.validators import FileExtensionValidator


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["xls", "xlsx"])]
    )


class DemandUploadForm(forms.Form):
    demand_center_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["xls", "xlsx"])]
    )


class InventoryUploadForm(ExcelUploadForm):
    pass
