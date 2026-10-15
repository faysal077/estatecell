# from django.contrib import admin

# from .models import (
#     RegionalOffice,
#     District,
#     Upazila,
#     IndustrialEstate,
#     EstateLayoutRevisionDocument,
#     Plot,
# )


# @admin.register(RegionalOffice)
# class RegionalOfficeAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)


# @admin.register(District)
# class DistrictAdmin(admin.ModelAdmin):
#     list_display = ("name",)
#     search_fields = ("name",)


# @admin.register(Upazila)
# class UpazilaAdmin(admin.ModelAdmin):
#     list_display = ("name", "district")
#     list_filter = ("district",)
#     search_fields = ("name", "district__name")


# class LayoutRevisionInline(admin.TabularInline):
#     model = EstateLayoutRevisionDocument
#     extra = 0


# @admin.register(IndustrialEstate)
# class IndustrialEstateAdmin(admin.ModelAdmin):
#     list_display = (
#         "name",
#         "regional_office",
#         "district",
#         "upazila",
#         "established_year",
#         "total_land_acre",
#         "allocatable_land_acre",
#         "layout_approved",
#     )
#     list_filter = (
#         "regional_office",
#         "district",
#         "layout_approved",
#         "layout_revised",
#     )
#     search_fields = (
#         "name",
#         "district__name",
#         "rd_office__name",
#         "officer_name",
#     )
#     readonly_fields = ("created_at", "updated_at")
#     inlines = (LayoutRevisionInline,)


# @admin.register(Plot)
# class PlotAdmin(admin.ModelAdmin):
#     list_display = (
#         "plot_number",
#         "estate",
#         "area_acre",
#         "current_status",
#     )
#     list_filter = ("estate", "current_status")
#     search_fields = ("plot_number", "estate__name")


# @admin.register(EstateLayoutRevisionDocument)
# class EstateLayoutRevisionDocumentAdmin(admin.ModelAdmin):
#     list_display = (
#         "estate",
#         "title",
#         "approval_date",
#         "uploaded_at",
#     )
#     list_filter = ("estate",)
#     search_fields = ("estate__name", "title")

from django.core.serializers import python
from django.contrib import admin

from .models import (
    RegionalOffice,
    District,
    Upazila,
    IndustrialEstate,
    EstateLayoutRevisionDocument,
    Plot,
    IndustrialUnit,
    UnitPlotAllocation,
    UnitProduct,
    EmploymentHistory,
    MonthlyReceivable,
    MonthlyPayment,
    BankLoan,
    BankLoanDocument,
    UnitTransfer,
    PlotCancellationAppeal,
    ExportProduct,
    EnvironmentalData,
    UtilityUsage,
)


# =========================================================
# Inlines
# =========================================================

class EstateLayoutRevisionDocumentInline(admin.TabularInline):
    model = EstateLayoutRevisionDocument
    extra = 0


class UnitPlotAllocationInline(admin.TabularInline):
    model = UnitPlotAllocation
    extra = 0
    autocomplete_fields = ["plot"]


class UnitProductInline(admin.TabularInline):
    model = UnitProduct
    extra = 0


class EmploymentHistoryInline(admin.TabularInline):
    model = EmploymentHistory
    extra = 0
    ordering = ["-year", "-month"]


class MonthlyPaymentInline(admin.TabularInline):
    model = MonthlyPayment
    extra = 0


class BankLoanDocumentInline(admin.TabularInline):
    model = BankLoanDocument
    extra = 0


class UtilityUsageInline(admin.TabularInline):
    model = UtilityUsage
    extra = 0


class ExportProductInline(admin.TabularInline):
    model = ExportProduct
    extra = 0


class UnitTransferInline(admin.TabularInline):
    model = UnitTransfer
    extra = 0


# =========================================================
# Reference data
# =========================================================

@admin.register(RegionalOffice)
class RegionalOfficeAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Upazila)
class UpazilaAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "district"]
    list_filter = ["district"]
    search_fields = ["name", "district__name"]
    autocomplete_fields = ["district"]


# =========================================================
# Industrial estates
# =========================================================

