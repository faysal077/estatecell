
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from datetime import date
from django.db import models
from django.core.exceptions import ValidationError
ZERO = Decimal("0.00")


# =========================================================
# 1. Existing reference models
# =========================================================

class RegionalOffice(models.Model):
    name = models.CharField("আঞ্চলিক কার্যালয়", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "আঞ্চলিক কার্যালয়"
        verbose_name_plural = "আঞ্চলিক কার্যালয়সমূহ"

    def __str__(self):
        return self.name


class District(models.Model):
    name = models.CharField("জেলা", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "জেলা"
        verbose_name_plural = "জেলাসমূহ"

    def __str__(self):
        return self.name


class Upazila(models.Model):
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="upazilas",
        verbose_name="জেলা",
    )
    name = models.CharField("উপজেলা", max_length=100)

    class Meta:
        ordering = ["district__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["district", "name"],
                name="unique_upazila_per_district",
            )
        ]
        verbose_name = "উপজেলা"
        verbose_name_plural = "উপজেলাসমূহ"

    def __str__(self):
        return f"{self.name}, {self.district.name}"


# =========================================================
# 2. Industrial estate
# Keep the existing fields and existing relationships.
# =========================================================

class IndustrialEstate(models.Model):
    class WorkflowStatus(models.TextChoices):
        DRAFT = "DRAFT", "খসড়া"
        SUBMITTED_TO_DATA_ENTRY = (
            "SUBMITTED_TO_DATA_ENTRY",
            "Data Entry-এর পর্যালোচনার অপেক্ষায়",
        )
        RETURNED_TO_ESTATE_OFFICER = (
            "RETURNED_TO_ESTATE_OFFICER",
            "Estate Officer-এর সংশোধনের অপেক্ষায়",
        )
        SUBMITTED_TO_RD_ADMIN = (
            "SUBMITTED_TO_RD_ADMIN",
            "RD Admin-এর পর্যালোচনার অপেক্ষায়",
        )
        RETURNED_TO_DATA_ENTRY = (
            "RETURNED_TO_DATA_ENTRY",
            "Data Entry-এর সংশোধনের অপেক্ষায়",
        )
        SUBMITTED_TO_SUPER_ADMIN = (
            "SUBMITTED_TO_SUPER_ADMIN",
            "Super Admin-এর যাচাইয়ের অপেক্ষায়",
        )
        RETURNED_TO_RD_ADMIN = (
            "RETURNED_TO_RD_ADMIN",
            "RD Admin-এর সংশোধনের অপেক্ষায়",
        )
        VERIFIED = "VERIFIED", "চূড়ান্তভাবে যাচাইকৃত"

    regional_office = models.ForeignKey(
        RegionalOffice,
        on_delete=models.PROTECT,
        related_name="industrial_estates",
        verbose_name="আঞ্চলিক কার্যালয়",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="industrial_estates",
        verbose_name="জেলা",
    )
    upazila = models.ForeignKey(
        Upazila,
        on_delete=models.PROTECT,
        related_name="industrial_estates",
        null=True,
        blank=True,
        verbose_name="উপজেলা",
    )

    name = models.CharField("শিল্পনগরীর নাম", max_length=250)
    officer_name = models.CharField(
        "দায়িত্বপ্রাপ্ত কর্মকর্তার নাম", max_length=200, blank=True
    )
    officer_designation = models.CharField(
        "পদবি", max_length=200, blank=True
    )
    officer_mobile = models.CharField(
        "মোবাইল নম্বর", max_length=20, blank=True
    )

    established_year = models.PositiveIntegerField(
        "প্রতিষ্ঠার বছর", null=True, blank=True
    )
    total_land_acre = models.DecimalField(
        "মোট জমি (একর)", max_digits=14, decimal_places=4,
        null=True, blank=True,
    )
    allocatable_land_acre = models.DecimalField(
        "বরাদ্দযোগ্য জমি (একর)", max_digits=14, decimal_places=4,
        null=True, blank=True,
    )

    layout_approved = models.BooleanField(
        "লে-আউট অনুমোদিত কি না", default=False
    )
    layout_approval_date = models.DateField(
        "লে-আউট অনুমোদনের তারিখ", null=True, blank=True
    )
    layout_file = models.FileField(
        "অনুমোদিত লে-আউট", upload_to="estates/layouts/",
        null=True, blank=True,
    )
    layout_revised = models.BooleanField(
        "লে-আউট সংশোধিত কি না", default=False
    )
    layout_revision_date = models.DateField(
        "লে-আউট সংশোধনের তারিখ", null=True, blank=True
    )
    establishment_purpose = models.TextField(
        "প্রতিষ্ঠার উদ্দেশ্য", blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_industrial_estates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "শিল্পনগরী"
        verbose_name_plural = "শিল্পনগরীসমূহ"

    def __str__(self):
        return self.name

    @property
    def total_plot_count(self):
        return self.plots.count()

    @property
    def allocated_plot_count(self):
        return self.plots.filter(current_status="allocated").count()

    @property
    def vacant_plot_count(self):
        return self.plots.filter(current_status="allocatable").count()

    @property
    def total_plot_area_sqft(self):
        return self.plots.aggregate(
            total=Sum("area_sqft")
        )["total"] or ZERO
    workflow_status = models.CharField(
        "পর্যালোচনার অবস্থা",
        max_length=40,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )

from django.conf import settings
from django.db import models
class EstateReview(models.Model):
    class Stage(models.TextChoices):
        DATA_ENTRY = "DATA_ENTRY", "Data Entry"
        RD_ADMIN = "RD_ADMIN", "RD Admin"
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"

    class Action(models.TextChoices):
        REVIEWED = "REVIEWED", "পর্যালোচনা"
        RETURNED = "RETURNED", "সংশোধনের জন্য ফেরত"
        FORWARDED = "FORWARDED", "পরবর্তী ধাপে প্রেরণ"
        VERIFIED = "VERIFIED", "চূড়ান্ত যাচাই"

    estate = models.ForeignKey(
        "industrial_estate.IndustrialEstate",
        on_delete=models.PROTECT,
        related_name="review_history",
        verbose_name="শিল্পনগরী",
    )

    stage = models.CharField(
        "পর্যালোচনার ধাপ",
        max_length=20,
        choices=Stage.choices,
    )

    action = models.CharField(
        "কার্যক্রম",
        max_length=20,
        choices=Action.choices,
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="estate_reviews",
        verbose_name="পর্যালোচনাকারী",
    )

    comment = models.TextField(
        "পর্যালোচনার মন্তব্য",
        blank=True,
    )

    created_at = models.DateTimeField(
        "পর্যালোচনার সময়",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "শিল্পনগরী পর্যালোচনা"
        verbose_name_plural = "শিল্পনগরী পর্যালোচনার ইতিহাস"

    def __str__(self):
        return (
            f"{self.estate.name} - "
            f"{self.get_stage_display()} - "
            f"{self.get_action_display()}"
        )


class EstateLayoutRevisionDocument(models.Model):
    estate = models.ForeignKey(
        IndustrialEstate,
        on_delete=models.CASCADE,
        related_name="layout_revision_documents",
    )
    title = models.CharField("দলিলের শিরোনাম", max_length=250)
    file = models.FileField(
        "PDF দলিল", upload_to="estates/layout_revisions/"
    )
    approval_date = models.DateField(
        "অনুমোদনের তারিখ", null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "লে-আউট সংশোধনী দলিল"
        verbose_name_plural = "লে-আউট সংশোধনী দলিলসমূহ"

    def __str__(self):
        return self.title


# =========================================================
# 3. Plot information (Page 2)
# =========================================================

class Plot(models.Model):
    class Status(models.TextChoices):
        ALLOCATABLE = "allocatable", "বরাদ্দযোগ্য"
        ALLOCATED = "allocated", "বরাদ্দকৃত"
        CANCELLED = "cancelled", "বাতিল"
        RESERVED = "reserved", "সংরক্ষিত"

    class PlotType(models.TextChoices):
        INDUSTRIAL = "industrial", "শিল্প প্লট"
        OTHER = "other", "অন্যান্য"

    estate = models.ForeignKey(
        IndustrialEstate,
        on_delete=models.PROTECT,
        related_name="plots",
        verbose_name="শিল্পনগরী",
    )
    plot_number = models.CharField("প্লট নম্বর", max_length=100)

    # Retain old data; new forms should use area_sqft.
    area_acre = models.DecimalField(
        "প্লটের আয়তন (পুরোনো একর ফিল্ড)",
        max_digits=14,
        decimal_places=4,
        null=True,
        blank=True,
    )
    area_sqft = models.DecimalField(
        "প্লটের আয়তন (বর্গফুট)",
        max_digits=16,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(ZERO)],
    )
    plot_type = models.CharField(
        "প্লটের শ্রেণি/ধরন",
        max_length=30,
        choices=PlotType.choices,
        default=PlotType.INDUSTRIAL,
    )
    current_status = models.CharField(
        "বর্তমান অবস্থা",
        max_length=20,
        choices=Status.choices,
        default=Status.ALLOCATABLE,
    )

    allocation_date = models.DateField(
        "বরাদ্দের তারিখ", null=True, blank=True
    )
    allocation_letter = models.FileField(
        "বরাদ্দপত্র",
        upload_to="plots/allocation_letters/",
        null=True,
        blank=True,
    )
    possession_date = models.DateField(
        "পজেশনের তারিখ", null=True, blank=True
    )
    possession_letter = models.FileField(
        "পজেশনপত্র",
        upload_to="plots/possession_letters/",
        null=True,
        blank=True,
    )

    cancellation_date = models.DateField(
        "প্লট বাতিলের তারিখ", null=True, blank=True
    )
    cancellation_reason = models.TextField(
        "বাতিলের কারণ ও কার্যালয়ের কার্যক্রম", blank=True
    )
    appeal_details = models.TextField("আপিলের তথ্য", blank=True)
    appeal_document = models.FileField(
        "আপিলের দলিল",
        upload_to="plots/appeals/",
        null=True,
        blank=True,
    )

    has_lease_deed = models.BooleanField(
        "লিজ ডিড আছে কি না", default=False
    )
    lease_deed_date = models.DateField(
        "লিজ ডিড সম্পাদনের তারিখ", null=True, blank=True
    )
    lessee_name = models.TextField(
        "লিজ গ্রহণকারী প্রতিষ্ঠানের নাম", blank=True
    )
    lease_deed = models.FileField(
        "লিজ ডিড",
        upload_to="plots/lease_deeds/",
        null=True,
        blank=True,
    )

    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estate__name", "plot_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["estate", "plot_number"],
                name="unique_plot_number_per_estate",
            )
        ]
        verbose_name = "প্লট"
        verbose_name_plural = "প্লটসমূহ"

    def __str__(self):
        return f"{self.estate.name} — {self.plot_number}"

    @property
    def allocated_area_sqft(self):
        return self.allocations.aggregate(
            total=Sum("allocated_area_sqft")
        )["total"] or ZERO


