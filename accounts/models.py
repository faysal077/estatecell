from django.db import models
from django.contrib.auth.models import User


class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    RD_ADMIN = "RD_ADMIN", "Regional Admin"
    DATA_ENTRY = "DATA_ENTRY", "Data Entry"
    VIEWER = "VIEWER", "Viewer"


class UserProfile(models.Model):
    """
    Extends Django's default User model with extra fields.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.DATA_ENTRY,
    )

    rd_admin = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": UserRole.RD_ADMIN},
        related_name="data_entry_users",
    )

    must_change_password = models.BooleanField(default=True)

    full_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )

    department = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )

    profile_picture = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.user.username


class PasswordChangeLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_change_logs",
    )

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="password_changes_made",
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.user.username} - {self.changed_at}"

class AuditLog(models.Model):
    """
    Central audit log for tracking POST requests and user activities.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    role = models.CharField(
        max_length=30,
        blank=True,
        null=True,
    )

    action = models.CharField(
        max_length=255,
    )

    method = models.CharField(
        max_length=10,
        default="POST",
    )

    path = models.TextField(
        blank=True,
        null=True,
    )

    request_data = models.JSONField(
        blank=True,
        null=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
        null=True,
    )

    status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["role", "-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
            models.Index(fields=["ip_address"]),
        ]

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"

        return (
            f"{username} | "
            f"{self.role or 'N/A'} | "
            f"{self.action} | "
            f"{self.timestamp}"
        )