@admin.register(IndustrialEstate)
class IndustrialEstateAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "regional_office",
        "district",
        "upazila",
        "established_year",
        "layout_approved",
        "layout_revised",
    ]

    list_filter = [
        "regional_office",
        "district",
        "layout_approved",
        "layout_revised",
    ]

    search_fields = [
        "name",
        "regional_office__name",
        "district__name",
        "upazila__name",
    ]

    autocomplete_fields = [
        "regional_office",
        "district",
        "upazila",
        "created_by",
    ]

    readonly_fields = ["created_at", "updated_at"]

    inlines = [EstateLayoutRevisionDocumentInline]

    fieldsets = [
        (
            "সাধারণ তথ্য",
            {
                "fields": (
                    "regional_office",
                    "district",
                    "upazila",
                    "name",
                    "officer_name",
                    "officer_designation",
                    "officer_mobile",
                    "established_year",
                )
            },
        ),
        (
            "জমির তথ্য",
            {
                "fields": (
                    "total_land_acre",
                    "allocatable_land_acre",
                )
            },
        ),
        (
            "লে-আউট সংক্রান্ত তথ্য",
            {
                "fields": (
                    "layout_approved",
                    "layout_approval_date",
                    "layout_file",
                    "layout_revised",
                    "layout_revision_date",
                )
            },
        ),
        (
            "অন্যান্য",
            {
                "fields": (
                    "establishment_purpose",
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    ]


# =========================================================
# Plots
# =========================================================

@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "estate",
        "plot_number",
        "area_sqft",
        "current_status",
        "plot_type",
        "allocation_date",
        "has_lease_deed",
    ]

    list_filter = [
        "estate",
        "current_status",
        "plot_type",
        "has_lease_deed",
    ]

    search_fields = [
        "plot_number",
        "estate__name",
        "lessee_name",
    ]

    autocomplete_fields = ["estate"]

    readonly_fields = ["created_at", "updated_at"]


# =========================================================
# Industrial units
# =========================================================

@admin.register(IndustrialUnit)
class IndustrialUnitAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "unit_code",
        "estate",
        "owner_name",
        "industry_size",
        "operational_status",
        "employment_count",
        "is_export_oriented",
    ]

    list_filter = [
        "estate",
        "ownership_type",
        "industry_size",
        "operational_status",
        "has_floor_rental",
        "is_export_oriented",
    ]

    search_fields = [
        "name",
        "unit_code",
        "owner_name",
        "owner_phone",
        "representative_name",
        "estate__name",
    ]

    autocomplete_fields = ["estate"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "employment_count",
        "allocated_area",
        "rental_duration",
    ]

    inlines = [
        UnitPlotAllocationInline,
        UnitProductInline,
        EmploymentHistoryInline,
        UnitTransferInline,
        ExportProductInline,
    ]

    fieldsets = [
        (
            "সাধারণ পরিচিতি",
            {
                "fields": (
                    "estate",
                    "name",
                    "unit_code",
                    "owner_name",
                    "owner_phone",
                    "representative_name",
                    "representative_phone",
                    "ownership_type",
                    "industry_size",
                    "production_sector",
                    "production_sector_other",
                    "production_subsector",
                    "comments",
                )
            },
        ),
        (
            "কারখানা ও উৎপাদন",
            {
                "fields": (
                    "factory_layout_approval_date",
                    "factory_layout_plan",
                    "production_start_date",
                )
            },
        ),
        (
            "সচলতা ও কর্মসংস্থান",
            {
                "fields": (
                    "operational_status",
                    "sick_closed_date",
                    "sick_closed_reason",
                    "office_action",
                    "employment_count",
                )
            },
        ),
        (
            "ফ্লোর স্পেস ভাড়া",
            {
                "fields": (
                    "has_floor_rental",
                    "tenant_name",
                    "rental_start_date",
                    "rental_end_date",
                    "rental_duration",
                    "annual_rent_received",
                    "rental_agreement",
                    "rental_comments",
                )
            },
        ),
        (
            "অন্যান্য",
            {
                "fields": (
                    "is_export_oriented",
                    "allocated_area",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    ]

    @admin.display(description="মোট কর্মসংস্থান")
    def employment_count(self, obj):
        return obj.total_employment

    @admin.display(description="বরাদ্দকৃত আয়তন (বর্গফুট)")
    def allocated_area(self, obj):
        return obj.total_allocated_area_sqft

    @admin.display(description="ভাড়ার মেয়াদ (মাস)")
    def rental_duration(self, obj):
        return obj.rental_duration_months


# =========================================================
# Monthly financial accounts
# =========================================================

@admin.register(MonthlyReceivable)
class MonthlyReceivableAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "fiscal_year",
        "month",
        "previous_balance",
        "current_month_due",
        "total_payable_display",
        "total_collected_display",
        "balance_display",
    ]

    list_filter = [
        "fiscal_year",
        "month",
        "industrial_unit__estate",
    ]

    search_fields = [
        "industrial_unit__name",
        "industrial_unit__unit_code",
        "industrial_unit__estate__name",
    ]

    autocomplete_fields = ["industrial_unit"]

    readonly_fields = [
        "current_month_due",
        "total_payable_display",
        "total_collected_display",
        "balance_display",
        "collection_percentage",
    ]

    inlines = [MonthlyPaymentInline]

    @admin.display(description="চলতি মাসের পাওনা")
    def current_month_due(self, obj):
        return obj.current_month_new_due

    @admin.display(description="মোট প্রাপ্য")
    def total_payable_display(self, obj):
        return obj.total_payable

    @admin.display(description="মোট আদায়")
    def total_collected_display(self, obj):
        return obj.total_collected

    @admin.display(description="অবশিষ্ট বকেয়া")
    def balance_display(self, obj):
        return obj.outstanding_balance

    @admin.display(description="আদায়ের হার (%)")
    def collection_percentage(self, obj):
        return obj.monthly_collection_percentage


@admin.register(MonthlyPayment)
class MonthlyPaymentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "account",
        "payment_date",
        "amount",
        "receipt_number",
    ]

    list_filter = ["payment_date"]

    search_fields = [
        "receipt_number",
        "account__industrial_unit__name",
        "account__industrial_unit__unit_code",
    ]

    autocomplete_fields = ["account"]


# =========================================================
# Bank loans and documents
# =========================================================

@admin.register(BankLoan)
class BankLoanAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "bank_name",
        "loan_amount",
        "loan_date",
        "noc_date",
        "status",
    ]

    list_filter = ["status", "bank_name"]

    search_fields = [
        "bank_name",
        "industrial_unit__name",
        "industrial_unit__unit_code",
    ]

    autocomplete_fields = ["industrial_unit"]

    inlines = [BankLoanDocumentInline]


@admin.register(BankLoanDocument)
class BankLoanDocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "loan", "title", "uploaded_at"]
    search_fields = ["title", "loan__bank_name"]
    autocomplete_fields = ["loan"]


