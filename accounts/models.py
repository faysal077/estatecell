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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.DATA_ENTRY
    )
    rd_admin = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": UserRole.RD_ADMIN},
        related_name="data_entry_users",
    )

    # Optional fields — you can add more later
    full_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    designation = models.CharField(max_length=150, blank=True, null=True)
    department = models.CharField(max_length=150, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

