from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    DetailView,
    UpdateView,
)
from django.db.models import Count, Sum, Q
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import get_object_or_404
from .models import IndustrialEstate
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from esate_db.districts import get_district_names_by_division
from .models import District, Upazila
from esate_db.districts import (DIVISION_DISTRICT_MAP,DISTRICT_NAMES_BN,)
from esate_db.districts import DIVISION_DISTRICT_MAP
from .models import District, Upazila
from django.http import JsonResponse
from .models import District, Upazila
from .models import (
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
from django.shortcuts import render
from .models import Plot
from .forms import (
    IndustrialEstateForm,
    EstateLayoutRevisionDocumentForm,
    PlotForm,
    IndustrialUnitForm,
    UnitPlotAllocationForm,
    UnitProductForm,
    EmploymentHistoryForm,
    MonthlyReceivableForm,
    MonthlyPaymentForm,
    BankLoanForm,
    BankLoanDocumentForm,
    UnitTransferForm,
    PlotCancellationAppealForm,
    ExportProductForm,
    EnvironmentalDataForm,
    UtilityUsageForm,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from accounts.models import UserRole
from .models import IndustrialEstate, Plot
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def get_user_profile(user):
    if not user.is_authenticated:
        raise PermissionDenied

    try:
        return user.userprofile
    except ObjectDoesNotExist:
        raise PermissionDenied(
            "আপনার UserProfile পাওয়া যায়নি।"
        )

# def get_user_profile(user):
#     if not user.is_authenticated:
#         raise PermissionDenied

#     try:
#         return user.userprofile
#     except ObjectDoesNotExist:
#         raise PermissionDenied(
#             "Your user profile has not been configured."
#         )


def get_accessible_estates(user):
    profile = get_user_profile(user)

    # Super Admin: সব Estate
    if profile.role == UserRole.SUPER_ADMIN:
        return IndustrialEstate.objects.all()

    # RD Admin: নিজের Regional Office-এর সব Estate
    if profile.role == UserRole.RD_ADMIN:
        if not profile.assigned_regional_office_id:
            return IndustrialEstate.objects.none()

        return IndustrialEstate.objects.filter(
            regional_office_id=profile.assigned_regional_office_id
        )

    # Data Entry:
    # নিজের তৈরি Estate + নিজের অধীনস্থ Estate Officer-দের তৈরি Estate
    if profile.role == UserRole.DATA_ENTRY:
        return IndustrialEstate.objects.filter(
            Q(created_by=user)
            | Q(
                created_by__userprofile__managed_by_data_entry=profile
            )
        ).distinct()

    # Estate Officer: শুধু নিজের তৈরি Estate
    if profile.role == UserRole.ESTATE_OFFICER:
        return IndustrialEstate.objects.filter(
            created_by=user
        )

    # Viewer: তার জন্য নির্ধারিত Estate শুধু দেখতে পারবে
    if profile.role == UserRole.VIEWER:
        return profile.assigned_estates.all()

    return IndustrialEstate.objects.none()

def get_user_role(user):
    return get_user_profile(user).role


def get_assigned_estate(user):
    """Return the estate assigned to an Estate Officer."""
    profile = get_user_profile(user)

    if profile.role != UserRole.ESTATE_OFFICER:
        raise PermissionDenied("এই কাজটি শুধু Estate Officer-এর জন্য।")

    if profile.assigned_estate_id is None:
        raise PermissionDenied(
            "আপনার জন্য কোনো শিল্পনগরী বরাদ্দ করা হয়নি।"
        )

    return profile.assigned_estate


# def get_accessible_estates(user):
#     """Return the estates visible to the current user."""
#     profile = get_user_profile(user)

#     if profile.role == UserRole.SUPER_ADMIN:
#         return IndustrialEstate.objects.all()

#     if profile.role == UserRole.ESTATE_OFFICER:
#         if profile.assigned_estate_id is None:
#             return IndustrialEstate.objects.none()

#         return IndustrialEstate.objects.filter(
#             pk=profile.assigned_estate_id
#         )

#     # RD_ADMIN, DATA_ENTRY এবং VIEWER-এর scope
#     # তাদের reporting/assignment policy অনুযায়ী নির্ধারণ করতে হবে।
#     return IndustrialEstate.objects.none()


def get_accessible_estate_or_404(user, estate_pk):
    return get_object_or_404(
        get_accessible_estates(user),
        pk=estate_pk,
    )
def is_read_only_user(user):
    return get_user_profile(user).role == UserRole.VIEWER


def require_write_access(user):
    if is_read_only_user(user):
        raise PermissionDenied("আপনার শুধু তথ্য দেখার অনুমতি রয়েছে।")
# =========================================================
# Division -> District -> Upazilla
# =========================================================
#@require_GET
def districts_by_division(request):
    division = request.GET.get("division", "")
    names = get_district_names_by_division(division)

    districts = District.objects.filter(
        name__in=names
    ).order_by("name")

    return JsonResponse([
        {
            "id": item.pk,
            "name": item.name,
            "label": item.name,
        }
        for item in districts
    ], safe=False)


def upazilas_by_district(request):
    district_id = request.GET.get("district_id", "")

    if not district_id.isdigit():
        return JsonResponse([], safe=False)

    upazilas = Upazila.objects.filter(
        district_id=int(district_id)
    ).order_by("name")

    return JsonResponse([
        {
            "id": item.pk,
            "name": item.name,
            "label": item.name,
        }
        for item in upazilas
    ], safe=False)

# =========================================================
# Reusable CRUD views
# =========================================================

class ProtectedListView(LoginRequiredMixin, ListView):
    paginate_by = 25


class ProtectedDetailView(LoginRequiredMixin, DetailView):
    pass


class ProtectedCreateView(LoginRequiredMixin, CreateView):
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            self.success_url_name,
            kwargs=self.get_success_url_kwargs(),
        )

    def get_success_url_kwargs(self):
        return {}

    def form_valid(self, form):
        messages.success(self.request, "তথ্য সফলভাবে সংরক্ষণ করা হয়েছে।")
        return super().form_valid(form)


class ProtectedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            self.success_url_name,
            kwargs=self.get_success_url_kwargs(),
        )

    def get_success_url_kwargs(self):
        return {}

    def form_valid(self, form):
        messages.success(self.request, "তথ্য সফলভাবে হালনাগাদ করা হয়েছে।")
        return super().form_valid(form)


