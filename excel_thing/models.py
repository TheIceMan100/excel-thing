from django.db import models

class Inventory(models.Model):
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
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.material} - {self.calendar_day} ({self.quantity})"