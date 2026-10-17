from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    RD_ADMIN = "RD_ADMIN", "Regional Admin"
    DATA_ENTRY = "DATA_ENTRY", "Data Entry"
    ESTATE_OFFICER = "ESTATE_OFFICER", "Estate Officer"
    VIEWER = "VIEWER", "Viewer"


class UserProfile(models.Model):
    """
    Extends Django User with roles and reporting relationships.

    Role hierarchy:
    SUPER_ADMIN
        └── manages their own isolated data

    RD_ADMIN
        └── manages assigned Data Entry users

    DATA_ENTRY
        └── manages assigned Estate Officers

    ESTATE_OFFICER
        └── assigned to one Data Entry user

    VIEWER
        └── read-only access according to assigned scope
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="userprofile",
    )

    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.DATA_ENTRY,
    )
    # assigned_estate = models.ForeignKey(
    #     "industrial_estate.IndustrialEstate",
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     related_name="assigned_officer_profiles",
    #     help_text="এই Estate Officer-এর দায়িত্বপ্রাপ্ত শিল্পনগরী।",
    # )
    # RD_ADMIN-এর দায়িত্বপ্রাপ্ত Regional Office
    assigned_regional_office = models.ForeignKey(
        "industrial_estate.RegionalOffice",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="admin_profiles",
    )

    assigned_estates = models.ManyToManyField(
        "industrial_estate.IndustrialEstate",
        blank=True,
        related_name="assigned_data_entry_profiles",
    )

    assigned_estate = models.ForeignKey(
        "industrial_estate.IndustrialEstate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assigned_officer_profiles",
    )
    # Regional Admin responsible for this Data Entry user.
    rd_admin = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": UserRole.RD_ADMIN},
        related_name="data_entry_users",
        help_text="যে Regional Admin এই Data Entry ব্যবহারকারীকে পরিচালনা করবেন।",
    )

    # Data Entry user responsible for this Estate Officer.
    managed_by_data_entry = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": UserRole.DATA_ENTRY},
        related_name="estate_officers",
        help_text="যে Data Entry ব্যবহারকারী এই Estate Officer-কে পরিচালনা করবেন।",
    )

    # Optional parent Super Admin for account-level ownership.
    # This relationship alone does not isolate database records.
    super_admin_owner = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": UserRole.SUPER_ADMIN},
        related_name="owned_profiles",
        help_text="এই ব্যবহারকারীর তথ্য ও ডেটার দায়িত্বপ্রাপ্ত Super Admin।",
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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["rd_admin", "role"]),
            models.Index(fields=["managed_by_data_entry", "role"]),
            models.Index(fields=["super_admin_owner", "role"]),
        ]

    def clean(self):
        """
        Validate role relationships.

        Note: Django does not automatically call clean() on save().
        Validate through ModelForms/admin or call full_clean() in services.
        """
        super().clean()

        if self.role == UserRole.ESTATE_OFFICER:
            if not self.managed_by_data_entry:
                raise ValidationError({
                    "managed_by_data_entry": (
                        "প্রতিটি Estate Officer-কে একজন Data Entry "
                        "ব্যবহারকারীর অধীনে assign করতে হবে।"
                    )
                })

            if self.managed_by_data_entry_id == self.pk:
                raise ValidationError({
                    "managed_by_data_entry": (
                        "একজন ব্যবহারকারী নিজেকে পরিচালনা করতে পারবেন না।"
                    )
                })

            if self.managed_by_data_entry.role != UserRole.DATA_ENTRY:
                raise ValidationError({
                    "managed_by_data_entry": (
                        "নির্বাচিত ব্যবহারকারীর role অবশ্যই Data Entry হতে হবে।"
                    )
                })

        elif self.managed_by_data_entry_id:
            raise ValidationError({
                "managed_by_data_entry": (
                    "শুধুমাত্র Estate Officer-এর জন্য Data Entry supervisor "
                    "নির্ধারণ করা যাবে।"
                )
            })

        if self.role == UserRole.DATA_ENTRY and self.rd_admin_id:
            if self.rd_admin.role != UserRole.RD_ADMIN:
                raise ValidationError({
                    "rd_admin": (
                        "নির্বাচিত ব্যবহারকারীর role অবশ্যই Regional Admin হতে হবে।"
                    )
                })

        elif self.role != UserRole.DATA_ENTRY and self.rd_admin_id:
            raise ValidationError({
                "rd_admin": (
                    "শুধুমাত্র Data Entry ব্যবহারকারীর জন্য Regional Admin "
                    "নির্ধারণ করা যাবে।"
                )
            })

        if self.super_admin_owner_id:
            if self.super_admin_owner.role != UserRole.SUPER_ADMIN:
                raise ValidationError({
                    "super_admin_owner": (
                        "নির্বাচিত account owner-এর role অবশ্যই Super Admin হতে হবে।"
                    )
                })

            if self.super_admin_owner_id == self.pk:
                raise ValidationError({
                    "super_admin_owner": (
                        "একজন Super Admin নিজের account owner হিসেবে নিজেকে "
                        "নির্বাচন করতে পারবেন না।"
                    )
                })

    def __str__(self):
        return self.full_name or self.user.username

    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

    @property
    def is_rd_admin(self):
        return self.role == UserRole.RD_ADMIN

    @property
    def is_data_entry(self):
        return self.role == UserRole.DATA_ENTRY

    @property
    def is_estate_officer(self):
        return self.role == UserRole.ESTATE_OFFICER

    @property
    def is_viewer(self):
        return self.role == UserRole.VIEWER


class PasswordChangeLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_change_logs",
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    Central audit log for tracking requests and user activities.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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

    action = models.CharField(max_length=255)

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

    timestamp = models.DateTimeField(auto_now_add=True)

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
