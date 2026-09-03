# from urllib import request

# from django.shortcuts import render
# from .forms import AnotherLandForm
# # Create your views here.
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import (
#     render,
#     redirect,
#     get_object_or_404,
# )

# from django.utils import timezone
# from django.contrib.auth.models import User

# from accounts.models import UserProfile, UserRole

# from documents.models import DocumentTagEntry

# from lands.models import LandVerification

# from esate_db.districts import (
#     DISTRICTS,
#     DIVISION_NAMES,
# )

# from .models import AnotherLand
# from .forms import AnotherLandForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.models import UserProfile, UserRole
from documents.models import DocumentTagEntry
from lands.models import LandVerification

from esate_db.districts import DISTRICTS

from .models import AnotherLand
from .forms import AnotherLandForm


# ==========================================================
# REQUIRED DOCUMENT TAGS
# ==========================================================

REQUIRED_TAGS = [
    "Gazette",
    "Deed (Sale Deed / Registry Deed)",
    "Khatiyan",
    "Mutation (Namamari)",
    "Lease Deed",
    "Land Tax (Khajna / DCR)",
    "Porcha",
    "Mouza Map",
    "Baina / Agreement for Sale",
    "Land Survey Report",
    "Building Plan Approval",
]


# ==========================================================
# ANOTHER LAND LIST
# ==========================================================

@login_required
def another_land_list(request):

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    # ======================================================
    # SUPER ADMIN
    # ======================================================

    if profile.role == UserRole.SUPER_ADMIN:

        another_lands = (
            AnotherLand.objects
            .select_related(
                "created_by",
                "admin_verified_by",
                "super_admin_verified_by",
            )
            .order_by("-created_at")
        )

    # ======================================================
    # RD ADMIN
    # ======================================================

    elif profile.role == UserRole.RD_ADMIN:

        data_entry_users = User.objects.filter(
            userprofile__role=UserRole.DATA_ENTRY,
            userprofile__rd_admin=profile
        )

        another_lands = (
            AnotherLand.objects
            .filter(
                created_by__in=data_entry_users
            )
            .select_related(
                "created_by",
                "admin_verified_by",
                "super_admin_verified_by",
            )
            .order_by("-created_at")
        )

    # ======================================================
    # DATA ENTRY
    # ======================================================

    elif profile.role == UserRole.DATA_ENTRY:

        another_lands = (
            AnotherLand.objects
            .filter(
                created_by=request.user
            )
            .select_related(
                "created_by",
                "admin_verified_by",
                "super_admin_verified_by",
            )
            .order_by("-created_at")
        )

    # ======================================================
    # OTHER USERS
    # ======================================================

    else:

        another_lands = AnotherLand.objects.none()

    # ======================================================
    # TAGGING STATUS
    # ======================================================

    for land in another_lands:

        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT use LandVerification here.
        # AnotherLand has its own verification fields.
        # --------------------------------------------------

        uploaded_types = set()

        land.tag_status = []

        completed_count = 0

        for tag in REQUIRED_TAGS:

            completed = tag in uploaded_types

            if completed:
                completed_count += 1

            land.tag_status.append({
                "name": tag,
                "completed": completed,
            })

        land.completed_count = completed_count

        land.pending_count = (
            len(REQUIRED_TAGS) - completed_count
        )

        land.progress = round(
            completed_count * 100 / len(REQUIRED_TAGS),
            1
        )

    # ======================================================
    # IMPORTANT:
    # RETURN MUST BE OUTSIDE THE FOR LOOP
    # ======================================================

    return render(
        request,
        "AnotherLand/another_land_list.html",
        {
            "lands": another_lands,
            "required_tags": REQUIRED_TAGS,
        }
    )

# ==========================================================
# ADD ANOTHER LAND
# ==========================================================

# @login_required
# def another_land_create(request):

#     district = request.GET.get("district", "").strip()

#     if request.method == "POST":

#         form = AnotherLandForm(request.POST)

#         if form.is_valid():

#             another_land = form.save(commit=False)

#             another_land.created_by = request.user

#             another_land.save()

#             messages.success(
#                 request,
#                 "Another Land record created successfully!"
#             )

#             return redirect(
#                 "AnotherLand:another_land_list"
#             )

#     else:

#         form = AnotherLandForm(
#             initial={
#                 "district": district
#             }
#         )

#     return render(
#         request,
#         "AnotherLand/another_land_form.html",
#         {
#             "form": form,
#             "title": "Add Land",
#             "districts_json": DISTRICTS,
#         }
#     )
@login_required
def another_land_create(request):

    district = request.GET.get("district", "").strip()

    if request.method == "POST":

        print("====================================")
        print("ANOTHER LAND POST")
        print("POST DATA:", request.POST)
        print("====================================")

        form = AnotherLandForm(request.POST)

        if form.is_valid():

            print("FORM IS VALID")

            another_land = form.save(commit=False)
            another_land.created_by = request.user
            another_land.save()

            messages.success(
                request,
                "Another Land record created successfully!"
            )

            print("SAVED ID:", another_land.id)
            print("REDIRECTING...")

            return redirect(
                "AnotherLand:another_land_list"
            )

        else:

            print("====================================")
            print("FORM IS INVALID")
            print("FORM ERRORS:", form.errors)
            print("====================================")

    else:

        form = AnotherLandForm(
            initial={
                "district": district
            }
        )

    return render(
        request,
        "AnotherLand/another_land_form.html",
        {
            "form": form,
            "title": "Add Land",
            "districts_json": DISTRICTS,
        }
    )

# ==========================================================
# EDIT ANOTHER LAND
# ==========================================================

@login_required
def another_land_update(request, pk):

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if profile.role == UserRole.SUPER_ADMIN:

        land = get_object_or_404(
            AnotherLand,
            pk=pk
        )

    else:

        land = get_object_or_404(
            AnotherLand,
            pk=pk,
            created_by=request.user
        )

    if request.method == "POST":

        form = AnotherLandForm(
            request.POST,
            instance=land
        )

        if form.is_valid():

            another_land = form.save(
                commit=False
            )

            another_land.owner_name = (
                another_land.office_name
            )

            another_land.total_plots = 0
            another_land.allocated_plots = 0
            another_land.remaining_plots = 0

            another_land.save()

            messages.success(
                request,
                "Another Land record updated successfully!"
            )

            return redirect(
                "AnotherLand:another_land_list"
            )

    else:

        form = AnotherLandForm(
            instance=land
        )

    return render(
        request,
        "AnotherLand/another_land_form.html",
        {
            "form": form,
            "title": "Edit Land",
            "districts_json": DISTRICTS,
        }
    )


# ==========================================================
# DELETE
# ==========================================================

@login_required
def another_land_delete(request, pk):

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if profile.role == UserRole.SUPER_ADMIN:

        land = get_object_or_404(
            AnotherLand,
            pk=pk
        )

    else:

        land = get_object_or_404(
            AnotherLand,
            pk=pk,
            created_by=request.user
        )

    if request.method == "POST":

        land.delete()

        messages.success(
            request,
            "Another Land record deleted successfully!"
        )

        return redirect(
            "AnotherLand:another_land_list"
        )

    return render(
        request,
        "AnotherLand/another_land_confirm_delete.html",
        {
            "land": land
        }
    )


# ==========================================================
# ADMIN / SUPER ADMIN VERIFICATION
# ==========================================================

@login_required
def another_land_verification(request, pk):

    land = get_object_or_404(
        AnotherLand,
        pk=pk
    )

    # Important:
    # LandVerification is connected to the parent Land.
    verification, created = (
        LandVerification.objects.get_or_create(
            land=land
        )
    )

    entries = (
        DocumentTagEntry.objects
        .filter(
            document__land=land
        )
        .prefetch_related("tags")
        .select_related(
            "document",
            "created_by"
        )
        .order_by("-created_at")
    )

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        action = request.POST.get("action")

        # ---------------------------------------------
        # ADMIN
        # ---------------------------------------------

        if action == "admin":

            if profile.role != UserRole.RD_ADMIN:

                messages.error(
                    request,
                    "Only Admin can verify."
                )

            else:

                verification.admin_verified = True
                verification.admin_verified_by = request.user
                verification.admin_verified_date = timezone.now()
                verification.save()

                messages.success(
                    request,
                    "Successfully verified."
                )

        # ---------------------------------------------
        # SUPER ADMIN
        # ---------------------------------------------

        elif action == "super":

            if profile.role != UserRole.SUPER_ADMIN:

                messages.error(
                    request,
                    "Only Super Admin can verify."
                )

            elif not verification.admin_verified:

                messages.error(
                    request,
                    "Admin verification required."
                )

            else:

                verification.super_admin_verified = True
                verification.super_admin_verified_by = request.user
                verification.super_admin_verified_date = timezone.now()
                verification.save()

                messages.success(
                    request,
                    "Super Admin verification completed."
                )

        return redirect(
            "AnotherLand:another_land_verification",
            pk=pk
        )

    return render(
        request,
        "AnotherLand/admin_verification.html",
        {
            "land": land,
            "verification": verification,
            "entries": entries,
            "profile": profile,
            "required_tags": REQUIRED_TAGS,

            "is_admin": (
                profile.role == UserRole.RD_ADMIN
            ),

            "is_super_admin": (
                profile.role == UserRole.SUPER_ADMIN
            ),

            "admin_verified_current": (
                verification.admin_verified
            ),

            "super_admin_verified_current": (
                verification.super_admin_verified
            ),
        }
    )