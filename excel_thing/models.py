from django.db import models

class Inventory(models.Model):
    item_class = models.CharField(max_length=50, verbose_name="Class")
    item_number = models.CharField(max_length=50, verbose_name="Item Number")
    revision = models.CharField(max_length=50, blank=True, verbose_name="Rev")
    description = models.CharField(max_length=255, blank=True)
    standard_cost = models.DecimalField(max_digits=24, decimal_places=16)
    on_hand = models.DecimalField(max_digits=14, decimal_places=2)
    non_conform = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.item_number} (On Hand: {self.on_hand})"


class LegacyInventory(models.Model):
    material = models.CharField(max_length=50, primary_key=True)
    on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.material} (On Hand: {self.on_hand})"


class DemandRecord(models.Model):
    material = models.CharField(max_length=50, db_index=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    record_type = models.CharField(max_length=50, db_index=True)
    work_center = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    calendar_day = models.DateField()
    quantity = models.DecimalField(max_digits=13, decimal_places=3)

    def __str__(self):
        return f"{self.material} - {self.calendar_day} ({self.quantity})"