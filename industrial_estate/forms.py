from django import forms
from .models import IndustrialUnit, UnitProduct
from django import forms
from django.core.exceptions import ValidationError
from django import forms
from esate_db.districts import DISTRICT_CHOICES_WITH_BN

from .models import District, Upazila
from esate_db.districts import (
    DISTRICT_CHOICES_WITH_BN,
    DIVISION_NAMES,
)

from .models import (
    RegionalOffice,
    District,
    Upazila,
    IndustrialEstate,
)
from .models import District, Upazila, IndustrialEstate
from esate_db.districts import (
    DIVISION_CHOICES_WITH_BN,
    DIVISION_DISTRICT_MAP,
    get_division_by_district,
)
from django.core.exceptions import PermissionDenied

from accounts.models import UserRole
from .models import (
    IndustrialEstate,
    IndustrialUnit,
    Plot,
    MonthlyReceivable,
    BankLoan,
    EnvironmentalData,
)
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
RD_OFFICE_CHOICES = [
    ("", "--------- আঞ্চলিক কার্যালয় নির্বাচন করুন ---------"),
    (
        "বিসিক আঞ্চলিক কার্যালয়, ঢাকা",
        "বিসিক আঞ্চলিক কার্যালয়, ঢাকা",
    ),
    (
        "বিসিক আঞ্চলিক কার্যালয়, চট্টগ্রাম",
        "বিসিক আঞ্চলিক কার্যালয়, চট্টগ্রাম",
    ),
    (
        "বিসিক আঞ্চলিক কার্যালয়, খুলনা",
        "বিসিক আঞ্চলিক কার্যালয়, খুলনা",
    ),
    (
        "বিসিক আঞ্চলিক কার্যালয়, রাজশাহী",
        "বিসিক আঞ্চলিক কার্যালয়, রাজশাহী",
    ),
]


class EstateScopedFormMixin:
    """
    Restrict related model choices to the current user's estate scope.
    Set self.user before calling this mixin's __init__.
    """

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if self.user is None:
            return

        estates = IndustrialEstate.objects.filter(
            pk__in=get_accessible_estates(self.user).values("pk")
        )

        profile = self.user.userprofile
        role = profile.role

        # Estate Officer must not select a different estate.
        if "estate" in self.fields:
            self.fields["estate"].queryset = estates

            if role == UserRole.ESTATE_OFFICER:
                if not profile.assigned_estate_id:
                    self.fields["estate"].queryset = (
                        IndustrialEstate.objects.none()
                    )
                else:
                    self.fields["estate"].initial = (
                        profile.assigned_estate_id
                    )

        # Industrial units are scoped through their estate.
        if "industrial_unit" in self.fields:
            self.fields["industrial_unit"].queryset = (
                IndustrialUnit.objects.filter(estate__in=estates)
            )

        if "plot" in self.fields:
            self.fields["plot"].queryset = Plot.objects.filter(
                estate__in=estates
            )

        if "account" in self.fields:
            self.fields["account"].queryset = (
                MonthlyReceivable.objects.filter(
                    industrial_unit__estate__in=estates
                )
            )

        if "loan" in self.fields:
            self.fields["loan"].queryset = BankLoan.objects.filter(
                industrial_unit__estate__in=estates
            )

        if "environmental_data" in self.fields:
            self.fields["environmental_data"].queryset = (
                EnvironmentalData.objects.filter(
                    industrial_unit__estate__in=estates
                )
            )

        # Regional Office selection is restricted for RD_ADMIN.
        office_field = (
            "regional_office"
            if "regional_office" in self.fields
            else "rd_office"
            if "rd_office" in self.fields
            else None
        )

        if office_field and role == UserRole.RD_ADMIN:
            if profile.assigned_regional_office_id:
                self.fields[office_field].queryset = (
                    self.fields[office_field].queryset.filter(
                        pk=profile.assigned_regional_office_id
                    )
                )
            else:
                self.fields[office_field].queryset = (
                    self.fields[office_field].queryset.none()
                )