# =========================================================
# Industrial estate pages
# =========================================================

@login_required
def estate_list(request):
    estates = (
        get_accessible_estates(request.user)
        .select_related(
            "regional_office",
            "district",
            "upazila",
        )
        .annotate(
            plot_count=Count("plots", distinct=True),
            unit_count=Count("industrial_units", distinct=True),
        )
    )

    return render(
        request,
        "industrial_estate/estate_list.html",
        {"estates": estates},
    )


@login_required
def estate_detail(request, pk):
    estate = get_accessible_estate_or_404(
        request.user,
        pk,
    )

    plots = Plot.objects.filter(estate=estate)
    # estate = get_object_or_404(
    #     IndustrialEstate.objects.select_related(
    #         "regional_office", "district", "upazila"
    #     ),
    #     pk=pk,
    # )

    # plots = estate.plots.all()
    units = estate.industrial_units.all()

    context = {
        "estate": estate,
        "plots": plots[:10],
        "units": units[:10],
        "plot_count": plots.count(),
        "allocated_plot_count": plots.filter(
            current_status=Plot.Status.ALLOCATED
        ).count(),
        "vacant_plot_count": plots.filter(
            current_status=Plot.Status.ALLOCATABLE
        ).count(),
        "unit_count": units.count(),
    }

    return render(
        request,
        "industrial_estate/estate_detail.html",
        context,
    )


class EstateCreateView(LoginRequiredMixin, CreateView):
    model = IndustrialEstate
    form_class = IndustrialEstateForm
    template_name = "industrial_estate/estate_form.html"
    success_url = reverse_lazy("industrial_estate:estate_list")

    def dispatch(self, request, *args, **kwargs):
        profile = get_user_profile(request.user)

        allowed_roles = {
            UserRole.SUPER_ADMIN,
            UserRole.RD_ADMIN,
            UserRole.DATA_ENTRY,
            UserRole.ESTATE_OFFICER,
        }

        if profile.role not in allowed_roles:
            raise PermissionDenied(
                "আপনার নতুন শিল্পনগরী তৈরির অনুমতি নেই।"
            )

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        response = super().form_valid(form)

        messages.success(
            self.request,
            "শিল্পনগরীর তথ্য সফলভাবে সংরক্ষণ করা হয়েছে।"
        )

        return response


