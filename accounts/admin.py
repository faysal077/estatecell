from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "full_name",
        "role",
        "designation",
        "department",
        "phone",
        "created_at",
    )

    list_filter = (
        "role",
        "department",
        "designation",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "full_name",
        "phone",
        "designation",
        "department",
    )

    ordering = (
        "user__username",
    )

    list_editable = (
        "role",
        "designation",
        "department",
    )

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