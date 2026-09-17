from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Value, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import render, get_object_or_404, redirect
from lands.models import Land
from documents.models import DocumentTagEntry
from AnotherLand.models import AnotherLand
from accounts.models import UserRole
from django.db.models import (
    Count,
    Sum,
    Value,
    DecimalField,
    IntegerField,
    Q,
)

# ============================================================
# REQUIRED TAGS
# ============================================================

REQUIRED_TAGS = [
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

        total_estates=Count("id"),

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

            total_estates=Count("id"),

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
# ADMIN VERIFICATION STATUS REPORT
# ============================================================

@super_admin_required
def admin_verification_status(request):

    # --------------------------------------------------------
    # Get all Land records
    # --------------------------------------------------------

    lands = (
        Land.objects
        .select_related(
            "verification",
            "verification__admin_verified_by",
        )
        .order_by(
            "rd_office",
            "owner_name"
        )
    )

    # --------------------------------------------------------
    # Get RD Offices
    # --------------------------------------------------------

    rd_offices = (
        Land.objects
        .values_list(
            "rd_office",
            flat=True
        )
        .distinct()
        .order_by("rd_office")
    )

    # --------------------------------------------------------
    # Build report
    # --------------------------------------------------------

    report_rows = []

    for rd_office in rd_offices:

        rd_lands = lands.filter(
            rd_office=rd_office
        )

        total_lands = rd_lands.count()

        # ----------------------------------------------------
        # Verified lands
        #
        # IMPORTANT:
        # Only admin_verified=True is considered verified.
        # ----------------------------------------------------

        verified_lands = rd_lands.filter(
            verification__admin_verified=True
        )

        verified_count = verified_lands.count()

        # ----------------------------------------------------
        # Pending lands
        #
        # This includes:
        # - no LandVerification record
        # - LandVerification exists but admin_verified=False
        # ----------------------------------------------------

        pending_lands = rd_lands.filter(
            Q(verification__isnull=True) |
            Q(verification__admin_verified=False)
        )

        pending_count = pending_lands.count()

        # ----------------------------------------------------
        # Prepare verified land data
        # ----------------------------------------------------

        verified_land_list = []

        for land in verified_lands:

            verified_land_list.append({
                "id": land.id,
                "name": land.owner_name,
                "status": "Verified",
                "url": (
                    f"/lands/verification/{land.id}/"
                ),
            })

        # ----------------------------------------------------
        # Prepare pending land data
        # ----------------------------------------------------

        pending_land_list = []

        for land in pending_lands:

            pending_land_list.append({
                "id": land.id,
                "name": land.owner_name,
                "status": "Pending",
                "url": (
                    f"/lands/verification/{land.id}/"
                ),
            })

        # ----------------------------------------------------
        # Verification percentage
        # ----------------------------------------------------

        verification_percentage = (
            round(
                (verified_count / total_lands) * 100,
                2
            )
            if total_lands
            else 0
        )

        report_rows.append({

            "rd_office": rd_office,

            "total_lands": total_lands,

            "verified_count": verified_count,

            "pending_count": pending_count,

            "verification_percentage":
                verification_percentage,

            "verified_lands":
                verified_land_list,

            "pending_lands":
                pending_land_list,

        })

    # --------------------------------------------------------
    # Overall totals
    # --------------------------------------------------------

    total_lands = lands.count()

    total_verified = lands.filter(
        verification__admin_verified=True
    ).count()

    total_pending = lands.filter(
        Q(verification__isnull=True) |
        Q(verification__admin_verified=False)
    ).count()

    total_percentage = (
        round(
            (total_verified / total_lands) * 100,
            2
        )
        if total_lands
        else 0
    )

    context = {

        "report_rows": report_rows,

        "total_lands": total_lands,

        "total_verified": total_verified,

        "total_pending": total_pending,

        "total_percentage": total_percentage,

    }

    return render(
        request,
        "reports/admin_verification_status.html",
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

            total_estates=Count("id"),

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


# ============================================================
# HELPER
# GET TAG STATUS FOR LAND
# ============================================================

# def get_land_tag_status(land):

#     added_tags = set()

#     entries = (
#         DocumentTagEntry.objects
#         .filter(document__land=land)
#         .prefetch_related("tags")
#     )

#     for entry in entries:

#         for tag in entry.tags.all():

#             if tag.name in REQUIRED_TAGS:
#                 added_tags.add(tag.name)

#     # --------------------------------------------------------
#     # Keep the exact REQUIRED_TAGS order
#     # --------------------------------------------------------

#     added_tags = [
#         tag
#         for tag in REQUIRED_TAGS
#         if tag in added_tags
#     ]

#     pending_tags = [
#         tag
#         for tag in REQUIRED_TAGS
#         if tag not in added_tags
#     ]

#     return added_tags, pending_tags

# ============================================================
# HELPER
# GET TAG STATUS FOR LAND
# ============================================================

def get_land_tag_status(land):

    # --------------------------------------------------------
    # Get all document types already added for this land
    # --------------------------------------------------------

    added_tag_set = set(
        DocumentTagEntry.objects
        .filter(document__land=land)
        .values_list("document_type", flat=True)
        .distinct()
    )

    # --------------------------------------------------------
    # Keep ONLY the 11 required tags
    # --------------------------------------------------------

    added_tags = [
        tag
        for tag in REQUIRED_TAGS
        if tag in added_tag_set
    ]

    # --------------------------------------------------------
    # Anything not added = Pending
    # --------------------------------------------------------

    pending_tags = [
        tag
        for tag in REQUIRED_TAGS
        if tag not in added_tag_set
    ]

    return added_tags, pending_tags


# ============================================================
# INDUSTRIAL LAND REPORT
# ============================================================

@super_admin_required
def industrial_land_report(request):

    lands = (
        Land.objects
        .all()
        .order_by("rd_office", "owner_name")
    )

    rd_offices = (
        Land.objects
        .values_list("rd_office", flat=True)
        .distinct()
        .order_by("rd_office")
    )

    estates = (
        Land.objects
        .values_list("owner_name", flat=True)
        .distinct()
        .order_by("owner_name")
    )

    # --------------------------------------------------------
    # GET FILTER VALUES
    # --------------------------------------------------------

    selected_rd_office = request.GET.get(
        "rd_office",
        ""
    ).strip()

    selected_estate = request.GET.get(
        "estate",
        ""
    ).strip()

    selected_added_tag = request.GET.get(
        "added_tag",
        ""
    ).strip()

    selected_pending_tag = request.GET.get(
        "pending_tag",
        ""
    ).strip()

    # --------------------------------------------------------
    # DATABASE FILTERS
    # --------------------------------------------------------

    if selected_rd_office:

        lands = lands.filter(
            rd_office=selected_rd_office
        )

    if selected_estate:

        lands = lands.filter(
            owner_name=selected_estate
        )

    # --------------------------------------------------------
    # BUILD REPORT DATA
    # --------------------------------------------------------

    report_rows = []

    for land in lands:

        added_tags, pending_tags = get_land_tag_status(
            land
        )

        # ----------------------------------------------------
        # Added Tag filter
        # ----------------------------------------------------

        if selected_added_tag:

            if selected_added_tag not in added_tags:
                continue

        # ----------------------------------------------------
        # Pending Tag filter
        # ----------------------------------------------------

        if selected_pending_tag:

            if selected_pending_tag not in pending_tags:
                continue

        report_rows.append({
            "land": land,
            "rd_office": land.rd_office,
            "estate": land.owner_name,
            "added_tags": added_tags,
            "pending_tags": pending_tags,
        })

    context = {

        "report_rows": report_rows,

        "rd_offices": rd_offices,

        "estates": estates,

        "required_tags": REQUIRED_TAGS,

        "selected_rd_office": selected_rd_office,

        "selected_estate": selected_estate,

        "selected_added_tag": selected_added_tag,

        "selected_pending_tag": selected_pending_tag,

    }

    return render(
        request,
        "reports/industrial_land_report.html",
        context
    )


# ============================================================
# NON-INDUSTRIAL LAND REPORT
# ============================================================

@super_admin_required
def non_industrial_land_report(request):

    lands = (
        AnotherLand.objects
        .all()
        .order_by("rd_office", "office_name")
    )

    rd_offices = (
        AnotherLand.objects
        .values_list("rd_office", flat=True)
        .distinct()
        .order_by("rd_office")
    )

    offices = (
        AnotherLand.objects
        .values_list("office_name", flat=True)
        .distinct()
        .order_by("office_name")
    )

    # --------------------------------------------------------
    # GET FILTER VALUES
    # --------------------------------------------------------

    selected_rd_office = request.GET.get(
        "rd_office",
        ""
    ).strip()

    selected_office = request.GET.get(
        "office",
        ""
    ).strip()

    selected_added_tag = request.GET.get(
        "added_tag",
        ""
    ).strip()

    selected_pending_tag = request.GET.get(
        "pending_tag",
        ""
    ).strip()

    # --------------------------------------------------------
    # DATABASE FILTERS
    # --------------------------------------------------------

    if selected_rd_office:

        lands = lands.filter(
            rd_office=selected_rd_office
        )

    if selected_office:

        lands = lands.filter(
            office_name=selected_office
        )

    # --------------------------------------------------------
    # BUILD REPORT DATA
    #
    # IMPORTANT:
    #
    # AnotherLand currently does not have a ForeignKey to
    # Document.
    #
    # Therefore tag status cannot yet be connected to
    # AnotherLand records using the current models.
    #
    # For now, all required tags are considered pending.
    # --------------------------------------------------------

    report_rows = []

    for land in lands:

        added_tags = []

        pending_tags = list(
            REQUIRED_TAGS
        )

        # ----------------------------------------------------
        # Added Tag filter
        # ----------------------------------------------------

        if selected_added_tag:

            if selected_added_tag not in added_tags:
                continue

        # ----------------------------------------------------
        # Pending Tag filter
        # ----------------------------------------------------

        if selected_pending_tag:

            if selected_pending_tag not in pending_tags:
                continue

        report_rows.append({
            "land": land,
            "rd_office": land.rd_office,
            "office": land.office_name,
            "added_tags": added_tags,
            "pending_tags": pending_tags,
        })

    context = {

        "report_rows": report_rows,

        "rd_offices": rd_offices,

        "offices": offices,

        "required_tags": REQUIRED_TAGS,

        "selected_rd_office": selected_rd_office,

        "selected_office": selected_office,

        "selected_added_tag": selected_added_tag,

        "selected_pending_tag": selected_pending_tag,

    }

    return render(
        request,
        "reports/non_industrial_land_report.html",
        context
    )