# =========================================================
# 4. Industrial unit general information (Page 3 / 01)
# =========================================================

class IndustrialUnit(models.Model):
    class OwnershipType(models.TextChoices):
        SOLE = "sole", "একক"
        PARTNERSHIP = "partnership", "অংশীদারি"
        LIMITED = "limited", "লিমিটেড কোম্পানি"

    class IndustrySize(models.TextChoices):
        COTTAGE = "cottage", "কুটির"
        SMALL = "small", "ক্ষুদ্র"
        MEDIUM = "medium", "মাঝারি"
        LARGE = "large", "বৃহৎ"

    class OperationalStatus(models.TextChoices):
        ACTIVE = "active", "সচল"
        SICK = "sick", "রুগ্ন"
        CLOSED = "closed", "বন্ধ"
        IMPLEMENTING = "implementing", "বাস্তবায়নাধীন"
    class UnitStatus(models.TextChoices):
        OPERATING = "OPERATING", "চালু"
        TEMPORARILY_CLOSED = "TEMP_CLOSED", "সাময়িকভাবে বন্ধ"
        PERMANENTLY_CLOSED = "PERM_CLOSED", "স্থায়ীভাবে বন্ধ"
        UNDER_CONSTRUCTION = "CONSTRUCTION", "নির্মাণাধীন"
        NOT_STARTED = "NOT_STARTED", "উৎপাদন শুরু হয়নি"
    current_status = models.CharField(
        "শিল্প ইউনিটের বর্তমান অবস্থা",
        max_length=20,
        choices=UnitStatus.choices,
        default=UnitStatus.NOT_STARTED,
    )
    production_active = models.BooleanField(
        "উৎপাদন কার্যক্রম চালু আছে কি না",
        default=False,
    )
    estate = models.ForeignKey(
        IndustrialEstate,
        on_delete=models.PROTECT,
        related_name="industrial_units",
        verbose_name="শিল্পনগরী",
    )
    name = models.CharField("শিল্প ইউনিটের নাম", max_length=250)
    unit_code = models.CharField(
        "ইউনিট কোড/নিবন্ধন নম্বর",
        max_length=100,
        unique=True,
    )

    owner_name = models.CharField(
        "উদ্যোক্তা/মালিকের নাম", max_length=250, blank=True
    )
    owner_phone = models.CharField(
        "মালিকের ফোন নম্বর", max_length=25, blank=True
    )
    representative_name = models.CharField(
        "প্রতিনিধির নাম", max_length=250, blank=True
    )
    representative_phone = models.CharField(
        "প্রতিনিধির ফোন নম্বর", max_length=25, blank=True
    )

    ownership_type = models.CharField(
        "মালিকানার ধরন",
        max_length=20,
        choices=OwnershipType.choices,
        blank=True,
    )
    industry_size = models.CharField(
        "শিল্পের ধরন",
        max_length=20,
        choices=IndustrySize.choices,
        blank=True,
    )
    production_sector = models.CharField(
        "উৎপাদনের খাত", max_length=250, blank=True
    )
    production_sector_other = models.CharField(
        "অন্যান্য উৎপাদন খাত", max_length=250, blank=True
    )
    production_subsector = models.CharField(
        "উৎপাদনের উপখাত", max_length=250, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)

    factory_layout_approval_date = models.DateField(
        "কারখানার লে-আউট অনুমোদনের তারিখ",
        null=True,
        blank=True,
    )
    factory_layout_plan = models.FileField(
        "অনুমোদিত লে-আউট প্ল্যান",
        upload_to="units/factory_layouts/",
        null=True,
        blank=True,
    )
    production_start_date = models.DateField(
        "উৎপাদন শুরুর তারিখ", null=True, blank=True
    )

    operational_status = models.CharField(
        "বর্তমান অবস্থা",
        max_length=20,
        choices=OperationalStatus.choices,
        default=OperationalStatus.IMPLEMENTING,
    )
    sick_closed_date = models.DateField(
        "রুগ্ন/বন্ধ হওয়ার তারিখ", null=True, blank=True
    )
    sick_closed_reason = models.TextField(
        "রুগ্ন/বন্ধ হওয়ার কারণ", blank=True
    )
    office_action = models.TextField(
        "শিল্পনগরী কার্যালয়ের গৃহীত ব্যবস্থা", blank=True
    )

    has_floor_rental = models.BooleanField(
        "ফ্লোর স্পেস ভাড়া দেওয়া আছে কি না", default=False
    )
    tenant_name = models.CharField(
        "ভাড়াটিয়া প্রতিষ্ঠানের নাম", max_length=250, blank=True
    )
    rental_start_date = models.DateField(
        "চুক্তি শুরুর তারিখ", null=True, blank=True
    )
    rental_end_date = models.DateField(
        "চুক্তি শেষের তারিখ", null=True, blank=True
    )
    annual_rent_received = models.DecimalField(
        "বাৎসরিক প্রাপ্ত অর্থ",
        max_digits=16,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )
    rental_agreement = models.FileField(
        "ভাড়ার চুক্তিপত্র",
        upload_to="units/rental_agreements/",
        null=True,
        blank=True,
    )
    rental_comments = models.TextField("ভাড়া সংক্রান্ত মন্তব্য", blank=True)

    is_export_oriented = models.BooleanField(
        "রপ্তানিমুখী শিল্প ইউনিট কি না", default=False
    )
    # কারখানা ও উৎপাদন
    factory_layout_approval_date = models.DateField(
        "কারখানার লে-আউট অনুমোদনের তারিখ",
        null=True,
        blank=True,
    )

    factory_layout_file = models.FileField(
        "কারখানার অনুমোদিত লে-আউট প্ল্যান",
        upload_to="industrial_units/factory_layouts/",
        null=True,
        blank=True,
    )

    production_start_date = models.DateField(
        "উৎপাদন শুরুর তারিখ",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estate__name", "name"]
        verbose_name = "শিল্প ইউনিট"
        verbose_name_plural = "শিল্প ইউনিটসমূহ"

    def __str__(self):
        return f"{self.name} ({self.unit_code})"

    @property
    def total_allocated_area_sqft(self):
        return self.plot_allocations.aggregate(
            total=Sum("allocated_area_sqft")
        )["total"] or ZERO

    @property
    def rental_duration_months(self):
        if not self.rental_start_date or not self.rental_end_date:
            return None
        return max(
            0,
            (self.rental_end_date.year - self.rental_start_date.year) * 12
            + self.rental_end_date.month
            - self.rental_start_date.month,
        )
# =========================================================
# 4. Floor space rental information (Page 3 / 02)
# =========================================================
def current_month_start():
    """Return the first day of the current month."""
    today = date.today()
    return today.replace(day=1)


class FloorSpaceRental(models.Model):
    industrial_unit = models.ForeignKey(
        "IndustrialUnit",
        on_delete=models.CASCADE,
        related_name="floor_rentals",
        verbose_name="শিল্প ইউনিট",
    )

    month = models.DateField(
        default=current_month_start,
        verbose_name="মাস",
        help_text="যে মাসের ভাড়ার তথ্য সংরক্ষণ করা হচ্ছে",
    )

    is_rented = models.BooleanField(
        default=False,
        verbose_name="ফ্লোর স্পেস ভাড়া দেওয়া আছে কি না",
    )

    tenant_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ভাড়াটিয়া প্রতিষ্ঠানের নাম",
    )

    rental_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="চুক্তি শুরুর তারিখ",
    )

    rental_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="চুক্তি শেষের তারিখ",
    )

    annual_rent_received = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="বাৎসরিক বিসিকের প্রাপ্ত অর্থ",
    )

    rental_agreement = models.FileField(
        upload_to="floor_rental/agreements/",
        blank=True,
        null=True,
        verbose_name="ভাড়ার চুক্তিপত্র",
    )

    rental_comments = models.TextField(
        blank=True,
        verbose_name="মন্তব্য",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "ফ্লোর স্পেস ভাড়ার তথ্য"
        verbose_name_plural = "ফ্লোর স্পেস ভাড়ার তথ্য"
        ordering = ["-month", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["industrial_unit", "month"],
                name="unique_floor_rental_unit_month",
            )
        ]

    def clean(self):
        if self.is_rented:
            errors = {}

            if not self.tenant_name:
                errors["tenant_name"] = (
                    "ভাড়াটিয়া প্রতিষ্ঠানের নাম লিখুন।"
                )

            if not self.rental_start_date:
                errors["rental_start_date"] = (
                    "চুক্তি শুরুর তারিখ দিন।"
                )

            if not self.rental_end_date:
                errors["rental_end_date"] = (
                    "চুক্তি শেষের তারিখ দিন।"
                )

            if (
                self.rental_start_date
                and self.rental_end_date
                and self.rental_end_date < self.rental_start_date
            ):
                errors["rental_end_date"] = (
                    "চুক্তি শেষের তারিখ শুরুর তারিখের আগে হতে পারবে না।"
                )

            if errors:
                raise ValidationError(errors)

    @property
    def rental_duration_months(self):
        """Approximate duration in months, including partial months."""
        if not self.rental_start_date or not self.rental_end_date:
            return None

        start = self.rental_start_date
        end = self.rental_end_date

        months = (
            (end.year - start.year) * 12
            + end.month - start.month
        )

        if end.day >= start.day:
            months += 1

        return max(months, 0)

    def __str__(self):
        return (
            f"{self.industrial_unit} - "
            f"{self.month:%Y-%m}"
        )

