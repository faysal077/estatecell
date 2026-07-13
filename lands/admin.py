
from django.contrib import admin
from .models import Land, LandVerification


class LandVerificationInline(admin.StackedInline):
    model = LandVerification
    extra = 0
    can_delete = False


@admin.register(Land)
class LandAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "owner_name",
        "division",
        "district",
        "upazila",
        "rd_office",
        "total_area",
        "total_plots",
        "allocated_plots",
        "remaining_plots",
        "document_count",
        "completed_tags",
        "pending_tags",
        "is_admin_verified",
        "is_super_admin_verified",
        "created_by",
        "created_at",
    )

    list_filter = (
        "division",
        "district",
        "upazila",
        "rd_office",
        "created_at",
    )

    search_fields = (
        "owner_name",
        "district",
        "division",
        "upazila",
        "rd_office",
    )

    readonly_fields = (
        "remaining_plots",
        "document_count",
        "verified_document_count",
        "pending_document_count",
        "completed_tags",
        "pending_tags",
        "tagging_percentage",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    inlines = [
        LandVerificationInline,
    ]

    fieldsets = (

        ("Owner Information", {
            "fields": (
                "owner_name",
                "created_by",
            )
        }),

        ("Location", {
            "fields": (
                "division",
                "district",
                "upazila",
                "rd_office",
            )
        }),

        ("Land Information", {
            "fields": (
                "total_area",
                "total_plots",
                "allocated_plots",
                "remaining_plots",
            )
        }),

        ("Documents", {
            "fields": (
                "document_count",
                "verified_document_count",
                "pending_document_count",
            )
        }),

        ("Tagging", {
            "fields": (
                "completed_tags",
                "pending_tags",
                "tagging_percentage",
            )
        }),

        ("Audit", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),

    )


@admin.register(LandVerification)
class LandVerificationAdmin(admin.ModelAdmin):

    list_display = (
        "land",
        "admin_verified",
        "admin_verified_by",
        "admin_verified_date",
        "super_admin_verified",
        "super_admin_verified_by",
        "super_admin_verified_date",
    )

    list_filter = (
        "admin_verified",
        "super_admin_verified",
    )

    search_fields = (
        "land__owner_name",
    )