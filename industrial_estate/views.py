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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from .models import IndustrialUnit, EmploymentHistory, UnitProduct, UnitPlotAllocation
from .forms import IndustrialUnitStatusForm, EmploymentHistoryForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import UnitPlotAllocation
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import IndustrialUnit, UnitProduct
from .forms import (
    IndustrialUnitProductionForm,
    UnitProductForm,
)
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView
from .models import UnitPlotAllocation, IndustrialEstate, Plot
from .forms import UnitPlotAllocationForm
from .models import UtilityUsage
from .models import IndustrialEstate, IndustrialUnit
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
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse
from django.contrib import messages

from accounts.models import UserRole
from .models import (
    IndustrialEstate,
    IndustrialUnit,
    Plot,
    UnitProduct,
    EstateReview,
)

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

def get_accessible_units(user):
    """
    Return only industrial units belonging to estates
    accessible to the logged-in user.
    """
    return IndustrialUnit.objects.filter(
        estate__in=get_accessible_estates(user)
    )

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

class IndustrialUnitListView(LoginRequiredMixin, ListView):
    model = IndustrialUnit
    template_name = "industrial_estate/industrial_unit_list.html"
    context_object_name = "units"

    def get_queryset(self):
        queryset = get_accessible_units(
            self.request.user
        ).select_related("estate").order_by("estate__name", "name")

        estate_pk = self.request.GET.get("estate")
        if estate_pk:
            queryset = queryset.filter(estate_id=estate_pk)

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(unit_code__icontains=search)
                | Q(owner_name__icontains=search)
            )

        return queryset


class IndustrialUnitDetailView(LoginRequiredMixin, DetailView):
    model = IndustrialUnit
    template_name = "industrial_estate/industrial_unit_detail.html"
    context_object_name = "unit"

    def get_queryset(self):
        return get_accessible_units(
            self.request.user
        ).select_related("estate").prefetch_related(
            "plot_allocations__plot",
            "products",
            "employment_records",
            "monthly_accounts__payments",
            "bank_loans",
            "transfers",
            "export_products",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unit = self.object

        # Section 01: General information
        context["section_01_unit"] = unit

        # Section 02: Plot allocation and possession
        context["section_02_allocations"] = unit.plot_allocations.all()

        # Section 03: Products
        context["section_03_products"] = unit.products.all()

        # Section 04: Employment
        context["section_04_employment"] = unit.employment_records.all()

        # Section 05: Floor-space rent
        # Actual model relationship is not yet confirmed.
        context["section_05_floor_rent"] = []

        # Section 06: Accounts and receivables
        context["section_06_receivables"] = unit.monthly_accounts.all()

        # Section 07: Bank loans
        context["section_07_bank_loans"] = unit.bank_loans.all()

        # Section 08: Transfers
        context["section_08_transfers"] = unit.transfers.all()

        # Section 09: Exports
        context["section_09_exports"] = unit.export_products.all()

        # Section 08: Cancellation and appeals
        context["section_08_cancellation_appeals"] = Plot.objects.filter(
            estate=unit.estate
        )

        # Section 10: Environmental data
        context["section_10_environmental_data"] = []

        # Section 10: Utility usage
        context["section_10_utility_usage"] = []

        context["can_edit"] = (
            get_user_profile(self.request.user).role != UserRole.VIEWER
        )

        return context


class IndustrialUnitCreateView(LoginRequiredMixin, CreateView):
    model = IndustrialUnit
    form_class = IndustrialUnitForm
    template_name = "industrial_estate/industrial_unit_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        profile = get_user_profile(self.request.user)

        form.fields["estate"].queryset = get_accessible_estates(
            self.request.user
        )

        if profile.role == UserRole.ESTATE_OFFICER:
            estates = get_accessible_estates(self.request.user)
            if estates.count() != 1:
                raise PermissionDenied(
                    "আপনার নামে একটি শিল্পনগরী নিশ্চিত করুন।"
                )

            estate = estates.first()
            form.fields["estate"].initial = estate.pk
            form.fields["estate"].disabled = True

        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "শিল্প ইউনিটের তথ্য সংরক্ষণ হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.pk},
        )


