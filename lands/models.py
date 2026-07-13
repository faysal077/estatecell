from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Land(models.Model):

    rd_office = models.CharField(max_length=100)

    division = models.CharField(max_length=100)

    district = models.CharField(max_length=100)

    upazila = models.CharField(max_length=100)

    owner_name = models.CharField(max_length=150)

    # NEW FIELD
    total_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Area in Acres"
    )
    total_plots = models.PositiveIntegerField(default=0)
    allocated_plots = models.PositiveIntegerField(default=0)

    remaining_plots = models.PositiveIntegerField(
        default=0,
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="lands"
    )

    def save(self, *args, **kwargs):
        self.remaining_plots = max(
            self.total_plots - self.allocated_plots,
            0
        )
        super().save(*args, **kwargs)

    @property
    def utilization_percentage(self):

        if self.total_plots == 0:
            return 0

        return round(
            (self.allocated_plots / self.total_plots) * 100,
            2
        )

    @property
    def document_count(self):
        return self.documents.count()
    @property
    def verified_document_count(self):
        return self.documents.filter(
            verified=True
        ).count()
    @property
    def pending_document_count(self):
        return self.documents.filter(
            verified=False
        ).count()
    @property
    def completed_tag_count(self):

        from documents.models import DocumentTagEntry

        return (
            DocumentTagEntry.objects
            .filter(document__land=self)
            .values("document_type")
            .distinct()
            .count()
        )
    @property
    def tagging_percentage(self):

        total = self.documents.count()

        if total == 0:
            return 0

        return round(
            self.completed_tag_count * 100 / total,
            2
        )
    @property
    def is_admin_verified(self):
        if hasattr(self, "verification"):
            return self.verification.admin_verified
        return False
    @property
    def is_super_admin_verified(self):
        if hasattr(self, "verification"):
            return self.verification.super_admin_verified
        return False
    @property
    def total_required_tags(self):
        """
        Total required unique document types.
        """
        return 11
    @property
    def completed_tags(self):

        from documents.models import DocumentTagEntry

        tags = (
            DocumentTagEntry.objects
            .filter(document__land=self)
            .values_list(
                "document_type",
                flat=True
            )
            .distinct()
        )

        return tags.count()
    @property
    def pending_tags(self):

        return max(
            self.total_required_tags -
            self.completed_tags,
            0
        )
    def __str__(self):
        return f"{self.owner_name} - {self.district}"


class LandVerification(models.Model):

    land = models.OneToOneField(
        Land,
        on_delete=models.CASCADE,
        related_name="verification"
    )

    # Admin Verification
    admin_verified = models.BooleanField(default=False)

    admin_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_verified_lands"
    )

    admin_verified_date = models.DateTimeField(
        null=True,
        blank=True
    )

    # Super Admin Verification
    super_admin_verified = models.BooleanField(default=False)

    super_admin_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="super_admin_verified_lands"
    )

    super_admin_verified_date = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Verification - {self.land.owner_name}"