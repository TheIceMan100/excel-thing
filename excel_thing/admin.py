from django.contrib import admin
from .models import Inventory, DemandRecord

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ("material", "on_hand")
    search_fields = ("material",)

@admin.register(DemandRecord)
class DemandRecordAdmin(admin.ModelAdmin):
    list_display = ("material", "work_center", "record_type", "calendar_day", "quantity")
    list_filter = ("record_type", "work_center", "calendar_day")
    search_fields = ("material", "description")