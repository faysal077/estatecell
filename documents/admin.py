from django.contrib import admin
from .models import Document, DocumentPage, Tag, PageTag


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'land', 'document_type', 'document_number', 'verified', 'created_at')
    list_filter = ('document_type', 'verified')
    search_fields = ('document_number',)


@admin.register(DocumentPage)
class DocumentPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'page_number', 'file_name', 'file_type', 'created_at')
    list_filter = ('file_type', 'document__document_type')
    search_fields = ('file_name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(PageTag)
class PageTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_page', 'tag', 'created_at')
    list_filter = ('tag',)
