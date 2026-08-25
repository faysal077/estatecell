from django.contrib import admin
from .models import UserProfile
from .models import PasswordChangeLog


# ======================================================
# User Profile Admin
# ======================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "role",
        "rd_admin_name",
        "designation",
        "department",
        "phone",
        "must_change_password",
        "created_at",
    )

    list_filter = (
        "role",
        "rd_admin__user__username",
        "department",
        "designation",
        "must_change_password",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "rd_admin__user__username",
        "full_name",
        "phone",
        "designation",
        "department",
    )

    ordering = ("user__username",)

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "User Information",
            {
                "fields": (
                    "user",
                    "role",
                    "rd_admin",
                    "must_change_password",
                )
            },
        ),
        (
            "Profile Details",
            {
                "fields": (
                    "full_name",
                    "phone",
                    "designation",
                    "department",
                    "profile_picture",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="RD Admin")
    def rd_admin_name(self, obj):
        return (
            obj.rd_admin.user.username
            if obj.rd_admin
            else "-"
        )


# ======================================================
# Password Change Log Admin
# ======================================================

@admin.register(PasswordChangeLog)
class PasswordChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "user_role",
        "rd_admin_name",
        "changed_at",
        "changed_by",
        "ip_address",
    )

    list_filter = (
        "changed_at",
        "user__userprofile__role",
    )

    search_fields = (
        "user__username",
        "user__userprofile__full_name",
        "ip_address",
    )

    ordering = ("-changed_at",)

    readonly_fields = (
        "user",
        "changed_at",
        "changed_by",
        "ip_address",
        "user_agent",
    )

    @admin.display(description="Role")
    def user_role(self, obj):
        return obj.user.userprofile.role

    @admin.display(description="RD Admin")
    def rd_admin_name(self, obj):
        profile = obj.user.userprofile

        return (
            profile.rd_admin.user.username
            if profile.rd_admin
            else "-"
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

from django.contrib import admin
from .models import (
    UserProfile,
    PasswordChangeLog,
    AuditLog,
)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "role",
        "action",
        "request_summary",
        "timestamp",
        "ip_address",
        "status_code",
    )

    list_filter = (
        "role",
        "action",
        "method",
        "status_code",
        "timestamp",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "role",
        "action",
        "path",
        "ip_address",
        "user_agent",
    )

    readonly_fields = (
        "user",
        "role",
        "action",
        "method",
        "path",
        "request_data",
        "timestamp",
        "ip_address",
        "user_agent",
        "status_code",
    )

    ordering = (
        "-timestamp",
    )

    date_hierarchy = "timestamp"

    list_per_page = 50

    def request_summary(self, obj):

        if not obj.request_data:
            return "-"

        text = str(obj.request_data)

        if len(text) > 100:
            return text[:100] + "..."

        return text

    request_summary.short_description = "Requests"