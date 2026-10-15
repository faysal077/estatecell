from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserProfile, UserRole

from .models import (
    UserProfile,
    PasswordChangeLog,
    AuditLog,
    UserRole,
)

User = get_user_model()


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
        "managed_by_data_entry_name",
        "super_admin_owner_name",
        "designation",
        "department",
        "phone",
        "must_change_password",
        "created_at",
    )

    list_filter = (
        "role",
        "rd_admin__user__username",
        "managed_by_data_entry__user__username",
        "super_admin_owner__user__username",
        "department",
        "designation",
        "must_change_password",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "full_name",
        "phone",
        "designation",
        "department",
        "rd_admin__user__username",
        "managed_by_data_entry__user__username",
        "super_admin_owner__user__username",
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
                    "managed_by_data_entry",
                    "super_admin_owner",
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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "user",
                "rd_admin__user",
                "managed_by_data_entry__user",
                "super_admin_owner__user",
            )
        )

    @admin.display(description="RD Admin")
    def rd_admin_name(self, obj):
        if obj.rd_admin:
            return obj.rd_admin.user.username
        return "-"

    @admin.display(description="Managed by Data Entry")
    def managed_by_data_entry_name(self, obj):
        if obj.managed_by_data_entry:
            return obj.managed_by_data_entry.user.username
        return "-"

    @admin.display(description="Super Admin Owner")
    def super_admin_owner_name(self, obj):
        if obj.super_admin_owner:
            return obj.super_admin_owner.user.username
        return "-"

    def save_model(self, request, obj, form, change):
        # Validate role relationships before saving.
        obj.full_clean()
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(
            super().get_readonly_fields(request, obj)
        )

        profile = getattr(request.user, "userprofile", None)

        is_super_admin = (
            request.user.is_superuser
            or (
                profile is not None
                and profile.role == UserRole.SUPER_ADMIN
            )
        )

        # Only Super Admin can map an Estate Officer
        if not is_super_admin:
            if "managed_by_data_entry" not in readonly_fields:
                readonly_fields.append("managed_by_data_entry")

        return readonly_fields
    def formfield_for_foreignkey(
        self, db_field, request, **kwargs
    ):
        if db_field.name == "managed_by_data_entry":
            kwargs["queryset"] = UserProfile.objects.filter(
                role=UserRole.DATA_ENTRY
            )

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
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
        try:
            return obj.user.userprofile.role
        except UserProfile.DoesNotExist:
            return "-"

    @admin.display(description="RD Admin")
    def rd_admin_name(self, obj):
        try:
            profile = obj.user.userprofile
        except UserProfile.DoesNotExist:
            return "-"

        if profile.rd_admin:
            return profile.rd_admin.user.username
        return "-"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ======================================================
# Audit Log Admin
# ======================================================

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

    ordering = ("-timestamp",)

    date_hierarchy = "timestamp"

    list_per_page = 50

    @admin.display(description="Request Summary")
    def request_summary(self, obj):
        if not obj.request_data:
            return "-"

        text = str(obj.request_data)

        if len(text) > 100:
            return text[:100] + "..."

        return text

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