class IndustrialUnitUpdateView(LoginRequiredMixin, UpdateView):
    model = IndustrialUnit
    form_class = IndustrialUnitForm
    template_name = "industrial_estate/industrial_unit_form.html"

    def get_queryset(self):
        return get_accessible_units(self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["estate"].queryset = get_accessible_estates(
            self.request.user
        )

        if get_user_profile(self.request.user).role == UserRole.ESTATE_OFFICER:
            form.fields["estate"].disabled = True

        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "শিল্প ইউনিটের তথ্য হালনাগাদ হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": self.object.pk},
        )

# =========================================================
# Reusable record CRUD views for related models
# =========================================================

class UnitRelatedListView(LoginRequiredMixin, ListView):
    template_name = "industrial_estate/related_record_list.html"
    context_object_name = "records"
    unit_lookup = "industrial_unit"

    def get_queryset(self):
        unit_pk = self.request.GET.get("unit")
        queryset = self.model.objects.filter(
            **{
                f"{self.unit_lookup}__estate__in":
                    get_accessible_estates(self.request.user)
            }
        )

        if unit_pk:
            queryset = queryset.filter(
                **{f"{self.unit_lookup}_id": unit_pk}
            )

        return queryset


class UnitRelatedCreateView(LoginRequiredMixin, CreateView):
    template_name = "industrial_estate/record_form.html"
    unit_field = "industrial_unit"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        unit_field = form.fields.get(self.unit_field)

        if unit_field:
            unit_field.queryset = get_accessible_units(self.request.user)

            unit_pk = self.request.GET.get("unit")
            if unit_pk:
                unit_field.initial = get_object_or_404(
                    get_accessible_units(self.request.user),
                    pk=unit_pk,
                ).pk

        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "তথ্য সংরক্ষণ করা হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        unit_id = getattr(self.object, f"{self.unit_field}_id")
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": unit_id},
        )


class UnitRelatedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "industrial_estate/record_form.html"
    unit_field = "industrial_unit"

    def get_queryset(self):
        return self.model.objects.filter(
            **{
                f"{self.unit_field}__estate__in":
                    get_accessible_estates(self.request.user)
            }
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        field = form.fields.get(self.unit_field)
        if field:
            field.queryset = get_accessible_units(self.request.user)
        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "তথ্য হালনাগাদ হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        unit_id = getattr(self.object, f"{self.unit_field}_id")
        return reverse(
            "industrial_estate:industrial_unit_detail",
            kwargs={"pk": unit_id},
        )


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
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages


@login_required
def estate_review_queue(request):
    profile = get_user_profile(request.user)

    if profile.role == UserRole.DATA_ENTRY:
        status = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_DATA_ENTRY

    elif profile.role == UserRole.RD_ADMIN:
        status = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_RD_ADMIN

    elif profile.role == UserRole.SUPER_ADMIN:
        status = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN

    else:
        raise PermissionDenied(
            "আপনার পর্যালোচনা তালিকা দেখার অনুমতি নেই।"
        )

    estates = get_accessible_estates(request.user).filter(
        workflow_status=status
    ).select_related(
        "regional_office",
        "created_by",
    ).order_by("name")

    return render(
        request,
        "industrial_estate/estate_review_queue.html",
        {
            "estates": estates,
            "profile": profile,
        },
    )
@login_required
@require_POST
def estate_review_action(request, pk):
    profile = get_user_profile(request.user)

    estate = get_accessible_estate_or_404(request.user, pk)
    action = request.POST.get("action")
    comment = request.POST.get("comment", "").strip()

    current_status = estate.workflow_status

    if profile.role == UserRole.DATA_ENTRY:
        expected = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_DATA_ENTRY
        stage = EstateReview.Stage.DATA_ENTRY

        if current_status != expected:
            raise PermissionDenied("এই তথ্য আপনার পর্যালোচনার জন্য অপেক্ষমাণ নয়।")

        if action == "forward":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.SUBMITTED_TO_RD_ADMIN
            )
            review_action = EstateReview.Action.FORWARDED
        elif action == "return":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.RETURNED_TO_ESTATE_OFFICER
            )
            review_action = EstateReview.Action.RETURNED
        else:
            raise PermissionDenied("অবৈধ কার্যক্রম।")

    elif profile.role == UserRole.RD_ADMIN:
        expected = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_RD_ADMIN
        stage = EstateReview.Stage.RD_ADMIN

        if current_status != expected:
            raise PermissionDenied("এই তথ্য আপনার পর্যালোচনার জন্য অপেক্ষমাণ নয়।")

        if action == "forward":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN
            )
            review_action = EstateReview.Action.FORWARDED
        elif action == "return":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.RETURNED_TO_DATA_ENTRY
            )
            review_action = EstateReview.Action.RETURNED
        else:
            raise PermissionDenied("অবৈধ কার্যক্রম।")

    elif profile.role == UserRole.SUPER_ADMIN:
        expected = IndustrialEstate.WorkflowStatus.SUBMITTED_TO_SUPER_ADMIN
        stage = EstateReview.Stage.SUPER_ADMIN

        if current_status != expected:
            raise PermissionDenied("এই তথ্য আপনার যাচাইয়ের জন্য অপেক্ষমাণ নয়।")

        if action == "verify":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.VERIFIED
            )
            review_action = EstateReview.Action.VERIFIED
        elif action == "return":
            estate.workflow_status = (
                IndustrialEstate.WorkflowStatus.RETURNED_TO_RD_ADMIN
            )
            review_action = EstateReview.Action.RETURNED
        else:
            raise PermissionDenied("অবৈধ কার্যক্রম।")

    else:
        raise PermissionDenied("আপনার এই কার্যক্রমের অনুমতি নেই।")

    estate.save(update_fields=["workflow_status", "updated_at"])

    EstateReview.objects.create(
        estate=estate,
        stage=stage,
        action=review_action,
        reviewer=request.user,
        comment=comment,
    )

    messages.success(request, "পর্যালোচনার কার্যক্রম সংরক্ষণ হয়েছে।")
    return redirect("industrial_estate:estate_review_queue")

class UnitPlotAllocationListView(LoginRequiredMixin, ListView):
    model = UnitPlotAllocation
    template_name = "industrial_estate/plot_allocation_list.html"
    context_object_name = "allocations"

    def get_queryset(self):
        queryset = UnitPlotAllocation.objects.filter(
            industrial_unit__in=get_accessible_units(self.request.user)
        ).select_related(
            "industrial_unit", "plot", "plot__estate"
        ).order_by(
            "plot__estate__name", "plot__plot_number"
        )

        unit_id = self.request.GET.get("industrial_unit")
        if unit_id:
            queryset = queryset.filter(industrial_unit_id=unit_id)

        search = self.request.GET.get("q")
        if search:
            queryset = queryset.filter(
                Q(industrial_unit__name__icontains=search)
                | Q(industrial_unit__unit_code__icontains=search)
                | Q(plot__plot_number__icontains=search)
                | Q(plot__estate__name__icontains=search)
            )

        return queryset