class BootstrapModelForm(forms.ModelForm):
    """Apply Bootstrap styling to model forms."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault(
                    "class", "form-check-input"
                )
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault(
                    "class", "form-select"
                )
            else:
                field.widget.attrs.setdefault(
                    "class", "form-control"
                )


class PDFValidationMixin:
    """Validate uploaded files by extension."""

    pdf_fields = ()

    def clean(self):
        cleaned = super().clean()

        for field_name in self.pdf_fields:
            uploaded = cleaned.get(field_name)

            if uploaded and not uploaded.name.lower().endswith(".pdf"):
                self.add_error(
                    field_name,
                    "শুধুমাত্র PDF ফাইল গ্রহণযোগ্য।",
                )

        return cleaned


class IndustrialEstateForm(forms.ModelForm):

    regional_office = forms.ModelChoiceField(
        queryset=RegionalOffice.objects.order_by("name"),
        empty_label="--------- আঞ্চলিক কার্যালয় নির্বাচন করুন ---------",
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
        label="আঞ্চলিক কার্যালয়",
    )
  
    division = forms.ChoiceField(
        choices=[("", "--------- Select Division (বিভাগ নির্বাচন করুন) ---------")]
        + DIVISION_CHOICES_WITH_BN,
        required=True,
        label="বিভাগ (Division)",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_division",
        }),
    )

    district = forms.ModelChoiceField(
        queryset=District.objects.none(),
        required=True,
        empty_label="--------- Select District (জেলা নির্বাচন করুন) ---------",
        label="জেলা (District)",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_district",
        }),
    )

    upazila = forms.ModelChoiceField(
        queryset=Upazila.objects.none(),
        required=False,
        empty_label="--------- Select Upazila (উপজেলা নির্বাচন করুন) ---------",
        label="উপজেলা (Upazila)",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_upazila",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Division is a form-only field; it is not saved to the model.
        district_id = (
            self.data.get("district")
            or self.initial.get("district")
            or getattr(self.instance, "district_id", None)
        )

        division = (
            self.data.get("division")
            or self.initial.get("division")
        )

        # Keep the selected district valid during POST and edit.
        if district_id:
            self.fields["district"].queryset = (
                District.objects.all().order_by("name")
            )

            try:
                selected_district = District.objects.get(pk=district_id)

                if not division:
                    division = get_division_by_district(
                        selected_district.name
                    )

                self.fields["upazila"].queryset = (
                    Upazila.objects.filter(
                        district_id=selected_district.pk
                    ).order_by("name")
                )

            except (District.DoesNotExist, TypeError, ValueError):
                self.fields["upazila"].queryset = Upazila.objects.none()

        elif self.is_bound:
            # Allow Django to validate a submitted district ID.
            self.fields["district"].queryset = (
                District.objects.all().order_by("name")
            )

            if district_id and str(district_id).isdigit():
                self.fields["upazila"].queryset = (
                    Upazila.objects.filter(
                        district_id=int(district_id)
                    ).order_by("name")
                )

        else:
            # On a new form, districts are loaded after division selection.
            self.fields["district"].queryset = District.objects.none()
            self.fields["upazila"].queryset = Upazila.objects.none()

        if division:
            self.initial["division"] = division
    class Meta:
        model = IndustrialEstate
        fields = [
            "regional_office",
            "division",
            "district",
            "upazila",
            "name",
            "officer_name",
            "officer_designation",
            "officer_mobile",
            "established_year",
            "total_land_acre",
            "allocatable_land_acre",
            "layout_approved",
            "layout_approval_date",
            "layout_file",
            "layout_revised",
            "layout_revision_date",
            "establishment_purpose",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "officer_name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "officer_designation": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "officer_mobile": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "established_year": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "total_land_acre": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
            "allocatable_land_acre": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
            }),
            "layout_approved": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "layout_approval_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "layout_file": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": ".pdf,application/pdf",
            }),
            "layout_revised": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
            "layout_revision_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "establishment_purpose": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
        }
    def clean(self):
        cleaned_data = super().clean()

        total_land = cleaned_data.get("total_land_acre")
        allocatable_land = cleaned_data.get("allocatable_land_acre")

        if (
            total_land is not None
            and allocatable_land is not None
            and allocatable_land > total_land
        ):
            self.add_error(
                "allocatable_land_acre",
                "বরাদ্দযোগ্য জমি মোট জমির চেয়ে বেশি হতে পারবে না।",
            )

        district = cleaned_data.get("district")
        upazila = cleaned_data.get("upazila")

        if upazila and district and upazila.district_id != district.pk:
            self.add_error(
                "upazila",
                "নির্বাচিত উপজেলাটি নির্বাচিত জেলার অন্তর্ভুক্ত নয়।",
            )

        if (
            cleaned_data.get("layout_approved")
            and not cleaned_data.get("layout_approval_date")
        ):
            self.add_error(
                "layout_approval_date",
                "লেআউট অনুমোদিত হলে অনুমোদনের তারিখ দিতে হবে।",
            )

        if (
            cleaned_data.get("layout_revised")
            and not cleaned_data.get("layout_revision_date")
        ):
            self.add_error(
                "layout_revision_date",
                "লেআউট সংশোধিত হলে সংশোধনের তারিখ দিতে হবে।",
            )

        return cleaned_data
class EstateLayoutRevisionDocumentForm(
    BootstrapModelForm, PDFValidationMixin
):
    pdf_fields = ("file",)

    class Meta:
        model = EstateLayoutRevisionDocument
        fields = ["title", "file", "approval_date"]
        widgets = {
            "approval_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


class PlotForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = (
        "allocation_letter",
        "possession_letter",
        "appeal_document",
        "lease_deed",
    )

    class Meta:
        model = Plot
        fields = [
            "estate",
            "plot_number",
            "area_sqft",
            "area_acre",
            "plot_type",
            "current_status",
            "allocation_date",
            "allocation_letter",
            "possession_date",
            "possession_letter",
            "cancellation_date",
            "cancellation_reason",
            "appeal_details",
            "appeal_document",
            "has_lease_deed",
            "lease_deed_date",
            "lessee_name",
            "lease_deed",
            "comments",
        ]
        widgets = {
            "allocation_date": forms.DateInput(attrs={"type": "date"}),
            "possession_date": forms.DateInput(attrs={"type": "date"}),
            "cancellation_date": forms.DateInput(attrs={"type": "date"}),
            "lease_deed_date": forms.DateInput(attrs={"type": "date"}),
            "cancellation_reason": forms.Textarea(attrs={"rows": 3}),
            "appeal_details": forms.Textarea(attrs={"rows": 3}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }
    def __init__(
        self,
        *args,
        estate_queryset=None,
        fixed_estate_id=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if estate_queryset is not None:
            self.fields["estate"].queryset = estate_queryset

        if fixed_estate_id is not None:
            self.fields["estate"].initial = fixed_estate_id
            self.fields["estate"].disabled = True

class IndustrialUnitForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("factory_layout_plan", "rental_agreement")

    class Meta:
        model = IndustrialUnit
        fields = [
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
            "factory_layout_approval_date",
            "factory_layout_plan",
            "production_start_date",
            "operational_status",
            "sick_closed_date",
            "sick_closed_reason",
            "office_action",
            "has_floor_rental",
            "tenant_name",
            "rental_start_date",
            "rental_end_date",
            "annual_rent_received",
            "rental_agreement",
            "rental_comments",
            "is_export_oriented",
        ]
        widgets = {
            "factory_layout_approval_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "production_start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "sick_closed_date": forms.DateInput(attrs={"type": "date"}),
            "rental_start_date": forms.DateInput(attrs={"type": "date"}),
            "rental_end_date": forms.DateInput(attrs={"type": "date"}),
            "comments": forms.Textarea(attrs={"rows": 2}),
            "sick_closed_reason": forms.Textarea(attrs={"rows": 2}),
            "office_action": forms.Textarea(attrs={"rows": 2}),
            "rental_comments": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()

        if cleaned.get("has_floor_rental"):
            if (
                cleaned.get("rental_start_date")
                and cleaned.get("rental_end_date")
                and cleaned["rental_end_date"] < cleaned["rental_start_date"]
            ):
                self.add_error(
                    "rental_end_date",
                    "চুক্তি শেষের তারিখ শুরুর তারিখের আগে হতে পারবে না।",
                )

        return cleaned


class UnitPlotAllocationForm(BootstrapModelForm):
    class Meta:
        model = UnitPlotAllocation
        fields = [
            "industrial_unit",
            "plot",
            "allocation_type",
            "allocated_area_sqft",
            "allocation_date",
            "possession_date",
            "comments",
        ]
        widgets = {
            "allocation_date": forms.DateInput(attrs={"type": "date"}),
            "possession_date": forms.DateInput(attrs={"type": "date"}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }

class IndustrialUnitProductionForm(forms.ModelForm):
    class Meta:
        model = IndustrialUnit
        fields = [
            "factory_layout_approval_date",
            "factory_layout_plan",
            "production_start_date",
        ]
        widgets = {
            "factory_layout_approval_date": forms.DateInput(
                attrs={"type": "date"}
            ),
            "production_start_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }
class UnitProductForm(BootstrapModelForm):
    class Meta:
        model = UnitProduct
        fields = [
            "industrial_unit",
            "name",
            "production_sector",
            "production_subsector",
            "comments",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class EmploymentHistoryForm(BootstrapModelForm):
    class Meta:
        model = EmploymentHistory
        fields = [
            "industrial_unit",
            "year",
            "month",
            "male_workers",
            "female_workers",
            "third_gender_workers",
            "temporary_workers",
            "comments",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_month(self):
        month = self.cleaned_data["month"]

        if not 1 <= month <= 12:
            raise ValidationError("মাস ১ থেকে ১২-এর মধ্যে হতে হবে।")

        return month


class MonthlyReceivableForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("statement_file",)

    class Meta:
        model = MonthlyReceivable
        fields = [
            "industrial_unit",
            "fiscal_year",
            "month",
            "calculation_date",
            "previous_balance",
            "service_charge_due",
            "service_charge_interest",
            "land_installment_due",
            "land_installment_interest",
            "land_development_tax_due",
            "land_development_tax_interest",
            "water_bill_due",
            "water_bill_interest",
            "other_due",
            "other_due_description",
            "annual_collection_target",
            "monthly_collection_target",
            "statement_file",
            "comments",
        ]
        widgets = {
            "calculation_date": forms.DateInput(attrs={"type": "date"}),
            "other_due_description": forms.Textarea(attrs={"rows": 2}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_month(self):
        month = self.cleaned_data["month"]

        if not 1 <= month <= 12:
            raise ValidationError("মাস ১ থেকে ১২-এর মধ্যে হতে হবে।")

        return month


class MonthlyPaymentForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("proof_file",)

    class Meta:
        model = MonthlyPayment
        fields = [
            "account",
            "payment_date",
            "amount",
            "receipt_number",
            "proof_file",
            "comments",
        ]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class BankLoanForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("noc_document",)

    class Meta:
        model = BankLoan
        fields = [
            "industrial_unit",
            "bank_name",
            "loan_amount",
            "loan_date",
            "noc_date",
            "status",
            "noc_document",
            "comments",
        ]
        widgets = {
            "loan_date": forms.DateInput(attrs={"type": "date"}),
            "noc_date": forms.DateInput(attrs={"type": "date"}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class BankLoanDocumentForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("file",)

    class Meta:
        model = BankLoanDocument
        fields = ["loan", "title", "file"]


class UnitTransferForm(BootstrapModelForm, PDFValidationMixin):
    pdf_fields = ("approval_document",)

    class Meta:
        model = UnitTransfer
        fields = [
            "industrial_unit",
            "transfer_date",
            "from_company",
            "to_company",
            "reason",
            "approval_document",
            "comments",
        ]
        widgets = {
            "transfer_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.Textarea(attrs={"rows": 2}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class PlotCancellationAppealForm(
    BootstrapModelForm, PDFValidationMixin
):
    pdf_fields = ("document",)

    class Meta:
        model = PlotCancellationAppeal
        fields = [
            "industrial_unit",
            "plot",
            "cancellation_date",
            "cancellation_reason",
            "office_action",
            "appeal_filed",
            "appeal_date",
            "appeal_details",
            "latest_status",
            "document",
        ]
        widgets = {
            "cancellation_date": forms.DateInput(attrs={"type": "date"}),
            "appeal_date": forms.DateInput(attrs={"type": "date"}),
            "cancellation_reason": forms.Textarea(attrs={"rows": 2}),
            "office_action": forms.Textarea(attrs={"rows": 2}),
            "appeal_details": forms.Textarea(attrs={"rows": 2}),
        }


class ExportProductForm(BootstrapModelForm):
    class Meta:
        model = ExportProduct
        fields = [
            "industrial_unit",
            "product_name",
            "importing_country",
            "comments",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class EnvironmentalDataForm(BootstrapModelForm):
    class Meta:
        model = EnvironmentalData
        fields = [
            "industrial_unit",
            "has_solar_panel",
            "solar_capacity",
            "solar_capacity_unit",
            "needs_liquid_waste_treatment",
            "has_etp",
            "etp_capacity",
            "etp_capacity_unit",
            "effluent_type",
            "solid_waste_quantity",
            "solid_waste_unit",
            "solid_waste_management",
            "has_own_liquid_waste_management",
            "waste_goes_to_city_drain",
            "comments",
        ]
        widgets = {
            "solid_waste_management": forms.Textarea(attrs={"rows": 3}),
            "comments": forms.Textarea(attrs={"rows": 2}),
        }


class UtilityUsageForm(BootstrapModelForm):
    class Meta:
        model = UtilityUsage
        fields = [
            "environmental_data",
            "utility_type",
            "period_type",
            "year",
            "month",
            "quantity",
            "quantity_unit",
            "bill_amount",
            "comments",
        ]
        widgets = {
            "comments": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()

        if (
            cleaned.get("period_type") == UtilityUsage.PeriodType.MONTHLY
            and cleaned.get("month") is None
        ):
            self.add_error(
                "month",
                "মাসিক হিসাবের জন্য মাস নির্বাচন করুন।",
            )

        if (
            cleaned.get("period_type") == UtilityUsage.PeriodType.ANNUAL
            and cleaned.get("month") is not None
        ):
            self.add_error(
                "month",
                "বাৎসরিক হিসাবের ক্ষেত্রে মাস ফাঁকা রাখুন।",
            )

        return cleaned