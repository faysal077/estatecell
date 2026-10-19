from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import (
    EstateFieldChangeLog,
    EstatePageVerification,
    EstateReportSubmission,
    EstateWorkflowHistory,
    VerificationComment,
)


class EstatePageVerificationInline(admin.TabularInline):
    model = EstatePageVerification
    extra = 0
    readonly_fields = ("verified_by", "verified_at", "updated_at")


class VerificationCommentInline(admin.TabularInline):
    model = VerificationComment
    extra = 0
    readonly_fields = ("author", "stage", "created_at")


@admin.register(EstateReportSubmission)
class EstateReportSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "estate",
        "status",
        "current_assignee",
        "submitted_at",
        "updated_at",
    )
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("estate__name",)
    readonly_fields = (
        "submitted_at",
        "last_action_at",
        "approved_at",
        "created_at",
        "updated_at",
    )
    inlines = [EstatePageVerificationInline, VerificationCommentInline]


@admin.register(EstatePageVerification)
class EstatePageVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "group_title",
        "page_title",
        "status",
        "verified_by",
        "verified_at",
    )
    list_filter = ("status", "group_key")
    search_fields = (
        "submission__estate__name",
        "page_title",
        "group_title",
        "page_key",
    )
    readonly_fields = ("verified_by", "verified_at", "updated_at")


@admin.register(VerificationComment)
class VerificationCommentAdmin(admin.ModelAdmin):
    list_display = ("submission", "page_verification", "author", "stage", "created_at")
    list_filter = ("stage", "created_at")
    search_fields = ("submission__estate__name", "comment")
    readonly_fields = ("author", "stage", "comment", "created_at")


@admin.register(EstateWorkflowHistory)
class EstateWorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "actor",
        "action",
        "from_status",
        "to_status",
        "created_at",
    )
    list_filter = ("action", "from_status", "to_status", "created_at")
    search_fields = ("submission__estate__name", "comment")
    readonly_fields = (
        "submission",
        "actor",
        "action",
        "from_status",
        "to_status",
        "comment",
        "metadata",
        "created_at",
    )


@admin.register(EstateFieldChangeLog)
class EstateFieldChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "actor",
        "model_label",
        "object_pk",
        "field_name",
        "created_at",
    )
    list_filter = ("model_label", "created_at")
    search_fields = (
        "submission__estate__name",
        "field_name",
        "reason",
    )
    readonly_fields = (
        "submission",
        "actor",
        "model_label",
        "object_pk",
        "field_name",
        "old_value",
        "new_value",
        "reason",
        "created_at",
    )
