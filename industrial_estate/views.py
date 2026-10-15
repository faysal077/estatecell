# from django.shortcuts import render

# # Create your views here.
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.db.models import Count, Q
# from django.shortcuts import get_object_or_404, redirect, render
# from django.views.decorators.http import require_POST

# from .forms import (
#     IndustrialEstateForm,
#     EstateLayoutRevisionDocumentForm,
# )
# from .models import IndustrialEstate, Plot


# @login_required
# def estate_list(request):
#     estates = IndustrialEstate.objects.select_related(
#         "rd_office",
#         "district",
#         "upazila",
#     ).annotate(
#         total_plots=Count("plots", distinct=True),
#         allocated_plots=Count(
#             "plots",
#             filter=Q(plots__current_status="allocated"),
#             distinct=True,
#         ),
#         allocatable_plots=Count(
#             "plots",
#             filter=Q(plots__current_status="allocatable"),
#             distinct=True,
#         ),
#     )

#     query = request.GET.get("q", "").strip()

#     if query:
#         estates = estates.filter(
#             Q(name__icontains=query)
#             | Q(district__name__icontains=query)
#             | Q(rd_office__name__icontains=query)
#         )

#     context = {
#         "estates": estates,
#         "q": query,
#     }

#     return render(
#         request,
#         "industrial_estate/estate_list.html",
#         context,
#     )


# @login_required
# def estate_detail(request, pk):
#     estate = get_object_or_404(
#         IndustrialEstate.objects.select_related(
#             "rd_office",
#             "district",
#             "upazila",
#         ),
#         pk=pk,
#     )

#     plots = estate.plots.all()

#     context = {
#         "estate": estate,
#         "total_plots": plots.count(),
#         "allocated_plots": plots.filter(
#             current_status="allocated"
#         ).count(),
#         "allocatable_plots": plots.filter(
#             current_status="allocatable"
#         ).count(),
#         "layout_revisions": estate.layout_revision_documents.all(),
#         "revision_form": EstateLayoutRevisionDocumentForm(),
#     }

#     return render(
#         request,
#         "industrial_estate/estate_detail.html",
#         context,
#     )


# @login_required
# def estate_create(request):
#     if request.method == "POST":
#         form = IndustrialEstateForm(
#             request.POST,
#             request.FILES,
#         )

#         if form.is_valid():
#             estate = form.save(commit=False)
#             estate.created_by = request.user
#             estate.save()

#             messages.success(
#                 request,
#                 "শিল্পনগরীর তথ্য সফলভাবে সংরক্ষণ করা হয়েছে।",
#             )

#             return redirect(
#                 "industrial_estate:estate-detail",
#                 pk=estate.pk,
#             )
#     else:
#         form = IndustrialEstateForm()

#     return render(
#         request,
#         "industrial_estate/estate_form.html",
#         {
#             "form": form,
#             "page_title": "নতুন শিল্পনগরীর তথ্য",
#         },
#     )


# @login_required
# def estate_update(request, pk):
#     estate = get_object_or_404(
#         IndustrialEstate,
#         pk=pk,
#     )

#     if request.method == "POST":
#         form = IndustrialEstateForm(
#             request.POST,
#             request.FILES,
#             instance=estate,
#         )

#         if form.is_valid():
#             form.save()

#             messages.success(
#                 request,
#                 "শিল্পনগরীর তথ্য হালনাগাদ করা হয়েছে।",
#             )

#             return redirect(
#                 "industrial_estate:estate-detail",
#                 pk=estate.pk,
#             )
#     else:
#         form = IndustrialEstateForm(instance=estate)

#     return render(
#         request,
#         "industrial_estate/estate_form.html",
#         {
#             "form": form,
#             "page_title": "শিল্পনগরীর তথ্য সম্পাদনা",
#             "estate": estate,
#         },
#     )


# @login_required
# @require_POST
# def layout_revision_upload(request, pk):
#     estate = get_object_or_404(
#         IndustrialEstate,
#         pk=pk,
#     )

#     form = EstateLayoutRevisionDocumentForm(
#         request.POST,
#         request.FILES,
#     )

#     if form.is_valid():
#         revision = form.save(commit=False)
#         revision.estate = estate
#         revision.save()

#         estate.layout_revised = True

#         if revision.approval_date:
#             estate.layout_revision_date = revision.approval_date

#         estate.save(
#             update_fields=[
#                 "layout_revised",
#                 "layout_revision_date",
#                 "updated_at",
#             ]
#         )

#         messages.success(
#             request,
#             "সংশোধিত লে-আউট প্ল্যান যুক্ত করা হয়েছে।",
#         )
#     else:
#         messages.error(
#             request,
#             "ফাইল যুক্ত করা যায়নি। PDF ফাইল ও প্রয়োজনীয় তথ্য যাচাই করুন।",
#         )

#     return redirect(
#         "industrial_estate:estate-detail",
#         pk=estate.pk,
#     )


# @login_required
# def plot_list(request, estate_pk):
#     estate = get_object_or_404(
#         IndustrialEstate,
#         pk=estate_pk,
#     )

#     plots = estate.plots.all()

#     return render(
#         request,
#         "industrial_estate/plot_list.html",
#         {
#             "estate": estate,
#             "plots": plots,
#         },
#     )
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
    estates = IndustrialEstate.objects.select_related(
        "regional_office", "district", "upazila"
    ).annotate(
        plot_count=Count("plots", distinct=True),
        unit_count=Count("industrial_units", distinct=True),
    )

    return render(
        request,
        "industrial_estate/estate_list.html",
        {"estates": estates},
    )


@login_required
def estate_detail(request, pk):
    estate = get_object_or_404(
        IndustrialEstate.objects.select_related(
            "regional_office", "district", "upazila"
        ),
        pk=pk,
    )

    plots = estate.plots.all()
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

    def form_valid(self, form):
        if hasattr(self.request.user, "is_authenticated"):
            form.instance.created_by = self.request.user
        messages.success(self.request, "শিল্পনগরীর তথ্য সংরক্ষণ করা হয়েছে।")
        return super().form_valid(form)


class EstateUpdateView(LoginRequiredMixin, UpdateView):
    model = IndustrialEstate
    form_class = IndustrialEstateForm
    template_name = "industrial_estate/estate_form.html"
    success_url = reverse_lazy("industrial_estate:estate_list")

    def form_valid(self, form):
        messages.success(self.request, "শিল্পনগরীর তথ্য হালনাগাদ হয়েছে।")
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
    estate = get_object_or_404(IndustrialEstate, pk=estate_pk)

    plots = estate.plots.all().order_by("plot_number")

    return render(
        request,
        "industrial_estate/plot_list.html",
        {
            "estate": estate,
            "plots": plots,
        },
    )


class PlotCreateView(LoginRequiredMixin, CreateView):
    model = Plot
    form_class = PlotForm
    template_name = "industrial_estate/record_form.html"

    def get_initial(self):
        initial = super().get_initial()
        estate_pk = self.request.GET.get("estate")
        if estate_pk:
            initial["estate"] = estate_pk
        return initial

    def get_success_url(self):
        return reverse(
            "industrial_estate:plot_list",
            kwargs={"estate_pk": self.object.estate_id},
        )


class PlotUpdateView(LoginRequiredMixin, UpdateView):
    model = Plot
    form_class = PlotForm
    template_name = "industrial_estate/record_form.html"

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
