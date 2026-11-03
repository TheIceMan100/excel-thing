from django import forms
from django.core.validators import FileExtensionValidator


class ExcelUploadForm(forms.Form):
    excel_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["xls", "xlsx"])]
    )


class DemandUploadForm(ExcelUploadForm):
    pass


class InventoryUploadForm(ExcelUploadForm):
    pass