class EstateUpdateView(LoginRequiredMixin, UpdateView):
    model = IndustrialEstate
    form_class = IndustrialEstateForm
    template_name = "industrial_estate/estate_form.html"
    success_url = reverse_lazy("industrial_estate:estate_list")

    def get_queryset(self):
        return get_accessible_estates(self.request.user)

    def form_valid(self, form):
        messages.success(
            self.request,
            "শিল্পনগরীর তথ্য হালনাগাদ হয়েছে।",
        )
        return super().form_valid(form)


@login_required
def layout_revision_add(request, pk):
    estate = get_object_or_404(IndustrialEstate, pk=pk)

    if request.method == "POST":
        form = EstateLayoutRevisionDocumentForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            revision = form.save(commit=False)
            revision.estate = estate
            revision.save()

            messages.success(request, "লে-আউট সংশোধনী দলিল সংরক্ষণ করা হয়েছে।")
            return redirect(
                "industrial_estate:estate_detail",
                pk=estate.pk,
            )
    else:
        form = EstateLayoutRevisionDocumentForm()

    return render(
        request,
        "industrial_estate/record_form.html",
        {
            "form": form,
            "page_title": "লে-আউট সংশোধনী দলিল যোগ",
            "cancel_url": reverse(
                "industrial_estate:estate_detail",
                kwargs={"pk": estate.pk},
            ),
        },
    )

# =========================================================
# Plot pages
# =========================================================

@login_required
def plot_list(request, estate_pk):
    estate = get_accessible_estate_or_404(
        request.user,
        estate_pk,
    )

    plots = estate.plots.all().order_by("plot_number")

    return render(
        request,
        "industrial_estate/plot_list.html",
        {
            "estate": estate,
            "plots": plots,
        },
    )


@login_required
def plot_list_all(request):
    accessible_estates = get_accessible_estates(request.user)

    plots = (
        Plot.objects
        .filter(estate__in=accessible_estates)
        .select_related("estate")
        .order_by("estate__name", "plot_number")
    )

    return render(
        request,
        "industrial_estate/plot_list.html",
        {
            "plots": plots,
            "estate": None,
        },
    )


class PlotCreateView(LoginRequiredMixin, CreateView):
    model = Plot
    form_class = PlotForm
    template_name = "industrial_estate/record_form.html"

    def get_estate_queryset(self):
        return get_accessible_estates(self.request.user)

    def get_fixed_estate_id(self):
        profile = get_user_profile(self.request.user)

        # Estate Officer: শুধু নিজের তৈরি Estate
        if profile.role == UserRole.ESTATE_OFFICER:
            estate_qs = IndustrialEstate.objects.filter(
                created_by=self.request.user
            )

            requested_id = self.request.GET.get("estate")

            if requested_id:
                estate = get_object_or_404(
                    estate_qs,
                    pk=requested_id,
                )
                return estate.pk

            # মাত্র একটি Estate থাকলে সেটি স্বয়ংক্রিয়ভাবে নির্বাচন
            if estate_qs.count() == 1:
                return estate_qs.values_list("pk", flat=True).first()

        return None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["estate_queryset"] = self.get_estate_queryset()
        kwargs["fixed_estate_id"] = self.get_fixed_estate_id()
        return kwargs

    def get_success_url(self):
        return reverse(
            "industrial_estate:plot_list",
            kwargs={"estate_pk": self.object.estate_id},
        )


class PlotUpdateView(LoginRequiredMixin, UpdateView):
    model = Plot
    form_class = PlotForm
    template_name = "industrial_estate/record_form.html"

    def get_queryset(self):
        return Plot.objects.filter(
            estate__in=get_accessible_estates(self.request.user)
        ).select_related("estate")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["estate_queryset"] = get_accessible_estates(
            self.request.user
        )

        # Plot-কে অন্য Estate-এ স্থানান্তর করতে দেওয়া হবে না
        kwargs["fixed_estate_id"] = self.object.estate_id
        return kwargs

    def get_success_url(self):
        return reverse(
            "industrial_estate:plot_list",
            kwargs={"estate_pk": self.object.estate_id},
        )


# =========================================================
# Industrial unit pages
# =========================================================