# =========================================================
# 5. Monthly record mixin for common date and month-year fields
# =========================================================
class MonthlyRecordMixin(models.Model):
    """মাসভিত্তিক রেকর্ডের জন্য সাধারণ তারিখ ও মাস-বছর।"""

    report_date = models.DateField(
        "রিপোর্টের তারিখ",
        default=timezone.localdate,
    )
    report_month = models.PositiveSmallIntegerField(
        "মাস",
        editable=False,
        db_index=True,
    )
    report_year = models.PositiveSmallIntegerField(
        "বছর",
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.report_month = self.report_date.month
        self.report_year = self.report_date.year
        super().save(*args, **kwargs)

# =========================================================
# 5. One plot can be allocated wholly or partly to a unit
# =========================================================

class UnitPlotAllocation(models.Model):
    class AllocationType(models.TextChoices):
        FULL = "FULL", "পূর্ণ বরাদ্দ"
        PARTIAL = "PARTIAL", "আংশিক বরাদ্দ"

    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.PROTECT,
        related_name="plot_allocations",
        verbose_name="শিল্প ইউনিট",
    )
    plot = models.ForeignKey(
        Plot,
        on_delete=models.PROTECT,
        related_name="allocations",
        verbose_name="প্লট",
    )
    allocation_type = models.CharField(
        "বরাদ্দের ধরন",
        max_length=10,
        choices=AllocationType.choices,
        default=AllocationType.FULL,
    )
    allocated_area_sqft = models.DecimalField(
        "বরাদ্দকৃত আয়তন (বর্গফুট)",
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    allocation_date = models.DateField(
        "বরাদ্দের তারিখ", null=True, blank=True
    )
    possession_date = models.DateField(
        "পজেশনের তারিখ", null=True, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plot__plot_number", "industrial_unit__name"]
        verbose_name = "প্লট বরাদ্দ"
        verbose_name_plural = "প্লট বরাদ্দসমূহ"

    def __str__(self):
        return f"{self.plot} → {self.industrial_unit}"

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if self.industrial_unit_id and self.plot_id:
            if self.industrial_unit.estate_id != self.plot.estate_id:
                errors["plot"] = (
                    "শিল্প ইউনিট ও প্লট একই শিল্পনগরীর হতে হবে।"
                )

        if self.plot_id and self.allocated_area_sqft:
            existing = self.plot.allocations.exclude(pk=self.pk).aggregate(
                total=Sum("allocated_area_sqft")
            )["total"] or ZERO

            if self.plot.area_sqft is not None:
                if existing + self.allocated_area_sqft > self.plot.area_sqft:
                    errors["allocated_area_sqft"] = (
                        "প্লটের মোট আয়তনের চেয়ে বরাদ্দ বেশি হতে পারবে না।"
                    )

        if errors:
            raise ValidationError(errors)


# =========================================================
# 6. Products (repeatable rows)
# =========================================================

class UnitProduct(models.Model):
    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.CASCADE,
        related_name="products",
    )
    name = models.CharField("পণ্যের নাম", max_length=250)
    production_sector = models.CharField(
        "উৎপাদনের খাত", max_length=250, blank=True
    )
    production_subsector = models.CharField(
        "উৎপাদনের উপখাত", max_length=250, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "উৎপাদিত পণ্য"
        verbose_name_plural = "উৎপাদিত পণ্যসমূহ"

    def __str__(self):
        return self.name


# =========================================================
# 7. Employment history (month/year records)
# =========================================================

class EmploymentHistory(models.Model):
    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.CASCADE,
        related_name="employment_records",
        verbose_name="শিল্প ইউনিট",
    )

    year = models.PositiveIntegerField("বছর")
    month = models.PositiveSmallIntegerField("মাস")

    permanent_male = models.PositiveIntegerField(
        "স্থায়ী পুরুষ কর্মী", default=0
    )
    permanent_female = models.PositiveIntegerField(
        "স্থায়ী নারী কর্মী", default=0
    )

    temporary_male = models.PositiveIntegerField(
        "অস্থায়ী পুরুষ কর্মী", default=0
    )
    temporary_female = models.PositiveIntegerField(
        "অস্থায়ী নারী কর্মী", default=0
    )

    third_gender_workers = models.PositiveIntegerField(
        "তৃতীয় লিঙ্গের কর্মী", default=0
    )

    comments = models.TextField("মন্তব্য", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_male(self):
        return self.permanent_male + self.temporary_male

    @property
    def total_female(self):
        return self.permanent_female + self.temporary_female

    @property
    def total_employment(self):
        return (
            self.permanent_male
            + self.permanent_female
            + self.temporary_male
            + self.temporary_female
            + self.third_gender_workers
        )

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(
                fields=["industrial_unit", "year", "month"],
                name="unique_employment_month_per_unit",
            )
        ]
        verbose_name = "কর্মসংস্থানের ইতিহাস"
        verbose_name_plural = "কর্মসংস্থানের ইতিহাস"

    def __str__(self):
        return (
            f"{self.industrial_unit} — "
            f"{self.month}/{self.year}"
        )


# =========================================================
# 8. Monthly receivables and collections
# =========================================================

class MonthlyReceivable(models.Model):
    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.PROTECT,
        related_name="monthly_accounts",
        verbose_name="শিল্প ইউনিট",
    )
    fiscal_year = models.CharField("অর্থবছর", max_length=9)
    month = models.PositiveSmallIntegerField("হিসাবের মাস")
    calculation_date = models.DateField("হিসাবের তারিখ")

    previous_balance = models.DecimalField(
        "পূর্ববর্তী বকেয়া", max_digits=16, decimal_places=2,
        default=ZERO,
    )
    service_charge_due = models.DecimalField(
        "সার্ভিস চার্জ", max_digits=16, decimal_places=2, default=ZERO
    )
    service_charge_interest = models.DecimalField(
        "সার্ভিস চার্জের সুদ", max_digits=16, decimal_places=2,
        default=ZERO,
    )
    land_installment_due = models.DecimalField(
        "জমির কিস্তি", max_digits=16, decimal_places=2, default=ZERO
    )
    land_installment_interest = models.DecimalField(
        "জমির কিস্তির সুদ", max_digits=16, decimal_places=2, default=ZERO
    )
    land_development_tax_due = models.DecimalField(
        "ভূমি উন্নয়ন কর", max_digits=16, decimal_places=2, default=ZERO
    )
    land_development_tax_interest = models.DecimalField(
        "ভূমি উন্নয়ন করের সুদ", max_digits=16, decimal_places=2,
        default=ZERO,
    )
    water_bill_due = models.DecimalField(
        "পানির বিল", max_digits=16, decimal_places=2, default=ZERO
    )
    water_bill_interest = models.DecimalField(
        "পানির বিলের সুদ", max_digits=16, decimal_places=2, default=ZERO
    )
    other_due = models.DecimalField(
        "অন্যান্য পাওনা", max_digits=16, decimal_places=2, default=ZERO
    )
    other_due_description = models.TextField(
        "অন্যান্য পাওনার বিবরণ", blank=True
    )

    annual_collection_target = models.DecimalField(
        "অর্থবছরের আদায় লক্ষ্যমাত্রা",
        max_digits=16, decimal_places=2, default=ZERO,
    )
    monthly_collection_target = models.DecimalField(
        "মাসিক আদায় লক্ষ্যমাত্রা",
        max_digits=16, decimal_places=2, default=ZERO,
    )
    statement_file = models.FileField(
        "রেওয়ামিল",
        upload_to="accounts/statements/",
        null=True,
        blank=True,
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["industrial_unit", "-fiscal_year", "-month"]
        constraints = [
            models.UniqueConstraint(
                fields=["industrial_unit", "fiscal_year", "month"],
                name="unique_monthly_account_per_unit",
            )
        ]
        verbose_name = "মাসিক পাওনার হিসাব"
        verbose_name_plural = "মাসিক পাওনার হিসাবসমূহ"

    def __str__(self):
        return f"{self.industrial_unit} — {self.fiscal_year}/{self.month}"

    @property
    def current_month_new_due(self):
        fields = (
            self.service_charge_due,
            self.service_charge_interest,
            self.land_installment_due,
            self.land_installment_interest,
            self.land_development_tax_due,
            self.land_development_tax_interest,
            self.water_bill_due,
            self.water_bill_interest,
            self.other_due,
        )
        return sum(fields, ZERO)

    @property
    def total_payable(self):
        return self.previous_balance + self.current_month_new_due

    @property
    def total_collected(self):
        return self.payments.aggregate(
            total=Sum("amount")
        )["total"] or ZERO

    @property
    def outstanding_balance(self):
        return self.total_payable - self.total_collected

    @property
    def monthly_collection_percentage(self):
        if not self.monthly_collection_target:
            return ZERO
        return (
            self.total_collected
            / self.monthly_collection_target
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    @property
    def fiscal_year_cumulative_collection(self):
        payments = MonthlyPayment.objects.filter(
            account__industrial_unit=self.industrial_unit,
            account__fiscal_year=self.fiscal_year,
        )

        if self.month >= 7:
            payments = payments.filter(
                account__month__gte=7,
                account__month__lte=self.month,
            )
        else:
            payments = payments.filter(
                account__month__gte=7
            ) | payments.filter(
                account__month__lte=self.month
            )

        return payments.aggregate(
            total=Sum("amount")
        )["total"] or ZERO

    def carry_forward_previous_balance(self):
        """Copy the preceding month's calculated outstanding balance."""
        previous = MonthlyReceivable.objects.filter(
            industrial_unit=self.industrial_unit,
            fiscal_year=self.fiscal_year,
            month=self.month - 1,
        ).first()

        if previous:
            self.previous_balance = previous.outstanding_balance
        elif self.month == 7:
            # July starts a new fiscal year; carry-forward across fiscal
            # years must be handled by the account-entry workflow.
            prior_year = str(int(self.fiscal_year[:4]) - 1)
            previous = MonthlyReceivable.objects.filter(
                industrial_unit=self.industrial_unit,
                fiscal_year=f"{prior_year}-{int(prior_year) + 1}",
                month=6,
            ).first()
            if previous:
                self.previous_balance = previous.outstanding_balance

        return self.previous_balance


class MonthlyPayment(models.Model):
    account = models.ForeignKey(
        MonthlyReceivable,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="মাসিক হিসাব",
    )
    payment_date = models.DateField("আদায়ের তারিখ")
    amount = models.DecimalField(
        "আদায়কৃত অর্থ",
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    receipt_number = models.CharField(
        "চালান/রসিদ নম্বর", max_length=150
    )
    proof_file = models.FileField(
        "আদায়ের প্রমাণপত্র",
        upload_to="accounts/payment_proofs/",
        null=True,
        blank=True,
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["payment_date", "pk"]
        verbose_name = "আদায়ের রেকর্ড"
        verbose_name_plural = "আদায়ের রেকর্ডসমূহ"

    def __str__(self):
        return f"{self.receipt_number} — {self.amount}"


# =========================================================
# 9. Bank loans and NOC
# =========================================================

class BankLoan(models.Model):
    class LoanStatus(models.TextChoices):
        ACTIVE = "active", "চলমান"
        REPAID = "repaid", "পরিশোধিত"
        CLOSED = "closed", "বন্ধ"
        DEFAULTED = "defaulted", "খেলাপি"
        OTHER = "other", "অন্যান্য"

    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.CASCADE,
        related_name="bank_loans",
    )
    bank_name = models.CharField("ব্যাংকের নাম", max_length=250)
    loan_amount = models.DecimalField(
        "ঋণের পরিমাণ", max_digits=16, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
    )
    loan_date = models.DateField("ঋণ গ্রহণের তারিখ", null=True, blank=True)
    noc_date = models.DateField(
        "অনাপত্তিপত্র প্রদানের তারিখ", null=True, blank=True
    )
    status = models.CharField(
        "ঋণের বর্তমান অবস্থা",
        max_length=20,
        choices=LoanStatus.choices,
        default=LoanStatus.ACTIVE,
    )
    noc_document = models.FileField(
        "অনাপত্তিপত্র", upload_to="units/bank_loans/noc/",
        null=True, blank=True,
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["bank_name"]
        verbose_name = "ব্যাংক ঋণ"
        verbose_name_plural = "ব্যাংক ঋণসমূহ"

    def __str__(self):
        return f"{self.bank_name} — {self.industrial_unit.name}"


class BankLoanDocument(models.Model):
    loan = models.ForeignKey(
        BankLoan,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField("নথির নাম", max_length=250)
    file = models.FileField(
        "নথি", upload_to="units/bank_loans/documents/"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# =========================================================
# 10. Unit ownership/transfer records
# =========================================================

class UnitTransfer(models.Model):
    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.PROTECT,
        related_name="transfers",
    )
    transfer_date = models.DateField("হস্তান্তরের তারিখ")
    from_company = models.CharField("দাতা প্রতিষ্ঠানের নাম", max_length=250)
    to_company = models.CharField("গ্রহীতা প্রতিষ্ঠানের নাম", max_length=250)
    reason = models.TextField("হস্তান্তরের কারণ", blank=True)
    approval_document = models.FileField(
        "অনুমোদন/চূড়ান্ত পত্র",
        upload_to="units/transfers/",
        null=True,
        blank=True,
    )
    comments = models.TextField("মন্তব্য", blank=True)

    class Meta:
        ordering = ["-transfer_date"]
        verbose_name = "মালিকানা/ইউনিট হস্তান্তর"
        verbose_name_plural = "মালিকানা/ইউনিট হস্তান্তরসমূহ"

    def __str__(self):
        return f"{self.from_company} → {self.to_company}"


# =========================================================
# 11. Plot cancellation and appeal history
# =========================================================

class PlotCancellationAppeal(models.Model):
    class RecordType(models.TextChoices):
        CANCELLATION = "cancellation", "প্লট বাতিল"
        APPEAL = "appeal", "আপিল"
    class AppealStatus(models.TextChoices):
        PENDING = "pending", "বিবেচনাধীন"
        APPROVED = "approved", "অনুমোদিত"
        REJECTED = "rejected", "নাকচ"
        WITHDRAWN = "withdrawn", "প্রত্যাহার"
        OTHER = "other", "অন্যান্য"
    
    record_type = models.CharField(
        "তথ্যের ধরন",
        max_length=20,
        choices=RecordType.choices,
        default=RecordType.CANCELLATION,
        db_index=True,
    )

    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.PROTECT,
        related_name="cancellation_appeals",
    )
    plot = models.ForeignKey(
        Plot,
        on_delete=models.PROTECT,
        related_name="cancellation_appeals",
    )
    cancellation_date = models.DateField(
        "বাতিলের তারিখ", null=True, blank=True
    )
    cancellation_reason = models.TextField("বাতিলের কারণ", blank=True)
    office_action = models.TextField(
        "কার্যালয় কর্তৃক গৃহীত কার্যক্রম", blank=True
    )
    appeal_filed = models.BooleanField("আপিল করা হয়েছে কি না", default=False)
    appeal_date = models.DateField("আপিলের তারিখ", null=True, blank=True)
    appeal_details = models.TextField("আপিলের বিবরণ", blank=True)
    latest_status = models.CharField(
        "সর্বশেষ অবস্থা",
        max_length=20,
        choices=AppealStatus.choices,
        default=AppealStatus.PENDING,
    )
    document = models.FileField(
        "সংশ্লিষ্ট দলিল",
        upload_to="plots/cancellation_appeals/",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cancellation_date", "-created_at"]
        verbose_name = "প্লট বাতিল ও আপিল"
        verbose_name_plural = "প্লট বাতিল ও আপিলসমূহ"

    def __str__(self):
        return f"{self.plot} — {self.get_latest_status_display()}"


# =========================================================
# 12. Export products (repeatable rows)
# =========================================================

class ExportProduct(models.Model):
    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.CASCADE,
        related_name="export_products",
    )
    product_name = models.CharField("রপ্তানিকৃত পণ্যের নাম", max_length=250)
    importing_country = models.CharField(
        "আমদানিকারক দেশের নাম", max_length=200, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)

    class Meta:
        ordering = ["product_name"]
        verbose_name = "রপ্তানিকৃত পণ্য"
        verbose_name_plural = "রপ্তানিকৃত পণ্যসমূহ"

    def __str__(self):
        return self.product_name


# =========================================================
# 13. Environment, solar, waste and utility usage
# =========================================================

class EnvironmentalData(models.Model):
    industrial_unit = models.OneToOneField(
        IndustrialUnit,
        on_delete=models.CASCADE,
        related_name="environmental_data",
    )
    has_solar_panel = models.BooleanField("সোলার প্যানেল আছে কি না", default=False)
    solar_capacity = models.DecimalField(
        "সোলার ক্যাপাসিটি", max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    solar_capacity_unit = models.CharField(
        "সোলার ক্যাপাসিটির একক", max_length=30, blank=True
    )

    needs_liquid_waste_treatment = models.BooleanField(
        "তরল বর্জ্য পরিশোধন প্রয়োজন কি না", default=False
    )
    has_etp = models.BooleanField("ETP আছে কি না", default=False)
    etp_capacity = models.DecimalField(
        "ETP-এর পরিশোধন ক্ষমতা", max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    etp_capacity_unit = models.CharField(
        "ETP ক্ষমতার একক", max_length=30, blank=True
    )
    effluent_type = models.CharField("ইফ্লুয়েন্টের ধরন", max_length=250, blank=True)
    solid_waste_quantity = models.DecimalField(
        "কঠিন বর্জ্যের পরিমাণ", max_digits=14, decimal_places=2,
        null=True, blank=True,
    )
    solid_waste_unit = models.CharField(
        "কঠিন বর্জ্যের একক", max_length=30, blank=True
    )
    solid_waste_management = models.TextField(
        "কঠিন বর্জ্য ব্যবস্থাপনার পদ্ধতি", blank=True
    )
    has_own_liquid_waste_management = models.BooleanField(
        "নিজস্ব তরল বর্জ্য ব্যবস্থাপনা আছে কি না", default=False
    )
    waste_goes_to_city_drain = models.BooleanField(
        "সিটি/পৌর ড্রেনে বর্জ্য যায় কি না", default=False
    )
    comments = models.TextField("মন্তব্য", blank=True)

    def __str__(self):
        return f"পরিবেশ তথ্য — {self.industrial_unit.name}"


class UtilityUsage(models.Model):
    class UtilityType(models.TextChoices):
        GAS = "gas", "গ্যাস"
        ELECTRICITY = "electricity", "বিদ্যুৎ"
        LPG = "lpg", "এলপিজি"
        WATER = "water", "পানি"

    class PeriodType(models.TextChoices):
        MONTHLY = "monthly", "মাসিক"
        ANNUAL = "annual", "বাৎসরিক"

    environmental_data = models.ForeignKey(
        EnvironmentalData,
        on_delete=models.CASCADE,
        related_name="utility_usages",
    )
    utility_type = models.CharField(
        "সেবার ধরন", max_length=20, choices=UtilityType.choices
    )
    period_type = models.CharField(
        "হিসাবের মেয়াদ", max_length=10, choices=PeriodType.choices
    )
    year = models.PositiveIntegerField("বছর")
    month = models.PositiveSmallIntegerField(
        "মাস", null=True, blank=True
    )
    quantity = models.DecimalField(
        "ব্যবহারের পরিমাণ", max_digits=16, decimal_places=2,
        validators=[MinValueValidator(ZERO)],
    )
    quantity_unit = models.CharField("পরিমাণের একক", max_length=30)
    bill_amount = models.DecimalField(
        "বিলের পরিমাণ", max_digits=16, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(ZERO)],
    )
    comments = models.TextField("মন্তব্য", blank=True)

    class Meta:
        ordering = ["-year", "-month", "utility_type"]
        verbose_name = "ইউটিলিটি ব্যবহারের তথ্য"
        verbose_name_plural = "ইউটিলিটি ব্যবহারের তথ্যসমূহ"

    def __str__(self):
        return f"{self.get_utility_type_display()} — {self.year}"
class LegalCase(models.Model):

    class CaseType(models.TextChoices):
        CIVIL = "civil", "দেওয়ানি"
        CRIMINAL = "criminal", "ফৌজদারি"
        OTHER = "other", "অন্যান্য"

    class CaseStatus(models.TextChoices):
        ONGOING = "ongoing", "চলমান"
        DISPOSED = "disposed", "নিষ্পত্তি"
        APPEAL = "appeal", "আপিল"

    estate = models.ForeignKey(
        IndustrialEstate,
        on_delete=models.PROTECT,
        related_name="legal_cases",
        verbose_name="শিল্পনগরী",
    )

    industrial_unit = models.ForeignKey(
        IndustrialUnit,
        on_delete=models.PROTECT,
        related_name="legal_cases",
        verbose_name="সংশ্লিষ্ট শিল্প ইউনিট",
        null=True,
        blank=True,
    )

    case_number = models.CharField("মামলার নম্বর", max_length=100)
    court_name = models.CharField("আদালতের নাম", max_length=255)

    case_type = models.CharField(
        "মামলার ধরন",
        max_length=20,
        choices=CaseType.choices,
    )

    case_date = models.DateField("মামলার তারিখ", null=True, blank=True)
    plaintiff_name = models.CharField("বাদীর নাম", max_length=255)
    defendant_name = models.CharField("বিবাদীর নাম", max_length=255)

    case_subject = models.TextField("মামলার বিষয়")
    local_office_action = models.TextField(
        "স্থানীয় কার্যালয়ের কার্যক্রম", blank=True
    )
    latest_progress = models.TextField("সর্বশেষ অগ্রগতি", blank=True)
    latest_hearing_date = models.DateField(
        "সর্বশেষ শুনানি/আদেশের তারিখ", null=True, blank=True
    )
    bscic_action_required = models.TextField("বিসিকের করণীয়", blank=True)

    current_status = models.CharField(
        "মামলার বর্তমান অবস্থা",
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.ONGOING,
    )

    next_date = models.DateField("পরবর্তী তারিখ", null=True, blank=True)
    next_action = models.TextField("পরবর্তী করণীয়", blank=True)
    remarks = models.TextField("মন্তব্য", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-case_date", "-created_at"]
        verbose_name = "মামলার তথ্য"
        verbose_name_plural = "মামলার তথ্যসমূহ"

    def __str__(self):
        return f"{self.case_number} — {self.court_name}"


class LegalCaseDocument(models.Model):

    class DocumentType(models.TextChoices):
        CASE_PAPER = "case_paper", "মামলার কাগজপত্র"
        OTHER = "other", "অন্যান্য দলিল"

    legal_case = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="মামলা",
    )

    document_type = models.CharField(
        "দলিলের ধরন",
        max_length=20,
        choices=DocumentType.choices,
    )

    title = models.CharField(
        "দলিলের নাম",
        max_length=255,
        blank=True,
    )

    file = models.FileField(
        "ফাইল",
        upload_to="legal_cases/%Y/%m/",
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "মামলার দলিল"
        verbose_name_plural = "মামলার দলিলসমূহ"

    def __str__(self):
        return self.title or self.file.name
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class GreenerySetting(models.Model):
    """Superadmin কর্তৃক নির্ধারিত ভিত্তি তারিখ।"""

    estate = models.OneToOneField(
        IndustrialEstate,
        on_delete=models.PROTECT,
        related_name="greenery_setting",
        verbose_name="শিল্পনগরী",
    )

    base_date = models.DateField("তুলনার ভিত্তি তারিখ")

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="সর্বশেষ হালনাগাদকারী",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "সবুজায়নের ভিত্তি তারিখ"
        verbose_name_plural = "সবুজায়নের ভিত্তি তারিখসমূহ"

    def __str__(self):
        return f"{self.estate} — {self.base_date:%d-%m-%Y}"


class GreeneryReport(models.Model):
    """নির্দিষ্ট রিপোর্টের তারিখে সবুজায়নের অগ্রগতি।"""

    estate = models.ForeignKey(
        IndustrialEstate,
        on_delete=models.PROTECT,
        related_name="greenery_reports",
        verbose_name="শিল্পনগরী",
    )

    # রিপোর্ট জমা দেওয়ার সময়কার ভিত্তি তারিখ সংরক্ষণ
    base_date = models.DateField("তুলনার ভিত্তি তারিখ")

    report_date = models.DateField(
        "রিপোর্টের তারিখ",
        default=timezone.localdate,
    )

    suitable_land = models.DecimalField(
        "বৃক্ষরোপণের জন্য উপযুক্ত মোট জমি (শতক)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    trees_at_base_date = models.PositiveIntegerField(
        "ভিত্তি তারিখ পর্যন্ত রোপিত গাছের সংখ্যা",
    )

    vacant_land_at_base_date = models.DecimalField(
        "ভিত্তি তারিখে খালি উপযুক্ত জমি (শতক)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    plantable_trees = models.PositiveIntegerField(
        "খালি জায়গায় রোপণযোগ্য গাছের সংখ্যা",
    )

    new_trees_planted = models.PositiveIntegerField(
        "ভিত্তি তারিখের পর নতুন রোপিত গাছের সংখ্যা",
    )

    newly_greenified_land = models.DecimalField(
        "নতুন সবুজায়নকৃত জমি (শতক)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    greenery_initiatives = models.TextField(
        "অবশিষ্ট জমিতে বৃক্ষরোপণের উদ্যোগ",
        blank=True,
    )

    comments = models.TextField("মন্তব্য", blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="greenery_reports",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-report_date", "-created_at"]
        verbose_name = "সবুজায়নের রিপোর্ট"
        verbose_name_plural = "সবুজায়নের রিপোর্টসমূহ"

    @property
    def greenery_rate(self):
        if self.vacant_land_at_base_date <= 0:
            return Decimal("0.00")

        return (
            self.newly_greenified_land
            / self.vacant_land_at_base_date
            * Decimal("100")
        ).quantize(Decimal("0.01"))

    def __str__(self):
        return f"{self.estate} — {self.report_date:%d-%m-%Y}"


class GreeneryReportImage(models.Model):
    """একটি রিপোর্টের একাধিক ছবি।"""

    report = models.ForeignKey(
        GreeneryReport,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(
        "বৃক্ষরোপণের ছবি",
        upload_to="greenery/%Y/%m/",
    )

    photo_date = models.DateField(
        "ছবির তারিখ",
        null=True,
        blank=True,
    )

    caption = models.CharField(
        "ছবির বিবরণ",
        max_length=255,
        blank=True,
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-photo_date", "-uploaded_at"]
        verbose_name = "সবুজায়নের ছবি"
        verbose_name_plural = "সবুজায়নের ছবিসমূহ"
# =========================================================
# Page 6: KPI-ভুক্ত প্রতিষ্ঠান
# =========================================================

class KPIInstitution(models.Model):
    class KPIType(models.TextChoices):
        STRATEGIC = "strategic", "কৌশলগত"
        SECURITY = "security", "নিরাপত্তা"
        GOVERNMENT = "government", "সরকারি গুরুত্বপূর্ণ প্রতিষ্ঠান"
        OTHER = "other", "অন্যান্য"

    class CurrentStatus(models.TextChoices):
        ACTIVE = "active", "সচল"
        INACTIVE = "inactive", "নিষ্ক্রিয়"
        UNDER_REVIEW = "under_review", "পর্যালোচনাধীন"
        OTHER = "other", "অন্যান্য"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="kpi_institutions", verbose_name="শিল্পনগরী"
    )
    institution_name = models.CharField("প্রতিষ্ঠানের নাম", max_length=255)
    kpi_type = models.CharField(
        "KPI-ভুক্তির ধরন/শ্রেণি", max_length=30, choices=KPIType.choices
    )
    kpi_date = models.DateField("KPI-ভুক্তির তারিখ")
    plot = models.ForeignKey(
        Plot, on_delete=models.PROTECT,
        related_name="kpi_institutions", verbose_name="প্রতিষ্ঠানের প্লট নম্বর"
    )
    lessee_name = models.CharField("ইজারা গ্রহিতার নাম", max_length=255)
    contact_info = models.CharField("যোগাযোগের তথ্য", max_length=100)
    approval_pdf = models.FileField(
        "KPI-ভুক্তির আদেশ/অনুমোদন",
        upload_to="kpi_institutions/approvals/"
    )
    current_status = models.CharField(
        "বর্তমান অবস্থা", max_length=20,
        choices=CurrentStatus.choices, default=CurrentStatus.ACTIVE
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estate__name", "institution_name"]
        verbose_name = "KPI-ভুক্ত প্রতিষ্ঠান"
        verbose_name_plural = "KPI-ভুক্ত প্রতিষ্ঠানসমূহ"

    def clean(self):
        if self.plot_id and self.estate_id:
            if self.plot.estate_id != self.estate_id:
                raise ValidationError({
                    "plot": "নির্বাচিত প্লটটি এই শিল্পনগরীর নয়।"
                })

    def __str__(self):
        return self.institution_name


# =========================================================
# Page 7: Street Light
# =========================================================

class StreetLightRecord(models.Model):
    class SupervisingOrganization(models.TextChoices):
        BSCIC = "bscic", "বিসিক"
        MUNICIPALITY = "municipality", "পৌরসভা"
        OTHER = "other", "অন্যান্য"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="street_light_records", verbose_name="শিল্পনগরী"
    )
    has_street_lights = models.BooleanField("স্ট্রিট লাইট আছে কি না", default=False)
    total_lights = models.PositiveIntegerField("মোট স্ট্রিট লাইটের সংখ্যা", default=0)
    working_lights = models.PositiveIntegerField("সচল লাইটের সংখ্যা", default=0)
    broken_lights = models.PositiveIntegerField("অচল লাইটের সংখ্যা", default=0)
    supervising_organization = models.CharField(
        "তদারকিকারী প্রতিষ্ঠান",
        max_length=20,
        choices=SupervisingOrganization.choices,
        default=SupervisingOrganization.BSCIC,
    )
    supervising_organization_other = models.CharField(
        "অন্যান্য তদারকিকারী প্রতিষ্ঠান", max_length=255, blank=True
    )
    last_inspection_date = models.DateField(
        "সর্বশেষ পরিদর্শনের তারিখ", null=True, blank=True
    )
    repair_installation_needs = models.TextField(
        "মেরামত বা স্থাপনের প্রয়োজনীয়তা", blank=True
    )
    photo = models.ImageField(
        "ছবি", upload_to="street_lights/", null=True, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)
    report_date = models.DateField("তথ্যের তারিখ", default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-report_date", "-created_at"]
        verbose_name = "স্ট্রিট লাইটের তথ্য"
        verbose_name_plural = "স্ট্রিট লাইটের তথ্যসমূহ"

    def clean(self):
        errors = {}
        if self.working_lights + self.broken_lights > self.total_lights:
            errors["broken_lights"] = (
                "সচল ও অচল লাইটের যোগফল মোট লাইটের বেশি হতে পারবে না।"
            )
        if not self.has_street_lights and (
            self.total_lights or self.working_lights or self.broken_lights
        ):
            errors["total_lights"] = (
                "স্ট্রিট লাইট না থাকলে লাইটের সংখ্যা শূন্য হতে হবে।"
            )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.estate} — {self.report_date}"


# =========================================================
# Page 8.1: Water Supply
# =========================================================

class WaterSupplyRecord(models.Model):
    class WaterSource(models.TextChoices):
        GROUNDWATER = "groundwater", "ভূগর্ভস্থ পানি"
        SURFACE = "surface", "ভূপৃষ্ঠের পানি"
        MUNICIPAL = "municipal", "পৌর/ওয়াসা সরবরাহ"
        OTHER = "other", "অন্যান্য"

    class SupplyStatus(models.TextChoices):
        NORMAL = "normal", "স্বাভাবিক"
        PARTIAL = "partial", "আংশিক সচল"
        INTERRUPTED = "interrupted", "বিঘ্নিত"
        STOPPED = "stopped", "বন্ধ"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="water_supply_records", verbose_name="শিল্পনগরী"
    )
    has_water_supply = models.BooleanField("পানি সরবরাহ ব্যবস্থা আছে কি না", default=False)
    supplier_name = models.CharField("সরবরাহকারী প্রতিষ্ঠান", max_length=255, blank=True)
    water_source = models.CharField(
        "পানি সরবরাহের উৎস", max_length=20,
        choices=WaterSource.choices, blank=True
    )
    monthly_quantity = models.DecimalField(
        "মাসিক সরবরাহের পরিমাণ", max_digits=14, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0"))]
    )
    quantity_unit = models.CharField(
        "পরিমাণের একক", max_length=30, blank=True,
        help_text="যেমন: ঘনমিটার, লিটার"
    )
    connection_count = models.PositiveIntegerField("পানির সংযোগের সংখ্যা", default=0)
    supply_status = models.CharField(
        "সরবরাহ ব্যবস্থার বর্তমান অবস্থা",
        max_length=20, choices=SupplyStatus.choices, blank=True
    )
    supply_problems = models.TextField("পানি সরবরাহের সমস্যা", blank=True)
    last_updated_date = models.DateField("সর্বশেষ হালনাগাদের তারিখ", default=timezone.localdate)
    attachment = models.FileField(
        "সংযুক্তি", upload_to="utilities/water/", null=True, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_updated_date", "-created_at"]
        verbose_name = "পানি সরবরাহের তথ্য"
        verbose_name_plural = "পানি সরবরাহের তথ্যসমূহ"

    def __str__(self):
        return f"{self.estate} — পানি"


# =========================================================
# Page 8.2: Electricity
# =========================================================

class ElectricityRecord(models.Model):
    class Supplier(models.TextChoices):
        PDB = "pdb", "পিডিবি"
        RURAL_ELECTRICITY = "rural_electricity", "পল্লী বিদ্যুৎ"
        OTHER = "other", "অন্যান্য"

    class SupplyStatus(models.TextChoices):
        NORMAL = "normal", "স্বাভাবিক"
        PARTIAL = "partial", "আংশিক সচল"
        STOPPED = "stopped", "বন্ধ"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="electricity_records", verbose_name="শিল্পনগরী"
    )
    has_electricity = models.BooleanField("বিদ্যুৎ সংযোগ আছে কি না", default=False)
    supplier = models.CharField(
        "বিদ্যুৎ সরবরাহকারী প্রতিষ্ঠান", max_length=30,
        choices=Supplier.choices, blank=True
    )
    supplier_other = models.CharField("অন্যান্য সরবরাহকারী", max_length=255, blank=True)
    connected_unit_count = models.PositiveIntegerField(
        "সংযুক্ত শিল্প ইউনিটের সংখ্যা", default=0
    )
    approved_load = models.DecimalField(
        "অনুমোদিত লোড", max_digits=14, decimal_places=3,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0"))]
    )
    approved_load_unit = models.CharField(
        "অনুমোদিত লোডের একক", max_length=10, blank=True,
        help_text="kW অথবা MW"
    )
    supply_status = models.CharField(
        "বিদ্যুৎ সরবরাহের বর্তমান অবস্থা", max_length=20,
        choices=SupplyStatus.choices, blank=True
    )
    supply_problems = models.TextField("বিদ্যুৎ বিভ্রাট/সরবরাহ সমস্যা", blank=True)
    last_updated_date = models.DateField("তথ্য হালনাগাদের তারিখ", default=timezone.localdate)
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_updated_date", "-created_at"]
        verbose_name = "বিদ্যুৎ সরবরাহের তথ্য"
        verbose_name_plural = "বিদ্যুৎ সরবরাহের তথ্যসমূহ"

    def __str__(self):
        return f"{self.estate} — বিদ্যুৎ"


# =========================================================
# Page 8.3: Gas
# =========================================================

class GasSupplyRecord(models.Model):
    class SupplyType(models.TextChoices):
        PIPELINE = "pipeline", "পাইপলাইন"
        CYLINDER = "cylinder", "সিলিন্ডার"
        OTHER = "other", "অন্যান্য"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="gas_supply_records", verbose_name="শিল্পনগরী"
    )
    has_gas_supply = models.BooleanField("গ্যাস সরবরাহ আছে কি না", default=False)
    supplier_name = models.CharField("সরবরাহকারী প্রতিষ্ঠান", max_length=255, blank=True)
    connected_unit_count = models.PositiveIntegerField(
        "গ্যাস সংযোগপ্রাপ্ত শিল্প ইউনিটের সংখ্যা", default=0
    )
    supply_type = models.CharField(
        "সরবরাহের ধরন", max_length=20, choices=SupplyType.choices, blank=True
    )
    supply_problems = models.TextField("গ্যাস সরবরাহের সমস্যা", blank=True)
    last_updated_date = models.DateField("সর্বশেষ হালনাগাদের তারিখ", default=timezone.localdate)
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_updated_date", "-created_at"]
        verbose_name = "গ্যাস সরবরাহের তথ্য"
        verbose_name_plural = "গ্যাস সরবরাহের তথ্যসমূহ"

    def __str__(self):
        return f"{self.estate} — গ্যাস"


# =========================================================
# Page 9: Ponds
# =========================================================

class PondRecord(models.Model):
    class LeaseCollectionStatus(models.TextChoices):
        PAID = "paid", "সম্পূর্ণ আদায়"
        PARTIAL = "partial", "আংশিক আদায়"
        DUE = "due", "বকেয়া"
        NOT_APPLICABLE = "not_applicable", "প্রযোজ্য নয়"

    estate = models.ForeignKey(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="pond_records", verbose_name="শিল্পনগরী"
    )
    pond_name = models.CharField("পুকুরের নাম/শনাক্তকরণ নম্বর", max_length=255)
    pond_count = models.PositiveIntegerField("পুকুরের সংখ্যা", default=1)
    pond_area = models.DecimalField(
        "পুকুরের আয়তন", max_digits=14, decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))]
    )
    area_unit = models.CharField(
        "আয়তনের একক", max_length=30, default="শতক",
        help_text="যেমন: শতক, একর, বর্গমিটার"
    )
    is_leased = models.BooleanField("পুকুর ইজারা দেওয়া হয়েছে কি না", default=False)
    lessee_name = models.CharField("ইজারাগ্রহীতার নাম", max_length=255, blank=True)
    lease_start_date = models.DateField("ইজারা শুরুর তারিখ", null=True, blank=True)
    lease_end_date = models.DateField("ইজারার মেয়াদ শেষের তারিখ", null=True, blank=True)
    lease_amount = models.DecimalField(
        "ইজারামূল্য", max_digits=14, decimal_places=2,
        null=True, blank=True, validators=[MinValueValidator(Decimal("0"))]
    )
    amount_collected = models.DecimalField(
        "ইজারার মাধ্যমে এ পর্যন্ত আদায়কৃত অর্থ",
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))]
    )
    collection_status = models.CharField(
        "ইজারার অর্থ আদায়ের অবস্থা", max_length=20,
        choices=LeaseCollectionStatus.choices,
        default=LeaseCollectionStatus.NOT_APPLICABLE
    )
    lease_agreement = models.FileField(
        "ইজারার চুক্তিপত্র (PDF)", upload_to="ponds/lease_agreements/",
        null=True, blank=True
    )
    repair_leaseable_count = models.PositiveIntegerField(
        "সংস্কারপূর্বক লিজযোগ্য পুকুরের সংখ্যা", default=0
    )
    unleaseable_count = models.PositiveIntegerField(
        "লিজ অযোগ্য পুকুরের সংখ্যা", default=0
    )
    photo = models.ImageField(
        "পুকুরের ছবি", upload_to="ponds/photos/", null=True, blank=True
    )
    comments = models.TextField("মন্তব্য", blank=True)
    report_date = models.DateField("তথ্যের তারিখ", default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["estate__name", "pond_name"]
        verbose_name = "পুকুরের তথ্য"
        verbose_name_plural = "পুকুরের তথ্যসমূহ"

    def clean(self):
        if self.is_leased:
            errors = {}
            if not self.lessee_name:
                errors["lessee_name"] = "ইজারাগ্রহীতার নাম আবশ্যক।"
            if self.lease_start_date and self.lease_end_date:
                if self.lease_end_date < self.lease_start_date:
                    errors["lease_end_date"] = "শেষের তারিখ শুরুর তারিখের আগে হতে পারবে না।"
            if errors:
                raise ValidationError(errors)

    def __str__(self):
        return f"{self.estate} — {self.pond_name}"


# =========================================================
# Page 10: Purpose of Industrial Estate
# =========================================================

class EstatePurposeRecord(models.Model):
    estate = models.OneToOneField(
        IndustrialEstate, on_delete=models.PROTECT,
        related_name="purpose_record", verbose_name="শিল্পনগরী"
    )
    main_purpose = models.TextField("স্থাপনের মূল উদ্দেশ্য")
    future_plan = models.TextField("ভবিষ্যৎ পরিকল্পনা", blank=True)
    comments = models.TextField("মন্তব্য", blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="updated_estate_purposes"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "শিল্পনগরী স্থাপনের উদ্দেশ্য"
        verbose_name_plural = "শিল্পনগরী স্থাপনের উদ্দেশ্যসমূহ"

    def __str__(self):
        return f"{self.estate} — স্থাপনের উদ্দেশ্য"