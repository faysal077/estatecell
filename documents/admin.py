from django.contrib import admin
from .models import Document, DocumentPage, Tag, PageTag, DocumentIndex


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'land', 'document_type', 'document_number', 'scanned_copy', 'file_name', 'created_at')
    list_filter = ('document_type', 'verified', 'created_at')
    search_fields = ('document_number', 'file_name', 'document_type')
    readonly_fields = ('document_number', 'created_at', 'updated_at', 'file_path_display')

    fieldsets = (
        ('Basic Info', {
            'fields': ('land', 'document_type', 'document_number', 'verified')
        }),
        ('File Info', {
            'fields': ('file_name', 'file_type', 'scanned_copy', 'merged_pdf', 'file_path_display')
        }),
        ('Page Range', {
            'fields': ('from_page', 'to_page')
        }),
        ('Metadata', {
            'fields': ('issue_date', 'issued_by', 'created_at', 'updated_at')
        }),
    )

    def file_path_display(self, obj):
        if obj.scanned_copy:
            return obj.scanned_copy.path
        return "No file uploaded"
    file_path_display.short_description = "File Path (on server)"


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


@admin.register(DocumentIndex)
class DocumentIndexAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'title', 'page_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title',)