class IndustrialUnitListView(ProtectedListView):
    model = IndustrialUnit
    template_name = "industrial_estate/industrial_unit_list.html"
    context_object_name = "units"

    def get_queryset(self):
        queryset = IndustrialUnit.objects.select_related("estate").order_by(
            "estate__name", "name"
        )

        estate_pk = self.request.GET.get("estate")
        if estate_pk:
            queryset = queryset.filter(estate_id=estate_pk)

        search = self.request.GET.get("q")
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(unit_code__icontains=search)
                | Q(owner_name__icontains=search)
            )

        return queryset


class IndustrialUnitDetailView(ProtectedDetailView):
    model = IndustrialUnit
    template_name = "industrial_estate/industrial_unit_detail.html"
    context_object_name = "unit"

    def get_queryset(self):
        return IndustrialUnit.objects.select_related("estate").prefetch_related(
            "plot_allocations__plot",
            "products",
            "employment_records",
            "monthly_accounts__payments",
            "bank_loans",
            "transfers",
            "export_products",
        )


class IndustrialUnitCreateView(LoginRequiredMixin, CreateView):
    model = IndustrialUnit
    form_class = IndustrialUnitForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        estate_pk = self.request.GET.get("estate")
        if estate_pk:
            initial["estate"] = estate_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.pk},
        )


class IndustrialUnitUpdateView(LoginRequiredMixin, UpdateView):
    model = IndustrialUnit
    form_class = IndustrialUnitForm
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.pk},
        )


# =========================================================
# Reusable record CRUD views for related models
# =========================================================

class UnitRelatedCreateView(LoginRequiredMixin, CreateView):
    template_name = "industrial_estate/record_form.html"
    unit_field = "industrial_unit"

    def get_initial(self):
        initial = super().get_initial()
        unit_pk = self.request.GET.get("unit")
        if unit_pk:
            initial[self.unit_field] = unit_pk
        return initial

    def form_valid(self, form):
        messages.success(self.request, "তথ্য সংরক্ষণ করা হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": getattr(self.object, self.unit_field + "_id")},
        )


class UnitRelatedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": getattr(self.object, "industrial_unit_id")},
        )

    def form_valid(self, form):
        messages.success(self.request, "তথ্য হালনাগাদ হয়েছে।")
        return super().form_valid(form)


class UnitRelatedListView(ProtectedListView):
    template_name = "industrial_estate/related_record_list.html"
    context_object_name = "records"
    unit_lookup = "industrial_unit_id"

    def get_queryset(self):
        unit_pk = self.request.GET.get("unit")
        queryset = self.model.objects.all()

        if unit_pk:
            queryset = queryset.filter(**{self.unit_lookup: unit_pk})

        return queryset


# Plot allocations
class AllocationCreateView(UnitRelatedCreateView):
    model = UnitPlotAllocation
    form_class = UnitPlotAllocationForm
    unit_field = "industrial_unit"


class AllocationUpdateView(UnitRelatedUpdateView):
    model = UnitPlotAllocation
    form_class = UnitPlotAllocationForm


class AllocationListView(UnitRelatedListView):
    model = UnitPlotAllocation


# Products
class ProductCreateView(UnitRelatedCreateView):
    model = UnitProduct
    form_class = UnitProductForm


class ProductUpdateView(UnitRelatedUpdateView):
    model = UnitProduct
    form_class = UnitProductForm


class ProductListView(UnitRelatedListView):
    model = UnitProduct


# Employment history
class EmploymentCreateView(UnitRelatedCreateView):
    model = EmploymentHistory
    form_class = EmploymentHistoryForm


class EmploymentUpdateView(UnitRelatedUpdateView):
    model = EmploymentHistory
    form_class = EmploymentHistoryForm


class EmploymentListView(UnitRelatedListView):
    model = EmploymentHistory


# Monthly receivables
class ReceivableCreateView(UnitRelatedCreateView):
    model = MonthlyReceivable
    form_class = MonthlyReceivableForm


class ReceivableUpdateView(UnitRelatedUpdateView):
    model = MonthlyReceivable
    form_class = MonthlyReceivableForm


class ReceivableListView(UnitRelatedListView):
    model = MonthlyReceivable


# Payments belong to a monthly account, not directly to a unit.
class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = MonthlyPayment
    form_class = MonthlyPaymentForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        account_pk = self.request.GET.get("account")
        if account_pk:
            initial["account"] = account_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:receivable_list"
        ) + f"?unit={self.object.account.industrial_unit_id}"


class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = MonthlyPayment
    form_class = MonthlyPaymentForm
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            "industrial_estate:receivable_list"
        ) + f"?unit={self.object.account.industrial_unit_id}"