class UnitPlotAllocationCreateView(LoginRequiredMixin, CreateView):
    model = UnitPlotAllocation
    form_class = UnitPlotAllocationForm
    template_name = "industrial_estate/plot_allocation_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        units = get_accessible_units(self.request.user)
        estates = get_accessible_estates(self.request.user)

        form.fields["industrial_unit"].queryset = units
        form.fields["plot"].queryset = Plot.objects.filter(
            estate__in=estates
        ).select_related("estate")

        unit_id = self.request.GET.get("industrial_unit")
        if unit_id and units.filter(pk=unit_id).exists():
            form.fields["industrial_unit"].initial = unit_id
            form.fields["plot"].queryset = Plot.objects.filter(
                estate_id=units.get(pk=unit_id).estate_id
            )

        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "প্লট বরাদ্দের তথ্য সংরক্ষণ হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("industrial_estate:allocation_list")


class UnitPlotAllocationUpdateView(LoginRequiredMixin, UpdateView):
    model = UnitPlotAllocation
    form_class = UnitPlotAllocationForm
    template_name = "industrial_estate/plot_allocation_form.html"

    def get_queryset(self):
        return UnitPlotAllocation.objects.filter(
            industrial_unit__in=get_accessible_units(self.request.user)
        ).select_related("industrial_unit", "plot")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        units = get_accessible_units(self.request.user)
        estates = get_accessible_estates(self.request.user)

        form.fields["industrial_unit"].queryset = units
        form.fields["plot"].queryset = Plot.objects.filter(
            estate__in=estates
        ).select_related("estate")

        return form

    def form_valid(self, form):
        require_write_access(self.request.user)
        messages.success(self.request, "প্লট বরাদ্দের তথ্য হালনাগাদ হয়েছে।")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("industrial_estate:allocation_list")
@login_required
def unit_production_list(request):
    """সাব-সেকশন ০৩: শিল্প ইউনিটের উৎপাদন ও পণ্যের তালিকা।"""

    units = get_accessible_units(request.user).select_related(
        "estate"
    ).prefetch_related("products")

    search = request.GET.get("q", "").strip()

    if search:
        units = units.filter(
            Q(name__icontains=search)
            | Q(unit_code__icontains=search)
            | Q(estate__name__icontains=search)
            | Q(products__name__icontains=search)
        ).distinct()

    return render(
        request,
        "industrial_estate/unit_production_list.html",
        {
            "units": units,
            "search": search,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def unit_production_update(request, pk):
    """কারখানার তথ্য সম্পাদনা এবং একাধিক পণ্য ব্যবস্থাপনা।"""

    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=pk,
    )

    if request.method == "POST":
        try:
            require_write_access(request.user)
        except PermissionDenied:
            raise

        if "save_production" in request.POST:
            production_form = IndustrialUnitProductionForm(
                request.POST,
                request.FILES,
                instance=unit,
            )
            product_form = UnitProductForm()

            if production_form.is_valid():
                production_form.save()
                messages.success(
                    request,
                    "কারখানা ও উৎপাদন-সংক্রান্ত তথ্য সংরক্ষণ হয়েছে।",
                )
                return redirect(
                    "industrial_estate:unit_production_update",
                    pk=unit.pk,
                )

        elif "add_product" in request.POST:
            production_form = IndustrialUnitProductionForm(
                instance=unit
            )
            product_form = UnitProductForm(request.POST)

            if product_form.is_valid():
                product = product_form.save(commit=False)
                product.industrial_unit = unit
                product.save()

                messages.success(
                    request,
                    "উৎপাদিত পণ্যের তথ্য যোগ করা হয়েছে।",
                )
                return redirect(
                    "industrial_estate:unit_production_update",
                    pk=unit.pk,
                )
        else:
            production_form = IndustrialUnitProductionForm(
                instance=unit
            )
            product_form = UnitProductForm()

    else:
        production_form = IndustrialUnitProductionForm(instance=unit)
        product_form = UnitProductForm()

    products = unit.products.all()

    return render(
        request,
        "industrial_estate/unit_production_form.html",
        {
            "unit": unit,
            "production_form": production_form,
            "product_form": product_form,
            "products": products,
        },
    )


@login_required
@require_http_methods(["POST"])
def unit_product_delete(request, pk, product_pk):
    """নির্বাচিত শিল্প ইউনিটের একটি পণ্য মুছে ফেলা।"""

    try:
        require_write_access(request.user)
    except PermissionDenied:
        raise

    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=pk,
    )

    product = get_object_or_404(
        UnitProduct,
        pk=product_pk,
        industrial_unit=unit,
    )
