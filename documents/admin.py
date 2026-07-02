from django.contrib import admin
from .models import (
    Document,
    DocumentPage,
    Tag,
    PageTag,
    DocumentIndex,
    DocumentTag,
    DocumentTagEntry,
)


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
        list_display = (
            'id',
            'document',
            'page_number',
            'file_name',
            'file_type',
            'description',
            'created_at'
        )

        list_filter = (
            'file_type',
            'created_at'
        )

        search_fields = (
            'file_name',
            'description'
        )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


# @admin.register(PageTag)
# class PageTagAdmin(admin.ModelAdmin):
#     list_display = ('id', 'document_page', 'tag', 'created_at')
#     list_filter = ('tag',)


# @admin.register(DocumentIndex)
# class DocumentIndexAdmin(admin.ModelAdmin):
#     list_display = ('id', 'document', 'title', 'page_number', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('title',)

@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'document',
        'tag',
        'created_at'
    )

    search_fields = (
        'document__document_type',
        'tag__name'
    )

    list_filter = (
        'created_at',
    )

@admin.register(PageTag)
class PageTagAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'document_page',
        'tag',
        'created_at'
    )

    search_fields = (
        'tag__name',
    )

    list_filter = (
        'tag',
        'created_at'
    )
@admin.register(DocumentIndex)
class DocumentIndexAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'document',
        'title',
        'page_number',
        'created_at'
    )

    search_fields = (
        'title',
    )

    list_filter = (
        'created_at',
    )
@admin.register(DocumentTagEntry)
class DocumentTagEntryAdmin(admin.ModelAdmin):
    
    
    list_display = (
            'id',
            'document',
            'document_type',
            'page_range',
            'tag_list',
            'separated_pdf',
            'created_by',
            'created_at'
    )

    list_filter = (
        'document_type',
        'survey_type',
        'created_at'
    )

    search_fields = (
        'document_type',
    )

    filter_horizontal = (
        'tags',
    )

    readonly_fields = (
        'created_at',
    )

    fieldsets = (

        ('Document', {
            'fields': (
                'document',
            )
        }),

        ('Tag Information', {
            'fields': (
                'document_type',
                'survey_type',
                'from_page',
                'to_page',
                'tags'
            )
        }),

        ('Generated PDF', {
            'fields': (
                'separated_pdf',
            )
        }),

        ('Audit', {
            'fields': (
                'created_by',
                'created_at'
            )
        }),
    
    )
    def tag_list(self, obj):
        return ", ".join(
            obj.tags.values_list('name', flat=True)
        )

    tag_list.short_description = "Tags"