# Bank loans
class BankLoanCreateView(UnitRelatedCreateView):
    model = BankLoan
    form_class = BankLoanForm


class BankLoanUpdateView(UnitRelatedUpdateView):
    model = BankLoan
    form_class = BankLoanForm


class BankLoanListView(UnitRelatedListView):
    model = BankLoan


# Additional bank documents
class BankLoanDocumentCreateView(LoginRequiredMixin, CreateView):
    model = BankLoanDocument
    form_class = BankLoanDocumentForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        loan_pk = self.request.GET.get("loan")
        if loan_pk:
            initial["loan"] = loan_pk
        return initial

    def get_success_url(self):
        return reverse("industrial_estate:bank_loan_list") + (
            f"?unit={self.object.loan.industrial_unit_id}"
        )


# Transfers
class TransferCreateView(UnitRelatedCreateView):
    model = UnitTransfer
    form_class = UnitTransferForm


class TransferUpdateView(UnitRelatedUpdateView):
    model = UnitTransfer
    form_class = UnitTransferForm


class TransferListView(UnitRelatedListView):
    model = UnitTransfer


# Export products
class ExportProductCreateView(UnitRelatedCreateView):
    model = ExportProduct
    form_class = ExportProductForm


class ExportProductUpdateView(UnitRelatedUpdateView):
    model = ExportProduct
    form_class = ExportProductForm


class ExportProductListView(UnitRelatedListView):
    model = ExportProduct


# Cancellation/appeals are linked to both a unit and a plot.
class AppealCreateView(LoginRequiredMixin, CreateView):
    model = PlotCancellationAppeal
    form_class = PlotCancellationAppealForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        unit_pk = self.request.GET.get("unit")
        plot_pk = self.request.GET.get("plot")
        if unit_pk:
            initial["industrial_unit"] = unit_pk
        if plot_pk:
            initial["plot"] = plot_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.industrial_unit_id},
        )


class AppealUpdateView(LoginRequiredMixin, UpdateView):
    model = PlotCancellationAppeal
    form_class = PlotCancellationAppealForm
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.industrial_unit_id},
        )


# Environment data is one-to-one with the unit.
class EnvironmentalDataCreateView(LoginRequiredMixin, CreateView):
    model = EnvironmentalData
    form_class = EnvironmentalDataForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        unit_pk = self.request.GET.get("unit")
        if unit_pk:
            initial["industrial_unit"] = unit_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.industrial_unit_id},
        )


class EnvironmentalDataUpdateView(LoginRequiredMixin, UpdateView):
    model = EnvironmentalData
    form_class = EnvironmentalDataForm
    template_name = "industrial_estate/record_form.html"

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.industrial_unit_id},
        )


class UtilityUsageCreateView(LoginRequiredMixin, CreateView):
    model = UtilityUsage
    form_class = UtilityUsageForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        environmental_pk = self.request.GET.get("environment")
        if environmental_pk:
            initial["environmental_data"] = environmental_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={
                "pk": self.object.environmental_data.industrial_unit_id
            },
        )
class UtilityUsageUpdateView(LoginRequiredMixin, UpdateView):
    model = UtilityUsage
    form_class = UtilityUsageForm
    template_name = "industrial_estate/record_form.html"
    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={
                "pk": self.object.environmental_data.industrial_unit_id
            },
        )

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Upazila


@require_GET
def upazila_options(request):
    district_id = request.GET.get("district_id")

    if not district_id or not district_id.isdigit():
        return JsonResponse([], safe=False)

    upazilas = (
        Upazila.objects
        .filter(district_id=int(district_id))
        .order_by("name")
        .values("id", "name")
    )

    return JsonResponse(list(upazilas), safe=False)



@require_GET
def location_options(request):
    division = request.GET.get("division")
    district_id = request.GET.get("district_id")

    if district_id:
        upazilas = (
            Upazila.objects
            .filter(district_id=district_id)
            .order_by("name")
        )

        return JsonResponse([
            {
                "id": item.pk,
                "name": item.name,
            }
            for item in upazilas
        ], safe=False)

    district_names = DIVISION_DISTRICT_MAP.get(division, [])

    districts = District.objects.filter(
        name__in=district_names
    ).order_by("name")

    return JsonResponse([
        {
            "id": item.pk,
            "name": item.name,
        }
        for item in districts
    ], safe=False)
