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

    REQUIRED_DOCUMENT_TYPES = [
        "Gazette",
        "Deed (Sale Deed / Registry Deed)",
        "Khatiyan",
        "Mutation (Namjari)",
        "Lease Deed",
        "Land Tax (Khajna / DCR)",
        "Porcha",
        "Mouza Map",
        "Baina / Agreement for Sale",
        "Land Survey Report",
        "Building Plan Approval",
    ]
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
        """
        Tagging progress based on required document types.
        """

        if self.total_required_tags == 0:
            return 0

        return round(
            (self.completed_tags / self.total_required_tags) * 100,
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
        return len(self.REQUIRED_DOCUMENT_TYPES)
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


# class LandVerification(models.Model):

#     land = models.OneToOneField(
#         Land,
#         on_delete=models.CASCADE,
#         related_name="verification"
#     )

#     # Admin Verification
#     admin_verified = models.BooleanField(default=False)

#     admin_verified_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="admin_verified_lands"
#     )

#     admin_verified_date = models.DateTimeField(
#         null=True,
#         blank=True
#     )

#     # Super Admin Verification
#     super_admin_verified = models.BooleanField(default=False)

#     super_admin_verified_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="super_admin_verified_lands"
#     )

#     super_admin_verified_date = models.DateTimeField(
#         null=True,
#         blank=True
#     )

#     def __str__(self):
#         return f"Verification - {self.land.owner_name}"

# class LandVerification(models.Model):

#     land = models.OneToOneField(
#         Land,
#         on_delete=models.CASCADE,
#         related_name="verification"
#     )

#     admin_verified = models.BooleanField(
#         default=False
#     )

#     admin_verified_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="admin_land_verifications"
#     )

#     admin_verified_date = models.DateTimeField(
#         null=True,
#         blank=True
#     )

#     super_admin_verified = models.BooleanField(
#         default=False
#     )

#     super_admin_verified_by = models.ForeignKey(
#         User,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name="super_admin_land_verifications"
#     )

#     super_admin_verified_date = models.DateTimeField(
#         null=True,
#         blank=True
#     )

#     def latest_tagged_entry(self):
#         """
#         Return the most recently tagged document entry.
#         """

#         return (
#             DocumentTagEntry.objects
#             .filter(document__land=self.land)
#             .order_by("-created_at")
#             .first()
#         )

#     def latest_tagged_date(self):
#         """
#         Return latest document tagging date.
#         """

#         entry = self.latest_tagged_entry()

#         if entry:
#             return entry.created_at

#         return None

#     def is_admin_currently_verified(self):
#         """
#         Admin verification is valid only if it happened
#         after the latest document/tag entry.
#         """

#         latest_tagged = self.latest_tagged_date()

#         if not latest_tagged:
#             return False

#         if not self.admin_verified:
#             return False

#         if not self.admin_verified_date:
#             return False

#         return self.admin_verified_date >= latest_tagged

#     def is_super_admin_currently_verified(self):
#         """
#         Super Admin verification is valid only if:
#         1. Admin has verified the latest version.
#         2. Super Admin verified after that Admin verification.
#         """

#         latest_tagged = self.latest_tagged_date()

#         if not latest_tagged:
#             return False

#         if not self.admin_verified:
#             return False

#         if not self.admin_verified_date:
#             return False

#         if not self.super_admin_verified:
#             return False

#         if not self.super_admin_verified_date:
#             return False

#         # New document/tag after Super Admin verification
#         if self.super_admin_verified_date < latest_tagged:
#             return False

#         # New Admin verification cycle after Super Admin verification
#         if self.super_admin_verified_date < self.admin_verified_date:
#             return False

#         return True

class LandVerification(models.Model):

    land = models.OneToOneField(
        Land,
        on_delete=models.CASCADE,
        related_name="verification"
    )

    admin_verified = models.BooleanField(default=False)

    admin_verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_land_verifications"
    )

    admin_verified_date = models.DateTimeField(
        null=True,
        blank=True
    )

    super_admin_verified = models.BooleanField(default=False)

    super_admin_verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="super_admin_land_verifications"
    )

    super_admin_verified_date = models.DateTimeField(
        null=True,
        blank=True
    )

    def latest_tagged_entry(self):
        from documents.models import DocumentTagEntry

        return (
            DocumentTagEntry.objects
            .filter(document__land=self.land)
            .order_by("-created_at")
            .first()
        )

    def latest_tagged_date(self):
        entry = self.latest_tagged_entry()

        if entry:
            return entry.created_at

        return None

    def is_admin_currently_verified(self):

        latest_tagged = self.latest_tagged_date()

        if not latest_tagged:
            return False

        if not self.admin_verified:
            return False

        if not self.admin_verified_date:
            return False

        return self.admin_verified_date >= latest_tagged

    def is_super_admin_currently_verified(self):

        latest_tagged = self.latest_tagged_date()

        if not latest_tagged:
            return False

        if not self.admin_verified:
            return False

        if not self.admin_verified_date:
            return False

        if not self.super_admin_verified:
            return False

        if not self.super_admin_verified_date:
            return False

        if self.super_admin_verified_date < latest_tagged:
            return False

        if self.super_admin_verified_date < self.admin_verified_date:
            return False

        return True

    def __str__(self):
        return f"Verification - {self.land.owner_name}"