from django.db import models
from django.conf import settings


class AnotherLand(models.Model):

    # ==========================================================
    # RD OFFICE
    # Alphabetical order
    # ==========================================================

    RD_OFFICE_CHOICES = [
        (
            "বিসিক আঞ্চলিক কার্যালয়, চট্টগ্রাম",
            "বিসিক আঞ্চলিক কার্যালয়, চট্টগ্রাম"
        ),
        (
            "বিসিক আঞ্চলিক কার্যালয়, ঢাকা",
            "বিসিক আঞ্চলিক কার্যালয়, ঢাকা"
        ),
        (
            "বিসিক আঞ্চলিক কার্যালয়, খুলনা",
            "বিসিক আঞ্চলিক কার্যালয়, খুলনা"
        ),
        (
            "বিসিক আঞ্চলিক কার্যালয়, রাজশাহী",
            "বিসিক আঞ্চলিক কার্যালয়, রাজশাহী"
        ),
    ]


    # ==========================================================
    # DIVISION
    # Alphabetical order by Bangla name
    # ==========================================================

    DIVISION_CHOICES = [
        ("বরিশাল", "বরিশাল (Barishal)"),
        ("চট্টগ্রাম", "চট্টগ্রাম (Chittagong)"),
        ("ঢাকা", "ঢাকা (Dhaka)"),
        ("ময়মনসিংহ", "ময়মনসিংহ (Mymensingh)"),
        ("রাজশাহী", "রাজশাহী (Rajshahi)"),
        ("রংপুর", "রংপুর (Rangpur)"),
        ("সিলেট", "সিলেট (Shylet)"),
        ("খুলনা", "খুলনা (Khulna)"),
    ]


    # ==========================================================
    # OFFICE TYPE
    # ==========================================================

    OFFICE_TYPE_CHOICES = [
        ("CIDP কার্যালয়", "CIDP কার্যালয়"),
        ("অন্যান্য", "অন্যান্য"),
        ("জেলা কার্যালয়", "জেলা কার্যালয়"),
        ("মৌমাছি পালন কর্মসূচি কার্যালয়", "মৌমাছি পালন কর্মসূচি কার্যালয়"),
        ("আঞ্চলিক কার্যালয়", "আঞ্চলিক কার্যালয়"),
    ]


    # ==========================================================
    # FIELDS
    # ==========================================================

    rd_office = models.CharField(
        max_length=255,
        choices=RD_OFFICE_CHOICES,
        verbose_name="RD Office"
    )

    division = models.CharField(
        max_length=100,
        choices=DIVISION_CHOICES,
        verbose_name="Division"
    )

    district = models.CharField(
        max_length=100,
        verbose_name="District"
    )

    upazila = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Upazila"
    )

    office_type = models.CharField(
        max_length=100,
        choices=OFFICE_TYPE_CHOICES,
        verbose_name="Office Type"
    )

    office_name = models.CharField(
        max_length=255,
        verbose_name="Office Name"
    )

    total_area = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Total Area (Acres)"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="another_land_created"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==========================================================
    # VERIFICATION
    # ==========================================================

    admin_verified = models.BooleanField(
        default=False
    )

    admin_verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    admin_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="another_land_admin_verified"
    )

    super_admin_verified = models.BooleanField(
        default=False
    )

    super_admin_verified_at = models.DateTimeField(
        null=True,
        blank=True
    )

    super_admin_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="another_land_super_admin_verified"
    )

    class Meta:
        ordering = ["district", "upazila", "office_name"]
        verbose_name = "Another Land"
        verbose_name_plural = "Another Lands"

    def __str__(self):
        return self.office_name