@login_required
@require_POST
def unit_plot_allocation_delete(request, pk):
    require_write_access(request.user)

    allocation = get_object_or_404(
        UnitPlotAllocation.objects.filter(
            industrial_unit__in=get_accessible_units(request.user)
        ),
        pk=pk,
    )

    allocation.delete()

    messages.success(request, "প্লট বরাদ্দের তথ্য মুছে ফেলা হয়েছে।")

    return redirect("industrial_estate:allocation_list")
@login_required
def employment_list(request):
    units = (
        get_accessible_units(request.user)
        .select_related("estate")
        .prefetch_related("employment_records")
        .order_by("estate__name", "name")
    )

    search = request.GET.get("q", "").strip()
    if search:
        units = units.filter(
            Q(name__icontains=search)
            | Q(unit_code__icontains=search)
            | Q(estate__name__icontains=search)
        ).distinct()

    return render(
        request,
        "industrial_estate/employment_list.html",
        {"units": units, "search": search},
    )


@login_required
@require_http_methods(["GET", "POST"])
def unit_status_update(request, pk):
    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=pk,
    )

    if request.method == "POST":
        require_write_access(request.user)
        form = IndustrialUnitStatusForm(request.POST, instance=unit)

        if form.is_valid():
            form.save()
            messages.success(request, "শিল্প ইউনিটের অবস্থা সংরক্ষণ হয়েছে।")
            return redirect(
                "industrial_estate:employment_list"
            )
    else:
        form = IndustrialUnitStatusForm(instance=unit)

    return render(
        request,
        "industrial_estate/unit_status_form.html",
        {"unit": unit, "form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def employment_create(request, unit_pk):
    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=unit_pk,
    )

    if request.method == "POST":
        require_write_access(request.user)
        form = EmploymentHistoryForm(request.POST)

        if form.is_valid():
            record = form.save(commit=False)
            record.industrial_unit = unit
            record.save()

            messages.success(request, "কর্মসংস্থানের তথ্য যোগ করা হয়েছে।")
            return redirect("industrial_estate:employment_list")
    else:
        form = EmploymentHistoryForm()

    return render(
        request,
        "industrial_estate/employment_form.html",
        {"unit": unit, "form": form, "page_title": "কর্মসংস্থানের তথ্য যোগ"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def employment_update(request, unit_pk, pk):
    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=unit_pk,
    )

    record = get_object_or_404(
        EmploymentHistory,
        pk=pk,
        industrial_unit=unit,
    )

    if request.method == "POST":
        require_write_access(request.user)
        form = EmploymentHistoryForm(request.POST, instance=record)

        if form.is_valid():
            form.save()
            messages.success(
                request, "কর্মসংস্থানের তথ্য হালনাগাদ হয়েছে।"
            )
            return redirect("industrial_estate:employment_list")
    else:
        form = EmploymentHistoryForm(instance=record)

    return render(
        request,
        "industrial_estate/employment_form.html",
        {"unit": unit, "form": form, "page_title": "কর্মসংস্থানের তথ্য সম্পাদনা"},
    )


@login_required
@require_POST
def employment_delete(request, unit_pk, pk):
    require_write_access(request.user)

    unit = get_object_or_404(
        get_accessible_units(request.user),
        pk=unit_pk,
    )

    record = get_object_or_404(
        EmploymentHistory,
        pk=pk,
        industrial_unit=unit,
    )
    record.delete()

    messages.success(request, "কর্মসংস্থানের রেকর্ড মুছে ফেলা হয়েছে।")
    return redirect("industrial_estate:employment_list")