from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'land', 'document_type', 'document_number', 'verified', 'created_at')
    list_filter = ('document_type', 'verified')
    search_fields = ('document_number', 'issued_by')


