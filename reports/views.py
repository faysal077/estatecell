from django.shortcuts import render

# Create your views here.
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import (
    Count,
    Sum,
    F,
    Value,
    DecimalField,
    IntegerField,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render, get_object_or_404, redirect

from lands.models import Land

from accounts.models import UserRole


# ============================================================
# SUPER ADMIN CHECK
# ============================================================

def super_admin_required(view_func):

    @login_required
    def wrapper(request, *args, **kwargs):

        try:
            profile = request.user.userprofile
        except Exception:
            messages.error(
                request,
                "User profile not found."
            )
            return redirect("lands:land_list")

        if profile.role != UserRole.SUPER_ADMIN:

            messages.error(
                request,
                "Only Super Admin can access Reports."
            )

            return redirect("lands:land_list")

        return view_func(
            request,
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# COMMON AGGREGATION
# ============================================================

def estate_summary(queryset):

    summary = queryset.aggregate(

        total_estates=Count(
            "id"
        ),

        total_acre=Coalesce(
            Sum("total_area"),
            Value(Decimal("0.00")),
            output_field=DecimalField(
                max_digits=15,
                decimal_places=2
            )
        ),

        total_plots=Coalesce(
            Sum("total_plots"),
            Value(0),
            output_field=IntegerField()
        ),

        allocated_plots=Coalesce(
            Sum("allocated_plots"),
            Value(0),
            output_field=IntegerField()
        ),

        remaining_plots=Coalesce(
            Sum("remaining_plots"),
            Value(0),
            output_field=IntegerField()
        ),
    )

    return summary


# ============================================================
# RD OFFICE REPORT
# ============================================================

@super_admin_required
def rd_office_report(request):

    lands = Land.objects.all()

    rd_offices = (
        lands
        .values("rd_office")
        .annotate(

            total_estates=Count(
                "id"
            ),

            total_acre=Coalesce(
                Sum("total_area"),
                Value(Decimal("0.00")),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=2
                )
            ),

            total_plots=Coalesce(
                Sum("total_plots"),
                Value(0),
                output_field=IntegerField()
            ),

            allocated_plots=Coalesce(
                Sum("allocated_plots"),
                Value(0),
                output_field=IntegerField()
            ),

            remaining_plots=Coalesce(
                Sum("remaining_plots"),
                Value(0),
                output_field=IntegerField()
            ),
        )
        .order_by("rd_office")
    )

    total = estate_summary(lands)

    context = {
        "rd_offices": rd_offices,
        "total": total,
    }

    return render(
        request,
        "reports/rd_office_report.html",
        context
    )


# ============================================================
# DISTRICT REPORT
# ============================================================

@super_admin_required
def district_report(request, rd_office):

    lands = Land.objects.filter(
        rd_office=rd_office
    )

    districts = (
        lands
        .values("district")
        .annotate(

            total_estates=Count(
                "id"
            ),

            total_acre=Coalesce(
                Sum("total_area"),
                Value(Decimal("0.00")),
                output_field=DecimalField(
                    max_digits=15,
                    decimal_places=2
                )
            ),

            total_plots=Coalesce(
                Sum("total_plots"),
                Value(0),
                output_field=IntegerField()
            ),

            allocated_plots=Coalesce(
                Sum("allocated_plots"),
                Value(0),
                output_field=IntegerField()
            ),

            remaining_plots=Coalesce(
                Sum("remaining_plots"),
                Value(0),
                output_field=IntegerField()
            ),
        )
        .order_by("district")
    )

    total = estate_summary(lands)

    context = {
        "rd_office": rd_office,
        "districts": districts,
        "total": total,
    }

    return render(
        request,
        "reports/district_report.html",
        context
    )


# ============================================================
# ESTATE REPORT
# ============================================================

@super_admin_required
def estate_report(request, rd_office, district):

    lands = Land.objects.filter(
        rd_office=rd_office,
        district=district
    ).order_by(
        "owner_name"
    )

    total = estate_summary(lands)

    context = {
        "rd_office": rd_office,
        "district": district,
        "lands": lands,
        "total": total,
    }

    return render(
        request,
        "reports/estate_report.html",
        context
    )


# ============================================================
# ESTATE DETAIL
# ============================================================

@super_admin_required
def estate_detail(request, pk):

    land = get_object_or_404(
        Land,
        pk=pk
    )

    context = {
        "land": land,
    }

    return render(
        request,
        "reports/estate_detail.html",
        context
    )