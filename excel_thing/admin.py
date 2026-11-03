from django.contrib import admin
from .models import DemandRecord, Inventory, LegacyInventory

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "item_class",
        "item_number",
        "revision",
        "description",
        "standard_cost",
        "on_hand",
        "non_conform",
    )
    search_fields = ("item_class", "item_number", "revision", "description")


@admin.register(LegacyInventory)
class LegacyInventoryAdmin(admin.ModelAdmin):
    list_display = ("material", "on_hand")
    search_fields = ("material",)
    readonly_fields = ("material", "on_hand")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DemandRecord)
class DemandRecordAdmin(admin.ModelAdmin):
    list_display = ("material", "work_center", "record_type", "calendar_day", "quantity")
    list_filter = ("record_type", "work_center", "calendar_day")
    search_fields = ("material", "description")