
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["estate__name", "name"]
        verbose_name = "শিল্প ইউনিট"
        verbose_name_plural = "শিল্প ইউনিটসমূহ"

    def __str__(self):
        return f"{self.name} ({self.unit_code})"

    @property
    def total_employment(self):
        latest = self.employment_records.order_by(
            "-year", "-month", "-created_at"
        ).first()
        if latest:
            return latest.total_employment
        return 0

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
# 5. One plot can be allocated wholly or partly to a unit
# =========================================================

class UnitPlotAllocation(models.Model):
    class AllocationType(models.TextChoices):
        FULL = "full", "পূর্ণ"
        PARTIAL = "partial", "অংশ"

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
    )
    year = models.PositiveIntegerField("বছর")
    month = models.PositiveSmallIntegerField("মাস")
    male_workers = models.PositiveIntegerField("পুরুষ কর্মী", default=0)
    female_workers = models.PositiveIntegerField("নারী কর্মী", default=0)
    third_gender_workers = models.PositiveIntegerField(
        "তৃতীয় লিঙ্গের কর্মী", default=0
    )
    temporary_workers = models.PositiveIntegerField(
        "অস্থায়ী কর্মী", default=0
    )
    comments = models.TextField("মন্তব্য", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
        return f"{self.industrial_unit} — {self.month}/{self.year}"

    @property
    def total_employment(self):
        return (
            self.male_workers
            + self.female_workers
            + self.third_gender_workers
            + self.temporary_workers
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
        return MonthlyPayment.objects.filter(
            account__industrial_unit=self.industrial_unit,
            account__fiscal_year=self.fiscal_year,
            account__month__lte=self.month,
        ).aggregate(total=Sum("amount"))["total"] or ZERO

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
    class AppealStatus(models.TextChoices):
        PENDING = "pending", "বিবেচনাধীন"
        APPROVED = "approved", "অনুমোদিত"
        REJECTED = "rejected", "নাকচ"
        WITHDRAWN = "withdrawn", "প্রত্যাহার"
        OTHER = "other", "অন্যান্য"

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