# =========================================================
# Transfers and cancellation appeals
# =========================================================

@admin.register(UnitTransfer)
class UnitTransferAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "transfer_date",
        "from_company",
        "to_company",
    ]

    list_filter = ["transfer_date"]

    search_fields = [
        "industrial_unit__name",
        "from_company",
        "to_company",
    ]

    autocomplete_fields = ["industrial_unit"]


@admin.register(PlotCancellationAppeal)
class PlotCancellationAppealAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "plot",
        "industrial_unit",
        "cancellation_date",
        "appeal_filed",
        "latest_status",
    ]

    list_filter = [
        "appeal_filed",
        "latest_status",
        "cancellation_date",
    ]

    search_fields = [
        "plot__plot_number",
        "industrial_unit__name",
        "industrial_unit__unit_code",
    ]

    autocomplete_fields = ["plot", "industrial_unit"]


# =========================================================
# Environmental and utility information
# =========================================================

@admin.register(EnvironmentalData)
class EnvironmentalDataAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "has_solar_panel",
        "needs_liquid_waste_treatment",
        "has_etp",
        "waste_goes_to_city_drain",
    ]

    list_filter = [
        "has_solar_panel",
        "needs_liquid_waste_treatment",
        "has_etp",
        "has_own_liquid_waste_management",
        "waste_goes_to_city_drain",
    ]

    search_fields = [
        "industrial_unit__name",
        "industrial_unit__unit_code",
    ]

    autocomplete_fields = ["industrial_unit"]

    inlines = [UtilityUsageInline]


@admin.register(UtilityUsage)
class UtilityUsageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "environmental_data",
        "utility_type",
        "period_type",
        "year",
        "month",
        "quantity",
        "quantity_unit",
        "bill_amount",
    ]

    list_filter = [
        "utility_type",
        "period_type",
        "year",
    ]

    search_fields = [
        "environmental_data__industrial_unit__name",
        "environmental_data__industrial_unit__unit_code",
    ]

    autocomplete_fields = ["environmental_data"]


# =========================================================
# Remaining models
# =========================================================

@admin.register(UnitPlotAllocation)
class UnitPlotAllocationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "plot",
        "allocation_type",
        "allocated_area_sqft",
        "allocation_date",
        "possession_date",
    ]

    list_filter = [
        "allocation_type",
        "plot__estate",
    ]

    search_fields = [
        "industrial_unit__name",
        "industrial_unit__unit_code",
        "plot__plot_number",
    ]

    autocomplete_fields = ["industrial_unit", "plot"]


@admin.register(UnitProduct)
class UnitProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "name",
        "production_sector",
        "production_subsector",
    ]

    search_fields = [
        "name",
        "industrial_unit__name",
        "industrial_unit__unit_code",
    ]

    autocomplete_fields = ["industrial_unit"]


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "year",
        "month",
        "male_workers",
        "female_workers",
        "third_gender_workers",
        "temporary_workers",
        "total_workers",
    ]

    list_filter = ["year", "month"]

    search_fields = [
        "industrial_unit__name",
        "industrial_unit__unit_code",
    ]

    autocomplete_fields = ["industrial_unit"]

    @admin.display(description="মোট কর্মী")
    def total_workers(self, obj):
        return obj.total_employment


@admin.register(ExportProduct)
class ExportProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "industrial_unit",
        "product_name",
        "importing_country",
    ]

    search_fields = [
        "product_name",
        "importing_country",
        "industrial_unit__name",
    ]

    autocomplete_fields = ["industrial_unit"]
