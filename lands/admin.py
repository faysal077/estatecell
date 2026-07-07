# lands/admin.py
from django.contrib import admin
from .models import Land

@admin.register(Land)
class LandAdmin(admin.ModelAdmin):
    list_display = ('owner_name', 'district', 'upazila', 'total_plots', 'total_area', 'rd_office')
    search_fields = ('owner_name', 'district', 'upazila', 'total_plots', 'total_area', 'rd_office')
    list_filter = ('division', 'district', 'upazila', 'rd_office')
