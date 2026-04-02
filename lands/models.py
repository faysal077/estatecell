# lands/models.py
from django.db import models

class Land(models.Model):
    rd_office = models.CharField(max_length=100)
    division = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    upazila = models.CharField(max_length=100)
    mouza = models.CharField(max_length=100, blank=True, null=True)
    dag_no = models.CharField(max_length=50, blank=True, null=True)
    khatian_no = models.CharField(max_length=50, blank=True, null=True)
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in acres")
    owner_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner_name} - {self.district} ({self.mouza})"
